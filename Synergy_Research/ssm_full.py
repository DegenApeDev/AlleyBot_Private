# ssm_full.py
import math
from dataclasses import dataclass
from typing import Dict, Any


# -----------------------------------------
# Synergy Standard Model (full JS version)
# -----------------------------------------

class SynergyStandardModel:
    def __init__(self):
        # core constants (match JS values)
        self.dc = 2240.0

        # Pi approximations
        self.pi_params = {
            "a": 3.940245e12,
            "b": 2217131.0,
            "c": 1.25385975e12,
        }
        self.pin_params = {
            "a": 20250000.0,
            "b": 194580.0,
            "c": 61919.0,
            "d": 2217131.0,
        }

        # Bubble-mass base (bu.a * bu.b * bu.c ~ electron mass denom)
        self.bu = {
            "a": 1352.0,
            "b": 5.442245307660239,
            "c": 1.2379901546155434e-34,
        }

        # Precompute Qp/Qs arena once to get c1/c2 etc.
        arena = self.Qp()  # uses bu + PI internally
        self.c1 = arena["cx"]
        self.c2 = arena["cy"]

        # SC = 1/162 (used in S / Sx)
        self.SC = 1.0 / 162.0

        # Structured vacuum impedance pieces
        self.C = self.Ma(self.Mx(1.0 / self.c1))
        self.G = self.Ma(7.327140922766658e19)
        self.Z0 = self.C / self.G

    # ---------- basic helpers ----------

    def rd(self, n: float) -> float:
        return round(n)

    def fl(self, n: float) -> float:
        return math.floor(n)

    # ---------- SyMod roots (alt naming of D/Dr/Dp/Dg) ----------

    def sym(self, n: float) -> int:
        """Primary SyMod digital root (JS sym)."""
        sq = 3 ** 2
        return int(self.rd(sq - (n / sq - self.fl(n / sq)) * sq))

    def dr(self, n: float) -> int:
        """Double application of sym."""
        return self.sym(self.sym(n))

    def pr(self, n: float) -> int:
        """Polar digital root (single application)."""
        return self.sym(n)

    def grp(self, n: float) -> int:
        """Group digital number (3-based variant)."""
        th = 3.0
        return int(
            self.rd(
                th ** 2
                - ((n / th) - self.fl(n / th)) * (th ** 2)
            )
        )

    # ---------- EM-style laws based on C/Z0 ----------

    def gaussE(self, rho: float) -> float:
        """Structured Gauss’s law for E."""
        return rho * self.C * self.Z0

    def gaussB(self, B: float) -> float:
        """No magnetic monopoles."""
        return B * 0.0

    def faraday(self, E: float) -> float:
        """Structured Faraday’s law."""
        return -1.0 * (E / self.C)

    def ampere(self, J: float, E: float) -> float:
        """Structured Ampère–Maxwell."""
        return (self.Z0 / self.C) * J + (1.0 / (self.C ** 2)) * E

    # ---------- Alternative D / “devil” equations ----------

    def D_dev(self, n: float = 1.0) -> float:
        """
        JS: D(n=1){
            const a = n+0.2169108218;
            const b = (a+1);
            return 1/(a*b);
        }
        """
        a = n + 0.2169108218
        b = a + 1.0
        return 1.0 / (a * b)

    def Dsy(self, n: float = 1.0) -> float:
        """
        JS: Dsy(n=1){
            const a = n + (1-(1/ Math.sqrt(1.62)));
            const b = (a+1);
            return 1/(a*b);
        }
        """
        a = n + (1.0 - 1.0 / math.sqrt(1.62))
        b = a + 1.0
        return 1.0 / (a * b)

    # (Dm in the JS uses global sy + PI etc.; it’s experimental.
    # You can port it if you actually need it, but it isn’t used
    # anywhere in the released logic.)

    # ---------- Feyn / stability helpers ----------

    def feyn(self, n: float) -> float:
        """
        JS:
          const q = Math.sqrt(5)/2;
          const Phi = q+0.5;
          const pha=360/Math.pow(Phi,2);
          return 1/(pha-(10*((this.PI(n)/3)-1)));
        """
        q = math.sqrt(5.0) / 2.0
        phi = q + 0.5
        pha = 360.0 / (phi ** 2)
        return 1.0 / (pha - 10.0 * ((self.PI(n) / 3.0) - 1.0))

    def stability(self, n: int = 1) -> float:
        """
        Direct translation of the JS stability(n) function.
        Uses Fibonacci-like digit sequences and dc cycle.
        """
        N = (10 * 15) * (2240 / ((math.sqrt(5) / 2.0)))
        LIM = self.B(N)

        seq_fib = {
            1: [1, 1, 2, 3, 5, 8, 4, 3, 7, 1, 8, 9, 8, 8, 7, 6, 4, 1, 5, 6, 2, 8, 1, 9],
            2: [2, 2, 4, 6, 1, 7, 8, 6, 5, 2, 7, 9, 7, 7, 5, 3, 8, 2, 1, 3, 4, 7, 2, 9],
            3: [3, 3, 6, 9, 6, 6, 3, 9, 3, 3, 6, 9, 6, 6, 3, 9, 3, 3, 6, 9, 6, 6, 3, 9],
            4: [4, 4, 8, 3, 2, 5, 7, 3, 1, 4, 5, 9, 5, 5, 1, 6, 7, 4, 2, 6, 8, 5, 4, 9],
            5: [5, 5, 1, 6, 7, 4, 2, 6, 8, 5, 4, 9, 4, 4, 8, 3, 2, 5, 7, 3, 1, 4, 5, 9],
            6: [6, 6, 3, 9, 3, 3, 6, 9, 6, 6, 3, 9, 3, 3, 6, 9, 6, 6, 3, 9, 3, 3, 6, 9],
            7: [7, 7, 5, 3, 8, 2, 1, 3, 4, 7, 2, 9, 2, 2, 4, 6, 1, 7, 8, 6, 5, 2, 7, 9],
            8: [8, 8, 7, 6, 4, 1, 5, 6, 2, 8, 1, 9, 1, 1, 2, 3, 5, 8, 4, 3, 7, 1, 8, 9],
            9: [9] * 24,
        }
        seq_dc = [1, 2, 4, 8, 7, 5]

        i = (n - 1) % 24
        di = (n - 1) % 6
        dr_val = self.dr(n)
        pr_val = self.pr(n)

        F = seq_fib[1][i]
        f = seq_fib[dr_val][i]
        dc = seq_dc[di]

        exp = math.sqrt(dr_val * pr_val * F * f * dc * n)
        diff = LIM - exp
        sT = diff / LIM
        return sT

    # ---------- Syπ and mass equations ----------

    def PI(self, n: float = 162.0) -> float:
        p = self.pi_params
        return p["a"] / (p["b"] * n + p["c"])

    def Px(self, n: float = 1.0) -> float:
        p = self.pin_params
        return p["a"] * (p["b"] - (p["c"] * n)) / (p["d"] * n)

    def Mb(self, n: float = 7.327140922766658e19) -> float:
        """Bubble mass base equation Mb(n)."""
        # JS: ((n/216)/100)**9
        return ((n / 216.0) / 100.0) ** 9

    def Md(self, n: float = 1.0, p: float = None) -> Dict[str, float]:
        """Bubble mass detect / diagnostic."""
        if p is None:
            p = self.Mb()
        m1 = self.Ma(p)
        m2 = ((n - m1) / 2.16) * self.PI(n)
        return {
            "n": n,
            "p": p,
            "m2": m2,
            "rat": m2 / m1,
            "comp": n / m2,
        }

    def Me(self, n: float = 1.0, c: float = 1.0) -> float:
        """Bubble mass impedance."""
        return self.Ma(self.Mx(1.0 / (c * n)))

    def Mi(self, n: float = 1.0) -> float:
        M = math.sqrt(2.0) + (1.0 / (n * (1.0 / (10.0 ** 2))))
        return self.dc / math.sqrt(M)

    def Mn(self) -> float:
        return self.Mi((2240.0 / (math.sqrt(5.0) / 2.0)) * (10.0 ** 15))

    def Mx(self, n: float = 1.0) -> float:
        return n / (self.bu["a"] * self.bu["b"] * self.bu["c"])

    def Ma(self, n: float = 1.0, units: bool = False) -> float:
        """Core mass calculation; if units=True, use Mu instead."""
        if not units:
            return n * self.bu["a"] * self.bu["b"] * self.bu["c"]
        return self.Mu(n, units)

    def Mu(self, n: float = 1.0, units: bool | str = False):
        """
        Mass with optional unit conversion.
        units in {False, 'kg', 'j', 'MeV', 'GeV'}.
        """
        kg = n * self.bu["a"] * self.bu["b"] * self.bu["c"]

        if not units or units == "kg":
            return kg

        c = self.c1
        joules = kg * (c ** 2)
        # ej = eV per joule factor from JS
        ej = 6.852004036967059e33
        mev = joules * ej  # MeV equivalent
        gev = mev / 1000.0

        if units == "j":
            return joules
        if units == "MeV":
            return mev
        if units == "GeV":
            return gev
        # default: full dict
        return {
            "kg": kg,
            "joules": joules,
            "MeV": mev,
            "GeV": gev,
        }

    # ---------- Einstein / Schrödinger ----------

    def EFE(self, n: float = 1.0, G: float | None = None, c: float | None = None) -> float:
        """Experimental Einstein field equation form."""
        if G is None:
            G = self.G
        if c is None:
            c = self.c1
        # ((8π(n) * Ma(G)) / c^4) * (Ma(n) * c^2)
        return ((8.0 * math.pi * self.Ma(G)) / (c ** 4)) * (self.Ma(n) * (c ** 2))

    def S(self, n: float = 0.0) -> float:
        """Pi mass equation S(n) = M(n+SC) * P(n)."""
        return self.M(n + self.SC) * self.P(n)

    # Note: M() and P() aren’t explicitly defined in the JS snippet you pasted.
    # If you need them, they can be mapped to Ma()/PI() or to your existing
    # synergy_logic equivalents.

    def Wv(self, n: float = 0.0) -> float:
        """Schrödinger wave term Wv(n)."""
        hbar = 1.054571817e-34
        return -1.0 * (hbar ** 2) / (2.0 * n)

    def Wa(self, n: float = 1.0, V: float = 0.0) -> float:
        """Synergy Schrödinger wave equation Wa."""
        m = self.S(n)
        return self.Wv(m) + V

    def Wx(self, n: float = 1.0, V: float = 0.0) -> float:
        """Inverse Schrödinger wave position."""
        Mv = self.Wv(n) + V
        return self.Sx(Mv)

    # ---------- Quadrian speed / path (full Qp) ----------

    def Qs(self, n: float) -> float:
        q = math.sqrt(1.0 ** 2 + 0.5 ** 2)
        a = 22.5 * (8.0 / 6.0)
        b = a - (1.0 / (1000.0 - n))
        c = b * (10.0 ** 7)
        d = 1.0 / (q / n)
        return c - d

    def Qp(self) -> Dict[str, float]:
        """
        Full Quadrian path arena (JS Qp()).
        Returns dict with cx, cy, C, Z0, μ0, ε0, etc.
        """
        Z = 1.0 / 2.0 / 4.0 / 8.0 / 7.0 / 5.0
        q = math.sqrt(1.0 ** 2 + 0.5 ** 2)
        D = 8.0 * q
        sqrt2 = math.sqrt(2.0)

        tx = (q + 0.5) * (15.0 + sqrt2)
        ty = 90.0 - tx
        tz = ty * 2.0
        td = ty - tx
        tu = tz * 7.0

        t1 = 4.0 * tx + 3.0 * ty
        t2 = 3.0 * tx + 4.0 * ty

        px = tu + tx
        py = tu + ty

        vx = (10.0 ** 3) - px
        vy = (10.0 ** 3) - py

        pxz = Z * t1
        pyz = Z * t2

        Pe = D + pxz
        Pn = D + pyz
        K = Pn - Pe
        pt = vy / vx

        cy = self.Qs(px)
        cx = self.Qs(py)

        G_val = self.Me(50.0 - (1.0 / 44.0), cx)
        C_val = self.Me(1.0, cx)

        mu0 = (4.0 * self.PI(162.0)) * (10e-8)
        eps0 = 1.0 / (mu0 * (cx ** 2))
        Z0 = C_val / eps0
        ident = eps0 * mu0 * (cx ** 2)

        return {
            "id": ident,
            "q": q,
            "tx": tx,
            "ty": ty,
            "td": td,
            "tu": tu,
            "t1": t1,
            "t2": t2,
            "px": px,
            "py": py,
            "vx": vx,
            "vy": vy,
            "pt": pt,
            "pxz": pxz,
            "pyz": pyz,
            "K": K,
            "G": G_val,
            "C": C_val,
            "Z0": Z0,
            "ε0": eps0,
            "μ0": mu0,
            "cy": cy,
            "cx": cx,
        }

    # ---------- meta helper ----------

    def meta(self, n: float, alt: bool = False) -> Dict[str, Any]:
        c = self.c2 if alt else self.c1
        return {
            "number": n,
            "root": self.dr(n),
            "group": self.grp(n),
            "polar": self.pr(n),
            "P": self.PI(n),
            "M": self.Ma(n),
            "Mx": self.Mx(n),
            "EFE": self.EFE(n, 7.327140922766658e19, c),
            "Wv": self.Wv(n),
            "Wx": self.Wx(self.Wv(n)),
            "stability": self.stability(int(n)),
        }


# -----------------------------------------
# SynergyNumbers catalog
# -----------------------------------------

class SynergyNumbers:
    """
    Direct port of the SynergyNumbers class.

    NOTE: I’ve left the huge atomic constant table as-is structurally;
    you can copy the numeric values 1:1 from your JS into `pe()`.
    """

    def __init__(self, symod: SynergyStandardModel):
        self.symod = symod

    def pe(self) -> Dict[str, float]:
        # paste the aH, aHe, ... , aUue constants here exactly
        # from your JS `pe()`; then return them in a dict.
        aH = 1837.5435195254177
        # ...
        # aUue = 574232.3498516929
        return {
            "aH": aH,
            # ... all other aX keys ...
            # "aUue": aUue,
        }

    def numbers(self, alt: bool = False, sort: bool = False,
                type: str = "all") -> Dict[str, float]:
        c = self.symod.c2 if alt else self.symod.c1

        # scalar constants (match JS names/values)
        gamma = 0.0
        gl = 0.0
        gr = 0.0
        Td = 9.365741240486245e-26
        Th = 2.247777897716699e-24
        Ts = 8.092000431780115e-21
        # ... continue porting the scalars from JS numbers() ...
        # W, emR, emM, ..., Tr, He, C2, C, Hb, Tpt, μ0, α, ej, etc.

        data = {
            "c": c,
            "γ": gamma,
            "gl": gl,
            "gr": gr,
            "Td": Td,
            "Th": Th,
            "Ts": Ts,
            # ... all other entries ...
        }

        # Optionally merge atom table
        # data.update(self.pe())

        categories = {
            "atoms": [
                "aH", "aHe", "aLi", "aBe", "aB", "aC", "aN", "aO",
                # ... full list from JS ...
            ],
            "molecules": ["H2O"],
            "force": ["W", "Wc", "S", "Sc"],
            "energy": ["eM", "k", "a", "eV", "j", "Hc", "ε0", "G", "C", "C2", "μ0", "α"],
            "life": ["Hs", "Hl", "Hm", "Tr", "He", "Hb"],
            "spectrum": ["emR", "emM", "emIr", "emVr", "emV", "emU", "emG"],
            "time": ["Td", "Th", "Ts", "Tml", "Tmc", "Tns", "Tps", "Tfs", "Tzs", "Tys", "Tpt"],
            "particles": ["γ", "gl", "gr", "νe", "νμ", "ντ", "νs", "L", "e", "p", "n",
                          "qU", "qD", "qS", "qC", "qB", "qT"],
            "leptons": ["γ", "gl", "gr", "νe", "νμ", "ντ", "νs", "L", "e", "p", "n", "m", "d"],
            "bosons": ["bW", "bZ", "bH"],
            "quarks": ["qU", "qD", "qS", "qC", "qB", "qT"],
        }

        if type != "all" and type in categories:
            keys = set(categories[type])
            filtered = {k: v for k, v in data.items() if k in keys}
        else:
            filtered = dict(data)

        if sort:
            filtered = dict(sorted(filtered.items(), key=lambda kv: kv[1]))

        return filtered

    def model(self, alt: bool = False, unit: bool = False,
              sort: bool = False, type: str = "all") -> Dict[str, float]:
        numbers = self.numbers(alt=alt, sort=sort, type=type)
        mass: Dict[str, float] = {}
        for key, value in numbers.items():
            if key != "c":
                mass[key] = self.symod.Mu(value, unit)
        return mass

if __name__ == "__main__":
    sy = SynergyStandardModel()

    # basic sanity checks
    print("PI(162) =", sy.PI(162))
    print("Ma(1)   =", sy.Ma(1))
    print("Mx(1)   =", sy.Mx(1))

    # golden-window style meta test
    m = sy.meta(42)
    print("meta(42) =", m)
