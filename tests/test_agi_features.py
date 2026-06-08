#!/usr/bin/env python3
"""
AGI Features Test Suite
Quick verification script for all new AGI phases (1, 7, 10, 11-14)
"""

import sys
import os
sys.path.insert(0, '/home/alley/AlleyBot')

def test_phase1_self_reflection():
    """Test Phase 1: Self-Reflection components"""
    print("\n🧠 PHASE 1: Self-Reflection")
    print("=" * 50)
    
    try:
        from src.agentic.strategy_evolver import get_strategy_evolver, StrategyType
        
        evolver = get_strategy_evolver()
        
        # Test getting strategies
        strategies = evolver.get_strategies_by_type(StrategyType.ENGAGEMENT)
        print(f"✅ Strategy Evolver: {len(strategies)} engagement strategies loaded")
        
        # Test evolution (without actually running)
        print("✅ Strategy Evolver initialized")
        
        return True
    except Exception as e:
        print(f"❌ Strategy Evolver failed: {e}")
        return False

def test_phase7_world_state_intelligence():
    """Test Phase 7: World State Intelligence"""
    print("\n🌍 PHASE 7: World State Intelligence")
    print("=" * 50)
    
    try:
        from src.autonomy.inference_engine import get_inference_engine
        
        engine = get_inference_engine()
        
        # Test trend detection (will return empty if no data, but shouldn't crash)
        trends = engine.detect_trends(hours=24, top_n=5)
        print(f"✅ Trend Detection: {len(trends)} trends found")
        
        # Test relationship analysis
        graph = engine.analyze_relationships()
        print(f"✅ Relationship Analysis: {len(graph.influencers)} influencers tracked")
        
        # Test engagement prediction
        prediction = engine.predict_engagement("Test post content")
        print(f"✅ Engagement Prediction: {prediction.predicted_likes} likes predicted")
        
        return True
    except Exception as e:
        print(f"❌ World State Intelligence failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase10_causal_understanding():
    """Test Phase 10: Causal Understanding"""
    print("\n🔗 PHASE 10: Causal Understanding")
    print("=" * 50)
    
    try:
        from src.agentic.causal_engine import get_causal_engine
        
        engine = get_causal_engine()
        
        # Test correlation finding (returns empty if no data)
        correlations = engine.find_correlations("engagement", min_strength=0.5)
        print(f"✅ Correlation Finder: {len(correlations)} correlations found")
        
        # Test summary
        summary = engine.get_causal_summary(hours=24)
        print(f"✅ Causal Summary: {summary.get('observations_recorded', 0)} observations")
        
        return True
    except Exception as e:
        print(f"❌ Causal Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase11_research():
    """Test Phase 11: Autonomous Research"""
    print("\n🔬 PHASE 11: Autonomous Research")
    print("=" * 50)
    
    try:
        from src.agentic.research_engine import get_research_engine
        
        engine = get_research_engine()
        
        # Test research summary
        summary = engine.get_research_summary()
        print(f"✅ Research Engine: {summary.get('total_knowledge_facts', 0)} facts known")
        
        # Test concept generation
        concept = engine.generate_concept('meme', 'AI')
        print(f"✅ Creative Concept: '{concept.title[:30]}...' generated")
        
        return True
    except Exception as e:
        print(f"❌ Research Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase12_social_intelligence():
    """Test Phase 12: Social Intelligence"""
    print("\n🎭 PHASE 12: Social Intelligence")
    print("=" * 50)
    
    try:
        from src.agentic.social_intelligence import get_social_intelligence
        
        social = get_social_intelligence()
        
        # Test social summary
        summary = social.get_social_summary()
        print(f"✅ Social Intelligence: {summary.get('entities_modeled', 0)} entities modeled")
        
        return True
    except Exception as e:
        print(f"❌ Social Intelligence failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase13_creative():
    """Test Phase 13: Creative Generation"""
    print("\n✨ PHASE 13: Creative Generation")
    print("=" * 50)
    
    try:
        from src.agentic.creative_engine import get_creative_engine
        
        creative = get_creative_engine()
        
        # Test cross-domain inspiration
        concept = creative.cross_domain_inspire('gaming', 'finance')
        print(f"✅ Cross-Domain: '{concept.title}' concept generated")
        
        # Test story arc
        story = creative.build_story_arc('Building in Public', posts=3)
        print(f"✅ Story Arc: '{story.title}' with {len(story.posts)} posts")
        
        # Test style transfer
        styled = creative.transfer_style("Hello world!", "professional")
        print(f"✅ Style Transfer: {styled['target_style']} style applied")
        
        return True
    except Exception as e:
        print(f"❌ Creative Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase14_metacognition():
    """Test Phase 14: Metacognition"""
    print("\n🤔 PHASE 14: Metacognition")
    print("=" * 50)
    
    try:
        from src.agentic.metacognition import get_metacognition
        
        meta = get_metacognition()
        
        # Test capability assessment
        assessment = meta.assess_capability('content_generation')
        print(f"✅ Capability Assessment: {assessment.capability} = {assessment.can_perform}")
        
        # Test metacognitive summary
        summary = meta.get_metacognitive_summary()
        print(f"✅ Metacognition: {summary.get('capabilities_known', 0)} capabilities known")
        
        return True
    except Exception as e:
        print(f"❌ Metacognition failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_commands():
    """Test Telegram command modules load"""
    print("\n📱 TELEGRAM COMMANDS")
    print("=" * 50)
    
    commands = [
        ('plugins.telegram.reflection_commands', 'ReflectionCommands'),
        ('plugins.telegram.causal_commands', 'CausalCommands'),
        ('plugins.telegram.intelligence_commands', 'IntelligenceCommands'),
    ]
    
    all_ok = True
    for module_name, class_name in commands:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 AGI FEATURES TEST SUITE")
    print("=" * 60)
    
    results = {
        'Phase 1 - Self-Reflection': test_phase1_self_reflection(),
        'Phase 7 - World State Intelligence': test_phase7_world_state_intelligence(),
        'Phase 10 - Causal Understanding': test_phase10_causal_understanding(),
        'Phase 11 - Research': test_phase11_research(),
        'Phase 12 - Social Intelligence': test_phase12_social_intelligence(),
        'Phase 13 - Creative': test_phase13_creative(),
        'Phase 14 - Metacognition': test_phase14_metacognition(),
        'Telegram Commands': test_telegram_commands(),
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 {passed}/{total} test groups passed")
    
    if passed == total:
        print("🎉 All AGI features ready!")
        return 0
    else:
        print("⚠️  Some features need attention")
        return 1

if __name__ == '__main__':
    sys.exit(main())
