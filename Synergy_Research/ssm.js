class SynergyStandardModel{
    constructor(){}
    //SyMod
    D(n) {
        const sq = 3**2;
        return Math.round(sq - (n / sq - Math.floor(n / sq)) * sq);
    }
    //Digtal Root
    Dr(n) { return this.D(this.D(n));}

    //Polar Digital Root
    Dp(n) { return this.D(n);}

    //Group Digital Number
    Dg(n) { return Math.round(Math.pow(3, 2) - ((n) / 3 - Math.floor((n) / 3)) * Math.pow(3, 2)); }

    //Quadrian e (Ramanujan & Euler)
    Qe(n = 163, c = 262537412640768744) {
        const b = c > 0 ? c : Math.exp(Math.PI * Math.sqrt(n));
        const q = Math.sqrt(5)/2;
        const PHI = q + (1 / 2);
        const phi = q - (1 / 2);
        const sq = Math.sqrt(n);
        const ln = Math.log(b);
        const pi = ln / sq;
        const e = Math.sqrt(PHI * (5 - ((3 * 5 - 2) / (3 * 5 * 2))));
        const id = (1/447867046214735262)*(10**18);
        const diff = Math.sqrt(5)-id;
        return { q, PHI, phi, e, pi, id,diff};
    }

    //Quadrian Path Equation
    Qp(n) {
        return (30 - 1 / (Math.pow(10, 3) - n)) - (2 * n / (Math.pow(10, 7) * Math.sqrt(5)));
    }

    //Quadrian Speed Equation
    Qs(n){
        return (Math.pow(10, 7) * (30 - (1 / (Math.pow(10, 3) - n))))-((2 * n) / Math.sqrt(5));
    }

    //Quadrian Arena Model
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
        const PNd = Math.pow(10, 3)-PNp;
        const PEd = Math.pow(10, 3)-PEp;
        const Qc = PNd/PEd;
        const Qa = PNa/PEa;
        const py = this.Qp(PNp);
        const px = this.Qp(PEp);
        const cy = this.Qs(PNp);
        const cx = this.Qs(PEp);
        const μ0 = (4*this.PI(162))*(10e-8)
        const ε0 = 1/(μ0*(cy**2));
        const C = {
            cy:this.Me(1, cy),
            cx:this.Me(1, cx)
        };
        const Z0 = {
            cy:C.cy / ε0,
            cx:C.cx / ε0,
        }
        const id = ε0 * μ0 * (cy**2);
        return { id,q,θx,θy,θv,θz,θu,PNa,PEa,PNp,PEp,PNd,PEd,Qc,Qa,C,Z0,ε0,μ0,py,px,cy,cx };
    }

    //Syπ Equation (Simplified)
    PI(n=162){
        return 3940245000000 / ((2217131 * n ) + 1253859750000);
    }

    //Syπ Position Equation (Simplified)
    Px(n=1){
        return 20250000 * (194580 - (61919 * n)) / (2217131 * n);
    }

    //Feyn-Wolfgang Triangle
    Ft(n=1){
        const a = 11.2169108218;
        const b = 12.2169108218;
        const c = Math.sqrt((a**2)+(b**2));
        const g = Math.sqrt((a**2)*2);
        const ra = a/c;
        const rb = b/c;
        const f = (b*n) * (1/b);
        const e = (b*n) * (rb*(1/b));
        const d = (a*n) * (ra*(1/a));
        return {
            a: a * n,
            b: b * n,
            c: c * n,
            g: g * n,
            f: f,
            e: e,
            d: d,
            FU:f
        };
    }

    //Feyn-Pencil Equation
    Fx(n,p){
        let PI = this.PI(p);
        let pi = 100/PI;
        let g = (Math.sqrt(5)/2)+.5;
        let ga = 360/(g**2)
        return ((pi*n)-(ga/1000))**2;
    }

    //Feyn-Wolfgang Coupling Equation
    Fw(n=11){
        let mx = Math.sqrt(2) + (1 / Math.sqrt((15**2) + (1 / Math.sqrt(((n + 5) * 20) - (1 / 20)))));
        let a = n + (Math.sqrt(mx) - 1);
        return 1/(a * (a + 1));
    }

    //Feyn-Wolfgang Coupling Equation (Simplified)
    Fe(n=11){
        let a = n + ( 1084554109 / 5000000000 );
        return 1/(a * (a + 1));
    }

    //Synergy Feyn Plank constant
    Fh(){
        const f = this.Fe(11);
        const m = this.Ma(1/f);
        const H = this.Mn()*(10**2)
        return m/H;
    }

    //Synergy Feyn Plank constants
    Fhc(){
        const Gn = this.Fx(11,-Math.sqrt(4538));
        const h = this.Fh();
        const hb = this.Fhbar();
        const G = this.Fe(Gn);
        const c = this.Qa().cy;
        const ε0 = this.Qa().ε0;
        const k = this.Ma((88**2)*1957);
        const tp = Math.sqrt((hb*G)/(c**5));
        const lp = Math.sqrt((hb*G)/(c**3));
        const mp = Math.sqrt((hb*c)/G)
        const Tp = Math.sqrt((hb*(c**5))/(G*(k**2)));
        const qp = Math.sqrt( 4*this.PI(h)*ε0*hb*c);
        return {h,hb,tp,lp,mp,Tp,qp}
    }

    //Synergy Feyn Plank reduced constant
    Fhbar(){
        return this.Fh()/(2*this.PI(this.Fh()));
    }

    //Synergy Feyn Plank Radius
    Fr(m){
        return 4*(this.Fhbar()/(m*this.Qa().cx));
    }

    //Bubble Mass Impedance*
    Me(n=1,c=1){ return this.Ma(this.Mx(1/(c*n))) }

    //Synergy Bubble Mass Index
    Mi(n=1) {
        const M = Math.sqrt(2) + (1 / (n * (1 / Math.pow(10, 2))));
        return 2240 / Math.sqrt(M)
    }

    //Synergy Bubble Mass Index (inverse)
    Mxi(n=1) {
        const dc = 2240;
        const sqrt2 = Math.sqrt(2);
        return 100 / (((dc / n) ** 2) - sqrt2);
    }

    //Synergy Bubble Mass Natural Limit
    Mn(){
        return this.Mi((2240/(Math.sqrt(5)/2))*(10**15))
    }

    //Synergy Bubble Mass Position (Inverse)
    Mx(n=1){
        return n / (1352 * 5.442245307660239 * 1.2379901546155434e-34)
    }

    //Synergy Bubble Mass Equation (Simplified)
    Ma(n = 1) {
        return n * 1352* 5.442245307660239 * 1.2379901546155434e-34
    }

    //Synergy Elements
    El(e,p,n){
        const me = this.Ma(1);
        const mp = this.Ma(1836.1813326060937);
        const mn = this.Ma(1838.1813326060937);
        const pc = mp*p;
        const nc = mn*n;
        const ec = me*e;
        const m =((pc+nc+ec)-((pc+nc+ec)*this.Fw(11)));
        return m;
    }

    //Synergy Field Structure
    Sfs(alt=true){
        const q = this.Qp();
        const C = alt ? q.C.cy : q.C.cx;
        const Z0 = alt ? q.Z0.cy : q.Z0.cx;
        return {C, Z0}
    }

    //Synergy Gauss’s Law (Electric Field from Structured Charge)
    SgE(rho) {
        const f = this.Sfs();
        return rho * f.C * f.Z0;
    }

    //Synergy Gauss’s Law for Magnetism (No Magnetic Monopoles)
    SgB(B) {
        return B * 0;
    }

    //Synergy Faraday’s Law (Structured Electromagnetic Wave Propagation)
    SfE(E) {
        const f = this.Sfs();
        return -1 * (E / f.C);
    }

    //Synergy Ampère-Maxwell Law (Structured Charge-Mass Interactions)
    SaE(J, E) {
        const f = this.Sfs();
        return (f.Z0 / f.C) * J + (1 / f.C ** 2) * (E);
    }
    //Quadrian Bubble Core Level
    Bcl(n = 1) {
        const B = 1;
        const L = n;
        const p = 1 / 16;
        const m = Math.sqrt(p);
        const d = Math.sqrt(L * m);
        const r = d / 2;
        const Q = Math.pow(d, B / L);
        const theta = (L - B) * (B + L);
        const angles = this.Qba(Q, d, theta);
        const octo = this.Qoc(d);
        const coords = this.Qc(d);
        const quads = this.Qbq(B, r, L);
        const shell = this.Qsh(B, m, d);
        return { L, angles, octo, coords, quads, shell };
    }
    //Quadrian Shell
    Qsh(B, m, d) {
        const Bm = Math.sqrt(B * m); // sqrt(B * m)
        const N = [Bm, d];
        const E = [d, Bm];
        const S = [Bm, 0];
        const W = [0, Bm];
        return { N, E, S, W };
    }
    //Quadrian Bubble Core Quadrants
    Qbq(B, r, L) {
        const rL = Math.sqrt((B * r) / L);
        const N1 = [r, r + rL];
        const E1 = [r + rL, r];
        const S1 = [rL, r];
        const W1 = [r, rL];
        return { N1, E1, S1, W1 };
    }
    //Quadrian Coordinates
    Qc(d) {
        const da = Math.pow(d, 3 / 4);
        const db = Math.pow(d, 1 / 4);
        return {
            Ne: [da, db],
            Se: [db, db],
            Sw: [db, da],
            Nw: [da, da]
        };
    }
    //Quadrian Octo Coordinates
    Qoc(d) {
        const da = Math.pow(d, 5 / 8);
        const db = Math.pow(d, 3 / 8);
        return {
            Ne1: [da, db],
            Se1: [da, db],
            Sw1: [db, db],
            Nw1: [db, da]
        };
    }
    //Quadrian Bubble Angles
    Qba(Q, d, theta) {
        const betaN = [d - Q, Q * Math.tan(theta)];
        const betaS = [d - Q, Q * Math.tan(theta)];
        const betaE = [d, 0];
        return { betaN, betaS, betaE };
    }
}

const sy = new SynergyStandardModel();

let Gn=sy.Fx(11,-Math.sqrt(4538));
console.log('Gn',sy.Fx(1,1))
console.log('Gn',Gn)
let Kn=(Gn**2)*sy.Mx(sy.Fe(Gn));
let KN=1097812076491272500000000000000;

/*
console.clear();
console.log(sy.Qa())
console.log(sy.Qe())
console.log('----------------------------------------');
console.log('Pi',sy.PI(162));
console.log('Quadrian Ratio',sy.Qa().q);
console.log('Golden Ratio',sy.Qa().q+.5);
console.log('Golden Ratio Reciprocal',sy.Qa().q-.5);
console.log('Quadrian Euler e',sy.Qe());
console.log('----------------------------------------');
console.log('Speed of Light (East)',sy.Qa().cx);
console.log('Speed of Light (North)',sy.Qa().cy);
console.log('Vacuum Permeability (μ0)',sy.Qa().μ0);
console.log('Vacuum Permittivity (ε0)',sy.Qa().ε0);
console.log('Inertial Impedance*',sy.Qa().C);
console.log('Characteristic Impedance of Free Space (Z0)',sy.Qa().Z0);
console.log('Electromagnetic Identity',sy.Qa().id);
console.log('----------------------------------------');
console.log('Graviton?',sy.Fe(1));
console.log('Graviton?',sy.Ma(GVn));
console.log('Fine-structure constant',sy.Fe(11));
console.log('Gravitational constant G',sy.Fe(Gn));
console.log('Kilogram Kn->(kg)',sy.Ma(Kn));
console.log('Kilogram KN->(kg)',sy.Ma(KN));
console.log('Atomic Unit',sy.Ma(1822.9610527929553));
console.log('----------------------------------------');
console.log('Planck constants',sy.Fhc());
console.log('----------------------------------------');
console.log('Muon Magnetic Moment',sy.Ma(10118108)); // Mu Moment 11*919828
console.log('----------------------------------------');
console.log('Boltzmann',sy.Ma(15155008)); // Boltzman 11*1377728
console.log('Avogadro',sy.Ma(66111788)); // Arvo 11*6010162.5454545454545454545454545
console.log('eV',sy.Ma(175888888888)); // eV 11*15989898989.818181818181818181818
console.log('----------------------------------------');
console.log('Electron Mass',sy.Ma(1));
console.log('Muon Mass',sy.Ma(207));
console.log('Proton Mass',sy.Ma(1836.1813326060937));
console.log('Neutron Mass',sy.Ma(1838.1813326060937));
console.log('Deuteron Mass',sy.Ma(3669));
console.log('----------------------------------------');
console.log('Up Quark',sy.Ma(1957*((1/22)**2)));
console.log('Down Quark',sy.Ma(1957*((1/14)**2)));
console.log('Strange Quark',sy.Ma(1957*((1/3.25)**2)));
console.log('Charm Quark',sy.Ma(1957*((1/1.126)**2)));
console.log('Bottom Quark',sy.Ma(1957*((1/2)**2)));
console.log('Top Quark',sy.Ma(1957*((1/13)**2)));
console.log('----------------------------------------');
console.log('Electron (νe)',sy.Ma((1/66111788)*0.5));
console.log('Muon (νμ)',sy.Ma((1/(19*523523))));
console.log('Tau (ντ)',sy.Ma(((1/2.61)/(19*523523))));
console.log('----------------------------------------');
console.log('Higgs Boson',sy.Ma(244625));
console.log('W Strong Boson',sy.Ma(154560));
console.log('Z Weak Boson',sy.Ma(176130));
console.log('----------------------------------------');
console.log('Strong Force',sy.Ma(273)); // Strong Force 11*24.8181818181
console.log('Weak Force',sy.Ma(156328)); //Weak Force 11*14211.636363636363636363636363636
console.log('----------------------------------------');
console.log("[H] - Hydrogen", sy.El(1,1,0));
console.log("[He] - Helium", sy.El(2,2,2));
console.log("[Li] - Lithium", sy.El(3,3,4));
console.log("[Be] - Beryllium", sy.El(4,4,5));
console.log("[B] - Boron", sy.El(5,5,6));
console.log("[C] - Carbon", sy.El(6,6,6));
console.log("[N] - Nitrogen", sy.El(7,7,7));
console.log("[O] - Oxygen", sy.El(8,8,8));
console.log("[F] - Fluorine", sy.El(9,9,10));
console.log("[Ne] - Neon", sy.El(10,10,10));
console.log("[Na] - Sodium", sy.El(11,11,12));
console.log("[Mg] - Magnesium", sy.El(12,12,12));
console.log("[Al] - Aluminum", sy.El(13,13,14));
console.log("[Si] - Silicon", sy.El(14,14,14));
console.log("[P] - Phosphorus", sy.El(15,15,16));
console.log("[S] - Sulfur", sy.El(16,16,16));
console.log("[Cl] - Chlorine", sy.El(17,17,18));
console.log("[Ar] - Argon", sy.El(18,18,22));
console.log("[K] - Potassium", sy.El(19,19,20));
console.log("[Ca] - Calcium", sy.El(20,20,20));
console.log("[Sc] - Scandium", sy.El(21,21,24));
console.log("[Ti] - Titanium", sy.El(22,22,26));
console.log("[V] - Vanadium", sy.El(23,23,28));
console.log("[Cr] - Chromium", sy.El(24,24,28));
console.log("[Mn] - Manganese", sy.El(25,25,30));
console.log("[Fe] - Iron", sy.El(26,26,30));
console.log("[Co] - Cobalt", sy.El(27,27,32));
console.log("[Ni] - Nickel", sy.El(28,28,31));
console.log("[Cu] - Copper", sy.El(29,29,35));
console.log("[Zn] - Zinc", sy.El(30,30,35));
console.log("[Ga] - Gallium", sy.El(31,31,39));
console.log("[Ge] - Germanium", sy.El(32,32,41));
console.log("[As] - Arsenic", sy.El(33,33,42));
console.log("[Se] - Selenium", sy.El(34,34,45));
console.log("[Br] - Bromine", sy.El(35,35,45));
console.log("[Kr] - Krypton", sy.El(36,36,48));
console.log("[Rb] - Rubidium", sy.El(37,37,48));
console.log("[Sr] - Strontium", sy.El(38,38,50));
console.log("[Y] - Yttrium", sy.El(39,39,50));
console.log("[Zr] - Zirconium", sy.El(40,40,51));
console.log("[Nb] - Niobium", sy.El(41,41,52));
console.log("[Mo] - Molybdenum", sy.El(42,42,54));
console.log("[Tc] - Technetium", sy.El(43,43,55));        // radioactive, most stable isotope: Tc-98
console.log("[Ru] - Ruthenium", sy.El(44,44,57));
console.log("[Rh] - Rhodium", sy.El(45,45,58));
console.log("[Pd] - Palladium", sy.El(46,46,60));
console.log("[Ag] - Silver", sy.El(47,47,61));
console.log("[Cd] - Cadmium", sy.El(48,48,64));
console.log("[In] - Indium", sy.El(49,49,66));
console.log("[Sn] - Tin", sy.El(50,50,69));
console.log("[Sb] - Antimony", sy.El(51,51,71));
console.log("[Te] - Tellurium", sy.El(52,52,76));
console.log("[I] - Iodine", sy.El(53,53,74));
console.log("[Xe] - Xenon", sy.El(54,54,77));
console.log("[Cs] - Cesium", sy.El(55,55,78));
console.log("[Ba] - Barium", sy.El(56,56,81));
console.log("[La] - Lanthanum", sy.El(57,57,82));
console.log("[Ce] - Cerium", sy.El(58,58,82));
console.log("[Pr] - Praseodymium", sy.El(59,59,82));
console.log("[Nd] - Neodymium", sy.El(60,60,84));
console.log("[Pm] - Promethium", sy.El(61,61,84));       // radioactive, longest-lived: Pm-145
console.log("[Sm] - Samarium", sy.El(62,62,88));
console.log("[Eu] - Europium", sy.El(63,63,89));
console.log("[Gd] - Gadolinium", sy.El(64,64,93));
console.log("[Tb] - Terbium", sy.El(65,65,94));
console.log("[Dy] - Dysprosium", sy.El(66,66,97));
console.log("[Ho] - Holmium", sy.El(67,67,98));
console.log("[Er] - Erbium", sy.El(68,68,99));
console.log("[Tm] - Thulium", sy.El(69,69,100));
console.log("[Yb] - Ytterbium", sy.El(70,70,103));
console.log("[Lu] - Lutetium", sy.El(71,71,104));
console.log("[Hf] - Hafnium", sy.El(72,72,106));
console.log("[Ta] - Tantalum", sy.El(73,73,108));
console.log("[W] - Tungsten", sy.El(74,74,110));
console.log("[Re] - Rhenium", sy.El(75,75,111));
console.log("[Os] - Osmium", sy.El(76,76,114));
console.log("[Ir] - Iridium", sy.El(77,77,115));
console.log("[Pt] - Platinum", sy.El(78,78,117));
console.log("[Au] - Gold", sy.El(79,79,118));
console.log("[Hg] - Mercury", sy.El(80,80,121));
console.log("[Tl] - Thallium", sy.El(81,81,123));
console.log("[Pb] - Lead", sy.El(82,82,125));
console.log("[Bi] - Bismuth", sy.El(83,83,126));
console.log("[Po] - Polonium", sy.El(84,84,125));       // radioactive, longest-lived: Po-209
console.log("[At] - Astatine", sy.El(85,85,125));       // radioactive, estimated: At-210
console.log("[Rn] - Radon", sy.El(86,86,136));          // radioactive, longest-lived: Rn-222
console.log("[Fr] - Francium", sy.El(87,87,136));       // radioactive, estimated: Fr-223
console.log("[Ra] - Radium", sy.El(88,88,138));
console.log("[Ac] - Actinium", sy.El(89,89,138));
console.log("[Th] - Thorium", sy.El(90,90,142));
console.log("[Pa] - Protactinium", sy.El(91,91,140));
console.log("[U] - Uranium", sy.El(92,92,146));
console.log("[Np] - Neptunium", sy.El(93,93,144));
console.log("[Pu] - Plutonium", sy.El(94,94,150));
console.log("[Am] - Americium", sy.El(95,95,148));
console.log("[Cm] - Curium", sy.El(96,96,151));
console.log("[Bk] - Berkelium", sy.El(97,97,150));
console.log("[Cf] - Californium", sy.El(98,98,153));
console.log("[Es] - Einsteinium", sy.El(99,99,153));
console.log("[Fm] - Fermium", sy.El(100,100,157));
console.log("[Md] - Mendelevium", sy.El(101,101,157));
console.log("[No] - Nobelium", sy.El(102,102,157));
console.log("[Lr] - Lawrencium", sy.El(103,103,159));
console.log("[Rf] - Rutherfordium", sy.El(104,104,157));
console.log("[Db] - Dubnium", sy.El(105,105,157));
console.log("[Sg] - Seaborgium", sy.El(106,106,160));
console.log("[Bh] - Bohrium", sy.El(107,107,157));
console.log("[Hs] - Hassium", sy.El(108,108,161));
console.log("[Mt] - Meitnerium", sy.El(109,109,169));
console.log("[Ds] - Darmstadtium", sy.El(110,110,171));
console.log("[Rg] - Roentgenium", sy.El(111,111,172));
console.log("[Cn] - Copernicium", sy.El(112,112,173));
console.log("[Nh] - Nihonium", sy.El(113,113,173));
console.log("[Fl] - Flerovium", sy.El(114,114,175));
console.log("[Mc] - Moscovium", sy.El(115,115,176));
console.log("[Lv] - Livermorium", sy.El(116,116,177));
console.log("[Ts] - Tennessine", sy.El(117,117,177));
console.log("[Og] - Oganesson", sy.El(118,118,176));
console.log('----------------------------------------');
console.log('Sommerfeld',sy.Ft(1/11.2169108218));
console.log('Wolfgang',sy.Ft(0.5));
console.log('Feynman',sy.Ft(1));
console.log('Newton',sy.Ft(10912.426374590997463750559137034));
console.log('Boltzmann',sy.Ft(23993597863.062500825560410269357));
console.log('----------------------------------------');
console.log('Joule','3864983.4319038160658266372422068',sy.Fe((sy.PI(3864983.4319038160658266372422068))),sy.PI(3864983.4319038160658266372422068));
console.log('One','1',sy.Fe(sy.PI(1211649.3116554683)),sy.PI(1211649.3116554683));
console.log('Pi',sy.Fe((sy.PI(1))),sy.PI(1));
console.log('Synergy constant','162',sy.Fe((sy.PI(162))),sy.PI(162));
console.log('Absolute Zero',sy.Fe(sy.PI(-273150)),sy.PI(-273150));
console.log('Fine-structure','11',sy.Fe((sy.PI(-403970.56335007225))),sy.PI(-403970.56335007225));
console.log('G','122403.7134932455',sy.Fe((sy.PI(-565518.0318314577))),sy.PI(-565518.0318314577));
console.log('kB','269134047524.10312',sy.Fe((sy.PI(-565532.550844023))),sy.PI(-565532.550844023));
console.log('----------------------------------------');
console.log("Level 1:", sy.Bcl(850))
console.log("Level sqrt(2):", sy.Bcl(Math.sqrt(2)))
console.log("Level sqrt(2):", sy.Bcl(Math.sqrt(3)))
console.log("Level 2:", sy.Bcl(2))
console.log('----------------------------------------');
console.log("Compton constant:", sy.Mx(2.42631023538e-12))
console.log("Compton constant:", sy.Ma(2663632677714545700))
*/
// SSM Log Outputs
/*
{
    id: 1,
        q: 1.118033988749895,
    'θx': 26.55875544251916,
    'θy': 63.44124455748084,
    'θv': 36.882489114961686,
    'θz': 126.88248911496169,
    'θu': 888.1774238047318,
    PNa: 296.55875544251916,
    PEa: 333.44124455748084,
    PNp: 951.6186683622127,
    PEp: 914.736179247251,
    PNd: 48.3813316377873,
    PEd: 85.26382075274898,
    Qc: 0.5674309597042945,
    Qa: 0.889388341373577,
    C: { cy: 3.3356409569522998e-9, cx: 3.3346460857225663e-9 },
    Z0: { cy: 376.73031658418466, cx: 376.617954924709 },
    'ε0': 8.854187757429692e-12,
    'μ0': 0.000001256637073723813,
    py: 29.979245755324857,
    px: 29.98818987962603,
    cy: 299792457.5532486,
    cx: 299881898.7962603
}
{
    q: 1.118033988749895,
        PHI: 1.618033988749895,
    phi: 0.6180339887498949,
    e: 2.7182755345913434,
    pi: 3.141592653589793,
    id: 2.2328054909414745,
    diff: 0.0032624865583152918
}
----------------------------------------
    Pi 3.1415926843095328
Quadrian Ratio 1.118033988749895
Golden Ratio 1.618033988749895
Golden Ratio Reciprocal 0.6180339887498949
Quadrian Euler e {
    q: 1.118033988749895,
        PHI: 1.618033988749895,
        phi: 0.6180339887498949,
        e: 2.7182755345913434,
        pi: 3.141592653589793,
        id: 2.2328054909414745,
        diff: 0.0032624865583152918
}
----------------------------------------
    Speed of Light (East) 299881898.7962603
Speed of Light (North) 299792457.5532486
Vacuum Permeability (μ0) 0.000001256637073723813
Vacuum Permittivity (ε0) 8.854187757429692e-12
Inertial Impedance* { cy: 3.3356409569522998e-9, cx: 3.3346460857225663e-9 }
Characteristic Impedance of Free Space (Z0) { cy: 376.73031658418466, cx: 376.617954924709 }
Electromagnetic Identity 1
----------------------------------------
    Fine-structure constant 0.007297352562786393
Gravitational constant G 6.674378179633154e-11
Kilogram Kn->(kg) 0.9999882861772882
Kilogram KN->(kg) 1
Atomic Unit 1.6605401706085603e-27
----------------------------------------
    Planck constants {
    h: 6.626987439910871e-34,
        hb: 1.0544157551953982e-34,
        tp: 5.390879110484635e-44,
        lp: 1.616144896904659e-35,
        mp: 2.176260547814635e-8,
        Tp: 1.4168508256452144e+32,
        qp: 1.87567584803208e-18
}
----------------------------------------
    Muon Magnetic Moment 9.21661203831769e-24
----------------------------------------
    Boltzmann 1.3804737918749321e-23
Avogadro 6.022140712033385e-23
eV 1.6021766626047706e-19
----------------------------------------
    Electron Mass 9.109027140565893e-31
Muon Mass 1.8855686180971397e-28
Proton Mass 1.6725825593709357e-27
Neutron Mass 1.6744043647990487e-27
Deuteron Mass 3.3421020578736265e-27
----------------------------------------
    Up Quark 3.683133494646168e-30
Down Quark 9.095084752085435e-30
Strange Quark 1.6877033007420074e-28
Charm Quark 1.4060023309919469e-27
Bottom Quark 4.456591528521863e-28
Top Quark 1.0548145629637546e-29
----------------------------------------
    Electron (νe) 6.889109655123751e-39
Muon (νμ) 9.157620220743223e-38
Tau (ντ) 3.508666751242614e-38
----------------------------------------
    Higgs Boson 2.2282957642609314e-25
W Strong Boson 1.4078912348458645e-25
Z Weak Boson 1.6043729502678705e-25
----------------------------------------
    Strong Force 2.4867644093744887e-28
Weak Force 1.4239959948303847e-25
----------------------------------------
    [H] - Hydrogen 1.66128139028063e-27
    [He] - Helium 6.646934072194125e-27
    [Li] - Lithium 1.1632586754107619e-26
    [Be] - Beryllium 1.4956053790204684e-26
    [B] - Boron 1.8279520826301743e-26
    [C] - Carbon 1.9940802216582374e-26
    [N] - Nitrogen 2.3264269252679435e-26
    [O] - Oxygen 2.65877362887765e-26
    [F] - Fluorine 3.1573388970689987e-26
    [Ne] - Neon 3.323467036097062e-26
    [Na] - Sodium 3.8220323042884116e-26
    [Mg] - Magnesium 3.988160443316475e-26
    [Al] - Aluminum 4.4867257115078246e-26
    [Si] - Silicon 4.652853850535887e-26
    [P] - Phosphorus 5.1514191187272375e-26
    [S] - Sulfur 5.3175472577553e-26
    [Cl] - Chlorine 5.81611252594665e-26
    [Ar] - Argon 6.647114923301284e-26
    [K] - Potassium 6.480805933166061e-26
    [Ca] - Calcium 6.646934072194124e-26
    [Sc] - Scandium 7.477936469548761e-26
    [Ti] - Titanium 7.97650173774011e-26
    [V] - Vanadium 8.475067005931458e-26
    [Cr] - Chromium 8.641195144959522e-26
    [Mn] - Manganese 9.139760413150872e-26
    [Fe] - Iron 9.305888552178935e-26
    [Co] - Cobalt 9.804453820370284e-26
    [Ni] - Nickel 9.804363394816705e-26
    [Cu] - Copper 1.063536579217134e-25
    [Zn] - Zinc 1.0801493931199403e-25
    [Ga] - Gallium 1.1632496328554037e-25
    [Ge] - Germanium 1.2131061596745387e-25
    [As] - Arsenic 1.2463408300355095e-25
    [Se] - Selenium 1.312819213312809e-25
    [Br] - Bromine 1.3294320272156152e-25
    [Kr] - Krypton 1.395910410492914e-25
    [Rb] - Rubidium 1.4125232243957207e-25
    [Sr] - Strontium 1.4623797512148554e-25
    [Y] - Yttrium 1.4789925651176617e-25
    [Zr] - Zirconium 1.5122272354786322e-25
    [Nb] - Niobium 1.5454619058396031e-25
    [Mo] - Molybdenum 1.595318432658738e-25
    [Tc] - Technetium 1.6285531030197086e-25
    [Ru] - Ruthenium 1.6784096298388436e-25
    [Rh] - Rhodium 1.7116443001998141e-25
    [Pd] - Palladium 1.761500827018949e-25
    [Ag] - Silver 1.7947354973799196e-25
    [Cd] - Cadmium 1.861213880657219e-25
    [In] - Indium 1.9110704074763538e-25
    [Sn] - Tin 1.9775487907536533e-25
    [Sb] - Antimony 2.027405317572788e-25
    [Te] - Tellurium 2.127127413766416e-25
    [I] - Iodine 2.110496514752894e-25
    [Xe] - Xenon 2.176974898030193e-25
    [Cs] - Cesium 2.2102095683911635e-25
    [Ba] - Barium 2.276687951668463e-25
    [La] - Lanthanum 2.3099226220294335e-25
    [Ce] - Cerium 2.3265354359322395e-25
    [Pr] - Praseodymium 2.343148249835046e-25
    [Nd] - Neodymium 2.393004776654181e-25
    [Pm] - Promethium 2.409617590556987e-25
    [Sm] - Samarium 2.492717830292451e-25
    [Eu] - Europium 2.525952500653422e-25
    [Gd] - Gadolinium 2.609052740388885e-25
    [Tb] - Terbium 2.6422874107498554e-25
    [Dy] - Dysprosium 2.7087657940271547e-25
    [Ho] - Holmium 2.7420004643881254e-25
    [Er] - Erbium 2.7752351347490966e-25
    [Tm] - Thulium 2.808469805110067e-25
    [Yb] - Ytterbium 2.874948188387366e-25
    [Lu] - Lutetium 2.908182858748337e-25
    [Hf] - Hafnium 2.9580393855674714e-25
    [Ta] - Tantalum 3.0078959123866064e-25
    [W] - Tungsten 3.0577524392057413e-25
    [Re] - Rhenium 3.0909871095667125e-25
    [Os] - Osmium 3.157465492844011e-25
    [Ir] - Iridium 3.190700163204982e-25
    [Pt] - Platinum 3.240556690024117e-25
    [Au] - Gold 3.2737913603850878e-25
    [Hg] - Mercury 3.3402697436623865e-25
    [Tl] - Thallium 3.390126270481522e-25
    [Pb] - Lead 3.4399827973006565e-25
    [Bi] - Bismuth 3.473217467661627e-25
    [Po] - Polonium 3.473208425106269e-25
    [At] - Astatine 3.4898212390090755e-25
    [Rn] - Radon 3.689274473951689e-25
    [Fr] - Francium 3.7058872878544957e-25
    [Ra] - Radium 3.7557438146736307e-25
    [Ac] - Actinium 3.772356628576437e-25
    [Th] - Thorium 3.8554568683119006e-25
    [Pa] - Protactinium 3.8388259692983777e-25
    [U] - Uranium 3.9551699219501706e-25
    [Np] - Neptunium 3.938539022936648e-25
    [Pu] - Plutonium 4.0548829755884406e-25
    [Am] - Americium 4.0382520765749186e-25
    [Cm] - Curium 4.1047304598522173e-25
    [Bk] - Berkelium 4.104721417296859e-25
    [Cf] - Californium 4.171199800574159e-25
    [Es] - Einsteinium 4.187812614476964e-25
    [Fm] - Fermium 4.270912854212429e-25
    [Md] - Mendelevium 4.287525668115234e-25
    [No] - Nobelium 4.30413848201804e-25
    [Lr] - Lawrencium 4.353995008837176e-25
    [Rf] - Rutherfordium 4.337364109823654e-25
    [Db] - Dubnium 4.353976923726459e-25
    [Sg] - Seaborgium 4.42045530700376e-25
    [Bh] - Bohrium 4.387202551532072e-25
    [Hs] - Hassium 4.470302791267536e-25
    [Mt] - Meitnerium 4.619890456835657e-25
    [Ds] - Darmstadtium 4.669746983654792e-25
    [Rg] - Roentgenium 4.702981654015762e-25
    [Cn] - Copernicium 4.736216324376733e-25
    [Nh] - Nihonium 4.752829138279539e-25
    [Fl] - Flerovium 4.802685665098675e-25
    [Mc] - Moscovium 4.835920335459645e-25
    [Lv] - Livermorium 4.869155005820616e-25
    [Ts] - Tennessine 4.885767819723422e-25
    [Og] - Oganesson 4.885758777168064e-25
----------------------------------------
    Sommerfeld {
    a: 0.9999999999999999,
        b: 1.0891511054947949,
        c: 1.4785973524257825,
        g: 1.414213562373095,
        f: 0.08915110549479503,
        e: 0.06566968684641475,
        d: 0.060294376524165944,
        FU: 0.08915110549479503
}
Wolfgang {
    a: 5.6084554109,
        b: 6.1084554109,
        c: 8.292647321754796,
        g: 7.9315537060595505,
        f: 0.5,
        e: 0.36830551052588345,
        d: 0.3381583222638005,
        FU: 0.5
}
Feynman {
    a: 11.2169108218,
        b: 12.2169108218,
        c: 16.58529464350959,
        g: 15.863107412119101,
        f: 1,
        e: 0.7366110210517669,
        d: 0.676316644527601,
        FU: 1
}
Newton {
    a: 122403.71349324551,
        b: 133316.1398678365,
        c: 180985.80669819686,
        g: 173104.9917069784,
        f: 10912.426374590998,
        e: 8038.213533939705,
        d: 7380.255589317877,
        FU: 10912.426374590998
}
Boltzmann {
    a: 269134047524.10312,
        b: 293127645387.16565,
        c: 397940890116.7737,
        g: 380613020104.9518,
        f: 23993597863.062504,
        e: 17673948620.615963,
        d: 16227269596.891047,
        FU: 23993597863.062504
}
----------------------------------------
    Joule 3864983.4319038160658266372422068 1.0000003733337912 0.4011229999899976
One 1 0.37067476711433983 1
Pi 0.06828291428647049 3.142487054628346
Synergy constant 162 0.06831511351345508 3.1415926843095328
Absolute Zero 0.021774838845128007 6.078276071317364
Fine-structure 11 0.007297352562786393 10.999999999999998
G 122403.7134932455 6.674300027060135e-11 122403.71349260675
kB 269134047524.10312 1.3805695689249107e-23 269135416479.06348
----------------------------------------
    Level 1: {
    L: 850,
        angles: {
        betaN: [ 13.574222444514662, -4.210023989656432 ],
            betaS: [ 13.574222444514662, -4.210023989656432 ],
            betaE: [ 14.577379737113251, 0 ]
    },
    octo: {
        Ne1: [ 5.337030282288433, 2.7313653785120935 ],
            Se1: [ 5.337030282288433, 2.7313653785120935 ],
            Sw1: [ 2.7313653785120935, 2.7313653785120935 ],
            Nw1: [ 2.7313653785120935, 5.337030282288433 ]
    },
    coords: {
        Ne: [ 7.460356830934512, 1.9539788869974513 ],
            Se: [ 1.9539788869974513, 1.9539788869974513 ],
            Sw: [ 1.9539788869974513, 7.460356830934512 ],
            Nw: [ 7.460356830934512, 7.460356830934512 ]
    },
    quads: {
        N1: [ 7.2886898685566255, 7.38129078246748 ],
            E1: [ 7.38129078246748, 7.2886898685566255 ],
            S1: [ 0.09260091391085426, 7.2886898685566255 ],
            W1: [ 7.2886898685566255, 0.09260091391085426 ]
    },
    shell: {
        N: [ 0.5, 14.577379737113251 ],
            E: [ 14.577379737113251, 0.5 ],
            S: [ 0.5, 0 ],
            W: [ 0, 0.5 ]
    }
}
Level sqrt(2): {
    L: 1.4142135623730951,
        angles: {
        betaN: [ -0.0977927394698227, 1.078343341425371 ],
            betaS: [ -0.0977927394698227, 1.078343341425371 ],
            betaE: [ 0.5946035575013605, 0 ]
    },
    octo: {
        Ne1: [ 0.7225904034885233, 0.8228777390769824 ],
            Se1: [ 0.7225904034885233, 0.8228777390769824 ],
            Sw1: [ 0.8228777390769824, 0.8228777390769824 ],
            Nw1: [ 0.8228777390769824, 0.7225904034885233 ]
    },
    coords: {
        Ne: [ 0.6771277734684463, 0.8781260801866497 ],
            Se: [ 0.8781260801866497, 0.8781260801866497 ],
            Sw: [ 0.8781260801866497, 0.6771277734684463 ],
            Nw: [ 0.6771277734684463, 0.6771277734684463 ]
    },
    quads: {
        N1: [ 0.29730177875068026, 0.7558038003530159 ],
            E1: [ 0.7558038003530159, 0.29730177875068026 ],
            S1: [ 0.4585020216023356, 0.29730177875068026 ],
            W1: [ 0.29730177875068026, 0.4585020216023356 ]
    },
    shell: {
        N: [ 0.5, 0.5946035575013605 ],
            E: [ 0.5946035575013605, 0.5 ],
            S: [ 0.5, 0 ],
            W: [ 0, 0.5 ]
    }
}
Level sqrt(2): {
    L: 1.7320508075688772,
        angles: {
        betaN: [ -0.12731936631787044, -1.7160349814216211 ],
            betaS: [ -0.12731936631787044, -1.7160349814216211 ],
            betaE: [ 0.6580370064762462, 0 ]
    },
    octo: {
        Ne1: [ 0.7698505932163339, 0.8547593679535334 ],
            Se1: [ 0.7698505932163339, 0.8547593679535334 ],
            Sw1: [ 0.8547593679535334, 0.8547593679535334 ],
            Nw1: [ 0.8547593679535334, 0.7698505932163339 ]
    },
    coords: {
        Ne: [ 0.7306135771043237, 0.9006635341821544 ],
            Se: [ 0.9006635341821544, 0.9006635341821544 ],
            Sw: [ 0.9006635341821544, 0.7306135771043237 ],
            Nw: [ 0.7306135771043237, 0.7306135771043237 ]
    },
    quads: {
        N1: [ 0.3290185032381231, 0.7648612746739909 ],
            E1: [ 0.7648612746739909, 0.3290185032381231 ],
            S1: [ 0.43584277143586786, 0.3290185032381231 ],
            W1: [ 0.3290185032381231, 0.43584277143586786 ]
    },
    shell: {
        N: [ 0.5, 0.6580370064762462 ],
            E: [ 0.6580370064762462, 0.5 ],
            S: [ 0.5, 0 ],
            W: [ 0, 0.5 ]
    }
}
Level 2: {
    L: 2,
        angles: {
        betaN: [ -0.13378963406716704, -0.11986687707796942 ],
            betaS: [ -0.13378963406716704, -0.11986687707796942 ],
            betaE: [ 0.7071067811865476, 0 ]
    },
    octo: {
        Ne1: [ 0.8052451659746271, 0.8781260801866497 ],
            Se1: [ 0.8052451659746271, 0.8781260801866497 ],
            Sw1: [ 0.8781260801866497, 0.8781260801866497 ],
            Nw1: [ 0.8781260801866497, 0.8052451659746271 ]
    },
    coords: {
        Ne: [ 0.7711054127039705, 0.9170040432046712 ],
            Se: [ 0.9170040432046712, 0.9170040432046712 ],
            Sw: [ 0.9170040432046712, 0.7711054127039705 ],
            Nw: [ 0.7711054127039705, 0.7711054127039705 ]
    },
    quads: {
        N1: [ 0.3535533905932738, 0.7740015982201311 ],
            E1: [ 0.7740015982201311, 0.3535533905932738 ],
            S1: [ 0.4204482076268573, 0.3535533905932738 ],
            W1: [ 0.3535533905932738, 0.4204482076268573 ]
    },
    shell: {
        N: [ 0.5, 0.7071067811865476 ],
            E: [ 0.7071067811865476, 0.5 ],
            S: [ 0.5, 0 ],
            W: [ 0, 0.5 ]
    }
}
*/
