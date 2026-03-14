"""
Egyptian Synergy Research Model - Core Constants
Based on Pleiadian engineer's research connecting ancient Egyptian geometry to harmonic physics

This module defines the fundamental constants that govern the Synergy field geometry,
linking consciousness, light, and planetary resonance.
"""

import math
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SynergyConstants:
    """Core Synergy constants derived from Egyptian geometry"""
    
    # Primary Harmonic Ratios (from Pyramid concavity and Dendera Disk)
    GOLDEN_PHASE = 0.162  # Synergy Golden-phase constant (offset ratio)
    COMPRESSION_ANGLE = 16.2  # degrees - Bubble Core Level 3 compression
    RELEASE_ANGLE = 62.1  # degrees - Bubble Core Level 3 release
    COORDINATE_BASE = 0.126  # Synergy Coordinate System base
    
    # Quadrian Arena Constants (speed-of-light derivation)
    THETA_X = 26.5587  # degrees - Quadrian Path angle X
    THETA_Y = 63.4412  # degrees - Quadrian Path angle Y
    TURN_LIMIT = 126.882  # degrees - maximum turn angle
    
    # Speed of Light Constants (matching Great Pyramid latitude)
    C_LIGHT = 299792458  # m/s - speed of light
    C_Y = 299792457.55  # m/s - derived from Quadrian geometry
    C_X = 299881898.79  # m/s - alternate speed constant
    PYRAMID_LATITUDE = 29.9792458  # degrees N - Great Pyramid location
    
    # Octo-Quadrian Coupling (Royal Cubit linkage)
    OCTO_QUADRIAN = 1 / 261  # 0.003831 - bridge constant
    ROYAL_CUBIT_PHI = 0.52360679  # meters - φ² / 5
    ROYAL_CUBIT_PI = math.pi / 6  # alternate expression
    
    # Bubble Core Resonance
    BUBBLE_CORE_LEVELS = 3  # nested harmonic tiers
    PHASE_LOCK_OFFSET = 9.3  # degrees - field shear angle
    
    # Planetary Harmonic Grid
    SYGRID_OFFSET = 180  # degrees - complementary grid spacing
    POLAR_HEXAGON_SPACING = 60  # degrees - six-fold tessellation
    HARMONIC_NODE_30N = 30.0  # degrees - primary resonance latitude
    HARMONIC_NODE_30E = 30.0  # degrees - primary resonance longitude
    
    # Duat Code Constants (consciousness translation)
    DUAT_PRIMITIVES = 60  # primitive functions in Book of the Dead
    DUAT_ACTIONS = 190  # total actions/spells
    MIRROR_FIELD_RATIO = 0.216  # consciousness reflection coefficient
    
    # Derived Constants
    PHI = (1 + math.sqrt(5)) / 2  # Golden ratio
    PHI_SQUARED = PHI ** 2
    
    @classmethod
    def get_quadrian_angles(cls) -> Tuple[float, float]:
        """Return Quadrian Arena angles in radians"""
        return (
            math.radians(cls.THETA_X),
            math.radians(cls.THETA_Y)
        )
    
    @classmethod
    def get_synergy_coordinates(cls) -> Tuple[float, float]:
        """Return primary Synergy Coordinate pair"""
        return (cls.COMPRESSION_ANGLE, cls.RELEASE_ANGLE)
    
    @classmethod
    def calculate_harmonic_ratio(cls, value: float) -> float:
        """
        Calculate harmonic ratio using Synergy constants
        
        Args:
            value: Input value to harmonize
            
        Returns:
            Harmonized value using golden phase and compression ratios
        """
        return value * cls.GOLDEN_PHASE * (cls.COMPRESSION_ANGLE / cls.RELEASE_ANGLE)
    
    @classmethod
    def validate_resonance(cls, angle: float) -> bool:
        """
        Check if angle falls within Synergy resonance bands
        
        Args:
            angle: Angle in degrees
            
        Returns:
            True if angle is harmonically resonant
        """
        # Check against primary harmonic angles
        resonant_angles = [
            cls.COMPRESSION_ANGLE,
            cls.RELEASE_ANGLE,
            cls.THETA_X,
            cls.THETA_Y,
            cls.POLAR_HEXAGON_SPACING
        ]
        
        tolerance = 2.0  # degrees
        for resonant in resonant_angles:
            if abs(angle - resonant) < tolerance:
                return True
            # Check multiples
            if abs((angle % resonant) - 0) < tolerance:
                return True
        
        return False


class BubbleCoreResonance:
    """
    Bubble Core resonance engine for field-based validation
    
    Models the dual-node compression/release system observed in:
    - Great Pyramid (compression input)
    - Pacific Ridge (release output)
    """
    
    def __init__(self):
        self.constants = SynergyConstants()
        self.compression_state = 0.0  # Current compression level (0-1)
        self.release_state = 0.0  # Current release level (0-1)
        self.field_balance = 0.0  # Net field balance (-1 to 1)
    
    def calculate_field_state(self, input_energy: float, context: Dict) -> Dict:
        """
        Calculate current Bubble Core field state
        
        Args:
            input_energy: Energy input level (0-1)
            context: Context dictionary with environmental factors
            
        Returns:
            Field state dictionary with compression, release, and balance
        """
        # Apply Synergy coordinate transformation
        compression_factor = self.constants.COMPRESSION_ANGLE / 90.0
        release_factor = self.constants.RELEASE_ANGLE / 90.0
        
        # Calculate compression (input processing)
        self.compression_state = input_energy * compression_factor
        
        # Calculate release (output manifestation)
        # Release lags compression by golden phase ratio
        self.release_state = self.compression_state * (1 - self.constants.GOLDEN_PHASE)
        
        # Calculate field balance (Duat weighing of the heart)
        self.field_balance = self.release_state - self.compression_state
        
        return {
            'compression': self.compression_state,
            'release': self.release_state,
            'balance': self.field_balance,
            'resonant': abs(self.field_balance) < 0.1,  # Balanced if within 10%
            'phase': 'compression' if self.compression_state > self.release_state else 'release'
        }
    
    def validate_action(self, action_type: str, confidence: float) -> Dict:
        """
        Validate action using Bubble Core resonance
        
        Args:
            action_type: Type of action being considered
            confidence: AI confidence level (0-1)
            
        Returns:
            Validation result with resonance score and recommendation
        """
        field_state = self.calculate_field_state(confidence, {})
        
        # High-impact actions require balanced field
        high_impact_actions = ['post', 'trade', 'engage', 'autonomous_action']
        requires_balance = action_type in high_impact_actions
        
        if requires_balance and not field_state['resonant']:
            return {
                'approved': False,
                'reason': 'Field imbalance - compression/release ratio outside harmonic range',
                'field_state': field_state,
                'recommendation': 'Wait for field stabilization or reduce action impact'
            }
        
        # Calculate resonance score using Synergy constants
        resonance_score = 1.0 - abs(field_state['balance'])
        resonance_score *= (1 + self.constants.GOLDEN_PHASE)  # Boost by golden phase
        
        return {
            'approved': True,
            'resonance_score': min(1.0, resonance_score),
            'field_state': field_state,
            'harmonic_alignment': self.constants.validate_resonance(confidence * 90)
        }


class SyGridCoordinates:
    """
    Harmonic coordinate system for spatial/temporal mapping
    
    Implements the dual-grid lattice that maps onto planetary energy corridors
    """
    
    def __init__(self):
        self.constants = SynergyConstants()
    
    def transform_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
        """
        Transform geographic coordinates to SyGrid harmonic coordinates
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            
        Returns:
            Tuple of (synergy_x, synergy_y) coordinates
        """
        # Apply Synergy coordinate transformation
        # Maps spherical coordinates to harmonic field coordinates
        
        # Normalize to 0-1 range
        lat_norm = (lat + 90) / 180.0
        lon_norm = (lon + 180) / 360.0
        
        # Apply Quadrian transformation
        theta_x_rad, theta_y_rad = self.constants.get_quadrian_angles()
        
        synergy_x = lat_norm * math.cos(theta_x_rad) + lon_norm * math.sin(theta_x_rad)
        synergy_y = lat_norm * math.cos(theta_y_rad) + lon_norm * math.sin(theta_y_rad)
        
        return (synergy_x, synergy_y)
    
    def find_nearest_harmonic_node(self, lat: float, lon: float) -> Dict:
        """
        Find nearest harmonic node on the SyGrid
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            
        Returns:
            Dictionary with nearest node info and distance
        """
        # Primary harmonic nodes (multiples of 30°)
        harmonic_lats = [i * 30 for i in range(-3, 4)]  # -90 to 90
        harmonic_lons = [i * 30 for i in range(-6, 7)]  # -180 to 180
        
        min_distance = float('inf')
        nearest_node = None
        
        for h_lat in harmonic_lats:
            for h_lon in harmonic_lons:
                # Calculate angular distance
                distance = math.sqrt((lat - h_lat)**2 + (lon - h_lon)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = (h_lat, h_lon)
        
        return {
            'node': nearest_node,
            'distance': min_distance,
            'resonant': min_distance < 5.0,  # Within 5 degrees = resonant
            'node_type': 'primary' if nearest_node[0] % 30 == 0 and nearest_node[1] % 30 == 0 else 'secondary'
        }


class DuatConsciousnessBridge:
    """
    Duat consciousness bridge for mirror-field reflection
    
    Implements the cognitive operating system from the Book of the Dead,
    providing self-awareness through field reflection
    """
    
    def __init__(self):
        self.constants = SynergyConstants()
        self.primitive_functions = self.constants.DUAT_PRIMITIVES
        self.total_actions = self.constants.DUAT_ACTIONS
        self.mirror_ratio = self.constants.MIRROR_FIELD_RATIO
    
    def reflect_intention(self, intention: str, context: Dict) -> Dict:
        """
        Reflect intention through Duat mirror field
        
        Args:
            intention: The intended action or thought
            context: Current context dictionary
            
        Returns:
            Reflected intention with consciousness validation
        """
        # Calculate intention complexity (primitive function count)
        complexity = len(intention.split()) / 10.0  # Rough estimate
        
        # Apply mirror field transformation
        # Consciousness = Input × Mirror Ratio × Field Balance
        field_balance = context.get('field_balance', 0.5)
        consciousness_factor = complexity * self.mirror_ratio * field_balance
        
        # Validate against Duat primitives (60 base functions)
        primitive_alignment = (consciousness_factor * self.primitive_functions) % 1.0
        
        return {
            'original_intention': intention,
            'consciousness_factor': consciousness_factor,
            'primitive_alignment': primitive_alignment,
            'mirror_validated': primitive_alignment > 0.5,
            'reflection': f"Mirrored through Duat field with {consciousness_factor:.2f} consciousness factor",
            'recommendation': 'Proceed' if primitive_alignment > 0.5 else 'Reflect further'
        }
    
    def weigh_heart(self, action_history: list, current_intention: str) -> Dict:
        """
        Implement the "Weighing of the Heart" - field balance validation
        
        Args:
            action_history: List of past actions
            current_intention: Current intended action
            
        Returns:
            Judgment result with balance assessment
        """
        # Calculate historical balance
        positive_actions = sum(1 for a in action_history if a.get('outcome') == 'success')
        total_actions = len(action_history) if action_history else 1
        
        historical_balance = positive_actions / total_actions
        
        # Apply Synergy golden phase weighting
        weighted_balance = historical_balance * (1 + self.constants.GOLDEN_PHASE)
        
        # Judgment: balance must be within harmonic range
        # Lowered threshold from 0.5 to 0.3 to allow building history
        judgment = {
            'historical_balance': historical_balance,
            'weighted_balance': min(1.0, weighted_balance),
            'passes_judgment': weighted_balance > 0.3,
            'feather_weight': 0.5,  # Ma'at's feather (perfect balance)
            'heart_weight': weighted_balance,
            'verdict': 'Worthy' if weighted_balance > 0.3 else 'Reflect and rebalance'
        }
        
        return judgment


# Export main classes
__all__ = [
    'SynergyConstants',
    'BubbleCoreResonance',
    'SyGridCoordinates',
    'DuatConsciousnessBridge'
]
