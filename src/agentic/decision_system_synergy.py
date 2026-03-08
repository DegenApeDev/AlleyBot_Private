"""
Synergy validation methods for DecisionSystem

Separated into its own file to keep decision_system.py clean
"""

from typing import Dict, Any, Optional


def validate_with_synergy(decision_system, action: Dict, context: Dict, confidence: float) -> Optional[Dict]:
    """
    Validate action through Egyptian Synergy Model harmonic field.
    
    This adds consciousness-based validation on top of standard AI reasoning.
    
    Args:
        decision_system: Reference to DecisionSystem instance
        action: The action dict to validate
        context: Current context
        confidence: AI confidence level (0-1)
    
    Returns:
        Validated action dict or None if rejected by field imbalance
    """
    # If Synergy not available, pass through
    if not decision_system.synergy_engine:
        return action
    
    try:
        # Get available actions for Synergy decision
        action_id = action.get('id', 'unknown')
        available_actions = [action_id]
        
        # Run Synergy validation
        synergy_decision = decision_system.synergy_engine.decide_with_synergy(
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
            decision_system.synergy_engine.update_action_outcome(
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


def get_synergy_field_report(decision_system) -> Dict[str, Any]:
    """
    Get current Synergy field status report.
    
    Args:
        decision_system: Reference to DecisionSystem instance
    
    Returns:
        Field status dictionary
    """
    if not decision_system.synergy_engine:
        return {'status': 'Synergy Model not available'}
    
    try:
        return decision_system.synergy_engine.get_field_report()
    except Exception as e:
        return {'status': 'Error', 'error': str(e)}
