// Interactive atom grids for the `diagrams` detail cards. A card whose label
// has a `Mol` (see `mol_for`) shows the formula, a mass bar and a bonded atom
// grid with a movable cursor above its text. Neighbours of the atom under the
// cursor light up and the pane below explains it.
//
// To add one: build a `Mol` (atoms on a char grid, bonds as index pairs) and
// match its card label in `mol_for`.

use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};

use crate::ui::theme::Theme;

#[derive(Clone, Copy, PartialEq)]
pub enum El {
    Si,
    O,
    H,
    Cl,
    B,
    P,
    C,
    Ar,
}

impl El {
    fn label(self) -> &'static str {
        match self {
            El::Si => "Si",
            El::O => "O",
            El::H => "H",
            El::Cl => "Cl",
            El::B => "B",
            El::P => "P",
            El::C => "C",
            El::Ar => "Ar",
        }
    }

    fn width(self) -> u16 {
        self.label().len() as u16
    }

    fn mass(self) -> f64 {
        match self {
            El::Si => 28.09,
            El::O => 16.00,
            El::H => 1.008,
            El::Cl => 35.45,
            El::B => 10.81,
            El::P => 30.97,
            El::C => 12.01,
            El::Ar => 39.95,
        }
    }

    pub fn style(self, t: &Theme) -> Style {
        let fg = match self {
            El::Si => return t.accent().add_modifier(Modifier::BOLD),
            El::O => Color::Cyan,
            El::H => return t.base().add_modifier(Modifier::BOLD),
            El::Cl => Color::Green,
            El::B => Color::Magenta,
            El::P => Color::Yellow,
            El::C => Color::Gray,
            El::Ar => Color::LightMagenta,
        };
        Style::new().fg(fg).add_modifier(Modifier::BOLD)
    }
}

pub struct Atom {
    pub el: El,
    pub row: u16,
    pub col: u16,
    pub info: &'static str,
}

/// Text segment, coloured by element when `Some`, dim otherwise.
type Seg = (&'static str, Option<El>);

pub struct Mol {
    pub atoms: Vec<Atom>,
    pub bonds: Vec<(usize, usize)>,
    /// Header formula, e.g. `SiO` `₂`.
    pub formula: Vec<Seg>,
    /// Atom ratio, e.g. `1 Si : 2 O`.
    pub ratio: Vec<Seg>,
    pub reaction: &'static str,
    /// Formula-unit composition for the mass bar.
    pub comp: Vec<(El, u32)>,
}

fn atom(el: El, row: u16, col: u16, info: &'static str) -> Atom {
    Atom { el, row, col, info }
}

const SI_INFO: &str = "Silicon. 4 bonds, one to each corner oxygen. Each of those oxygens is shared with a neighbouring Si, so this Si owns only 4 x 1/2 = 2 O. That is the 1:2 in SiO2. Mass 28.";
const BRIDGE_INFO: &str = "Oxygen, bridging. 2 bonds, one to each Si it sits between, so each Si counts half of it. Si-O is about 1.61 A and very strong, which is why quartz melts near 1700 C and the furnace needs so much power. Mass 16.";
const EDGE_INFO: &str = "Oxygen at the edge of this sketch. It bonds the Si shown here and a second Si off-screen, where the network keeps going. Quartz has no SiO2 molecules, only this repeating network. Mass 16.";
const CORNER_INFO: &str = "Oxygen, bridging. One bond is to the Si on screen, the other goes up or down out of this flat slice into the 3D network (each Si has 4 O in a tetrahedron). Shared by 2 Si. Mass 16.";

/// Quartz SiO2: two flat-projected Si, each with 4 O; the middle O is shared.
fn quartz() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 8, SI_INFO),
        atom(Si, 2, 21, SI_INFO),
        atom(O, 0, 8, CORNER_INFO),
        atom(O, 4, 8, CORNER_INFO),
        atom(O, 0, 21, CORNER_INFO),
        atom(O, 4, 21, CORNER_INFO),
        atom(O, 2, 2, EDGE_INFO),
        atom(O, 2, 15, BRIDGE_INFO),
        atom(O, 2, 28, EDGE_INFO),
    ];
    let bonds = vec![
        (0, 2),
        (0, 3),
        (0, 6),
        (0, 7),
        (1, 4),
        (1, 5),
        (1, 7),
        (1, 8),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![("SiO", Some(Si)), ("₂", Some(O))],
        ratio: vec![("1 Si", Some(Si)), (" : ", None), ("2 O", Some(O))],
        reaction: "SiO₂ + 2C ──▶ Si + 2CO",
        comp: vec![(Si, 1), (O, 2)],
    }
}

const TCS_SI: &str = "Silicon at the centre, bonded to 3 Cl and 1 H. Unlike quartz this is a real molecule, not a network, so it is small and volatile. Mass 28.";
const TCS_H: &str = "Hydrogen. The only H on the molecule. Mass 1, so almost no weight, but it is what lets the Si-H form that H2 later reduces.";
const TCS_CL: &str = "Chlorine. Heavy: 3 Cl make up about 79% of the molecule's mass. On the hot rod at ~1100 C they leave as HCl and the Si stays behind. Mass 35.";

/// Trichlorosilane SiHCl3: the gas that carries silicon to the bell jar.
fn tcs() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 8, TCS_SI),
        atom(H, 2, 2, TCS_H),
        atom(Cl, 0, 8, TCS_CL),
        atom(Cl, 4, 8, TCS_CL),
        atom(Cl, 2, 15, TCS_CL),
    ];
    Mol {
        atoms,
        bonds: vec![(0, 1), (0, 2), (0, 3), (0, 4)],
        formula: vec![("SiHCl", None), ("₃", None)],
        ratio: vec![
            ("1 Si", Some(Si)),
            (" : ", None),
            ("1 H", Some(H)),
            (" : ", None),
            ("3 Cl", Some(Cl)),
        ],
        reaction: "SiHCl₃ + H₂ ──▶ Si + 3HCl",
        comp: vec![(Si, 1), (H, 1), (Cl, 3)],
    }
}

// LOAD card: substitutional B (p-type) and P (n-type) sitting in Si lattice sites.
// Sources: k0 B 0.8 / As 0.3 (US 9,634,098), P 0.35 (US 9,580,327, US 7,811,356),
// Si 5e22 atoms/cm3 (Berkeley EE105), Si-Si 2.35 A / 109.5 deg (MicroChemicals),
// ionization B 45, P 44, As 54 meV (Chenming Hu ch1 slides), 4.6 ohm-cm at 1e15
// (BYU cleanroom calculator, Masetti 1983).

const DOP_B: &str = "Boron, substitutional p-type dopant. Only 3 valence electrons, so of its 4 bonds to Si one is missing an electron: a hole. It costs only ~45 meV to set that hole free, so at room temperature nearly every B gives one. k0 = 0.8, so B freezes in almost as fast as it arrives: resistivity stays fairly even along the ingot. Mass 11.";
const DOP_P: &str = "Phosphorus, substitutional n-type dopant. 5 valence electrons: 4 make the bonds to Si, the 5th is held by only ~44 meV and roams free at room temperature. k0 = 0.35 (arsenic is similar at 0.3), so the crystal takes only about a third of what the melt holds and the rest piles up in the liquid. Mass 31.";
const DOP_SI_W: &str = "Silicon at the edge of this sketch; the lattice keeps going off-screen. A crystal holds about 5e22 Si atoms per cm3. Every Si here has 4 neighbours, each sharing one pair of electrons, which is why pure Si conducts so poorly: no electron is left over. Mass 28.";
const DOP_SI_BN: &str = "Silicon bonded to the boron. The real bonds point to the corners of a tetrahedron, 109.5 degrees apart, flattened here into a cross. The Si-Si spacing is 2.35 A, and B is small enough to sit in a Si site without any extra bonds. Mass 28.";
const DOP_SI_BS: &str = "Silicon bonded to the boron. Its bond to B is short one electron. A neighbouring electron hops in to fill it, and the gap moves on: the hole drifts through the lattice as a positive carrier, while B is left as a fixed negative ion. Mass 28.";
const DOP_SI_MID: &str = "Silicon between both dopants, drawn bonded to B and to P. Real doping is far thinner: 1e15 dopants in 5e22 Si per cm3 is 1 per 5e7 Si, so dopants sit ~100 nm apart. If B and P met in one crystal they would cancel (compensation). Mass 28.";
const DOP_SI_PN: &str = "Silicon bonded to the phosphorus. All 4 of its electrons go into normal pairs, one of them shared with P. P's 5th electron fits no bond, so it drifts away as a negative carrier, leaving P as a fixed positive ion. Mass 28.";
const DOP_SI_PS: &str = "Silicon bonded to the phosphorus. Since P's k0 is 0.35, the melt gets richer in P as the crystal grows (Scheil equation, textbook), so later Si sites take in more P. The tail ends up more heavily doped and lower in resistivity than the head. Mass 28.";
const DOP_SI_E: &str = "Silicon at the edge of the sketch. Why one dopant per ~5e7 Si matters: at 1e15 per cm3 the resistivity is about 4.6 ohm-cm (BYU calculator, varies by dopant), and the dose loaded with the charge sets it for the whole ingot. Mass 28.";

/// Substitutional dopants: B (p-type) and P (n-type), each in a Si site with 4 Si neighbours.
fn dopants() -> Mol {
    use El::*;
    let atoms = vec![
        atom(B, 2, 9, DOP_B),
        atom(P, 2, 22, DOP_P),
        atom(Si, 2, 2, DOP_SI_W),
        atom(Si, 2, 15, DOP_SI_MID),
        atom(Si, 2, 28, DOP_SI_E),
        atom(Si, 0, 9, DOP_SI_BN),
        atom(Si, 4, 9, DOP_SI_BS),
        atom(Si, 0, 22, DOP_SI_PN),
        atom(Si, 4, 22, DOP_SI_PS),
    ];
    let bonds = vec![
        (0, 2),
        (0, 3),
        (0, 5),
        (0, 6),
        (1, 3),
        (1, 4),
        (1, 7),
        (1, 8),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![
            ("Si", Some(Si)),
            (":B", Some(B)),
            (" / ", None),
            ("Si", Some(Si)),
            (":P", Some(P)),
        ],
        ratio: vec![
            ("1 B", Some(B)),
            (" : ", None),
            ("1 P", Some(P)),
            (" : ", None),
            ("7 Si", Some(Si)),
        ],
        reaction: "melt + dopant ──▶ Si:B (k0 0.8), Si:P (k0 0.35)",
        comp: vec![(Si, 7), (B, 1), (P, 1)],
    }
}

// Sources for the numbers below:
//   SiO attacks graphite, CO back-diffuses: https://ecs.confex.com/ecs/226/webprogram/Paper39706.html ;
//     https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4956153 (0.5 ppma breakdown limit)
//   graphite -> SiC surface: https://patents.google.com/patent/US9212431 ; https://patents.google.com/patent/US6221478 (SiO at ~1410 C)
//   Ar 50-200 L/min, 20-80 kPa: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12297560
//   Ar 100 L/min, 1200 Pa: https://www.researching.cn/ArticlePdf/m00098/2020/41/10/102702.pdf
//   Ar 100 L/min, 2500 Pa: https://www.comsol.com/blogs/thermal-analysis-of-a-czochralski-crystal-growth-furnace
//   C < 2e14 /cm3, poly ~5e14: https://www.scientific.net/SSP.242.3 ; FT-IR limit ~1e15: US 10,355,092
//   SGL SIGRAFINE hot zone ~1500 C: https://www.sglcarbon.com/en/markets-solutions/material/sigrafine-isostatic-graphite/
//   Toyo Tanso isotropic graphite since 1974: https://www.toyotanso.co.jp/introduction/products_en.html

const HZ_SIO_SI: &str = "Silicon in SiO gas. The melt dissolves the quartz crucible (SiO2 + Si -> 2SiO, textbook) and SiO boils off from about 1410 C (US 6,221,478). Here its Si is grabbing one graphite C below it: that C will leave as SiC. Mass 28.";
const HZ_SIO_O: &str = "Oxygen in SiO gas. Bonded to the Si beside it, and reaching down for the second graphite C. O + C leave together as CO gas, the main carbon carrier into the crystal (US 4,956,153). One SiO eats 2 C atoms of heater. Mass 16.";
const HZ_GR_SI: &str = "Graphite carbon of the heater/susceptor, bonded in a flat sp2 sheet (textbook). The Si of SiO lands here and turns this C into SiC. This is how hot-zone parts get a SiC skin that can flake off (US 9,212,431), so they are consumables. Mass 12.";
const HZ_GR_O: &str = "Graphite carbon, second of the 2C. The O of SiO takes this one away as CO, so the heater literally erodes. SGL SIGRAFINE isostatic graphite hot zones run near 1500 C (SGL); Toyo Tanso has mass-produced isotropic graphite since 1974. Mass 12.";
const HZ_SIC_SI: &str = "Silicon now locked in SiC, one bond to the C below in this sketch (4 in the real tetrahedral crystal, textbook). SiC stays on the graphite as a solid crust; it does not reach the melt but changes the part's shape and heat flow. Mass 28.";
const HZ_SIC_C: &str = "Carbon in SiC, the first product. Graphite part mass is lost into this crust and into CO; patents describe susceptor walls thinning until they crack and let the crucible bulge (US 6,221,478). Mass 12.";
const HZ_CO_C: &str = "Carbon in CO gas, the second product. Bonded to one O (a triple bond, textbook). If argon does not sweep it out, CO back-diffuses into the melt (ECS 2014). Reported to peak during meltdown, when the hot zone is hottest (Kyushu review). Mass 12.";
const HZ_CO_O: &str = "Oxygen in CO. It came from the crucible via SiO. Higher argon flow above the melt raises CO evaporation in both melting and growth (Trans Tech, SSP 242). So the gas recipe is also a carbon-control knob. Mass 16.";
const HZ_MELT_SI: &str = "Silicon of the melt/crystal lattice. Each Si has 4 neighbours (textbook); here one of them is a carbon from dissolved CO. Pure Si has about 5e22 atoms per cm3 (textbook), so 1 ppma is about 5e16 /cm3. Mass 28.";
const HZ_SUB_C: &str = "Substitutional carbon: CO dissolved in the melt and froze in, C sitting on a Si site. Above 0.5 ppma (about 2.5e16 /cm3) p-n breakdown voltage can suffer (US 4,956,153). GlobalWafers grew CZ under 2e14 /cm3; poly feed holds ~5e14. Mass 12.";
const HZ_AR_TOP: &str = "Argon, no bonds: a noble gas with a full outer shell (textbook). It reacts with nothing, so it is the sweep gas. One patent runs 50-200 L/min at 20-80 kPa (150-600 Torr); a 2020 study 100 L/min at 1200 Pa (about 9 Torr). Mass 40.";
const HZ_AR_MID: &str = "Argon flowing past the gap between crystal and heat shield, carrying SiO and CO out the exhaust before they meet graphite or fall back. More flow and lower pressure lift SiO off the melt and cut oxygen (2020 study). COMSOL model: 100 L/min at 2500 Pa. Mass 40.";
const HZ_AR_OUT: &str = "Argon at the exhaust, still unbonded. It is pumped out with the SiO and CO it carries; in pressure terms the 2500 Pa COMSOL case is about 19 Torr (1 Torr = 133 Pa, textbook). A 2020 study found raising argon flow effectively inhibits CO and its back-diffusion into the melt. Mass 40.";

/// Hot zone: SiO from the melt eats graphite (SiO + 2C -> SiC + CO); CO
/// back-dissolves as substitutional carbon; argon sweeps the gases out.
fn hot_zone_carbon() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 2, HZ_SIO_SI),   // 0 SiO
        atom(O, 2, 9, HZ_SIO_O),     // 1 SiO
        atom(C, 4, 2, HZ_GR_SI),     // 2 graphite
        atom(C, 4, 9, HZ_GR_O),      // 3 graphite
        atom(Si, 2, 24, HZ_SIC_SI),  // 4 SiC
        atom(C, 4, 24, HZ_SIC_C),    // 5 SiC
        atom(C, 2, 37, HZ_CO_C),     // 6 CO
        atom(O, 2, 43, HZ_CO_O),     // 7 CO
        atom(Si, 8, 30, HZ_MELT_SI), // 8 lattice
        atom(C, 8, 37, HZ_SUB_C),    // 9 substitutional C
        atom(Si, 8, 43, HZ_MELT_SI), // 10 lattice
        atom(Ar, 0, 16, HZ_AR_TOP),  // 11
        atom(Ar, 6, 24, HZ_AR_MID),  // 12
        atom(Ar, 0, 50, HZ_AR_OUT),  // 13
    ];
    let bonds = vec![
        (0, 1),
        (0, 2),
        (1, 3),
        (2, 3),
        (4, 5),
        (6, 7),
        (8, 9),
        (9, 10),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![("SiO", Some(Si)), (" + ", None), ("2C", Some(C))],
        ratio: vec![
            ("1 Si", Some(Si)),
            (" : ", None),
            ("1 O", Some(O)),
            (" : ", None),
            ("2 C", Some(C)),
        ],
        reaction: "SiO + 2C ──▶ SiC + CO",
        comp: vec![(Si, 1), (O, 1), (C, 2)],
    }
}

// Interstitial oxygen (Oi) in the Si lattice, for the MELT + PULL "Oxygen" card.
// Sources: arxiv.org/pdf/mtrl-th/9504001 (bond-centre site, 1.563 A);
// patents.google.com/patent/USH520 (12-18 ppma, bulk 12-16 ppma);
// patents.google.com/patent/US4545849 (1.6e18 cm-3 = about 32 ppma; SiO evaporation);
// patents.google.com/patent/US4010064 (oxygen falls as crucible dissolution slows);
// SEMI MF1188 (1107 cm-1 band); core.ac.uk/works/140288043 + Cambridge JMR (450 C thermal
// donors, 2-5 O cores; C suppresses them); ecs.confex.com/ecs/aimes2018/webprogram/Paper113734.html
// (Oi strengthens vs slip, bulk precipitates getter metals); image-ppubs 6503594 (precipitates pin
// slip dislocations); image-ppubs 7397110 (carbon >= 0.5e16 vs BMD strength loss);
// jstage jjacg vol 26 (segregation coefficient 0.8 +- 0.1).

const OI_O: &str = "Interstitial oxygen (Oi). It sits in a puckered bond-centre site along <111>, wedged into what was a Si-Si bond, with 2 bonds, one to each Si. CZ bulk typically holds 12-16 ppma (patent), about 6-8e17 /cm3 on the 32 ppma = 1.6e18 scale. FTIR reads it from the 1107 cm-1 band (SEMI MF1188). Mass 16.";
const OI_SI_L: &str = "Silicon bonded to the Oi. It keeps 4 bonds: 3 to Si and 1 to O instead of its old Si neighbour. Si-O is shorter than Si-Si, about 1.56 A in one modelling study versus 2.35 A (textbook), so the O pushes the two Si apart and puckers off-axis to fit. Mass 28.";
const OI_SI_R: &str = "Silicon on the other side of the Si-O-Si bridge. Hold the crystal near 450 C and mobile Oi gather into small clusters (models fit cores of 2-5 O) that act as thermal donors, adding electrons that shift resistivity. Carbon is known to suppress them. Mass 28.";
const OI_SI_EDGE: &str = "Ordinary lattice silicon: 4 Si-Si bonds of 2.35 A in the diamond lattice, about 5e22 atoms per cm3 (textbook). Against that, 14 ppma of oxygen is roughly 1 O for every 70,000 Si, a trace that still decides wafer strength and gettering. Mass 28.";
const OI_SI_SRC: &str = "Lattice silicon, frozen from the melt. Its oxygen came from the crucible: SiO2 + Si(l) gives 2SiO. A large portion of that SiO evaporates from the melt surface and is swept off by argon (patent); the rest reaches the interface and freezes in, with a segregation coefficient near 0.8 +- 0.1 in one study. Mass 28.";
const OI_SI_UP_L: &str = "Lattice silicon above the bridge, bonded out of this flat slice into the 3D network. In later anneals, supersaturated Oi clusters into SiO2 precipitates (bulk micro defects). Bulk precipitates act as gettering sinks that trap metal impurities away from the device surface (ECS 2018 abstract). Mass 28.";
const OI_SI_DN_L: &str = "Lattice silicon below the bridge. Oi and oxide precipitates pin dislocations, so a slip line is less likely to run during hot fab steps (patent: oxide precipitates pin slip). That is why low-oxygen float-zone silicon is mechanically weaker in big wafers (textbook). Mass 28.";
const OI_SI_UP_R: &str = "Lattice silicon, read along the crystal length. A standard crucible gives 12-18 ppma (patent), and oxygen falls from seed end to tail as the crucible dissolves more slowly and melt contact shrinks (patents). Rotation and magnetic fields are scheduled to flatten that drift. Mass 28.";
const OI_SI_DN_R: &str = "Lattice silicon in the device zone. Here oxygen is a villain: precipitates in the active area degrade devices (ECS 2018 abstract). Wafer makers therefore aim for a near-surface zone free of precipitates over a bulk that keeps them, a denuded zone (textbook). Mass 28.";
const OI_C: &str = "Carbon on a substitutional site, bonded to 4 Si (1 shown). It comes from the graphite hot zone, where SiO + C makes CO. Carbon changes how oxygen precipitates: one patent dopes C at about 0.5e16 /cm3 or more to stop large precipitates lowering wafer strength. Mass 12.";

/// Interstitial oxygen: an O in a bond-centred site between two Si, in a Si lattice.
fn oxy_interstitial() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 2, OI_SI_EDGE),  // 0
        atom(Si, 2, 9, OI_SI_L),     // 1
        atom(O, 2, 16, OI_O),        // 2
        atom(Si, 2, 22, OI_SI_R),    // 3
        atom(Si, 2, 29, OI_SI_SRC),  // 4
        atom(Si, 0, 9, OI_SI_UP_L),  // 5
        atom(Si, 4, 9, OI_SI_DN_L),  // 6
        atom(Si, 0, 22, OI_SI_UP_R), // 7
        atom(Si, 4, 22, OI_SI_DN_R), // 8
        atom(C, 4, 29, OI_C),        // 9
    ];
    let bonds = vec![
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (1, 5),
        (1, 6),
        (3, 7),
        (3, 8),
        (4, 9),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![
            ("Si-", Some(Si)),
            ("O", Some(O)),
            ("-Si", Some(Si)),
            (" (Oi)", None),
        ],
        ratio: vec![("1 O", Some(O)), (" : ", None), ("~70,000 Si", Some(Si))],
        reaction: "SiO₂(crucible) + Si(l) ──▶ 2SiO",
        comp: vec![(Si, 2), (O, 1)],
    }
}

// Sources for the numbers below:
//   lattice 5.431 A, 5.0e22 atoms/cm3, 109.5 deg: pv-manufacturing.org/solar-cell-manufacturing/silicon-crystallograpy/ ;
//     tricor.readthedocs.io/en/latest/examples/silicon/index.html
//   8 atoms/cell, 2.33 g/cm3: faculty-web.msoe.edu/johnsontimoj/CE3101/files3101/silicon_crystal_structure.pdf
//   bond 2.35 A = a*sqrt(3)/4 = 2.352 A (geometry from a = 5.431 A)
//   1414 C, 1826 J/g: link.springer.com/article/10.1007/s10973-019-08716-5
//   50.21 kJ/mol: en.wikipedia.org/wiki/Enthalpy_of_fusion
//   melt ~10% denser, metallic: patent US 6,800,540 ; link.aps.org/accepted/10.1103/PhysRevB.97.140103
//   melt coordination 5.5-6: arxiv.org/pdf/1201.0401
//   1e18 O/cm3, 9.9 kg/h, 1403-1407.5 C: MELT_PULL.details.txt (Wikipedia, COMSOL)

const SIL_A: &str = "Silicon inside the crystal. 4 bonds, the full diamond-cubic set: left, right, up toward the seed, down toward the melt, each 2.35 A long at 109.5 deg in 3D (flattened here). Every neighbour is in its exact lattice spot, which is what single crystal means.";
const SIL_B: &str = "Silicon, a second lattice site 2 bonds along. Same 4 bonds as its twin on the left. The pattern repeats every 5.431 A (the cubic cell edge), and one cell holds 8 atoms, so the solid packs 5.0e22 Si per cm3. Mass 28.09.";
const SIL_UP_L: &str = "Silicon one layer up, frozen earlier. Its other 3 bonds run off this slice into the 3D network. Every layer above copies the orientation of the seed ({100} or {111}), so the whole ingot is one crystal with the seed's orientation.";
const SIL_UP_R: &str = "Silicon one layer up, nearer the seed and cooler. On {100} the atomic layers are a/4 = 1.36 A apart, so at 1.0 mm/min about 4e8 layers freeze per hour (60 mm / 1.36 A, arithmetic), each copying the one below.";
const SIL_IF_L: &str = "Silicon at the growth interface, the newest layer. Bonded up into the crystal but facing the melt below. Joining releases the latent heat, 50.21 kJ/mol (about 1826 J/g measured), which the puller must conduct away up the crystal.";
const SIL_IF_R: &str = "Silicon at the interface, just locked into place. The front sits at the freezing point, 1414 C, held by the heater: the card's model puts the seed contact at 1403-1407.5 C. Too cold and the front speeds up and traps defects.";
const SIL_EDGE_L: &str = "Silicon at the left edge of this slice. It bonds the Si shown here and continues off-screen: a 300 mm crystal is about 5.5e8 lattice cells across (300 mm / 5.431 A, arithmetic). One wrong bond anywhere starts a dislocation.";
const SIL_MID: &str = "Silicon shared between the two centre atoms, like the bridging O in quartz but Si-Si, all covalent. Each atom owns half of each of its 4 bonds, so pure Si has 2 bonds per atom. Mass 28.09, 100% of the formula.";
const SIL_EDGE_R: &str = "Silicon at the right edge, linking on to more lattice off-screen. Solid silicon is an open structure, only 2.33 g/cm3, because 4 tetrahedral bonds leave lots of empty space. That openness is why it shrinks when it melts.";
const MELT_A: &str = "Silicon in the melt, no fixed bonds. Liquid Si averages about 5.5-6 near neighbours instead of 4, so it packs tighter: the melt is about 10% denser than the crystal. Ice works the same way (textbook), so the crystal would float.";
const MELT_B: &str = "Silicon right under the interface, waiting to join. On melting Si turns metallic, so the liquid conducts electricity well. That is why a horizontal or cusp magnetic field can grip the melt and damp its convection.";
const MELT_C: &str = "Silicon in the melt, carried by convection from the hot crucible wall to the cool crystal. When it freezes it expands about 10% (patent US 6,800,540), the reverse of most metals, so the crystal is the lighter phase.";
const MELT_D: &str = "Silicon deep in the melt near the crucible. Each mole that freezes must shed 50.21 kJ, so at 9.9 kg/h (1.0 mm/min, 300 mm) the interface releases about 5 kW of latent heat (9900 g/h x 1826 J/g, arithmetic).";
const MELT_O: &str = "Oxygen dissolved in the melt, from the quartz crucible: SiO2 + Si ──▶ 2SiO. Most leaves as SiO gas swept by argon, but some freezes in at about 1e18 atoms per cm3, roughly 1 O per 50,000 Si (5.0e22 / 1e18, arithmetic). Mass 16.";

/// Diamond-cubic Si above a disordered melt: the Czochralski growth front.
fn si_lattice() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 9, SIL_A),
        atom(Si, 2, 23, SIL_B),
        atom(Si, 0, 9, SIL_UP_L),
        atom(Si, 0, 23, SIL_UP_R),
        atom(Si, 4, 9, SIL_IF_L),
        atom(Si, 4, 23, SIL_IF_R),
        atom(Si, 2, 2, SIL_EDGE_L),
        atom(Si, 2, 16, SIL_MID),
        atom(Si, 2, 30, SIL_EDGE_R),
        atom(Si, 6, 4, MELT_A),
        atom(Si, 6, 16, MELT_B),
        atom(Si, 6, 27, MELT_C),
        atom(Si, 8, 10, MELT_D),
        atom(O, 8, 22, MELT_O),
    ];
    let bonds = vec![
        (0, 2),
        (0, 4),
        (0, 6),
        (0, 7),
        (1, 3),
        (1, 5),
        (1, 7),
        (1, 8),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![("Si", Some(Si))],
        ratio: vec![("1 Si", Some(Si)), (" : ", None), ("4 bonds", None)],
        reaction: "Si(l) ──▶ Si(crystal) + heat",
        comp: vec![(Si, 1)],
    }
}

// Sources: US 7,226,508 ; US 9,593,432 ; US 11,466,381 ; US 11,821,103 ;
// US 4,010,064 ; US 6,302,957 ; Cz crucible patents (1817 K flow point, graphite
// susceptor) ; arXiv 1109.2852 (a-SiO2 angle) ; Mauri et al. PRB 62 R4786 (2000) ;
// https://en.wikipedia.org/wiki/High-purity_quartz (BNEF ~80%) ;
// https://en.wikipedia.org/wiki/Czochralski_method (1e18 O/cm3) ;
// J. Jpn. Assoc. Cryst. Growth vol 26 (sessile-drop triple junction).

const CW_GLASS_SI: &str = "Silicon in the fused-silica body of the crucible. Same 4 O as quartz, but glass: no long-range order. The feed is high-purity quartz, mostly from Spruce Pine, NC (Sibelco, The Quartz Corp), which supplied about 80% of the HPQ used by PV and chip makers in 2024 (BNEF via Wikipedia). Mass 28.";
const CW_NET_O: &str = "Oxygen, bridging up into the 3D glass net. In fused silica the Si-O-Si angle is spread out, about 141.5 +/- 12.5 deg in one study, while crystalline silica sits nearer 157 deg (Mauri et al., PRB 2000). That disorder is what separates this glass from the quartz grains on the SAND page. Mass 16.";
const CW_BULK_O: &str = "Oxygen in the bulk wall. Glass has no sharp melting point, it just gets runnier: above about 1400 C its viscosity drops so far that a crucible can buckle or collapse inward during the pull (US 11,821,103). The wall is only held in shape by the graphite outside it. Mass 16.";
const CW_OUTER_O: &str = "Oxygen on the outer face, resting on the graphite. No bond crosses that gap: the glass just sits in the susceptor cup. Where they touch, hot SiO2 and C can react to SiO and CO (textbook), so the outside wears too and adds carbon risk to the hot zone. Mass 16.";
const CW_C: &str = "Carbon, the graphite susceptor. Not part of the crucible but the rigid cup holding it: one patent says vitreous silica flows easily under stress above 1817 K (about 1544 C), close to the 1414 C Si melt (textbook). Graphite does not flow at growth temperatures and is chosen for strength, inertness and cleanliness (patent text). Mass 12.";
const CW_BRIDGE_O: &str = "Oxygen, bridging the bulk glass to the inner wall layer. Si-O is about 1.61 A and very strong (textbook), so the wall dissolves slowly. Makers fuse a bubble-free inner layer of 80 um to 4 mm (US 9,593,432) so no trapped bubbles burst into the melt as the wall wears back. Mass 16.";
const CW_WALL_SI: &str = "Silicon on the inner wall. In contact with the melt the glass slowly devitrifies to cristobalite, seen as brown rings. If a cristobalite flake peels off and reaches the crystal it causes dislocations (US 11,466,381), so a uniform, continuous cristobalite shell is wanted. Mass 28.";
const CW_BA_O: &str = "Oxygen at the coated face. A devitrification promoter, usually barium hydroxide (US 7,226,508), is applied so cristobalite nucleates everywhere at once as a continuous beta-cristobalite shell (US 9,593,432). Catch: Ba(OH)2 picks up CO2 from air as BaCO3, so the dose is hard to control. Mass 16.";
const CW_COOL_O: &str = "Oxygen in the wall at shutdown. The crucible is normally single use: leftover melt freezes, and the thermal-expansion mismatch between Si and silica cracks the crucible on cooling (patent text). A reuse patent (US 6,302,957) notes crucibles are a large share of crystal cost, yet reuse was not established. Mass 16.";
const CW_WALL_O: &str = "Oxygen at the wall, the one under attack. Molten Si pulls it out: SiO2 + Si -> 2SiO (textbook), the source of oxygen in CZ silicon. A sessile-drop study found dissolution fastest where melt, glass and argon meet, and faster crucible rotation raises wall-to-melt mass transfer (patent text). Mass 16.";
const CW_MELT_SI: &str = "Silicon, liquid, held just above its 1414 C melting point (textbook). It wets the wall and reduces the silica, taking an O to become SiO. Liquid Si is metallic, so its bonds are fleeting. As the melt level falls the wetted wall area shrinks, so less oxygen enters late in the pull (patent text). Mass 28.";
const CW_AR: &str = "Argon above the free melt surface. Inert, so it bonds to nothing. Its job is to sweep evaporating SiO away; evaporation depends on argon pressure and flow rate (2025 study, J. Chin. Ceram. Soc.). The wall dissolves fastest at the triple line of melt, silica and argon (sessile-drop study). Mass 40.";
const CW_SIO_SI: &str = "Silicon in silicon monoxide, the product: one SiO2 plus one Si gives 2 SiO. Most SiO leaves as gas from the free melt surface and only a small fraction freezes into the crystal (patent text). Downstream it meets hot graphite and makes CO. Mass 28.";
const CW_SIO_O: &str = "Oxygen carried by SiO. The part that does not evaporate ends up interstitial in the crystal, about 1e18 atoms per cm3 (Wikipedia). That oxygen strengthens wafers and getters metals but can precipitate into defects, so the crucible wall sets a key wafer spec. Mass 16.";

/// Crucible wall: graphite | fused SiO2 glass | inner (cristobalite) wall | Si(l), with SiO leaving.
fn crucible_wall() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 12, CW_GLASS_SI),
        atom(Si, 2, 25, CW_WALL_SI),
        atom(O, 0, 12, CW_NET_O),
        atom(O, 4, 12, CW_BULK_O),
        atom(O, 0, 25, CW_BA_O),
        atom(O, 4, 25, CW_COOL_O),
        atom(O, 2, 6, CW_OUTER_O),
        atom(O, 2, 19, CW_BRIDGE_O),
        atom(O, 2, 32, CW_WALL_O),
        atom(Si, 2, 38, CW_MELT_SI),
        atom(C, 2, 0, CW_C),
        atom(Ar, 0, 46, CW_AR),
        atom(Si, 6, 46, CW_SIO_SI),
        atom(O, 6, 53, CW_SIO_O),
    ];
    let bonds = vec![
        (0, 2),
        (0, 3),
        (0, 6),
        (0, 7),
        (1, 4),
        (1, 5),
        (1, 7),
        (1, 8),
        (8, 9),
        (12, 13),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![
            ("SiO", Some(Si)),
            ("₂", Some(O)),
            (" | ", None),
            ("Si(l)", Some(Si)),
        ],
        ratio: vec![("1 SiO₂", Some(O)), (" : ", None), ("1 Si", Some(Si))],
        reaction: "SiO₂ + Si ──▶ 2SiO",
        // Mass of the reacting pair SiO2 + Si (= 2 SiO).
        comp: vec![(Si, 2), (O, 2)],
    }
}

pub fn mol_for(label: &str) -> Option<Mol> {
    match label.trim() {
        "QUARTZITE" => Some(quartz()),
        "SiHCl3 + H2" => Some(tcs()),
        "LOAD" => Some(dopants()),
        "GRAPHITE HEATER" => Some(hot_zone_carbon()),
        "Oxygen" => Some(oxy_interstitial()),
        "MOLTEN SILICON" => Some(si_lattice()),
        "QUARTZ CRUCIBLE" => Some(crucible_wall()),
        _ => None,
    }
}

impl Mol {
    pub fn neighbours(&self, cur: usize) -> Vec<usize> {
        self.bonds
            .iter()
            .filter_map(|&(a, b)| match (a == cur, b == cur) {
                (true, _) => Some(b),
                (_, true) => Some(a),
                _ => None,
            })
            .collect()
    }

    /// Nearest atom in direction (dx, dy). Terminal cells are about twice as
    /// tall as wide, so rows count triple to keep "nearest" visually honest.
    pub fn step(&self, cur: usize, dx: i32, dy: i32) -> usize {
        let c = &self.atoms[cur];
        let (cx, cy) = (c.col as i32, c.row as i32 * 3);
        self.atoms
            .iter()
            .enumerate()
            .filter(|(i, _)| *i != cur)
            .filter_map(|(i, a)| {
                let (ddx, ddy) = (a.col as i32 - cx, a.row as i32 * 3 - cy);
                let (along, across) = if dx != 0 {
                    (ddx * dx, ddy.abs())
                } else {
                    (ddy * dy, ddx.abs())
                };
                (along > 0).then_some((along + 2 * across, i))
            })
            .min()
            .map_or(cur, |(_, i)| i)
    }

    /// The atom grid as styled lines. Cursor atom is inverted, its neighbours
    /// and the bonds touching it are bold.
    pub fn lines(&self, cur: usize, t: &Theme) -> Vec<Line<'static>> {
        let w = self
            .atoms
            .iter()
            .map(|a| a.col + a.el.width())
            .max()
            .unwrap_or(0) as usize
            + 1;
        let h = self.atoms.iter().map(|a| a.row).max().unwrap_or(0) as usize + 1;
        // (char, style) per cell
        let mut grid: Vec<Vec<(char, Style)>> = vec![vec![(' ', t.base()); w]; h];
        let near = self.neighbours(cur);
        let bond_on = t.accent().add_modifier(Modifier::BOLD);
        for &(a, b) in &self.bonds {
            let (pa, pb) = (&self.atoms[a], &self.atoms[b]);
            let style = if a == cur || b == cur {
                bond_on
            } else {
                t.border()
            };
            if pa.row == pb.row {
                let (l, r) = if pa.col < pb.col { (pa, pb) } else { (pb, pa) };
                for x in l.col + l.el.width() + 1..r.col - 1 {
                    grid[l.row as usize][x as usize] = ('─', style);
                }
            } else {
                let (u, d) = if pa.row < pb.row { (pa, pb) } else { (pb, pa) };
                for y in u.row + 1..d.row {
                    grid[y as usize][u.col as usize] = ('│', style);
                }
            }
        }
        for (i, a) in self.atoms.iter().enumerate() {
            let style = if i == cur {
                t.on_cursor(a.el.style(t))
            } else if near.contains(&i) {
                a.el.style(t).add_modifier(Modifier::UNDERLINED)
            } else {
                a.el.style(t)
            };
            for (k, ch) in a.el.label().chars().enumerate() {
                grid[a.row as usize][a.col as usize + k] = (ch, style);
            }
        }
        grid.into_iter()
            .map(|row| {
                Line::from(
                    row.into_iter()
                        .map(|(c, s)| Span::styled(c.to_string(), s))
                        .collect::<Vec<_>>(),
                )
            })
            .collect()
    }
}

fn segs(segs: &[Seg], t: &Theme) -> Vec<Span<'static>> {
    segs.iter()
        .map(|&(text, el)| match el {
            Some(e) => Span::styled(text, e.style(t)),
            None => Span::styled(text, t.title()),
        })
        .collect()
}

impl Mol {
    /// `SiO₂   =   1 Si : 2 O      SiO₂ + 2C ──▶ Si + 2CO` with element colours.
    pub fn formula_line(&self, t: &Theme) -> Line<'static> {
        let mut spans = segs(&self.formula, t);
        spans.push(Span::styled("   =   ", t.dim()));
        spans.extend(segs(&self.ratio, t).into_iter().map(|mut s| {
            if s.content.trim() == ":" {
                s.style = t.dim();
            }
            s
        }));
        spans.push(Span::styled(format!("      {}", self.reaction), t.dim()));
        Line::from(spans)
    }

    /// Mass share bar from the composition.
    pub fn mass_line(&self, t: &Theme) -> Line<'static> {
        const W: usize = 30;
        let total: f64 = self.comp.iter().map(|&(e, n)| e.mass() * n as f64).sum();
        let mut spans = vec![Span::styled("mass  ", t.dim())];
        let mut label = String::new();
        let mut used = 0usize;
        for (k, &(e, n)) in self.comp.iter().enumerate() {
            let frac = e.mass() * n as f64 / total;
            let cells = if k + 1 == self.comp.len() {
                W - used
            } else {
                (frac * W as f64).round() as usize
            };
            used += cells;
            spans.push(Span::styled("█".repeat(cells), e.style(t)));
            label.push_str(&format!("  {} {:.0}%", e.label(), frac * 100.0));
        }
        spans.push(Span::styled(label, t.dim()));
        Line::from(spans)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quartz_grid_shape() {
        let t = Theme::default();
        let m = quartz();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  O ─── Si ─── O ─── Si ─── O");
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.step(0, 1, 0), 7);
    }

    #[test]
    fn tcs_and_mass() {
        let t = Theme::default();
        let m = tcs();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  H ─── Si ─── Cl");
        let bar: String = m
            .mass_line(&t)
            .spans
            .iter()
            .map(|s| s.content.as_ref())
            .collect();
        println!("{bar}");
        assert!(bar.contains("Si 21%") && bar.contains("Cl 79%"));
        assert_eq!(
            m.mass_line(&t)
                .spans
                .iter()
                .filter(|s| s.content.contains('█'))
                .map(|s| s.content.chars().count())
                .sum::<usize>(),
            30
        );
    }

    #[test]
    fn dopants_grid() {
        let t = Theme::default();
        let m = dopants();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  Si ─── B ─── Si ─── P ─── Si");
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.neighbours(1).len(), 4);
        assert_eq!(m.step(0, 1, 0), 3);
    }

    #[test]
    fn hot_zone_carbon_grid() {
        let t = Theme::default();
        let m = hot_zone_carbon();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows.len(), 9);
        assert_eq!(
            rows[2].trim_end(),
            "  Si ─── O              Si           C ─── O"
        );
        assert_eq!(
            rows[8].trim_end(),
            format!("{}Si ─── C ─── Si", " ".repeat(30))
        );
        assert_eq!(m.neighbours(0).len(), 2);
        assert!(m.neighbours(11).is_empty());
        assert_eq!(m.step(0, 1, 0), 1);
    }

    #[test]
    fn oxy_interstitial_grid() {
        let t = Theme::default();
        let m = oxy_interstitial();
        let rows: Vec<String> = m
            .lines(2, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows.len(), 5);
        assert_eq!(rows[0].trim_end(), "         Si           Si");
        assert_eq!(rows[1].trim_end(), "         │            │");
        assert_eq!(rows[2].trim_end(), "  Si ─── Si ─── O ─── Si ─── Si");
        assert_eq!(rows[3].trim_end(), "         │            │      │");
        assert_eq!(rows[4].trim_end(), "         Si           Si     C");
        assert_eq!(m.neighbours(2).len(), 2);
        assert_eq!(m.neighbours(1).len(), 4);
        assert_eq!(m.step(2, 1, 0), 3);
    }

    #[test]
    fn si_lattice_grid() {
        let t = Theme::default();
        let m = si_lattice();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  Si ─── Si ─── Si ─── Si ─── Si");
        assert_eq!(rows[3].trim_end(), "         │             │");
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.neighbours(9).len(), 0);
        assert_eq!(m.step(0, 1, 0), 7);
    }

    #[test]
    fn crucible_wall_grid() {
        let t = Theme::default();
        let m = crucible_wall();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(
            rows[2].trim_end(),
            "C     O ─── Si ─── O ─── Si ─── O ─── Si"
        );
        assert_eq!(rows[6].trim_end(), format!("{}Si ─── O", " ".repeat(46)));
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.neighbours(1).len(), 4);
        assert_eq!(m.step(0, 1, 0), 7);
    }
}
