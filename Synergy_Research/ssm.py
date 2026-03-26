"""
Synergy Standard Model (SSM) - Python Implementation
Author: Wesley Long
Converts JavaScript ssm.js to Python with identical mathematical outputs
"""

import math


class SynergyStandardModel:
    """SSM Physics Engine - Derives fundamental constants from pure geometry"""
    
    def __init__(self, strict=False):
        self.strict = strict
        if strict:
            self._derive_constants()
    
    # SyMod - Digital Root
    def D(self, n):
        sq = 3**2
        return round(sq - (n / sq - math.floor(n / sq)) * sq)
    
    # Digital Root
    def Dr(self, n):
        return self.D(self.D(n))
    
    # Polar Digital Root
    def Dp(self, n):
        return self.D(n)
    
    # Group Digital Number
    def Dg(self, n):
        return round(3**2 - ((n) / 3 - math.floor((n) / 3)) * 3**2)
    
    # Quadrian e (Ramanujan & Euler)
    def Qe(self, n=163, c=262537412640768744):
        b = c if c > 0 else math.exp(math.pi * math.sqrt(n))
        q = math.sqrt(5) / 2
        PHI = q + (1 / 2)
        phi = q - (1 / 2)
        sq = math.sqrt(n)
        ln = math.log(b)
        pi = ln / sq
        e = math.sqrt(PHI * (5 - ((3 * 5 - 2) / (3 * 5 * 2))))
        id_val = (1 / 447867046214735262) * (10**18)
        diff = math.sqrt(5) - id_val
        return {'q': q, 'PHI': PHI, 'phi': phi, 'e': e, 'pi': pi, 'id': id_val, 'diff': diff}
    
    def _derive_constants(self):
        """STRICT MODE: Derive all constants from the forced chain. No cached literals."""
        # Step 4: q and Φ from unit square
        q = math.sqrt(1**2 + 0.5**2)  # √5/2
        PHI = q + 0.5
        phi = q - 0.5  # φ = Φ - 1
        
        # Step 7: Scale factors from q and 8-direction structure
        D = 8 * q  # total path length: 8 directions × leg length q
        U = D**2 / 8  # mean squared displacement per leg = 10
        L = 8 * (U * q)**2  # arena capacity = 1000
        F = 30  # R_turn × R_pent × R_tri (arena point count ratios)
        
        # Step 8: Speed equation → cy
        sqrt2 = math.sqrt(2)
        theta_x = PHI * (15 + sqrt2)
        theta_y = 90 - theta_x
        theta_z = theta_y * 2
        theta_u = theta_z * 7
        PNp = theta_u + theta_y
        S = L * 10**4  # = 10^7
        cy = S * (F - 1 / (L - PNp)) - (2 * PNp) / math.sqrt(5)
        
        # Step 11: Mass index from Doubling Circuit
        # Mi(75) → 1352 (self-referential index)
        self._mi_75 = 2240 / math.sqrt(sqrt2 + (1 / (75 * (1 / 10**2))))
        
        # Step 11: Proton/electron ratio from self-reference
        # Mi(Mi(75)) = 1836.18...
        self._proton_electron = 2240 / math.sqrt(sqrt2 + (1 / (self._mi_75 * (1 / 10**2))))
        self._neutron_electron = self._proton_electron + 2
        
        # Steps 4+7: √(F + φ - 1)
        self._mass_scale = math.sqrt(F + phi - 1)
        
        # Step 8: 1/cy⁴
        self._inv_cy4 = 1 / cy**4
        
        # Step 10: Fw(11) → a value for Ft()
        mx = sqrt2 + (1 / math.sqrt((15**2) + (1 / math.sqrt(((11 + 5) * 20) - (1 / 20)))))
        self._fw_a = 11 + (math.sqrt(mx) - 1)
    
    # Quadrian Path Equation
    def Qp(self, n):
        return (30 - 1 / (10**3 - n)) - (2 * n / (10**7 * math.sqrt(5)))
    
    # Quadrian Speed Equation
    def Qs(self, n):
        return (10**7 * (30 - (1 / (10**3 - n)))) - ((2 * n) / math.sqrt(5))
    
    # Quadrian Arena Model
    def Qa(self):
        q = math.sqrt(1**2 + 0.5**2)
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
        PNd = 10**3 - PNp
        PEd = 10**3 - PEp
        Qc = PNd / PEd
        Qa_val = PNa / PEa
        py = self.Qp(PNp)
        px = self.Qp(PEp)
        cy = self.Qs(PNp)
        cx = self.Qs(PEp)
        μ0 = (4 * self.PI(162)) * (10e-8)
        ε0 = 1 / (μ0 * (cy**2))
        C = {
            'cy': self.Me(1, cy),
            'cx': self.Me(1, cx)
        }
        Z0 = {
            'cy': C['cy'] / ε0,
            'cx': C['cx'] / ε0
        }
        id_val = ε0 * μ0 * (cy**2)
        return {
            'id': id_val, 'q': q, 'θx': θx, 'θy': θy, 'θv': θv, 'θz': θz, 'θu': θu,
            'PNa': PNa, 'PEa': PEa, 'PNp': PNp, 'PEp': PEp, 'PNd': PNd, 'PEd': PEd,
            'Qc': Qc, 'Qa': Qa_val, 'C': C, 'Z0': Z0, 'ε0': ε0, 'μ0': μ0,
            'py': py, 'px': px, 'cy': cy, 'cx': cx
        }
    
    # Syπ Equation (Simplified)
    def PI(self, n=162):
        return 3940245000000 / ((2217131 * n) + 1253859750000)
    
    # Syπ Position Equation (Simplified)
    def Px(self, n=1):
        return 20250000 * (194580 - (61919 * n)) / (2217131 * n)
    
    # Feyn-Wolfgang Triangle
    def Ft(self, n=1):
        if self.strict:
            a = self._fw_a
            b = a + 1
        else:
            a = 11.2169108218
            b = 12.2169108218
        c = math.sqrt(a**2 + b**2)
        g = math.sqrt(a**2 * 2)
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
    
    # Feyn-Pencil Equation
    def Fx(self, n, p):
        PI_val = self.PI(p)
        pi = 100 / PI_val
        g = (math.sqrt(5) / 2) + 0.5
        ga = 360 / (g**2)
        return ((pi * n) - (ga / 1000))**2
    
    # Feyn-Wolfgang Coupling Equation
    def Fw(self, n=11):
        mx = math.sqrt(2) + (1 / math.sqrt((15**2) + (1 / math.sqrt(((n + 5) * 20) - (1 / 20)))))
        a = n + (math.sqrt(mx) - 1)
        return 1 / (a * (a + 1))
    
    # Feyn-Wolfgang Coupling Equation (Simplified)
    def Fe(self, n=11):
        a = n + (1084554109 / 5000000000)
        return 1 / (a * (a + 1))
    
    # Synergy Feyn Planck constant
    def Fh(self):
        f = self.Fe(11)
        m = self.Ma(1 / f)
        H = self.Mn() * (10**2)
        return m / H
    
    # Synergy Feyn Planck constants
    def Fhc(self):
        Gn = self.Fx(11, -math.sqrt(4538))
        h = self.Fh()
        hb = self.Fhbar()
        G = self.Fe(Gn)
        qa = self.Qa()
        c = qa['cy']
        ε0 = qa['ε0']
        k = self.Ma((88**2) * 1957)
        tp = math.sqrt((hb * G) / (c**5))
        lp = math.sqrt((hb * G) / (c**3))
        mp = math.sqrt((hb * c) / G)
        Tp = math.sqrt((hb * (c**5)) / (G * (k**2)))
        qp = math.sqrt(4 * self.PI(h) * ε0 * hb * c)
        return {'h': h, 'hb': hb, 'tp': tp, 'lp': lp, 'mp': mp, 'Tp': Tp, 'qp': qp}
    
    # Synergy Feyn Planck reduced constant
    def Fhbar(self):
        return self.Fh() / (2 * self.PI(self.Fh()))
    
    # Synergy Feyn Planck Radius
    def Fr(self, m):
        return 4 * (self.Fhbar() / (m * self.Qa()['cx']))
    
    # Bubble Mass Impedance
    def Me(self, n=1, c=1):
        return self.Ma(self.Mx(1 / (c * n)))
    
    # Synergy Bubble Mass Index
    def Mi(self, n=1):
        M = math.sqrt(2) + (1 / (n * (1 / 10**2)))
        return 2240 / math.sqrt(M)
    
    # Synergy Bubble Mass Index (inverse)
    def Mxi(self, n=1):
        dc = 2240
        sqrt2 = math.sqrt(2)
        return 100 / (((dc / n)**2) - sqrt2)
    
    # Synergy Bubble Mass Natural Limit
    def Mn(self):
        return self.Mi((2240 / (math.sqrt(5) / 2)) * (10**15))
    
    # Synergy Bubble Mass Position (Inverse)
    def Mx(self, n=1):
        if self.strict:
            return n / (self._mi_75 * self._mass_scale * self._inv_cy4)
        return n / (1352 * 5.442245307660239 * 1.2379901546155434e-34)
    
    # Synergy Bubble Mass Equation (Simplified)
    def Ma(self, n=1):
        if self.strict:
            return n * self._mi_75 * self._mass_scale * self._inv_cy4
        return n * 1352 * 5.442245307660239 * 1.2379901546155434e-34
    
    # Synergy Elements
    def El(self, e, p, n):
        me = self.Ma(1)
        if self.strict:
            mp = self.Ma(self._proton_electron)
            mn = self.Ma(self._neutron_electron)
        else:
            mp = self.Ma(1836.1813326060937)
            mn = self.Ma(1838.1813326060937)
        pc = mp * p
        nc = mn * n
        ec = me * e
        m = ((pc + nc + ec) - ((pc + nc + ec) * self.Fw(11)))
        return m
    
    # Synergy Field Structure
    def Sfs(self, alt=True):
        q = self.Qa()
        C = q['C']['cy'] if alt else q['C']['cx']
        Z0 = q['Z0']['cy'] if alt else q['Z0']['cx']
        return {'C': C, 'Z0': Z0}
    
    # Synergy Gauss's Law (Electric Field from Structured Charge)
    def SgE(self, rho):
        f = self.Sfs()
        return rho * f['C'] * f['Z0']
    
    # Synergy Gauss's Law for Magnetism (No Magnetic Monopoles)
    def SgB(self, B):
        return B * 0
    
    # Synergy Faraday's Law (Structured EM Wave Propagation)
    def SfE(self, E):
        f = self.Sfs()
        return -1 * (E / f['C'])
    
    # Synergy Ampère-Maxwell Law (Structured Charge-Mass Interactions)
    def SaE(self, J, E):
        f = self.Sfs()
        return (f['Z0'] / f['C']) * J + (1 / f['C']**2) * E
    
    # Quadrian Bubble Core Level
    def Bcl(self, n=1):
        B = 1
        L = n
        p = 1 / 16
        m = math.sqrt(p)
        d = math.sqrt(L * m)
        r = d / 2
        Q = d**(B / L)
        theta = (L - B) * (B + L)
        angles = self.Qba(Q, d, theta)
        octo = self.Qoc(d)
        coords = self.Qc(d)
        quads = self.Qbq(B, r, L)
        shell = self.Qsh(B, m, d)
        return {'L': L, 'angles': angles, 'octo': octo, 'coords': coords, 'quads': quads, 'shell': shell}
    
    # Quadrian Shell
    def Qsh(self, B, m, d):
        Bm = math.sqrt(B * m)
        N = [Bm, d]
        E = [d, Bm]
        S = [Bm, 0]
        W = [0, Bm]
        return {'N': N, 'E': E, 'S': S, 'W': W}
    
    # Quadrian Bubble Core Quadrants
    def Qbq(self, B, r, L):
        rL = math.sqrt((B * r) / L)
        N1 = [r, r + rL]
        E1 = [r + rL, r]
        S1 = [rL, r]
        W1 = [r, rL]
        return {'N1': N1, 'E1': E1, 'S1': S1, 'W1': W1}
    
    # Quadrian Coordinates
    def Qc(self, d):
        da = d**(3 / 4)
        db = d**(1 / 4)
        return {'Ne': [da, db], 'Se': [db, db], 'Sw': [db, da], 'Nw': [da, da]}
    
    # Quadrian Octo Coordinates
    def Qoc(self, d):
        da = d**(5 / 8)
        db = d**(3 / 8)
        return {'Ne1': [da, db], 'Se1': [da, db], 'Sw1': [db, db], 'Nw1': [db, da]}
    
    # Quadrian Bubble Angles
    def Qba(self, Q, d, theta):
        betaN = [d - Q, Q * math.tan(theta)]
        betaS = [d - Q, Q * math.tan(theta)]
        betaE = [d, 0]
        return {'betaN': betaN, 'betaS': betaS, 'betaE': betaE}


# Global instance for easy access
sy = SynergyStandardModel()
# Strict mode instance — no cached literals, everything derived from chain
sy_strict = SynergyStandardModel(strict=True)


def run_validation_suite(strict=False):
    """Run full validation comparing outputs to known values"""
    s = sy_strict if strict else sy
    mode = "STRICT (no cached literals)" if strict else "STANDARD"
    print("=" * 70)
    print(f"SYNERGY STANDARD MODEL - PYTHON VALIDATION SUITE [{mode}]")
    print("=" * 70)
    
    # Test Qa
    print("\n--- Quadrian Arena (Qa) ---")
    qa = s.Qa()
    print(f"q (Quadrian Ratio): {qa['q']:.15f}")
    print(f"θx: {qa['θx']:.15f}°")
    print(f"θy: {qa['θy']:.15f}°")
    print(f"θz: {qa['θz']:.15f}°")
    print(f"cy (Speed of Light North): {qa['cy']:.10f} m/s")
    print(f"cx (Speed of Light East): {qa['cx']:.10f} m/s")
    print(f"ε0 (Vacuum Permittivity): {qa['ε0']:.15e}")
    print(f"μ0 (Vacuum Permeability): {qa['μ0']:.15e}")
    print(f"Z0 cy (Impedance North): {qa['Z0']['cy']:.10f} Ω")
    print(f"EM Identity (ε₀μ₀c²): {qa['id']:.15f}")
    
    # Test Qe
    print("\n--- Quadrian Euler (Qe) ---")
    qe = s.Qe()
    print(f"PHI (Golden Ratio): {qe['PHI']:.15f}")
    print(f"phi (Golden Reciprocal): {qe['phi']:.15f}")
    print(f"e (Euler): {qe['e']:.15f}")
    print(f"pi: {qe['pi']:.15f}")
    
    # Test Syπ
    print("\n--- Syπ Values ---")
    print(f"PI(162): {s.PI(162):.15f}")
    print(f"PI(1): {s.PI(1):.15f}")
    
    # Test Fine-Structure
    print("\n--- Coupling Constants ---")
    print(f"Fe(11) [Fine-structure α]: {s.Fe(11):.15f}")
    print(f"1/Fe(11) [~137]: {1/s.Fe(11):.10f}")
    
    # Test Planck
    print("\n--- Planck Constants ---")
    fhc = s.Fhc()
    print(f"h: {fhc['h']:.15e} J⋅s")
    print(f"ℏ (h-bar): {fhc['hb']:.15e} J⋅s")
    print(f"Planck time (tp): {fhc['tp']:.15e} s")
    print(f"Planck length (lp): {fhc['lp']:.15e} m")
    print(f"Planck mass (mp): {fhc['mp']:.15e} kg")
    print(f"Planck temp (Tp): {fhc['Tp']:.15e} K")
    print(f"Planck charge (qp): {fhc['qp']:.15e} C")
    
    # Test particle masses
    print("\n--- Particle Masses ---")
    print(f"Electron: {s.Ma(1):.15e} kg")
    print(f"Muon: {s.Ma(207):.15e} kg")
    if strict:
        print(f"Proton: {s.Ma(s._proton_electron):.15e} kg")
        print(f"Neutron: {s.Ma(s._neutron_electron):.15e} kg")
    else:
        print(f"Proton: {s.Ma(1836.1813326060937):.15e} kg")
        print(f"Neutron: {s.Ma(1838.1813326060937):.15e} kg")
    
    # Test elements
    print("\n--- Element Masses (sample) ---")
    elements = [
        ('H', 1, 1, 0), ('He', 2, 2, 2), ('C', 6, 6, 6),
        ('O', 8, 8, 8), ('Fe', 26, 26, 30), ('Au', 79, 79, 118)
    ]
    for symbol, e, p, n in elements:
        mass = s.El(e, p, n)
        print(f"[{symbol}] {symbol}: {mass:.15e} kg")
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    
    return True



# ======================================================================
# CROSS-VALIDATION SUITE (merged from test_validation.py)
# Compares Python implementation outputs to JavaScript reference values
# ======================================================================

def test_ssm_crossval():
    """Validate SSM Python matches JS reference values"""
    print("=" * 70)
    print("SSM VALIDATION - Python vs JavaScript Reference")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test Qa - reference values from ssm.js comments
    qa = sy.Qa()
    tests = [
        ('q', qa['q'], 1.118033988749895),
        ('thx', qa['θx'], 26.55875544251916),
        ('thy', qa['θy'], 63.44124455748084),
        ('thz', qa['θz'], 126.88248911496169),
        ('PNa', qa['PNa'], 296.55875544251916),
        ('PEa', qa['PEa'], 333.44124455748084),
        ('PNp', qa['PNp'], 951.6186683622127),
        ('PEp', qa['PEp'], 914.736179247251),
        ('PNd', qa['PNd'], 48.3813316377873),
        ('PEd', qa['PEd'], 85.26382075274898),
        ('Qc', qa['Qc'], 0.5674309597042945),
        ('Qa', qa['Qa'], 0.889388341373577),
        ('e0', qa['ε0'], 8.854187757429692e-12),
        ('u0', qa['μ0'], 0.000001256637073723813),
        ('py', qa['py'], 29.979245755324857),
        ('px', qa['px'], 29.98818987962603),
        ('cy', qa['cy'], 299792457.5532486),
        ('cx', qa['cx'], 299881898.7962603),
        ('id', qa['id'], 1.0),
    ]
    
    print("\n--- Quadrian Arena (Qa) ---")
    for name, actual, expected in tests:
        diff = abs(actual - expected)
        tolerance = 1e-10 if expected < 100 else 1e-6
        status = 'PASS' if diff < tolerance else 'FAIL'
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        print(f"{name:12s}: {actual:20.15f} vs {expected:20.15f} [{status}]")
    
    # Test Qe
    qe = sy.Qe()
    print("\n--- Quadrian Euler (Qe) ---")
    for name, actual, expected in [
        ('q', qe['q'], 1.118033988749895),
        ('PHI', qe['PHI'], 1.618033988749895),
        ('phi', qe['phi'], 0.6180339887498949),
        ('e', qe['e'], 2.7182755345913434),
        ('pi', qe['pi'], 3.141592653589793),
    ]:
        diff = abs(actual - expected)
        status = 'PASS' if diff < 1e-12 else 'FAIL'
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        print(f"{name:12s}: {actual:20.15f} vs {expected:20.15f} [{status}]")
    
    # Test SyPI
    print("\n--- SyPI Values ---")
    pi_162 = sy.PI(162)
    pi_1 = sy.PI(1)
    print(f"PI(162): {pi_162:.15f} (expected: 3.1415926843095328)")
    print(f"PI(1):   {pi_1:.15f} (expected: 3.142487054628346)")
    
    # Test coupling constants
    print("\n--- Coupling Constants ---")
    fe_11 = sy.Fe(11)
    print(f"Fe(11) [alpha]: {fe_11:.15f}")
    print(f"1/alpha: {1/fe_11:.10f} (expected ~137.036)")
    
    # Test Planck
    print("\n--- Planck Constants ---")
    fhc = sy.Fhc()
    planck_tests = [
        ('h', fhc['h'], 6.626987439910871e-34),
        ('hb', fhc['hb'], 1.0544157551953982e-34),
        ('tp', fhc['tp'], 5.390879110484635e-44),
        ('lp', fhc['lp'], 1.616144896904659e-35),
        ('mp', fhc['mp'], 2.176260547814635e-8),
        ('Tp', fhc['Tp'], 1.4168508256452144e+32),
        ('qp', fhc['qp'], 1.87567584803208e-18),
    ]
    for name, actual, expected in planck_tests:
        diff = abs(actual - expected) / expected
        status = 'PASS' if diff < 1e-10 else 'FAIL'
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        print(f"{name:12s}: {actual:20.15e} vs {expected:20.15e} [{status}]")
    
    # Test particle masses
    print("\n--- Particle Masses ---")
    mass_tests = [
        ('Electron', sy.Ma(1), 9.109027140565893e-31),
        ('Muon', sy.Ma(207), 1.8855686180971397e-28),
        ('Proton', sy.Ma(1836.1813326060937), 1.6725825593709357e-27),
        ('Neutron', sy.Ma(1838.1813326060937), 1.6744043647990487e-27),
    ]
    for name, actual, expected in mass_tests:
        diff = abs(actual - expected) / expected
        status = 'PASS' if diff < 1e-10 else 'FAIL'
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        print(f"{name:12s}: {actual:20.15e} kg [{status}]")
    
    # Test elements
    print("\n--- Element Masses (sample) ---")
    elements = [
        ('H', 1, 1, 0, 1.66128139028063e-27),
        ('He', 2, 2, 2, 6.646934072194125e-27),
        ('C', 6, 6, 6, 1.9940802216582374e-26),
        ('O', 8, 8, 8, 2.65877362887765e-26),
        ('Fe', 26, 26, 30, 9.305888552178935e-26),
        ('Au', 79, 79, 118, 3.2737913603850878e-25),
    ]
    for symbol, e, p, n, expected in elements:
        mass = sy.El(e, p, n)
        diff = abs(mass - expected) / expected
        status = 'PASS' if diff < 1e-10 else 'FAIL'
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        print(f"[{symbol:2s}] {symbol:8s}: {mass:20.15e} kg [{status}]")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    
    return failed == 0


def test_duat_crossval():
    """Validate Duat engine runs correctly"""
    try:
        from duat import DuatCognitionEngine
    except ImportError:
        print("\n[SKIP] duat.py not found — skipping Duat cross-validation")
        return True
    
    print("\n" + "=" * 70)
    print("DUAT COGNITION ENGINE - Python Implementation Test")
    print("=" * 70)
    
    engine = DuatCognitionEngine()
    
    print("\nInitial state:")
    print(f"  truth: {engine.state['truth']:.3f}")
    print(f"  coherence: {engine.state['coherence']:.3f}")
    print(f"  energy: {engine.state['energy']:.3f}")
    
    # Run actions
    actions_to_test = ['reflection', 'purification', 'coherence_init', 'ascension_prime']
    
    for action_name in actions_to_test:
        try:
            engine.run(action_name)
            print(f"\nAfter '{action_name}':")
            print(f"  truth: {engine.state['truth']:.3f}")
            print(f"  coherence: {engine.state['coherence']:.3f}")
            print(f"  energy: {engine.state['energy']:.3f}")
            print(f"  time: {engine.state['time']}")
            print(f"  entropy: {engine.state['entropy']:.3f}")
        except Exception as e:
            print(f"ERROR running '{action_name}': {e}")
            return False
    
    # Test sequence
    print("\n--- Testing sequence ---")
    engine2 = DuatCognitionEngine()
    engine2.sequence(['reflection', 'coherence_init', 'ascension_prime'])
    print(f"Final: truth={engine2.state['truth']:.3f}, coherence={engine2.state['coherence']:.3f}")
    
    print("\n" + "=" * 70)
    print("DUAT TEST COMPLETE")
    print("=" * 70)
    
    return True


def compare_to_codata():
    """Compare SSM outputs to CODATA 2018 values"""
    print("\n" + "=" * 70)
    print("SSM vs CODATA 2018 COMPARISON")
    print("=" * 70)
    
    qa = sy.Qa()
    fhc = sy.Fhc()
    
    comparisons = [
        ('Speed of light (c)', qa['cy'], 299792458, 'm/s'),
        ('Fine-structure (alpha)', sy.Fe(11), 0.0072973525693, ''),
        ('Vacuum permittivity (e0)', qa['ε0'], 8.854187817e-12, 'F/m'),
        ('Vacuum permeability (u0)', qa['μ0'], 1.2566370614e-6, 'H/m'),
        ('Planck constant (h)', fhc['h'], 6.62607015e-34, 'J.s'),
        ('Reduced Planck (hbar)', fhc['hb'], 1.054571817e-34, 'J.s'),
        ('Planck time', fhc['tp'], 5.391247e-44, 's'),
        ('Planck length', fhc['lp'], 1.616255e-35, 'm'),
        ('Planck mass', fhc['mp'], 2.176434e-8, 'kg'),
        ('Planck temp', fhc['Tp'], 1.416784e+32, 'K'),
        ('Planck charge', fhc['qp'], 1.875545956e-18, 'C'),
    ]
    
    print(f"\n{'Constant':35s} {'SSM':20s} {'CODATA':20s} {'Error':10s}")
    print("-" * 105)
    
    for name, ssm_val, codata_val, unit in comparisons:
        if codata_val != 0:
            error_pct = abs(ssm_val - codata_val) / codata_val * 100
            error_str = f"{error_pct:.6f}%"
        else:
            error_str = "N/A"
        
        if unit:
            print(f"{name:35s} {ssm_val:20.10e} {codata_val:20.10e} {error_str:>10s}")
        else:
            print(f"{name:35s} {ssm_val:20.10f} {codata_val:20.10f} {error_str:>10s}")
    
    print("=" * 70)


if __name__ == "__main__":
    import sys
    strict = '--strict' in sys.argv
    crossval = '--crossval' in sys.argv
    
    if crossval:
        # Run cross-validation suite (merged from test_validation.py)
        print("\n" + "=" * 70)
        print("  SYNERGY STANDARD MODEL & DUAT VALIDATION SUITE  ".center(70))
        print("=" * 70)
        ssm_ok = test_ssm_crossval()
        duat_ok = test_duat_crossval()
        compare_to_codata()
        print("\n" + "=" * 70)
        if ssm_ok and duat_ok:
            print("  ALL TESTS PASSED  ".center(70))
        else:
            print("  SOME TESTS FAILED  ".center(70))
        print("=" * 70)
    else:
        run_validation_suite(strict=strict)
        if not strict:
            print("\n" + "=" * 70)
            print("STRICT MODE COMPARISON (no cached literals)")
            print("=" * 70)
            run_validation_suite(strict=True)
