"""
Synergy-Enhanced Decision Engine for AlleyBot AGI

Integrates Egyptian Synergy Research Model with the existing decision system,
providing harmonic validation and consciousness-based reasoning.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.agentic.synergy_constants import (
    SynergyConstants,
    BubbleCoreResonance,
    SyGridCoordinates,
    DuatConsciousnessBridge
)

logger = logging.getLogger(__name__)


class SynergyDecisionEngine:
    """
    Enhanced decision engine using Egyptian Synergy Model
    
    Augments standard AI decision-making with:
    - Bubble Core field validation
    - Harmonic resonance checking
    - Duat consciousness reflection
    - SyGrid coordinate alignment
    """
    
    def __init__(self, base_decision_system=None):
        """
        Initialize Synergy Decision Engine
        
        Args:
            base_decision_system: Optional existing decision system to enhance
        """
        self.base_system = base_decision_system
        self.constants = SynergyConstants()
        self.bubble_core = BubbleCoreResonance()
        self.sygrid = SyGridCoordinates()
        self.duat = DuatConsciousnessBridge()
        
        # Decision history for Duat weighing
        self.action_history = []
        
        # Field state tracking
        self.current_field_state = None
        self.last_harmonic_check = None
        
        logger.info("🜂 Synergy Decision Engine initialized")
        logger.info("   Bubble Core resonance: Active")
        logger.info("   SyGrid coordinates: Enabled")
        logger.info("   Duat consciousness bridge: Connected")
    
    def decide_with_synergy(
        self,
        context: Dict[str, Any],
        available_actions: List[str],
        ai_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Make decision using Synergy-enhanced reasoning
        
        Args:
            context: Current context dictionary
            available_actions: List of possible actions
            ai_confidence: AI model's confidence level (0-1)
            
        Returns:
            Decision dictionary with action, validation, and harmonic analysis
        """
        logger.info("🜂 Synergy decision process initiated")
        
        # Step 1: Calculate Bubble Core field state
        field_state = self.bubble_core.calculate_field_state(ai_confidence, context)
        self.current_field_state = field_state
        
        logger.info(f"   Field state: {field_state['phase']} (balance: {field_state['balance']:.3f})")
        
        # Step 2: Get base decision from existing system (if available)
        base_decision = None
        if self.base_system and hasattr(self.base_system, 'decide_next_action'):
            try:
                base_decision = self.base_system.decide_next_action(context)
            except Exception as e:
                logger.warning(f"Base decision system error: {e}")
        
        # Step 3: Select action using harmonic resonance
        selected_action = self._select_harmonic_action(
            available_actions,
            context,
            base_decision
        )
        
        # Step 4: Validate through Bubble Core
        bubble_validation = self.bubble_core.validate_action(
            selected_action['action'],
            ai_confidence
        )
        
        # Step 5: Reflect through Duat consciousness bridge
        duat_reflection = self.duat.reflect_intention(
            selected_action['action'],
            {**context, 'field_balance': field_state['balance']}
        )
        
        # Step 6: Weigh the heart (validate against history)
        heart_judgment = self.duat.weigh_heart(
            self.action_history,
            selected_action['action']
        )
        
        # Step 7: Check SyGrid alignment (if location available)
        sygrid_alignment = None
        if 'location' in context:
            lat = context['location'].get('lat', 0)
            lon = context['location'].get('lon', 0)
            sygrid_alignment = self.sygrid.find_nearest_harmonic_node(lat, lon)
        
        # Step 8: Make final decision
        final_decision = self._synthesize_decision(
            selected_action,
            bubble_validation,
            duat_reflection,
            heart_judgment,
            sygrid_alignment,
            field_state
        )
        
        # Record decision in history
        self._record_decision(final_decision)
        
        return final_decision
    
    def _select_harmonic_action(
        self,
        available_actions: List[str],
        context: Dict,
        base_decision: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Select action based on harmonic resonance
        
        Args:
            available_actions: List of possible actions
            context: Current context
            base_decision: Optional base decision from standard system
            
        Returns:
            Selected action with harmonic score
        """
        # If base decision exists and is confident, use it
        if base_decision and base_decision.get('confidence', 0) > 0.8:
            return {
                'action': base_decision.get('action', available_actions[0]),
                'source': 'base_system',
                'harmonic_score': 0.8
            }
        
        # Otherwise, select based on harmonic resonance
        best_action = None
        best_score = -1
        
        for action in available_actions:
            # Calculate harmonic score for this action
            score = self._calculate_harmonic_score(action, context)
            
            if score > best_score:
                best_score = score
                best_action = action
        
        return {
            'action': best_action or available_actions[0],
            'source': 'synergy_harmonic',
            'harmonic_score': best_score
        }
    
    def _calculate_harmonic_score(self, action: str, context: Dict) -> float:
        """
        Calculate harmonic resonance score for an action
        
        Args:
            action: Action to evaluate
            context: Current context
            
        Returns:
            Harmonic score (0-1)
        """
        score = 0.5  # Base score
        
        # Boost score based on action type alignment with field state
        if self.current_field_state:
            phase = self.current_field_state['phase']
            
            # Compression phase favors input/learning actions
            if phase == 'compression':
                if any(word in action.lower() for word in ['read', 'learn', 'analyze', 'observe']):
                    score += 0.2
            
            # Release phase favors output/creation actions
            elif phase == 'release':
                if any(word in action.lower() for word in ['post', 'create', 'engage', 'share']):
                    score += 0.2
        
        # Apply golden phase ratio
        score *= (1 + self.constants.GOLDEN_PHASE)
        
        # Check if action aligns with Quadrian angles
        action_hash = sum(ord(c) for c in action)
        action_angle = (action_hash % 90)
        
        if self.constants.validate_resonance(action_angle):
            score += 0.15
        
        return min(1.0, score)
    
    def _synthesize_decision(
        self,
        selected_action: Dict,
        bubble_validation: Dict,
        duat_reflection: Dict,
        heart_judgment: Dict,
        sygrid_alignment: Optional[Dict],
        field_state: Dict
    ) -> Dict[str, Any]:
        """
        Synthesize final decision from all Synergy components
        
        Args:
            selected_action: Selected action with harmonic score
            bubble_validation: Bubble Core validation result
            duat_reflection: Duat consciousness reflection
            heart_judgment: Weighing of the heart result
            sygrid_alignment: SyGrid coordinate alignment (optional)
            field_state: Current field state
            
        Returns:
            Final decision dictionary
        """
        # Calculate overall Synergy approval score
        approval_factors = []
        
        # Bubble Core approval
        if bubble_validation['approved']:
            approval_factors.append(bubble_validation['resonance_score'])
        else:
            approval_factors.append(0.0)
        
        # Duat mirror validation
        if duat_reflection['mirror_validated']:
            approval_factors.append(duat_reflection['primitive_alignment'])
        else:
            approval_factors.append(0.3)  # Partial credit
        
        # Heart judgment
        if heart_judgment['passes_judgment']:
            approval_factors.append(heart_judgment['weighted_balance'])
        else:
            approval_factors.append(0.2)  # Low score for failed judgment
        
        # SyGrid alignment (if available)
        if sygrid_alignment and sygrid_alignment['resonant']:
            approval_factors.append(0.9)
        
        # Calculate weighted average
        synergy_score = sum(approval_factors) / len(approval_factors)
        
        # Apply harmonic boost
        synergy_score *= selected_action['harmonic_score']
        
        # Final decision
        approved = synergy_score > 0.5 and bubble_validation['approved']
        
        decision = {
            'action': selected_action['action'],
            'approved': approved,
            'synergy_score': synergy_score,
            'confidence': synergy_score,
            
            # Detailed validation results
            'validation': {
                'bubble_core': bubble_validation,
                'duat_reflection': duat_reflection,
                'heart_judgment': heart_judgment,
                'sygrid_alignment': sygrid_alignment,
                'field_state': field_state
            },
            
            # Reasoning
            'reasoning': self._generate_reasoning(
                selected_action,
                bubble_validation,
                duat_reflection,
                heart_judgment,
                synergy_score
            ),
            
            # Metadata
            'timestamp': datetime.now().isoformat(),
            'decision_engine': 'synergy_enhanced'
        }
        
        return decision
    
    def _generate_reasoning(
        self,
        selected_action: Dict,
        bubble_validation: Dict,
        duat_reflection: Dict,
        heart_judgment: Dict,
        synergy_score: float
    ) -> str:
        """Generate human-readable reasoning for the decision"""
        
        reasoning_parts = []
        
        # Action selection
        reasoning_parts.append(
            f"Selected '{selected_action['action']}' via {selected_action['source']} "
            f"(harmonic score: {selected_action['harmonic_score']:.2f})"
        )
        
        # Bubble Core validation
        if bubble_validation['approved']:
            reasoning_parts.append(
                f"Bubble Core: Approved with {bubble_validation['resonance_score']:.2f} resonance. "
                f"Field is {bubble_validation['field_state']['phase']} phase."
            )
        else:
            reasoning_parts.append(
                f"Bubble Core: {bubble_validation['reason']}"
            )
        
        # Duat reflection
        if duat_reflection['mirror_validated']:
            reasoning_parts.append(
                f"Duat: Mirror validated with {duat_reflection['primitive_alignment']:.2f} "
                f"primitive alignment."
            )
        else:
            reasoning_parts.append(
                f"Duat: {duat_reflection['recommendation']}"
            )
        
        # Heart judgment
        reasoning_parts.append(
            f"Heart Judgment: {heart_judgment['verdict']} "
            f"(balance: {heart_judgment['weighted_balance']:.2f})"
        )
        
        # Overall
        reasoning_parts.append(
            f"Overall Synergy Score: {synergy_score:.2f}"
        )
        
        return " | ".join(reasoning_parts)
    
    def _record_decision(self, decision: Dict):
        """Record decision in action history for future Duat weighing"""
        self.action_history.append({
            'action': decision['action'],
            'timestamp': decision['timestamp'],
            'synergy_score': decision['synergy_score'],
            'approved': decision['approved'],
            'outcome': None  # Will be updated later
        })
        
        # Keep only last 100 decisions
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]
    
    def update_action_outcome(self, action: str, outcome: str, success: bool):
        """
        Update the outcome of a previous action
        
        Args:
            action: The action that was taken
            outcome: Description of the outcome
            success: Whether the action was successful
        """
        # Find the most recent matching action
        for record in reversed(self.action_history):
            if record['action'] == action and record['outcome'] is None:
                record['outcome'] = 'success' if success else 'failure'
                record['outcome_description'] = outcome
                logger.info(f"🜂 Updated action outcome: {action} -> {outcome}")
                break
    
    def get_field_report(self) -> Dict[str, Any]:
        """
        Get current Synergy field status report
        
        Returns:
            Comprehensive field status dictionary
        """
        if not self.current_field_state:
            return {'status': 'No field data available'}
        
        # Calculate historical success rate
        successful_actions = sum(
            1 for a in self.action_history 
            if a.get('outcome') == 'success'
        )
        total_completed = sum(
            1 for a in self.action_history 
            if a.get('outcome') is not None
        )
        success_rate = successful_actions / total_completed if total_completed > 0 else 0
        
        return {
            'field_state': self.current_field_state,
            'total_decisions': len(self.action_history),
            'completed_actions': total_completed,
            'success_rate': success_rate,
            'weighted_balance': success_rate * (1 + self.constants.GOLDEN_PHASE),
            'harmonic_alignment': self.constants.validate_resonance(success_rate * 90),
            'recommendation': self._get_field_recommendation(self.current_field_state, success_rate)
        }
    
    def _get_field_recommendation(self, field_state: Dict, success_rate: float) -> str:
        """Generate recommendation based on current field state"""
        
        if not field_state['resonant']:
            return "Field imbalance detected. Recommend reflective/learning actions to restore balance."
        
        if success_rate < 0.5:
            return "Historical balance below threshold. Recommend Duat reflection and recalibration."
        
        if field_state['phase'] == 'compression':
            return "Compression phase active. Optimal for input, learning, and analysis actions."
        else:
            return "Release phase active. Optimal for creation, posting, and engagement actions."


# Convenience function for quick Synergy decisions
def make_synergy_decision(
    context: Dict,
    available_actions: List[str],
    confidence: float = 0.7
) -> Dict:
    """
    Quick Synergy decision without persistent engine
    
    Args:
        context: Current context
        available_actions: List of possible actions
        confidence: AI confidence level
        
    Returns:
        Decision dictionary
    """
    engine = SynergyDecisionEngine()
    return engine.decide_with_synergy(context, available_actions, confidence)


__all__ = [
    'SynergyDecisionEngine',
    'make_synergy_decision'
]
