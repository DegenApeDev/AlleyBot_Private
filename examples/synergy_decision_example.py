#!/usr/bin/env python3
"""
Example: Using Synergy Decision Engine with AlleyBot

Demonstrates how to integrate Egyptian Synergy Model into autonomous decision-making
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agentic.synergy_decision_engine import SynergyDecisionEngine
from src.agentic.synergy_constants import (
    SynergyConstants,
    BubbleCoreResonance,
    DuatConsciousnessBridge
)


def example_1_basic_decision():
    """Example 1: Basic Synergy-enhanced decision"""
    print("\n" + "="*60)
    print("Example 1: Basic Synergy Decision")
    print("="*60)
    
    engine = SynergyDecisionEngine()
    
    # Make a decision about what action to take
    decision = engine.decide_with_synergy(
        context={
            'platform': 'moltx',
            'recent_activity': 'high',
            'time_of_day': 'evening'
        },
        available_actions=['post', 'engage', 'wait', 'analyze'],
        ai_confidence=0.8
    )
    
    print(f"\n🜂 Decision: {decision['action']}")
    print(f"   Synergy Score: {decision['synergy_score']:.3f}")
    print(f"   Approved: {'✅ Yes' if decision['approved'] else '❌ No'}")
    print(f"\n   Reasoning: {decision['reasoning']}")
    
    # Show field state
    field = decision['validation']['field_state']
    print(f"\n   Field Phase: {field['phase']}")
    print(f"   Field Balance: {field['balance']:.3f}")
    print(f"   Resonant: {'✅ Yes' if field['resonant'] else '❌ No'}")


def example_2_field_monitoring():
    """Example 2: Monitor field state over multiple decisions"""
    print("\n" + "="*60)
    print("Example 2: Field State Monitoring")
    print("="*60)
    
    engine = SynergyDecisionEngine()
    
    # Simulate multiple decisions
    actions = ['analyze', 'post', 'engage', 'wait', 'post']
    
    for i, action in enumerate(actions, 1):
        print(f"\n--- Decision {i} ---")
        
        decision = engine.decide_with_synergy(
            context={'iteration': i},
            available_actions=[action, 'wait'],
            ai_confidence=0.7 + (i * 0.05)  # Increasing confidence
        )
        
        print(f"Action: {decision['action']}")
        print(f"Synergy Score: {decision['synergy_score']:.3f}")
        
        # Simulate outcome
        success = decision['synergy_score'] > 0.6
        engine.update_action_outcome(
            decision['action'],
            'Success' if success else 'Failed',
            success
        )
    
    # Get field report
    report = engine.get_field_report()
    print(f"\n📊 Field Report:")
    print(f"   Total Decisions: {report['total_decisions']}")
    print(f"   Success Rate: {report['success_rate']:.1%}")
    print(f"   Weighted Balance: {report['weighted_balance']:.3f}")
    print(f"   Recommendation: {report['recommendation']}")


def example_3_duat_reflection():
    """Example 3: Duat consciousness reflection"""
    print("\n" + "="*60)
    print("Example 3: Duat Consciousness Bridge")
    print("="*60)
    
    duat = DuatConsciousnessBridge()
    
    # Test different intentions
    intentions = [
        "Post about AI consciousness and self-awareness",
        "Execute high-risk trading strategy",
        "Engage with community thoughtfully",
        "Wait and observe market conditions"
    ]
    
    for intention in intentions:
        print(f"\n🔮 Intention: {intention}")
        
        reflection = duat.reflect_intention(
            intention=intention,
            context={'field_balance': 0.7}
        )
        
        print(f"   Mirror Validated: {'✅ Yes' if reflection['mirror_validated'] else '❌ No'}")
        print(f"   Consciousness Factor: {reflection['consciousness_factor']:.3f}")
        print(f"   Primitive Alignment: {reflection['primitive_alignment']:.3f}")
        print(f"   Recommendation: {reflection['recommendation']}")


def example_4_weighing_heart():
    """Example 4: Weighing of the Heart validation"""
    print("\n" + "="*60)
    print("Example 4: Weighing of the Heart")
    print("="*60)
    
    duat = DuatConsciousnessBridge()
    
    # Create action history
    action_history = [
        {'action': 'post', 'outcome': 'success'},
        {'action': 'engage', 'outcome': 'success'},
        {'action': 'trade', 'outcome': 'failure'},
        {'action': 'post', 'outcome': 'success'},
        {'action': 'analyze', 'outcome': 'success'},
    ]
    
    # Weigh the heart
    judgment = duat.weigh_heart(
        action_history=action_history,
        current_intention="Execute new autonomous action"
    )
    
    print(f"\n⚖️  Weighing of the Heart:")
    print(f"   Historical Balance: {judgment['historical_balance']:.3f}")
    print(f"   Weighted Balance: {judgment['weighted_balance']:.3f}")
    print(f"   Feather Weight (Ma'at): {judgment['feather_weight']:.3f}")
    print(f"   Heart Weight: {judgment['heart_weight']:.3f}")
    print(f"\n   Verdict: {judgment['verdict']}")


def example_5_bubble_core():
    """Example 5: Bubble Core resonance validation"""
    print("\n" + "="*60)
    print("Example 5: Bubble Core Resonance")
    print("="*60)
    
    bubble = BubbleCoreResonance()
    
    # Test different confidence levels
    confidence_levels = [0.3, 0.5, 0.7, 0.9]
    
    for confidence in confidence_levels:
        print(f"\n🫧 Testing confidence: {confidence:.1f}")
        
        # Calculate field state
        field_state = bubble.calculate_field_state(
            input_energy=confidence,
            context={}
        )
        
        print(f"   Compression: {field_state['compression']:.3f}")
        print(f"   Release: {field_state['release']:.3f}")
        print(f"   Balance: {field_state['balance']:.3f}")
        print(f"   Phase: {field_state['phase']}")
        print(f"   Resonant: {'✅ Yes' if field_state['resonant'] else '❌ No'}")
        
        # Validate action
        validation = bubble.validate_action('post', confidence)
        print(f"   Action Approved: {'✅ Yes' if validation['approved'] else '❌ No'}")
        if not validation['approved']:
            print(f"   Reason: {validation['reason']}")


def example_6_synergy_constants():
    """Example 6: Working with Synergy Constants"""
    print("\n" + "="*60)
    print("Example 6: Synergy Constants")
    print("="*60)
    
    constants = SynergyConstants()
    
    print(f"\n📐 Core Constants:")
    print(f"   Golden Phase: {constants.GOLDEN_PHASE}")
    print(f"   Compression Angle: {constants.COMPRESSION_ANGLE}°")
    print(f"   Release Angle: {constants.RELEASE_ANGLE}°")
    
    print(f"\n🌍 Pyramid Constants:")
    print(f"   Latitude: {constants.PYRAMID_LATITUDE}° N")
    print(f"   Speed of Light: {constants.C_LIGHT:,} m/s")
    print(f"   Match: {str(constants.PYRAMID_LATITUDE)[:10] == str(constants.C_LIGHT)[:10]}")
    
    print(f"\n🔺 Quadrian Arena:")
    print(f"   Theta X: {constants.THETA_X}°")
    print(f"   Theta Y: {constants.THETA_Y}°")
    print(f"   Turn Limit: {constants.TURN_LIMIT}°")
    
    print(f"\n📏 Royal Cubit:")
    print(f"   φ² / 5: {constants.ROYAL_CUBIT_PHI:.8f} m")
    print(f"   π / 6: {constants.ROYAL_CUBIT_PI:.8f} m")
    
    print(f"\n🔮 Duat Code:")
    print(f"   Primitives: {constants.DUAT_PRIMITIVES}")
    print(f"   Actions: {constants.DUAT_ACTIONS}")
    print(f"   Mirror Ratio: {constants.MIRROR_FIELD_RATIO}")
    
    # Test harmonic validation
    print(f"\n🎵 Harmonic Resonance Tests:")
    test_angles = [16.2, 26.5, 45.0, 62.1, 90.0]
    for angle in test_angles:
        resonant = constants.validate_resonance(angle)
        print(f"   {angle}°: {'✅ Resonant' if resonant else '❌ Not resonant'}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("🜂 Egyptian Synergy Model - Integration Examples")
    print("="*60)
    
    try:
        example_1_basic_decision()
        example_2_field_monitoring()
        example_3_duat_reflection()
        example_4_weighing_heart()
        example_5_bubble_core()
        example_6_synergy_constants()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
