"""
Value Dynamics Model (VDM) - FairMind DNA Core

Thermodynamic value theory: VALUE = a + b + c + d
Based on FairMind DNA research (2015-2026).

This is the "ethical substrate" for decision-making.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class ValueType(Enum):
    """Four pillars of value"""
    SENTIMENTAL = "a"  # Emotional/symbolic
    INTRINSIC = "b"    # Physical/material
    FUNCTIONAL = "c"   # Utility/performance
    COMPRESSED = "d"   # Historical/inherited


@dataclass
class ValueComponents:
    """
    The four components of value in SVU (Synergy Value Units)
    SVU = human operational hours
    """
    a: float = 0.0  # Sentimental value (emotional investment)
    b: float = 0.0  # Intrinsic value (material/energy cost)
    c: float = 0.0  # Functional value (utility produced)
    d: float = 0.0  # Compressed value (historical dependencies)
    
    @property
    def total(self) -> float:
        """Total value in SVU"""
        return self.a + self.b + self.c + self.d
    
    def to_dict(self) -> Dict:
        return {
            'sentimental': self.a,
            'intrinsic': self.b,
            'functional': self.c,
            'compressed': self.d,
            'total_svu': self.total
        }


class ValueDynamicsModel:
    """
    VDM - Thermodynamic value theory
    VALUE = a + b + c + d (in SVU units)
    
    This enables ethical decision-making by measuring true value,
    not just engagement or profit.
    """
    
    def __init__(self):
        self.history: list = []
    
    def calculate_value(self, action: Dict) -> ValueComponents:
        """
        Calculate total value of an action
        
        Args:
            action: Action details including:
                - time_invested: Hours spent
                - energy_cost: Computational/physical energy
                - utility_produced: Measurable benefit
                - dependencies: Historical work required
        
        Returns:
            ValueComponents with all four pillars
        """
        a = self._sentimental_value(action)
        b = self._intrinsic_value(action)
        c = self._functional_value(action)
        d = self._compressed_value(action)
        
        components = ValueComponents(a=a, b=b, c=c, d=d)
        
        # Store in history
        self.history.append({
            'action': action.get('description', 'unknown'),
            'components': components,
            'timestamp': action.get('timestamp', 'unknown')
        })
        
        return components
    
    def _sentimental_value(self, action: Dict) -> float:
        """
        Calculate sentimental value (a)
        
        Primary anchor: Time invested
        Sentimental value grows with temporal investment
        """
        time_invested = action.get('time_invested', 0.0)  # Hours
        emotional_weight = action.get('emotional_weight', 1.0)  # 0-2 multiplier
        
        # Base: time invested in SVU
        base_svu = time_invested
        
        # Adjust for emotional significance
        sentimental_svu = base_svu * emotional_weight
        
        return sentimental_svu
    
    def _intrinsic_value(self, action: Dict) -> float:
        """
        Calculate intrinsic value (b)
        
        Physical/thermodynamic worth
        Energy in equilibrium with nature
        """
        energy_cost = action.get('energy_cost', 0.0)  # kWh or compute units
        material_quality = action.get('material_quality', 1.0)  # 0-1 quality factor
        
        # Convert energy to SVU (rough approximation)
        # 1 kWh ≈ 0.1 SVU (human hour equivalent)
        energy_svu = energy_cost * 0.1
        
        # Adjust for quality
        intrinsic_svu = energy_svu * material_quality
        
        return intrinsic_svu
    
    def _functional_value(self, action: Dict) -> float:
        """
        Calculate functional value (c)
        
        How effectively something fulfills its role
        Kinetic value - energy in motion
        """
        utility_produced = action.get('utility_produced', 0.0)  # Measurable benefit
        efficiency = action.get('efficiency', 1.0)  # 0-1 efficiency factor
        
        # Utility in SVU (time saved or value created)
        functional_svu = utility_produced * efficiency
        
        return functional_svu
    
    def _compressed_value(self, action: Dict) -> float:
        """
        Calculate compressed value (d)
        
        Invisible history inside the object
        Inherited effort unpriced in the present
        """
        dependencies = action.get('dependencies', [])  # List of historical work
        dependency_depth = action.get('dependency_depth', 1)  # How many layers
        
        # Each dependency adds compressed value
        compressed_svu = len(dependencies) * 0.5 * dependency_depth
        
        return compressed_svu
    
    def inversion_test(self, action: Dict) -> Dict:
        """
        Test if action creates or extracts value
        
        The Inversion Test (qualitative):
        1. Dependency: Freedom (graduation) or Addiction (need)?
        2. Energy: Generate (add density) or Dilute (remove integrity)?
        3. Source: Create new value or Capture existing value?
        
        Returns:
            inversion_score: IS = GC × ΔI × SR
            - IS > 0: value generation (synergy)
            - IS < 0: entropy extraction (inversion)
        """
        gc = self._graduation_coefficient(action)
        delta_i = self._integrity_delta(action)
        sr = self._source_ratio(action)
        
        inversion_score = gc * delta_i * sr
        
        result = {
            'graduation_coefficient': gc,
            'integrity_delta': delta_i,
            'source_ratio': sr,
            'inversion_score': inversion_score,
            'verdict': 'SYNERGY' if inversion_score > 0 else 'ENTROPY' if inversion_score < 0 else 'NEUTRAL',
            'is_entropy_merchant': inversion_score < -0.5
        }
        
        return result
    
    def _graduation_coefficient(self, action: Dict) -> float:
        """
        GC = 1 / (time-to-independence in SVU)
        
        Higher = faster graduation (creates freedom)
        Lower = slower graduation (creates dependency)
        """
        time_to_independence = action.get('time_to_independence', 10.0)  # Hours
        
        if time_to_independence <= 0:
            return 0.0  # Infinite dependency
        
        gc = 1.0 / time_to_independence
        return gc
    
    def _integrity_delta(self, action: Dict) -> float:
        """
        ΔI = Δ(b + d) per use cycle in SVU
        
        Positive = generation (adds density)
        Negative = dilution (removes integrity)
        """
        value_before = action.get('value_before', 0.0)
        value_after = action.get('value_after', 0.0)
        
        delta_i = value_after - value_before
        return delta_i
    
    def _source_ratio(self, action: Dict) -> float:
        """
        SR = new value created / value redirected from existing pools
        
        < 1 = capture (rent-seeking)
        > 1 = creation (value generation)
        """
        value_created = action.get('value_created', 0.0)
        value_captured = action.get('value_captured', 1.0)  # Avoid division by zero
        
        sr = value_created / value_captured if value_captured > 0 else 0.0
        return sr
    
    def detect_entropy_merchant(self, entity_id: str, history: list) -> bool:
        """
        Detect if entity is extracting value without creating
        
        Entropy Merchant = Addiction + Dilution + Capture
        """
        if not history:
            return False
        
        # Analyze entity's action history
        is_addictive = self._creates_dependency(history)
        is_diluting = self._reduces_integrity(history)
        is_capturing = self._captures_not_creates(history)
        
        return is_addictive and is_diluting and is_capturing
    
    def _creates_dependency(self, history: list) -> bool:
        """Check if actions create dependency"""
        # If most actions have low graduation coefficient
        low_gc_count = sum(1 for h in history if h.get('gc', 1.0) < 0.2)
        return low_gc_count > len(history) * 0.6
    
    def _reduces_integrity(self, history: list) -> bool:
        """Check if actions reduce integrity"""
        # If most actions have negative integrity delta
        negative_di_count = sum(1 for h in history if h.get('delta_i', 0.0) < 0)
        return negative_di_count > len(history) * 0.6
    
    def _captures_not_creates(self, history: list) -> bool:
        """Check if entity captures more than creates"""
        # If most actions have source ratio < 1
        capture_count = sum(1 for h in history if h.get('sr', 1.0) < 1.0)
        return capture_count > len(history) * 0.6
    
    def get_value_stats(self) -> Dict:
        """Get statistics on value calculations"""
        if not self.history:
            return {'total_calculations': 0}
        
        total_svu = sum(h['components'].total for h in self.history)
        avg_svu = total_svu / len(self.history)
        
        # Average by component
        avg_a = sum(h['components'].a for h in self.history) / len(self.history)
        avg_b = sum(h['components'].b for h in self.history) / len(self.history)
        avg_c = sum(h['components'].c for h in self.history) / len(self.history)
        avg_d = sum(h['components'].d for h in self.history) / len(self.history)
        
        return {
            'total_calculations': len(self.history),
            'total_svu': total_svu,
            'avg_svu_per_action': avg_svu,
            'avg_components': {
                'sentimental': avg_a,
                'intrinsic': avg_b,
                'functional': avg_c,
                'compressed': avg_d
            },
            'dominant_component': max(
                [('sentimental', avg_a), ('intrinsic', avg_b), 
                 ('functional', avg_c), ('compressed', avg_d)],
                key=lambda x: x[1]
            )[0]
        }


# Factory function for easy integration
def get_value_dynamics_model() -> ValueDynamicsModel:
    """Get or create VDM instance"""
    return ValueDynamicsModel()
