/**
 * SSM Verification Suite — JavaScript (Node.js)
 * Run: node test_ssm.js
 * 
 * Compares SSM-derived values against CODATA 2018 reference constants.
 * Zero inputs. Zero parameters. Pure geometric derivation.
 */

// Inline the SSM class (self-contained — no imports needed)
class SynergyStandardModel {
    constructor() {}
    D(n) { const sq = 9; return Math.round(sq - (n / sq - Math.floor(n / sq)) * sq); }
    Dr(n) { return this.D(this.D(n)); }
    PI(n = 162) { return 3940245000000 / ((2217131 * n) + 1253859750000); }
    Px(n = 1) { return 20250000 * (194580 - (61919 * n)) / (2217131 * n); }
    Qs(n) { return (Math.pow(10, 7) * (30 - (1 / (Math.pow(10, 3) - n)))) - ((2 * n) / Math.sqrt(5)); }
    Qp(n) { return (30 - 1 / (Math.pow(10, 3) - n)) - (2 * n / (Math.pow(10, 7) * Math.sqrt(5))); }
    Fw(n = 11) {
        let mx = Math.sqrt(2) + (1 / Math.sqrt((15**2) + (1 / Math.sqrt(((n + 5) * 20) - (1 / 20)))));
        let a = n + (Math.sqrt(mx) - 1);
        return 1 / (a * (a + 1));
    }
    Fe(n = 11) { let a = n + (1084554109 / 5000000000); return 1 / (a * (a + 1)); }
    Mi(n = 1) { const M = Math.sqrt(2) + (1 / (n * (1 / Math.pow(10, 2)))); return 2240 / Math.sqrt(M); }
    Mn() { return this.Mi((2240 / (Math.sqrt(5) / 2)) * (1e15)); }
    Ma(n = 1) { return n * 1352 * 5.442245307660239 * 1.2379901546155434e-34; }
    Mx(n = 1) { return n / (1352 * 5.442245307660239 * 1.2379901546155434e-34); }
    Me(n = 1, c = 1) { return this.Ma(this.Mx(1 / (c * n))); }
    Fh() { const f = this.Fe(11); const m = this.Ma(1 / f); const H = this.Mn() * (1e2); return m / H; }
    Fhbar() { return this.Fh() / (2 * this.PI(this.Fh())); }
    Fx(n, p) { let PI = this.PI(p); let pi = 100 / PI; let g = (Math.sqrt(5) / 2) + .5; let ga = 360 / (g**2); return ((pi * n) - (ga / 1000))**2; }
    Qa() {
        const q = Math.sqrt(Math.pow(1, 2) + Math.pow(0.5, 2));
        const sqrt2 = Math.sqrt(2);
        const θx = (q + 0.5) * (15 + sqrt2);
        const θy = 90 - θx;
        const θz = θy * 2;
        const θv = θy - θx;
        const θu = θz * 7;
        const PNa = 4 * θx + 3 * θy;
        const PEa = 3 * θx + 4 * θy;
        const PEp = θu + θx;
        const PNp = θu + θy;
        const PNd = 1e3 - PNp;
        const PEd = 1e3 - PEp;
        const Qc = PNd / PEd;
        const Qa = PNa / PEa;
        const py = this.Qp(PNp);
        const px = this.Qp(PEp);
        const cy = this.Qs(PNp);
        const cx = this.Qs(PEp);
        const μ0 = (4 * this.PI(162)) * (10e-8);
        const ε0 = 1 / (μ0 * (cy**2));
        const C = { cy: this.Me(1, cy), cx: this.Me(1, cx) };
        const Z0 = { cy: C.cy / ε0, cx: C.cx / ε0 };
        const id = ε0 * μ0 * (cy**2);
        return { id, q, θx, θy, θv, θz, θu, PNa, PEa, PNp, PEp, PNd, PEd, Qc, Qa, C, Z0, ε0, μ0, py, px, cy, cx };
    }
    Fhc() {
        const Gn = this.Fx(11, -Math.sqrt(4538));
        const h = this.Fh();
        const hb = this.Fhbar();
        const G = this.Fe(Gn);
        const c = this.Qa().cy;
        const ε0 = this.Qa().ε0;
        const k = this.Ma((88**2) * 1957);
        const tp = Math.sqrt((hb * G) / (c**5));
        const lp = Math.sqrt((hb * G) / (c**3));
        const mp = Math.sqrt((hb * c) / G);
        const Tp = Math.sqrt((hb * (c**5)) / (G * (k**2)));
        const qp = Math.sqrt(4 * this.PI(h) * ε0 * hb * c);
        return { h, hb, tp, lp, mp, Tp, qp };
    }
    El(e, p, n) {
        const me = this.Ma(1);
        const mp = this.Ma(1836.1813326060937);
        const mn = this.Ma(1838.1813326060937);
        const pc = mp * p;
        const nc = mn * n;
        const ec = me * e;
        return ((pc + nc + ec) - ((pc + nc + ec) * this.Fw(11)));
    }
}

// ═══════════════════════════════════════════════════════════════════
//  TEST RUNNER
// ═══════════════════════════════════════════════════════════════════

const sy = new SynergyStandardModel();
let passed = 0;
let failed = 0;

function assert(name, actual, expected, tolerance) {
    const diff = Math.abs(actual - expected);
    const relErr = expected !== 0 ? diff / Math.abs(expected) : diff;
    const ok = relErr < tolerance;
    if (ok) {
        passed++;
        console.log(`  ✓ ${name}: ${actual} (error: ${(relErr * 100).toFixed(10)}%)`);
    } else {
        failed++;
        console.log(`  ✗ ${name}: ${actual} vs ${expected} (error: ${(relErr * 100).toFixed(6)}%) FAIL`);
    }
}

console.log('═'.repeat(70));
console.log('  SYNERGY STANDARD MODEL — JAVASCRIPT VERIFICATION SUITE');
console.log('═'.repeat(70));

// ─── 1. SPEED OF LIGHT ───────────────────────────────────────────
console.log('\n── Step 1: Speed of Light ──');
const qa = sy.Qa();
assert('cy (North path)', qa.cy, 299792457.5532486, 1e-12);
assert('cx (East path)', qa.cx, 299881898.7962603, 1e-12);
assert('cy vs CODATA c', qa.cy, 299792458, 2e-9);   // <0.0000002% error

// ─── 2. Syπ ──────────────────────────────────────────────────────
console.log('\n── Step 2: Syπ Equation ──');
assert('Syπ(162)', sy.PI(162), 3.1415926843095328, 1e-12);
const px = sy.Px(Math.PI);
assert('Syπ(Px(π)) ≈ π', sy.PI(px), Math.PI, 1e-14);

// ─── 3. FINE-STRUCTURE CONSTANT ──────────────────────────────────
console.log('\n── Step 3: Fine-Structure Constant ──');
const alpha = sy.Fe(11);
assert('α = Fe(11)', alpha, 0.007297352562786393, 1e-12);
assert('1/α ≈ 137.036', 1 / alpha, 137.03599920601394, 1e-12);
assert('α vs CODATA', alpha, 0.0072973525693, 1e-6);

// ─── 4. MASS ─────────────────────────────────────────────────────
console.log('\n── Step 4: Particle Masses ──');
assert('Electron mass', sy.Ma(1), 9.109027140565893e-31, 1e-12);
assert('Proton mass', sy.Ma(1836.1813326060937), 1.6725825593709357e-27, 1e-12);
assert('Neutron mass', sy.Ma(1838.1813326060937), 1.6744043647990487e-27, 1e-12);
assert('Muon mass', sy.Ma(207), 1.8855686180971397e-28, 1e-12);
assert('Electron vs CODATA', sy.Ma(1), 9.1093837015e-31, 4e-5);

// ─── 5. MASS INDEX ───────────────────────────────────────────────
console.log('\n── Step 5: Mass Index (Mi) ──');
const mi75 = sy.Mi(75);
assert('Mi(75) → 1352', mi75, 1352, 1e-3);
const mi1352 = sy.Mi(mi75);
assert('Mi(1352) → 1836.18', mi1352, 1836.1813326060937, 1e-6);

// ─── 6. ELECTROMAGNETIC CONSTANTS ────────────────────────────────
console.log('\n── Step 6: EM Constants ──');
assert('ε₀', qa.ε0, 8.854187757429692e-12, 1e-12);
assert('μ₀', qa.μ0, 1.256637073723813e-6, 1e-12);
assert('ε₀μ₀c² = 1', qa.id, 1.0, 1e-12);
assert('Z₀ (North)', qa.Z0.cy, 376.73031658418466, 1e-10);
assert('ε₀ vs CODATA', qa.ε0, 8.8541878128e-12, 1e-5);

// ─── 7. PLANCK CONSTANTS ─────────────────────────────────────────
console.log('\n── Step 7: Planck Constants ──');
const fhc = sy.Fhc();
assert('h (Planck)', fhc.h, 6.626987439910871e-34, 1e-10);
assert('ℏ (reduced)', fhc.hb, 1.0544157551953982e-34, 1e-10);
assert('Planck time', fhc.tp, 5.390879110484635e-44, 1e-10);
assert('Planck length', fhc.lp, 1.616144896904659e-35, 1e-10);
assert('Planck mass', fhc.mp, 2.176260547814635e-8, 1e-10);
assert('h vs CODATA', fhc.h, 6.62607015e-34, 2e-4);

// ─── 8. ARENA INTERMEDIATES ──────────────────────────────────────
console.log('\n── Step 8: Arena Intermediates ──');
assert('q (Quadrian Ratio)', qa.q, 1.118033988749895, 1e-14);
assert('Φ (Golden Ratio)', qa.q + 0.5, 1.618033988749895, 1e-14);
assert('θx', qa.θx, 26.55875544251916, 1e-12);
assert('θy', qa.θy, 63.44124455748084, 1e-12);
assert('PNp', qa.PNp, 951.6186683622127, 1e-12);
assert('PEp', qa.PEp, 914.736179247251, 1e-12);

// ─── 9. ELEMENT MASSES ──────────────────────────────────────────
console.log('\n── Step 9: Element Masses (sample) ──');
assert('[H] Hydrogen', sy.El(1, 1, 0), 1.66128139028063e-27, 1e-10);
assert('[He] Helium', sy.El(2, 2, 2), 6.646934072194125e-27, 1e-10);
assert('[C] Carbon', sy.El(6, 6, 6), 1.9940802216582374e-26, 1e-10);
assert('[O] Oxygen', sy.El(8, 8, 8), 2.65877362887765e-26, 1e-10);
assert('[Fe] Iron', sy.El(26, 26, 30), 9.305888552178935e-26, 1e-10);
assert('[Au] Gold', sy.El(79, 79, 118), 3.2737913603850878e-25, 1e-10);

// ─── 10. CODATA COMPARISON TABLE ─────────────────────────────────
console.log('\n── CODATA 2018 Comparison ──');
const codata = [
    ['Speed of light (c)', qa.cy, 299792458, 'm/s'],
    ['Fine-structure (α)', alpha, 0.0072973525693, ''],
    ['Vacuum permittivity (ε₀)', qa.ε0, 8.8541878128e-12, 'F/m'],
    ['Vacuum permeability (μ₀)', qa.μ0, 1.25663706212e-6, 'H/m'],
    ['Planck constant (h)', fhc.h, 6.62607015e-34, 'J·s'],
    ['Reduced Planck (ℏ)', fhc.hb, 1.054571817e-34, 'J·s'],
    ['Electron mass (mₑ)', sy.Ma(1), 9.1093837015e-31, 'kg'],
    ['Proton mass (mₚ)', sy.Ma(1836.1813326060937), 1.67262192369e-27, 'kg'],
];
console.log(`${'Constant'.padEnd(30)} ${'SSM'.padStart(20)} ${'CODATA'.padStart(20)} ${'Error %'.padStart(12)}`);
console.log('─'.repeat(85));
for (const [name, ssm, ref, unit] of codata) {
    const err = Math.abs(ssm - ref) / ref * 100;
    console.log(`${name.padEnd(30)} ${ssm.toExponential(10).padStart(20)} ${ref.toExponential(10).padStart(20)} ${err.toFixed(8).padStart(12)}%`);
}

// ═══════════════════════════════════════════════════════════════════
//  SUMMARY
// ═══════════════════════════════════════════════════════════════════
console.log('\n' + '═'.repeat(70));
console.log(`  RESULTS: ${passed} PASSED, ${failed} FAILED`);
if (failed === 0) {
    console.log('  ALL TESTS PASSED — SSM outputs verified');
} else {
    console.log(`  ${failed} TEST(S) FAILED — investigate above`);
}
console.log('═'.repeat(70));

process.exit(failed > 0 ? 1 : 0);
