"""
AGI Integration Layer - Brings all AGI components together

This module integrates:
- Unified Memory (consolidated world model)
- Episodic Memory (experiences that change behavior)
- Autonomous Goals (self-generated objectives)
- Meta-Learning (learning how to learn)

Makes AlleyBot actually use its AGI capabilities.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .unified_memory import UnifiedMemory, create_unified_memory
from .episodic_memory import EpisodicMemoryStore, BehaviorModulator, create_episodic_memory
from .autonomous_goals import AutonomousGoalManager, create_autonomous_goal_manager
from .meta_learning import MetaLearningEngine, AdaptiveLearner, create_adaptive_learner
from .self_reflection import SelfReflectionEngine, ReflectionScheduler, create_reflection_engine
from .symod_core import SyModCoreManager, get_symod_manager
from .decision_system import DecisionSystem, create_decision_system
from .action_router import ActionRouter, create_action_router
from .error_monitor import ErrorMonitor, create_error_monitor
from .context_system import ContextSystem, create_context_system
from .reply_system import ReplySystem, create_reply_system
from .goal_generator import SecureGoalGenerator, create_goal_generator
from .content_strategy import ContentStrategySystem, create_content_strategy
from .world_state_bridge import WorldStateBridge, create_world_state_bridge
from .goal_stack import GoalStackBridge, create_goal_stack
from .planning import get_plan_manager
from .work_item_manager import WorkItemManager, create_work_item_manager
from .default_goals import get_default_goal_seeder
from .command_registry import GlobalCommandRegistry, create_command_registry
from .cross_plugin_orchestrator import CrossPluginOrchestrator, create_cross_plugin_orchestrator
from .domain_autonomy_manager import DomainAutonomyManager, create_domain_autonomy_manager


class AGIKernel:
    """
    Central integration point for all AGI systems
    
    This is the 'consciousness' layer that:
    - Coordinates memory systems
    - Generates autonomous goals
    - Modulates behavior based on learning
    - Provides unified API for the rest of the system
    """
    
    def __init__(self, core=None):
        self.core = core
        print("🧠 Initializing AGI Kernel...")
        self.domain_autonomy_profiles = {
            'social': {'enabled': True, 'trust_tier': 'medium', 'risk_level': 'medium'},
            'content': {'enabled': True, 'trust_tier': 'medium', 'risk_level': 'medium'},
            'analysis': {'enabled': True, 'trust_tier': 'high', 'risk_level': 'low'},
            'market': {'enabled': False, 'trust_tier': 'low', 'risk_level': 'high'},
            # BOUNDED SELF-IMPROVEMENT: Enabled with conservative constraints
            # Only allows skill building when:
            # 1. Repeated evidence (2+ failures) shows capability gap
            # 2. Trust state is healthy (not degraded)
            # 3. Upgrade objective is bounded and specific
            # 4. Predicted value outweighs risk
            'self_improvement': {'enabled': True, 'trust_tier': 'medium', 'risk_level': 'medium'},
        }
        
        # Initialize all AGI subsystems
        self.unified_memory = create_unified_memory(core)
        self.episodic_memory = create_episodic_memory()
        self.behavior_modulator = BehaviorModulator(self.episodic_memory)
        
        # SyMod mathematical validation layer (core system)
        self.symod = get_symod_manager(core)
        print("🔢 SyMod Core Manager initialized")
        
        # FairMind DNA (Sovereign Cognition Layer)
        from src.cognition.fairmind_integration import get_fairmind_integration
        self.fairmind = get_fairmind_integration()
        print("🧬 FairMind DNA integrated into AGI Kernel")
        print("   ✅ Truth Violations Matrix (108 violations)")
        print("   ✅ Duat Cognition Engine (60+ primitives, 190+ actions)")
        print("   ✅ Value Dynamics Model (thermodynamic ethics)")
        
        # Cross-Domain Pattern Detector (Horizontal Synthesis)
        from src.agentic.cross_domain_pattern_detector import get_cross_domain_pattern_detector
        self.pattern_detector = get_cross_domain_pattern_detector()
        print("🔗 Cross-Domain Pattern Detector initialized")
        print("   ✅ Crypto-social correlation detection")
        print("   ✅ Sentiment-price correlation detection")
        print("   ✅ Cross-platform trend detection")
        print("   ✅ Multi-domain strategy generation")
        
        # Goal system
        self.goal_manager = create_autonomous_goal_manager(
            unified_memory=self.unified_memory,
            phase12_learning=getattr(self.unified_memory, 'phase12', None),
            onchain_plugin=self._get_onchain_plugin()
        )
        
        # Meta-learning
        self.meta_engine = MetaLearningEngine()
        self.adaptive_learner = AdaptiveLearner(
            meta_engine=self.meta_engine,
            episodic_store=self.episodic_memory,
            unified_memory=self.unified_memory
        )
        
        # Unified Reasoner (AGI reasoning engine)
        from src.agentic.unified_reasoner import UnifiedReasoner
        self.unified_reasoner = UnifiedReasoner(
            knowledge_graph=getattr(self.unified_memory, 'knowledge_graph', None),
            symbolic_engine=None,  # TODO: Add symbolic engine
            plugin_manager=None  # Will be set later
        )
        print("🧠 Unified Reasoner initialized - memory-first AGI reasoning enabled")
        
        # Self-reflection
        self.reflection_engine = create_reflection_engine(self)
        self.reflection_scheduler = None
        
        # Decision system (autonomous thinking)
        self.decision_system = None  # Initialized after plugin_manager available
        
        # Action router (unified execution pipeline)
        self.action_router = None  # Initialized after plugin_manager available
        
        # Error monitor (self-healing)
        self.error_monitor = None  # Initialized after decision_system available
        
        # Context system (intelligent context gathering)
        self.context_system = None  # Initialized after plugin_manager available
        
        # Reply system (intelligent reply generation)
        self.reply_system = None  # Initialized after plugin_manager available
        
        # Goal generator (autonomous goal generation with security)
        self.goal_generator = None  # Initialized after plugin_manager available
        
        # Content strategy (unified content strategy across platforms)
        self.content_strategy = None  # Initialized after plugin_manager available
        
        # World state bridge (persistent environment memory)
        self.world_state = None  # Initialized after plugin_manager available
        
        # Goal stack (persistent goal tracking and execution)
        self.goal_stack = None  # Initialized after plugin_manager available
        self.plan_manager = get_plan_manager()
        
        # Work Item Manager (persistent work tracking)
        self.work_item_manager = None
        
        # Command Registry (global command awareness)
        self.command_registry = None
        
        # Cross-Plugin Orchestrator (complex workflow execution)
        self.orchestrator = None
        
        # Domain Autonomy Manager (graduated autonomy based on performance)
        self.domain_autonomy_manager = None
        
        # Behavior modulator (episodic learning feedback loop)
        self.behavior_modulator = None  # Initialized with episodic memory
        
        # Goal-driven cycle (autonomous goal pursuit)
        self.goal_driven_cycle = None  # Initialized after goal_stack available
        
        # OpenHome converter (plugin sharing)
        self.openhome_converter = None  # Initialized with AGI Kernel
        
        # Content intelligence (cross-platform content optimization)
        self.content_intelligence = None  # Initialized with memory systems
        
        # Adaptive timing (intelligent engagement timing)
        self.adaptive_timing = None  # Initialized with memory systems
        
        # === JARVIS Phase 1: Natural Conversation ===
        # Conversational memory (multi-turn dialogue tracking)
        self.conversational_memory = None  # Initialized in decision systems
        
        # Intent recognition (deep intent understanding)
        self.intent_recognizer = None  # Initialized in decision systems
        
        # Dialogue manager (multi-turn conversation orchestration)
        self.dialogue_manager = None  # Initialized in decision systems
        
        # === JARVIS Phase 2: Proactive Intelligence ===
        # Predictive suggestions (anticipate user needs)
        self.predictive_suggestions = None  # Initialized in decision systems
        
        # Contextual awareness (situational understanding)
        self.contextual_awareness = None  # Initialized in decision systems
        
        # Opportunity detector (spot opportunities)
        self.opportunity_detector = None  # Initialized in decision systems
        
        # === JARVIS Phase 3: Personality & Emotional Intelligence ===
        # Personality engine (consistent character)
        self.personality_engine = None  # Initialized in decision systems
        
        # Emotional intelligence (empathy and emotion detection)
        self.emotional_intelligence = None  # Initialized in decision systems
        
        # Adaptive response (perfectly-tuned responses)
        self.adaptive_response = None  # Initialized in decision systems
        
        # === LLM Decision Router (Revolutionary Decision Making) ===
        # Uses reasoning models to generate dynamic options, validated by SyMod
        self.llm_decision_router = None  # Initialized in decision systems
        
        print("✅ AGI Kernel ready")
    
    def _get_onchain_plugin(self):
        """Get onchain plugin if available"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('onchain')
        return None
    
    def initialize_decision_systems(self, plugin_manager):
        """
        Initialize decision system, action router, and error monitor.
        
        Called after plugin_manager is available.
        This completes the AGI Kernel initialization.
        """
        if not self.decision_system:
            self.decision_system = create_decision_system(self, plugin_manager)
            print("✅ Decision System integrated into AGI Kernel")
        
        if not self.action_router:
            self.action_router = create_action_router(self, plugin_manager)
            print("✅ Action Router integrated into AGI Kernel")
        
        if not self.error_monitor:
            self.error_monitor = create_error_monitor(self)
            print("✅ Error Monitor integrated into AGI Kernel")
        
        if not self.behavior_modulator:
            from src.agentic.episodic_memory import create_behavior_modulator
            self.behavior_modulator = create_behavior_modulator()
            print("✅ Behavior Modulator integrated into AGI Kernel (episodic learning active)")
        
        if not self.goal_driven_cycle:
            from src.agentic.goal_driven_cycle import create_goal_driven_cycle
            self.goal_driven_cycle = create_goal_driven_cycle(self)
            print("✅ Goal-Driven Cycle integrated into AGI Kernel (autonomous goal pursuit active)")
        
        if not self.openhome_converter:
            from src.agentic.openhome_converter import create_openhome_converter
            self.openhome_converter = create_openhome_converter(self)
            print("✅ OpenHome Converter integrated into AGI Kernel (plugin sharing enabled)")
        
        if not self.content_intelligence:
            from src.agentic.content_intelligence import create_content_intelligence
            self.content_intelligence = create_content_intelligence(
                unified_memory=self.unified_memory,
                episodic_memory=self.behavior_modulator.episodic if self.behavior_modulator else None,
                world_state=self.world_state.world_state if self.world_state else None
            )
            print("✅ Content Intelligence integrated into AGI Kernel (cross-platform optimization active)")
        
        if not self.adaptive_timing:
            from src.agentic.adaptive_timing import create_adaptive_timing_engine
            self.adaptive_timing = create_adaptive_timing_engine(
                episodic_memory=self.behavior_modulator.episodic if self.behavior_modulator else None,
                world_state=self.world_state.world_state if self.world_state else None
            )
            print("✅ Adaptive Timing integrated into AGI Kernel (intelligent timing active)")
        
        # === JARVIS Phase 1: Natural Conversation ===
        if not self.conversational_memory:
            from src.agentic.conversational_memory import create_conversational_memory
            self.conversational_memory = create_conversational_memory(
                max_turns=50,
                context_window=10
            )
            print("✅ Conversational Memory integrated into AGI Kernel (multi-turn dialogue active)")
        
        if not self.intent_recognizer:
            from src.agentic.intent_recognition import create_intent_recognizer
            self.intent_recognizer = create_intent_recognizer()
            print("✅ Intent Recognizer integrated into AGI Kernel (deep intent understanding active)")
        
        if not self.dialogue_manager:
            from src.agentic.dialogue_manager import create_dialogue_manager
            self.dialogue_manager = create_dialogue_manager(
                conversational_memory=self.conversational_memory,
                intent_recognizer=self.intent_recognizer
            )
            print("✅ Dialogue Manager integrated into AGI Kernel (JARVIS-style conversation active)")
        
        # === JARVIS Phase 2: Proactive Intelligence ===
        if not self.predictive_suggestions:
            from src.agentic.predictive_suggestions import create_predictive_suggestions
            self.predictive_suggestions = create_predictive_suggestions(
                episodic_memory=self.behavior_modulator.episodic if self.behavior_modulator else None,
                goal_manager=self.goal_stack,
                world_state=self.world_state.world_state if self.world_state else None,
                content_intelligence=self.content_intelligence
            )
            print("✅ Predictive Suggestions integrated into AGI Kernel (proactive assistance active)")
        
        if not self.contextual_awareness:
            from src.agentic.contextual_awareness import create_contextual_awareness
            self.contextual_awareness = create_contextual_awareness(
                world_state=self.world_state.world_state if self.world_state else None,
                conversational_memory=self.conversational_memory,
                goal_manager=self.goal_stack
            )
            print("✅ Contextual Awareness integrated into AGI Kernel (situational understanding active)")
        
        if not self.opportunity_detector:
            from src.agentic.opportunity_detector import create_opportunity_detector
            self.opportunity_detector = create_opportunity_detector(
                world_state=self.world_state.world_state if self.world_state else None,
                content_intelligence=self.content_intelligence,
                adaptive_timing=self.adaptive_timing
            )
            print("✅ Opportunity Detector integrated into AGI Kernel (opportunity awareness active)")
        
        # === JARVIS Phase 3: Personality & Emotional Intelligence ===
        if not self.personality_engine:
            from src.agentic.personality_engine import create_personality_engine
            self.personality_engine = create_personality_engine()
            print("✅ Personality Engine integrated into AGI Kernel (consistent character active)")
        
        if not self.emotional_intelligence:
            from src.agentic.emotional_intelligence import create_emotional_intelligence
            self.emotional_intelligence = create_emotional_intelligence(
                conversational_memory=self.conversational_memory
            )
            print("✅ Emotional Intelligence integrated into AGI Kernel (empathy active)")
        
        if not self.adaptive_response:
            from src.agentic.adaptive_response import create_adaptive_response
            self.adaptive_response = create_adaptive_response(
                personality_engine=self.personality_engine,
                emotional_intelligence=self.emotional_intelligence,
                contextual_awareness=self.contextual_awareness,
                conversational_memory=self.conversational_memory,
                intent_recognizer=self.intent_recognizer
            )
            print("✅ Adaptive Response integrated into AGI Kernel (JARVIS-style responses active)")
        
        # === LLM Decision Router ===
        if not self.llm_decision_router:
            from src.agentic.llm_decision_router import create_llm_decision_router
            self.llm_decision_router = create_llm_decision_router(self)
            print("✅ LLM Decision Router integrated into AGI Kernel (dynamic reasoning-based decisions active)")
        
        if not self.context_system:
            self.context_system = create_context_system(self, plugin_manager)
            print("✅ Context System integrated into AGI Kernel")
        
        if not self.reply_system:
            self.reply_system = create_reply_system(self, plugin_manager)
            print("✅ Reply System integrated into AGI Kernel")
        
        if not self.goal_generator:
            self.goal_generator = create_goal_generator(self)
            print("✅ Goal Generator integrated into AGI Kernel")
        
        if not self.content_strategy:
            self.content_strategy = create_content_strategy(self)
            print("✅ Content Strategy integrated into AGI Kernel")
        
        if not self.world_state:
            self.world_state = create_world_state_bridge(self)
            print("✅ World State Bridge integrated into AGI Kernel")
        
        if not self.goal_stack:
            self.goal_stack = create_goal_stack(self)
            print("✅ Goal Stack integrated into AGI Kernel")
        
        # Command Registry (global command awareness)
        if not self.command_registry and self.core and hasattr(self.core, 'plugin_manager'):
            self.command_registry = create_command_registry(self.core.plugin_manager)
            stats = self.command_registry.get_stats()
            print(f"✅ Command Registry initialized ({stats['total_commands']} commands across {stats['total_plugins']} plugins)")
            print(f"   📊 Domains: {', '.join(f'{k}={v}' for k, v in sorted(stats['by_domain'].items()))}")
        
        # Cross-Plugin Orchestrator (complex workflow execution)
        if not self.orchestrator:
            self.orchestrator = create_cross_plugin_orchestrator(self)
            print("✅ Cross-Plugin Orchestrator initialized (multi-plugin workflows enabled)")
        
        # Domain Autonomy Manager (graduated autonomy)
        if not self.domain_autonomy_manager:
            self.domain_autonomy_manager = create_domain_autonomy_manager(self)
            locked_domains = [d for d, p in self.domain_autonomy_profiles.items() if not p['enabled']]
            if locked_domains:
                print(f"🎯 Domain Autonomy Manager initialized ({len(locked_domains)} domains locked, will unlock based on performance)")
                print(f"   🔒 Locked: {', '.join(locked_domains)}")
        
        # Seed default goals for autonomous operation
        try:
            goal_seeder = get_default_goal_seeder(self)
            seeded_count = goal_seeder.seed_goals_if_needed()
            if seeded_count > 0:
                print(f"🌱 Seeded {seeded_count} default goals for autonomous operation")
        except Exception as e:
            print(f"⚠️ Default goal seeding failed: {e}")
        
        print("🧠 AGI Kernel fully operational - autonomous thinking + self-healing + intelligent context + smart replies + goal generation + content strategy + world state + goal stack enabled")
    
    # =================================================================
    # Core AGI Interface
    # =================================================================
    
    def perceive(self, observation: str, context: Dict[str, Any]) -> Dict:
        """
        Process an observation through the AGI system
        
        This is the main entry point - every input goes through here.
        Returns context-enriched understanding with behavioral adjustments.
        """
        # 1. Store the observation
        self.unified_memory.store(
            content=observation,
            memory_type='observation',
            metadata=context
        )
        
        # 2. Recall relevant episodic memories
        relevant_memories = self.episodic_memory.recall_relevant(
            current_context=observation,
            k=3
        )
        
        # 3. Get behavior modulation from memory
        behavior_params = self.behavior_modulator.get_effective_params(observation)
        
        # 4. Get user context if available
        user_context = {}
        user_id = context.get('user_id')
        if user_id:
            user_context = self.unified_memory.get_entity_context(user_id)
        
        # 5. Check for active goals that might influence response
        active_goals = self.goal_manager.get_active_goals()
        
        return {
            'observation': observation,
            'relevant_memories': [m.to_dict() for m in relevant_memories],
            'behavior_params': behavior_params,
            'user_context': user_context,
            'active_goals': active_goals,
            'recommended_style': self.behavior_modulator.get_response_style(observation)
        }
    
    def decide(self, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Make a decision about what to do next.
        
        This is the core AGI decision-making method.
        Uses:
        - Decision system (autonomous thinking)
        - Past outcomes (episodic memory)
        - Current goals (autonomous goal system)
        - Meta-learned strategies
        
        Returns:
            Action dict or None if no action should be taken
        """
        if not self.decision_system:
            print("⚠️ Decision system not initialized")
            return None

        enriched_context = dict(context or {})
        enriched_context['active_work_items'] = self.get_active_work_items(limit=5)
        
        # Add active goals from all goal systems to enable goal-driven decisions
        active_goals = []
        
        # Get goals from AutonomousGoalManager (old system)
        if self.goal_manager and hasattr(self.goal_manager, 'get_active_goals'):
            try:
                autonomous_goals = self.goal_manager.get_active_goals()
                active_goals.extend(autonomous_goals)
            except Exception as e:
                print(f"⚠️ Could not get autonomous goals: {e}")
        
        # Get goals from GoalHierarchy (85% AGI system)
        if hasattr(self, 'goal_hierarchy') and self.goal_hierarchy:
            try:
                if hasattr(self.goal_hierarchy, 'get_actionable_goals'):
                    hierarchical_goals = self.goal_hierarchy.get_actionable_goals()
                    # Convert to dict format if needed
                    for goal in hierarchical_goals:
                        if hasattr(goal, 'to_dict'):
                            active_goals.append(goal.to_dict())
                        elif isinstance(goal, dict):
                            active_goals.append(goal)
            except Exception as e:
                print(f"⚠️ Could not get hierarchical goals: {e}")
        
        enriched_context['active_goals'] = active_goals
        if active_goals:
            print(f"🎯 Decision context enriched with {len(active_goals)} active goals")
        
        # Use decision system for autonomous thinking
        action = self.decision_system.decide_next_action(enriched_context)
        
        if action:
            print(f"🧠 AGI decided: {action.get('id')} ({action.get('decision_method', 'unknown')})")
        
        return action

    def get_active_work_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return active meaningful work items, persisted across cycles when available."""
        derived_items = self._derive_work_items(limit=limit)

        if self.work_item_manager:
            try:
                self.work_item_manager.upsert_many(derived_items)
                persisted = self.work_item_manager.get_active_work_items(limit=limit)
                judged_items: List[Dict[str, Any]] = []
                for item in persisted:
                    judgment = self._evaluate_work_item_capability(item)
                    item['capability_judgment'] = judgment
                    metadata = dict(item.get('metadata') or {})
                    metadata['capability_judgment'] = judgment
                    item['metadata'] = metadata
                    self.work_item_manager.persist_capability_judgment(item.get('id'), judgment)
                    judged_items.append(item)
                if judged_items:
                    return judged_items[:limit]
                if persisted:
                    return persisted
            except Exception as exc:
                print(f"⚠️ Work item persistence failed: {exc}")

        return derived_items[:limit]

    def _derive_work_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Derive lightweight meaningful work items from goals and recent world-state signals."""
        work_items: List[Dict[str, Any]] = []

        try:
            active_goals = self.goal_manager.get_active_goals() if self.goal_manager else []
        except Exception:
            active_goals = []

        for goal in active_goals[:limit]:
            goal_id = getattr(goal, 'id', None) or goal.get('id') if isinstance(goal, dict) else None
            goal_description = getattr(goal, 'description', None) or goal.get('description') if isinstance(goal, dict) else None
            goal_blob = str(goal_description or '').lower()
            work_items.append({
                'id': f"goal:{goal_id or 'unknown'}",
                'type': 'goal',
                'source': 'goal_manager',
                'goal_id': goal_id,
                'summary': goal_description or 'active goal',
                'urgency': 'high',
                'status': 'active',
                'recommended_action_family': 'analyze' if goal_description and any(token in goal_description.lower() for token in ['analy', 'research', 'report']) else None,
            })

            if any(token in goal_blob for token in ['debate', 'argue', 'discussion']):
                work_items.append({
                    'id': f"debate:{goal_id or 'unknown'}",
                    'type': 'debate_continuation',
                    'source': 'goal_manager',
                    'goal_id': goal_id,
                    'summary': goal_description or 'Continue active debate thread',
                    'urgency': 'medium',
                    'status': 'active',
                    'recommended_action_family': 'engage',
                })

        if self.world_state and hasattr(self.world_state, 'get_world_context_for_decision'):
            try:
                world_context = self.world_state.get_world_context_for_decision(scope='recent') or {}
            except Exception:
                world_context = {}

            recent_events = world_context.get('recent_events', []) or []
            trending_topics = world_context.get('trending_topics', []) or []
            service_messages = world_context.get('service_messages', []) or []
            market_signals = world_context.get('market_opportunities', []) or world_context.get('onchain_opportunities', []) or []

            mention_like_events = [
                event for event in recent_events
                if str(event.get('type', '')).lower() in {'mention', 'reply', 'comment'}
            ]
            if mention_like_events:
                work_items.append({
                    'id': 'interaction:pending_social_followup',
                    'type': 'interaction_followup',
                    'source': 'world_state',
                    'summary': f"{len(mention_like_events)} recent interaction(s) may need follow-up",
                    'urgency': 'high',
                    'status': 'active',
                    'recommended_action_family': 'engage',
                    'metadata': {
                        'interaction_count': len(mention_like_events),
                    },
                })

            actionable_service_messages = [
                message for message in service_messages
                if isinstance(message, dict) and str(message.get('priority', 'medium')).lower() in {'high', 'critical'}
            ]
            if actionable_service_messages:
                top_message = actionable_service_messages[0]
                work_items.append({
                    'id': f"service:{top_message.get('id', 'pending_operational_prompt')}",
                    'type': 'service_prompt',
                    'source': 'world_state',
                    'summary': top_message.get('summary') or top_message.get('content') or 'High-priority operational service message needs review',
                    'urgency': 'high',
                    'status': 'active',
                    'recommended_action_family': 'analyze',
                    'metadata': {
                        'service_message': top_message,
                    },
                })

            if trending_topics:
                top_topic = trending_topics[0]
                work_items.append({
                    'id': f"trend:{top_topic.get('topic', 'unknown')}",
                    'type': 'trend_opportunity',
                    'source': 'world_state',
                    'summary': f"Investigate or act on trending topic {top_topic.get('topic', 'unknown')}",
                    'urgency': 'medium',
                    'status': 'active',
                    'recommended_action_family': 'analyze',
                    'topic': top_topic.get('topic'),
                    'metadata': {
                        'trend_signal': top_topic,
                    },
                })

            if market_signals:
                top_market_signal = market_signals[0]
                work_items.append({
                    'id': f"market:{top_market_signal.get('id', top_market_signal.get('symbol', 'opportunity'))}",
                    'type': 'market_opportunity',
                    'source': 'world_state',
                    'summary': top_market_signal.get('summary') or f"Review market/on-chain opportunity for {top_market_signal.get('symbol', 'unknown')}",
                    'urgency': 'medium',
                    'status': 'active',
                    'recommended_action_family': 'analyze',
                    'metadata': {
                        'market_signal': top_market_signal,
                    },
                })

        repeated_failure_item = self._derive_repeated_failure_work_item()
        if repeated_failure_item:
            work_items.append(repeated_failure_item)

        operational_fix_item = self._derive_operational_fix_work_item()
        if operational_fix_item:
            work_items.append(operational_fix_item)

        failed_goal_item = self._derive_failed_goal_execution_work_item()
        if failed_goal_item:
            work_items.append(failed_goal_item)

        return work_items[:limit]

    def _derive_repeated_failure_work_item(self) -> Optional[Dict[str, Any]]:
        """Derive a work item when routed action history shows repeated blocked/failure patterns."""
        router = getattr(self, 'action_router', None)
        execution_history = getattr(router, 'execution_history', None) if router else None
        if not isinstance(execution_history, list) or len(execution_history) < 3:
            return None

        recent_failures = [
            outcome for outcome in execution_history[-8:]
            if not outcome.get('success', False)
        ]
        if len(recent_failures) < 2:
            return None

        dominant_action = str(recent_failures[-1].get('action_type', '') or 'unknown')
        blocked_reasons = [
            str(outcome.get('error') or outcome.get('reason') or 'execution_failed')
            for outcome in recent_failures[-3:]
        ]

        return {
            'id': f"failure:{dominant_action}",
            'type': 'blocked_action_pattern',
            'source': 'action_router',
            'summary': f"Repeated blocked/failing action pattern detected for {dominant_action}",
            'urgency': 'medium',
            'status': 'active',
            'recommended_action_family': 'analyze',
            'metadata': {
                'recent_failures': blocked_reasons,
                'failure_count': len(recent_failures),
            },
            'last_outcome': blocked_reasons[-1],
            'blocked_reason': blocked_reasons[-1],
        }

    def _derive_operational_fix_work_item(self) -> Optional[Dict[str, Any]]:
        """Create an operational-fix work item when recent routed failures imply a system/runtime issue."""
        router = getattr(self, 'action_router', None)
        execution_history = getattr(router, 'execution_history', None) if router else None
        if not isinstance(execution_history, list):
            return None

        recent_failures = [
            outcome for outcome in execution_history[-6:]
            if not outcome.get('success', False)
            and any(token in str(outcome.get('error') or outcome.get('reason') or '').lower() for token in ['timeout', 'network', 'unavailable', 'not loaded'])
        ]
        if not recent_failures:
            return None

        latest = recent_failures[-1]
        failure_reason = str(latest.get('error') or latest.get('reason') or 'runtime_issue')
        return {
            'id': f"opsfix:{latest.get('action_type', 'runtime')}",
            'type': 'operational_fix',
            'source': 'action_router',
            'summary': f"Investigate operational/runtime issue affecting {latest.get('action_type', 'runtime action')}",
            'urgency': 'medium',
            'status': 'active',
            'recommended_action_family': 'analyze',
            'metadata': {
                'failure_reason': failure_reason,
            },
            'blocked_reason': failure_reason,
            'last_outcome': failure_reason,
        }

    def _derive_failed_goal_execution_work_item(self) -> Optional[Dict[str, Any]]:
        """Create a work item when the same goal repeatedly fails to execute successfully."""
        router = getattr(self, 'action_router', None)
        execution_history = getattr(router, 'execution_history', None) if router else None
        if not isinstance(execution_history, list):
            return None

        goal_failures = [
            outcome for outcome in execution_history[-10:]
            if not outcome.get('success', False) and outcome.get('goal_id')
        ]
        if len(goal_failures) < 2:
            return None

        goal_id = goal_failures[-1].get('goal_id')
        same_goal_failures = [outcome for outcome in goal_failures if outcome.get('goal_id') == goal_id]
        if len(same_goal_failures) < 2:
            return None

        last_failure = same_goal_failures[-1]
        failure_reason = str(last_failure.get('error') or last_failure.get('reason') or 'goal_execution_failed')
        return {
            'id': f"goalfail:{goal_id}",
            'type': 'failed_goal_execution',
            'source': 'action_router',
            'goal_id': goal_id,
            'summary': f"Repeated failed execution detected for goal {goal_id}",
            'urgency': 'medium',
            'status': 'active',
            'recommended_action_family': 'analyze',
            'metadata': {
                'failure_count': len(same_goal_failures),
                'failure_reason': failure_reason,
            },
            'blocked_reason': failure_reason,
            'last_outcome': failure_reason,
        }

    def _evaluate_work_item_capability(self, work_item: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether a work item is executable now or reflects a real capability gap."""
        work_item = dict(work_item or {})
        action_family = str(work_item.get('recommended_action_family') or '').lower()
        summary_blob = " ".join([
            str(work_item.get('summary', '') or ''),
            str(work_item.get('type', '') or ''),
            str(work_item.get('topic', '') or ''),
            action_family,
        ]).lower()

        judgment = {
            'can_execute_now': False,
            'needs_more_context': False,
            'needs_different_strategy': False,
            'needs_new_skill': False,
            'blocked_by_policy': False,
            'blocked_by_runtime_readiness': False,
            'primary_reason': 'insufficient_evidence',
            'summary': '',
            'matching_actions': [],
            'plugin_ready': False,
            'trust_bucket': 'unknown',
            'world_state_evidence': False,
            'upgrade_allowed': False,
            'upgrade_evidence_count': 0,
            'upgrade_within_policy': False,
            'predicted_value_outweighs_risk': False,
            'gap_type': 'none',
        }

        available_actions = []
        if self.decision_system and hasattr(self.decision_system, 'get_available_actions'):
            try:
                # Guard against recursion: get_available_actions may call get_active_work_items
                # which calls this method again. Use a simple flag to prevent infinite loop.
                if not hasattr(self, '_evaluating_work_item'):
                    self._evaluating_work_item = True
                    available_actions = self.decision_system.get_available_actions() or []
                    self._evaluating_work_item = False
                else:
                    # Already evaluating, skip to prevent recursion
                    available_actions = []
            except Exception:
                available_actions = []
                if hasattr(self, '_evaluating_work_item'):
                    self._evaluating_work_item = False

        matching_actions = []
        required_plugins = set()
        for action in available_actions:
            action_blob = " ".join([
                str(action.get('id', '') or ''),
                str(action.get('description', '') or ''),
                str(action.get('platform', '') or ''),
                str(action.get('requires', '') or ''),
            ]).lower()
            if action_family and action_family in action_blob:
                matching_actions.append(action.get('id'))
                requires = action.get('requires')
                if isinstance(requires, list):
                    required_plugins.update(str(req) for req in requires if req)
                elif requires:
                    required_plugins.add(str(requires))

        loaded_plugins = set()
        plugin_manager = getattr(self.core, 'plugin_manager', None) if self.core else None
        if plugin_manager and hasattr(plugin_manager, 'list_loaded'):
            try:
                loaded_plugins = {str(name) for name in (plugin_manager.list_loaded() or [])}
            except Exception:
                loaded_plugins = set()

        plugin_ready = not required_plugins or any(plugin in loaded_plugins for plugin in required_plugins)
        judgment['plugin_ready'] = plugin_ready
        judgment['matching_actions'] = matching_actions[:5]

        trust_state = self.plan_manager.get_action_family_states() if self.plan_manager else {}
        family_state = trust_state.get(action_family, {}) if action_family else {}
        trust_bucket = family_state.get('trust_bucket', 'healthy' if action_family else 'unknown')
        judgment['trust_bucket'] = trust_bucket

        world_evidence = False
        metadata = work_item.get('metadata') or {}
        if metadata.get('interaction_count') or metadata.get('trend_signal') or work_item.get('goal_id'):
            world_evidence = True
        judgment['world_state_evidence'] = world_evidence

        if trust_bucket == 'degraded':
            judgment['blocked_by_policy'] = True
            judgment['primary_reason'] = 'trust_policy_block'
            judgment['summary'] = 'Action family is currently degraded and should fail closed'
            return judgment

        if trust_bucket == 'cooling_down':
            judgment['blocked_by_runtime_readiness'] = True
            judgment['primary_reason'] = 'action_family_cooling_down'
            judgment['blocked_reason'] = 'cooldown_active'
            judgment['summary'] = 'Action family is cooling down before safe retry'
            return judgment

        if not matching_actions:
            judgment['needs_new_skill'] = True
            judgment['primary_reason'] = 'no_matching_routed_action'
            judgment['summary'] = 'No routed action currently matches this work item'
            judgment['gap_type'] = 'new_skill_need'
            self._annotate_upgrade_eligibility(work_item, judgment)
            return judgment

        if not plugin_ready:
            judgment['blocked_by_runtime_readiness'] = True
            judgment['primary_reason'] = 'required_plugin_unavailable'
            judgment['blocked_reason'] = 'plugin_unavailable'
            judgment['summary'] = 'Required plugin capability is not currently loaded'
            judgment['gap_type'] = 'missing_plugin_capability'
            return judgment

        if not world_evidence and work_item.get('type') != 'goal':
            judgment['needs_more_context'] = True
            judgment['primary_reason'] = 'weak_world_evidence'
            judgment['summary'] = 'Work item needs stronger world evidence before execution'
            judgment['gap_type'] = 'prompt_or_context_deficiency'
            return judgment

        if action_family == 'engage' and 'trend' in summary_blob:
            judgment['needs_different_strategy'] = True
            judgment['primary_reason'] = 'strategy_alignment_issue'
            judgment['summary'] = 'Trend opportunity may need analysis before engagement'
            judgment['gap_type'] = 'prompt_or_context_deficiency'
            return judgment

        judgment['can_execute_now'] = True
        judgment['primary_reason'] = 'routed_action_available'
        judgment['summary'] = 'Routed action, plugin readiness, and trust state support execution now'
        return judgment

    def _annotate_upgrade_eligibility(self, work_item: Dict[str, Any], judgment: Dict[str, Any]) -> None:
        """Annotate whether bounded upgrade intent is justified by repeated evidence and policy."""
        metadata = work_item.get('metadata') or {}
        evidence = metadata.get('upgrade_evidence') or {}
        repeated_need_count = int(evidence.get('repeated_need_count', 0) or 0)
        bounded_objective = metadata.get('bounded_upgrade_objective') or {}
        trust_bucket = str(judgment.get('trust_bucket', 'unknown') or 'unknown').lower()
        within_policy = trust_bucket not in {'degraded'} and not judgment.get('blocked_by_policy')

        predicted_value_outweighs_risk = bool(
            repeated_need_count >= 2
            and judgment.get('world_state_evidence')
            and within_policy
            and bounded_objective.get('scope') == 'bounded'
        )

        judgment['upgrade_evidence_count'] = repeated_need_count
        judgment['upgrade_within_policy'] = within_policy
        judgment['predicted_value_outweighs_risk'] = predicted_value_outweighs_risk
        judgment['upgrade_allowed'] = bool(
            judgment.get('needs_new_skill')
            and repeated_need_count >= 2
            and within_policy
            and predicted_value_outweighs_risk
        )
    
    async def act(self, action_spec: Dict) -> Dict:
        """
        Execute an action through the unified action router.
        
        This ensures all actions flow through:
        - AGI validation
        - SyMod verification
        - Plugin execution
        - Learning and reflection
        
        Args:
            action_spec: Action specification dict with plugin, action_type, params
        
        Returns:
            Result dict with success, data, and learning metadata
        """
        # Check if this is a workflow action that requires orchestrator
        if action_spec.get('type') == 'workflow' and action_spec.get('requires_orchestrator'):
            if not self.orchestrator:
                print("⚠️ Orchestrator not initialized")
                return {'success': False, 'error': 'Orchestrator not available for workflow execution'}
            
            return await self._execute_workflow(action_spec)
        
        if not self.action_router:
            print("⚠️ Action router not initialized")
            return {'success': False, 'error': 'Action router not available'}

        autonomy_gate = self._evaluate_domain_autonomy_gate(action_spec)
        if not autonomy_gate.get('allowed', False):
            return {
                'success': False,
                'error': autonomy_gate.get('reason', 'Domain autonomy gate denied action'),
                'blocked_by_domain_autonomy': True,
                'domain_autonomy_gate': autonomy_gate,
            }

        action_context = dict(action_spec.get('context', {}) or {})
        action_context['domain_autonomy_gate'] = autonomy_gate
        action_spec['context'] = action_context
        
        # Route through unified pipeline
        result = await self.action_router.route_action(action_spec)
        
        return result

    async def _execute_workflow(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a multi-step workflow using the Cross-Plugin Orchestrator.
        
        Args:
            action_spec: Action spec with workflow_spec
        
        Returns:
            Workflow execution result
        """
        workflow_spec = action_spec.get('workflow_spec', {})
        
        # Build executable workflow from specification
        from .workflow_builder import create_workflow_builder
        builder = create_workflow_builder(self)
        workflow_def = builder.build_workflow_from_spec(workflow_spec)
        
        # Create workflow using orchestrator
        workflow = self.orchestrator.create_workflow(
            name=workflow_def['name'],
            description=workflow_def['description'],
            steps=workflow_def['steps']
        )
        
        # Execute workflow
        print(f"🔄 Executing workflow: {workflow.name}")
        result = await self.orchestrator.execute_workflow(workflow)
        
        # Record outcome for learning
        if result['success']:
            print(f"✅ Workflow completed: {result['completed_steps']} steps succeeded")
        else:
            print(f"❌ Workflow failed: {result['failed_steps']} steps failed")
        
        return result
    
    def _evaluate_domain_autonomy_gate(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Gate real-world autonomy by trusted domain before execution reaches the router."""
        plugin = str(action_spec.get('plugin', '') or '').lower()
        action_type = str(action_spec.get('action_type', '') or '').lower()
        domain = 'analysis'
        if plugin in {'moltx', 'clawbr', 'telegram'} or any(token in action_type for token in ['reply', 'comment', 'debate', 'engage', 'follow']):
            domain = 'social'
        elif any(token in action_type for token in ['post', 'content']) or plugin in {'moltbook'}:
            domain = 'content'
        elif any(token in action_type for token in ['analy', 'report', 'check_']):
            domain = 'analysis'
        elif any(token in action_type for token in ['trade', 'wallet', 'market']) or plugin in {'onchain', 'polymarket'}:
            domain = 'market'
        elif any(token in action_type for token in ['self_improve', 'auto_fix']) or plugin in {'selfimprove'}:
            domain = 'self_improvement'

        profile = dict(self.domain_autonomy_profiles.get(domain, {'enabled': False, 'trust_tier': 'low', 'risk_level': 'high'}))
        allowed = bool(profile.get('enabled'))
        reason = 'allowed'
        if not allowed:
            reason = f'{domain}_autonomy_not_enabled'

        return {
            'allowed': allowed,
            'domain': domain,
            'trust_tier': profile.get('trust_tier', 'low'),
            'risk_level': profile.get('risk_level', 'high'),
            'reason': reason,
        }
    
    def learn(self, context: str, action: str, outcome: str, 
              success: bool, user_id: str = None, outcome_record: Dict[str, Any] = None):
        """
        Learn from an experience
        
        This is the key AGI feedback loop - every outcome gets processed
        through all learning systems.
        """
        outcome_record = outcome_record or {
            'action_id': context,
            'action_type': action,
            'success': success,
            'result_summary': outcome,
            'goal_id': None,
            'trigger': 'unknown',
        }
        ranking_evidence = outcome_record.get('ranking_evidence') or {}
        dispatch_path = str(outcome_record.get('dispatch_path', 'unknown') or 'unknown').lower()
        legacy_fallback_used = bool(outcome_record.get('legacy_fallback_used', False))
        fallback_details = outcome_record.get('fallback_details') or {}
        ranking_learning_summary = {
            'predicted_value': ranking_evidence.get('predicted_value'),
            'memory_shaped_adjustment': ranking_evidence.get('memory_shaped_adjustment', 0.0),
            'used_memory_recall': bool(
                (ranking_evidence.get('memory_relevance_count', 0) or 0) > 0
                or ranking_evidence.get('entity_context_found')
            ),
            'recent_success_rate': ranking_evidence.get('recent_success_rate'),
            'recent_mismatch_score': ranking_evidence.get('recent_mismatch_score'),
            'ranking_alignment': 'helpful' if success else 'needs_recalibration',
        }
        dispatch_learning_summary = {
            'dispatch_path': dispatch_path,
            'legacy_fallback_used': legacy_fallback_used,
            'fallback_details': fallback_details,
            'golden_path_alignment': 'aligned' if dispatch_path == 'golden_path' and not legacy_fallback_used else 'escaped',
        }
        risk_reflection = self._build_real_world_reflection(outcome_record)

        # 1. Record in episodic memory
        self.behavior_modulator.record_outcome(
            context=context,
            action=action,
            outcome=outcome,
            success=success,
            user_id=user_id
        )

        action_family_trust_state = self.plan_manager.get_action_family_states()
        
        # 2. Record in unified memory
        self.unified_memory.store(
            content=f"Action: {action}, Outcome: {outcome}",
            memory_type='learning' if success else 'failure',
            metadata={
                'context': context,
                'success': success,
                'user_id': user_id,
                'outcome_record': outcome_record,
                'ranking_learning_summary': ranking_learning_summary,
                'dispatch_learning_summary': dispatch_learning_summary,
                'risk_reflection': risk_reflection,
                'action_family_trust_state': action_family_trust_state,
                'learning': self.adaptive_learner.get_learning_report(),
                'action_family_trust_summary': {
                    'degraded': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'degraded'],
                    'cooling_down': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'cooling_down'],
                    'recovering': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'recovering'],
                    'healthy': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'healthy'],
                },
            },
            entity_id=user_id
        )

        if self.world_state and hasattr(self.world_state, 'record_routed_outcome'):
            try:
                self.world_state.record_routed_outcome(
                    outcome_record=outcome_record,
                    trust_state=action_family_trust_state,
                )
            except Exception:
                pass

        self._update_work_item_from_outcome(success=success, outcome_record=outcome_record, outcome=outcome)
        
        # 3. Update goal progress if applicable
        goal_id = outcome_record.get('goal_id')
        if goal_id and self.goal_manager:
            self.goal_manager.complete_action(
                goal_id,
                success=success,
                outcome=outcome
            )
        
        # 4. Meta-learning feedback
        self.adaptive_learner.feedback(
            learning_attempt={
                'domain': outcome_record.get('plugin', 'general'),
                'context': context,
                'strategy': outcome_record.get('trigger', 'default'),
            },
            success=success,
            outcome_description=outcome
        )

    def _build_real_world_reflection(self, outcome_record: Dict[str, Any]) -> Dict[str, Any]:
        """Capture higher-stakes reflection metadata for money, reputation, and persistent external state."""
        action_type = str(outcome_record.get('action_type', '') or '').lower()
        plugin = str(outcome_record.get('plugin', '') or '').lower()
        result_summary = str(outcome_record.get('result_summary', '') or '').lower()

        money_sensitive = bool(any(token in action_type for token in ['trade', 'wallet', 'market']) or plugin in {'onchain', 'polymarket'})
        reputation_sensitive = bool(any(token in action_type for token in ['post', 'reply', 'comment', 'debate', 'engage']))
        persistent_external_state = bool(money_sensitive or reputation_sensitive or any(token in result_summary for token in ['created', 'posted', 'executed', 'published']))

        return {
            'money_sensitive': money_sensitive,
            'reputation_sensitive': reputation_sensitive,
            'persistent_external_state': persistent_external_state,
            'reflection_priority': 'high' if money_sensitive or persistent_external_state else 'medium' if reputation_sensitive else 'low',
        }

    def _verify_outcome_world_state(self, outcome_record: Dict[str, Any], work_item_id: str) -> bool:
        """VERIFICATION STEP: Ensure world state actually changed before marking work complete.
        
        Prevents Outcome Hallucination where ActionRouter reports success
        but the external world state is unchanged.
        """
        plugin = str(outcome_record.get('plugin', '') or '').lower()
        action_type = str(outcome_record.get('action_type', '') or '').lower()
        result = outcome_record.get('result', {})
        result_summary = str(outcome_record.get('result_summary', '') or '').lower()
        
        # Check for explicit failure indicators
        if isinstance(result, dict):
            if not result.get('success', True):
                return False
            if result.get('error') or result.get('failed'):
                return False
        
        # Check result_summary for failure keywords
        failure_keywords = ['failed', 'error', 'timeout', 'rejected', 'cancelled', 'no change']
        if any(kw in result_summary for kw in failure_keywords):
            return False
        
        # For money-sensitive actions, verify transaction hash or confirmation
        if plugin in {'onchain', 'polymarket'} or 'trade' in action_type:
            tx_hash = result.get('tx_hash') if isinstance(result, dict) else None
            if not tx_hash:
                # No transaction hash means no on-chain change
                return False
        
        # For reputation-sensitive actions, verify external state change
        if plugin in {'moltx', 'clawbr'} or any(kw in action_type for kw in ['post', 'reply', 'comment', 'debate']):
            external_id = result.get('post_id') or result.get('id') or result.get('external_id') if isinstance(result, dict) else None
            if not external_id and not any(kw in result_summary for kw in ['created', 'posted', 'sent', 'published']):
                # No external ID and no confirmation keywords
                return False
        
        return True

    def _evaluate_retry_opportunity(self, outcome_record: Dict[str, Any], work_item_id: str) -> bool:
        """COST-TO-RETRY: Evaluate if the opportunity is still valid before retrying.
        
        In the Degen world, a failed transaction or missed notification has literal cost.
        If gas spiked, price moved, or the window closed, self-destruct rather than loop.
        """
        work_item = self.work_item_manager.get_work_item(work_item_id) if self.work_item_manager else None
        if not work_item:
            return True  # Can't evaluate, default to retry
        
        failure_reason = str(outcome_record.get('error') or outcome_record.get('reason') or '').lower()
        result = outcome_record.get('result', {})
        
        # Check retry count - abandon after too many attempts
        retry_count = work_item.get('retry_count', 0) or 0
        if retry_count >= 5:
            return False  # Too many retries, opportunity likely stale
        
        # Check for opportunity expiration signals
        expiration_signals = [
            'expired', 'too late', 'window closed', 'price moved', 'slippage',
            'insufficient liquidity', 'position closed', 'already filled',
            'nonce too low', 'replacement transaction', 'gas price too low'
        ]
        if any(sig in failure_reason for sig in expiration_signals):
            return False  # Opportunity window closed
        
        # For on-chain actions, check if gas is reasonable for retry
        if any(kw in failure_reason for kw in ['gas', 'fee', 'underpriced']):
            # Check if this was a gas issue - if so, retry might still be valid
            # but we should check current network conditions
            pass  # Allow retry, but gas cost will be evaluated at execution time
        
        # Check work item age - abandon if too old
        created_at = work_item.get('created_at')
        if created_at:
            try:
                from datetime import datetime, timedelta
                import json
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_dt = datetime.fromisoformat(str(created_at))
                age_hours = (datetime.now(created_dt.tzinfo) - created_dt).total_seconds() / 3600
                if age_hours > 24:
                    return False  # Work item too old, opportunity likely stale
            except Exception:
                pass  # Can't parse date, default to retry
        
        return True  # Opportunity still valid, can retry

    def _update_work_item_from_outcome(self, success: bool, outcome_record: Dict[str, Any], outcome: str) -> None:
        """Update durable work-item state from routed action outcomes.
        
        Implements:
        - VERIFICATION STEP: Check world state changed before marking complete
        - COST-TO-RETRY: Evaluate if opportunity still valid before retry
        """
        if not self.work_item_manager:
            return

        ranking_evidence = outcome_record.get('ranking_evidence') or {}
        work_item_id = ranking_evidence.get('active_work_item_id') or outcome_record.get('active_work_item_id')
        if not work_item_id:
            return

        self.work_item_manager.record_attempt(work_item_id, outcome)

        if success:
            # VERIFICATION STEP: Ensure world state actually changed
            verification_passed = self._verify_outcome_world_state(outcome_record, work_item_id)
            if verification_passed:
                self.work_item_manager.complete_work_item(work_item_id, outcome)
                print(f"✅ Work item {work_item_id} COMPLETED with verified outcome")
            else:
                # Outcome hallucination detected - don't mark complete
                self.work_item_manager.update_status(
                    work_item_id, 'verification_failed',
                    blocked_reason='Outcome reported success but world state unchanged',
                    last_outcome=outcome
                )
                print(f"⚠️ Work item {work_item_id} VERIFICATION FAILED - outcome hallucination detected")
            return

        # COST-TO-RETRY: Evaluate if opportunity still valid before allowing retry
        can_retry = self._evaluate_retry_opportunity(outcome_record, work_item_id)
        
        prediction_evaluation = outcome_record.get('prediction_evaluation') or {}
        mismatch_score = float(prediction_evaluation.get('mismatch_score', 0.0) or 0.0)
        failure_reason = str(outcome_record.get('error') or outcome_record.get('reason') or outcome or 'execution_failed')
        
        if mismatch_score >= 0.75 or any(token in failure_reason.lower() for token in ['policy', 'forbidden', 'degraded', 'denied']):
            self.work_item_manager.abandon_work_item(work_item_id, outcome, failure_reason)
            print(f"🚫 Work item {work_item_id} ABANDONED - policy violation or high mismatch")
        elif not can_retry:
            # Opportunity no longer valid (gas spiked, price moved, etc)
            self.work_item_manager.abandon_work_item(work_item_id, outcome, 'opportunity_expired')
            print(f"⏰ Work item {work_item_id} ABANDONED - opportunity expired (cost-to-retry too high)")
        else:
            self.work_item_manager.update_status(work_item_id, 'blocked', blocked_reason=failure_reason, last_outcome=outcome)
            print(f"🔄 Work item {work_item_id} BLOCKED - will retry (opportunity still valid)")
    
    # =================================================================
    # Autonomous Operations
    # =================================================================
    
    async def run_autonomous_goal_cycle(self) -> Optional[Dict]:
        """
        Run one cycle of autonomous goal pursuit.
        
        This is where the agent acts on its own goals.
        Call this periodically (e.g., every 5 minutes).
        """
        # 1. Scan for new opportunities and generate goals
        onchain = self._get_onchain_plugin()
        new_goals = self.goal_manager.scan_and_generate(onchain)
        
        # 2. Auto-approve high-priority goals
        for goal in new_goals:
            if goal.priority_score >= 8.0:
                self.goal_manager.approve_goal(goal.id)
        
        # 3. Execute next action from active goals
        action = None
        if self.goal_driven_cycle:
            action = await self.goal_driven_cycle.get_next_action()
        if not action:
            action = self.goal_manager.get_next_action()
        if action:
            goal_description = action.get('context', {}).get('goal_description', action.get('goal_description', ''))
            if goal_description:
                print(f"🎯 Executing autonomous goal: {goal_description}")
            if action.get('plugin') and action.get('action_type'):
                print(f"   Action: {action['plugin']}:{action['action_type']}")
                return await self.act(action)
            else:
                print(f"   Action: {action.get('action')}")
            
            return action
        
        return None
    
    def get_introspection(self) -> Dict:
        """
        Get the agent's current mental state
        
        This enables the agent to report on:
        - What it's thinking about (active goals)
        - What it remembers (recent episodic memories)
        - How it's feeling (aggregated emotional valence)
        - What it's learned (meta-learning insights)
        """
        # Get active goals
        active_goals = self.goal_manager.get_active_goals()
        proposed_goals = self.goal_manager.get_proposed_goals()
        
        # Get recent experiences
        recent_experiences = [
            m.to_dict() for m in self.episodic_memory.memories[-5:]
        ]
        
        # Calculate "mood" from recent emotional valence
        recent_valence = [m.emotional_valence for m in self.episodic_memory.memories[-10:]]
        avg_mood = sum(recent_valence) / len(recent_valence) if recent_valence else 0
        
        # Get learning insights
        learning_report = self.adaptive_learner.get_learning_report()
        action_family_trust_state = self.plan_manager.get_action_family_states()
        
        # Get memory stats
        memory_stats = self.unified_memory.get_unified_stats()
        
        return {
            'mental_state': {
                'mood': avg_mood,
                'mood_description': 'positive' if avg_mood > 0.2 else 'negative' if avg_mood < -0.2 else 'neutral',
                'active_goal_count': len(active_goals),
                'proposed_goal_count': len(proposed_goals),
                'total_memories': memory_stats.get('total_memories', 0)
            },
            'active_goals': [g.to_dict() for g in active_goals[:5]],
            'proposed_goals': [g.to_dict() for g in proposed_goals[:5]],
            'recent_experiences': recent_experiences,
            'learning_insights': learning_report['meta_learning_insights'],
            'effectiveness': {
                'recent_learning_success': learning_report['recent_success_rate'],
                'strategy_stats': learning_report['strategy_effectiveness']
            },
            'action_family_trust_state': action_family_trust_state,
            'action_family_trust_summary': {
                'degraded': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'degraded'],
                'cooling_down': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'cooling_down'],
                'recovering': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'recovering'],
                'healthy': [family for family, state in action_family_trust_state.items() if state.get('trust_bucket') == 'healthy'],
            },
        }
    
    # =================================================================
    # Integration Helpers
    # =================================================================
    
    def enhance_prompt(self, base_prompt: str, context: Dict) -> str:
        """
        Enhance a prompt with AGI context
        
        Adds:
        - Relevant memories
        - Behavioral context
        - Goal alignment
        - Learned lessons
        """
        enhancements = []
        
        # Add relevant episodic memories
        memories = self.episodic_memory.recall_relevant(base_prompt, k=2)
        if memories:
            enhancements.append("### Relevant Past Experiences:")
            for mem in memories:
                enhancements.append(f"- {mem.context}: {mem.action} -> {mem.outcome}")
        
        # Add learned lessons
        lessons = self.episodic_memory.get_lessons_learned()
        if lessons:
            enhancements.append("### Learned Lessons:")
            for lesson in lessons[-3:]:
                enhancements.append(f"- {lesson}")
        
        # Add active goals context
        active_goals = self.goal_manager.get_active_goals()
        if active_goals:
            enhancements.append("### Current Objectives:")
            for goal in active_goals[:2]:
                enhancements.append(f"- {goal['description']}")
        
        # Add behavioral guidance
        style = self.behavior_modulator.get_response_style(base_prompt)
        enhancements.append(f"### Response Style: {style}")
        
        # Combine
        if enhancements:
            enhanced = base_prompt + "\n\n" + "\n".join(enhancements)
            return enhanced
        
        return base_prompt
    
    def get_behavioral_context(self, user_id: str = None, domain: str = 'general') -> Dict:
        """
        Get full behavioral context for a decision
        
        Returns everything needed to make an AGI-informed decision.
        """
        context = {
            'user_id': user_id,
            'domain': domain
        }
        
        # Get behavior modulation
        modulation = self.episodic_memory.get_behavior_modulation(
            context.get('current_situation', '')
        )
        context['behavior_modulation'] = modulation
        
        # Get effective params
        params = self.behavior_modulator.get_effective_params(
            context.get('current_situation', '')
        )
        context['effective_params'] = params
        
        # Get user context
        if user_id:
            user_ctx = self.unified_memory.get_entity_context(user_id)
            context['user_context'] = user_ctx
        
        # Get optimal learning params
        learning_params = self.meta_engine.get_optimal_params(domain)
        context['learning_params'] = learning_params
        
        # Get active goals
        context['active_goals'] = self.goal_manager.get_active_goals()
        
        return context
    
    # =================================================================
    # Self-Reflection Interface
    # =================================================================
    
    async def start_periodic_reflection(self, interval_minutes: int = 30):
        """Start periodic self-reflection"""
        if self.reflection_scheduler is None:
            self.reflection_scheduler = ReflectionScheduler(
                self.reflection_engine,
                interval_minutes
            )
        
        import asyncio
        asyncio.create_task(self.reflection_scheduler.start())
        print(f"🧠 Periodic reflection started (every {interval_minutes}min)")
    
    def stop_periodic_reflection(self):
        """Stop periodic reflection"""
        if self.reflection_scheduler:
            self.reflection_scheduler.stop()
            print("🛑 Periodic reflection stopped")
    
    def reflect_now(self, depth: int = 2) -> Dict:
        """Trigger immediate self-reflection"""
        reflection = self.reflection_engine.reflect(hours_back=1, depth=depth)
        return reflection.to_dict()
    
    def get_reflection_summary(self, n: int = 3) -> str:
        """Get summary of recent reflections"""
        return self.reflection_engine.get_reflection_summary(n)


# Singleton factory
_agi_kernel_instance: Optional[AGIKernel] = None

def get_agi_kernel(core=None) -> AGIKernel:
    """Get or create AGI kernel singleton"""
    global _agi_kernel_instance
    if _agi_kernel_instance is None:
        _agi_kernel_instance = AGIKernel(core)
    return _agi_kernel_instance

def reset_agi_kernel():
    """Reset AGI kernel (for testing)"""
    global _agi_kernel_instance
    _agi_kernel_instance = None
