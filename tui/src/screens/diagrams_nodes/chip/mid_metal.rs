// CHIP tab, MID METAL (tools/pbr3d/blender/chip_mid_metal.py). The overview opens and closes on the
// whole-chip scene (chip_kit.py) and in between works on a detailed cut-away of the M5-M9 wiring
// (chip_mid_metal_detail.py), with signal beads riding the copper. Zoom-ins a-e and sections 1-10
// are cut-aways too (docs/diagram-pages.md): zooms are 3 beats, sections 3 or 4.
//
// Sources: tui/src/screens/diagrams_pages/CHIP_MID_METAL.txt and .details.txt (IBM copper history
// and resistivity study; Intel 4 and TSMC N5 and N3E node notes; low-k modulus, patent text; Intel
// IEDM 2024; Lienig EM slides; Applied and Lam filings; textbook RC).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the middle tier: M5-M9", BEAT_MS)
        .note(
            "Between the thin cell wiring and the thick top levels sit five medium levels, M5-M9. They carry signals from block to block across the chip.",
            "The whole chip, the middle tier lit violet between the thin wiring below and the thick top tier and bumps above.",
        )
        .detail(
            "Medium wires for reach between blocks.",
            &["M5-M9 medium copper for block signals (CHIP_MID_METAL.txt, section 1)"],
        ),
    Beat::new("five levels in cut-away", BEAT_MS)
        .note(
            "Cut open, each level is a layer of copper wires in low-k dielectric, sealed by a thin cap. Alternate levels run at right angles, and vias connect a wire to the one above or below.",
            "Rows of copper cross-sections alternating with long copper bars, vertical vias between them, a pale green cap on every level, and a few cyan signals moving.",
        )
        .detail(
            "Five passes of the dual-damascene loop.",
            &["M5-M9: five passes, each about 4-6 tool visits (CHIP_MID_METAL.txt, section 1)"],
        ),
    Beat::new("a short hop", BEAT_MS)
        .note(
            "A signal climbs a via from an M6 line onto an M7 wire and travels one block over. On a short wire the resistance and capacitance are small, so it arrives almost at once.",
            "Cyan beads rising through a via into the M7 copper bar and running a short way along it.",
        )
        .detail(
            "Short wires are fast.",
            &["Wire delay ~ R x C, and both grow with length (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("a long run", BEAT_MS)
        .note(
            "The same signal sent along the full length of an M5 wire takes far longer. Resistance and capacitance both grow with length, so delay grows roughly with length squared.",
            "Cyan beads dropping a via onto the long M5 bar at the bottom and crawling slowly to its far end.",
        )
        .detail(
            "Twice the length, about four times the delay.",
            &["RC ~ L^2 (CHIP_MID_METAL.txt, section 3); the timing here is schematic"],
        ),
    Beat::new("R and C on one wire", BEAT_MS)
        .note(
            "Close on one wire: its resistance comes from the narrow copper itself, and its capacitance from the wires around it, here the M6 lines just below, across a thin layer of low-k.",
            "The M7 wire glowing orange for its resistance, with blue electron beads in it, and yellow bands down to the M6 lines for the capacitance.",
        )
        .detail(
            "Wire width sets R; spacing and k set C.",
            &["R = rho L / (W H); C grows with k and H/S (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("long runs climb to the top", BEAT_MS)
        .note(
            "The longest connections leave the middle tier and climb to the thick top levels, where the resistance per micron is lowest.",
            "The whole chip again, the thick top tier lit amber above the middle tier.",
        )
        .detail(
            "Each tier has its job.",
            &["M10-M14: thick copper for power, clock and global wires (CHIP_MID_METAL.txt, section 3)"],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

// ---- zoom-ins a-e -----------------------------------------------------------------------------

// a is section 1's pass from the etch on; d is section 6 seen from the other side.
const ZA_BEATS: &[Beat] = SEC1_BEATS.split_at(1).1;

const ZB_BEATS: &[Beat] = &[
    Beat::new("R: the copper itself", BEAT_MS)
        .note(
            "A wire's resistance is R = rho x L / (W x H): it grows with length and falls with width and height. At tens of nanometres wide, a mid-level wire has real resistance per micron.",
            "The long M7 wire at the top glowing orange, with blue electron beads moving through it.",
        )
        .detail(
            "Narrow copper resists.",
            &[
                "R = rho L / (W H) (CHIP_MID_METAL.txt, section 3)",
                "About 2.0 uOhm-cm in wide lines, over 3.0 below ~60 nm (IBM study)",
            ],
        ),
    Beat::new("C: through the low-k", BEAT_MS)
        .note(
            "The wire also stores charge against its neighbours: the M6 lines below it through the via-level dielectric, and side by side within a level. Every transition has to charge that capacitance through the wire's resistance.",
            "Yellow bands from the M7 wire down to each M6 line, and more yellow between the M6 lines.",
        )
        .detail(
            "Low-k cuts C.",
            &["C grows with k and with H/S (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("delay ~ L^2", BEAT_MS)
        .note(
            "Because R and C both grow with length, the delay of an unbuffered wire grows roughly with its length squared. A short hop is quick; the long wire is many times slower, so long runs get repeaters or move to thicker metal.",
            "Cyan beads crawling the full M7 wire at the top while a quick stream crosses a short stretch of M5 at the bottom.",
        )
        .detail(
            "The reason levels get fatter going up.",
            &["Delay ~ rho k eps0 L^2 / (W S) (CHIP_MID_METAL.txt, section 3)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("porous low-k", BEAT_MS)
        .note(
            "The film between the wires is a carbon-doped oxide filled with pores to bring k down toward 2.5 and below. Lower k means less capacitance, but the film gets soft: a 58% porous CDO is down to about 3 GPa.",
            "Dark pores packed into the dielectric between the copper lines.",
        )
        .detail(
            "Lower k, softer film.",
            &[
                "CDO k ~2.7: 7-10 GPa; 58% porous CDO: 3 GPa (CHIP_MID_METAL.txt, section 5)",
                "SiO2: k ~4.0, 72 GPa",
            ],
        ),
    Beat::new("air gaps", BEAT_MS)
        .note(
            "The lowest k of all is nothing: the film between lines is etched out and the cap bridges over the gap. Air gaps cut capacitance by 25% or more, but add no strength.",
            "Dark empty gaps between the copper lines, with the pale green cap spanning over them.",
        )
        .detail("k about 1.", &["Air gap: capacitance down 25% or more (CHIP_MID_METAL.txt, section 5)"]),
    Beat::new("etched ruthenium", BEAT_MS)
        .note(
            "At the tightest pitches, ruthenium lines are etched out of a blanket film instead of copper being filled into trenches. Ru needs no barrier, and the gaps between lines can be left as air.",
            "Blue-grey ruthenium lines with no barrier, dark air gaps between them, and a cap over the top.",
        )
        .detail(
            "Below about 20 nm pitch.",
            &["Subtractive Ru with air gap, -25% line-line C (Intel, IEDM 2024)"],
        ),
];

const ZD_BEATS: &[Beat] = SEC6_BEATS;

const ZE_BEATS: &[Beat] = &[
    Beat::new("a via on target", BEAT_MS)
        .note(
            "A via is printed by its own exposure, so it has to line up with the line below. Landed where planned, its whole foot sits on copper: low resistance and plenty of margin to the next line.",
            "A copper via dropping from the long M7 wire onto an M6 line, its foot glowing green across the full width of the line.",
        )
        .detail(
            "Overlay is the budget.",
            &["Overlay budget about 1/4 of the pitch at 70 nm and below (CHIP_MID_METAL.txt, section 7)"],
        ),
    Beat::new("edge placement error", BEAT_MS)
        .note(
            "If overlay and size errors add up, the via lands partly off its line. Less of its foot touches copper, so resistance and current density rise, and its edge creeps toward the neighbouring line, risking a short.",
            "The via shifted right, a red patch where its foot hangs over the dielectric, and the thin gap left to the next line.",
        )
        .detail(
            "A small shift, a big risk.",
            &["Misaligned via: narrower contact, higher R, short or EM risk (patent 11916010)"],
        ),
    Beat::new("RC extraction", BEAT_MS)
        .note(
            "Before tape-out, every wire's resistance and its capacitance to its neighbours are extracted from the layout and fed to timing sign-off, so delays like these are known for every net. Synopsys StarRC and Cadence Quantus are the standard tools.",
            "The M7 wire glowing orange for its resistance with electron beads in it, and yellow bands between the M6 lines for capacitance.",
        )
        .detail("Software for every wire.", &["Synopsys StarRC (SNPS), Cadence Quantus (CDNS)"]),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "one dual-damascene pass",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "RC delay",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "low-k, air gaps and ruthenium",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "electromigration",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "vias, edge placement and RC extraction",
        build: zoom_e,
    },
];

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_d.glb"),
        ZD_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_e.glb"),
        ZE_BEATS,
    )
}

// ---- sections 1-10 ---------------------------------------------------------------------------

const SEC1_BEATS: &[Beat] = &[
    Beat::new("deposit: low-k film on the etch stop", BEAT_MS)
        .note(
            "Each wiring level starts as a blank film. A thin SiCN etch stop already covers the level below; a low-k dielectric (a carbon-doped oxide) is deposited on it, then a TiN hard mask that will hold the pattern during the etch.",
            "The copper bar of M5 at the bottom, the pale green etch stop on it, the grey-blue low-k film growing upward, and the dark grey TiN mask landing on top.",
        )
        .detail(
            "Every level of M5-M9 repeats this loop.",
            &[
                "M5-M9: five passes, each about 4-6 tool visits (CHIP_MID_METAL.txt, section 1)",
                "Etch stop and cap: SiCN or SiN",
            ],
        ),
    Beat::new("pattern and etch: trench and via", BEAT_MS)
        .note(
            "Lithography and a plasma etch cut a trench for each wire and, under some of them, a deeper hole for the via that will reach M5. The hard mask protects the film between the trenches.",
            "The purple plasma glow in the openings, then grey-blue fins of low-k standing between empty trenches, and two narrow via holes reaching down to the M5 bar.",
        )
        .detail(
            "Dual damascene: trench and via in one film.",
            &[
                "Trench and via etched through one hard mask (CHIP_MID_METAL.txt, section 1)",
                "The via opens through the etch stop onto M5 copper",
            ],
        ),
    Beat::new("barrier, liner, then copper", BEAT_MS)
        .note(
            "A few-nanometre TaN/Ta barrier and a Ru or Co liner coat the trench walls so copper cannot diffuse into the dielectric. Copper then electroplates from the bottom up, filling via and trench in one step and piling up as excess on top.",
            "Dark blue U-shaped barrier shells first, then copper filling them and the two via columns, and a copper slab growing across the top.",
        )
        .detail(
            "One fill for via and trench.",
            &[
                "Barrier/liner TaN/Ta and Ru by PVD, ALD or CVD (CHIP_MID_METAL.txt, section 1)",
                "Bottom-up electroplating; barrier drawn thicker than life",
            ],
        ),
    Beat::new("CMP and cap, then the next level", BEAT_MS)
        .note(
            "Chemical-mechanical polishing grinds off the excess copper and stops on the dielectric, leaving each wire separate. A SiCN cap then seals the copper, and the next level is built on top. Five passes make M5 to M9.",
            "The dark CMP pad sweeping across, the copper slab gone, five separate copper lines left in the low-k, and a pale green cap over them.",
        )
        .detail(
            "Polish flat, seal, repeat.",
            &[
                "CMP strips the excess and stops on the dielectric (CHIP_MID_METAL.txt, section 1)",
                "CAP+REPEAT: SiCN/SiN cap, then the next level",
            ],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("one copper line in section", BEAT_MS)
        .note(
            "Cut across, a wire is a copper rectangle wrapped on three sides by a liner and a barrier; the cap closes the fourth side. At tens of nanometres wide, those few-nanometre layers take a real share of the cross-section, and they conduct far worse than copper.",
            "A copper rectangle with a thin pale liner inside a dark blue barrier, its neighbours either side, and grey-blue low-k between them.",
        )
        .detail(
            "The barrier keeps copper out of the dielectric.",
            &[
                "Barrier/liner: TaN/Ta plus Ru or Co (CHIP_MID_METAL.txt, section 1)",
                "Barrier and liner are a few nm thick (drawn thicker here)",
            ],
        ),
    Beat::new("via and line: one copper fill", BEAT_MS)
        .note(
            "In dual damascene the via and the line above it are plated as one piece, so each level needs one fill and one CMP. The barrier coats the via walls but not its foot, so the via's copper touches the copper below directly.",
            "A copper column rising from an M6 line into the M7 wire above, and the green glow at the via foot where copper meets copper.",
        )
        .detail(
            "Fewer steps, lower via resistance.",
            &[
                "One plating step and one CMP per level (CHIP_MID_METAL.txt, section 2)",
                "No barrier at the via bottom",
            ],
        ),
    Beat::new("the cap between levels", BEAT_MS)
        .note(
            "A thin SiCN or SiN cap seals the top of every level and is the etch stop for the next. Its k is higher than the low-k around it, so it adds capacitance; thinner caps and selective metal caps are used to cut that.",
            "The bright yellow band along the cap on top of M6, and the same pale green layer on top of every other level.",
        )
        .detail(
            "Needed, but it costs capacitance.",
            &[
                "SiCN k ~4.5-5 against ULK ~2.5 (typical values, estimate)",
                "Thinner and selective metal caps cut capacitance (CHIP_MID_METAL.txt, section 2)",
            ],
        ),
    Beat::new("ultra-low-k between the lines", BEAT_MS)
        .note(
            "The film between wires is ultra-low-k: a carbon-doped oxide made porous so it stores less charge. Lower k means less capacitance between neighbours and faster signals, but a softer, more fragile film.",
            "Dark pores dotted through the grey-blue dielectric between the copper lines and in the via layer above them.",
        )
        .detail(
            "Lower k, faster wires.",
            &["ULK k ~2.5 or below; SiO2 ~4.0 (CHIP_MID_METAL.txt, section 5)"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("RC: thin, medium and thick levels", BEAT_MS)
        .note(
            "A wire's delay grows roughly with its resistance times its capacitance, and both scale with length. Thin lower wires have the most resistance per micron, so a signal crawls along them; thick top wires let it race. That is why levels get fatter going up.",
            "One block with three tiers: tiny M2-M3 lines at the bottom, M6-M7 in the middle, big M12-M13 on top, and cyan signal dots crossing slowly on the thin wire and fast on the thick one.",
        )
        .detail(
            "Each tier trades density for speed.",
            &[
                "Delay ~ R x C = rho k eps0 L^2 / (W S) (CHIP_MID_METAL.txt, section 3)",
                "Thin M1-M4 have the highest R per micron",
            ],
        ),
    Beat::new("C: mostly line to line", BEAT_MS)
        .note(
            "In a dense level most of a wire's capacitance is to the wires beside it. It grows with the dielectric's k and with how tall the wires are compared with the gap, so making wires taller to cut R also raises C.",
            "Yellow bands filling the gaps between the M6 copper lines: the line-to-line capacitance.",
        )
        .detail(
            "R and C pull against each other.",
            &["C grows with k and with H/S; R falls with W x H (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("the size effect", BEAT_MS)
        .note(
            "Copper's resistivity rises as lines narrow: electrons scatter off grain boundaries and surfaces, and the barrier takes a bigger share of the cross-section. Thin lines conduct well below what bulk copper would suggest.",
            "The thin M2 lines glowing orange at the bottom, the wider M6 lines above them in plain copper.",
        )
        .detail(
            "Narrow copper is worse copper.",
            &[
                "About 2.0 uOhm-cm in wide lines (IBM study)",
                "Over 3.0 uOhm-cm below about 60 nm width (IBM study)",
            ],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("Intel 7 and Intel 4 pitches", BEAT_MS)
        .note(
            "Each level has its own pitch, the centre-to-centre spacing of its wires. Published points: Intel 7 M2 at 44 nm and M4 at 52 nm by DUV multipatterning; Intel 4 M2 and M4 at 45 nm, with EUV for some metal and via layers.",
            "Three copper gratings stacked up, each with a glowing bar spanning one pitch: Intel 7 M2 at the bottom, Intel 7 M4 in the middle, Intel 4 M2 on top.",
        )
        .detail(
            "Published points, not full tables.",
            &[
                "Intel 7 M2/M4: 44/52 nm, DUV multipatterning (WikiChip, AnandTech)",
                "Intel 4 M2/M4: 45 nm, EUV for some layers",
            ],
        ),
    Beat::new("TSMC N3E M0: 23 nm, one EUV shot", BEAT_MS)
        .note(
            "At TSMC N3E the tightest metal, M0, is 23 nm pitch, printed in a single EUV exposure. N3B used EUV double patterning on three layers: two exposures that each print every other line and must line up with each other.",
            "The lower grating in plain copper (one exposure) and the upper one with alternate lines tinted orange and blue (two exposures).",
        )
        .detail(
            "EUV vs multipatterning is a per-level choice.",
            &[
                "N3E M0: 23 nm, EUV single pattern; N3B: 3 layers EUV double (SemiAnalysis)",
                "TSMC N5 Mx about 30% tighter than N7",
            ],
        ),
    Beat::new("Intel IEDM 2024: etched Ru", BEAT_MS)
        .note(
            "At 25 nm pitch and below, Intel showed ruthenium lines etched out of a blanket film instead of copper filled into trenches. Ru needs no barrier, and the spaces between lines can be left as air gaps, which cut line-to-line capacitance by about 25%.",
            "Blue-grey ruthenium lines with no barrier, dark air gaps between them, and a cap bridging over the top.",
        )
        .detail(
            "A different way to make the tightest wires.",
            &["Subtractive Ru with air gap, -25% line-line capacitance (Intel, IEDM 2024)"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("SiO2: stiff, k 4.0", BEAT_MS)
        .note(
            "Plain silicon dioxide was the original film between wires. It is stiff and tough, but its k of about 4.0 means high capacitance between neighbouring wires.",
            "Pale solid SiO2 between the copper lines, and the tall grey bar on the right for its stiffness.",
        )
        .detail("The stiff baseline.", &["SiO2: k ~4.0, modulus 72 GPa (CHIP_MID_METAL.txt, section 5)"]),
    Beat::new("carbon-doped oxide: k 2.7", BEAT_MS)
        .note(
            "Adding carbon to the oxide lowers k to about 2.7, cutting capacitance by about a third. The film gets far softer, which makes polishing and packaging stress harder to survive.",
            "A darker blue film with a few pores between the lines, and a short second bar next to the SiO2 one.",
        )
        .detail(
            "Lower k, much softer.",
            &[
                "CDO k ~2.7: 7-10 GPa (CHIP_MID_METAL.txt, section 5)",
                "Intel patent target: k 2.5 or less at 15 GPa",
            ],
        ),
    Beat::new("porous CDO: 3 GPa", BEAT_MS)
        .note(
            "Making the film porous lowers k further, at a price: a 58% porous CDO is down to about 3 GPa, and films below k 2 are at least half pores. Stiffness falls by about ten times as k drops by a third.",
            "The dielectric full of dark pores, and a third bar barely above the base.",
        )
        .detail(
            "Soft films crack and absorb damage.",
            &["58% porous CDO: 3 GPa; spin-on k below 2.0: 1-3 GPa (CHIP_MID_METAL.txt, section 5)"],
        ),
    Beat::new("air gap: no dielectric at all", BEAT_MS)
        .note(
            "The limit is to etch the film out between lines and leave air, k about 1. The cap bridges over the gap. Air gaps cut capacitance by 25% or more, but the gap carries no mechanical load.",
            "Dark empty gaps between the copper lines, and the pale green cap spanning over them.",
        )
        .detail("The lowest k possible.", &["Air gap: capacitance down 25% or more (CHIP_MID_METAL.txt, section 5)"]),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("the electron wind", BEAT_MS)
        .note(
            "Electrons flowing at high current density push on the copper atoms. The atoms drift the same way as the electrons, fastest along the weakest path: the interface between the copper and its cap.",
            "Blue electron dots running along the M7 wire from the via on the left, and small orange copper atoms creeping along its top edge under the cap.",
        )
        .detail(
            "The slow wear-out of every wire.",
            &["EM drift runs along the Cu/cap interface (CHIP_MID_METAL.txt, section 6)"],
        ),
    Beat::new("a void and a hillock", BEAT_MS)
        .note(
            "Where atoms leave faster than they arrive, a void opens, usually just past the via where the current enters, and the wire's resistance climbs until it fails open. Downstream the atoms pile into a hillock that can crack the cap. Black's equation gives the lifetime.",
            "A black void opening in the wire beside the left via, a copper hillock pushing up through the cap on the right, and the wire glowing hot.",
        )
        .detail(
            "Lifetime falls steeply with current and heat.",
            &[
                "MTTF = A x J^-n x exp(Ea / kT), n often ~2 (Black's equation)",
                "Cu Ea ~0.7-1.1 eV vs Al 0.5-0.7 eV",
            ],
        ),
    Beat::new("caps that hold the copper", BEAT_MS)
        .note(
            "The fix is a stronger top interface. A cobalt cap, or CoWP or Ru, bonds to copper better than SiCN does, so the atoms drift far more slowly. Mn or Co liners and copper reflow help too.",
            "A bright blue-silver cobalt layer along the top of the wire, and only a few orange atoms moving.",
        )
        .detail("Caps and liners buy lifetime.", &["Fixes: CoWP, Co or Ru caps; Mn or Co liners; Cu reflow (CHIP_MID_METAL.txt, section 6)"]),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("a via on target", BEAT_MS)
        .note(
            "A via is printed by its own exposure, so it has to line up with the line below. Landed where planned, its whole foot sits on copper: low resistance and plenty of margin to the next line.",
            "A copper via dropping from the long M7 wire onto an M6 line, its foot glowing green across the full width of the line.",
        )
        .detail(
            "Overlay is the budget.",
            &["Overlay budget about 1/4 of the pitch at 70 nm and below (CHIP_MID_METAL.txt, section 7)"],
        ),
    Beat::new("edge placement error", BEAT_MS)
        .note(
            "If overlay and size errors add up, the via lands partly off its line. Less of its foot touches copper, so resistance and current density rise, and its edge creeps toward the neighbouring line, risking a short.",
            "The via shifted right, a red patch where its foot hangs over the dielectric, and the thin gap left between it and the next line.",
        )
        .detail(
            "A small shift, a big risk.",
            &["Misaligned via: narrower contact, higher R, short or EM risk (patent 11916010)"],
        ),
    Beat::new("self-aligned vias", BEAT_MS)
        .note(
            "With self-aligned vias the line grating sets the via's edges: the opening is drawn wider than needed and trimmed to the line it lands on. Below about 20 nm pitch, etched ruthenium is expected to replace damascene copper.",
            "The wide yellow opening at the top of the via, and the copper via under it exactly the width of its line.",
        )
        .detail(
            "Let the lines do the aligning.",
            &[
                "Self-aligned via: the line edges set the via edge (CHIP_MID_METAL.txt, section 7)",
                "Below ~20 nm pitch: subtractive Ru, no barrier",
            ],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("the tools for each layer", BEAT_MS)
        .note(
            "Every step of the loop has its tool makers. Applied Materials deposits the low-k (Black Diamond) and the barrier and seed (Endura, with Ru CVD); Lam Research plates the copper (SABRE); Applied and Ebara polish it; Tokyo Electron also sells deposition and etch.",
            "Tags on the grey-blue low-k, the dark barrier, the copper and the top cap of a three-level cut-away.",
        )
        .detail(
            "Fabs: TSMC (TSM), Intel (INTC), Samsung (005930.KS).",
            &[
                "AMAT: Endura, Black Diamond; LRCX: SABRE (CHIP_MID_METAL.txt, section 8)",
                "TEL (8035.T), Ebara (6361.T)",
            ],
        ),
    Beat::new("RC extraction", BEAT_MS)
        .note(
            "Before tape-out, every wire's resistance and its capacitance to its neighbours are extracted from the layout and fed to timing sign-off. Synopsys StarRC and Cadence Quantus are the standard extraction tools.",
            "An orange glow along an M7 wire for its resistance, and yellow bands between the M6 lines for capacitance.",
        )
        .detail("Software for every wire.", &["Synopsys StarRC (SNPS), Cadence Quantus (CDNS)"]),
    Beat::new("Applied: 30% from China", BEAT_MS)
        .note(
            "Applied Materials' fiscal 2025 revenue was $28,368M, and 30% of it, $8,529M, came from China. That exposure is a risk if export rules tighten.",
            "A tall copper bar for Applied's total revenue and a short glowing bar for China, beside the stack.",
        )
        .detail(
            "The biggest supplier's China exposure.",
            &["AMAT FY2025: $28,368M revenue, $8,529M (30%) China (AMAT FY2025 annual report)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("the copper resistance wall", BEAT_MS)
        .note(
            "At about 20 nm pitch a copper line is only about 10 nm wide, and the barrier and liner, which do not shrink with it, take most of that width. Ruthenium needs no barrier, so the tightest levels are moving to Ru.",
            "Top row: tiny copper cores inside thick dark barriers. Bottom row: solid blue-grey Ru lines with dark air gaps between them.",
        )
        .detail(
            "Copper stops scaling.",
            &["Copper resistance wall below ~20 nm pitch; switch to Ru (CHIP_MID_METAL.txt, section 9)"],
        ),
    Beat::new("fragile low-k, more current", BEAT_MS)
        .note(
            "Porous ultra-low-k is easily damaged: the etch and strip plasmas pull carbon out of the trench walls, which raises k and weakens the film. Higher current per wire also speeds electromigration.",
            "The purple plasma over the trenches, damaged purple bands on the dielectric beside each line, and one line glowing hot.",
        )
        .detail(
            "Two reliability limits.",
            &["Porous ULK damage; EM at higher current (CHIP_MID_METAL.txt, section 9)"],
        ),
    Beat::new("who sells the tools", BEAT_MS)
        .note(
            "About 30% of Applied's sales go to China. And if the tightest levels switch to etched ruthenium, spending moves from copper plating and CMP toward deposition and etch, which changes which tool makers win.",
            "Two bars, about 70% rest of world and about 30% China, and a small etched-Ru grating with air gaps.",
        )
        .detail(
            "A market shift and a geographic risk.",
            &[
                "China ~30% of Applied FY2025 revenue (AMAT annual report)",
                "Etched Ru favours deposition and etch over plating and CMP (estimate)",
            ],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources: copper and resistivity", BEAT_MS)
        .note(
            "The sources behind this page, in four groups. The first cover the copper history, barrier scaling and the resistivity study.",
            "The M5-M9 cut-away from the front right: copper lines in low-k, vias and caps.",
        )
        .detail(
            "Sources 1, 2 and 6, as listed on the page.",
            &[
                "[1] IBM Cu history: ibm.com/history/copper-interconnects ; en.wikipedia.org/wiki/Copper_interconnects",
                "[2] Barrier scaling: semiengineering.com/how-far-will-copper-interconnects-scale",
                "[6] IBM Cu resistivity study: research.ibm.com/publications/the-effect-of-microstructure-on-resistivity-and-reliability-in-copper-interconnects",
            ],
        ),
    Beat::new("sources: nodes and fabs", BEAT_MS)
        .note(
            "These sources cover the node pitches and the IEDM papers.",
            "Close on a via joining an M6 line to the M7 wire above.",
        )
        .detail(
            "Sources 3 to 5, as listed on the page.",
            &[
                "[3] Intel 4: anandtech.com/show/17448 ; fuse.wikichip.org/news/6720/a-look-at-intel-4-process-technology/3 ; realworldtech.com/intel-4/5",
                "[4] N5: semiwiki.com TSMC IEDM2019 5nm article ; N3E: semianalysis.com/p/iedm2022p1",
                "[5] fuse.wikichip.org/?p=7375 (TSMC N3)",
            ],
        ),
    Beat::new("sources: dielectric, EM and vias", BEAT_MS)
        .note(
            "These sources cover the low-k modulus, electromigration and via placement.",
            "The block from above and to the left, its line ends showing on the side.",
        )
        .detail(
            "Sources 7 to 10, as listed on the page.",
            &[
                "[7] Intel IEDM 2024: newsroom.intel.com/intel-foundry/intel-foundry-unveils-technology-advancements-iedm-2024",
                "[8] Low-k modulus: patents.justia.com/patent/9766170 ; image-ppubs.uspto.gov 6964919",
                "[9] EM: ifte.de/mitarbeiter/lienig/vlsi05.pdf ; halbleiter.org/en/reliability/electromigration-tddb-nbti/",
                "[10] Via EPE: image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11916010",
            ],
        ),
    Beat::new("sources: tools and EDA", BEAT_MS)
        .note(
            "The last sources cover the tool makers and the extraction tools.",
            "The block nearly face on, the green caps marking each level.",
        )
        .detail(
            "Sources 11 and 12, as listed on the page.",
            &[
                "[11] AMAT FY2025 ARS: sec.gov/Archives/edgar/data/6951/000119312526027318/d54380dars.pdf",
                "[12] StarRC: synopsys.com/implementation-and-signoff/signoff/starrc.html",
            ],
        ),
];

static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_mid_metal_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` heading of CHIP_MID_METAL.txt, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, SEC3_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, SEC5_BEATS),
    section!(6, SEC6_BEATS),
    section!(7, SEC7_BEATS),
    section!(8, SEC8_BEATS),
    section!(9, SEC9_BEATS),
    section!(10, SEC10_BEATS),
];

pub const NODE: Node = Node {
    page: "MID METAL",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};
    use super::*;

    #[test]
    fn overview_zooms_are_keyed_abcde() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        assert_eq!(s.beats().len(), 6);
        explained(s.as_ref(), "MID METAL overview");
    }

    #[test]
    fn zooms_have_three_explained_beats_and_draw() {
        let counts: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3]);
        for z in ZOOMS {
            let s = (z.build)();
            explained(s.as_ref(), &format!("MID METAL zoom {}", z.key));
            draws_every_beat(s.as_ref(), &format!("MID METAL zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [4, 4, 3, 3, 4, 3, 3, 3, 3, 4]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            explained(s.as_ref(), &format!("MID METAL section {}", i + 1));
            draws_every_beat(s.as_ref(), &format!("MID METAL section {}", i + 1));
        }
    }
}
