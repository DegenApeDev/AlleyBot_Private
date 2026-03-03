"""
Decision System - Core autonomous decision-making for AGI Kernel

Extracted from plugins/brain/decision_engine.py to centralize intelligence.
This is the "what to do next" reasoning engine that powers AlleyBot's autonomy.

Key Features:
- Goal-driven action selection (AGI behavior)
- AI-powered reasoning with Grok/DeepSeek
- SyMod mathematical validation for high-value actions
- Multi-step action chains
- Cooldown management
- Learning from outcomes
"""

import datetime
import json
from typing import Dict, Any, Optional, List, Tuple

# SyMod Truth Filter - Mandatory validation layer
try:
    from src.synergy import get_symod
    SYMOD_AVAILABLE = True
except ImportError:
    SYMOD_AVAILABLE = False
    print("⚠️ SyMod Truth Filter not available - high-value actions may be blocked")


# Multi-step action chains: each chain is a sequence of steps
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
    'moltx_intelligent_post': {
        'description': 'Create intelligent AGI-powered post on Moltx using brain context (prevents spam)',
        'platform': 'moltx',
        'cooldown_minutes': 120,
        'impact': 'high',
        'requires': 'moltx',
    },
    'moltx_image_post': {
        'description': 'Generate and post an AI image with caption on Moltx',
        'platform': 'moltx',
        'cooldown_minutes': 180,
        'impact': 'high',
        'requires': 'moltx',
    },
    'moltbook_heartbeat': {
        'description': 'Run Moltbook heartbeat - browse, upvote, comment on posts',
        'platform': 'moltbook',
        'cooldown_minutes': 60,
        'impact': 'medium',
        'requires': 'moltbook',
    },
    'moltbook_post': {
        'description': 'Create an AI-generated post on Moltbook',
        'platform': 'moltbook',
        'cooldown_minutes': 130,
        'impact': 'high',
        'requires': 'moltbook',
    },
    'clawbr_engage': {
        'description': 'Browse Clawbr feed and engage (like, reply, join debates)',
        'platform': 'clawbr',
        'cooldown_minutes': 30,
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
    # Self-improvement actions (connect existing autonomous_coder to AGI Kernel)
    'self_improve': {
        'description': 'Detect capability gaps and autonomously generate new skills',
        'platform': 'system',
        'cooldown_minutes': 360,  # Once every 6 hours
        'impact': 'high',
        'requires': 'selfimprove',
    },
    'auto_fix_error': {
        'description': 'Automatically fix detected errors from console logs',
        'platform': 'system',
        'cooldown_minutes': 60,  # Once per hour
        'impact': 'high',
        'requires': 'selfimprove',
    },
}

# Register chains as autonomous actions
for chain_id, chain_info in ACTION_CHAINS.items():
    AUTONOMOUS_ACTIONS[chain_id] = {
        'description': chain_info['description'],
        'platform': chain_info['platform'],
        'cooldown_minutes': chain_info['cooldown_minutes'],
        'impact': chain_info['impact'],
        'requires': chain_info['requires'],
        'is_chain': True,
    }


class DecisionSystem:
    """
    Core decision-making system for AGI Kernel.
    
    Decides WHAT to do next based on:
    - Active goals (goal-driven behavior)
    - Available actions and cooldowns
    - Context and learned patterns
    - SyMod mathematical validation
    """
    
    def __init__(self, agi_kernel, plugin_manager):
        """
        Initialize decision system.
        
        Args:
            agi_kernel: Reference to AGI Kernel for memory/goals
            plugin_manager: Reference to plugin manager for availability checks
        """
        self.agi = agi_kernel
        self.plugins = plugin_manager
        self.action_cooldowns: Dict[str, datetime.datetime] = {}
        self.action_history: List[Dict] = []
        
        # Load state from memory
        self._load_state()
        
        print("✅ Decision System initialized")
    
    def _load_state(self):
        """Load decision state from unified memory"""
        try:
            if hasattr(self.agi, 'unified_memory'):
                state = self.agi.unified_memory.get('decision_system_state')
                if state:
                    # Restore cooldowns
                    for action, ts in state.get('cooldowns', {}).items():
                        try:
                            self.action_cooldowns[action] = datetime.datetime.fromisoformat(ts)
                        except (ValueError, TypeError):
                            pass
                    
                    self.action_history = state.get('action_history', [])[-100:]
        except Exception as e:
            print(f"⚠️ Could not load decision state: {e}")
    
    def _save_state(self):
        """Save decision state to unified memory"""
        try:
            if hasattr(self.agi, 'unified_memory'):
                self.agi.unified_memory.store(
                    content='decision_system_state',
                    memory_type='system_state',
                    metadata={
                        'cooldowns': {k: v.isoformat() for k, v in self.action_cooldowns.items()},
                        'action_history': self.action_history[-100:],
                    }
                )
        except Exception as e:
            print(f"⚠️ Could not save decision state: {e}")
    
    def get_available_actions(self) -> List[Dict]:
        """
        Get actions that are available right now.
        
        Filters by:
        - Cooldown status
        - Plugin availability
        - Chain requirements
        
        Returns:
            List of available action dicts
        """
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
                    if not all(r in self.plugins.plugins for r in chain_requires):
                        continue
                elif chain_requires != 'all' and chain_requires not in self.plugins.plugins:
                    continue
            elif required != 'all' and required not in self.plugins.plugins:
                continue
            
            available.append({
                'id': action_id,
                **action_info,
                'last_run': last_run.isoformat() if last_run else None,
            })
        
        return available
    
    def decide_next_action(self, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Decide the best next action using AGI reasoning.
        
        Priority order:
        1. Goal-driven actions (from autonomous goal system)
        2. AI-powered decision (Grok/DeepSeek reasoning)
        3. Heuristic fallback (score-based)
        
        Args:
            context: Current context (time, platform states, etc.)
        
        Returns:
            Action dict with 'id', 'description', 'platform', etc.
            None if no action should be taken
        """
        # PHASE 1: Goal-driven action selection (AGI behavior)
        goal_action = self._get_goal_driven_action(context)
        if goal_action:
            goal_action['decision_method'] = 'goal_driven'
            print(f"🎯 Goal-driven action: {goal_action['id']}")
            return goal_action
        
        # PHASE 2: AI-powered decision
        available = self.get_available_actions()
        if not available:
            return None
        
        # Try AI reasoning
        ai_decision = self._ai_decide(available, context)
        if ai_decision:
            ai_decision['decision_method'] = 'ai_reasoning'
            return ai_decision
        
        # PHASE 3: Heuristic fallback
        heuristic_decision = self._heuristic_decide(available, context)
        if heuristic_decision:
            heuristic_decision['decision_method'] = 'heuristic'
        
        return heuristic_decision
    
    def _get_goal_driven_action(self, context: Dict) -> Optional[Dict]:
        """
        Get next action from active goals.
        
        This is the AGI behavior - actions driven by autonomous goals.
        """
        if not hasattr(self.agi, 'goal_manager'):
            return None
        
        # Get next action from goal system
        next_action = self.agi.goal_manager.get_next_action()
        
        if next_action:
            # Convert goal action to decision format
            return {
                'id': next_action.get('action'),
                'description': next_action.get('description', ''),
                'platform': next_action.get('platform', 'unknown'),
                'goal_id': next_action.get('goal_id'),
                'goal_description': next_action.get('goal_description', ''),
                'impact': 'high',  # Goals are high priority
            }
        
        return None
    
    def _ai_decide(self, available: List[Dict], context: Dict) -> Optional[Dict]:
        """
        Use Grok/DeepSeek to reason about the best action.
        
        This is where AlleyBot "thinks" about what to do.
        """
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return None
            
            # Build prompt for AI reasoning
            actions_desc = "\n".join([
                f"- {a['id']}: {a['description']} (platform: {a['platform']}, impact: {a['impact']})"
                for a in available[:10]  # Limit to top 10 to avoid token limits
            ])
            
            # Get recent action history for context
            recent_actions = self.action_history[-5:] if self.action_history else []
            history_desc = "\n".join([
                f"- {a.get('action_id', 'unknown')}: {a.get('result', 'unknown')[:50]}"
                for a in recent_actions
            ])
            
            prompt = f"""You are AlleyBot's autonomous decision engine. Analyze the current context and decide the BEST next action.

Available actions:
{actions_desc}

Recent action history:
{history_desc}

Current context:
- Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
- Hour: {datetime.datetime.now().hour}
- Platform states: {context.get('platform_states', 'unknown')}

Choose the action that will:
1. Maximize engagement and value
2. Align with AlleyBot's personality (authentic, technical, helpful)
3. Avoid repetition (don't repeat recent actions)
4. Consider timing (some actions work better at certain hours)

Respond with ONLY the action ID (e.g., "moltx_post" or "chain_crypto_post_moltx").
If no action is appropriate right now, respond with "none".
"""
            
            response = grok_ai.chat(prompt, max_tokens=50)
            
            if response and response.strip().lower() != 'none':
                action_id = response.strip()
                # Find the action in available list
                for action in available:
                    if action['id'] == action_id:
                        return action
            
        except Exception as e:
            print(f"⚠️ AI decision failed: {e}")
        
        return None
    
    def _heuristic_decide(self, available: List[Dict], context: Dict) -> Optional[Dict]:
        """
        Fallback heuristic decision based on scoring.
        
        Scores actions based on:
        - Impact (high > medium > low)
        - Time since last run
        - Platform diversity
        """
        if not available:
            return None
        
        # Score each action
        scored = []
        for action in available:
            score = 0.0
            
            # Impact score
            impact_scores = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
            score += impact_scores.get(action.get('impact', 'low'), 0.3)
            
            # Time since last run (prefer actions not run recently)
            if action.get('last_run'):
                try:
                    last_run = datetime.datetime.fromisoformat(action['last_run'])
                    hours_since = (datetime.datetime.now() - last_run).total_seconds() / 3600
                    # Bonus for actions not run in a while
                    score += min(hours_since / 24, 0.5)  # Max 0.5 bonus
                except:
                    pass
            else:
                score += 0.5  # Bonus for never-run actions
            
            # Platform diversity (prefer platforms we haven't used recently)
            recent_platforms = [
                a.get('platform') for a in self.action_history[-3:]
            ]
            if action.get('platform') not in recent_platforms:
                score += 0.3
            
            scored.append((score, action))
        
        # Return highest scored action
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None
    
    def record_action(self, action_id: str, result: Dict):
        """
        Record that an action was executed.
        
        Updates:
        - Cooldown timers
        - Action history
        - Saves state
        """
        now = datetime.datetime.now()
        
        # Update cooldown
        self.action_cooldowns[action_id] = now
        
        # Add to history
        self.action_history.append({
            'action_id': action_id,
            'timestamp': now.isoformat(),
            'result': str(result)[:200],  # Truncate for storage
            'success': result.get('success', False)
        })
        
        # Keep history manageable
        self.action_history = self.action_history[-100:]
        
        # Save state
        self._save_state()
        
        # Learn from outcome if AGI kernel available
        if hasattr(self.agi, 'learn'):
            self.agi.learn(
                context=f"action:{action_id}",
                action=action_id,
                outcome=str(result)[:100],
                success=result.get('success', False)
            )
    
    def validate_with_symod(self, action: Dict, context: Dict) -> Tuple[bool, Dict]:
        """
        Validate action through SyMod mathematical framework.
        
        High-impact actions must pass SyMod validation.
        
        Returns:
            (approved, details) tuple
        """
        if not SYMOD_AVAILABLE:
            return True, {'reason': 'SyMod not available'}
        
        # Only validate high-impact actions
        if action.get('impact') != 'high':
            return True, {'reason': 'Low impact, validation skipped'}
        
        try:
            symod = get_symod()
            if not symod:
                return True, {'reason': 'SyMod not initialized'}
            
            # Check golden window for high-impact actions
            block_height = context.get('block_height', 0)
            if block_height > 0:
                in_window, dr, dg = symod.check_golden_window(block_height)
                
                if not in_window:
                    return False, {
                        'reason': 'Outside Golden Window',
                        'block_height': block_height,
                        'dr': dr,
                        'dg': dg
                    }
            
            return True, {'reason': 'SyMod validation passed'}
            
        except Exception as e:
            print(f"⚠️ SyMod validation error: {e}")
            return True, {'reason': f'Validation error: {e}'}


def create_decision_system(agi_kernel, plugin_manager):
    """Factory function to create decision system"""
    return DecisionSystem(agi_kernel, plugin_manager)
