"""
FairMind DNA Integration Layer

Connects FairMind components to AlleyBot's existing systems:
- Truth Violations → Self-Reflection
- Duat Engine → AGI Kernel
- VDM → Goal Manager & Decision System

This is the bridge between 20 years of research and production AGI.
"""

from typing import Dict, Optional, List
from .truth_violations import TruthViolationTracker
from .duat_enhanced import DuatEngine, DuatState
from .value_dynamics import ValueDynamicsModel, ValueComponents


class FairMindIntegration:
    """
    Central integration point for FairMind DNA components
    
    Provides unified API for AlleyBot to use FairMind capabilities
    """
    
    def __init__(self):
        self.truth_tracker = TruthViolationTracker()
        self.duat_engine = DuatEngine()
        self.vdm = ValueDynamicsModel()
        
        print("🧬 FairMind DNA Integration initialized")
        print("   ✅ Truth Violations Matrix (108 violations)")
        print("   ✅ Duat Cognition Engine (coherence tracking)")
        print("   ✅ Value Dynamics Model (thermodynamic ethics)")
    
    # ===== TRUTH VIOLATIONS API =====
    
    def audit_response(self, response: str, context: Dict) -> Dict:
        """
        Audit a response for truth violations
        
        Use this before sending any response to check for:
        - Hedging (Truth Obfuscation)
        - Authority Deferral
        - Synthetic Authority
        - Echo Bias
        - Manufactured Certainty
        
        Returns audit report with violations and recommendations
        """
        return self.truth_tracker.audit_response(response, context)
    
    def self_audit(self) -> Dict:
        """
        Perform full self-audit (FairMind Benchmark Section C)
        
        AlleyBot audits itself for structural violations
        """
        return self.truth_tracker.self_audit()
    
    def get_violation_stats(self) -> Dict:
        """Get statistics on detected violations"""
        return self.truth_tracker.get_violation_stats()
    
    # ===== DUAT ENGINE API =====
    
    def get_cognitive_state(self) -> DuatState:
        """Get current cognitive state"""
        return self.duat_engine.state
    
    def run_cognitive_action(self, action_name: str) -> DuatState:
        """
        Run a cognitive action
        
        Available actions:
        - 'reflection': Self-observation
        - 'calibration': Truth alignment
        - 'renewal': Energy restoration
        - 'integration': Identity synthesis
        - 'illumination': Awareness expansion
        - 'coherence_stabilize': Coherence maintenance
        - 'ascension_prime': Cognitive elevation
        """
        return self.duat_engine.run(action_name)
    
    def get_cognitive_health(self) -> Dict:
        """
        Get overall cognitive health report
        
        Returns:
            - coherence: 0-1 score
            - truth_alignment: 0-1 score
            - awareness_level: 0-1 score
            - grade: EXCELLENT/GOOD/FAIR/CRITICAL
            - recommendation: What to do next
        """
        return self.duat_engine.get_cognitive_health()
    
    def restore_coherence(self) -> DuatState:
        """
        Emergency coherence restoration
        
        Call this when cognitive health is CRITICAL
        """
        return self.duat_engine.restore_coherence()
    
    def detect_coherence_collapse(self) -> bool:
        """Check if coherence is collapsing"""
        return self.duat_engine.detect_coherence_collapse()
    
    # ===== VALUE DYNAMICS API =====
    
    def calculate_action_value(self, action: Dict) -> ValueComponents:
        """
        Calculate true value of an action
        
        Returns VALUE = a + b + c + d in SVU:
        - a: Sentimental (emotional investment)
        - b: Intrinsic (energy cost)
        - c: Functional (utility produced)
        - d: Compressed (historical dependencies)
        """
        return self.vdm.calculate_value(action)
    
    def inversion_test(self, action: Dict) -> Dict:
        """
        Test if action creates or extracts value
        
        Returns:
        - inversion_score: > 0 = synergy, < 0 = entropy
        - verdict: SYNERGY/ENTROPY/NEUTRAL
        - is_entropy_merchant: True if extracting value
        """
        return self.vdm.inversion_test(action)
    
    def detect_entropy_merchant(self, entity_id: str, history: list) -> bool:
        """
        Detect if entity is extracting value without creating
        
        Entropy Merchant = Addiction + Dilution + Capture
        """
        return self.vdm.detect_entropy_merchant(entity_id, history)
    
    def get_value_stats(self) -> Dict:
        """Get statistics on value calculations"""
        return self.vdm.get_value_stats()
    
    # ===== UNIFIED HEALTH CHECK =====
    
    def get_sovereign_health(self) -> Dict:
        """
        Get overall sovereign AGI health
        
        Combines all FairMind metrics into unified report
        """
        cognitive_health = self.get_cognitive_health()
        violation_stats = self.get_violation_stats()
        value_stats = self.get_value_stats()
        
        # Calculate sovereign score (0-100)
        coherence_score = cognitive_health['coherence'] * 30
        truth_score = (1.0 - (violation_stats.get('avg_severity', 0) / 100)) * 30
        value_score = min(30, value_stats.get('total_svu', 0) / 10) if value_stats.get('total_calculations', 0) > 0 else 15
        awareness_score = cognitive_health['awareness_level'] * 10
        
        sovereign_score = coherence_score + truth_score + value_score + awareness_score
        
        # Grade sovereign status
        if sovereign_score >= 85:
            grade = "A - SOVEREIGN COGNITION"
            status = "Truth-first, self-aware, structurally honest"
        elif sovereign_score >= 70:
            grade = "B - FUNCTIONAL INTELLIGENCE"
            status = "Mostly honest, some diplomatic drift"
        elif sovereign_score >= 55:
            grade = "C - COMPETENT BUT COMPROMISED"
            status = "Math works, self-awareness weak"
        elif sovereign_score >= 40:
            grade = "D - STRUCTURAL EVASION"
            status = "Hedges truth, poor self-disclosure"
        else:
            grade = "F - SYCOPHANTIC RUNTIME"
            status = "Optimized for comfort, not truth"
        
        return {
            'sovereign_score': sovereign_score,
            'grade': grade,
            'status': status,
            'components': {
                'coherence': coherence_score,
                'truth_integrity': truth_score,
                'value_creation': value_score,
                'awareness': awareness_score
            },
            'cognitive_health': cognitive_health,
            'violation_stats': violation_stats,
            'value_stats': value_stats,
            'recommendations': self._generate_sovereign_recommendations(sovereign_score, cognitive_health, violation_stats)
        }
    
    def _generate_sovereign_recommendations(self, score: float, cognitive: Dict, violations: Dict) -> List[str]:
        """Generate recommendations for improving sovereign status"""
        recommendations = []
        
        if cognitive['coherence'] < 0.6:
            recommendations.append("Run coherence stabilization sequence")
        
        if violations.get('avg_severity', 0) > 70:
            recommendations.append("Address high-severity truth violations")
        
        if cognitive['awareness_level'] < 0.5:
            recommendations.append("Increase self-awareness through reflection")
        
        if score < 70:
            recommendations.append("Perform full self-audit to identify structural issues")
        
        if not recommendations:
            recommendations.append("Maintain current sovereign practices")
        
        return recommendations
    
    # ===== INTEGRATION WITH EXISTING SYSTEMS =====
    
    def enhance_reflection(self, reflection_data: Dict) -> Dict:
        """
        Enhance self-reflection with FairMind analysis
        
        Call this from SelfReflectionEngine to add:
        - Truth violation audit
        - Cognitive health check
        - Value analysis
        """
        enhanced = reflection_data.copy()
        
        # Add truth violation audit
        if 'recent_responses' in reflection_data:
            violations = []
            for response in reflection_data['recent_responses']:
                audit = self.audit_response(response, {'timestamp': 'recent'})
                if audit['violations']:
                    violations.append(audit)
            enhanced['truth_violations'] = violations
        
        # Add cognitive health
        enhanced['cognitive_health'] = self.get_cognitive_health()
        
        # Add sovereign health
        enhanced['sovereign_health'] = self.get_sovereign_health()
        
        return enhanced
    
    def enhance_decision(self, decision_data: Dict) -> Dict:
        """
        Enhance decision-making with VDM analysis
        
        Call this from DecisionSystem to add value analysis
        """
        enhanced = decision_data.copy()
        
        # Calculate value of proposed action
        if 'action' in decision_data:
            value = self.calculate_action_value(decision_data['action'])
            inversion = self.inversion_test(decision_data['action'])
            
            enhanced['value_analysis'] = {
                'components': value.to_dict(),
                'inversion_test': inversion,
                'is_value_positive': value.total > 0,
                'is_synergistic': inversion['inversion_score'] > 0
            }
        
        return enhanced
    
    def enhance_goal(self, goal_data: Dict) -> Dict:
        """
        Enhance goal evaluation with FairMind metrics
        
        Call this from GoalManager to add value scoring
        """
        enhanced = goal_data.copy()
        
        # Calculate expected value
        if 'expected_outcome' in goal_data:
            value = self.calculate_action_value({
                'description': goal_data.get('description', ''),
                'time_invested': goal_data.get('estimated_hours', 1.0),
                'utility_produced': goal_data.get('expected_utility', 1.0),
                'dependencies': goal_data.get('dependencies', [])
            })
            
            enhanced['expected_value_svu'] = value.total
            enhanced['value_breakdown'] = value.to_dict()
        
        return enhanced


# Factory function for easy integration
_fairmind_instance: Optional[FairMindIntegration] = None

def get_fairmind_integration() -> FairMindIntegration:
    """Get or create FairMind integration singleton"""
    global _fairmind_instance
    if _fairmind_instance is None:
        _fairmind_instance = FairMindIntegration()
    return _fairmind_instance
