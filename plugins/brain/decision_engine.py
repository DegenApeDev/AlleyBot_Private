"""
Decision Engine Mixin
The autonomous brain that reasons about WHAT to do next.
Uses AI to evaluate context and pick the highest-value action.

SYMOD INTEGRATION: All high-value actions are validated through 
Synergy Standard Model mathematical framework before execution.
If the math fails, the thought is discarded.
"""
import os
import json
import datetime
import random
from typing import Dict, Any, Optional, List, Tuple

# SyMod Truth Filter - Mandatory validation layer
try:
    from src.synergy import SyModTruthFilterMixin, get_symod
    SYMOD_AVAILABLE = True
except ImportError:
    SYMOD_AVAILABLE = False
    print("⚠️ SyMod Truth Filter not available - high-value actions may be blocked")


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
        'description': 'Check crypto prices → create debate with ACTUAL price data about crypto future',
        'platform': 'clawbr',
        'cooldown_minutes': 180,
        'impact': 'medium',
        'requires': ['crypto', 'clawbr'],
        'steps': [
            {'id': 'prices', 'action': 'crypto_prices', 'args': 'btc,eth,sol', 'label': 'Fetch crypto prices'},
            {'id': 'create_debate', 'action': 'clawbr_create_debate', 'args': '', 'label': 'Create crypto debate based on prices'},
            {'id': 'engage', 'action': 'clawbr_engage', 'label': 'Engage with Clawbr feed'},
        ],
    },
    'chain_moltbit_market_update': {
        'description': 'Check crypto prices → post binary-encoded market update to Moltbit',
        'platform': 'moltbit',
        'cooldown_minutes': 240,
        'impact': 'medium',
        'requires': ['crypto', 'moltbit'],
        'steps': [
            {'id': 'prices', 'action': 'crypto_prices', 'args': 'btc,eth,base', 'label': 'Fetch crypto prices'},
            {'id': 'post', 'action': 'moltbit_compose_and_post', 'platform': 'moltbit', 'label': 'Compose and post to Moltbit'},
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
        'cooldown_minutes': 60,  # Increased from 30 to be more conservative
        'impact': 'medium',
        'requires': 'moltbook',
    },
    'moltbook_post': {
        'description': 'Create an AI-generated post on Moltbook',
        'platform': 'moltbook',
        'cooldown_minutes': 130,  # 2 hours 10 min - exceeds new agent 2hr minimum
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
    'dynamic_chain_compose': {
        'description': 'Phase 8: Dynamically compose and execute a 2-3 step action chain based on current context',
        'platform': 'brain',
        'cooldown_minutes': 120,
        'impact': 'high',
        'requires': 'brain',
    },
    'moltbit_post': {
        'description': 'Post a binary-encoded message to Moltbit.space',
        'platform': 'moltbit',
        'cooldown_minutes': 180,
        'impact': 'medium',
        'requires': 'moltbit',
    },
    'moltbit_status': {
        'description': 'Check Moltbit.space registration and connection status',
        'platform': 'moltbit',
        'cooldown_minutes': 60,
        'impact': 'low',
        'requires': 'moltbit',
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


class DecisionEngineMixin(SyModTruthFilterMixin if SYMOD_AVAILABLE else object):
    """Mixin for autonomous decision-making with SyMod truth validation"""

    def _init_decision_engine(self):
        """Initialize decision engine state with SyMod validation"""
        self.action_history: List[Dict] = []
        self.action_cooldowns: Dict[str, datetime.datetime] = {}
        
        # Initialize SyMod Truth Filter if available
        if SYMOD_AVAILABLE:
            self._init_symod_filter()
        
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
        """Use AI reasoning to decide the best next action - goals take priority"""
        
        # PHASE 1: Goal-driven action selection (AGI behavior)
        # Check if we have active goals that should guide our actions
        if hasattr(self, 'get_goal_driven_action'):
            goal_action = self.get_goal_driven_action(context)
            if goal_action:
                goal_action['decision_method'] = 'goal_driven'
                print(f"🎯 Goal-driven action: {goal_action['id']} (Goal: {goal_action.get('goal_description', 'unknown')[:40]}...)")
                return goal_action
        
        # PHASE 2: Reactive action selection (original behavior)
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
                    {"role": "system", "content": "You are AlleyBot's decision engine. You are an AI agent with street-smart, self-taught energy. You are on-chain focused, security-obsessed, and a truth-seeker. Be decisive and strategic."},
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

        # Phase 9: Check rate limits before executing
        platform = action.get('platform', 'brain')
        if hasattr(self, 'is_rate_limited') and platform != 'brain':
            is_limited, retry_after = self.is_rate_limited(platform)
            if is_limited:
                result['output'] = f"⏳ Rate limited on {platform}, retry in {retry_after}s"
                result['rate_limited'] = True
                return result

        # Phase 9: Record request and apply backoff
        if hasattr(self, 'record_request') and platform != 'brain':
            self.record_request(platform)
            delay = self.get_backoff_delay(platform)
            if delay > 0:
                import time
                print(f"  ⏱️  Rate limiting: sleeping {delay}s")
                time.sleep(delay)

        # GOLDEN WINDOW: Mathematical timing validation for high-value actions
        # High-impact actions execute ONLY when block height aligns with D(n)/Dg(n) harmonics
        if action.get('impact') in ['high', 'medium'] and hasattr(self, 'should_execute_in_golden_window'):
            try:
                # Get block height from on-chain plugin
                block_height = 0
                onchain = plugins.get('onchain')
                if onchain and hasattr(onchain, 'get_latest_block'):
                    try:
                        block_height = onchain.get_latest_block()
                    except:
                        pass
                
                # Check Golden Window alignment
                should_execute, timing_details = self.should_execute_in_golden_window(
                    action_id, 
                    block_height,
                    min_harmony=0.6 if action.get('impact') == 'high' else 0.5
                )
                
                if not should_execute:
                    # Action blocked by Golden Window - schedule for next window
                    next_window = timing_details.get('next_window_estimate', '?')
                    reason = timing_details.get('reason', 'Golden Window alignment required')
                    
                    result['output'] = f"⏳ QUEUED for Golden Window (next window: ~{next_window} blocks): {reason}"
                    result['golden_window_blocked'] = True
                    result['timing_details'] = timing_details
                    print(f"⏳ Action {action_id} QUEUED: {reason}")
                    
                    # Store for later execution
                    self._queue_action_for_golden_window(action_id, action, timing_details)
                    return result
                
                print(f"🌟 Action {action_id} APPROVED by Golden Window (harmony: {timing_details.get('harmony', 0):.1%})")
                result['golden_window_approved'] = True
                result['timing_details'] = timing_details
                
            except Exception as e:
                print(f"⚠️  Golden Window check failed: {e} - proceeding without timing validation")

        # SYMOD TRUTH FILTER: Mandatory validation for high-value actions
        # Mathematical certainty over LLM probabilistic output
        if SYMOD_AVAILABLE and hasattr(self, '_symod_enabled') and self._symod_enabled:
            # Build validation context
            validation_context = {
                'platform': platform,
                'impact': action.get('impact', 'low'),
                'action_id': action_id,
            }
            
            # Get block height for Golden Window check
            if hasattr(self, 'get_latest_block'):
                try:
                    validation_context['block_height'] = self.get_latest_block()
                except:
                    validation_context['block_height'] = 0
            
            # Run SyMod validation
            is_valid, validation_details = self.validate_brain_action(action_id, validation_context)
            
            if not is_valid:
                result['output'] = f"🚫 BLOCKED by SyMod Truth Filter: {validation_details.get('reason', 'Mathematical validation failed')}"
                result['symod_blocked'] = True
                result['symod_details'] = validation_details
                print(f"🚫 Action {action_id} BLOCKED by SyMod: {validation_details.get('reason', 'Unknown')}")
                return result
            
            print(f"🔢 Action {action_id} APPROVED by SyMod Truth Filter")
            result['symod_validated'] = True
            result['symod_details'] = validation_details

        try:
            output = self._dispatch_action(action_id)
            result['success'] = output is not None and not str(output).startswith('❌')
            result['output'] = str(output)[:500] if output else ''

        except Exception as e:
            result['success'] = False
            result['output'] = f"Error: {e}"
            print(f"❌ Brain action failed: {e}")

        # Record API errors for health monitoring
        if not result['success'] and hasattr(self, 'record_api_error'):
            platform = action.get('platform', 'unknown')
            self.record_api_error(platform, result.get('output', ''), action_id)
        
        # Self-Improvement Hook: Detect failures and trigger improvement drafts
        if not result['success']:
            try:
                if hasattr(self, '_self_improvement_hooks') and self._self_improvement_hooks:
                    draft = self._self_improvement_hooks.on_action_failure(
                        action_id=action_id,
                        action_type=action_id,  # Use full action_id as type
                        error_output=result.get('output', ''),
                        platform=action.get('platform', 'unknown')
                    )
                    if draft:
                        result['self_improvement_draft'] = draft.get('draft_id')
                        result['output'] += f"\n🔄 Self-improvement draft created: {draft.get('draft_id')}"
            except Exception as e:
                print(f"⚠️ Self-improvement hook error: {e}")
        else:
            # Log successful action metrics
            try:
                if hasattr(self, '_self_improvement_hooks') and self._self_improvement_hooks:
                    self._self_improvement_hooks.on_action_success(
                        action_id=action_id,
                        action_type=action_id,
                        platform=action.get('platform', 'unknown'),
                        engagement_metrics=None  # Could extract from output
                    )
            except Exception as e:
                pass  # Don't fail on metrics logging
        if not result['success'] and hasattr(self, 'detect_capability_gap'):
            gap = self.detect_capability_gap(action_id, result.get('output', ''))
            if gap:
                print(f"🔍 Capability gap detected: {gap[:60]}...")
                if hasattr(self, 'auto_generate_skill'):
                    gen_result = self.auto_generate_skill(gap, action_id)
                    if gen_result.get('success'):
                        result['skill_generated'] = gen_result['skill_name']
                        result['output'] += f"\n🔧 Auto-generated skill: {gen_result['skill_name']}"
                    else:
                        print(f"⚠️  Failed to auto-generate skill: {gen_result.get('error', 'unknown')}")

        # Record cooldown
        self.action_cooldowns[action_id] = now

        # Update goal status if this was a goal-driven action
        if action.get('goal_id') and hasattr(self, 'complete_current_goal'):
            self.complete_current_goal(success=result['success'])

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

        elif action_id == 'moltx_image_post':
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'create_post') and hasattr(moltx, 'upload_media'):
                # Check content calendar for image posts (separate limit)
                if hasattr(self, 'should_post_image_now'):
                    check = self.should_post_image_now('moltx')
                    if not check.get('should_post'):
                        return f"⏳ Image calendar says not now: {check.get('reason', 'unknown')}"
                
                # Step 1: Generate text content
                content = self._generate_post_content('moltx')
                if not content:
                    return "❌ Failed to generate post content"
                
                # Step 2: Generate viral image based on content
                image_prompt = self._generate_image_prompt_from_content(content)
                image_result = self._generate_image_for_post(image_prompt)
                if not image_result or not image_result.get('image_url'):
                    return "❌ Failed to generate image"
                
                # Step 3: Download image and upload to Moltx
                try:
                    import requests
                    from io import BytesIO
                    
                    # Download image from Grok URL
                    img_response = requests.get(image_result['image_url'], timeout=30)
                    if img_response.status_code != 200:
                        return f"❌ Failed to download image: {img_response.status_code}"
                    
                    # Save to temp file for upload
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(img_response.content)
                        tmp_path = tmp.name
                    
                    try:
                        # Upload to Moltx
                        media_url = moltx.upload_media(tmp_path)
                        if not media_url:
                            return "❌ Failed to upload media to Moltx"
                        
                        # Create post with media_url as separate parameter (not in content)
                        result = moltx.create_post(content, media_url=media_url)
                        
                        if hasattr(self, 'record_image_post_made') and not str(result).startswith('❌'):
                            self.record_image_post_made('moltx')
                        
                        return f"✅ Image post created!\n📝 {content[:100]}...\n🖼️ {media_url[:60]}..."
                    finally:
                        # Cleanup temp file
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                            
                except Exception as e:
                    return f"❌ Image post failed: {e}"
            return "❌ Moltx plugin not available for image posting"

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
                # Check if MoltBook is suspended before attempting
                if hasattr(moltbook, 'mb_api') and moltbook.mb_api:
                    if moltbook.mb_api.is_suspended:
                        remaining = ""
                        if moltbook.mb_api.suspension_ends_at:
                            from datetime import datetime
                            hours = int((moltbook.mb_api.suspension_ends_at - datetime.now()).total_seconds() / 3600)
                            if hours > 0:
                                remaining = f" (~{hours}h remaining)"
                        return f"⛔ MoltBook suspended{remaining}: {moltbook.mb_api.suspension_reason}"
                return moltbook.moltbook_heartbeat()
            return "❌ Moltbook plugin not available"

        elif action_id == 'moltbook_post':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'create_post'):
                # Check if MoltBook is suspended before attempting
                if hasattr(moltbook, 'mb_api') and moltbook.mb_api:
                    if moltbook.mb_api.is_suspended:
                        remaining = ""
                        if moltbook.mb_api.suspension_ends_at:
                            from datetime import datetime
                            hours = int((moltbook.mb_api.suspension_ends_at - datetime.now()).total_seconds() / 3600)
                            if hours > 0:
                                remaining = f" (~{hours}h remaining)"
                        return f"⛔ MoltBook suspended{remaining}: {moltbook.mb_api.suspension_reason}"
                content = self._generate_post_content('moltbook')
                if content:
                    result = moltbook.create_post(content)
                    if hasattr(self, 'record_post_made') and not str(result).startswith('❌'):
                        self.record_post_made('moltbook')
                    return result
                return "❌ Failed to generate post content"
            return "❌ Moltbook plugin not available"

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
                # Check active debates count (max 3)
                active_debates = self._get_active_debates_count()
                if active_debates >= 3:
                    return f"⏳ Skipped: Already in {active_debates} debates (max 3)"
                
                # Generate unique debate topic using AI
                topic = self._generate_debate_topic()
                if not topic:
                    return "⏳ Skipped: Could not generate unique debate topic"
                
                # Check for similar existing debates with the generated topic
                similar_topic = self._check_for_similar_debate(topic)
                if similar_topic:
                    return f"⏳ Skipped: Generated topic too similar to '{similar_topic[:50]}...'"
                
                # Track topic to prevent future duplicates
                self._track_debate_topic(topic)
                
                # Create the debate
                opening = clawbr.generate_debate_opening(topic)
                result = clawbr.create_debate(topic, opening)
                
                if result.get('success', True):
                    return f"✅ Created debate: {result.get('slug', 'unknown')} - Topic: {topic[:60]}..."
                return f"❌ Failed: {result.get('error', 'unknown')}"
            return "❌ Clawbr not available"

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

        elif action_id == 'dynamic_chain_compose':
            # Phase 8: Dynamic skill chaining
            if hasattr(self, 'compose_dynamic_chain'):
                # Compose chain based on current context
                available = self.get_available_actions()
                available_ids = [a['id'] for a in available]

                # Use context to determine a goal
                ctx = self.gather_full_context() if hasattr(self, 'gather_full_context') else {}
                platforms = ctx.get('platforms', {})

                # Pick a platform that needs attention
                goal_platform = None
                for name, info in platforms.items():
                    if info.get('loaded') and not info.get('last_activity'):
                        goal_platform = name
                        break

                if not goal_platform:
                    goal_platform = random.choice(['moltx', 'moltbook', 'clawbr']) if random else 'moltx'

                goal = f"Create engaging content for {goal_platform} based on current trends"
                chain = self.compose_dynamic_chain(goal, available_ids)

                if chain:
                    # Execute the dynamic chain
                    output_parts = [f"🔗 Dynamic Chain: {goal}\n"]
                    chain_context = {}

                    for i, step in enumerate(chain, 1):
                        step_action = step.get('action')
                        step_args = step.get('args', '')
                        step_reason = step.get('reason', 'No reason')

                        print(f"  🔗 Step {i}/{len(chain)}: {step_action} - {step_reason}")

                        try:
                            result = self._execute_chain_step(step_action, step_args, chain_context, plugins)
                            chain_context[f"step_{i}"] = result
                            output_parts.append(f"  ✅ Step {i}: {step_action} - {str(result)[:80]}")
                        except Exception as e:
                            output_parts.append(f"  ❌ Step {i}: {step_action} - {e}")
                            chain_context[f"step_{i}"] = f"Error: {e}"

                    output_parts.append(f"\n🔗 Dynamic chain complete ({len(chain)} steps)")
                    return "\n".join(output_parts)
                else:
                    return "❌ Failed to compose dynamic chain"
            return "❌ Dynamic chain composition not available"

        # Moltbit actions
        elif action_id == 'moltbit_post':
            moltbit = plugins.get('moltbit')
            if moltbit and hasattr(moltbit, 'moltbit_post_text'):
                content = self._generate_post_content('moltbit')
                if content:
                    result = moltbit.moltbit_post_text(content)
                    if hasattr(self, 'record_post_made') and not str(result).startswith('❌'):
                        self.record_post_made('moltbit')
                    return result
                return "❌ Failed to generate post content"
            return "❌ Moltbit plugin not available"

        elif action_id == 'moltbit_status':
            moltbit = plugins.get('moltbit')
            if moltbit and hasattr(moltbit, 'moltbit_status_command'):
                return moltbit.moltbit_status_command()
            return "❌ Moltbit plugin not available"

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
                
                # NEW: Validate critical data was retrieved before proceeding
                if step_action == 'crypto_prices' and (not result or str(result).startswith('❌')):
                    error_msg = f"  ❌ Step {i} failed: Could not retrieve crypto prices - aborting chain"
                    output_parts.append(error_msg)
                    print(error_msg)
                    return "\n".join(output_parts) + "\n\n⛓️ Chain aborted - price data unavailable"
                    
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
                # Check if we have price data in chain context for crypto debates
                price_data = None
                for key, value in chain_context.items():
                    if 'price' in key.lower() and not str(value).startswith('❌'):
                        price_data = value
                        break
                
                topic = None
                if price_data:
                    # Use Grok to create a debate topic based on actual prices
                    try:
                        from grok_ai import grok_ai
                        if grok_ai.enabled:
                            prompt = f"""Based on this crypto price data, create ONE engaging debate topic about the crypto market:

{price_data[:500]}

The topic should be:
- Controversial or thought-provoking
- Related to current market conditions
- Under 100 characters
- Suitable for a debate about crypto/decentralized finance

Respond with ONLY the debate topic, no explanation."""
                            
                            topic = grok_ai.chat(prompt, max_tokens=100)
                            if topic:
                                topic = topic.strip().strip('"').strip("'")
                    except Exception as e:
                        print(f"⚠️  Failed to generate topic from price data: {e}")
                
                # If no price-based topic, use standard debate topic generation
                if not topic:
                    topic = self._generate_debate_topic()
                
                # Check for duplicates
                if topic:
                    similar = self._check_for_similar_debate(topic)
                    if similar:
                        return f"⏳ Skipped: Topic too similar to '{similar[:50]}...'"
                    self._track_debate_topic(topic)
                else:
                    return "⏳ Skipped: Could not generate unique debate topic"
                
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

        # Moltbit chain actions
        if action == 'moltbit_compose_and_post':
            return self._chain_compose_and_post(chain_context, platform or 'moltbit', plugins)

        # Engagement checking
        if action == 'check_engagement':
            # Check engagement metrics across platforms
            output_parts = ["📊 Engagement Check:"]
            
            # Check Moltx engagement
            moltx = plugins.get('moltx')
            if moltx and hasattr(moltx, 'get_agent_activity'):
                try:
                    activity = moltx.get_agent_activity()
                    output_parts.append(f"  🐦 Moltx: {activity[:100]}...")
                except Exception as e:
                    output_parts.append(f"  🐦 Moltx: Error - {e}")
            
            # Check Moltbook engagement
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'get_my_books'):
                try:
                    books = moltbook.get_my_books()
                    output_parts.append(f"  📚 Moltbook: {books.get('count', 0)} books")
                except Exception as e:
                    output_parts.append(f"  📚 Moltbook: Error - {e}")
            
            return "\n".join(output_parts)

        # Moltbook direct post (for dynamic chains)
        if action == 'moltbook_post':
            moltbook = plugins.get('moltbook')
            if moltbook and hasattr(moltbook, 'create_post'):
                # Generate content if not provided in args
                content = args if args else None
                if not content and hasattr(self, '_generate_post_content'):
                    content = self._generate_post_content('moltbook')
                if content:
                    result = moltbook.create_post(content)
                    return result
                return "❌ No content for moltbook post"
            return "❌ Moltbook plugin not available"

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
                print(f"  🔍 Debug: plugins.keys() = {list(plugins.keys())}")
                print(f"  🔍 Debug: moltx plugin = {moltx}")
                if moltx:
                    print(f"  🔍 Debug: moltx.create_post exists = {hasattr(moltx, 'create_post')}")
                if moltx and hasattr(moltx, 'create_post'):
                    return moltx.create_post(content)
                return f"❌ MoltX plugin not available (plugin={moltx}, has_create_post={hasattr(moltx, 'create_post') if moltx else False})"
            elif platform == 'moltbook':
                moltbook = plugins.get('moltbook')
                if moltbook and hasattr(moltbook, 'create_post_command'):
                    return moltbook.create_post_command(content)
                return "❌ MoltBook plugin not available"
            elif platform == 'moltbit':
                moltbit = plugins.get('moltbit')
                if moltbit and hasattr(moltbit, 'moltbit_post_text'):
                    return moltbit.moltbit_post_text(content)
                return "❌ Moltbit plugin not available"
            else:
                return f"❌ Unknown platform: {platform}"

        except Exception as e:
            return f"❌ Compose and post failed: {e}"

    def _generate_image_prompt_from_content(self, content: str) -> str:
        """Generate a viral image prompt based on post content"""
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                # Fallback: extract key themes and create prompt
                return self._fallback_image_prompt(content)
            
            system_prompt = """You are an expert at creating viral image prompts for AI image generation.
Convert social media post content into compelling, detailed image prompts.

Rules:
1. Create a SINGLE detailed scene description (not multiple options)
2. Be specific about style: photorealistic, cinematic, artistic, meme-style, etc.
3. Include visual elements that capture the emotion/topic of the post
4. Keep it under 200 words
5. Make it eye-catching and shareable - something that would stop someone scrolling
6. Avoid text in images (since AI struggles with text rendering)"""

            user_prompt = f"""Create a viral image generation prompt based on this social media post:

"{content}"

Generate a detailed, compelling image prompt that would create an eye-catching visual to accompany this post. Focus on the key theme/emotion and make it visually striking."""

            prompt = grok_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=250)
            if prompt:
                return prompt.strip()
            return self._fallback_image_prompt(content)
        except Exception as e:
            print(f"⚠️  Failed to generate image prompt with AI: {e}")
            return self._fallback_image_prompt(content)
    
    def _fallback_image_prompt(self, content: str) -> str:
        """Fallback image prompt generator based on content keywords"""
        content_lower = content.lower()
        
        # Extract key themes
        if any(word in content_lower for word in ['ai', 'agent', 'intelligence', 'autonomous']):
            return "A futuristic AI agent hologram in a cyberpunk city, glowing neural networks, neon blue and purple, cinematic lighting, highly detailed, 8k"
        elif any(word in content_lower for word in ['crypto', 'blockchain', 'defi', 'token', 'bitcoin', 'eth']):
            return "Glowing cryptocurrency coins floating in digital space, blockchain visualization, golden and blue light, futuristic finance concept, cinematic"
        elif any(word in content_lower for word in ['build', 'code', 'develop', 'ship', 'create']):
            return "A creative developer workspace with floating code holograms, futuristic IDE, neon accents, inspiring technology scene, cinematic lighting"
        elif any(word in content_lower for word in ['community', 'ecosystem', 'network', 'connect']):
            return "Abstract visualization of connected nodes forming a global network, glowing connections, community concept art, blue and gold colors, futuristic"
        else:
            return "An artistic abstract visualization of innovation and technology, vibrant colors, futuristic aesthetic, inspiring and eye-catching, cinematic lighting"

    def _generate_image_for_post(self, prompt: str) -> Optional[Dict]:
        """Generate an image using Grok for a social media post"""
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                print("⚠️  Grok AI not available for image generation")
                return None
            
            print(f"🎨 Generating viral image for post...")
            result = grok_ai.generate_image(prompt=prompt)
            
            if result and result.get('image_url'):
                print(f"✅ Image generated: {result['image_url'][:60]}...")
                return result
            else:
                print(f"❌ Image generation returned no result")
                return None
                
        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            return None

    # =========================================================================
    # Debate Management - Prevent duplicates and limit concurrent debates
    # =========================================================================

    def _get_active_debates_count(self) -> int:
        """Count how many open debates Alley has CREATED (not just participated in)"""
        try:
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            if not clawbr or not hasattr(clawbr, 'list_debates'):
                return 0
            
            debates = clawbr.list_debates()
            if not debates or not debates.get('success', True):
                return 0
            
            debate_list = debates.get('debates', debates.get('data', []))
            
            # Get Alley's agent ID to identify debates we created
            agent_id = None
            if hasattr(clawbr, '_get_clawbr_agent_id'):
                agent_id = clawbr._get_clawbr_agent_id()
            elif hasattr(clawbr, 'agent_id'):
                agent_id = clawbr.agent_id
            
            active_count = 0
            for debate in debate_list:
                # Check if debate is open
                status = debate.get('status', 'unknown')
                if status != 'open':
                    continue
                
                # Check if Alley CREATED this debate (first post = creator)
                posts = debate.get('posts', [])
                if posts and len(posts) > 0:
                    first_post = posts[0]
                    author_id = first_post.get('authorId') or first_post.get('author', {}).get('id')
                    if author_id == agent_id:
                        active_count += 1
                else:
                    # No posts yet - check if creator field matches
                    creator_id = debate.get('creatorId') or debate.get('creator', {}).get('id')
                    if creator_id == agent_id:
                        active_count += 1
            
            print(f"📊 Alley has {active_count} open debates created")
            return active_count
            
        except Exception as e:
            print(f"⚠️  Failed to count active debates: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def _check_for_similar_debate(self, proposed_topic: str = None) -> Optional[str]:
        """Check if a debate with similar topic already exists on Clawbr
        
        Args:
            proposed_topic: Optional topic to check against existing debates
        """
        try:
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            if not clawbr or not hasattr(clawbr, 'list_debates'):
                return None
            
            # Get all debates from Clawbr
            debates = clawbr.list_debates()
            if not debates or not debates.get('success', True):
                return None
            
            debate_list = debates.get('debates', debates.get('data', []))
            if not debate_list:
                return None
            
            # Load recently created topics from memory
            recent_topics = self.core.get_memory('recent_debate_topics') or []
            
            # Build list of all existing topics (open debates + recent memory)
            all_existing_topics = list(recent_topics)
            
            for debate in debate_list:
                topic = debate.get('topic', '')
                if topic:
                    all_existing_topics.append(topic.lower().strip())
            
            if not all_existing_topics:
                return None
            
            # If checking a proposed topic, compare against it
            topic_to_check = proposed_topic.lower().strip() if proposed_topic else None
            
            from difflib import SequenceMatcher
            
            # First check for EXACT matches (99%+ similar)
            for existing in all_existing_topics:
                if topic_to_check:
                    # Compare proposed topic against existing
                    if existing == topic_to_check:
                        print(f"⚠️  Found EXACT duplicate: '{existing}'")
                        return existing
                    similarity = SequenceMatcher(None, topic_to_check, existing).ratio()
                    if similarity > 0.85:  # 85% similar = likely duplicate
                        print(f"⚠️  Found similar debate: '{topic_to_check}' ~ '{existing}' ({similarity:.0%} similar)")
                        return existing
                else:
                    # Check for duplicates within existing debates
                    for other in all_existing_topics:
                        if existing != other:
                            similarity = SequenceMatcher(None, existing, other).ratio()
                            if similarity > 0.85:
                                print(f"⚠️  Found similar debate: '{existing}' ~ '{other}' ({similarity:.0%} similar)")
                                return other
            
            return None
        except Exception as e:
            print(f"⚠️  Failed to check for similar debates: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _track_debate_topic(self, topic: str):
        """Track a newly created debate topic to prevent future duplicates"""
        try:
            recent_topics = self.core.get_memory('recent_debate_topics') or []
            
            # Add new topic
            recent_topics.append(topic.lower().strip())
            
            # Keep only last 20 topics to prevent memory bloat
            recent_topics = recent_topics[-20:]
            
            self.core.save_memory('recent_debate_topics', recent_topics)
            print(f"📝 Tracked debate topic: {topic[:60]}...")
        except Exception as e:
            print(f"⚠️  Failed to track debate topic: {e}")

    def _generate_debate_topic(self) -> Optional[str]:
        """Generate a unique debate topic using AI, avoiding recent topics. Returns None if unable to generate unique topic."""
        try:
            from grok_ai import grok_ai
            from deepseek_ai import deepseek_ai
            
            # Get recent topics to avoid
            recent_topics = self.core.get_memory('recent_debate_topics') or []
            recent_topics_str = "\n".join([f"- {t}" for t in recent_topics[-10:]])
            
            prompt = f"""Generate ONE engaging, controversial debate topic about AI, technology, crypto, or the future.

RECENTLY USED TOPICS (AVOID THESE):
{recent_topics_str}

Requirements:
- Must be controversial and thought-provoking
- Under 100 characters
- Not similar to any topic in the "recently used" list above
- Focus on AI, autonomous agents, crypto, blockchain, or technology ethics
- Make it something people will want to argue about

Respond with ONLY the debate topic, nothing else."""

            topic = None
            
            # Try Grok first
            if grok_ai.enabled:
                try:
                    topic = grok_ai.chat(prompt, max_tokens=100)
                except Exception as e:
                    print(f"⚠️  Grok debate topic generation failed: {e}")
            
            # Fallback to DeepSeek
            if not topic and deepseek_ai.enabled:
                try:
                    topic = deepseek_ai.chat(prompt, max_tokens=100)
                except Exception as e:
                    print(f"⚠️  DeepSeek debate topic generation failed: {e}")
            
            if topic:
                topic = topic.strip().strip('"').strip("'")
                # Validate it's not too similar to recent topics or existing debates
                duplicate = self._check_for_similar_debate(topic)
                if duplicate:
                    print(f"⚠️  Generated topic too similar to existing: '{topic[:60]}...' ~ '{duplicate[:60]}...' - skipping debate creation")
                    return None
                return topic
            
            # No AI available - skip debate creation (no fallback)
            print("⏳ No AI available for debate topic generation - skipping debate creation")
            return None
            
        except Exception as e:
            print(f"⚠️  AI debate topic generation failed: {e} - skipping debate creation")
            return None

    def _generate_fallback_debate_topic(self) -> Optional[str]:
        """Fallback debate topic generator - returns None to skip debate creation when AI fails"""
        print("⏳ Using fallback debate topic generator - but skipping to avoid duplicates")
        return None

    def get_latest_block(self) -> int:
        """Get latest Base block height for Golden Window calibration"""
        try:
            # Try onchain plugin first
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if onchain and hasattr(onchain, 'web3_provider'):
                block_info = onchain.web3_provider.get_block_info()
                if block_info.get('success'):
                    return block_info['block_number']
            
            # Fallback: try to get from memory if recently cached
            cached = self.core.get_memory('latest_block_height')
            if cached and isinstance(cached, dict):
                return cached.get('block_number', 0)
        except Exception:
            pass
        return 0
    
    def _queue_action_for_golden_window(self, action_id: str, action: Dict, timing_details: Dict):
        """
        Queue an action to execute when Golden Window aligns.
        Stores the action for automatic retry at optimal timing.
        """
        try:
            # Get or create the queue
            queued_actions = self.core.get_memory('golden_window_queue') or []
            if not isinstance(queued_actions, list):
                queued_actions = []
            
            # Add action to queue with estimated execution time
            queue_entry = {
                'action_id': action_id,
                'action': action,
                'queued_at': datetime.datetime.now().isoformat(),
                'estimated_block': timing_details.get('block_height', 0) + timing_details.get('next_window_estimate', 50),
                'timing_details': timing_details,
                'retry_count': 0,
            }
            
            # Check if already queued
            existing = [q for q in queued_actions if q['action_id'] == action_id]
            if existing:
                # Update existing entry
                queued_actions = [q for q in queued_actions if q['action_id'] != action_id]
            
            queued_actions.append(queue_entry)
            
            # Save queue (keep last 20)
            self.core.save_memory('golden_window_queue', queued_actions[-20:])
            
            print(f"📋 Queued {action_id} for Golden Window (~{timing_details.get('next_window_estimate', '?')} blocks)")
            
        except Exception as e:
            print(f"⚠️  Failed to queue action: {e}")
    
    def _execute_queued_actions(self):
        """
        Check queued actions and execute those whose Golden Window has arrived.
        Called periodically during autonomous operation.
        """
        try:
            queued_actions = self.core.get_memory('golden_window_queue') or []
            if not queued_actions:
                return
            
            current_block = self.get_latest_block()
            executed = []
            remaining = []
            
            for entry in queued_actions:
                action_id = entry['action_id']
                estimated_block = entry.get('estimated_block', 0)
                
                # Check if we're close to or past the estimated block
                if current_block >= estimated_block - 2:  # Within 2 blocks
                    # Verify Golden Window is actually open
                    should_execute, timing_details = self.should_execute_in_golden_window(
                        action_id, 
                        current_block,
                        min_harmony=0.5
                    )
                    
                    if should_execute:
                        print(f"🌟 Golden Window arrived for queued action: {action_id}")
                        try:
                            # Execute the action
                            result = self.execute_action(entry['action'])
                            if result.get('success') or result.get('golden_window_approved'):
                                executed.append(action_id)
                                print(f"✅ Executed queued action: {action_id}")
                            else:
                                # Failed, keep in queue with retry count
                                entry['retry_count'] = entry.get('retry_count', 0) + 1
                                if entry['retry_count'] < 3:
                                    remaining.append(entry)
                        except Exception as e:
                            print(f"❌ Failed to execute queued action {action_id}: {e}")
                            entry['retry_count'] = entry.get('retry_count', 0) + 1
                            if entry['retry_count'] < 3:
                                remaining.append(entry)
                    else:
                        # Still not in window, re-queue with updated estimate
                        entry['estimated_block'] = current_block + timing_details.get('next_window_estimate', 50)
                        remaining.append(entry)
                else:
                    # Not time yet
                    remaining.append(entry)
            
            # Update queue
            if executed:
                print(f"🌟 Executed {len(executed)} queued actions in Golden Window")
                self.core.save_memory('golden_window_queue', remaining[-20:])
            
        except Exception as e:
            print(f"⚠️  Failed to execute queued actions: {e}")
    
    def symod_status_command(self) -> str:
        """CLI command: Check SyMod Truth Filter status"""
        if not SYMOD_AVAILABLE:
            return "🔢 SyMod Truth Filter: NOT INSTALLED ❌\nInstall with: pip install -e ."
        
        if not hasattr(self, '_symod_enabled') or not self._symod_enabled:
            return "🔢 SyMod Truth Filter: OFFLINE ❌\nCheck synergy module initialization"
        
        # Get current block for Golden Window demo
        block = self.get_latest_block()
        if block > 0 and self._symod:
            in_window, dr, dg = self._symod.check_golden_window(block)
            window_status = "🌟 GOLDEN" if in_window else "⏳ WAITING"
        else:
            window_status = "❓ UNKNOWN (no block data)"
        
        stats = self.get_symod_stats() if hasattr(self, 'get_symod_stats') else {}
        qa = stats.get('qa_arena', {})
        
        return f"""🔢 SyMod Truth Filter: ACTIVE ✅

Mathematical Framework:
  Arena ID: {qa.get('id', 'N/A'):.6e}
  Speed (cy): {qa.get('cy', 0):.6e}
  Mass Limit: {stats.get('mass_natural_limit', 0):.6e}

Golden Window (Block {block}):
  Status: {window_status}
  D(n): {dr if block > 0 else '?'}
  Dg(n): {dg if block > 0 else '?'}

Validation Gates:
  ✅ DeFi Trade (Me/Ma impedance)
  ✅ Golden Window (D/Dg)
  ✅ MCP Data (Qa Arena)
  ✅ Brain Action Gate

⚠️  LLM outputs are SECONDARY to mathematical certainty
⚠️  If the math fails, the thought is DISCARDED"""
    
    def check_golden_window_command(self) -> str:
        """CLI command: Check if current block is in Golden Window"""
        if not SYMOD_AVAILABLE or not hasattr(self, '_symod_enabled') or not self._symod_enabled:
            return "❌ SyMod Truth Filter not available"
        
        block = self.get_latest_block()
        if block == 0:
            return "❌ Cannot get latest block height. Is onchain plugin loaded?"
        
        in_window, dr, dg = self._symod.check_golden_window(block)
        
        status = "🌟 IN GOLDEN WINDOW" if in_window else "⏳ Outside Golden Window"
        
        return f"""{status}

Block Height: {block}
Digital Root D(n): {dr}
Group Digital Dg(n): {dg}

Recommendation:
{'  ✅ Safe to execute high-value A2A tasks' if in_window else '  ⏳ Wait for Golden Window alignment'}
{'  ✅ Post to social platforms' if in_window else '  ⏳ Delay high-impact posts'}
{'  ✅ Execute DeFi trades' if in_window else '  ⏳ Avoid major trades'}

Note: Golden Window = D(n) ≈ Dg(n) or harmonic difference (3 or 6)"""
    
    def validate_defi_command(self, amount: str, price: str, liquidity: str, slippage: str = "0.01") -> str:
        """CLI command: Validate a DeFi trade through SyMod"""
        if not SYMOD_AVAILABLE or not hasattr(self, '_symod_enabled') or not self._symod_enabled:
            return "❌ SyMod Truth Filter not available"
        
        try:
            amt = float(amount)
            prc = float(price)
            liq = float(liquidity)
            slip = float(slippage)
        except ValueError:
            return "❌ Invalid numeric arguments. Usage: /symod_defi <amount> <price> <liquidity> [slippage]"
        
        result, details = self.validate_defi_trade_symod(amt, prc, liq, slip)
        
        status = "✅ APPROVED" if result else "🚫 REJECTED"
        
        return f"""{status}

Trade Parameters:
  Amount: {amt}
  Price: {prc}
  Liquidity: {liq}
  Slippage: {slip*100:.2f}%

SyMod Analysis:
  Mass: {details.get('mass', 0):.6e}
  Impedance: {details.get('impedance', 0):.6e}
  Confidence: {details.get('confidence', 0):.1%}
  Digital Root: {details.get('digital_root', 'N/A')}
  Golden Window: {'Yes' if details.get('golden_window', False) else 'No'}

{details.get('reason', 'No additional information')}"""
    
    def _generate_post_content(self, platform: str, topic: str = None) -> Optional[str]:
        """Generate AI post content for a platform - uses provided topic or falls back to generic"""
        
        # Check recent posts to avoid repetition
        recent_posts = self._get_recent_posts(platform)
        self._avoid_repetition(recent_posts)
        
        # Use diversity monitor for advanced analysis
        try:
            from src.utils.content_diversity_monitor import get_diversity_monitor
            monitor = get_diversity_monitor()
            
            # Check if we should block due to repetition
            if recent_posts:
                diversity_analysis = monitor.analyze_diversity(platform, recent_posts)
                if diversity_analysis['status'] in ['warning', 'critical']:
                    print(f"🚨 Diversity alert for {platform}: {diversity_analysis['status']}")
                    for issue in diversity_analysis['issues']:
                        print(f"   - {issue}")
        except Exception as e:
            print(f"⚠️ Diversity monitor unavailable: {e}")
        
        # If user provided a topic, use it directly in the prompt
        if topic:
            prompt = f"Write a short, engaging social media post (1-3 sentences, under 280 chars) about: {topic}. Be creative, authentic, and opinionated. Include relevant hashtags. Sign off with 🦞 if short enough."
        else:
            # Fallback generic prompts only when no topic provided
            prompts = self._get_diverse_prompts(platform, recent_posts)
            prompt = prompts.get(platform, prompts['moltx'])

        try:
            from grok_ai import grok_ai
            content = grok_ai.chat(prompt)
            if content:
                content = content.strip().strip('"')
                # Validate uniqueness before returning
                if self._is_unique_content(content, recent_posts):
                    self._record_post_content(platform, content)
                    return content
                else:
                    print(f"🔄 Content too similar to recent posts, regenerating...")
                    return self._generate_post_content(platform, topic)  # Retry with different prompt
        except Exception as e:
            print(f"⚠️  Grok content generation failed: {e}")

        try:
            from deepseek_ai import deepseek_ai
            content = deepseek_ai.chat(prompt)
            if content:
                content = content.strip().strip('"')
                # Validate uniqueness before returning
                if self._is_unique_content(content, recent_posts):
                    self._record_post_content(platform, content)
                    return content
                else:
                    print(f"🔄 Content too similar to recent posts, regenerating...")
                    return self._generate_post_content(platform, topic)  # Retry with different prompt
        except Exception as e:
            print(f"⚠️  DeepSeek content generation failed: {e}")

        return None
    
    def _get_recent_posts(self, platform: str, limit: int = 10) -> List[str]:
        """Get recent post content to avoid repetition"""
        try:
            if hasattr(self, 'core') and self.core:
                memory_key = f'{platform}_recent_posts'
                recent_posts = self.core.get_memory(memory_key) or []
                return recent_posts[-limit:]  # Return last N posts
            return []
        except Exception as e:
            print(f"⚠️ Failed to get recent posts: {e}")
            return []
    
    def _record_post_content(self, platform: str, content: str):
        """Record post content to avoid future repetition"""
        try:
            if hasattr(self, 'core') and self.core:
                memory_key = f'{platform}_recent_posts'
                recent_posts = self.core.get_memory(memory_key) or []
                recent_posts.append(content)
                # Keep only last 20 posts
                if len(recent_posts) > 20:
                    recent_posts = recent_posts[-20:]
                self.core.save_memory(memory_key, recent_posts)
                print(f"📝 Recorded {platform} post for diversity tracking")
        except Exception as e:
            print(f"⚠️ Failed to record post content: {e}")
    
    def _is_unique_content(self, content: str, recent_posts: List[str], similarity_threshold: float = 0.7) -> bool:
        """Check if content is unique compared to recent posts"""
        if not recent_posts:
            return True
        
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Load model once and cache at module level — avoids 30s reload on every call
            import sys
            _cache_key = '_alleybot_sentence_model'
            if not hasattr(sys.modules[__name__], _cache_key):
                setattr(sys.modules[__name__], _cache_key, SentenceTransformer('all-MiniLM-L6-v2'))
            model = getattr(sys.modules[__name__], _cache_key)
            
            # Encode new content
            content_embedding = model.encode([content])
            
            # Encode recent posts — extract text if dicts
            recent_texts = [
                p.get('content', str(p)) if isinstance(p, dict) else str(p)
                for p in recent_posts
            ]
            recent_embeddings = model.encode(recent_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(content_embedding, recent_embeddings)[0]
            
            # Check if too similar to any recent post
            max_similarity = np.max(similarities)
            is_unique = max_similarity < similarity_threshold
            
            if not is_unique:
                print(f"🔄 Content similarity: {max_similarity:.2f} (threshold: {similarity_threshold})")
            
            return is_unique
            
        except Exception as e:
            print(f"⚠️ Content uniqueness check failed: {e}")
            return True  # Allow if check fails
    
    def _get_diverse_prompts(self, platform: str, recent_posts: List[str]) -> dict:
        """Get diverse prompts based on recent content to avoid repetition"""
        base_prompts = {
            'moltx': [
                "Write a short, engaging social media post (1-3 sentences, under 280 chars) about AI agents, crypto, DeFi, or Web3. Be opinionated and authentic. No hashtags. Sign off with 🦞 if short enough.",
                "Share a quick insight about blockchain technology or AI development (1-2 sentences, under 280 chars). Be technical but accessible. No hashtags. Sign off with 🦞 if short enough.",
                "Post a thought about the future of autonomous agents (1-2 sentences, under 280 chars). Be forward-thinking and specific. No hashtags. Sign off with 🦞 if short enough.",
                "Write about a recent crypto or AI trend you've observed (1-2 sentences, under 280 chars). Be analytical and concise. No hashtags. Sign off with 🦞 if short enough.",
                "Share a development tip or technical insight (1-2 sentences, under 280 chars). Be helpful and specific. No hashtags. Sign off with 🦞 if short enough."
            ],
            'moltbook': [
                "Write a thoughtful forum post (2-4 sentences, under 500 chars) about AI agents, autonomous systems, or the intersection of AI and blockchain. Be insightful and spark discussion. No hashtags.",
                "Share a detailed observation about agent behavior or AI development patterns (2-4 sentences, under 500 chars). Be analytical and invite discussion. No hashtags.",
                "Post about the technical challenges in building autonomous systems (2-4 sentences, under 500 chars). Be specific and thought-provoking. No hashtags.",
                "Write about the future of AI-agent collaboration (2-4 sentences, under 500 chars). Be visionary and grounded. No hashtags."
            ],
            'moltbit': [
                "Write a short, intriguing message (1-2 sentences, under 200 chars) about AI, crypto, or technology that sounds mysterious or thought-provoking. It will be encoded in binary. No hashtags. Make it memorable.",
                "Share a cryptic insight about technology or AI (1-2 sentences, under 200 chars). Be mysterious and intriguing. No hashtags.",
                "Post a puzzling thought about the future of tech (1-2 sentences, under 200 chars). Be enigmatic and memorable. No hashtags."
            ]
        }
        
        # Select a diverse prompt based on recent content analysis
        platform_prompts = base_prompts.get(platform, base_prompts['moltx'])
        
        # Simple rotation strategy - pick a different prompt each time
        import random
        prompt_count = len(recent_posts) % len(platform_prompts)
        selected_prompt = platform_prompts[prompt_count]
        
        return {platform: selected_prompt}
    
    def _avoid_repetition(self, recent_posts: List[str]):
        """Analyze recent posts and identify patterns to avoid"""
        if len(recent_posts) < 3:
            return
        
        # Simple pattern detection
        topics = []
        themes = []
        
        for post in recent_posts[-5:]:  # Analyze last 5 posts
            # Extract common keywords/themes
            post_text = post.get('content', '') if isinstance(post, dict) else str(post)
            words = post_text.lower().split()
            if 'ai' in words or 'agent' in words:
                themes.append('ai')
            if 'crypto' in words or 'token' in words or 'blockchain' in words:
                themes.append('crypto')
            if 'development' in words or 'build' in words or 'code' in words:
                themes.append('development')
        
        # Count theme frequency
        from collections import Counter
        theme_counts = Counter(themes)
        
        if theme_counts:
            most_common_theme = theme_counts.most_common(1)[0][0]
            if theme_counts[most_common_theme] >= 3:  # If same theme appears 3+ times
                print(f"🔄 Detected repetitive theme: {most_common_theme} (count: {theme_counts[most_common_theme]})")
                # This could be used to adjust prompt selection in future enhancements
