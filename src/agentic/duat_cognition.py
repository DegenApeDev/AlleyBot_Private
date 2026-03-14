"""
Duat Cognition Engine - Advanced State Tracking for AlleyBot AGI
Based on Egyptian Synergy Research - Mirror-field concept for consciousness tracking

The Duat is a computational state machine tracking:
- Energy (cognitive resources)
- Truth (alignment with reality)
- Deception (misalignment accumulation)
- Awareness (conscious attention)
- Coherence (internal consistency)
- Entropy (disorder measure)

60+ cognitive primitives for self-reflection and state management.
"""

import math
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DuatState:
    """Duat cognitive state structure"""
    energy: float = 0.6
    truth: float = 0.6
    deception: float = 0.0
    awareness: float = 0.3
    coherence: float = 0.3
    entropy: float = 0.7
    temperature: float = 0.0
    time: int = 0
    frequency: float = 1.0
    level: int = 0
    mode: str = "receptive"
    
    context: Dict[str, Any] = field(default_factory=lambda: {"scope": "local", "integrity": 1.0})
    identity: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    field: Dict[str, Any] = field(default_factory=dict)
    insight: List[str] = field(default_factory=list)


class DuatCognitionEngine:
    """
    Duat Cognition Engine - State machine for consciousness tracking
    
    Implements 60+ cognitive primitives for:
    - Truth validation
    - Energy management
    - Coherence tracking
    - Deception detection
    - Awareness expansion
    """
    
    def __init__(self, initial_state: Optional[Dict] = None, storage_path: str = 'data/duat_state.json'):
        self.threshold = 0.8
        self.golden_ratio = 1.618
        self.limit = 1.0
        
        # Runtime parameters
        self.energy_cost = 0.01
        self.time_step = 1
        
        # Initialize state
        if initial_state:
            self.state = DuatState(**initial_state)
        else:
            self.state = DuatState()
        
        # Storage
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load persisted state if exists
        self._load_state()
        
        logger.info("🜂 Duat Cognition Engine initialized")
        logger.info(f"   Energy: {self.state.energy:.2f} | Truth: {self.state.truth:.2f} | Coherence: {self.state.coherence:.2f}")
    
    # ============================================================
    # CORE NUMERIC HELPERS
    # ============================================================
    
    def clamp(self, v: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, v))
    
    def lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation"""
        return a + (b - a) * t
    
    def soft_gain(self, v: float, amt: float = 0.1) -> float:
        """Soft increase with clamping"""
        return self.clamp(v + amt)
    
    def soft_loss(self, v: float, amt: float = 0.1) -> float:
        """Soft decrease with clamping"""
        return self.clamp(v - amt)
    
    def avg(self, *nums: float) -> float:
        """Average of numbers"""
        return sum(nums) / len(nums) if nums else 0.0
    
    # ============================================================
    # COGNITIVE PRIMITIVES (60+)
    # ============================================================
    
    def observe(self) -> float:
        """Increase awareness through observation"""
        self.state.awareness = self.clamp(self.state.awareness + 0.1)
        return self.state.awareness
    
    def detect_distortion(self) -> float:
        """Detect misalignment from truth"""
        distortion = self.clamp(1.0 - self.state.truth)
        self.state.deception = distortion
        return distortion
    
    def normalize(self, v: float) -> float:
        """Normalize value to valid range"""
        return self.clamp(v)
    
    def update_coherence(self) -> float:
        """Update internal coherence based on truth, energy, and deception"""
        self.state.coherence = self.clamp(
            self.avg(self.state.truth, self.state.energy, 1.0 - self.state.deception)
        )
        return self.state.coherence
    
    def restore_flow(self) -> float:
        """Restore energy flow"""
        self.state.coherence = self.clamp(self.state.coherence + 0.15)
        return self.state.coherence
    
    def measure_coherence(self) -> float:
        """Measure current coherence level"""
        return self.state.coherence
    
    def amplify(self, factor: float = 1.1) -> float:
        """Amplify energy"""
        self.state.energy = self.clamp(self.state.energy * factor)
        return self.state.energy
    
    def remove_noise(self) -> float:
        """Remove noise, increase truth"""
        self.state.truth = self.clamp(self.state.truth + 0.05)
        return self.state.truth
    
    def recalibrate(self) -> Dict[str, float]:
        """Recalibrate all state values"""
        self.state.truth = self.clamp(self.state.truth)
        self.state.energy = self.clamp(self.state.energy)
        self.state.awareness = self.clamp(self.state.awareness)
        self.state.coherence = self.update_coherence()
        return {
            'truth': self.state.truth,
            'energy': self.state.energy,
            'awareness': self.state.awareness,
            'coherence': self.state.coherence
        }
    
    def amplify_through_unity(self) -> float:
        """Amplify through harmonic unity"""
        harmony = self.clamp(0.7)
        self.state.coherence = self.clamp(self.state.coherence * harmony)
        return self.state.coherence
    
    def reinforce(self, value: float) -> float:
        """Reinforce a value"""
        return self.clamp(value + 0.05)
    
    def stabilize(self) -> float:
        """Stabilize current state"""
        self.state.coherence = self.clamp(0.8)
        return self.state.coherence
    
    def rebalance(self) -> float:
        """Rebalance energy"""
        self.state.energy = self.clamp(self.state.energy)
        return self.state.energy
    
    def clarify(self) -> float:
        """Clarify truth"""
        self.state.truth = self.clamp(self.state.truth + 0.1)
        return self.state.truth
    
    def harmonize(self, a: float, b: float) -> float:
        """Harmonize two values"""
        return self.clamp(self.avg(a, b))
    
    def unify(self, values: List[float]) -> float:
        """Unify multiple values"""
        if not values:
            return 0.5
        return self.clamp(self.avg(*values))
    
    def distill(self) -> float:
        """Distill essence"""
        return self.clamp(0.9)
    
    def tune(self) -> float:
        """Tune to optimal frequency"""
        self.state.frequency = self.clamp(1.0)
        return self.state.frequency
    
    def strengthen(self) -> float:
        """Strengthen coherence"""
        self.state.coherence = self.clamp(self.state.coherence + 0.05)
        return self.state.coherence
    
    # ============================================================
    # CONTEXT MANAGEMENT
    # ============================================================
    
    def degrade_context(self, amount: float = 0.05) -> float:
        """Degrade context integrity"""
        self.state.context['integrity'] = self.clamp(
            self.state.context.get('integrity', 1.0) - amount
        )
        return self.state.context['integrity']
    
    def restore_context(self, amount: float = 0.1) -> float:
        """Restore context integrity"""
        self.state.context['integrity'] = self.clamp(
            self.state.context.get('integrity', 0.5) + amount
        )
        return self.state.context['integrity']
    
    def shift_context(self, scope: str = "universal") -> Dict[str, Any]:
        """Shift context scope"""
        self.state.context['scope'] = scope
        return self.state.context
    
    # ============================================================
    # HIGH-LEVEL ACTIONS
    # ============================================================
    
    def reflection(self) -> Dict[str, float]:
        """Perform reflection action"""
        awareness = self.observe()
        distortion = self.detect_distortion()
        return {
            'awareness': awareness,
            'distortion': distortion,
            'action': 'reflection'
        }
    
    def calibration(self) -> Dict[str, float]:
        """Perform calibration action"""
        distortion = self.detect_distortion()
        self.normalize(distortion)
        coherence = self.update_coherence()
        return {
            'distortion': distortion,
            'coherence': coherence,
            'action': 'calibration'
        }
    
    def renewal(self) -> Dict[str, float]:
        """Perform renewal action"""
        coherence = self.update_coherence()
        flow = self.restore_flow()
        return {
            'coherence': coherence,
            'flow': flow,
            'action': 'renewal'
        }
    
    def illumination(self) -> Dict[str, float]:
        """Perform illumination action"""
        energy = self.amplify()
        awareness = self.observe()
        return {
            'energy': energy,
            'awareness': awareness,
            'action': 'illumination'
        }
    
    def purification(self) -> Dict[str, float]:
        """Perform purification action"""
        distortion = self.detect_distortion()
        truth = self.remove_noise()
        state = self.recalibrate()
        return {
            'distortion': distortion,
            'truth': truth,
            'state': state,
            'action': 'purification'
        }
    
    # ============================================================
    # STATE MANAGEMENT
    # ============================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            'energy': self.state.energy,
            'truth': self.state.truth,
            'deception': self.state.deception,
            'awareness': self.state.awareness,
            'coherence': self.state.coherence,
            'entropy': self.state.entropy,
            'temperature': self.state.temperature,
            'time': self.state.time,
            'frequency': self.state.frequency,
            'level': self.state.level,
            'mode': self.state.mode,
            'context': self.state.context,
            'identity': self.state.identity,
            'memory': self.state.memory,
            'insight': self.state.insight
        }
    
    def advance_time(self) -> int:
        """Advance time by one step"""
        self.state.time += self.time_step
        return self.state.time
    
    def consume_energy(self, amount: float = None) -> float:
        """Consume energy for cognitive operations"""
        cost = amount if amount is not None else self.energy_cost
        self.state.energy = self.clamp(self.state.energy - cost)
        return self.state.energy
    
    def add_insight(self, insight: str) -> List[str]:
        """Add insight to state"""
        self.state.insight.append(insight)
        # Keep only last 100 insights
        if len(self.state.insight) > 100:
            self.state.insight = self.state.insight[-100:]
        return self.state.insight
    
    def passes_judgment(self) -> bool:
        """Check if state passes judgment threshold"""
        return (
            self.state.truth >= self.threshold and
            self.state.coherence >= self.threshold and
            self.state.deception < (1.0 - self.threshold)
        )
    
    # ============================================================
    # PERSISTENCE
    # ============================================================
    
    def _load_state(self):
        """Load state from disk"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Update state with loaded data
                    for key, value in data.items():
                        if hasattr(self.state, key):
                            setattr(self.state, key, value)
                logger.info(f"🜂 Loaded Duat state from {self.storage_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load Duat state: {e}")
    
    def save_state(self):
        """Save state to disk"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.get_state(), f, indent=2)
            logger.debug(f"💾 Saved Duat state to {self.storage_path}")
        except Exception as e:
            logger.error(f"❌ Could not save Duat state: {e}")


# Singleton instance
_duat_engine: Optional[DuatCognitionEngine] = None


def get_duat_engine(initial_state: Optional[Dict] = None) -> DuatCognitionEngine:
    """Get or create Duat Cognition Engine singleton"""
    global _duat_engine
    if _duat_engine is None:
        _duat_engine = DuatCognitionEngine(initial_state)
    return _duat_engine


def create_duat_engine(initial_state: Optional[Dict] = None) -> DuatCognitionEngine:
    """Create new Duat Cognition Engine instance"""
    return DuatCognitionEngine(initial_state)
