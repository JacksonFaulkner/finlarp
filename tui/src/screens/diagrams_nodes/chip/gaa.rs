// CHIP tab, GATE-ALL-AROUND: the overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with a detailed nanosheet transistor drawn at the NMOS spot and the camera gliding in on it
// (tools/pbr3d/blender/chip_gaa_detail.py). Zoom-ins a-e and sections 1-10 are detailed, cut-away
// nanosheet close-ups from the same file, all in the picture-and-panel template.
// Sources are section 10 of CHIP_GAA.txt.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the whole chip: a gate-all-around transistor", BEAT_MS)
        .note(
            "This is the same chip as the hero, with its NMOS built as a gate-all-around (GAA) nanosheet transistor. GAA is the transistor of the newest nodes: Samsung's 3 nm, TSMC N2 and Intel 18A. The silicon, wiring and bumps around it are unchanged.",
            "The cyan box at the left of the silicon under the wiring: a small transistor with blue epi, a teal gate cap and grey contacts.",
        )
        .detail("GAA replaces the FinFET from the 3 nm class on.", &["Samsung 3GAA: 2022", "TSMC N2: 4Q25; Intel 18A: 2025"]),
    Beat::new("in on the stack of nanosheets", BEAT_MS)
        .note(
            "Cut along the channel, the transistor is a stack of three thin silicon sheets running from the source epi on the left to the drain epi on the right. Gate metal fills the gaps between the sheets, above and below each one.",
            "Tall blue epi on both sides, three grey sheets between them, yellow and bronze gate layers in the gaps, teal spacers and cap, grey contacts on top.",
        )
        .detail("Three sheets ~5-6 nm thick, ~10 nm apart (textbook).", &["~3 sheets per stack", "Gaps ~10 nm (page text)"]),
    Beat::new("the gate wraps every side of each sheet", BEAT_MS)
        .note(
            "Cut across the gate as well, you can see each sheet ringed completely: yellow high-k on all four faces, then bronze work-function metal filling the gaps. A FinFET gate touches three faces; this one touches four, so it shuts the channel off more firmly.",
            "The transistor cut two ways: blue epi on the left, and on the cut across the gate three grey sheets each inside a yellow ring, embedded in bronze metal.",
        )
        .detail("Four gated faces per sheet.", &["Gate-all-around: 4 faces vs 3 for a fin"]),
    Beat::new("current through every sheet", BEAT_MS)
        .note(
            "Turned on, electrons come down the source contact, through the source epi, along all three sheets at once and up the drain epi to the drain contact. Stacking sheets adds current without adding chip area.",
            "The three sheets glowing cyan, white beads riding down the left contact, across each sheet and up the right side.",
        )
        .detail("Three channels in one footprint.", &["Current ~ sheets x (width + thickness) (textbook)"]),
    Beat::new("a wide sheet: more drive current", BEAT_MS)
        .note(
            "Unlike a fin, a sheet's width is drawn on the mask and can be set per transistor. A wide sheet has more gated perimeter, so it carries more current for fast logic. The stack height does not change.",
            "Cut across the gate: three wide grey sheets, each ringed in yellow, inside a wide bronze gate block.",
        )
        .detail("A design knob FinFET did not have.", &["N2 mixes sheet widths on one chip (TSMC)"]),
    Beat::new("a narrow sheet: less leakage, less area", BEAT_MS)
        .note(
            "A narrow sheet carries less current but leaks less and fits in a shorter cell, which suits dense or low-power blocks. Both widths can sit on the same chip.",
            "The same three-sheet stack, now narrow, in a much thinner gate block.",
        )
        .detail("Width per device.", &["Sheet width ~15-50 nm in this picture (estimate)"]),
    Beat::new("back out to the whole chip", BEAT_MS)
        .note(
            "Back out at the whole chip. The GAA transistor sits where the planar NMOS sat; everything above it, the contacts, wiring and bumps, is built the same way.",
            "The whole chip again, the nanosheet transistor at the NMOS spot under the wiring.",
        )
        .detail("Same chip, new transistor.", &["Samsung SF3E 2022; TSMC N2 4Q25; Intel 18A 2025"]),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

// ---- zoom-ins a-e: the process flow, release, sheet width, backside power, roadmap ----

const ZA_BEATS: &[Beat] = &[
    Beat::new("superlattice: Si and SiGe layers in the fin", BEAT_MS)
        .note(
            "The process starts by growing alternating silicon and silicon-germanium layers on the wafer, then etching them into fins. The silicon layers will be the channels; the SiGe layers only hold the gaps open.",
            "A striped fin cut open on two faces: grey silicon bands, purple SiGe bands, a teal hard mask on top, standing in cream oxide.",
        )
        .detail("Layer thickness is controlled to about a nanometre.", &["~3 Si/SiGe pairs", "~1 nm thickness control (page text)"]),
    Beat::new("dummy gate, inner spacer and S/D epi", BEAT_MS)
        .note(
            "A placeholder poly gate goes on. The stack beside it is etched away, the SiGe ends are recessed and filled with nitride inner spacers, and the source and drain are grown from the exposed sheet ends.",
            "A tan dummy gate with teal spacers, purple SiGe stopping short of the stack ends, teal inner spacers in the pockets and blue epi either side.",
        )
        .detail("Inner spacers are the step FinFETs never needed.", &["S/D epi: SiP for NMOS, SiGe:B for PMOS"]),
    Beat::new("release and the real gate: HK/metal fills the gaps", BEAT_MS)
        .note(
            "The dummy gate is removed, the SiGe is etched out sideways, and high-k and metal are deposited into every gap. The sheets end up wrapped on all four sides, with contacts landing on the epi.",
            "Grey sheets each ringed in yellow high-k inside bronze metal, dark fill on top, grey trench contacts on the blue epi.",
        )
        .detail("Every layer has to fit a ~10 nm gap.", &["HK/metal by ALD (page text)"]),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("before release: sheets with SiGe between", BEAT_MS)
        .note(
            "Cut along the channel before release: purple SiGe still fills the gaps between the silicon sheets under the dummy gate. Nitride inner spacers already cap the SiGe ends, and the source and drain have been grown.",
            "Purple SiGe between grey sheets under a tan dummy gate, teal inner spacers at the gap ends, blue epi either side.",
        )
        .detail("The SiGe thickness sets the gap the gate will fill.", &["Gap ~10 nm (page text)"]),
    Beat::new("SiGe etched sideways", BEAT_MS)
        .note(
            "With the dummy gate gone, a selective etch eats the SiGe from both ends of each gap. It must remove SiGe and leave silicon almost untouched; any silicon lost thins the sheets and shifts the threshold voltage.",
            "The purple SiGe shrinking to nothing in each gap, the grey sheets left hanging between the teal spacers.",
        )
        .detail("The key spec is Si:SiGe selectivity.", &["Lam Akara (2025) targets GAA etch", "Dry selective SiGe etch (IBM research)"]),
    Beat::new("gate metal takes its place", BEAT_MS)
        .note(
            "The empty gaps are lined with high-k and filled with work-function metal by atomic layer deposition, one atomic layer at a time, so the gate surrounds every sheet.",
            "Yellow high-k lining each gap, bronze metal filling it, dark fill metal above the top sheet.",
        )
        .detail("ALD is the only way into ~10 nm gaps.", &["HK/METAL GATE (page text, section 4)"]),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("FinFET: width in whole fins", BEAT_MS)
        .note(
            "Cut across the gate, a FinFET is one or more fins, each wrapped on three sides. Its width only comes in whole fins: a designer wanting 1.5 fins of current has to pick 1 or 2.",
            "Two grey fins in the cream oxide, each inside a yellow and bronze U, dark fill metal above.",
        )
        .detail("Quantised width.", &["Fin ~7 nm wide (textbook)"]),
    Beat::new("wide sheet: drive and speed", BEAT_MS)
        .note(
            "A nanosheet's width is drawn on the mask, so each transistor can have its own. Wide sheets have more gated perimeter and carry more current, for fast logic. The stack height stays the same.",
            "Three wide grey sheets, each ringed in yellow, inside a wide bronze gate block.",
        )
        .detail("A continuous knob, not whole steps.", &["Sheet width ~15-50 nm here (estimate)", "N2 mixes widths on one chip (TSMC)"]),
    Beat::new("narrow sheet: less leakage, less area", BEAT_MS)
        .note(
            "Narrow sheets carry less current but leak less and fit shorter cells, for dense or low-power blocks.",
            "The same three-sheet stack, narrow, in a much thinner gate block.",
        )
        .detail("Gated perimeter per sheet is 2 x (W + T).", &["Narrow: less leakage, less area"]),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("front-side power: shared, crowded metal", BEAT_MS)
        .note(
            "Normally power comes down from the top through the same metal layers as the signals. The thick power rails crowd the signal wires, and the long path down to the transistors loses voltage.",
            "Three nanosheet transistors under the wiring; a gold power rail on top feeds a via down to the left source past the copper signal wires; grey substrate below.",
        )
        .detail("Power and signals compete for the same layers.", &["Front-side power delivery (conventional)"]),
    Beat::new("rails move under the substrate", BEAT_MS)
        .note(
            "With backside power, the wafer is flipped and thinned almost to the transistors, and power rails are built on the back. Nano-TSVs reach up to the devices; TSMC's A16 contacts the source directly.",
            "The substrate gone, a gold rail under the device and a gold nano-TSV rising into the left source epi, power dots climbing it.",
        )
        .detail("A shorter, fatter power path.", &["Intel PowerVia: 18A (2025)", "TSMC Super Power Rail: A16 (2026+)"]),
    Beat::new("the front metal is all signals", BEAT_MS)
        .note(
            "With power underneath, the front-side metal carries only signals, so wires can be spaced for speed and cells packed tighter.",
            "The front copper lines glowing cyan with signal dots running along them, the gold rail and nano-TSV underneath.",
        )
        .detail("Vendor claim.", &["A16 vs N2P: up to 8-10% density (TSMC claim)"]),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("FinFET: three gated sides", BEAT_MS)
        .note(
            "Cut across the gate, a FinFET channel is a fin gated on its top and two sides. The foot of the fin, inside the oxide, is never gated.",
            "One grey fin inside a yellow and bronze U, its foot running down into the cream oxide.",
        )
        .detail("Three faces.", &["FinFET: ~2012 to N3 (Intel 22 nm to TSMC N3)"]),
    Beat::new("nanosheet: gate on four sides", BEAT_MS)
        .note(
            "A nanosheet transistor slices the channel into stacked sheets and fills the gaps with gate, so each sheet is gripped on four sides.",
            "Three grey sheets, each ringed in yellow, inside a bronze gate block on a silicon mesa.",
        )
        .detail("Four faces.", &["Samsung SF3 (2022), TSMC N2, Intel 18A (2025)"]),
    Beat::new("forksheet: a wall between n and p", BEAT_MS)
        .note(
            "A forksheet puts a thin dielectric wall between the n and p sheet stacks so they can sit almost touching, shrinking the cell. The gate then wraps three sides of each sheet.",
            "A teal wall through the middle of the gate block, wide sheets butting against it on both sides.",
        )
        .detail("imec roadmap.", &["imec: forksheet to ~A10"]),
    Beat::new("CFET: NMOS over PMOS", BEAT_MS)
        .note(
            "A complementary FET stacks the nFET sheets directly on top of the pFET sheets under one gate, so a cell needs much less area. imec expects monolithic CFET after 2030.",
            "Six sheets in one tall gate: three pFET sheets at the bottom, three nFET sheets on top, with a taller gap between the two stacks.",
        )
        .detail("Roadmap, not product.", &["imec: monolithic CFET ~A7, after 2030"]),
];

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_a.glb"),
        ZA_BEATS,
    )
}
fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_b.glb"),
        ZB_BEATS,
    )
}
fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_c.glb"),
        ZC_BEATS,
    )
}
fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_d.glb"),
        ZD_BEATS,
    )
}
fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the process flow: superlattice to gate",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "release: etching out the SiGe",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "sheet width: a new design knob",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "backside power",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "roadmap: nanosheet, forksheet, CFET",
        build: zoom_e,
    },
];

// ---- sections 1-10, one picture per `# ` heading of CHIP_GAA.txt ----
// Detailed close-ups (chip_gaa_detail.py): nanosheets, inner spacers, the gate between the sheets,
// epi, backside power, forksheet and CFET, drawn to a nanometre scale and cut away.

const SEC1: &[Beat] = &[
    Beat::new("stack the layers: Si and SiGe", BEAT_MS)
        .note(
            "A gate-all-around transistor starts as a stack of alternating silicon and silicon-germanium layers, etched into a fin. The silicon layers become the channels. The SiGe layers are only placeholders that set the gaps.",
            "A fin cut open on two faces: grey silicon bands alternating with purple SiGe, a teal hard mask on top, standing in the cream oxide.",
        )
        .detail(
            "Three sheets is the usual count.",
            &["~3 Si/SiGe pairs (textbook)", "Thickness control ~1 nm"],
        ),
    Beat::new("release: the SiGe is etched out", BEAT_MS)
        .note(
            "Later in the flow the SiGe is etched away sideways, leaving the silicon sheets hanging between the source and drain like rungs of a ladder. Nitride inner spacers at each end keep the future gate away from the source and drain.",
            "Grey sheets floating in empty gaps, held at their ends by the blue source/drain epi, with teal inner spacers between the gaps and the epi.",
        )
        .detail(
            "The etch must remove SiGe and leave the silicon untouched.",
            &["Needs high Si:SiGe etch selectivity"],
        ),
    Beat::new("wrap: the gate fills every gap", BEAT_MS)
        .note(
            "High-k and metal are then deposited into the gaps, so each sheet is surrounded on all four sides. That full wrap shuts the channel off better than a fin's three sides, which lets the gate get shorter.",
            "Yellow high-k ringing each grey sheet, bronze metal filling the gaps between them, dark fill metal above, grey trench contact on the epi.",
        )
        .detail(
            "Gate on four sides, three channels per transistor.",
            &["Gaps ~10 nm, filled by ALD (page text)", "Samsung first in production, 2022"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("along the channel: source, sheets, drain", BEAT_MS)
        .note(
            "Cut along the channel, a nanosheet transistor reads left to right: source epi, a stack of three silicon sheets under the gate, drain epi. The epi is phosphorus-doped silicon for NMOS and boron-doped SiGe for PMOS.",
            "Three gates in a row, each with three grey sheets, bronze and yellow gate layers between them, teal spacers either side and tall blue epi between the gates.",
        )
        .detail(
            "Each gate drives three channels in parallel.",
            &["NMOS epi: SiP; PMOS epi: SiGe:B"],
        ),
    Beat::new("electrons run through every sheet", BEAT_MS)
        .note(
            "With the gate on, electrons cross from the source to the drain through all three sheets at once. Stacking sheets vertically adds drive current without taking more chip area.",
            "The middle gate's three sheets glowing cyan, white dots streaming through each from the left epi to the right.",
        )
        .detail(
            "Three channels in one footprint.",
            &["Current scales with sheets x (width + thickness) (textbook)"],
        ),
    Beat::new("inner spacers and the punch-through stop", BEAT_MS)
        .note(
            "Between the gate and the epi at every level sits a small nitride inner spacer that cuts capacitance and prevents shorts. Below the stack, a doped punch-through stop blocks a parasitic channel through the silicon underneath.",
            "Teal inner spacers at both ends of each gap, bronze gate metal filling the gaps, and a purple band across the silicon below the stack.",
        )
        .detail(
            "Inner spacers are new with GAA.",
            &["Inner spacer: SiN or SiOCN"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("before release: SiGe between the sheets", BEAT_MS)
        .note(
            "Before release, the gaps between the silicon sheets are still filled with SiGe under a placeholder poly gate. The SiGe ends were already recessed and replaced by nitride inner spacers, and the source and drain have been grown.",
            "Purple SiGe between grey sheets, a tan dummy gate on top, teal inner spacers at the gap ends and blue epi either side.",
        )
        .detail(
            "The SiGe sets the gap height the gate will fill.",
            &["Gap ~10 nm (page text)"],
        ),
    Beat::new("release: SiGe etched sideways", BEAT_MS)
        .note(
            "The dummy gate is removed and a selective etch eats the SiGe sideways from both ends. Any silicon it takes thins the sheets and shifts the threshold voltage, so the etch has to be very selective.",
            "The purple SiGe shrinking to nothing in each gap, the grey sheets left hanging between the teal spacers.",
        )
        .detail(
            "Lam's Akara (2025) and dry selective etch target this step.",
            &["Key spec: Si:SiGe selectivity (page text)"],
        ),
    Beat::new("after release: high-k and metal in the gaps", BEAT_MS)
        .note(
            "The empty gaps are then coated with high-k and filled with work-function metal, layer by layer, by atomic layer deposition. The gate now surrounds each sheet.",
            "Yellow high-k lining each gap above and below the sheets, bronze metal filling them, dark fill metal above the top sheet.",
        )
        .detail(
            "Every layer has to fit inside a ~10 nm gap.",
            &["HK/metal gate by ALD (page text)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("SUPERLATTICE and FIN PATTERN", BEAT_MS)
        .note(
            "Alternating Si and SiGe layers are grown by epitaxy, then etched into fins under a hard mask. The layer thicknesses become the sheet thickness and the gap.",
            "The striped grey and purple fin, cut open, under its teal hard mask.",
        )
        .detail("3-4 pairs, ~1 nm thickness control.", &["SUPERLATTICE (page text, section 4)"]),
    Beat::new("DUMMY GATE and INNER SPACER", BEAT_MS)
        .note(
            "A poly placeholder gate goes on. The stack is etched away beside it, the SiGe is recessed at its exposed ends, and the pockets are filled with nitride.",
            "A tan dummy gate with teal spacers, the purple SiGe stopping short of the stack's ends, teal inner spacers filling the pockets.",
        )
        .detail("New with GAA; a source of variation.", &["Isotropic SiGe recess, fill, etch back"]),
    Beat::new("S/D EPI", BEAT_MS)
        .note(
            "Source and drain are grown epitaxially from the exposed sheet ends. The epi strains the channel for speed and gives the contacts a large landing area.",
            "Blue faceted epi blocks on each side of the stack.",
        )
        .detail("Grown from the sheet edges.", &["NMOS SiP, PMOS SiGe:B"]),
    Beat::new("RELEASE", BEAT_MS)
        .note(
            "The dummy gate is pulled out and the SiGe etched away, leaving free-standing silicon sheets held by the epi.",
            "Grey sheets bridging the epi with empty dark gaps where the SiGe was.",
        )
        .detail("Needs Si:SiGe selectivity.", &["Lateral SiGe removal"]),
    Beat::new("HK/METAL GATE", BEAT_MS)
        .note(
            "High-k and metal fill every gap by atomic layer deposition, closing the gate round all four sides of each sheet.",
            "Yellow high-k round each sheet, bronze metal in the gaps, dark fill metal on top.",
        )
        .detail("Five new or harder modules than FinFET.", &["ALD into ~10 nm gaps"]),
];

const SEC5: &[Beat] = &[
    Beat::new("FinFET: width in whole fins", BEAT_MS)
        .note(
            "A FinFET's width comes in whole fins: one, two or three. A designer who wants 1.5 fins of current has to pick 1 or 2.",
            "Two fins cut across the gate, each in its yellow and bronze U, standing in the cream oxide.",
        )
        .detail("Quantised width.", &["Fin ~7 nm wide (textbook)"]),
    Beat::new("wide sheets: more drive", BEAT_MS)
        .note(
            "A nanosheet's width is drawn on the mask, so it can be anything in a range. Wide sheets carry more current for fast logic. The stack height stays the same.",
            "Three wide grey sheets, each ringed by yellow high-k, embedded in bronze gate metal.",
        )
        .detail(
            "A new knob FinFET did not have.",
            &["Sheet width: ~15-50 nm drawn here (estimate)", "N2 mixes sheet widths on one chip (TSMC)"],
        ),
    Beat::new("narrow sheets: less leakage, smaller cell", BEAT_MS)
        .note(
            "Narrow sheets leak less and fit in shorter cells, for dense or low-power blocks. Both widths can sit on the same chip.",
            "The same three-sheet stack, now narrow, with a much thinner gate block around it.",
        )
        .detail(
            "Width per device, not per chip.",
            &["Gated perimeter per sheet: 2 x (W + T)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("front-side power: wires share the space", BEAT_MS)
        .note(
            "In a normal chip, power comes down from the top through the same metal layers as the signals. Thick power rails take room the signal wires need, and the long thin path down loses voltage.",
            "Three transistors under the wiring; a gold power rail on top feeds a via down to the left source, past copper signal wires; grey substrate below.",
        )
        .detail(
            "Power and signals compete for the same layers.",
            &["Front-side power delivery (conventional)"],
        ),
    Beat::new("backside power: rails under the device", BEAT_MS)
        .note(
            "With backside power, the wafer is flipped and thinned almost to the transistors. Power rails are built on the back and reach up through nano-TSVs. TSMC's A16 Super Power Rail contacts the source directly.",
            "The substrate gone, a gold rail under the device, and a gold nano-TSV rising to the left source epi with power dots climbing it.",
        )
        .detail(
            "Shorter power path, less voltage droop.",
            &["Intel PowerVia: 18A (2025)", "TSMC Super Power Rail: A16 (2026+)"],
        ),
    Beat::new("front metal: signals only", BEAT_MS)
        .note(
            "With power moved underneath, the front-side metal is left to signals. Wires can be spaced for speed and cells packed tighter.",
            "The front copper lines glowing cyan with signal dots, the gold rail and nano-TSV underneath.",
        )
        .detail(
            "Intel reported its PowerVia test chip gave better cell use and frequency.",
            &["A16 vs N2P: up to 8-10% density (TSMC claim)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("Samsung SF3E: first GAA (2022)", BEAT_MS)
        .note(
            "Samsung shipped the first gate-all-around process in 2022 and calls its version MBCFET, using wide sheets. Against its 5 nm it claimed 45% less power, 23% more performance and 16% less area.",
            "A nanosheet transistor cut open on two faces, three wide grey sheets ringed in yellow and bronze, blue epi either side.",
        )
        .detail("Vendor claims under different conditions.", &["SF3E vs 5 nm: -45% power, +23% perf, -16% area"]),
    Beat::new("TSMC N2 and Intel 18A (2025)", BEAT_MS)
        .note(
            "TSMC N2 entered volume production in 4Q25 with stacked nanosheets. Intel's 18A RibbonFET, shown here with four ribbons, adds PowerVia backside power. Each claims a big step over its own previous node.",
            "Two stacks cut across the gate: on the left Intel's four ribbons over a gold backside rail, on the right TSMC's three sheets on bulk silicon.",
        )
        .detail(
            "Vendor claims, not equal conditions.",
            &["N2 vs N3E: +10-15% speed or -25-30% power", "18A vs Intel 3: ~25% frequency or -36% power"],
        ),
    Beat::new("TSMC A16 (2026+): Super Power Rail", BEAT_MS)
        .note(
            "A16 keeps N2's nanosheets and adds backside power that contacts the source and drain directly from below, one step more direct than PowerVia.",
            "One transistor cut along its channel, a gold contact rising from the backside rail straight into the blue source epi, power dots climbing it.",
        )
        .detail("Vendor claim.", &["A16 vs N2P: +8-10% speed, -15-20% power"]),
];

const SEC8: &[Beat] = &[
    Beat::new("today: n and p nanosheets side by side", BEAT_MS)
        .note(
            "In a logic cell, the n and p nanosheet stacks sit side by side under a shared gate with a gap between them. That gap is width the cell pays for but cannot use.",
            "Two three-sheet stacks cut across the gate, inside one bronze gate block, a wide gap of metal between them.",
        )
        .detail(
            "N2, 18A and SF2 all build it this way.",
            &["Nanosheet nodes: Samsung SF3, TSMC N2, Intel 18A, TSMC A16"],
        ),
    Beat::new("forksheet: a wall between n and p", BEAT_MS)
        .note(
            "A forksheet puts a thin dielectric wall between the n and p sheets so they can sit almost touching. The gate then wraps three sides of each sheet. imec sees it extending nanosheets to about the A10 node.",
            "A teal wall rising through the middle of the gate, the sheets on each side butting against it.",
        )
        .detail(
            "Tools: Applied puts GAA module spend at ~$7B per 100K wafer starts a month vs ~$6B for FinFET.",
            &["imec: forksheet to ~A10", "Applied GAA revenue ~$2.5B in FY2024"],
        ),
    Beat::new("CFET: nFET stacked on pFET", BEAT_MS)
        .note(
            "A complementary FET stacks the nFET sheets directly on top of the pFET sheets under one gate, so a cell needs much less area. imec expects monolithic CFET around A7, after 2030.",
            "Six sheets in one tall gate: three pFET sheets at the bottom and three nFET sheets at the top, with a taller gap between the two stacks.",
        )
        .detail("Roadmap, not product.", &["imec: monolithic CFET ~A7, after 2030"]),
];

const SEC9: &[Beat] = &[
    Beat::new("Samsung SF3E: ~50-60% yield (reports)", BEAT_MS)
        .note(
            "Press reports put Samsung's first GAA yields at about 50 to 60% in 2024, with its second-generation SF3 and SF2 trials lower. These are secondary reports, not audited figures.",
            "A wafer seen from above, its dies split roughly half green (good) and half red (failed).",
        )
        .detail("Secondary reports.", &["SF3E 50-60% (2024)", "SF3 ~20%, SF2 test ~30% (Feb 2025)"]),
    Beat::new("TSMC N3E FinFET: ~82-86% (reports)", BEAT_MS)
        .note(
            "The mature FinFET it replaces yields far better, at a reported 82 to 86%. A new transistor architecture resets the yield learning curve.",
            "The same wafer, now mostly green with a scattering of red dies.",
        )
        .detail("Report.", &["N3E ~82-86% (report)"]),
    Beat::new("N2 wafers: over $30,000 (reported)", BEAT_MS)
        .note(
            "Reports put an N2 wafer above $30,000 against about $18,000 for N3. TSMC does not confirm prices. Combined with lower early yields, cost per good die rises steeply.",
            "Two wafers with a stack of gold coins behind each, one coin per $1,000: 18 for N3, 30 for N2.",
        )
        .detail("Unconfirmed press reports.", &["N3 ~$18k, N2 >$30k per wafer (reports)"]),
];

const SEC10: &[Beat] = &[
    Beat::new("Samsung 3GAA and Intel 18A", BEAT_MS)
        .note(
            "Samsung's announcement of the first GAA production, and Intel's 18A performance figures and PowerVia results.",
            "The finished nanosheet row cut open, the camera starting to turn.",
        )
        .detail("Vendor announcements.", &["Samsung news; Intel newsroom and Tom's Hardware (sources 1, 2)"]),
    Beat::new("TSMC N2, A16 and imec", BEAT_MS)
        .note(
            "TSMC's N2 and A16 announcements and coverage, and imec's forksheet and CFET roadmap.",
            "The row from further round, the sheets and gate metal on the cut faces.",
        )
        .detail("Sources 3 to 5.", &["TSMC research; IEEE Spectrum; AnandTech; imec articles"]),
    Beat::new("yields, prices and tool spend", BEAT_MS)
        .note(
            "Press reports on yields and wafer prices, and Applied Materials' figures on GAA tool spending.",
            "The row seen more from the side, the epi and contacts in view.",
        )
        .detail("Sources 6 and 7.", &["TechSpot, NotebookCheck, Tom's Hardware; Applied Q2 FY2024 call"]),
    Beat::new("Lam Akara and selective SiGe etch", BEAT_MS)
        .note(
            "Lam's Akara etch tool and the research on dry selective SiGe etch for releasing stacked nanosheets.",
            "The row from above, the gaps between the sheets in view.",
        )
        .detail("Sources 8 and 9.", &["StorageNewsletter (Lam Akara); PMC and IBM research"]),
];

static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_gaa_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` heading of the page, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

pub const NODE: Node = Node {
    page: "GATE-ALL-AROUND",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_and_sections_match_the_blender_beats_and_draw() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        let zoom_beats: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(zoom_beats, [3, 3, 3, 3, 4]);
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 5, 3, 3, 3, 3, 3, 4]);
        for z in ZOOMS {
            let s = (z.build)();
            super::super::super::blender::explained(s.as_ref(), &format!("zoom {}", z.key));
            super::super::super::blender::draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
