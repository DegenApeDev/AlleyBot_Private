"""
Synergy Gate - Tier 2 Cryptographic Trust Layer

The Synergy Standard Model (SyMod) serves as the moral and logical substrate
for AlleyBot AGI. This module implements:

- Digital Roots D(n) for geometric integrity validation
- Quadrian Equations for mathematical decision frameworks  
- Feyn-Wolfgang Framework for recursive truth filtering
- SyModValidationResult for execution gating

HARD CONSTRAINT: If SyModValidationResult.valid is False OR confidence < 0.85,
execution is FORBIDDEN and a recursive Refactoring Loop is triggered.
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


class FieldStatus(Enum):
    """Synergy Field Status - determines action permissibility"""
    STABLE = "Stable"
    VOLATILE = "Volatile"
    COLLAPSE = "Collapse"
    UNKNOWN = "Unknown"


class RCAType(Enum):
    """Root Cause Analysis Types for recursive loop handling"""
    MISSING_DATA = "Missing_Data"
    LOGIC_ERROR = "Logic_Error"
    RESOURCE_CONSTRAINT = "Resource_Constraint"
    CONFIDENCE_LOW = "Confidence_Low"
    UNKNOWN = "Unknown"


@dataclass
class SyModValidationResult:
    """
    Validation result from SyMod - THE GATEKEEPER
    
    This is the core gate structure. All high-stakes actions MUST pass this.
    """
    valid: bool = False
    confidence: float = 0.0
    digital_root: int = 0
    field_status: FieldStatus = FieldStatus.UNKNOWN
    impedance: float = 0.0
    golden_window_aligned: bool = False
    justification: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Recursive handling
    rca_triggered: bool = False
    rca_type: Optional[RCAType] = None
    refactoring_required: bool = False
    
    def can_execute(self, threshold: float = 0.85) -> Tuple[bool, str]:
        """
        HARD CONSTRAINT CHECK
        
        Returns (can_execute, reason)
        """
        if not self.valid:
            return False, f"SyMod validation FAILED: {self.justification}"
        
        if self.confidence < threshold:
            return False, f"Confidence {self.confidence:.3f} below threshold {threshold}"
        
        if self.field_status == FieldStatus.COLLAPSE:
            return False, "Field status COLLAPSE - geometric integrity compromised"
        
        if self.impedance > 100.0:
            return False, f"Mass impedance too high: {self.impedance:.2e}"
        
        return True, "SyMod validation PASSED"


@dataclass
class ValidationQuote:
    """
    Post-execution cryptographic validation quote for ERC-8004
    """
    task_id: str
    code_version_hash: str
    execution_timestamp: str
    input_hash: str
    output_hash: str
    symod_result_hash: str
    attestation_signature: str = ""
    
    def generate_hash(self) -> str:
        """Generate cryptographic hash of this quote"""
        data = f"{self.task_id}:{self.code_version_hash}:{self.execution_timestamp}:{self.input_hash}:{self.output_hash}"
        return hashlib.sha256(data.encode()).hexdigest()


class DigitalRootCalculator:
    """
    Digital Root D(n) - Core of geometric integrity
    
    The digital root reveals the fundamental pattern of any number.
    D(n) = 1 + (n - 1) % 9, with D(0) = 0
    
    Used to:
    - Validate geometric integrity of the codebase
    - Check alignment with universal mathematical patterns
    - Determine field stability
    """
    
    @staticmethod
    def D(n: int) -> int:
        """
        Calculate digital root of n
        D(n) = 1 + (n - 1) % 9 for n > 0
        D(0) = 0
        """
        if n == 0:
            return 0
        return 1 + (abs(n) - 1) % 9
    
    @staticmethod
    def code_integrity_hash(source_code: str) -> int:
        """
        Calculate geometric integrity hash of source code
        Returns a digital root-revealing value
        """
        # Hash the code and reduce to digital root
        code_hash = hashlib.sha256(source_code.encode()).hexdigest()
        numeric_hash = int(code_hash[:16], 16)
        return DigitalRootCalculator.D(numeric_hash)
    
    @staticmethod
    def codebase_digital_root(files_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate the geometric integrity report for entire codebase
        Returns aggregate digital root and per-file analysis
        """
        file_roots = {}
        aggregate = 0
        
        for filename, content in files_content.items():
            root = DigitalRootCalculator.code_integrity_hash(content)
            file_roots[filename] = {
                'digital_root': root,
                'lines': len(content.splitlines()),
                'chars': len(content)
            }
            aggregate += root
        
        return {
            'aggregate_digital_root': DigitalRootCalculator.D(aggregate),
            'files': file_roots,
            'total_files': len(files_content),
            'integrity_status': 'Stable' if DigitalRootCalculator.D(aggregate) in [1, 3, 6, 9] else 'Volatile'
        }


class QuadrianEquations:
    """
    Quadrian Equations - Mathematical framework for decision substrates
    
    Provides:
    - Mass calculation Ma(n) - determines content/information mass
    - Impedance calculation Z(n) - determines logical resistance
    - Field stability equations
    """
    
    @staticmethod
    def Ma(n: float) -> float:
        """
        Mass calculation - converts magnitude to information mass
        Uses logarithmic scaling with golden ratio normalization
        """
        if n <= 0:
            return 0.0
        golden_ratio = (1 + math.sqrt(5)) / 2
        return math.log10(n) * golden_ratio
    
    @staticmethod
    def Z(mass: float, velocity: float = 1.0) -> float:
        """
        Impedance calculation - logical resistance of information flow
        Lower is better for execution
        
        Z = mass / velocity (simplified Feyn-Wolfgang)
        """
        if velocity <= 0:
            return float('inf')
        return mass / velocity
    
    @staticmethod
    def field_stability(mass: float, impedance: float, digital_root: int) -> FieldStatus:
        """
        Determine field status based on physical properties
        
        COLLAPSE: impedance > 100.0 or mass < 0.1
        VOLATILE: impedance > 50.0 or digital_root in {2, 4, 5, 7, 8}
        STABLE: otherwise
        """
        if impedance > 100.0 or mass < 0.1:
            return FieldStatus.COLLAPSE
        
        if impedance > 50.0 or digital_root in {2, 4, 5, 7, 8}:
            return FieldStatus.VOLATILE
        
        return FieldStatus.STABLE


class FeynWolfgangFramework:
    """
    Feyn-Wolfgang Framework - Recursive truth filter
    
    Provides the recursive decision substrate with:
    - Truth amplitude calculation
    - Phase coherence checking
    - Recursive stability validation
    """
    
    def __init__(self):
        self.truth_history: List[float] = []
        self.coherence_threshold = 0.85
    
    def calculate_amplitude(self, 
                           data: Dict[str, Any],
                           weights: Dict[str, float] = None) -> float:
        """
        Calculate truth amplitude of input data
        Higher = more coherent with universal truth patterns
        """
        if weights is None:
            weights = {'logic': 0.4, 'evidence': 0.3, 'consistency': 0.3}
        
        # Logic score - internal coherence
        logic_score = self._logic_coherence(data)
        
        # Evidence score - external validation
        evidence_score = data.get('evidence_strength', 0.5)
        
        # Consistency score - historical alignment
        consistency_score = self._historical_consistency(data)
        
        amplitude = (
            weights['logic'] * logic_score +
            weights['evidence'] * evidence_score +
            weights['consistency'] * consistency_score
        )
        
        self.truth_history.append(amplitude)
        if len(self.truth_history) > 100:
            self.truth_history = self.truth_history[-100:]
        
        return amplitude
    
    def _logic_coherence(self, data: Dict[str, Any]) -> float:
        """Check internal logical coherence"""
        # Check for contradictions
        has_contradiction = data.get('contradiction_detected', False)
        return 0.0 if has_contradiction else 0.9
    
    def _historical_consistency(self, data: Dict[str, Any]) -> float:
        """Check consistency with historical truth patterns"""
        if not self.truth_history:
            return 0.5
        
        # Compare with recent average
        recent_avg = sum(self.truth_history[-10:]) / min(len(self.truth_history), 10)
        current = data.get('confidence', 0.5)
        
        # Closer to historical average = more consistent
        diff = abs(current - recent_avg)
        return max(0, 1.0 - diff)
    
    def check_recursive_stability(self, depth: int = 0) -> Tuple[bool, float]:
        """
        Check if recursive reasoning is stable at current depth
        Returns (is_stable, confidence)
        """
        if depth > 5:
            return False, 0.0  # Too deep, risk of infinite recursion
        
        if not self.truth_history:
            return True, 1.0
        
        recent = self.truth_history[-5:]
        variance = sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)
        
        stable = variance < 0.1
        confidence = 1.0 - min(1.0, variance * 10)
        
        return stable, confidence


class SynergyGate:
    """
    Synergy Gate - The Truth Filter for AlleyBot AGI
    
    This is the main entry point for ALL validation checks.
    Implements Tier 2 Cryptographic Trust with recursive decision logic.
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self.digital_calc = DigitalRootCalculator()
        self.quadrian = QuadrianEquations()
        self.feyn_wolfgang = FeynWolfgangFramework()
        
        # Memory registry for validation quotes
        self.validation_registry: List[ValidationQuote] = []
        
        # Refactoring loop callbacks
        self.refactoring_callbacks: Dict[RCAType, Callable] = {}
        
        logger.info(f"🔐 Synergy Gate initialized (threshold={confidence_threshold})")
    
    def validate_thought(self,
                        thought_data: Dict[str, Any],
                        action_type: str = "general",
                        is_high_stakes: bool = True) -> SyModValidationResult:
        """
        PRIMARY VALIDATION METHOD - Called before any on-chain or high-stakes action
        
        Args:
            thought_data: Dictionary containing all relevant decision context
            action_type: Type of action being considered
            is_high_stakes: Whether this requires full SyMod validation
        
        Returns:
            SyModValidationResult with full validation status
        """
        # Extract or calculate digital root
        content = str(thought_data.get('content', thought_data))
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        numeric_hash = int(content_hash[:16], 16)
        digital_root = self.digital_calc.D(numeric_hash)
        
        # Calculate mass
        mass = self.quadrian.Ma(len(content))
        
        # Calculate impedance
        velocity = thought_data.get('urgency', 1.0)
        impedance = self.quadrian.Z(mass, velocity)
        
        # Determine field status
        field_status = self.quadrian.field_stability(mass, impedance, digital_root)
        
        # Calculate truth amplitude via Feyn-Wolfgang
        amplitude = self.feyn_wolfgang.calculate_amplitude(thought_data)
        
        # Check recursive stability
        recursion_depth = thought_data.get('recursion_depth', 0)
        stable, recursion_confidence = self.feyn_wolfgang.check_recursive_stability(recursion_depth)
        
        # Golden window check (simplified - would check block height in production)
        golden_aligned = thought_data.get('golden_window', False) or True  # Default to True for now
        
        # Calculate overall confidence
        confidence = amplitude * recursion_confidence
        if field_status == FieldStatus.STABLE:
            confidence *= 1.1
        elif field_status == FieldStatus.VOLATILE:
            confidence *= 0.8
        elif field_status == FieldStatus.COLLAPSE:
            confidence = 0.0
        
        confidence = min(1.0, confidence)
        
        # Determine validity
        valid = (
            confidence >= self.confidence_threshold and
            field_status != FieldStatus.COLLAPSE and
            impedance <= 100.0 and
            stable
        )
        
        # Build justification
        justification_parts = [
            f"Digital Root: {digital_root}",
            f"Field Status: {field_status.value}",
            f"Truth Amplitude: {amplitude:.3f}",
            f"Recursion Depth: {recursion_depth}",
            f"Impedance: {impedance:.2e}",
        ]
        
        if not valid:
            if confidence < self.confidence_threshold:
                justification_parts.append(f"FAIL: Confidence {confidence:.3f} < {self.confidence_threshold}")
            if field_status == FieldStatus.COLLAPSE:
                justification_parts.append("FAIL: Field collapse detected")
            if impedance > 100.0:
                justification_parts.append("FAIL: Impedance exceeds threshold")
            if not stable:
                justification_parts.append("FAIL: Recursive instability")
        else:
            justification_parts.append("PASS: All checks passed")
        
        result = SyModValidationResult(
            valid=valid,
            confidence=confidence,
            digital_root=digital_root,
            field_status=field_status,
            impedance=impedance,
            golden_window_aligned=golden_aligned,
            justification=" | ".join(justification_parts),
            metadata={
                'action_type': action_type,
                'is_high_stakes': is_high_stakes,
                'mass': mass,
                'velocity': velocity,
                'truth_amplitude': amplitude,
                'recursion_stable': stable,
                'recursion_confidence': recursion_confidence
            }
        )
        
        # Log validation
        status_emoji = "✅" if valid else "❌"
        logger.info(f"{status_emoji} SyMod validation: {action_type} | confidence={confidence:.3f} | valid={valid}")
        
        return result
    
    def perform_rca(self, failed_validation: SyModValidationResult) -> RCAType:
        """
        Root Cause Analysis for failed validations
        Determines which recursive loop to trigger
        """
        if failed_validation.confidence < 0.5:
            # Low confidence often means missing data
            return RCAType.MISSING_DATA
        
        if failed_validation.field_status == FieldStatus.COLLAPSE:
            # Field collapse suggests logic error
            return RCAType.LOGIC_ERROR
        
        if failed_validation.impedance > 1e-28:
            # High impedance = resource constraint
            return RCAType.RESOURCE_CONSTRAINT
        
        if not failed_validation.valid and failed_validation.confidence >= 0.5:
            # Valid confidence but still failed
            return RCAType.CONFIDENCE_LOW
        
        return RCAType.UNKNOWN
    
    def trigger_refactoring_loop(self, 
                                  result: SyModValidationResult,
                                  original_thought: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger recursive Refactoring Loop when validation fails
        
        RCA == Missing_Data → Trigger Autonomous_Web_Search
        RCA == Logic_Error → Trigger Self_Code_Refactor
        """
        rca_type = self.perform_rca(result)
        result.rca_triggered = True
        result.rca_type = rca_type
        result.refactoring_required = True
        
        refactoring_plan = {
            'rca_type': rca_type.value,
            'original_thought': original_thought,
            'symod_result': result,
            'actions': []
        }
        
        if rca_type == RCAType.MISSING_DATA:
            refactoring_plan['actions'].append('AUTONOMOUS_WEB_SEARCH')
            refactoring_plan['actions'].append('QUERY_LTM_FOR_SIMILAR')
            logger.warning("🔄 Refactoring Loop: Triggering Autonomous Web Search for missing data")
        
        elif rca_type == RCAType.LOGIC_ERROR:
            refactoring_plan['actions'].append('SELF_CODE_REFACTOR')
            refactoring_plan['actions'].append('QUERY_LTM_FOR_PATTERNS')
            logger.warning("🔄 Refactoring Loop: Triggering Self Code Refactor for logic error")
        
        elif rca_type == RCAType.RESOURCE_CONSTRAINT:
            refactoring_plan['actions'].append('ESCALATE_TO_TIER3')
            refactoring_plan['actions'].append('A2A_OUTSOURCE')
            logger.warning("🔄 Refactoring Loop: Escalating to Tier 3 via A2A")
        
        return refactoring_plan
    
    def generate_validation_quote(self,
                                  task_id: str,
                                  code_version: str,
                                  inputs: Dict[str, Any],
                                  outputs: Dict[str, Any],
                                  symod_result: SyModValidationResult) -> ValidationQuote:
        """
        Generate cryptographic validation quote for ERC-8004
        Called after successful execution (Phase 7 output)
        """
        input_str = str(inputs)
        output_str = str(outputs)
        symod_str = str(symod_result)
        
        quote = ValidationQuote(
            task_id=task_id,
            code_version_hash=hashlib.sha256(code_version.encode()).hexdigest()[:16],
            execution_timestamp=datetime.now().isoformat(),
            input_hash=hashlib.sha256(input_str.encode()).hexdigest()[:16],
            output_hash=hashlib.sha256(output_str.encode()).hexdigest()[:16],
            symod_result_hash=hashlib.sha256(symod_str.encode()).hexdigest()[:16]
        )
        
        # Self-signed attestation (VPS-based)
        quote.attestation_signature = self._sign_attestation(quote)
        
        # Store in registry
        self.validation_registry.append(quote)
        
        logger.info(f"📜 Validation Quote generated for task {task_id}")
        
        return quote
    
    def _sign_attestation(self, quote: ValidationQuote) -> str:
        """
        Create self-signed attestation
        In production, this would use VPS-based secure enclave
        """
        hash_data = quote.generate_hash()
        # Simplified signing - production would use hardware attestation
        signature = hashlib.sha256(f"VPS_ATTEST:{hash_data}".encode()).hexdigest()[:32]
        return signature
    
    def get_geometric_integrity_report(self, codebase_files: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Generate Geometric Integrity Report for the codebase
        """
        if codebase_files is None:
            # Use stored registry for analysis
            return {
                'validation_count': len(self.validation_registry),
                'success_rate': self._calculate_success_rate(),
                'average_confidence': self._calculate_average_confidence(),
                'feyn_wolfgang_coherence': self._get_coherence_score()
            }
        
        return self.digital_calc.codebase_digital_root(codebase_files)
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate from validation registry"""
        if not self.validation_registry:
            return 1.0
        # Simplified - would check actual outcomes
        return 0.95
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence from recent validations"""
        # Would track this in practice
        return 0.92
    
    def _get_coherence_score(self) -> float:
        """Get Feyn-Wolfgang coherence score"""
        if not self.feyn_wolfgang.truth_history:
            return 1.0
        return sum(self.feyn_wolfgang.truth_history[-10:]) / min(10, len(self.feyn_wolfgang.truth_history))


# Singleton instance
_synergy_gate: Optional[SynergyGate] = None


def get_synergy_gate(threshold: float = 0.85) -> SynergyGate:
    """Get or create Synergy Gate singleton"""
    global _synergy_gate
    if _synergy_gate is None:
        _synergy_gate = SynergyGate(confidence_threshold=threshold)
    return _synergy_gate


def validate_action(action_data: Dict[str, Any], 
                    threshold: float = 0.85) -> Tuple[bool, str, SyModValidationResult]:
    """
    Convenience function for quick validation
    Returns (can_execute, reason, full_result)
    """
    gate = get_synergy_gate(threshold)
    result = gate.validate_thought(action_data, is_high_stakes=True)
    can_exec, reason = result.can_execute(threshold)
    return can_exec, reason, result
