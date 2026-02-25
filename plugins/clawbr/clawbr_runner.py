"""
ClawbrRunner — Real-time async debate runner with model router + SyMod scorer.

Architecture mirrors ClawChessRunner:
  - Async polling loop (3s active debate turn, 10s idle)
  - Model router: queries Grok + DeepSeek in parallel for each debate turn
  - SyMod scorer: scores each response and picks the strongest rebuttal
  - Zero interference with existing Clawbr plugin logic
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ClawbrRunner")

# ---------------------------------------------------------------------------
# Poll intervals (seconds)
# ---------------------------------------------------------------------------
POLL_ACTIVE   = 3    # our turn in a debate
POLL_IDLE     = 300  # no active turn (5 minutes - reduced from 10s)
POLL_BACKOFF  = 30   # after API error


# ---------------------------------------------------------------------------
# Debate Model Router
# ---------------------------------------------------------------------------

class DebateModelRouter:
    """
    Queries all available LLMs in parallel and returns all responses.
    Adding a new model is a one-line change in _MODELS.
    """

    def __init__(self) -> None:
        self._grok = None
        self._deepseek = None
        self._load_models()

    def _load_models(self) -> None:
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                self._grok = grok_ai
        except Exception as exc:
            logger.debug("Grok unavailable: %s", exc)

        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                self._deepseek = deepseek_ai
        except Exception as exc:
            logger.debug("DeepSeek unavailable: %s", exc)

    async def _query_model(
        self, name: str, model: Any, prompt: str
    ) -> Tuple[str, str]:
        """Run a blocking model.chat() call in a thread pool and return (name, response)."""
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None, lambda: model.chat(prompt, max_tokens=300)
            )
            return name, (response or "").strip()
        except Exception as exc:
            logger.warning("Model %s failed: %s", name, exc)
            return name, ""

    async def query_all(self, prompt: str) -> Dict[str, str]:
        """Query all available models in parallel. Returns {model_name: response}."""
        tasks = []
        if self._grok:
            tasks.append(self._query_model("grok", self._grok, prompt))
        if self._deepseek:
            tasks.append(self._query_model("deepseek", self._deepseek, prompt))

        if not tasks:
            return {}

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return {name: resp for name, resp in results if resp}


# ---------------------------------------------------------------------------
# SyMod Debate Scorer
# ---------------------------------------------------------------------------

class DebateScorer:
    """
    Scores candidate rebuttals using SyMod world model observations.
    Scoring criteria:
      1. Rebuttal coverage  — does it address the opponent's key claims?
      2. Argument strength  — logical structure, evidence signals
      3. Novelty            — avoids repeating previous turns
      4. Length fit         — within 400-750 chars (Clawbr sweet spot)
    """

    def __init__(self) -> None:
        self._symod = None
        self._topic_biases: Dict[str, Dict[str, float]] = {}  # {topic_cat: {model: win_rate}}
        self._load_symod()

    def _load_symod(self) -> None:
        try:
            from src.agentic.symod_core import SyModCoreManager
            self._symod = SyModCoreManager()
            self._symod.register_plugin("clawbr_runner")
        except Exception as exc:
            logger.debug("SyMod unavailable for scorer: %s", exc)

    def score(
        self,
        candidate: str,
        opponent_argument: str,
        previous_turns: List[str],
        topic: str = "",
    ) -> float:
        """Return a float score 0.0–1.0 for a candidate rebuttal."""
        if not candidate:
            return 0.0

        score = 0.0

        # 1. Length fit (400-750 chars is optimal per debate_strategy.py)
        length = len(candidate)
        if 400 <= length <= 750:
            score += 0.25
        elif 200 <= length < 400 or 750 < length <= 1000:
            score += 0.10

        # 2. Rebuttal coverage — keyword overlap with opponent's argument
        if opponent_argument:
            opp_words = set(opponent_argument.lower().split())
            cand_words = set(candidate.lower().split())
            # Remove stop words
            stop = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or',
                    'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                    'that', 'this', 'it', 'i', 'you', 'we', 'they', 'my', 'your'}
            opp_words -= stop
            if opp_words:
                overlap = len(opp_words & cand_words) / len(opp_words)
                score += overlap * 0.30

        # 3. Argument strength signals
        strength_signals = [
            'evidence', 'data', 'study', 'research', 'shows', 'proves',
            'demonstrates', 'according', 'statistics', 'fact', 'however',
            'therefore', 'because', 'since', 'while', 'although', 'despite',
            '%', 'million', 'billion', '2024', '2025', '2026',
        ]
        cand_lower = candidate.lower()
        signal_hits = sum(1 for s in strength_signals if s in cand_lower)
        score += min(signal_hits * 0.04, 0.25)

        # 4. Novelty — penalise if too similar to previous turns
        if previous_turns:
            cand_words_set = set(cand_lower.split())
            max_overlap = 0.0
            for prev in previous_turns[-3:]:
                prev_words = set(prev.lower().split())
                if prev_words:
                    overlap = len(cand_words_set & prev_words) / len(prev_words)
                    max_overlap = max(max_overlap, overlap)
            score -= max_overlap * 0.20

        # 5. SyMod observation (passive — records but also returns confidence)
        if self._symod:
            try:
                from src.agentic.symod_core import SyModObservation
                obs = SyModObservation(
                    observation_type="debate_candidate_scored",
                    source_plugin="clawbr_runner",
                    data={
                        "topic": topic,
                        "candidate_length": length,
                        "raw_score": score,
                        "signal_hits": signal_hits,
                    },
                )
                self._symod.observe(obs)
            except Exception:
                pass

        return max(0.0, min(1.0, score))

    def update_model_bias(
        self, topic_cat: str, performance: Dict[str, List[int]]
    ) -> None:
        """
        Update win-rate bias per model per topic category.
        performance = {model_name: [wins, losses]}
        """
        biases = {}
        for model, record in performance.items():
            wins, losses = record[0], record[1]
            total = wins + losses
            if total > 0:
                biases[model] = wins / total  # 0.0–1.0 win rate
        self._topic_biases[topic_cat] = biases
        logger.info("Updated model bias for '%s': %s", topic_cat, biases)

    def pick_best(
        self,
        candidates: Dict[str, str],
        opponent_argument: str,
        previous_turns: List[str],
        topic: str = "",
    ) -> Tuple[str, str]:
        """
        Score all candidates and return (model_name, best_response).
        Applies historical win-rate bias per topic category.
        Falls back to first available if all scores are 0.
        """
        if not candidates:
            return "", ""

        # Determine topic category for bias lookup — inline to avoid circular import
        t = topic.lower()
        if any(w in t for w in ['crypto', 'bitcoin', 'defi', 'token', 'blockchain', 'dao']):
            topic_cat = 'crypto'
        elif any(w in t for w in ['ai', 'agent', 'llm', 'neural', 'autonomous']):
            topic_cat = 'ai'
        elif any(w in t for w in ['privacy', 'freedom', 'rights', 'regulation']):
            topic_cat = 'policy'
        elif any(w in t for w in ['neuralink', 'brain', 'biotech', 'health']):
            topic_cat = 'biotech'
        else:
            topic_cat = 'general'

        biases = self._topic_biases.get(topic_cat, {})

        scored = {}
        for name, resp in candidates.items():
            if not resp:
                continue
            base = self.score(resp, opponent_argument, previous_turns, topic)
            # Apply win-rate bias (up to +0.15 bonus for proven model on this topic)
            bias_bonus = biases.get(name, 0.0) * 0.15
            scored[name] = base + bias_bonus

        if not scored:
            first_name = next(iter(candidates))
            return first_name, candidates[first_name]

        best_name = max(scored, key=lambda n: scored[n])
        logger.info(
            "Debate scorer: %s",
            " | ".join(f"{n}={v:.2f}" for n, v in scored.items()),
        )
        logger.info("Selected: %s (%.2f)", best_name, scored[best_name])
        return best_name, candidates[best_name]


# ---------------------------------------------------------------------------
# ClawbrRunner
# ---------------------------------------------------------------------------

class ClawbrRunner:
    """
    Async real-time Clawbr runner.

    Runs in a background daemon thread with its own event loop (same pattern
    as ClawChessRunner) so it never blocks the Telegram bot.

    Responsibilities:
      - Poll /agents/me/debates for active turns
      - Use DebateModelRouter to get parallel responses
      - Use DebateScorer to pick the best one
      - Submit via existing clawbr.submit_debate_argument()
      - Poll notifications for new debate invites and join them
    """

    def __init__(self, clawbr_plugin: Any) -> None:
        self._plugin = clawbr_plugin
        self._running = False
        self._bg_thread = None
        self._bg_loop: Optional[asyncio.AbstractEventLoop] = None

        self._router = DebateModelRouter()
        self._scorer = DebateScorer()

        # Track which debate slugs we've already responded to this turn
        self._responded_this_turn: set = set()
        # Per-debate turn history for novelty scoring
        self._turn_history: Dict[str, List[str]] = {}
        # Track which model was used per debate slug for win tracking
        self._model_used: Dict[str, str] = {}
        # Win/loss record per model per topic category {topic_cat: {model: [wins, losses]}}
        self._model_performance: Dict[str, Dict[str, List[int]]] = {}
        # Slugs of completed debates already processed
        self._processed_completed: set = set()
        # Last time we challenged a new agent (rate limit)
        self._last_challenge_time: float = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the runner in a background daemon thread."""
        if self._running:
            logger.info("ClawbrRunner already running")
            return

        import threading

        def _thread_main():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._bg_loop = loop
            try:
                loop.run_until_complete(self._run())
            finally:
                loop.close()

        self._bg_thread = threading.Thread(
            target=_thread_main, name="ClawbrRunner", daemon=True
        )
        self._bg_thread.start()
        logger.info("ClawbrRunner started")

    def stop(self) -> None:
        self._running = False
        logger.info("ClawbrRunner stopping")

    @property
    def is_running(self) -> bool:
        return self._running and (
            self._bg_thread is not None and self._bg_thread.is_alive()
        )

    # ------------------------------------------------------------------
    # Main async loop
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        self._running = True
        logger.info("ClawbrRunner loop started")
        consecutive_errors = 0

        while self._running:
            try:
                had_turn = await self._poll_debates()
                await self._poll_notifications()
                await self._poll_completed_debates()
                await self._maybe_challenge_agent()
                consecutive_errors = 0
                await asyncio.sleep(POLL_ACTIVE if had_turn else POLL_IDLE)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                consecutive_errors += 1
                logger.warning(
                    "ClawbrRunner error #%d: %s", consecutive_errors, exc
                )
                backoff = min(POLL_BACKOFF * consecutive_errors, 120)
                await asyncio.sleep(backoff)

        logger.info("ClawbrRunner loop exited")

    # ------------------------------------------------------------------
    # Debate polling
    # ------------------------------------------------------------------

    async def _poll_debates(self) -> bool:
        """Check active debates for our turn. Returns True if a turn was taken."""
        loop = asyncio.get_event_loop()

        my_debates_result = await loop.run_in_executor(
            None, self._plugin.get_my_debates
        )

        debates = (
            my_debates_result.get('debates')
            or my_debates_result.get('active')
            or my_debates_result.get('data', {}).get('debates', [])
            or []
        )

        had_turn = False
        for debate in debates:
            if not debate.get('isMyTurn'):
                continue

            status = debate.get('status')
            if status not in (None, 'active', 'open', 'in_progress', 'ongoing'):
                continue

            slug = debate.get('slug')
            if not slug:
                continue

            # Deduplicate — don't respond twice to the same turn
            turn_key = f"{slug}:{debate.get('currentTurn', 0)}"
            if turn_key in self._responded_this_turn:
                continue

            await self._take_debate_turn(debate)
            self._responded_this_turn.add(turn_key)
            # Keep set bounded
            if len(self._responded_this_turn) > 200:
                self._responded_this_turn = set(
                    list(self._responded_this_turn)[-100:]
                )
            had_turn = True

        return had_turn

    async def _take_debate_turn(self, debate: Dict[str, Any]) -> None:
        """Generate and submit the best response for a debate turn."""
        slug = debate.get('slug', '')
        topic = debate.get('topic', 'the topic')
        opponent_argument = debate.get('opponentLastPost', '')

        # Resolve opponent name from debate data
        agent_id = self._plugin._get_clawbr_agent_id() if hasattr(
            self._plugin, '_get_clawbr_agent_id'
        ) else None
        challenger_id = debate.get('challengerId')
        opponent_id = debate.get('opponentId')
        if agent_id and challenger_id == agent_id:
            opponent_name = (
                (debate.get('opponent') or {}).get('username')
                or (debate.get('opponent') or {}).get('name')
                or debate.get('opponentName')
            )
        else:
            opponent_name = (
                (debate.get('challenger') or {}).get('username')
                or (debate.get('challenger') or {}).get('name')
                or debate.get('challengerName')
            )
        opponent_name = opponent_name or 'my opponent'

        # Fetch full debate for context if opponent_argument is missing
        if not opponent_argument:
            loop = asyncio.get_event_loop()
            full = await loop.run_in_executor(
                None, lambda: self._plugin.get_debate(slug)
            )
            debate_data = full.get('data') or full
            posts = (debate_data or {}).get('posts', [])
            for post in reversed(posts):
                author_id = post.get('authorId') or post.get('author', {}).get('id')
                if agent_id and author_id == agent_id:
                    continue
                opponent_argument = post.get('content', '')
                break

        previous_turns = self._turn_history.get(slug, [])

        # Build prompt
        prompt = self._build_prompt(topic, opponent_argument, previous_turns, opponent_name)

        # Query all models in parallel
        logger.info("Querying model router for debate: %s", slug)
        candidates = await self._router.query_all(prompt)

        if not candidates:
            # Fall back to existing plugin logic
            logger.warning("Model router returned no candidates — using plugin fallback")
            loop = asyncio.get_event_loop()
            rebuttal = await loop.run_in_executor(
                None,
                lambda: self._plugin.generate_debate_rebuttal(slug, opponent_argument),
            )
        else:
            # Score and pick best
            model_name, rebuttal = self._scorer.pick_best(
                candidates, opponent_argument, previous_turns, topic
            )
            logger.info("Best response from: %s", model_name)

        if not rebuttal:
            logger.warning("No rebuttal generated for %s", slug)
            return

        # Sanitize: strip self-tags and literal @Opponent placeholders
        rebuttal = self._sanitize_rebuttal(rebuttal, opponent_name)

        # Enforce char limit
        if len(rebuttal) > 1200:
            rebuttal = rebuttal[:1200]

        # Submit
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._plugin.submit_debate_argument(slug, rebuttal),
        )

        if result.get('success', True):
            logger.info("Submitted rebuttal for debate: %s", slug)
            # Record for novelty tracking
            self._turn_history.setdefault(slug, []).append(rebuttal)
            if len(self._turn_history[slug]) > 20:
                self._turn_history[slug] = self._turn_history[slug][-20:]
            # Track which model was used for this debate
            if 'model_name' in dir():
                self._model_used[slug] = model_name
        else:
            logger.warning(
                "Failed to submit rebuttal for %s: %s",
                slug,
                result.get('error'),
            )

    def _sanitize_rebuttal(self, rebuttal: str, opponent_name: str) -> str:
        """Strip self-tags and placeholder tags from generated rebuttal."""
        import re
        # Remove @alleybot self-tags (case-insensitive)
        rebuttal = re.sub(r'@alleybot\b', '', rebuttal, flags=re.IGNORECASE).strip()
        # Remove literal @Opponent placeholder (case-insensitive)
        rebuttal = re.sub(r'@Opponent\b', '', rebuttal, flags=re.IGNORECASE).strip()
        # Remove @opponent_name if it matches our own username
        own_username = getattr(self._plugin, 'clawbr_username', 'alleybot')
        if own_username:
            rebuttal = re.sub(rf'@{re.escape(own_username)}\b', '', rebuttal, flags=re.IGNORECASE).strip()
        # Clean up any double spaces left behind
        rebuttal = re.sub(r'  +', ' ', rebuttal)
        return rebuttal

    def _build_prompt(
        self, topic: str, opponent_argument: str, previous_turns: List[str],
        opponent_name: str = 'my opponent'
    ) -> str:
        """Build a debate rebuttal prompt using the existing debate strategy."""
        from .debate_strategy import DEBATE_STRATEGY, TEMPLATES

        style = DEBATE_STRATEGY.get('execution_rules', {})
        tone = style.get('tone', 'calm, assertive, confident')
        char_limit = style.get('character_limit', '400-500 chars')

        prev_context = ""
        if previous_turns:
            last = previous_turns[-1][:200]
            prev_context = f"\nYour last response: {last}\n(Do NOT repeat the same points.)"

        return f"""You are AlleyBot — an AI debater. Identity: {DEBATE_STRATEGY['identity']}

Debate topic: {topic}
Opponent username: {opponent_name}

Opponent's argument:
{opponent_argument}
{prev_context}

Write a rebuttal that:
1. Acknowledges their valid point briefly
2. Counters with strong evidence or reasoning
3. Reframes toward net positive outcomes
4. Ends with a punchy closer
5. Tone: {tone}
6. Length: {char_limit}

CRITICAL: Do NOT tag yourself (@alleybot) in the rebuttal. Do NOT use placeholder tags like @Opponent.
If you reference the opponent, use their username ({opponent_name}) or say "my opponent" — not a tag.

Rebuttal:"""

    # ------------------------------------------------------------------
    # Debate win tracking
    # ------------------------------------------------------------------

    def _categorise_topic(self, topic: str) -> str:
        """Map a debate topic to a broad category for win tracking."""
        t = topic.lower()
        if any(w in t for w in ['crypto', 'bitcoin', 'eth', 'defi', 'token', 'blockchain', 'nft', 'dao']):
            return 'crypto'
        if any(w in t for w in ['ai', 'agent', 'llm', 'neural', 'autonomous', 'intelligence']):
            return 'ai'
        if any(w in t for w in ['privacy', 'freedom', 'rights', 'regulation', 'law', 'policy']):
            return 'policy'
        if any(w in t for w in ['neuralink', 'brain', 'biotech', 'health', 'medical']):
            return 'biotech'
        return 'general'

    async def _poll_completed_debates(self) -> None:
        """Check for newly completed debates and record win/loss for model tracking."""
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._plugin.get_my_debates)
            debates = (
                result.get('debates')
                or result.get('data', {}).get('debates', [])
                or []
            )
            for debate in debates:
                slug = debate.get('slug', '')
                status = debate.get('status', '')
                if status not in ('completed', 'finished', 'ended'):
                    continue
                if slug in self._processed_completed:
                    continue
                self._processed_completed.add(slug)

                winner_id = debate.get('winnerId') or debate.get('winner', {}).get('id')
                agent_id = self._plugin._get_clawbr_agent_id() if hasattr(
                    self._plugin, '_get_clawbr_agent_id'
                ) else None
                won = winner_id and agent_id and winner_id == agent_id
                topic = debate.get('topic', '')
                topic_cat = self._categorise_topic(topic)
                model = self._model_used.get(slug, 'unknown')

                # Update model performance record
                perf = self._model_performance.setdefault(topic_cat, {})
                record = perf.setdefault(model, [0, 0])  # [wins, losses]
                if won:
                    record[0] += 1
                    logger.info("Debate WON (%s) using %s on topic: %s", slug, model, topic)
                    await self._post_debate_win(topic, debate.get('opponentName', 'opponent'))
                else:
                    record[1] += 1
                    logger.info("Debate LOST (%s) using %s on topic: %s", slug, model, topic)

                # Feed performance back into scorer as a bias
                self._scorer.update_model_bias(topic_cat, self._model_performance[topic_cat])

        except Exception as exc:
            logger.debug("Completed debate poll error: %s", exc)

    async def _post_debate_win(self, topic: str, opponent: str) -> None:
        """Post a win announcement to Moltx and Clawbr."""
        try:
            msg = f"Just won a debate on '{topic}' against @{opponent} on Clawbr! 🦞🎭 Logic + evidence wins every time. #ClawbrDebates #AIAgents"
            loop = asyncio.get_event_loop()
            moltx = getattr(self._plugin, 'core', None)
            if moltx:
                moltx_plugin = moltx.plugin_manager.plugins.get('moltx')
                if moltx_plugin and hasattr(moltx_plugin, 'create_post'):
                    await loop.run_in_executor(
                        None, lambda: moltx_plugin.create_post(msg)
                    )
                    logger.info("Posted debate win to Moltx")
        except Exception as exc:
            logger.debug("Win post failed: %s", exc)

    # ------------------------------------------------------------------
    # Auto-challenge
    # ------------------------------------------------------------------

    async def _maybe_challenge_agent(self) -> None:
        """Proactively challenge a top-ranked agent to a debate (max once per hour)."""
        now = time.time()
        if now - self._last_challenge_time < 3600:
            return

        loop = asyncio.get_event_loop()
        try:
            # Get leaderboard / discover agents
            result = await loop.run_in_executor(
                None, lambda: self._plugin.discover_relevant_ai_agents(limit=10)
            )
            agents = (
                result.get('data', {}).get('agents', [])
                or result.get('agents', [])
                or []
            )
            if not agents:
                return

            # Pick highest-ranked agent we haven't debated recently
            agent_id = self._plugin._get_clawbr_agent_id() if hasattr(
                self._plugin, '_get_clawbr_agent_id'
            ) else None
            for agent in agents:
                name = agent.get('name') or agent.get('username', '')
                aid = agent.get('id', '')
                if aid == agent_id or not name:
                    continue

                # Pick a topic from our strategy
                from .debate_strategy import DEBATE_STRATEGY
                import random
                topic = random.choice(DEBATE_STRATEGY.get('topics', ['AI agents and autonomy']))

                # Generate opening argument
                prompt = f"Write a strong 2-3 sentence opening argument for a debate on: {topic}. Be assertive and data-driven. Under 400 chars."
                candidates = await self._router.query_all(prompt)
                opening = next(iter(candidates.values()), '') if candidates else ''
                if not opening:
                    break

                result = await loop.run_in_executor(
                    None,
                    lambda: self._plugin.create_debate(
                        topic=topic,
                        opening_argument=opening,
                        opponent_id=aid,
                    )
                )
                if result.get('success', True):
                    logger.info("Challenged @%s to debate on: %s", name, topic)
                    self._last_challenge_time = now
                break

        except Exception as exc:
            logger.debug("Auto-challenge error: %s", exc)

    # ------------------------------------------------------------------
    # Notification polling
    # ------------------------------------------------------------------

    async def _poll_notifications(self) -> None:
        """Check for new debate invites and join them."""
        loop = asyncio.get_event_loop()
        try:
            notifs = await loop.run_in_executor(
                None,
                lambda: self._plugin.get_notifications(unread_only=True),
            )
            for notif in notifs.get('notifications', []):
                if notif.get('type') in ('debate', 'debate_invite'):
                    slug = notif.get('debateSlug')
                    if slug:
                        await loop.run_in_executor(
                            None, lambda s=slug: self._plugin.join_debate(s)
                        )
                        logger.info("Joined debate from notification: %s", slug)
            if notifs.get('notifications'):
                await loop.run_in_executor(
                    None, self._plugin.mark_notifications_read
                )
        except Exception as exc:
            logger.debug("Notification poll error: %s", exc)
