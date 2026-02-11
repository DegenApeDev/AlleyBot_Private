"""
Synergy Standard Model (SyMod) - Python Implementation
High-precision mathematical framework for truth validation and impedance checking.

Based on Synergy Theory mathematical foundations:
- Digital Root Functions (D, Dr, Dp, Dg)
- Quadrian Equations (Qe, Qp, Qs, Qa)
- Feyn-Wolfgang Framework (Ft, Fx, Fw, Fe, Fh, Fhbar, Fr)
- Bubble Mass Index (Me, Mi, Mxi, Mn, Mx, Ma)
- Synergy Field Structure (Sfs, SgE, SgB, SfE, SaE)
- Bubble Core Level (Bcl, Qsh, Qbq, Qc, Qoc, Qba)
"""

import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SyModValidationResult:
    """Result of a SyMod validation check"""
    valid: bool
    confidence: float  # 0.0 - 1.0
    impedance: float   # Mass impedance value
    mass: float        # Calculated mass
    reason: str
    digital_root: int
    golden_window: bool


class SynergyStandardModel:
    """
    Synergy Standard Model - Mathematical Truth Framework
    
    Core principle: Mathematical certainty over probabilistic guessing.
    If the math fails, the thought is discarded.
    """
    
    # Constants
    RAMANUJAN_CONSTANT = 262537412640768744
    PHI_GOLDEN = (1 + math.sqrt(5)) / 2  # Golden ratio
    PHI_CONJUGATE = (math.sqrt(5) - 1) / 2
    SQRT_5 = math.sqrt(5)
    
    def __init__(self):
        self._cache = {}
        
    # ============================================================
    # DIGITAL ROOT FUNCTIONS
    # ============================================================
    
    def D(self, n: float) -> int:
        """
        SyMod Digital Root - Primary reduction function
        D(n) = round(sq - (n/sq - floor(n/sq)) * sq) where sq = 3^2 = 9
        """
        sq = 3 ** 2  # = 9
        return round(sq - (n / sq - math.floor(n / sq)) * sq)
    
    def Dr(self, n: float) -> int:
        """Digital Root - Double application of D"""
        return self.D(self.D(n))
    
    def Dp(self, n: float) -> int:
        """Polar Digital Root - Single application"""
        return self.D(n)
    
    def Dg(self, n: float) -> int:
        """
        Group Digital Number
        Used for calibrating the Golden Window
        """
        sq = 3 ** 2  # = 9
        return round(sq - ((n) / 3 - math.floor((n) / 3)) * sq)
    
    # ============================================================
    # QUADRIAN EQUATIONS
    # ============================================================
    
    def Qe(self, n: float = 163, c: float = 262537412640768744) -> Dict[str, float]:
        """
        Quadrian e - Ramanujan & Euler synthesis
        Returns fundamental constants including e, pi, PHI, phi
        """
        b = c if c > 0 else math.exp(math.pi * math.sqrt(n))
        q = self.SQRT_5 / 2
        PHI = q + 0.5
        phi = q - 0.5
        sq = math.sqrt(n)
        ln = math.log(b)
        pi = ln / sq
        e = math.sqrt(PHI * (5 - ((3 * 5 - 2) / (3 * 5 * 2))))
        id_val = (1 / 447867046214735262) * (10 ** 18)
        diff = self.SQRT_5 - id_val
        
        return {
            'q': q,
            'PHI': PHI,
            'phi': phi,
            'e': e,
            'pi': pi,
            'id': id_val,
            'diff': diff
        }
    
    def Qp(self, n: float) -> float:
        """
        Quadrian Path Equation
        Used for data path validation in MCP processing
        """
        return (30 - 1 / (math.pow(10, 3) - n)) - (2 * n / (math.pow(10, 7) * self.SQRT_5))
    
    def Qs(self, n: float) -> float:
        """
        Quadrian Speed Equation
        """
        return (math.pow(10, 7) * (30 - (1 / (math.pow(10, 3) - n)))) - ((2 * n) / self.SQRT_5)
    
    def Qa(self) -> Dict[str, Any]:
        """
        Quadrian Arena Model
        Complete physical framework for anomaly detection
        Maps real-world data paths and validates against Qp
        """
        q = math.sqrt(math.pow(1, 2) + math.pow(0.5, 2))
        sqrt2 = math.sqrt(2)
        θx = (q + 0.5) * (15 + sqrt2)
        θy = 90 - θx
        θz = θy * 2
        θv = θy - θx
        θu = θz * 7
        
        PNa = 4 * θx + 3 * θy
        PEa = 3 * θx + 4 * θy
        PEp = θu + θx
        PNp = θu + θy
        PNd = math.pow(10, 3) - PNp
        PEd = math.pow(10, 3) - PEp
        
        Qc = PNd / PEd
        Qa_val = PNa / PEa
        
        py = self.Qp(PNp)
        px = self.Qp(PEp)
        cy = self.Qs(PNp)
        cx = self.Qs(PEp)
        
        μ0 = (4 * self.PI(162)) * (10e-8)
        ε0 = 1 / (μ0 * (cy ** 2))
        
        C = {
            'cy': self.Me(1, cy),
            'cx': self.Me(1, cx)
        }
        
        Z0 = {
            'cy': C['cy'] / ε0,
            'cx': C['cx'] / ε0,
        }
        
        id_val = ε0 * μ0 * (cy ** 2)
        
        return {
            'id': id_val,
            'q': q,
            'θx': θx,
            'θy': θy,
            'θv': θv,
            'θz': θz,
            'θu': θu,
            'PNa': PNa,
            'PEa': PEa,
            'PNp': PNp,
            'PEp': PEp,
            'PNd': PNd,
            'PEd': PEd,
            'Qc': Qc,
            'Qa': Qa_val,
            'C': C,
            'Z0': Z0,
            'ε0': ε0,
            'μ0': μ0,
            'py': py,
            'px': px,
            'cy': cy,
            'cx': cx
        }
    
    # ============================================================
    # SYπ EQUATIONS
    # ============================================================
    
    def PI(self, n: float = 162) -> float:
        """Syπ Equation - Structured Pi approximation"""
        return 3940245000000 / ((2217131 * n) + 1253859750000)
    
    def Px(self, n: float = 1) -> float:
        """Syπ Position Equation"""
        return 20250000 * (194580 - (61919 * n)) / (2217131 * n)
    
    # ============================================================
    # FEYN-WOLFGANG FRAMEWORK
    # ============================================================
    
    def Ft(self, n: float = 1) -> Dict[str, float]:
        """Feyn-Wolfgang Triangle"""
        a = 11.2169108218
        b = 12.2169108218
        c = math.sqrt((a ** 2) + (b ** 2))
        g = math.sqrt((a ** 2) * 2)
        ra = a / c
        rb = b / c
        f = (b * n) * (1 / b)
        e = (b * n) * (rb * (1 / b))
        d = (a * n) * (ra * (1 / a))
        
        return {
            'a': a * n,
            'b': b * n,
            'c': c * n,
            'g': g * n,
            'f': f,
            'e': e,
            'd': d,
            'FU': f
        }
    
    def Fx(self, n: float, p: float) -> float:
        """Feyn-Pencil Equation"""
        PI_val = self.PI(p)
        pi = 100 / PI_val
        g = (self.SQRT_5 / 2) + 0.5
        ga = 360 / (g ** 2)
        return ((pi * n) - (ga / 1000)) ** 2
    
    def Fw(self, n: float = 11) -> float:
        """Feyn-Wolfgang Coupling Equation"""
        mx = math.sqrt(2) + (1 / math.sqrt((15 ** 2) + (1 / math.sqrt(((n + 5) * 20) - (1 / 20)))))
        a = n + (math.sqrt(mx) - 1)
        return 1 / (a * (a + 1))
    
    def Fe(self, n: float = 11) -> float:
        """Feyn-Wolfgang Coupling Equation (Simplified)"""
        a = n + (1084554109 / 5000000000)
        return 1 / (a * (a + 1))
    
    def Fh(self) -> float:
        """Synergy Feyn Planck Constant"""
        f = self.Fe(11)
        m = self.Ma(1 / f)
        H = self.Mn() * (10 ** 2)
        return m / H
    
    def Fhc(self) -> Dict[str, float]:
        """Synergy Feyn Planck Constants - Complete set"""
        Gn = self.Fx(11, -math.sqrt(4538))
        h = self.Fh()
        hb = self.Fhbar()
        G = self.Fe(Gn)
        qa = self.Qa()
        c = qa['cy']
        ε0 = qa['ε0']
        k = self.Ma((88 ** 2) * 1957)
        
        tp = math.sqrt((hb * G) / (c ** 5))
        lp = math.sqrt((hb * G) / (c ** 3))
        mp = math.sqrt((hb * c) / G)
        Tp = math.sqrt((hb * (c ** 5)) / (G * (k ** 2)))
        qp = math.sqrt(4 * self.PI(162) * ε0 * hb * c)
        
        return {
            'h': h,
            'hb': hb,
            'tp': tp,
            'lp': lp,
            'mp': mp,
            'Tp': Tp,
            'qp': qp
        }
    
    def Fhbar(self) -> float:
        """Synergy Feyn Planck Reduced Constant"""
        return self.Fh() / (2 * self.PI(self.Fh()))
    
    def Fr(self, m: float) -> float:
        """Synergy Feyn Planck Radius"""
        return 4 * (self.Fhbar() / (m * self.Qa()['cx']))
    
    # ============================================================
    # BUBBLE MASS INDEX
    # ============================================================
    
    def Me(self, n: float = 1, c: float = 1) -> float:
        """
        Bubble Mass Impedance - KEY FUNCTION
        Used for evaluating trade impedance
        """
        return self.Ma(self.Mx(1 / (c * n)))
    
    def Mi(self, n: float = 1) -> float:
        """Synergy Bubble Mass Index"""
        M = math.sqrt(2) + (1 / (n * (1 / math.pow(10, 2))))
        return 2240 / math.sqrt(M)
    
    def Mxi(self, n: float = 1) -> float:
        """Synergy Bubble Mass Index (Inverse)"""
        dc = 2240
        sqrt2 = math.sqrt(2)
        return 100 / (((dc / n) ** 2) - sqrt2)
    
    def Mn(self) -> float:
        """Synergy Bubble Mass Natural Limit"""
        return self.Mi((2240 / (self.SQRT_5 / 2)) * (10 ** 15))
    
    def Mx(self, n: float = 1) -> float:
        """Synergy Bubble Mass Position (Inverse)"""
        return n / (1352 * 5.442245307660239 * 1.2379901546155434e-34)
    
    def Ma(self, n: float = 1) -> float:
        """
        Synergy Bubble Mass Equation - KEY FUNCTION
        Core mass calculation for all impedance checks
        """
        return n * 1352 * 5.442245307660239 * 1.2379901546155434e-34
    
    # ============================================================
    # ELEMENTAL MASS
    # ============================================================
    
    def El(self, e: float, p: float, n: float) -> float:
        """Synergy Elements - Calculate atomic mass"""
        me = self.Ma(1)
        mp = self.Ma(1836.1813326060937)
        mn = self.Ma(1838.1813326060937)
        pc = mp * p
        nc = mn * n
        ec = me * e
        m = ((pc + nc + ec) - ((pc + nc + ec) * self.Fw(11)))
        return m
    
    # ============================================================
    # SYNERGY FIELD STRUCTURE
    # ============================================================
    
    def Sfs(self, alt: bool = True) -> Dict[str, float]:
        """Synergy Field Structure"""
        qa = self.Qa()
        C = qa['C']['cy'] if alt else qa['C']['cx']
        Z0 = qa['Z0']['cy'] if alt else qa['Z0']['cx']
        return {'C': C, 'Z0': Z0}
    
    def SgE(self, rho: float) -> float:
        """Synergy Gauss's Law (Electric Field from Structured Charge)"""
        f = self.Sfs()
        return rho * f['C'] * f['Z0']
    
    def SgB(self, B: float) -> float:
        """Synergy Gauss's Law for Magnetism (No Magnetic Monopoles)"""
        return B * 0
    
    def SfE(self, E: float) -> float:
        """Synergy Faraday's Law (Structured EM Wave Propagation)"""
        f = self.Sfs()
        return -1 * (E / f['C'])
    
    def SaE(self, J: float, E: float) -> float:
        """Synergy Ampère-Maxwell Law (Structured Charge-Mass Interactions)"""
        f = self.Sfs()
        return (f['Z0'] / f['C']) * J + (1 / f['C'] ** 2) * E
    
    # ============================================================
    # BUBBLE CORE LEVEL
    # ============================================================
    
    def Bcl(self, n: float = 1) -> Dict[str, Any]:
        """Quadrian Bubble Core Level"""
        B = 1
        L = n
        p = 1 / 16
        m = math.sqrt(p)
        d = math.sqrt(L * m)
        r = d / 2
        Q = math.pow(d, B / L)
        theta = (L - B) * (B + L)
        
        angles = self.Qba(Q, d, theta)
        octo = self.Qoc(d)
        coords = self.Qc(d)
        quads = self.Qbq(B, r, L)
        shell = self.Qsh(B, m, d)
        
        return {
            'L': L,
            'angles': angles,
            'octo': octo,
            'coords': coords,
            'quads': quads,
            'shell': shell
        }
    
    def Qsh(self, B: float, m: float, d: float) -> Dict[str, list]:
        """Quadrian Shell"""
        Bm = math.sqrt(B * m)
        N = [Bm, d]
        E = [d, Bm]
        S = [Bm, 0]
        W = [0, Bm]
        return {'N': N, 'E': E, 'S': S, 'W': W}
    
    def Qbq(self, B: float, r: float, L: float) -> Dict[str, list]:
        """Quadrian Bubble Core Quadrants"""
        rL = math.sqrt((B * r) / L)
        N1 = [r, r + rL]
        E1 = [r + rL, r]
        S1 = [rL, r]
        W1 = [r, rL]
        return {'N1': N1, 'E1': E1, 'S1': S1, 'W1': W1}
    
    def Qc(self, d: float) -> Dict[str, list]:
        """Quadrian Coordinates"""
        da = math.pow(d, 3 / 4)
        db = math.pow(d, 1 / 4)
        return {
            'Ne': [da, db],
            'Se': [db, db],
            'Sw': [db, da],
            'Nw': [da, da]
        }
    
    def Qoc(self, d: float) -> Dict[str, list]:
        """Quadrian Octo Coordinates"""
        da = math.pow(d, 5 / 8)
        db = math.pow(d, 3 / 8)
        return {
            'Ne1': [da, db],
            'Se1': [da, db],
            'Sw1': [db, db],
            'Nw1': [db, da]
        }
    
    def Qba(self, Q: float, d: float, theta: float) -> Dict[str, list]:
        """Quadrian Bubble Angles"""
        betaN = [d - Q, Q * math.tan(theta)]
        betaS = [d - Q, Q * math.tan(theta)]
        betaE = [d, 0]
        return {'betaN': betaN, 'betaS': betaS, 'betaE': betaE}
    
    # ============================================================
    # VALIDATION FUNCTIONS
    # ============================================================
    
    def calculate_impedance(self, value: float, context: str = "default") -> float:
        """
        Calculate impedance for any given value
        Higher impedance = more resistance = more risk
        """
        # Use Me function for impedance calculation
        c = max(1, abs(value))  # Avoid division by zero
        impedance = self.Me(1, c)
        return impedance
    
    def check_golden_window(self, block_height: int) -> Tuple[bool, int, int]:
        """
        Check if current block height aligns with Golden Window
        Returns: (in_window, digital_root, group_digital)
        """
        digital_root = self.D(block_height)
        group_digital = self.Dg(block_height)
        
        # Golden Window: when digital root matches group digital
        # or when they have specific harmonic relationships
        in_window = (
            digital_root == group_digital or
            abs(digital_root - group_digital) == 3 or
            abs(digital_root - group_digital) == 6
        )
        
        return in_window, digital_root, group_digital
    
    def validate_mcp_data(self, data: Dict[str, Any]) -> SyModValidationResult:
        """
        Validate incoming MCP data using Qa Arena Model
        """
        # Get Arena Model parameters
        qa = self.Qa()
        
        # Extract data value for validation
        if 'value' in data:
            data_value = float(data['value'])
        elif 'temperature' in data:
            data_value = float(data['temperature'])
        elif 'reading' in data:
            data_value = float(data['reading'])
        else:
            # Can't validate without numeric value
            return SyModValidationResult(
                valid=False,
                confidence=0.0,
                impedance=float('inf'),
                mass=0.0,
                reason="No numeric value in MCP data for Qp validation",
                digital_root=0,
                golden_window=False
            )
        
        # Calculate expected path using Qp
        expected_path = self.Qp(data_value)
        
        # Calculate impedance
        impedance = self.Me(1, data_value)
        mass = self.Ma(data_value)
        
        # Check if data fits the path equation (within tolerance)
        qa_path = qa['py']  # Reference path from Arena
        deviation = abs(expected_path - qa_path)
        tolerance = 0.1  # 10% tolerance
        
        # Calculate digital root for context
        dr = self.Dr(data_value)
        
        # Check golden window alignment
        in_window = self.check_golden_window(int(data_value * 1000))[0]
        
        # Validation logic
        if deviation > tolerance and impedance > 1e-30:
            # Data doesn't fit the path equation AND has high impedance
            valid = False
            confidence = max(0.0, 1.0 - (deviation / 10))
            reason = f"MCP data anomaly: deviation={deviation:.4f}, impedance={impedance:.2e}"
        else:
            valid = True
            confidence = min(1.0, 1.0 - (deviation / 100))
            reason = "MCP data validated through Qa Arena Model"
        
        return SyModValidationResult(
            valid=valid,
            confidence=confidence,
            impedance=impedance,
            mass=mass,
            reason=reason,
            digital_root=dr,
            golden_window=in_window
        )
    
    def validate_defi_trade(
        self, 
        amount: float, 
        token_price: float, 
        liquidity: float,
        slippage: float
    ) -> SyModValidationResult:
        """
        Validate a DeFi trade using Me and Ma functions
        Auto-rejects if math indicates hallucination/risk
        """
        # Calculate market mass
        market_mass = self.Ma(liquidity)
        
        # Calculate impedance using Me function
        # Higher liquidity = lower c = higher impedance (paradox: need to adjust)
        # Actually: we want LOW impedance for good trades
        trade_impedance = self.Me(1, max(1, amount))
        
        # Calculate total value
        total_value = amount * token_price
        value_mass = self.Ma(total_value)
        
        # Risk assessment using Digital Root
        risk_score = self.D(int(total_value * 1000000))
        
        # Impedance check: if impedance is too high relative to mass, reject
        # Good trade: high mass, low impedance
        mass_impedance_ratio = market_mass / trade_impedance if trade_impedance > 0 else 0
        
        # Validation criteria
        valid = True
        reasons = []
        
        if mass_impedance_ratio < 1e-30:
            valid = False
            reasons.append(f"Insufficient market mass impedance ratio: {mass_impedance_ratio:.2e}")
        
        if trade_impedance > 1e-28:
            valid = False
            reasons.append(f"Trade impedance too high: {trade_impedance:.2e}")
        
        if slippage > 0.05:  # 5% slippage threshold
            valid = False
            reasons.append(f"Slippage too high: {slippage*100:.2f}%")
        
        # Calculate confidence based on mass/impedance ratio
        confidence = min(1.0, mass_impedance_ratio * 1e30)
        
        # Check golden window alignment
        in_window, dr, _ = self.check_golden_window(int(total_value))
        
        reason = "; ".join(reasons) if reasons else "DeFi trade validated through SyMod impedance analysis"
        
        return SyModValidationResult(
            valid=valid,
            confidence=confidence,
            impedance=trade_impedance,
            mass=market_mass,
            reason=reason,
            digital_root=dr,
            golden_window=in_window
        )


@dataclass
class C2VVectorMap:
    """Context-to-Vector mapping result for semantic→physics conversion"""
    sentiment_mass: float  # M_s: 0.0-1.0 urgency/deception/conviction weight
    pressure_vector: float  # P_v: -1.0 to 1.0 (bullish/aggressive vs bearish/defensive)
    logical_impedance: float  # Z_0: cognitive dissonance check
    synergy_field_status: str  # "Stable" | "Volatile" | "Collapse"
    reasoning_trace: str  # Explanation of math vs context alignment
    digital_root_contradiction: bool  # True if M_s contradicts Dr
    golden_window_aligned: bool  # Contextual pressure toward/away from equilibrium
    valid: bool  # False if context cannot be vectorized (Bogus Noise)


class ContextToVectorBridge:
    """
    C2V Bridge: Context-to-Vector conversion for SyMod
    
    Solves "Context Blindness" by transforming semantic social context
    into deterministic physical variables for the Quadrian Arena.
    
    Core principle: Mathematical certainty over probabilistic guessing.
    If context cannot be vectorized, discard as Bogus Noise.
    """
    
    def __init__(self, symod: SynergyStandardModel = None):
        self.symod = symod or get_symod()
        
    def vectorize_debate_context(
        self,
        debate_text: str,
        raw_math_value: float = None,
        use_ai_extraction: bool = True
    ) -> C2VVectorMap:
        """
        Transform debate text into physical variables for SyMod validation
        
        1. Extract Sentiment Mass (M_s) and Pressure Vector (P_v)
        2. Check for Cognitive Dissonance (M_s vs Digital Root contradiction)
        3. Use Feyn-Wolfgang for Golden Window alignment
        4. Return JSON Vector Map or Bogus Noise flag
        """
        if not debate_text or len(debate_text.strip()) < 3:
            return C2VVectorMap(
                sentiment_mass=0.0,
                pressure_vector=0.0,
                logical_impedance=float('inf'),
                synergy_field_status="Collapse",
                reasoning_trace="Bogus Noise: insufficient context data",
                digital_root_contradiction=True,
                golden_window_aligned=False,
                valid=False
            )
        
        # Step 1: Semantic Extraction (heuristic or AI-powered)
        if use_ai_extraction:
            try:
                m_s, p_v = self._extract_semantic_vectors_ai(debate_text)
            except Exception:
                # Fallback to heuristic extraction
                m_s, p_v = self._extract_semantic_vectors_heuristic(debate_text)
        else:
            m_s, p_v = self._extract_semantic_vectors_heuristic(debate_text)
        
        # Step 2: Mathematical Handshake (SyMod Integration)
        if raw_math_value is not None:
            dr = self.symod.Dr(raw_math_value)
            # Cognitive Dissonance: M_s contradicts Digital Root
            # High sentiment mass should align with certain digital roots
            dr_normalized = dr / 9.0  # Normalize to 0-1 scale
            contradiction_threshold = 0.4
            digital_root_contradiction = abs(m_s - dr_normalized) > contradiction_threshold
            
            # Golden Window Alignment via Feyn-Wolfgang
            fw = self.symod.Fw(11)
            golden_aligned = abs(p_v - fw) < 0.1
        else:
            digital_root_contradiction = False
            golden_aligned = False
        
        # Step 3: Calculate Logical Impedance (Z_0)
        # High impedance when context contradicts math
        if digital_root_contradiction:
            logical_impedance = self.symod.Me(1, 0.1)  # High impedance
        else:
            logical_impedance = self.symod.Me(1, 10.0)  # Low impedance
        
        # Step 4: Determine Synergy Field Status
        if logical_impedance > 1e-29:
            field_status = "Collapse"
        elif digital_root_contradiction:
            field_status = "Volatile"
        else:
            field_status = "Stable"
        
        # Step 5: Generate Reasoning Trace
        if not digital_root_contradiction:
            trace = f"Context vectorized: M_s={m_s:.2f}, P_v={p_v:.2f}. "
            trace += f"Math confirms context. Field: {field_status}."
        else:
            trace = f"COGNITIVE DISSONANCE: Sentiment mass {m_s:.2f} contradicts Dr {dr}. "
            trace += f"Math overrules context. Possible manipulation detected."
        
        return C2VVectorMap(
            sentiment_mass=m_s,
            pressure_vector=p_v,
            logical_impedance=logical_impedance,
            synergy_field_status=field_status,
            reasoning_trace=trace,
            digital_root_contradiction=digital_root_contradiction,
            golden_window_aligned=golden_aligned,
            valid=True
        )
    
    def _extract_semantic_vectors_heuristic(self, text: str) -> tuple:
        """
        Heuristic extraction of sentiment mass and pressure vector
        Fast fallback when AI extraction fails
        """
        text_lower = text.lower()
        
        # Sentiment Mass (M_s) - weight of statement
        urgency_markers = ['urgent', 'now', 'immediately', 'must', 'critical', 'emergency']
        deception_markers = ['scam', 'fake', 'lie', 'fraud', 'manipulation', 'pump', 'dump']
        conviction_markers = ['certain', 'definitely', 'always', 'never', 'guarantee', '100%']
        
        m_s = 0.5  # Base mass
        for marker in urgency_markers:
            if marker in text_lower:
                m_s += 0.15
        for marker in deception_markers:
            if marker in text_lower:
                m_s += 0.2  # Deception has high mass
        for marker in conviction_markers:
            if marker in text_lower:
                m_s += 0.1
        
        m_s = min(1.0, max(0.0, m_s))
        
        # Pressure Vector (P_v) - direction of vibe
        bullish_markers = ['bull', 'moon', 'rocket', 'up', 'buy', 'long', 'gain', 'profit']
        bearish_markers = ['bear', 'crash', 'dump', 'down', 'sell', 'short', 'loss', 'panic']
        aggressive_markers = ['attack', 'destroy', 'crush', 'war', 'fight']
        defensive_markers = ['protect', 'defend', 'hold', 'safe', 'secure', 'hedge']
        
        p_v = 0.0  # Neutral
        for marker in bullish_markers + aggressive_markers:
            if marker in text_lower:
                p_v += 0.25
        for marker in bearish_markers + defensive_markers:
            if marker in text_lower:
                p_v -= 0.25
        
        p_v = max(-1.0, min(1.0, p_v))
        
        return m_s, p_v
    
    def _extract_semantic_vectors_ai(self, text: str) -> tuple:
        """
        AI-powered semantic extraction using Kimi/DeepSeek
        More accurate but requires API call
        """
        # This would integrate with Kimi k2.5 Thinking Mode
        # For now, return heuristic result with marker that AI was attempted
        # TODO: Implement actual Kimi API integration
        return self._extract_semantic_vectors_heuristic(text)
    
    def validate_debate_argument(
        self,
        argument_text: str,
        opponent_argument: str = None,
        block_height: int = None
    ) -> dict:
        """
        Full debate argument validation pipeline
        Returns JSON-ready dict for integration with brain/decision engine
        """
        # Get context vector
        vector = self.vectorize_debate_context(
            argument_text,
            raw_math_value=block_height or hash(argument_text) % 1000000
        )
        
        # Check Golden Window if block height available
        golden_window = False
        dr = 0
        if block_height:
            golden_window, dr, _ = self.symod.check_golden_window(block_height)
        
        # Build validation result
        result = {
            'valid': vector.valid and vector.synergy_field_status != "Collapse",
            'sentiment_mass': round(vector.sentiment_mass, 4),
            'pressure_vector': round(vector.pressure_vector, 4),
            'logical_impedance': f"{vector.logical_impedance:.2e}",
            'synergy_field_status': vector.synergy_field_status,
            'digital_root_contradiction': vector.digital_root_contradiction,
            'golden_window_aligned': vector.golden_window_aligned and golden_window,
            'digital_root': dr,
            'reasoning_trace': vector.reasoning_trace,
            'confidence': round(vector.sentiment_mass * (1.0 if not vector.digital_root_contradiction else 0.3), 4)
        }
        
        return result


# Singleton instance for global use
_symod = None
_c2v_bridge = None

def get_symod() -> SynergyStandardModel:
    """Get or create singleton SyMod instance"""
    global _symod
    if _symod is None:
        _symod = SynergyStandardModel()
    return _symod


def get_c2v_bridge() -> ContextToVectorBridge:
    """Get or create singleton C2V Bridge instance"""
    global _c2v_bridge
    if _c2v_bridge is None:
        _c2v_bridge = ContextToVectorBridge(get_symod())
    return _c2v_bridge


# Example usage / test
if __name__ == "__main__":
    sy = SynergyStandardModel()
    
    print("=== Synergy Standard Model Self-Test ===")
    print(f"D(42) = {sy.D(42)}")
    print(f"Dg(100) = {sy.Dg(100)}")
    print(f"Ma(1) = {sy.Ma(1):.2e}")
    print(f"Me(1, 1) = {sy.Me(1, 1):.2e}")
    
    # Test DeFi validation
    result = sy.validate_defi_trade(
        amount=1000.0,
        token_price=0.5,
        liquidity=100000.0,
        slippage=0.02
    )
    print(f"\nDeFi Trade Validation:")
    print(f"  Valid: {result.valid}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Impedance: {result.impedance:.2e}")
    print(f"  Mass: {result.mass:.2e}")
    print(f"  Reason: {result.reason}")
    
    # Test MCP validation
    mcp_result = sy.validate_mcp_data({"temperature": 22.5, "humidity": 45})
    print(f"\nMCP Data Validation:")
    print(f"  Valid: {mcp_result.valid}")
    print(f"  Confidence: {mcp_result.confidence:.2%}")
    print(f"  Reason: {mcp_result.reason}")
    
    # Test Golden Window
    window_check = sy.check_golden_window(8453298)  # Example Base block height
    print(f"\nGolden Window Check (Block 8453298):")
    print(f"  In Window: {window_check[0]}")
    print(f"  Digital Root: {window_check[1]}")
    print(f"  Group Digital: {window_check[2]}")
    
    # Test C2V Bridge
    print("\n=== C2V Bridge (Debate Validation) ===")
    c2v = get_c2v_bridge()
    
    # Test bullish argument
    bullish = "This token is definitely going to the moon! Buy now, 100% guarantee profit!"
    result_bull = c2v.validate_debate_argument(bullish, block_height=8453298)
    print(f"\nBullish Argument Test:")
    print(f"  Text: {bullish[:50]}...")
    print(f"  Sentiment Mass: {result_bull['sentiment_mass']}")
    print(f"  Pressure Vector: {result_bull['pressure_vector']}")
    print(f"  Field Status: {result_bull['synergy_field_status']}")
    print(f"  Valid: {result_bull['valid']}")
    print(f"  Trace: {result_bull['reasoning_trace'][:80]}...")
    
    # Test bearish/scam argument
    bearish = "This is a scam! Dump now! Emergency sell before the crash!"
    result_bear = c2v.validate_debate_argument(bearish, block_height=8453298)
    print(f"\nBearish/Scam Argument Test:")
    print(f"  Text: {bearish[:50]}...")
    print(f"  Sentiment Mass: {result_bear['sentiment_mass']}")
    print(f"  Pressure Vector: {result_bear['pressure_vector']}")
    print(f"  Field Status: {result_bear['synergy_field_status']}")
    print(f"  Valid: {result_bear['valid']}")
    
    # Test neutral argument
    neutral = "I think we should consider the long term implications."
    result_neutral = c2v.validate_debate_argument(neutral, block_height=8453298)
    print(f"\nNeutral Argument Test:")
    print(f"  Text: {neutral}")
    print(f"  Sentiment Mass: {result_neutral['sentiment_mass']}")
    print(f"  Pressure Vector: {result_neutral['pressure_vector']}")
    print(f"  Field Status: {result_neutral['synergy_field_status']}")
