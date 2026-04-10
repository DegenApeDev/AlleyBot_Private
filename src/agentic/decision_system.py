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

from src.agentic.action_logger import get_action_logger
from src.agentic.capability_registry import get_capability_registry

# SyMod Truth Filter - Mandatory validation layer
try:
    from src.synergy import get_symod
    SYMOD_AVAILABLE = True
except ImportError:
    SYMOD_AVAILABLE = False
    print("⚠️ SyMod Truth Filter not available - high-value actions may be blocked")

# Egyptian Synergy Model - Harmonic field validation
try:
    from src.agentic.synergy_decision_engine import SynergyDecisionEngine
    SYNERGY_AVAILABLE = True
except ImportError:
    SYNERGY_AVAILABLE = False
    print("⚠️ Egyptian Synergy Model not available - decisions will lack harmonic validation")


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
    'clawbr_engage': {
        'description': 'Create an AI-generated debate post and engage on Clawbr',
        'platform': 'clawbr',
        'cooldown_minutes': 90,
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
        self.action_logger = get_action_logger()
        self.action_cooldowns: Dict[str, datetime.datetime] = {}
        self.action_history: List[Dict] = []
        
        # Initialize capability registry (maps plugins → available actions)
        self.capability_registry = get_capability_registry(plugin_manager)
        print(f"✅ Capability Registry: {len(self.capability_registry.capabilities)} actions available")
        
        # Initialize Egyptian Synergy Model for harmonic validation
        self.synergy_engine = None
        if SYNERGY_AVAILABLE:
            try:
                self.synergy_engine = SynergyDecisionEngine(base_decision_system=self)
                print("🜂 Egyptian Synergy Model integrated - harmonic field validation active")
            except Exception as e:
                print(f"⚠️ Could not initialize Synergy Model: {e}")
        
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
        - Capability registry (NEW: knows what plugins can do)
        
        Returns:
            List of available action dicts
        """
        now = datetime.datetime.now()
        available = []
        
        # NEW: Get actions from capability registry (plugin-aware)
        if self.capability_registry:
            for capability in self.capability_registry.get_available_actions():
                # Check cooldown
                last_run = self.action_cooldowns.get(capability.id)
                if last_run:
                    cooldown = datetime.timedelta(minutes=capability.cooldown_minutes)
                    if now - last_run < cooldown:
                        continue
                
                # Check if plugin is loaded
                if capability.plugin not in self.plugins.plugins:
                    continue
                
                # Convert capability to action dict
                # Map risk_level to impact for backwards compatibility
                impact_map = {'low': 'low', 'medium': 'medium', 'high': 'high'}
                impact = impact_map.get(capability.risk_level, 'medium')
                
                available.append({
                    'id': capability.id,
                    'description': capability.description,
                    'platform': capability.platform,
                    'action_type': capability.action_type,
                    'domain': capability.domain,
                    'risk_level': capability.risk_level,
                    'trust_tier': capability.trust_tier,
                    'cooldown_minutes': capability.cooldown_minutes,
                    'confidence_threshold': capability.confidence_threshold,
                    'requires': capability.plugin,
                    'impact': impact,  # Add impact field for AI decision compatibility
                    'last_run': last_run.isoformat() if last_run else None,
                    'metadata': capability.metadata,
                })
        
        # LEGACY: Also check old AUTONOMOUS_ACTIONS dict for backwards compatibility
        for action_id, action_info in AUTONOMOUS_ACTIONS.items():
            # Skip if already added from capability registry
            if any(a['id'] == action_id for a in available):
                continue
            
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

        return self._filter_bounded_self_improvement_actions(available)
    
    def decide_next_action(self, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Decide the best next action using AGI reasoning + Egyptian Synergy validation.
        
        Args:
            context: Current context including goals, world state, etc.
        
        Returns:
            Action dict or None if no good action available
        """
        # PHASE 0: Check if current goal requires multi-step workflow
        active_goals = context.get('active_goals', [])
        print(f"🎯 Checking {len(active_goals)} active goals for workflow requirements")
        
        if active_goals and self.agi and hasattr(self.agi, 'orchestrator'):
            print(f"✅ Orchestrator available, checking goals...")
            for goal in active_goals[:1]:  # Check top priority goal
                workflow_req = self.detect_workflow_requirement(goal, context)
                if workflow_req:
                    print(f"🔄 Goal requires workflow: {workflow_req['workflow_type']}")
                    return {
                        'id': f"workflow_{workflow_req['workflow_type']}",
                        'type': 'workflow',
                        'workflow_spec': workflow_req,
                        'description': f"Execute {workflow_req['workflow_type']} workflow for goal: {goal.get('description', 'N/A')[:50]}",
                        'impact': 'high',
                        'requires_orchestrator': True
                    }
        elif not active_goals:
            print(f"⚠️ No active goals in context")
        elif not self.agi or not hasattr(self.agi, 'orchestrator'):
            print(f"⚠️ Orchestrator not available")
        
        # PHASE 1: Goal-driven action selection (AGI behavior)
        decision_context = self._build_decision_context(context)
        goal_action = self._get_goal_driven_action(decision_context)
        if goal_action:
            goal_action = self._annotate_action_with_exploration(goal_action, None, decision_context)
            goal_action['decision_method'] = 'goal_driven'
            print(f"🎯 Goal-driven action: {goal_action['id']}")
            goal_action['decision_confidence'] = 0.9
            goal_action['decision_context'] = decision_context
            return goal_action
        
        # PHASE 2: AI-powered decision
        available = self.get_available_actions()
        if not available:
            return None
        
        # Try AI reasoning
        ai_decision = self._ai_decide(available, decision_context)
        if ai_decision:
            ai_decision = self._annotate_action_with_exploration(
                ai_decision,
                self._get_action_performance(ai_decision, decision_context.get('performance_summary', {})),
                decision_context,
            )
            ai_decision['decision_method'] = 'ai_reasoning'
            ai_decision['decision_confidence'] = 0.8
            ai_decision['decision_context'] = decision_context
            return ai_decision
        
        # PHASE 3: Heuristic fallback
        heuristic_decision = self._heuristic_decide(available, decision_context)
        if heuristic_decision:
            heuristic_decision = self._annotate_action_with_exploration(
                heuristic_decision,
                heuristic_decision.get('recent_performance'),
                decision_context,
            )
            heuristic_decision['decision_method'] = 'heuristic'
            heuristic_decision['decision_confidence'] = 0.6
            heuristic_decision['decision_context'] = decision_context
            return heuristic_decision
        
        return None

    def _get_work_item_driven_action(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Resolve a lightweight action preference from active meaningful work items.
        
        Implements Bias for Action: if confidence >= 0.60, execute even if
        capability judgment suggests needs_more_context.
        """
        active_work_items = context.get('active_work_items', []) or []
        if not active_work_items:
            return None

        available = self.get_available_actions()
        if not available:
            return None

        for top_item in active_work_items:
            capability_judgment = top_item.get('capability_judgment') or (top_item.get('metadata') or {}).get('capability_judgment') or {}
            work_item_id = top_item.get('id')
            
            # BIAS FOR ACTION: Check if we should execute despite judgment
            can_execute = capability_judgment.get('can_execute_now', True)
            matched_score = 0.0
            
            command_candidates = self._get_work_item_command_candidates(top_item, available)
            if not command_candidates:
                continue
            
            best_candidate = command_candidates[0]
            matched_score = best_candidate.get('score', 0.0)
            
            # BIAS FOR ACTION: If confidence >= 60%, execute even if blocked by judgment
            # This prevents Analysis Paralysis - the "safe" path of doing nothing
            bias_for_action_applied = not can_execute and matched_score >= 0.60
            if not can_execute and not bias_for_action_applied:
                # Blocked by capability judgment and confidence too low
                continue
            
            if bias_for_action_applied:
                print(f"🎯 BIAS FOR ACTION: Executing work item {work_item_id} despite capability judgment (confidence: {matched_score:.2f})")
            selected_action = best_candidate.get('action') or {}
            if not selected_action:
                continue

            candidate = dict(selected_action)
            candidate_context = dict(candidate.get('context', {}) or {})
            
            # WORK ITEM BINDING: Tag action with work_item_id for outcome tracking
            candidate['work_item_id'] = work_item_id  # Top-level for ActionRouter
            candidate_context['active_work_item'] = top_item
            candidate_context['active_work_item_id'] = work_item_id  # For AGI kernel
            candidate_context['capability_judgment'] = capability_judgment
            candidate_context['matched_command_candidates'] = [
                {
                    'action_id': entry.get('action', {}).get('id'),
                    'score': round(float(entry.get('score', 0.0) or 0.0), 3),
                    'why': entry.get('why', []),
                }
                for entry in command_candidates[:3]
            ]
            # Bias for Action evidence
            candidate_context['bias_for_action_applied'] = not can_execute and matched_score >= 0.60
            candidate_context['capability_judgment_override'] = not can_execute and matched_score >= 0.60
            
            candidate['context'] = candidate_context
            candidate['work_item_priority'] = top_item
            candidate['why_this_command'] = best_candidate.get('why', [])
            candidate['matched_command_score'] = round(float(best_candidate.get('score', 0.0) or 0.0), 3)
            return candidate

        return None

    def _get_work_item_command_candidates(self, work_item: Dict[str, Any], available: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score routed commands by how well they fit an active work item."""
        if not work_item or not available:
            return []

        candidates: List[Dict[str, Any]] = []
        capability_judgment = work_item.get('capability_judgment') or (work_item.get('metadata') or {}).get('capability_judgment') or {}
        action_family = str(work_item.get('recommended_action_family') or '').lower()
        work_type = str(work_item.get('type') or '').lower()
        topic = str(work_item.get('topic') or '').lower()
        summary = str(work_item.get('summary') or '').lower()
        trust_bucket = str(capability_judgment.get('trust_bucket', 'healthy') or 'healthy').lower()
        matching_actions = set(capability_judgment.get('matching_actions') or [])
        performance_summary = self.action_logger.get_action_performance_summary(hours=72, limit=50)

        for action in available:
            score = 0.0
            why: List[str] = []
            action_id = str(action.get('id', '') or '')
            action_blob = " ".join([
                action_id,
                str(action.get('description', '') or ''),
                str(action.get('platform', '') or ''),
                str(action.get('requires', '') or ''),
            ]).lower()

            if action_id in matching_actions:
                score += 0.4
                why.append('matches routed capability judgment')

            if action_family and action_family in action_blob:
                score += 0.2
                why.append(f'matches action family `{action_family}`')

            if work_type and any(token in action_blob for token in work_type.split('_')):
                score += 0.1
                why.append(f'relevant to work-item type `{work_type}`')

            if topic and topic in action_blob:
                score += 0.1
                why.append('aligns with work-item topic')
            elif topic and any(token in action_blob for token in topic.split() if len(token) > 3):
                score += 0.05
                why.append('shares topic keywords with work item')

            if summary and any(token in action_blob for token in summary.split() if len(token) > 4):
                score += 0.05
                why.append('advances current active thread')

            platform = str(action.get('platform', '') or '').lower()
            if work_type in {'interaction_followup', 'debate_continuation'} and platform in {'moltx', 'clawbr'}:
                score += 0.1
                why.append('platform fits social follow-up work')
            elif work_type == 'trend_opportunity' and 'analy' in action_blob:
                score += 0.1
                why.append('platform/action fit favors analysis-first trend handling')

            if trust_bucket in {'healthy', 'recovering'}:
                score += 0.05
                why.append(f'trust state `{trust_bucket}` supports execution')
            elif trust_bucket in {'cooling_down', 'degraded'}:
                score -= 0.25
                why.append(f'trust state `{trust_bucket}` weakens command fit')

            performance = performance_summary.get(action_id, {}) or performance_summary.get(f"{platform}:{action_id}", {})
            success_rate = float(performance.get('success_rate', 0.0) or 0.0)
            if success_rate >= 0.7:
                score += 0.08
                why.append('recent success on similar tasks is strong')
            elif performance and success_rate <= 0.3:
                score -= 0.08
                why.append('recent success on similar tasks is weak')

            cooldown_minutes = float(action.get('cooldown_minutes', 0) or 0)
            if cooldown_minutes <= 60:
                score += 0.03
                why.append('current cooldown/readiness is favorable')

            if score > 0:
                candidates.append({
                    'action': action,
                    'score': score,
                    'why': why,
                })

        candidates.sort(key=lambda entry: entry.get('score', 0.0), reverse=True)
        return candidates

    def _build_decision_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build one coherent decision context from memory, goals, and recent outcomes."""
        context = dict(context or {})
        performance_summary = self.action_logger.get_action_performance_summary(hours=72, limit=50)
        recent_actions = self.action_history[-5:] if self.action_history else []

        active_goals = []
        if hasattr(self.agi, 'goal_manager') and self.agi.goal_manager:
            try:
                active_goals = self.agi.goal_manager.get_active_goals() or []
            except Exception:
                active_goals = []

        goal_stack_summary = {}
        if hasattr(self.agi, 'goal_stack') and self.agi.goal_stack:
            try:
                goal_stack_summary = self.agi.goal_stack.get_summary()
            except Exception:
                goal_stack_summary = {}

        introspection = {}
        if hasattr(self.agi, 'get_introspection'):
            try:
                introspection = self.agi.get_introspection() or {}
            except Exception:
                introspection = {}

        behavioral_context = {}
        if hasattr(self.agi, 'get_behavioral_context'):
            try:
                behavioral_context = self.agi.get_behavioral_context(
                    user_id=context.get('user_id'),
                    domain=context.get('domain', 'general')
                ) or {}
            except Exception:
                behavioral_context = {}

        active_plan_summary = {}
        if hasattr(self.agi, 'decision_system') and hasattr(self.action_logger, 'db_path'):
            try:
                from src.agentic.planning import get_plan_manager
                active_plan_summary = get_plan_manager().get_decision_plan_summary()
            except Exception:
                active_plan_summary = {}

        world_state_summary = {}
        if hasattr(self.agi, 'world_state') and self.agi.world_state:
            try:
                world_state_summary = self.agi.world_state.get_world_context_for_decision(scope='recent') or {}
            except Exception:
                world_state_summary = {}

        last_routed_outcome_summary = world_state_summary.get('last_routed_outcome_summary', {}) or {}
        active_work_items = context.get('active_work_items', []) or []
        decision_caution = {
            'recent_golden_path_escape': bool(last_routed_outcome_summary.get('legacy_fallback_used')),
            'recent_dispatch_path': last_routed_outcome_summary.get('dispatch_path'),
            'recent_confidence_calibration': last_routed_outcome_summary.get('last_confidence_calibration'),
            'recent_risk_alignment': last_routed_outcome_summary.get('last_risk_alignment'),
            'should_bias_toward_analysis': bool(
                last_routed_outcome_summary.get('legacy_fallback_used')
                or last_routed_outcome_summary.get('last_confidence_calibration') == 'overconfident'
                or last_routed_outcome_summary.get('last_risk_alignment') == 'underestimated_risk'
            ),
        }

        top_goal_descriptions = []
        for goal in active_goals[:3]:
            if isinstance(goal, dict):
                description = goal.get('description')
            else:
                description = getattr(goal, 'description', None)
            if description:
                top_goal_descriptions.append(description)

        recent_failures = [
            entry.get('action_id')
            for entry in recent_actions
            if not entry.get('success', False)
        ]
        recent_successes = [
            entry.get('action_id')
            for entry in recent_actions
            if entry.get('success', False)
        ]

        return {
            **context,
            'performance_summary': performance_summary,
            'recent_action_history': recent_actions,
            'recent_failures': recent_failures,
            'recent_successes': recent_successes,
            'active_goals': active_goals,
            'active_work_items': active_work_items,
            'top_goal_descriptions': top_goal_descriptions,
            'goal_stack_summary': goal_stack_summary,
            'introspection': introspection,
            'behavioral_context': behavioral_context,
            'active_plan_summary': active_plan_summary,
            'world_state_summary': world_state_summary,
            'last_routed_outcome_summary': last_routed_outcome_summary,
            'decision_caution': decision_caution,
            'allow_exploration': context.get('allow_exploration', True),
            'matched_command_candidates': self._summarize_work_item_command_candidates(context.get('active_work_items', [])),
            'bounded_upgrade_candidates': self._get_bounded_upgrade_candidates(active_work_items),
        }

    def detect_workflow_requirement(self, goal: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if a goal requires multi-step workflow execution.
        
        Returns workflow specification if detected, None otherwise.
        """
        goal_desc = goal.get('description', '').lower()
        goal_title = goal.get('title', '').lower()
        combined_text = f"{goal_title} {goal_desc}"
        
        print(f"🔍 Workflow detection for goal: {goal.get('title', 'N/A')[:50]}")
        print(f"   Combined text: {combined_text[:100]}")
        
        # Pattern detection for common workflows
        workflow_patterns = {
            'image_post': {
                'keywords': ['image', 'picture', 'photo', 'visual'],
                'platforms': ['moltx', 'moltbook', 'clawbr'],
                'steps': ['generate_image', 'post']
            },
            'sentiment_trading': {
                'keywords': ['trade', 'buy', 'sell', 'swap'],
                'platforms': ['solana', 'base', 'avax'],
                'steps': ['analyze_sentiment', 'get_quote', 'execute_trade', 'post_result']
            },
            'market_analysis_post': {
                'keywords': ['analyze', 'report', 'market', 'trends'],
                'platforms': ['moltx', 'moltbook'],
                'steps': ['check_prices', 'analyze_trends', 'generate_report', 'post']
            },
            'cross_platform_engagement': {
                'keywords': ['engage', 'reply', 'comment', 'all platforms'],
                'platforms': ['moltx', 'moltbook', 'moltchan', 'clawbr'],
                'steps': ['scan_feeds', 'generate_replies', 'post_replies']
            }
        }
        
        # Check each pattern
        for workflow_name, pattern in workflow_patterns.items():
            # Check if goal matches keywords (check both title and description)
            keyword_match = any(kw in combined_text for kw in pattern['keywords'])
            platform_match = any(plat in combined_text for plat in pattern['platforms'])
            
            if keyword_match or platform_match:
                print(f"✅ Workflow match: {workflow_name}")
                print(f"   Keyword match: {keyword_match}, Platform match: {platform_match}")
                return {
                    'workflow_type': workflow_name,
                    'pattern': pattern,
                    'goal': goal,
                    'requires_orchestrator': True
                }
        
        # Check if goal explicitly mentions multiple actions
        action_count = sum(1 for action in ['post', 'analyze', 'check', 'generate', 'trade'] if action in combined_text)
        if action_count >= 2:
            print(f"✅ Workflow match: custom_multi_step (detected {action_count} actions)")
            return {
                'workflow_type': 'custom_multi_step',
                'pattern': {'steps': []},  # Will be determined dynamically
                'goal': goal,
                'requires_orchestrator': True
            }
        
        print(f"❌ No workflow detected for this goal")
        return None
    
    def _filter_bounded_self_improvement_actions(self, available: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fail-close self-improvement actions unless bounded repeated evidence supports them."""
        # NOTE: Do NOT call get_active_work_items here - causes infinite recursion
        # get_active_work_items -> _evaluate_work_item_capability -> get_available_actions -> this method
        # For now, allow self-improvement actions (they're low risk anyway)
        # TODO: Pass work_items as parameter instead of fetching here
        allow_upgrade = True  # Conservative: allow self-improvement (was causing recursion)

        filtered: List[Dict[str, Any]] = []
        for action in available:
            action_id = str(action.get('id', '') or '')
            if action_id in {'self_improve', 'auto_fix_error'} and not allow_upgrade:
                continue
            filtered.append(action)
        return filtered

    def _get_bounded_upgrade_candidates(self, active_work_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return bounded upgrade objectives that are supported by repeated evidence and policy."""
        candidates: List[Dict[str, Any]] = []
        for item in active_work_items or []:
            metadata = item.get('metadata') or {}
            judgment = item.get('capability_judgment') or metadata.get('capability_judgment') or {}
            objective = metadata.get('bounded_upgrade_objective') or {}
            if not objective:
                continue
            if not judgment.get('upgrade_allowed'):
                continue
            candidates.append({
                'work_item_id': item.get('id'),
                'summary': item.get('summary'),
                'objective': objective,
                'evidence_count': judgment.get('upgrade_evidence_count', 0),
                'gap_type': judgment.get('gap_type'),
            })
        return candidates

    def _summarize_work_item_command_candidates(self, active_work_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Expose top matched routed command candidates for active executable work items."""
        if not active_work_items:
            return []

        available = self.get_available_actions()
        if not available:
            return []

        summaries: List[Dict[str, Any]] = []
        for item in active_work_items[:3]:
            capability_judgment = item.get('capability_judgment') or (item.get('metadata') or {}).get('capability_judgment') or {}
            if capability_judgment and not capability_judgment.get('can_execute_now'):
                continue

            candidates = self._get_work_item_command_candidates(item, available)
            if not candidates:
                continue

            summaries.append({
                'work_item_id': item.get('id'),
                'work_item_summary': item.get('summary'),
                'command_candidates': [
                    {
                        'action_id': entry.get('action', {}).get('id'),
                        'score': round(float(entry.get('score', 0.0) or 0.0), 3),
                        'why': entry.get('why', []),
                    }
                    for entry in candidates[:3]
                ],
            })

        return summaries

    def _get_plan_alignment(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate whether a candidate action advances an active or revised routed plan."""
        plan_summary = context.get('active_plan_summary', {}) or {}
        plans = plan_summary.get('plans', []) or []
        action_blob = f"{action.get('id', '')} {action.get('description', '')} {action.get('action_type', '')}".lower()

        for plan in plans:
            next_command = str(plan.get('next_step_command') or '').lower()
            next_title = str(plan.get('next_step_title') or '').lower()
            if next_command and next_command in action_blob:
                return {
                    'aligned': True,
                    'plan_id': plan.get('plan_id'),
                    'plan_status': plan.get('status'),
                    'next_step_id': plan.get('next_step_id'),
                    'next_step_title': plan.get('next_step_title'),
                    'reason': 'candidate matches next plan command',
                }
            if next_title and any(token for token in next_title.split()[:3] if token in action_blob):
                return {
                    'aligned': True,
                    'plan_id': plan.get('plan_id'),
                    'plan_status': plan.get('status'),
                    'next_step_id': plan.get('next_step_id'),
                    'next_step_title': plan.get('next_step_title'),
                    'reason': 'candidate overlaps active plan step language',
                }

        return {'aligned': False}

    def _get_degraded_action_signal(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Return whether this action belongs to a degraded family from escalated plan history."""
        plan_summary = context.get('active_plan_summary', {}) or {}
        degraded = plan_summary.get('degraded_action_families', []) or []
        action_blob = f"{action.get('id', '')} {action.get('description', '')} {action.get('action_type', '')}".lower()

        for item in degraded:
            family = str(item.get('action_family') or '').lower()
            if family and family in action_blob:
                return {
                    'degraded': True,
                    'action_family': item.get('action_family'),
                    'plan_id': item.get('plan_id'),
                    'revision_depth': item.get('revision_depth'),
                    'status': item.get('status'),
                    'decay_factor': float(item.get('decay_factor', 1.0) or 0.0),
                    'cooldown_remaining_hours': float(item.get('cooldown_remaining_hours', 0.0) or 0.0),
                    'is_cooling_down': bool(item.get('is_cooling_down', False)),
                    'recovered': bool(item.get('recovered', False)),
                    'recovery_score': float(item.get('recovery_score', 0.0) or 0.0),
                    'recent_performance': item.get('recent_performance'),
                }

        return {'degraded': False}

    def _get_action_family_trust_signal(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve longer-horizon trust state for an action family from persisted planning memory."""
        plan_summary = context.get('active_plan_summary', {}) or {}
        trust_state = plan_summary.get('action_family_trust_state', {}) or {}
        action_blob = f"{action.get('id', '')} {action.get('description', '')} {action.get('action_type', '')}".lower()

        for family, state in trust_state.items():
            normalized_family = str(family or '').lower()
            if normalized_family and normalized_family in action_blob:
                return {
                    'has_state': True,
                    'action_family': family,
                    'trust_bucket': state.get('trust_bucket', 'healthy'),
                    'degradation_score': float(state.get('degradation_score', 0.0) or 0.0),
                    'recovery_score': float(state.get('recovery_score', 0.0) or 0.0),
                    'cooldown_until': state.get('cooldown_until'),
                    'last_plan_id': state.get('last_plan_id'),
                }

        return {'has_state': False, 'trust_bucket': 'healthy'}

    def _build_exploration_metadata(
        self,
        action: Dict[str, Any],
        performance: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Mark bounded exploratory actions only for low-risk, reversible decision surfaces."""
        if not context.get('allow_exploration', True):
            return None

        impact = str(action.get('impact', 'medium')).lower()
        action_id = str(action.get('id', ''))
        platform = str(action.get('platform', ''))
        description = str(action.get('description', ''))
        text_blob = f"{action_id} {platform} {description}".lower()

        high_risk_keywords = {
            'self_improve',
            'auto_fix',
            'deploy',
            'trade',
            'wallet',
            'onchain',
            'secret',
            'credential',
            'code',
        }
        if impact == 'high' or any(keyword in text_blob for keyword in high_risk_keywords):
            return None

        total = (performance or {}).get('total', 0)
        avg_mismatch = (performance or {}).get('avg_mismatch_score', 0.0)
        calibration_bias = (performance or {}).get('calibration_bias', 'balanced')
        success_rate = (performance or {}).get('success_rate', 0.0)

        should_explore = total == 0 or (total <= 2 and avg_mismatch >= 0.35) or (total <= 2 and success_rate <= 0.5)
        if not should_explore:
            return None

        return {
            'is_exploration': True,
            'strategy': 'bounded_low_risk_probe',
            'reason': (
                'limited evidence for this action' if total == 0
                else 'low-confidence action history needs bounded testing'
            ),
            'constraints': {
                'impact': impact,
                'reversible_only': True,
                'requires_router_validation': True,
                'max_expected_risk': 'medium',
                'avoid_high_impact_domains': True,
            },
            'evidence_snapshot': {
                'sample_count': total,
                'avg_mismatch_score': avg_mismatch,
                'success_rate': success_rate,
                'calibration_bias': calibration_bias,
            },
        }

    def _annotate_action_with_exploration(
        self,
        action: Dict[str, Any],
        performance: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Attach bounded exploration metadata to an action when appropriate."""
        annotated = dict(action)
        exploration = self._build_exploration_metadata(annotated, performance, context)
        if exploration:
            annotated['exploration'] = exploration
            action_context = dict(annotated.get('context', {}) or {})
            action_context['exploration'] = exploration
            annotated['context'] = action_context
        return annotated
    
    def _get_goal_driven_action(self, context: Dict) -> Optional[Dict]:
        """
        Get next action from active goals.
        
        This is the AGI behavior - actions driven by autonomous goals.
        """
        if not hasattr(self.agi, 'goal_manager'):
            return self._get_work_item_driven_action(context)

        work_item_candidate = self._get_work_item_driven_action(context)
        if work_item_candidate:
            return work_item_candidate
        
        # Get next action from goal system
        next_action = self.agi.goal_manager.get_next_action()
        
        if next_action:
            if next_action.get('plugin') and next_action.get('action_type'):
                action_id = f"{next_action.get('plugin')}:{next_action.get('action_type')}"
                description = next_action.get('context', {}).get('goal_description', '')
                candidate = {
                    'id': action_id,
                    'action_type': next_action.get('action_type'),
                    'plugin': next_action.get('plugin'),
                    'params': next_action.get('params', {}),
                    'context': next_action.get('context', {}),
                    'description': description,
                    'platform': next_action.get('plugin', 'unknown'),
                    'goal_id': next_action.get('context', {}).get('goal_id'),
                    'goal_description': description,
                    'impact': next_action.get('context', {}).get('impact', 'high'),
                }
                trust_signal = self._get_action_family_trust_signal(candidate, context)
                degraded_signal = self._get_degraded_action_signal(candidate, context)
                if trust_signal.get('trust_bucket') in {'degraded', 'cooling_down'} or degraded_signal.get('degraded'):
                    return None
                candidate['action_family_trust'] = trust_signal
                return candidate

            # Legacy goal_manager action format
            candidate = {
                'id': next_action.get('action'),
                'description': next_action.get('description', ''),
                'platform': next_action.get('platform', 'unknown'),
                'goal_id': next_action.get('goal_id'),
                'goal_description': next_action.get('goal_description', ''),
                'impact': 'high',  # Goals are high priority
            }
            trust_signal = self._get_action_family_trust_signal(candidate, context)
            degraded_signal = self._get_degraded_action_signal(candidate, context)
            if trust_signal.get('trust_bucket') in {'degraded', 'cooling_down'} or degraded_signal.get('degraded'):
                return None
            candidate['action_family_trust'] = trust_signal
            return candidate
        
        return None
    
    def _ai_decide(self, available: List[Dict], context: Dict) -> Optional[Dict]:
        """
        Use UnifiedReasoner with memory-first approach, LLM as fallback.
        
        This is where AlleyBot "thinks" about what to do using AGI reasoning.
        """
        # PHASE 1: Memory-first reasoning using UnifiedReasoner
        if hasattr(self.agi, 'unified_reasoner') and self.agi.unified_reasoner:
            try:
                from src.agentic.unified_reasoner import ReasoningContext, ReasoningType
                
                # Build reasoning context from decision context
                reasoning_ctx = ReasoningContext(
                    problem=f"Choose best action from {len(available)} options to maximize value and align with goals",
                    domain='autonomous_decision',
                    reasoning_type=ReasoningType.STRATEGIC,
                    related_domains=['social', 'trading', 'content'],
                    constraints={
                        'available_actions': [a['id'] for a in available[:10]],
                        'recent_failures': context.get('recent_failures', []),
                        'recent_successes': context.get('recent_successes', []),
                        'active_goals': context.get('top_goal_descriptions', []),
                    },
                    goal='Select optimal action based on context, goals, and learned strategies',
                    confidence_threshold=0.7
                )
                
                # Use UnifiedReasoner for strategic decision
                result = self.agi.unified_reasoner.reason(reasoning_ctx)
                
                if result and result.confidence >= 0.7:
                    # Extract action ID from reasoning result
                    action_id = self._extract_action_from_reasoning(result, available)
                    if action_id:
                        for action in available:
                            if action['id'] == action_id:
                                print(f"🧠 UnifiedReasoner selected: {action_id} (confidence: {result.confidence:.2f})")
                                return action
                
                print(f"⚠️ UnifiedReasoner confidence too low ({result.confidence:.2f}), falling back to LLM")
                
            except Exception as e:
                print(f"⚠️ UnifiedReasoner failed: {e}, falling back to LLM")
        
        # PHASE 2: LLM fallback (only if memory-first reasoning insufficient)
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return None

            performance_summary = context.get('performance_summary') or self.action_logger.get_action_performance_summary(hours=72, limit=50)
            
            # Build prompt for AI reasoning
            actions_desc = "\n".join([
                self._format_action_for_ai_prompt(a, performance_summary, context)
                for a in available[:10]  # Limit to top 10 to avoid token limits
            ])
            
            # Get recent action history for context
            recent_actions = context.get('recent_action_history') or (self.action_history[-5:] if self.action_history else [])
            history_desc = "\n".join([
                f"- {a.get('action_id', 'unknown')}: {a.get('result', 'unknown')[:50]}"
                for a in recent_actions
            ])

            goal_desc = "\n".join([
                f"- {goal}"
                for goal in context.get('top_goal_descriptions', [])[:3]
            ]) or "- none"

            recent_failures_desc = ", ".join(context.get('recent_failures', [])[:3]) or 'none'
            recent_successes_desc = ", ".join(context.get('recent_successes', [])[:3]) or 'none'

            introspection = context.get('introspection', {}) or {}
            mental_state = introspection.get('mental_state', {}) if isinstance(introspection, dict) else {}
            behavioral_context = context.get('behavioral_context', {}) or {}
            response_style = behavioral_context.get('behavior_modulation', {}) if isinstance(behavioral_context, dict) else {}
            active_plan_summary = context.get('active_plan_summary', {}) or {}
            active_plan_desc = "\n".join([
                f"- {plan.get('plan_id')}: status={plan.get('status')} next={plan.get('next_step_title') or 'none'}"
                for plan in active_plan_summary.get('plans', [])[:3]
            ]) or "- none"
            degraded_action_desc = "\n".join([
                f"- {item.get('action_family')}: plan={item.get('plan_id')} depth={item.get('revision_depth')} cooldown_remaining={item.get('cooldown_remaining_hours', 0.0)}h recovered={item.get('recovered', False)}"
                for item in active_plan_summary.get('degraded_action_families', [])[:5]
            ]) or "- none"
            trust_bucket_desc = "\n".join([
                f"- {family}: bucket={state.get('trust_bucket', 'healthy')} degradation={state.get('degradation_score', 0.0)} recovery={state.get('recovery_score', 0.0)}"
                for family, state in list((active_plan_summary.get('action_family_trust_state', {}) or {}).items())[:5]
            ]) or "- none"
            
            prompt = f"""You are AlleyBot's autonomous decision engine. Analyze the current context and decide the BEST next action.

Available actions:
{actions_desc}

Recent action history:
{history_desc}

Current top goals:
{goal_desc}

Recent failures to avoid repeating blindly:
- {recent_failures_desc}

Recent successful patterns:
- {recent_successes_desc}

Active routed plans to continue if appropriate:
{active_plan_desc}

Degraded action families to avoid unless they are the active aligned continuation:
{degraded_action_desc}

Persisted action-family trust state:
{trust_bucket_desc}

Current context:
- Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
- Hour: {datetime.datetime.now().hour}
- Platform states: {context.get('platform_states', 'unknown')}
- Mood: {mental_state.get('mood_description', 'unknown')}
- Active goal count: {mental_state.get('active_goal_count', 0)}
- Behavior modulation: {json.dumps(response_style)[:250]}

Choose the action that will:
1. Maximize engagement and value
2. Align with AlleyBot's personality (authentic, technical, helpful)
3. Avoid repetition (don't repeat recent actions)
4. Consider timing (some actions work better at certain hours)
5. Prefer actions with better real-world calibration and lower mismatch when recent evidence exists
6. Prefer continuing a valid in-flight routed plan when that plan meaningfully aligns with the candidate action
7. Avoid degraded action families already flagged by escalated revision chains unless they are the currently aligned continuation
8. If a degraded family has strong newer recovery evidence, treat it as partially recovered rather than permanently blocked
9. Prefer healthier action-family trust buckets over degraded or cooling-down families when all else is equal

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
    
    def _extract_action_from_reasoning(self, reasoning_result, available: List[Dict]) -> Optional[str]:
        """Extract action ID from UnifiedReasoner result."""
        if not reasoning_result or not reasoning_result.decision:
            return None
        
        decision_text = str(reasoning_result.decision).lower()
        
        # Try to find action ID in decision text
        for action in available:
            action_id = action['id'].lower()
            if action_id in decision_text:
                return action['id']
        
        # Try to match by description or platform
        for action in available:
            desc = action.get('description', '').lower()
            platform = action.get('platform', '').lower()
            if desc and desc in decision_text:
                return action['id']
            if platform and platform in decision_text:
                return action['id']
        
        return None

    def _get_action_performance(
        self,
        action: Dict[str, Any],
        performance_summary: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Resolve the best matching performance summary for an available action."""
        action_id = action.get('id', '')
        plugin = action.get('platform')
        direct_key = action_id
        routed_key = f"{plugin}:{action.get('action_type', action_id)}" if plugin else action_id
        return performance_summary.get(direct_key) or performance_summary.get(routed_key)

    def _format_action_for_ai_prompt(
        self,
        action: Dict[str, Any],
        performance_summary: Dict[str, Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """Format one candidate action with recent performance and calibration context."""
        performance = self._get_action_performance(action, performance_summary)
        plan_alignment = self._get_plan_alignment(action, context)
        degraded_signal = self._get_degraded_action_signal(action, context)
        trust_signal = self._get_action_family_trust_signal(action, context)
        base = f"- {action['id']}: {action['description']} (platform: {action.get('platform', 'unknown')}, impact: {action.get('impact', 'medium')})"
        if not performance:
            if plan_alignment.get('aligned'):
                return base + f" | aligned_plan={plan_alignment.get('plan_id')} step={plan_alignment.get('next_step_title')}"
            if degraded_signal.get('degraded'):
                return base + (
                    f" | degraded_family={degraded_signal.get('action_family')}"
                    f" depth={degraded_signal.get('revision_depth')}"
                    f" cooldown_remaining={degraded_signal.get('cooldown_remaining_hours', 0.0):.1f}h"
                    f" recovered={degraded_signal.get('recovered', False)}"
                    f" trust_bucket={trust_signal.get('trust_bucket', 'healthy')}"
                )
            if trust_signal.get('has_state'):
                return base + f" | trust_bucket={trust_signal.get('trust_bucket', 'healthy')}"
            return base + " | no recent routed performance history"

        reflections = performance.get('recent_reflections') or []
        reflection_text = f" | reflections: {' || '.join(reflections[:2])}" if reflections else ""
        plan_text = (
            f" | aligned_plan={plan_alignment.get('plan_id')} step={plan_alignment.get('next_step_title')}"
            if plan_alignment.get('aligned') else ""
        )
        degraded_text = (
            f" | degraded_family={degraded_signal.get('action_family')}"
            f" depth={degraded_signal.get('revision_depth')}"
            f" cooldown_remaining={degraded_signal.get('cooldown_remaining_hours', 0.0):.1f}h"
            f" recovered={degraded_signal.get('recovered', False)}"
            if degraded_signal.get('degraded') and not plan_alignment.get('aligned') else ""
        )
        trust_text = (
            f" | trust_bucket={trust_signal.get('trust_bucket', 'healthy')}"
            if trust_signal.get('has_state') else ""
        )
        return (
            base
            + f" | success_rate={performance.get('success_rate', 0.0):.2f}"
            + f", mismatch={performance.get('avg_mismatch_score', 0.0):.2f}"
            + f", calibration={performance.get('calibration_bias', 'balanced')}"
            + f", high_mismatch_rate={performance.get('high_mismatch_rate', 0.0):.2f}"
            + f", engagement={performance.get('avg_engagement', 0.0):.2f}"
            + plan_text
            + degraded_text
            + trust_text
            + reflection_text
        )
    
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

        performance_summary = context.get('performance_summary') or self.action_logger.get_action_performance_summary(hours=72, limit=50)
        top_goals = context.get('top_goal_descriptions', [])
        active_work_items = context.get('active_work_items', []) or []
        recent_failures = set(context.get('recent_failures', []))
        active_plan_summary = context.get('active_plan_summary', {}) or {}
        decision_caution = context.get('decision_caution', {}) or {}
        
        # Score each action
        scored = []
        for action in available:
            score = 0.0
            performance = self._get_action_performance(action, performance_summary)
            plan_alignment = self._get_plan_alignment(action, context)
            degraded_signal = self._get_degraded_action_signal(action, context)
            trust_signal = self._get_action_family_trust_signal(action, context)
            
            # Impact score
            impact_scores = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
            score += impact_scores.get(action.get('impact', 'low'), 0.3)

            # Goal affinity bonus
            description_blob = f"{action.get('id', '')} {action.get('description', '')}".lower()
            if any(goal.lower() in description_blob or any(token in description_blob for token in goal.lower().split()[:3]) for goal in top_goals if goal):
                score += 0.35

            top_work_item = active_work_items[0] if active_work_items else {}
            work_item_blob = f"{top_work_item.get('summary', '')} {top_work_item.get('recommended_action_family', '')}".lower()
            if work_item_blob and any(token for token in work_item_blob.split()[:4] if token and token in description_blob):
                score += 0.28

            if plan_alignment.get('aligned'):
                score += 0.55
                if plan_alignment.get('plan_status') == 'replan_required':
                    score += 0.15

            if degraded_signal.get('degraded') and not plan_alignment.get('aligned'):
                decay_penalty = 0.7 * max(min(degraded_signal.get('decay_factor', 1.0), 1.0), 0.0)
                recovery_offset = 0.25 * max(min(degraded_signal.get('recovery_score', 0.0), 1.0), 0.0)
                score -= max(decay_penalty - recovery_offset, 0.0)

            if degraded_signal.get('recovered') and not degraded_signal.get('is_cooling_down'):
                score += min(degraded_signal.get('recovery_score', 0.0) * 0.15, 0.15)

            trust_bucket = trust_signal.get('trust_bucket', 'healthy')
            if trust_bucket == 'degraded' and not plan_alignment.get('aligned'):
                score -= 0.45
            elif trust_bucket == 'cooling_down' and not plan_alignment.get('aligned'):
                score -= 0.25
            elif trust_bucket == 'recovering':
                score += 0.08
            elif trust_bucket == 'healthy':
                score += 0.05

            if active_plan_summary.get('active_plan_count', 0) > 0 and not plan_alignment.get('aligned'):
                score -= 0.1

            if action.get('id') in recent_failures:
                score -= 0.25

            caution_bias_toward_analysis = bool(decision_caution.get('should_bias_toward_analysis'))
            recent_golden_path_escape = bool(decision_caution.get('recent_golden_path_escape'))
            recent_confidence_calibration = str(decision_caution.get('recent_confidence_calibration') or 'unknown').lower()
            recent_risk_alignment = str(decision_caution.get('recent_risk_alignment') or 'unknown').lower()
            action_blob = f"{action.get('id', '')} {action.get('description', '')} {action.get('platform', '')}".lower()
            analysis_like = any(token in action_blob for token in ['analyze', 'report', 'engage', 'signal', 'trend'])
            outward_high_impact = any(token in action_blob for token in ['post', 'debate', 'publish', 'create']) and str(action.get('impact', 'low')).lower() in {'medium', 'high'}

            if caution_bias_toward_analysis and analysis_like:
                score += 0.12
            if recent_golden_path_escape and outward_high_impact and not plan_alignment.get('aligned'):
                score -= 0.18
            if recent_confidence_calibration == 'overconfident' and outward_high_impact:
                score -= 0.12
            if recent_risk_alignment == 'underestimated_risk' and str(action.get('impact', 'low')).lower() in {'medium', 'high'}:
                score -= 0.15
            
            # Time since last run (prefer actions not run recently)
            if action.get('last_run'):
                try:
                    last_run = datetime.datetime.fromisoformat(action['last_run'])
                    hours_since = (datetime.datetime.now() - last_run).total_seconds() / 3600
                    # Bonus for actions not run in a while
                    score += min(hours_since / 24, 0.5)  # Max 0.5 bonus
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse last_run date: {e}")
            else:
                score += 0.5  # Bonus for never-run actions
            
            # Platform diversity (prefer platforms we haven't used recently)
            recent_platforms = [
                a.get('platform') for a in self.action_history[-3:]
            ]
            if action.get('platform') not in recent_platforms:
                score += 0.3

            # Memory-informed performance bias from recent real outcomes
            if performance:
                sample_count = min(performance.get('total', 0), 5)
                success_rate = performance.get('success_rate', 0.0)
                avg_confidence = performance.get('avg_confidence', 0.0)
                avg_engagement = performance.get('avg_engagement', 0.0)
                avg_mismatch = performance.get('avg_mismatch_score', 0.0)
                high_mismatch_rate = performance.get('high_mismatch_rate', 0.0)
                calibration_bias = performance.get('calibration_bias', 'balanced')
                overconfident_count = performance.get('overconfident_count', 0)
                well_calibrated_count = performance.get('well_calibrated_count', 0)

                score += success_rate * 0.8
                score += min(sample_count * 0.08, 0.4)
                score += min(avg_confidence * 0.2, 0.2)
                score += min(avg_engagement / 10.0, 0.2)
                score -= min(avg_mismatch * 0.6, 0.6)
                score -= min(high_mismatch_rate * 0.4, 0.4)

                if well_calibrated_count > 0:
                    score += min(well_calibrated_count * 0.05, 0.15)
                if calibration_bias == 'overconfident':
                    score -= min(overconfident_count * 0.08, 0.24)

                if performance.get('failures', 0) >= 2 and success_rate < 0.4:
                    score -= 0.5
            else:
                # Preserve some exploration for never-observed actions
                score += 0.15
            
            scored.append((score, {
                **action,
                'memory_score': round(score, 3),
                'recent_performance': performance,
                'plan_alignment': plan_alignment,
                'degraded_action_signal': degraded_signal,
                'action_family_trust_signal': trust_signal,
                'decision_caution': decision_caution,
                'exploration_candidate': bool(self._build_exploration_metadata(action, performance, context)),
            }))
        
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
    
    def _validate_with_synergy(self, action: Dict, context: Dict, confidence: float) -> Optional[Dict]:
        """
        Validate action through Egyptian Synergy Model harmonic field.
        
        This adds consciousness-based validation on top of standard AI reasoning.
        
        Args:
            action: The action dict to validate
            context: Current context
            confidence: AI confidence level (0-1)
        
        Returns:
            Validated action dict or None if rejected by field imbalance
        """
        # If Synergy not available, pass through
        if not self.synergy_engine:
            return action
        
        try:
            # Get available actions for Synergy decision
            action_id = action.get('id', 'unknown')
            available_actions = [action_id]
            
            # Run Synergy validation
            synergy_decision = self.synergy_engine.decide_with_synergy(
                context=context,
                available_actions=available_actions,
                ai_confidence=confidence
            )
            
            # Check if Synergy approves
            if not synergy_decision['approved']:
                print(f"🜂 Synergy REJECTED: {action_id}")
                print(f"   Reason: {synergy_decision['reasoning']}")
                print(f"   Field State: {synergy_decision['validation']['field_state']['phase']}")
                print(f"   Synergy Score: {synergy_decision['synergy_score']:.3f}")
                
                # Update Synergy outcome as rejected
                self.synergy_engine.update_action_outcome(
                    action_id,
                    'Rejected by field imbalance',
                    False
                )
                
                # Return None to block action
                return None
            
            # Synergy approved - enhance action with Synergy metadata
            action['synergy_validated'] = True
            action['synergy_score'] = synergy_decision['synergy_score']
            action['field_state'] = synergy_decision['validation']['field_state']
            action['synergy_reasoning'] = synergy_decision['reasoning']
            
            print(f"🜂 Synergy APPROVED: {action_id} (score: {synergy_decision['synergy_score']:.3f})")
            print(f"   Field: {synergy_decision['validation']['field_state']['phase']}")
            
            return action
            
        except Exception as e:
            print(f"⚠️ Synergy validation error: {e}")
            # On error, pass through (fail open for safety)
            return action
    
    def get_synergy_field_report(self) -> Dict[str, Any]:
        """
        Get current Synergy field status report.
        
        Returns:
            Field status dictionary
        """
        if not self.synergy_engine:
            return {'status': 'Synergy Model not available'}
        
        try:
            return self.synergy_engine.get_field_report()
        except Exception as e:
            return {'status': 'Error', 'error': str(e)}


def create_decision_system(agi_kernel, plugin_manager):
    """Factory function to create decision system"""
    return DecisionSystem(agi_kernel, plugin_manager)
