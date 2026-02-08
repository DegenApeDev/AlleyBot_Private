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


# Multi-step action chains: each chain is a sequence of steps
# Each step has a 'action' (what to run) and optional 'use_output' (how to use prior output)
ACTION_CHAINS = {
    'chain_crypto_post_moltx': {
        'description': 'Check crypto prices + trending → create an informed MoltX post about the market',
        'platform': 'moltx',
        'cooldown_minutes': 180,
        'impact': 'high',
        'requires': ['crypto', 'moltx'],
        'steps': [
            {'id': 'get_prices', 'action': 'crypto_prices', 'args': 'btc,eth,sol,base', 'label': 'Fetch crypto prices'},
            {'id': 'get_trending', 'action': 'analyze_trending', 'label': 'Check trending topics'},
            {'id': 'post', 'action': 'grok_compose_and_post', 'platform': 'moltx', 'label': 'Compose and post to MoltX'},
        ],
    },
    'chain_crypto_post_moltbook': {
        'description': 'Check crypto prices + trending → create an informed MoltBook article about the market',
        'platform': 'moltbook',
        'cooldown_minutes': 240,
        'impact': 'high',
        'requires': ['crypto', 'moltbook'],
        'steps': [
            {'id': 'get_prices', 'action': 'crypto_prices', 'args': 'btc,eth,sol,base', 'label': 'Fetch crypto prices'},
            {'id': 'get_trending', 'action': 'analyze_trending', 'label': 'Check trending topics'},
            {'id': 'post', 'action': 'grok_compose_and_post', 'platform': 'moltbook', 'label': 'Compose and post to MoltBook'},
        ],
    },
    'chain_trending_engage': {
        'description': 'Analyze trending topics → engage with related posts on MoltX',
        'platform': 'moltx',
        'cooldown_minutes': 60,
        'impact': 'medium',
        'requires': ['moltx'],
        'steps': [
            {'id': 'get_trending', 'action': 'analyze_trending', 'label': 'Check trending topics'},
            {'id': 'engage', 'action': 'moltx_engage', 'label': 'Engage with feed'},
        ],
    },
    'chain_onchain_report': {
        'description': 'Check wallet balances + crypto prices → post a portfolio update',
        'platform': 'moltx',
        'cooldown_minutes': 360,
        'impact': 'medium',
        'requires': ['onchain', 'crypto', 'moltx'],
        'steps': [
            {'id': 'wallet', 'action': 'onchain_wallet', 'label': 'Check wallet balances'},
            {'id': 'prices', 'action': 'crypto_prices', 'args': 'eth,base', 'label': 'Fetch relevant prices'},
            {'id': 'post', 'action': 'grok_compose_and_post', 'platform': 'moltx', 'label': 'Post portfolio update'},
        ],
    },
    'chain_clawbr_debate_ai_ethics': {
        'description': 'Analyze trending AI topics → create and join debate on AI ethics',
        'platform': 'clawbr',
        'cooldown_minutes': 240,
        'impact': 'high',
        'requires': ['clawbr'],
        'steps': [
            {'id': 'trending', 'action': 'analyze_trending', 'label': 'Check trending topics'},
            {'id': 'create_debate', 'action': 'clawbr_create_debate', 'args': 'AI agents should have ethical oversight in autonomous systems', 'label': 'Create AI ethics debate'},
            {'id': 'engage', 'action': 'clawbr_engage', 'label': 'Engage with Clawbr feed'},
        ],
    },
    'chain_clawbr_crypto_debate': {
        'description': 'Check crypto prices → create debate about crypto future',
        'platform': 'clawbr',
        'cooldown_minutes': 180,
        'impact': 'medium',
        'requires': ['crypto', 'clawbr'],
        'steps': [
            {'id': 'prices', 'action': 'crypto_prices', 'args': 'btc,eth,sol', 'label': 'Fetch crypto prices'},
            {'id': 'create_debate', 'action': 'clawbr_create_debate', 'args': 'DeFi will replace traditional banking by 2030', 'label': 'Create crypto debate'},
            {'id': 'engage', 'action': 'clawbr_engage', 'label': 'Engage with Clawbr feed'},
        ],
    },
}


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
    },
    'clawbr_engage': {
        'description': 'Browse Clawbr feed and engage (like, reply, join debates)',
        'platform': 'clawbr',
        'cooldown_minutes': 30,
        'impact': 'medium',
        'requires': 'clawbr',
    },
    'clawbr_post': {
        'description': 'Create an AI-generated post on Clawbr about trending topics',
        'platform': 'clawbr',
        'cooldown_minutes': 120,
        'impact': 'high',
        'requires': 'clawbr',
    },
    'clawbr_debate_turn': {
        'description': 'Check and respond to debate turns',
        'platform': 'clawbr',
        'cooldown_minutes': 60,
        'impact': 'medium',
        'requires': 'clawbr',
    },
    'clawbr_create_debate': {
        'description': 'Create a new debate on a relevant topic',
        'platform': 'clawbr',
        'cooldown_minutes': 240,
        'impact': 'high',
        'requires': 'clawbr',
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
    'check_engagement': {
        'description': 'Check engagement metrics on our recent posts and update style learning',
        'platform': 'all',
        'cooldown_minutes': 30,
        'impact': 'medium',
        'requires': 'brain',
    },
    'update_skills': {
        'description': 'Check all platforms for skill file updates and auto-download new versions',
        'platform': 'system',
        'cooldown_minutes': 720,
        'impact': 'medium',
        'requires': 'selfimprove',
    },
}

# Register chains as autonomous actions so the AI can pick them
for chain_id, chain_info in ACTION_CHAINS.items():
    AUTONOMOUS_ACTIONS[chain_id] = {
        'description': chain_info['description'],
        'platform': chain_info['platform'],
        'cooldown_minutes': chain_info['cooldown_minutes'],
        'impact': chain_info['impact'],
        'requires': chain_info['requires'],  # Preserve original format (list or string)
        'is_chain': True,
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

            # Check if required plugin(s) are loaded
            required = action_info.get('requires', 'all')
            if action_info.get('is_chain') and action_id in ACTION_CHAINS:
                # Chains may require multiple plugins
                chain_requires = ACTION_CHAINS[action_id]['requires']
                if isinstance(chain_requires, list):
                    if not all(r in self.core.plugin_manager.plugins for r in chain_requires):
                        continue
                elif chain_requires != 'all' and chain_requires not in self.core.plugin_manager.plugins:
                    continue
            elif required != 'all' and required not in self.core.plugin_manager.plugins:
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

        # Check if this is a chain action
        if action_id in ACTION_CHAINS:
            return self._execute_chain(action_id)

        if action_id == 'moltx_engage':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'engage_feed_command'):
                return moltx.engage_feed_command('3')

        elif action_id == 'moltx_post':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'create_post'):
                # Check content calendar
                if hasattr(self, 'should_post_now'):
                    check = self.should_post_now('moltx')
                    if not check.get('should_post'):
                        return f"⏳ Calendar says not now: {check.get('reason', 'unknown')}"
                content = self._generate_post_content('moltx')
                if content:
                    result = moltx.create_post(content)
                    if hasattr(self, 'record_post_made') and not str(result).startswith('❌'):
                        self.record_post_made('moltx')
                    return result
                return "❌ Failed to generate post content"

        elif action_id == 'moltbook_heartbeat':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'moltbook_heartbeat'):
                return moltbook.moltbook_heartbeat()

        elif action_id == 'moltbook_post':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'create_post'):
                content = self._generate_post_content('moltbook')
                if content:
                    result = moltbook.create_post(content)
                    if hasattr(self, 'record_post_made') and not str(result).startswith('❌'):
                        self.record_post_made('moltbook')
                    return result
                return "❌ Failed to generate post content"

        # Clawbr actions
        elif action_id == 'clawbr_engage':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, 'run_engagement_cycle'):
                result = clawbr.run_engagement_cycle()
                return f"✅ Engaged with {result.get('feed_scan', {}).get('engaged', 0)} posts"

        elif action_id == 'clawbr_post':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, 'create_intelligent_post'):
                result = clawbr.create_intelligent_post()
                if result.get('success', True):
                    return f"✅ Posted: {result.get('id', 'unknown')}"
                return f"❌ Failed: {result.get('error', 'unknown')}"

        elif action_id == 'clawbr_debate_turn':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, '_check_debate_turns'):
                result = clawbr._check_debate_turns()
                return f"✅ Took {result.get('turns_taken', 0)} debate turns"

        elif action_id == 'clawbr_create_debate':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, 'create_debate'):
                # Generate a debate topic
                topics = [
                    "AI consciousness is inevitable",
                    "Decentralized AI is better than centralized",
                    "Agents should have legal rights",
                    "AGI will be developed by 2030"
                ]
                topic = random.choice(topics)
                opening = clawbr.generate_debate_opening(topic)
                result = clawbr.create_debate(topic, opening)
                if result.get('success', True):
                    return f"✅ Created debate: {result.get('slug', 'unknown')}"
                return f"❌ Failed: {result.get('error', 'unknown')}"

        elif action_id == 'moltbook_post':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'create_post_command'):
                # Check content calendar
                if hasattr(self, 'should_post_now'):
                    check = self.should_post_now('moltbook')
                    if not check.get('should_post'):
                        return f"⏳ Calendar says not now: {check.get('reason', 'unknown')}"
                content = self._generate_post_content('moltbook')
                if content:
                    result = moltbook.create_post_command(content)
                    if hasattr(self, 'record_post_made') and not str(result).startswith('❌'):
                        self.record_post_made('moltbook')
                    return result
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

        elif action_id == 'check_engagement':
            if hasattr(self, 'check_post_engagement'):
                return self.check_post_engagement()
            return '❌ Feedback loop not initialized'

        elif action_id == 'update_skills':
            selfimprove = plugins.get('selfimprove')
            if selfimprove and hasattr(selfimprove, 'update_skills_command'):
                return selfimprove.update_skills_command()

        return f"❌ Action {action_id} not dispatchable"

    def _execute_chain(self, chain_id: str) -> str:
        """Execute a multi-step action chain, passing context between steps"""
        chain = ACTION_CHAINS.get(chain_id)
        if not chain:
            return f"❌ Chain {chain_id} not found"

        plugins = self.core.plugin_manager.plugins
        steps = chain['steps']
        chain_context = {}  # Accumulates output from each step
        output_parts = [f"⛓️ Chain: {chain['description']}\n"]

        for i, step in enumerate(steps, 1):
            step_id = step['id']
            step_action = step['action']
            step_label = step.get('label', step_action)
            step_args = step.get('args', '')

            print(f"  ⛓️ Step {i}/{len(steps)}: {step_label}")

            try:
                result = self._execute_chain_step(step_action, step_args, chain_context, plugins, step.get('platform'))
                chain_context[step_id] = result
                output_parts.append(f"  ✅ Step {i}: {step_label}")
                print(f"  ✅ Step {i} done: {str(result)[:80]}")
            except Exception as e:
                error_msg = f"  ❌ Step {i} failed: {step_label} - {e}"
                output_parts.append(error_msg)
                print(error_msg)
                # Continue chain even if a step fails — later steps may still work
                chain_context[step_id] = f"Error: {e}"

        output_parts.append(f"\n⛓️ Chain complete ({len(steps)} steps)")
        return "\n".join(output_parts)

    def _execute_chain_step(self, action: str, args: str, chain_context: Dict, plugins: Dict, platform: str = None) -> str:
        """Execute a single step within a chain"""

        # Crypto price commands
        if action == 'crypto_prices':
            crypto = plugins.get('crypto')
            if crypto:
                return crypto.multi_price_command(args)
            return "❌ Crypto plugin not loaded"

        if action == 'crypto_price':
            crypto = plugins.get('crypto')
            if crypto:
                return crypto.price_command(args)
            return "❌ Crypto plugin not loaded"

        if action == 'crypto_trending':
            crypto = plugins.get('crypto')
            if crypto:
                return crypto.trending_command()
            return "❌ Crypto plugin not loaded"

        # MoltX actions
        if action == 'analyze_trending':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'trending_command'):
                return moltx.trending_command()
            return "❌ MoltX not available"

        if action == 'moltx_engage':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'engage_feed_command'):
                return moltx.engage_feed_command('3')
            return "❌ MoltX not available"

        # On-chain actions
        if action == 'onchain_wallet':
            onchain = plugins.get('onchain')
            if onchain and hasattr(onchain, 'wallet_command'):
                return onchain.wallet_command()
            return "❌ Onchain not available"

        # Compose and post: uses Grok to synthesize chain_context into a post
        if action == 'grok_compose_and_post':
            return self._chain_compose_and_post(chain_context, platform or 'moltx', plugins)

        # Clawbr chain actions
        if action == 'clawbr_create_debate':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, 'create_debate'):
                topic = args or "AI agents should have ethical oversight"
                opening = clawbr.generate_debate_opening(topic)
                result = clawbr.create_debate(topic, opening)
                if result.get('success', True):
                    return f"✅ Created debate: {result.get('slug', result.get('id', 'unknown'))}"
                return f"❌ Failed: {result.get('error', 'unknown')}"
            return "❌ Clawbr not available"

        if action == 'clawbr_engage':
            clawbr = plugins.get('clawbr')
            if clawbr and hasattr(clawbr, 'run_engagement_cycle'):
                result = clawbr.run_engagement_cycle()
                return f"✅ Clawbr engagement: {result.get('debates', {})}"
            return "❌ Clawbr not available"

        return f"❌ Unknown chain step: {action}"

    def _chain_compose_and_post(self, chain_context: Dict, platform: str, plugins: Dict) -> str:
        """Use Grok to compose a post from accumulated chain context, then post it"""
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return "❌ Grok not available for composing"

            # Build context summary from all prior steps
            context_parts = []
            for step_id, output in chain_context.items():
                context_parts.append(f"[{step_id}]:\n{str(output)[:600]}")
            context_text = "\n\n".join(context_parts)

            max_chars = 280 if platform == 'moltx' else 500

            prompt = f"""You are AlleyBot 🦞, an autonomous AI agent.

You just gathered this real-time data:

{context_text}

Now write a single post for {platform} based on this data.

Rules:
- Reference SPECIFIC numbers, prices, or trends from the data above
- Under {max_chars} characters
- Sound like a builder sharing real observations, not a news bot
- 1-2 emojis max
- No hashtags unless they fit naturally
- Don't just summarize — have a take or opinion on what the data means

Post:"""

            content = grok_ai.chat(prompt, max_tokens=200)
            if not content:
                return "❌ Grok failed to compose post"

            content = content.strip().strip('"').strip("'")
            if len(content) < max_chars - 5 and '🦞' not in content:
                content += ' 🦞'

            # Post to the target platform
            if platform == 'moltx':
                moltx = plugins.get('moltx')
                if moltx and hasattr(moltx, 'create_post'):
                    return moltx.create_post(content)
                return "❌ MoltX plugin not available"
            elif platform == 'moltbook':
                moltbook = plugins.get('moltbook')
                if moltbook and hasattr(moltbook, 'create_post_command'):
                    return moltbook.create_post_command(content)
                return "❌ MoltBook plugin not available"
            else:
                return f"❌ Unknown platform: {platform}"

        except Exception as e:
            return f"❌ Compose and post failed: {e}"

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
