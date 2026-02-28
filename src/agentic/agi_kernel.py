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
        
        # Initialize all AGI subsystems
        self.unified_memory = create_unified_memory(core)
        self.episodic_memory = create_episodic_memory()
        self.behavior_modulator = BehaviorModulator(self.episodic_memory)
        
        # SyMod mathematical validation layer (core system)
        self.symod = get_symod_manager(core)
        print("🔢 SyMod Core Manager initialized")
        
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
        
        # Behavior modulator (episodic learning feedback loop)
        self.behavior_modulator = None  # Initialized with episodic memory
        
        # Goal-driven cycle (autonomous goal pursuit)
        self.goal_driven_cycle = None  # Initialized after goal_stack available
        
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
        
        # Use decision system for autonomous thinking
        action = self.decision_system.decide_next_action(context)
        
        if action:
            print(f"🧠 AGI decided: {action.get('id')} ({action.get('decision_method', 'unknown')})")
        
        return action
    
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
        if not self.action_router:
            print("⚠️ Action router not initialized")
            return {'success': False, 'error': 'Action router not available'}
        
        # Route through unified pipeline
        result = await self.action_router.route_action(action_spec)
        
        return result
    
    def learn(self, context: str, action: str, outcome: str, 
              success: bool, user_id: str = None):
        """
        Learn from an experience
        
        This is the key AGI feedback loop - every outcome gets processed
        through all learning systems.
        """
        # 1. Record in episodic memory
        self.behavior_modulator.record_outcome(
            context=context,
            action=action,
            outcome=outcome,
            success=success,
            user_id=user_id
        )
        
        # 2. Record in unified memory
        self.unified_memory.store(
            content=f"Action: {action}, Outcome: {outcome}",
            memory_type='learning' if success else 'failure',
            metadata={
                'context': context,
                'success': success,
                'user_id': user_id
            },
            entity_id=user_id
        )
        
        # 3. Update goal progress if applicable
        if success and self.goal_manager:
            # Try to complete current goal step
            active = self.goal_manager.get_next_action()
            if active:
                self.goal_manager.complete_action(
                    active['goal_id'],
                    success=True,
                    outcome=outcome
                )
        
        # 4. Meta-learning feedback
        self.adaptive_learner.feedback(
            learning_attempt={'domain': 'general', 'context': context, 'strategy': 'default'},
            success=success,
            outcome_description=outcome
        )
    
    # =================================================================
    # Autonomous Operations
    # =================================================================
    
    async def run_autonomous_cycle(self):
        """
        Run one cycle of autonomous operation
        
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
        action = self.goal_manager.get_next_action()
        if action:
            print(f"🎯 Executing autonomous goal: {action['goal_description']}")
            print(f"   Action: {action['action']}")
            
            # In practice, this would actually execute the action
            # For now, just log it
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
            'active_goals': active_goals,
            'proposed_goals': proposed_goals,
            'recent_experiences': recent_experiences,
            'learning_insights': learning_report['meta_learning_insights'],
            'effectiveness': {
                'recent_learning_success': learning_report['recent_success_rate'],
                'strategy_stats': learning_report['strategy_effectiveness']
            }
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
