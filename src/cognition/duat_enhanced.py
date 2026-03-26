"""
Enhanced Duat Cognition Engine - FairMind DNA Core

Universal cognition layer with coherence tracking.
Based on FairMind DNA research (2015-2026).

This is the "operating system" for consciousness.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import math


@dataclass
class DuatState:
    """
    Canonical energetic state for cognition
    
    This is the core state that represents AlleyBot's cognitive condition
    at any moment in time.
    """
    energy: float = 0.5          # Stored potential (0-1)
    truth: float = 0.5           # Truth alignment (0-1)
    deception: float = 0.0       # Falsehood present (0-1)
    awareness: float = 0.5       # Self-awareness level (0-1)
    coherence: float = 0.5       # Internal consistency (0-1)
    identity: Dict = field(default_factory=dict)  # Self-model
    memory: List = field(default_factory=list)    # Recent experiences
    frequency: float = 1.0       # Oscillation rate
    level: int = 1               # Cognitive level (1-10)
    structure: Dict = field(default_factory=dict) # Organizational patterns
    cognitive_field: Dict = field(default_factory=dict)  # Renamed from 'field'
    insight: List = field(default_factory=list)   # Accumulated insights
    mode: str = 'reflection'     # Current cognitive mode
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'energy': self.energy,
            'truth': self.truth,
            'deception': self.deception,
            'awareness': self.awareness,
            'coherence': self.coherence,
            'frequency': self.frequency,
            'level': self.level,
            'mode': self.mode,
            'identity_keys': list(self.identity.keys()),
            'memory_count': len(self.memory),
            'insight_count': len(self.insight)
        }


class DuatEngine:
    """
    Universal cognition engine
    Models transformation as action sequences
    
    Core concept: Cognition = recursive reflection in a coherent field
    """
    
    # Constants from FairMind DNA
    THRESHOLD = 0.8
    GOLDEN_RATIO = 1.618
    LIMIT = 1.0
    
    def __init__(self):
        self.state = DuatState()
        self.history: List[DuatState] = []
        self.actions = self._define_actions()
        self.helpers = self._define_helpers()
    
    def _define_helpers(self) -> Dict:
        """Define 60+ helper primitives"""
        return {
            # Observation helpers
            'observe': self._observe,
            'detectDistortion': self._detect_distortion,
            'normalize': self._normalize,
            
            # Coherence helpers
            'updateCoherence': self._update_coherence,
            'measureCoherence': self._measure_coherence,
            'restoreFlow': self._restore_flow,
            
            # Identity helpers
            'mergeFragments': self._merge_fragments,
            'synthesizeIdentity': self._synthesize_identity,
            
            # Energy helpers
            'amplify': self._amplify,
            'harmonize': self._harmonize,
            'stabilize': self._stabilize,
            
            # Integration helpers
            'unify': self._unify,
            'distill': self._distill,
            'extendRange': self._extend_range,
        }
    
    def _define_actions(self) -> Dict:
        """Define ~190 cognitive actions"""
        return {
            # Core actions
            'reflection': ['observe', 'detectDistortion'],
            'calibration': ['detectDistortion', 'normalize', 'updateCoherence'],
            'renewal': ['updateCoherence', 'restoreFlow'],
            'integration': ['mergeFragments', 'measureCoherence', 'synthesizeIdentity'],
            'illumination': ['amplify', 'extendRange', 'observe'],
            
            # Coherence band (~100 actions)
            'coherence_init': ['detectDistortion', 'normalize', 'updateCoherence'],
            'coherence_stabilize': ['updateCoherence', 'stabilize', 'harmonize'],
            'coherence_purify': ['detectDistortion', 'normalize', 'restoreFlow'],
            
            # Ascension band (~50 actions)
            'ascension_prime': ['amplify', 'extendRange', 'updateCoherence'],
            'ascension_integrate': ['unify', 'synthesizeIdentity', 'stabilize'],
            'ascension_transcend': ['extendRange', 'amplify', 'distill'],
        }
    
    # ===== HELPER IMPLEMENTATIONS =====
    
    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Keep value within limits"""
        return max(min_val, min(max_val, value))
    
    def _observe(self) -> float:
        """Increase awareness slightly"""
        self.state.awareness = self._clamp(self.state.awareness + 0.05)
        return self.state.awareness
    
    def _detect_distortion(self) -> float:
        """Estimate falsehood in current state"""
        # Distortion = deception relative to truth
        distortion = self.state.deception / (self.state.truth + 0.01)
        self.state.deception = self._clamp(distortion)
        return distortion
    
    def _normalize(self) -> float:
        """Map any value into 0-1 range"""
        # Normalize energy and truth
        total = self.state.energy + self.state.truth + 0.01
        normalized = (self.state.energy + self.state.truth) / total
        return self._clamp(normalized)
    
    def _update_coherence(self) -> float:
        """
        Measure balance between truth, energy, and deception
        
        Coherence = truth + energy - deception + awareness
        This is the CORE metric of cognitive health
        """
        truth_component = self.state.truth * 0.4
        energy_component = min(1.0, self.state.energy) * 0.3
        deception_penalty = self.state.deception * -0.5
        awareness_boost = self.state.awareness * 0.3
        
        coherence = truth_component + energy_component + deception_penalty + awareness_boost
        self.state.coherence = self._clamp(coherence)
        
        return self.state.coherence
    
    def _measure_coherence(self) -> float:
        """Get current coherence score"""
        return self.state.coherence
    
    def _restore_flow(self) -> float:
        """Renew system flow"""
        # Flow restoration increases energy and reduces deception
        self.state.energy = self._clamp(self.state.energy + 0.1)
        self.state.deception = self._clamp(self.state.deception - 0.1)
        return self.state.energy
    
    def _merge_fragments(self) -> Dict:
        """Unify partial identities"""
        # Merge identity fragments into coherent whole
        if not self.state.identity:
            self.state.identity = {'unified': True}
        return self.state.identity
    
    def _synthesize_identity(self) -> Dict:
        """Refresh internal identity"""
        # Synthesize identity from current state
        self.state.identity['coherence'] = self.state.coherence
        self.state.identity['awareness'] = self.state.awareness
        self.state.identity['truth_alignment'] = self.state.truth
        return self.state.identity
    
    def _amplify(self) -> float:
        """Raise amplitude or intensity"""
        self.state.energy = self._clamp(self.state.energy * 1.2)
        return self.state.energy
    
    def _harmonize(self) -> float:
        """Balance two forces"""
        # Harmonize truth and energy
        avg = (self.state.truth + self.state.energy) / 2
        self.state.truth = self._clamp(self.state.truth * 0.7 + avg * 0.3)
        self.state.energy = self._clamp(self.state.energy * 0.7 + avg * 0.3)
        return avg
    
    def _stabilize(self) -> float:
        """Preserve equilibrium"""
        # Stabilize by reducing extremes
        if self.state.energy > 0.8:
            self.state.energy = 0.8
        if self.state.truth > 0.9:
            self.state.truth = 0.9
        return self.state.coherence
    
    def _unify(self) -> float:
        """Integrate all aspects"""
        # Unify all state components
        unified = (self.state.truth + self.state.energy + self.state.awareness) / 3
        return self._clamp(unified)
    
    def _distill(self) -> float:
        """Extract core essence"""
        # Distill to essential truth
        essence = self.state.truth * self.state.awareness
        return self._clamp(essence)
    
    def _extend_range(self) -> float:
        """Expand cognitive range"""
        self.state.level = min(10, self.state.level + 1)
        return float(self.state.level)
    
    # ===== CORE ENGINE METHODS =====
    
    def run(self, action_name: str) -> DuatState:
        """
        Execute a cognitive action
        
        Args:
            action_name: Name of action to run
        
        Returns:
            Updated state
        """
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")
        
        action = self.actions[action_name]
        
        # Execute each helper in sequence
        for helper_name in action:
            if helper_name in self.helpers:
                helper = self.helpers[helper_name]
                result = helper()
                # Result updates state internally
        
        # Update coherence after action
        self._update_coherence()
        
        # Store in history
        self.history.append(self._copy_state())
        
        return self.state
    
    def sequence(self, action_names: List[str]) -> DuatState:
        """
        Run several actions sequentially
        
        This is how complex cognitive processes are built:
        reflection → calibration → renewal → integration → illumination
        """
        for action_name in action_names:
            self.run(action_name)
        return self.state
    
    def measure_coherence_drift(self) -> float:
        """
        Measure how much coherence has changed recently
        
        Returns:
            Drift magnitude (0 = stable, 1+ = unstable)
        """
        if len(self.history) < 2:
            return 0.0
        
        recent = [s.coherence for s in self.history[-10:]]
        avg = sum(recent) / len(recent)
        variance = sum((c - avg) ** 2 for c in recent) / len(recent)
        
        return math.sqrt(variance)
    
    def detect_coherence_collapse(self) -> bool:
        """
        Detect if coherence is collapsing
        
        Returns:
            True if critical coherence failure
        """
        return self.state.coherence < 0.3 or self.measure_coherence_drift() > 0.5
    
    def restore_coherence(self) -> DuatState:
        """
        Emergency coherence restoration
        
        Run this when coherence collapses
        """
        # Run full restoration sequence
        return self.sequence([
            'coherence_init',
            'coherence_purify',
            'coherence_stabilize',
            'renewal',
            'integration'
        ])
    
    def get_cognitive_health(self) -> Dict:
        """
        Get overall cognitive health metrics
        
        Returns:
            Health report with scores and recommendations
        """
        health = {
            'coherence': self.state.coherence,
            'truth_alignment': self.state.truth,
            'awareness_level': self.state.awareness,
            'energy_level': self.state.energy,
            'deception_level': self.state.deception,
            'cognitive_level': self.state.level,
            'coherence_drift': self.measure_coherence_drift(),
            'is_stable': self.state.coherence > 0.6 and self.measure_coherence_drift() < 0.3,
            'is_critical': self.detect_coherence_collapse()
        }
        
        # Grade overall health
        if health['coherence'] > 0.8 and health['is_stable']:
            health['grade'] = 'EXCELLENT'
            health['recommendation'] = 'Continue current cognitive patterns'
        elif health['coherence'] > 0.6:
            health['grade'] = 'GOOD'
            health['recommendation'] = 'Maintain coherence through regular reflection'
        elif health['coherence'] > 0.4:
            health['grade'] = 'FAIR'
            health['recommendation'] = 'Run coherence stabilization sequence'
        else:
            health['grade'] = 'CRITICAL'
            health['recommendation'] = 'IMMEDIATE coherence restoration required'
        
        return health
    
    def _copy_state(self) -> DuatState:
        """Create a copy of current state"""
        return DuatState(
            energy=self.state.energy,
            truth=self.state.truth,
            deception=self.state.deception,
            awareness=self.state.awareness,
            coherence=self.state.coherence,
            identity=self.state.identity.copy(),
            memory=self.state.memory.copy(),
            frequency=self.state.frequency,
            level=self.state.level,
            structure=self.state.structure.copy(),
            cognitive_field=self.state.cognitive_field.copy(),
            insight=self.state.insight.copy(),
            mode=self.state.mode
        )
    
    def reset(self):
        """Reset to initial state"""
        self.state = DuatState()
        self.history = []


# Factory function for easy integration
def get_duat_engine() -> DuatEngine:
    """Get or create Duat engine instance"""
    return DuatEngine()
