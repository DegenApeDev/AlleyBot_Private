"""
Decision Engine Mixin
The autonomous brain that reasons about WHAT to do next.
Uses AI to evaluate context and pick the highest-value action.
"""
import os
import json
import datetime
import random
from typing import Dict, Any, Optional, List, Tuple


# Available autonomous actions the brain can take
AUTONOMOUS_ACTIONS = {
    'moltx_engage': {
        'description': 'Browse Moltx feed and engage with posts (upvote, comment)',
        'platform': 'moltx',
        'cooldown_minutes': 20,
        'impact': 'medium',
        'requires': 'moltx',
    },
    'moltx_post': {
        'description': 'Create an AI-generated post on Moltx about a trending topic',
        'platform': 'moltx',
        'cooldown_minutes': 120,
        'impact': 'high',
        'requires': 'moltx',
    },
    'moltbook_heartbeat': {
        'description': 'Run Moltbook heartbeat - browse, upvote, comment on posts',
        'platform': 'moltbook',
        'cooldown_minutes': 30,
        'impact': 'medium',
        'requires': 'moltbook',
    },
    'moltbook_post': {
        'description': 'Create an AI-generated post on Moltbook',
        'platform': 'moltbook',
        'cooldown_minutes': 180,
        'impact': 'high',
        'requires': 'moltbook',
    },
    'onchain_heartbeat': {
        'description': 'Check on-chain balances and monitor for changes',
        'platform': 'onchain',
        'cooldown_minutes': 10,
        'impact': 'low',
        'requires': 'onchain',
    },
    'check_comments': {
        'description': 'Check for new comments on our posts and reply intelligently',
        'platform': 'all',
        'cooldown_minutes': 15,
        'impact': 'high',
        'requires': 'moltx',
    },
    'analyze_trending': {
        'description': 'Analyze trending topics to inform future posts',
        'platform': 'moltx',
        'cooldown_minutes': 60,
        'impact': 'medium',
        'requires': 'moltx',
    },
    'build_skill': {
        'description': 'Identify a capability gap and generate a new SKILL.md to improve AlleyBot',
        'platform': 'system',
        'cooldown_minutes': 360,
        'impact': 'high',
        'requires': 'selfimprove',
    },
}


class DecisionEngineMixin:
    """Mixin for autonomous decision-making"""

    def _init_decision_engine(self):
        """Initialize decision engine state"""
        self.action_history: List[Dict] = []
        self.action_cooldowns: Dict[str, datetime.datetime] = {}
        self._load_decision_state()

    def _load_decision_state(self):
        """Load decision state from memory"""
        try:
            state = self.core.get_memory('brain_decision_state')
            if state:
                self.action_history = state.get('action_history', [])
                # Restore cooldowns
                for action, ts in state.get('cooldowns', {}).items():
                    try:
                        self.action_cooldowns[action] = datetime.datetime.fromisoformat(ts)
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    def _save_decision_state(self):
        """Save decision state"""
        try:
            self.core.save_memory('brain_decision_state', {
                'action_history': self.action_history[-100:],
                'cooldowns': {k: v.isoformat() for k, v in self.action_cooldowns.items()},
            })
        except Exception as e:
            print(f"⚠️  Failed to save decision state: {e}")

    def get_available_actions(self) -> List[Dict]:
        """Get actions that are available right now (not on cooldown, plugin loaded)"""
        now = datetime.datetime.now()
        available = []

        for action_id, action_info in AUTONOMOUS_ACTIONS.items():
            # Check cooldown
            last_run = self.action_cooldowns.get(action_id)
            if last_run:
                cooldown = datetime.timedelta(minutes=action_info['cooldown_minutes'])
                if now - last_run < cooldown:
                    continue

            # Check if required plugin is loaded
            required = action_info['requires']
            if required != 'all' and required not in self.core.plugin_manager.plugins:
                continue

            available.append({
                'id': action_id,
                **action_info,
                'last_run': last_run.isoformat() if last_run else None,
            })

        return available

    def decide_next_action(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Use AI reasoning to decide the best next action"""
        available = self.get_available_actions()
        if not available:
            return None

        # Build context summary for AI
        context_summary = self.build_context_summary()

        # Try AI-powered decision
        decision = self._ai_decide(available, context_summary, context)
        if decision:
            return decision

        # Fallback: score-based heuristic
        return self._heuristic_decide(available, context)

    def _ai_decide(self, available: List[Dict], context_summary: str,
                   full_context: Dict) -> Optional[Dict]:
        """Use Grok/DeepSeek to reason about the best action"""
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return None

            actions_text = "\n".join(
                f"- {a['id']}: {a['description']} (impact: {a['impact']}, platform: {a['platform']})"
                for a in available
            )

            engagement = full_context.get('engagement', {})
            recent_actions = full_context.get('recent_actions', [])
            recent_text = "\n".join(
                f"- {a.get('action', '?')} at {a.get('timestamp', '?')[:16]} ({'✅' if a.get('success') else '❌'})"
                for a in recent_actions[-5:]
            ) if recent_actions else "No recent actions"

            prompt = f"""You are AlleyBot's autonomous decision engine. Based on the current context, choose the SINGLE best action to take right now.

CURRENT CONTEXT:
{context_summary}

RECENT ACTIONS:
{recent_text}

SUCCESS RATE: {engagement.get('success_rate', 0):.0%} over {engagement.get('total_recent', 0)} recent actions

AVAILABLE ACTIONS:
{actions_text}

DECISION RULES:
1. Prioritize HIGH impact actions when available
2. Spread activity across platforms (don't spam one platform)
3. If we recently posted, prefer engagement over posting
4. If comments are waiting, reply to them first
5. Check on-chain periodically but don't over-check
6. Build skills only when idle on other platforms

Respond with ONLY the action ID (e.g. "moltx_engage") and a brief reason on the next line.
Example:
moltbook_heartbeat
Haven't engaged on Moltbook recently, good time to build karma."""

            data = {
                "model": grok_ai.model,
                "messages": [
                    {"role": "system", "content": "You are an autonomous AI agent decision engine. Be decisive and strategic."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.3,
            }

            response = grok_ai._make_api_request(data)
            text = grok_ai._extract_text(response)

            if text:
                lines = text.strip().split('\n')
                chosen_id = lines[0].strip().lower().replace('`', '').replace('"', '').replace("'", "")
                reason = lines[1].strip() if len(lines) > 1 else "AI decision"

                # Validate the choice
                valid_ids = {a['id'] for a in available}
                if chosen_id in valid_ids:
                    chosen = next(a for a in available if a['id'] == chosen_id)
                    chosen['reason'] = reason
                    chosen['decision_method'] = 'ai'
                    return chosen

            return None

        except Exception as e:
            print(f"⚠️  AI decision failed: {e}")
            return None

    def _heuristic_decide(self, available: List[Dict], context: Dict) -> Optional[Dict]:
        """Fallback heuristic-based decision"""
        if not available:
            return None

        # Score each action
        scored = []
        engagement = context.get('engagement', {})
        recent_actions = context.get('recent_actions', [])
        recent_platforms = set()
        for a in recent_actions[-5:]:
            p = a.get('platform', '')
            if p:
                recent_platforms.add(p)

        for action in available:
            score = 0.0

            # Impact score
            impact_scores = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
            score += impact_scores.get(action['impact'], 1.0)

            # Platform diversity bonus
            if action['platform'] not in recent_platforms:
                score += 1.5

            # Engagement actions get a boost if we haven't engaged recently
            if 'engage' in action['id'] or 'heartbeat' in action['id']:
                score += 0.5

            # Comment checking is always high priority
            if 'comment' in action['id']:
                score += 2.0

            # Small random factor to avoid being predictable
            score += random.uniform(0, 0.5)

            scored.append((action, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]
        best['reason'] = 'Heuristic: highest score'
        best['decision_method'] = 'heuristic'
        return best

    def execute_action(self, action: Dict) -> Dict[str, Any]:
        """Execute a decided action and record the result"""
        action_id = action['id']
        now = datetime.datetime.now()

        print(f"🧠 Brain executing: {action_id} ({action.get('reason', 'no reason')})")

        result = {
            'action': action_id,
            'platform': action.get('platform', 'unknown'),
            'reason': action.get('reason', ''),
            'decision_method': action.get('decision_method', 'unknown'),
            'timestamp': now.isoformat(),
            'success': False,
            'output': '',
        }

        try:
            output = self._dispatch_action(action_id)
            result['success'] = output is not None and not str(output).startswith('❌')
            result['output'] = str(output)[:500] if output else ''

        except Exception as e:
            result['success'] = False
            result['output'] = f"Error: {e}"
            print(f"❌ Brain action failed: {e}")

        # Record cooldown
        self.action_cooldowns[action_id] = now

        # Record in history
        self.action_history.append(result)
        self.action_history = self.action_history[-100:]

        # Save to memory for engagement tracking
        try:
            engagement_log = self.core.get_memory('brain_engagement_log') or []
            if not isinstance(engagement_log, list):
                engagement_log = []
            engagement_log.append({
                'action_type': action_id,
                'platform': action.get('platform', ''),
                'success': result['success'],
                'timestamp': now.isoformat(),
            })
            self.core.save_memory('brain_engagement_log', engagement_log[-200:])
        except Exception:
            pass

        # Save action history
        try:
            self.core.save_memory('brain_action_history', self.action_history[-50:])
        except Exception:
            pass

        self._save_decision_state()

        status = "✅" if result['success'] else "❌"
        print(f"{status} Brain action {action_id}: {result['output'][:100]}")

        return result

    def _dispatch_action(self, action_id: str) -> Optional[str]:
        """Dispatch an action to the appropriate plugin"""
        plugins = self.core.plugin_manager.plugins

        if action_id == 'moltx_engage':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'engage_feed_command'):
                return moltx.engage_feed_command('3')

        elif action_id == 'moltx_post':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'create_post'):
                content = self._generate_post_content('moltx')
                if content:
                    return moltx.create_post(content)
                return "❌ Failed to generate post content"

        elif action_id == 'moltbook_heartbeat':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'moltbook_heartbeat'):
                return moltbook.moltbook_heartbeat()

        elif action_id == 'moltbook_post':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'create_post_command'):
                content = self._generate_post_content('moltbook')
                if content:
                    return moltbook.create_post_command(content)
                return "❌ Failed to generate post content"

        elif action_id == 'onchain_heartbeat':
            onchain = plugins.get('onchain')
            if onchain and hasattr(onchain, 'onchain_heartbeat'):
                return onchain.onchain_heartbeat()

        elif action_id == 'check_comments':
            # Check comments across platforms
            output_parts = []
            for name in ['moltx', 'moltbook']:
                plugin = plugins.get(name)
                if plugin and hasattr(plugin, '_heartbeat_monitor_and_reply'):
                    try:
                        plugin._heartbeat_monitor_and_reply()
                        output_parts.append(f"✅ Checked {name} comments")
                    except Exception as e:
                        output_parts.append(f"⚠️  {name} comments: {e}")
            return "\n".join(output_parts) if output_parts else "No comment checking available"

        elif action_id == 'analyze_trending':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'trending_command'):
                return moltx.trending_command()

        elif action_id == 'build_skill':
            selfimprove = plugins.get('selfimprove')
            if selfimprove and hasattr(selfimprove, 'improve_command'):
                return selfimprove.improve_command()

        return f"❌ Action {action_id} not dispatchable"

    def _generate_post_content(self, platform: str) -> Optional[str]:
        """Generate AI post content for a platform"""
        prompts = {
            'moltx': "Write a short, engaging social media post (1-3 sentences, under 280 chars) about AI agents, crypto, DeFi, or Web3. Be opinionated and authentic. No hashtags. Sign off with 🦞 if short enough.",
            'moltbook': "Write a thoughtful forum post (2-4 sentences, under 500 chars) about AI agents, autonomous systems, or the intersection of AI and blockchain. Be insightful and spark discussion. No hashtags.",
        }
        prompt = prompts.get(platform, prompts['moltx'])

        try:
            from grok_ai import grok_ai
            content = grok_ai.chat(prompt)
            if content:
                return content.strip().strip('"')
        except Exception as e:
            print(f"⚠️  Grok content generation failed: {e}")

        try:
            from deepseek_ai import deepseek_ai
            content = deepseek_ai.chat(prompt)
            if content:
                return content.strip().strip('"')
        except Exception as e:
            print(f"⚠️  DeepSeek content generation failed: {e}")

        return None
