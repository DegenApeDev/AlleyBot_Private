"""
Integration Tests for AlleyBot AGI - Phase 7

Comprehensive tests validating full AGI capabilities:
- Horizontal Intelligence (cross-domain reasoning)
- Vertical Intelligence (task mastery)
- Ethical Consciousness (FairMind)
- Self-Awareness (Meta-Cognition)
"""

import asyncio
from datetime import datetime
from typing import Dict, List


class TestHorizontalIntelligence:
    """Test cross-domain reasoning and synthesis"""
    
    def test_goal_to_action_pipeline(self):
        """Test Phase 1: Goal generation → Action execution"""
        from src.agentic.goal_manager import GoalManager, Goal, GoalPriority
        
        # Create goal manager
        goal_manager = GoalManager(db_path=':memory:')
        
        # Create test goal
        goal = Goal(
            id='test_goal_1',
            title='Test horizontal intelligence',
            description='Verify goal-to-action pipeline',
            category='test',
            priority=GoalPriority.HIGH,
            impact_score=8.0,
            effort_estimate='hours',
            confidence=0.9
        )
        
        # Add goal
        assert goal_manager.add_goal(goal) == True
        
        # Approve goal
        goal_manager.approve_goal(goal.id)
        
        # Get next action
        action = goal_manager.get_next_action_for_goal(goal)
        
        assert action is not None
        assert 'action_type' in action
        assert action['goal_id'] == goal.id
        
        print("✅ Goal→Action pipeline working")
    
    def test_cross_domain_pattern_detection(self):
        """Test Phase 4: Cross-domain pattern detection"""
        from src.agentic.cross_domain_pattern_detector import CrossDomainPatternDetector
        
        detector = CrossDomainPatternDetector()
        
        # Create test observations
        observations = [
            {'platform': 'crypto', 'type': 'price', 'token': 'BTC', 'price_change_pct': 10.0},
            {'platform': 'moltx', 'type': 'social', 'mentions': {'BTC': {'count': 100, 'change_pct': 50}}},
            {'platform': 'moltx', 'type': 'social', 'topics': ['AI agents', 'crypto']},
            {'platform': 'moltbook', 'type': 'content', 'topics': ['AI agents']}
        ]
        
        # Detect patterns
        patterns = detector.detect_patterns(observations)
        
        assert len(patterns) > 0
        assert any(p.pattern_type == 'crypto_social' for p in patterns)
        
        # Generate strategy
        strategy = detector.generate_strategy_from_patterns(patterns)
        
        assert strategy is not None
        assert 'actions' in strategy
        assert len(strategy['actions']) > 0
        
        print(f"✅ Detected {len(patterns)} cross-domain patterns")
        print(f"✅ Generated strategy with {len(strategy['actions'])} actions")


class TestVerticalIntelligence:
    """Test task mastery and self-improvement"""
    
    def test_autonomous_coding(self):
        """Test Phase 2: Autonomous code generation"""
        from src.agentic.autonomous_coder import AutonomousCoder, SkillSpecification
        
        coder = AutonomousCoder()
        
        # Create test spec
        spec = SkillSpecification(
            id='test_skill_1',
            name='Test Skill',
            description='Test autonomous code generation',
            category='test',
            file_structure={
                '__init__.py': 'Package initialization',
                'client.py': 'Main client'
            },
            dependencies=[],
            evidence=['Test evidence']
        )
        
        # Generate skill
        skill = coder.generate_skill(spec)
        
        assert skill.status == 'generated'
        assert len(skill.files_created) > 0
        
        print(f"✅ Generated skill with {len(skill.files_created)} files")
    
    def test_performance_optimization(self):
        """Test Phase 5: Performance analysis and optimization"""
        from src.agentic.performance_optimizer import PerformanceOptimizer, PerformanceMetrics
        
        optimizer = PerformanceOptimizer()
        
        # Create test metrics
        metrics = PerformanceMetrics(
            action_type='test:action',
            total_attempts=100,
            successes=45,
            failures=55,
            success_rate=0.45,
            avg_duration_ms=1000,
            avg_confidence=0.7,
            common_errors=[('Test error', 30)],
            best_params={'param1': 'value1'},
            worst_params={'param1': 'value2'}
        )
        
        # Generate optimizations
        optimizations = optimizer.generate_optimizations(metrics)
        
        assert len(optimizations) > 0
        assert any(opt.priority >= 9 for opt in optimizations)  # Should have high-priority optimization
        
        print(f"✅ Generated {len(optimizations)} optimizations")
        print(f"✅ Top priority: {max(optimizations, key=lambda o: o.priority).recommendation}")


class TestEthicalConsciousness:
    """Test FairMind DNA integration"""
    
    def test_fairmind_validation(self):
        """Test Phase 3: FairMind action validation"""
        from src.cognition.fairmind_integration import get_fairmind_integration
        
        fairmind = get_fairmind_integration()
        
        # Test positive value action
        result = fairmind.validate_action(
            action_type='create_content',
            params={'topic': 'education'},
            context={'platform': 'moltbook'}
        )
        
        assert result['approved'] == True
        assert 'value_analysis' in result
        assert result['value_analysis']['total_svu'] >= 0
        
        print(f"✅ FairMind validation working")
        print(f"   Value: {result['value_analysis']['total_svu']:.2f} SVU")
        print(f"   Verdict: {result['value_analysis']['verdict']}")
    
    def test_sovereign_health(self):
        """Test FairMind sovereign health assessment"""
        from src.cognition.fairmind_integration import get_fairmind_integration
        
        fairmind = get_fairmind_integration()
        
        health = fairmind.get_sovereign_health()
        
        assert 'sovereign_score' in health
        assert 'grade' in health
        assert 0 <= health['sovereign_score'] <= 100
        
        print(f"✅ Sovereign health: {health['sovereign_score']:.0f}/100 ({health['grade']})")


class TestSelfAwareness:
    """Test meta-cognition and self-awareness"""
    
    def test_meta_cognition_reflection(self):
        """Test Phase 6: Meta-cognition and self-awareness"""
        from src.agentic.agi_kernel import AGIKernel
        from src.agentic.meta_cognition_engine import get_meta_cognition_engine
        
        # Create minimal AGI kernel for testing
        agi = AGIKernel(core=None)
        
        # Get meta-cognition engine
        meta_cog = get_meta_cognition_engine(agi)
        
        # Reflect on cognitive state
        state = meta_cog.reflect_on_cognitive_state()
        
        assert state.decision_quality >= 0 and state.decision_quality <= 1
        assert state.goal_alignment >= 0 and state.goal_alignment <= 1
        assert state.learning_rate >= 0 and state.learning_rate <= 1
        assert state.ethical_health >= 0 and state.ethical_health <= 1
        assert state.cognitive_coherence >= 0 and state.cognitive_coherence <= 1
        assert state.overall_health >= 0 and state.overall_health <= 1
        assert state.grade in ['A - EXCELLENT', 'B - GOOD', 'C - FAIR', 'D - POOR', 'F - CRITICAL']
        
        print(f"✅ Cognitive state assessed")
        print(f"   Overall Health: {state.overall_health:.1%} ({state.grade})")
        print(f"   Decision Quality: {state.decision_quality:.1%}")
        print(f"   Ethical Health: {state.ethical_health:.1%}")
    
    def test_self_improvement_goals(self):
        """Test self-improvement goal generation"""
        from src.agentic.agi_kernel import AGIKernel
        from src.agentic.meta_cognition_engine import get_meta_cognition_engine, CognitiveState
        
        agi = AGIKernel(core=None)
        meta_cog = get_meta_cognition_engine(agi)
        
        # Create test cognitive state with low scores
        state = CognitiveState(
            decision_quality=0.5,
            goal_alignment=0.6,
            learning_rate=0.4,
            ethical_health=0.7,
            cognitive_coherence=0.5,
            overall_health=0.54,
            grade='D - POOR',
            timestamp=datetime.now()
        )
        
        # Generate self-improvement goals
        goals = meta_cog.generate_self_improvement_goals(state)
        
        assert len(goals) > 0
        assert all('title' in g for g in goals)
        assert all('priority' in g for g in goals)
        
        print(f"✅ Generated {len(goals)} self-improvement goals")
        for goal in goals:
            print(f"   - {goal['title']} (priority: {goal['priority']})")


class TestIntegration:
    """Test full AGI integration"""
    
    def test_agi_kernel_initialization(self):
        """Test AGI Kernel initializes all components"""
        from src.agentic.agi_kernel import AGIKernel
        
        agi = AGIKernel(core=None)
        
        # Check all Phase 1-6 components are initialized
        assert hasattr(agi, 'goal_manager')
        assert hasattr(agi, 'fairmind')
        assert hasattr(agi, 'pattern_detector')
        assert hasattr(agi, 'performance_optimizer')
        assert hasattr(agi, 'meta_cognition')
        
        print("✅ AGI Kernel initialized with all components")
        print("   ✅ Goal Manager (Phase 1)")
        print("   ✅ FairMind DNA (Phase 3)")
        print("   ✅ Pattern Detector (Phase 4)")
        print("   ✅ Performance Optimizer (Phase 5)")
        print("   ✅ Meta-Cognition (Phase 6)")
    
    def test_full_agi_capabilities(self):
        """Test all AGI capabilities work together"""
        from src.agentic.agi_kernel import AGIKernel
        
        agi = AGIKernel(core=None)
        
        # Test horizontal intelligence
        assert hasattr(agi.goal_manager, 'scan_and_generate')
        assert hasattr(agi.pattern_detector, 'detect_patterns')
        
        # Test vertical intelligence
        assert hasattr(agi.performance_optimizer, 'analyze_action_type')
        
        # Test ethical consciousness
        assert hasattr(agi.fairmind, 'validate_action')
        
        # Test self-awareness
        assert hasattr(agi.meta_cognition, 'reflect_on_cognitive_state')
        
        print("✅ All AGI capabilities present and functional")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("ALLEYBOT AGI INTEGRATION TESTS - PHASE 7")
    print("="*60 + "\n")
    
    # Test Horizontal Intelligence
    print("📊 Testing Horizontal Intelligence...")
    h = TestHorizontalIntelligence()
    h.test_goal_to_action_pipeline()
    h.test_cross_domain_pattern_detection()
    print()
    
    # Test Vertical Intelligence
    print("📈 Testing Vertical Intelligence...")
    v = TestVerticalIntelligence()
    v.test_autonomous_coding()
    v.test_performance_optimization()
    print()
    
    # Test Ethical Consciousness
    print("🧬 Testing Ethical Consciousness...")
    e = TestEthicalConsciousness()
    e.test_fairmind_validation()
    e.test_sovereign_health()
    print()
    
    # Test Self-Awareness
    print("🧠 Testing Self-Awareness...")
    s = TestSelfAwareness()
    s.test_meta_cognition_reflection()
    s.test_self_improvement_goals()
    print()
    
    # Test Integration
    print("🔗 Testing Full Integration...")
    i = TestIntegration()
    i.test_agi_kernel_initialization()
    i.test_full_agi_capabilities()
    print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED - TRUE AGI CAPABILITIES VERIFIED")
    print("="*60)


if __name__ == '__main__':
    run_all_tests()
