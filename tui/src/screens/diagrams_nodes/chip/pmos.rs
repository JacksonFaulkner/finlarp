// CHIP tab, PMOS: the overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py) with the
// camera zooming in on this part (tools/pbr3d/blender/chip_pmos.py). Zoom-ins a-e and sections 1-10
// are Blender scenes from the same script: a the n-well and its tap, b SiGe strain, c the CMOS
// inverter, d width ratio, e GAA PFET and germanium; sections in the order of CHIP_PMOS.txt. Sources:
// CHIP_PMOS.txt section 10 and tui/src/screens/diagrams_pages/CHIP_PMOS.details.txt; textbook figures
// are marked as such.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("PMOS: the hole-carrying pull-up in the chip", BEAT_MS)
        .note(
            "The whole chip in cut-away: silicon at the bottom, copper wiring above, package bumps on top. The transistor outlined in yellow is a PMOS, the switch that pulls a signal up to VDD. Power comes in through the bumps.",
            "The chip as a slab: the blue NMOS on the left and the pink PMOS on the right in the tan silicon, wiring tiers and silver bumps above, a yellow box round the PMOS.",
        )
        .detail(
            "The PMOS is the pull-up half of every CMOS gate.",
            &["PMOS conducts with holes when its gate is low (CHIP_PMOS.txt, section 1)"],
        ),
    Beat::new("gate low: holes form a channel", BEAT_MS)
        .note(
            "Up close the PMOS is the NMOS mirrored: p+ source and drain in an n-type well whose free carriers are electrons. The source is tied to VDD. With the gate at 0 V, well below the source, the field draws holes to the surface and a channel forms.",
            "Pink p+ blocks under orange SiGe:B raised epitaxy, grey contact pillars up to the copper, the dark gate, cyan dots (electrons) in the slate-blue n-well, and a bright orange strip (the hole channel) under the gate.",
        )
        .detail(
            "A PMOS is on when its gate is low: the opposite of an NMOS.",
            &["|Vt| ~0.2-0.4 V at leading nodes (typical)", "SiGe:B source and drain (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("holes flow from VDD to the output", BEAT_MS)
        .note(
            "Holes come in from VDD down the source contact, cross the channel, and leave up the drain contact to the output, charging it toward VDD. Holes are about a third as mobile as electrons, so the PMOS is the weaker half.",
            "Orange beads ride down the right contact pillar, along the orange channel under the gate, and up the left pillar toward the copper wire.",
        )
        .detail(
            "Every PMOS trick, from SiGe strain to wider devices, makes up for slow holes.",
            &["Holes ~450 vs electrons ~1400 cm2/Vs in bulk Si (textbook)"],
        ),
    Beat::new("gate high: the channel closes, PMOS off", BEAT_MS)
        .note(
            "The input rises to VDD. With gate and source at the same voltage there is no field to hold holes at the surface, so the channel disappears and the PMOS turns off. The well's electrons return under the gate.",
            "The gate's fill metal glowing amber, the orange strip gone, and cyan electrons back under the gate.",
        )
        .detail(
            "High input: PMOS off, so the output can be pulled low.",
            &["Gate high ~0.75 V: PMOS off (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("CMOS: one of the pair is always off", BEAT_MS)
        .note(
            "Pulled back to the pair: the same high input turns the NMOS on. Electrons flow through it and pull the output to ground while the PMOS is off. Because one of the two is always off, there is no steady path from VDD to ground.",
            "The NMOS on the left with an amber gate, a cyan channel and cyan beads riding through it; the PMOS on the right with an amber gate and no channel.",
        )
        .detail(
            "CMOS draws power mainly while it switches: about C V^2 f.",
            &["CMOS power ~ C V^2 f (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("gate low again: back to the PMOS on", BEAT_MS)
        .note(
            "The input falls again and the camera returns to the whole chip. The PMOS turns back on and the NMOS off, and the output goes high.",
            "The whole chip, the yellow box back round the PMOS.",
        )
        .detail(
            "Each input change flips which of the pair conducts.",
            &["Input 0 -> output 1 (CHIP_PMOS.txt, section 3)"],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_pmos.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

// ---- zoom-ins a-e -----------------------------------------------------------------------------

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

const ZA_BEATS: &[Beat] = &[
    Beat::new("the n-well sits under the PMOS", BEAT_MS)
        .note(
            "A PMOS needs n-type silicon around it, but the wafer is p-type. So it is built in an n-well: a pocket of phosphorus-doped silicon whose free carriers are electrons. NMOS devices sit in the p-type silicon alongside.",
            "A yellow outline round the slate-blue n-well under the PMOS, cyan dots (electrons) through it, and the tan p substrate below.",
        )
        .detail(
            "The well and substrate form a junction too, which must stay reverse-biased.",
            &["N-well: n-type silicon under the PMOS (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("a tap ties the well to VDD", BEAT_MS)
        .note(
            "An n+ tap past the STI wall connects the well to the VDD wire, the same wire that feeds the source. Holding the well at the highest voltage keeps every p+/n junction reverse-biased and stops the parasitic thyristor between neighbouring wells from latching up.",
            "Yellow outlines on the blue n+ tap and its contact pillar at the right, and a red arched VDD wire joining the tap contact to the source contact.",
        )
        .detail(
            "Taps and well spacing set how robust a chip is against latch-up.",
            &["Well tied to VDD through an n+ tap (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("only the channel conducts", BEAT_MS)
        .note(
            "With the well at VDD, the source and drain junctions stay blocked, so the only path for current is the channel under the gate. Pull the gate low and holes flow source to drain, and nowhere else.",
            "Violet depletion bands round the pink source and drain (blocked junctions), an orange channel under the gate, and orange holes crossing from the right contact to the left.",
        )
        .detail(
            "Isolation by reverse-biased junctions is what lets PMOS and NMOS share one wafer.",
            &["P+/n junctions reverse-biased (CHIP_PMOS.txt, section 2)"],
        ),
];

// The same picture as section 6, so the same beats.
const ZB_BEATS: &[Beat] = SEC6_BEATS;

const ZC_BEATS: &[Beat] = &[
    Beat::new("PMOS pull-up, NMOS pull-down", BEAT_MS)
        .note(
            "An inverter: the PMOS connects the output to VDD, the NMOS connects it to ground. Their gates share the input, and their drains share an output wire that runs to the next gate, which looks to the inverter like a small capacitor to charge or empty.",
            "The NMOS (blue, tan well) left and the PMOS (pink, slate well) right; a copper input bar joins the gates; a copper wire arches from drain to drain and rises to two plates (the load); blue ground and red VDD caps on the outer contacts.",
        )
        .detail(
            "Every CMOS gate is a pull-up network over a pull-down network.",
            &["PMOS on top (pull-up), NMOS below (pull-down) (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("input 0: PMOS on, output high", BEAT_MS)
        .note(
            "With the input at 0 V the PMOS turns on and the NMOS stays off. Holes ride from VDD through the PMOS, up its drain contact, along the arched output wire and into the load, charging it to VDD.",
            "An orange channel under the PMOS gate and orange beads riding from the red VDD contact, through the PMOS, along the arch and up to the plates.",
        )
        .detail(
            "Charging the load takes energy of about C V^2 per cycle from the supply.",
            &["Input 0: PMOS on, output charged to VDD (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("input 1: NMOS on, output low", BEAT_MS)
        .note(
            "With the input high the NMOS turns on and the PMOS off. Electrons ride from ground through the NMOS, up the arched output wire and into the load, emptying its charge: the output falls to 0 V.",
            "Both gates amber, a cyan channel under the NMOS gate, and cyan beads riding from the blue ground contact, through the NMOS, along the arch and up to the plates.",
        )
        .detail(
            "One of the pair is always off, so there is no steady current, only switching current.",
            &["Input 1: NMOS on, output discharged (CHIP_PMOS.txt, section 3)", "CMOS power ~ C V^2 f (CHIP_PMOS.txt, section 3)"],
        ),
];

// The same picture as section 5, so the same beats.
const ZD_BEATS: &[Beat] = SEC5_BEATS;

// The same picture as section 7, so the same beats.
const ZE_BEATS: &[Beat] = SEC7_BEATS;

macro_rules! zoom {
    ($cell:ident, $glb:literal, $beats:ident, $name:ident) => {
        fn $name() -> Box<dyn Scene> {
            page(
                &$cell,
                include_bytes!(concat!("../../../../../tools/pbr3d/assets/", $glb)),
                $beats,
            )
        }
    };
}

zoom!(ZA, "chip_pmos_zoom_a.glb", ZA_BEATS, zoom_a);
zoom!(ZB, "chip_pmos_zoom_b.glb", ZB_BEATS, zoom_b);
zoom!(ZC, "chip_pmos_zoom_c.glb", ZC_BEATS, zoom_c);
zoom!(ZD, "chip_pmos_zoom_d.glb", ZD_BEATS, zoom_d);
zoom!(ZE, "chip_pmos_zoom_e.glb", ZE_BEATS, zoom_e);

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the n-well and its tap",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "SiGe strain: squeezing the channel",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "the CMOS inverter",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "width ratio: making up for slow holes",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "GAA PFET and germanium",
        build: zoom_e,
    },
];

// ---- sections 1-10 -----------------------------------------------------------------------------
// Each section is a close-up of one detailed PMOS in cut-away (chip_mos_detail.py): pink p+
// source and drain under orange SiGe:B epitaxy, dark silicide and grey tungsten contacts, the gate
// stack (white SiO2, teal high-k, gold p-type work-function metal, grey fill, green nitride),
// slate-blue n-well over a tan p substrate, white STI walls. The source is on the right (VDD).

const SEC1_BEATS: &[Beat] = &[
    Beat::new("a PMOS at rest: gate high, off", BEAT_MS)
        .note(
            "A PMOS is the mirror image of an NMOS: p+ source and drain sitting in an n-type well, where the free carriers are electrons. Its source is tied to VDD. With the gate high (at VDD, ~0.75 V) there is no voltage between gate and source, so no channel forms and the switch is off.",
            "The cut face of one transistor: pink p+ blocks under orange SiGe raised epitaxy and grey contact pillars, the gate's fill metal glowing amber (high), and cyan dots (electrons) through the slate-blue n-well.",
        )
        .detail(
            "A PMOS turns on when its gate goes low: the opposite of an NMOS.",
            &["PMOS conducts with holes when the gate is low (CHIP_PMOS.txt, section 1)", "Supply at leading nodes ~0.7-0.8 V (typical)"],
        ),
    Beat::new("gate low: holes flow source to drain", BEAT_MS)
        .note(
            "Pulling the gate to 0 V puts it well below the source. The field pushes the well's electrons away from the surface and draws holes into a thin channel under the gate. Holes then flow from the VDD source to the drain, charging the output.",
            "The gate dark, a bright orange strip (the hole channel) on the surface, and orange dots (holes) coming down the right contact, across the channel and up the left contact.",
        )
        .detail(
            "Holes are the weaker carrier, so every PMOS trick is about closing that gap.",
            &["Bulk Si hole mobility ~450 vs electrons ~1400 cm2/Vs (textbook)", "|Vt| ~0.2-0.4 V at leading nodes (typical)"],
        ),
    Beat::new("paired with an NMOS: the CMOS inverter", BEAT_MS)
        .note(
            "A PMOS and an NMOS with their gates tied (the input) and their drains tied (the output) make an inverter, the simplest CMOS gate. The PMOS pulls the output up to VDD, the NMOS pulls it down to ground, and only one is on at a time.",
            "The NMOS (blue n+ in a tan p-well) on the left and the PMOS (pink p+ in a slate n-well) on the right; a copper bar joins the two gates, a lower copper bar joins the drains, a blue ground cap on the far-left contact and a red VDD cap on the far-right.",
        )
        .detail(
            "Because one of the pair is always off, CMOS draws current mostly while it switches.",
            &["INVERTER: output = NOT input (CHIP_PMOS.txt, section 3)", "CMOS power ~ C V^2 f (CHIP_PMOS.txt, section 3)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("p+ SOURCE: SiGe:B on the VDD side", BEAT_MS)
        .note(
            "The source supplies the holes. It is boron-doped silicon under a raised layer of silicon-germanium grown with boron already in it (SiGe:B). The germanium squeezes the channel (section 6). A silicide cap lets the tungsten contact connect it to VDD.",
            "A yellow outline round the right side: the pink p+ block, the orange SiGe:B raised epitaxy on it, the dark silicide strip and the grey contact pillar.",
        )
        .detail(
            "The source's resistance and strain together set much of the PMOS drive current.",
            &["p+ source: SiGe:B stressor on the VDD side (CHIP_PMOS.txt, section 2)", "p+ boron ~1e20-1e21 /cm3 (typical)"],
        ),
    Beat::new("PMOS CHANNEL: holes under a low gate", BEAT_MS)
        .note(
            "With the gate low, a thin layer of holes forms on the silicon surface under it, joining source and drain. The channel is only tens of nanometres long, and squeezing it with SiGe makes the holes move faster.",
            "Close on the middle: the bright orange strip under the dark gate and orange holes running along it from right to left.",
        )
        .detail(
            "Strain, interface roughness and bias-temperature instability set channel mobility.",
            &["Holes flow source to drain when the gate is low (CHIP_PMOS.txt, section 2)", "Gate lengths ~15-20 nm at leading nodes (estimate)"],
        ),
    Beat::new("p+ DRAIN: the output", BEAT_MS)
        .note(
            "The drain is built like the source and is the output node. In a pull-up it delivers the holes that charge the output to VDD. Its junction capacitance is part of the load the circuit must charge every cycle.",
            "A yellow outline round the left side: pink p+ block, orange SiGe:B epitaxy, dark silicide, and the grey contact pillar to the output.",
        )
        .detail(
            "Drain capacitance feeds straight into the C in C V^2 f.",
            &["p+ drain: SiGe:B stressor, the output (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("PMOS GATE: high-k and a p-type metal", BEAT_MS)
        .note(
            "The gate stack matches the NMOS layer for layer: SiO2 interlayer, hafnium-oxide high-k, a work-function metal, fill metal and a nitride cap. Only the work-function metal differs: a p-type metal (TiN-based) that sets the PMOS threshold.",
            "Close on the gate: white interlayer at the bottom, teal high-k lining the U-shaped trench, gold p-type work-function metal inside it, grey fill, green nitride cap and spacers.",
        )
        .detail(
            "Separate work-function metals are why NMOS and PMOS gates are built in separate steps.",
            &["HKMG: high-k hafnium dielectric, metal gate (CHIP_PMOS.txt, section 2)", "HfO2 k ~20-25 vs SiO2 3.9 (textbook)", "NBTI: a PMOS ageing effect (textbook)"],
        ),
    Beat::new("N-WELL: n-type silicon tied to VDD", BEAT_MS)
        .note(
            "The PMOS sits in an n-well, a pocket of phosphorus-doped silicon in the p-type wafer. An n+ tap past the STI wall ties the well to VDD, so the p+/n junctions stay reverse-biased and the well cannot turn on a parasitic path to the NMOS next door (latch-up).",
            "A yellow outline round the slate-blue n-well with its cyan electrons, another on the blue n+ tap at the far right, and the tan p substrate below.",
        )
        .detail(
            "Taps and well spacing set how robust a chip is against latch-up.",
            &["N-well tied to VDD through an n+ tap (CHIP_PMOS.txt, section 2)", "Electrons: the well's majority carrier (textbook)"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("the inverter: pull-up over pull-down", BEAT_MS)
        .note(
            "In an inverter the PMOS connects the output to VDD and the NMOS connects it to ground. Their gates share the input and their drains share the output. Every logic gate is built from pull-up and pull-down networks like this.",
            "The two transistors side by side with no current flowing: the NMOS left over a tan p-well, the PMOS right over a slate n-well, the copper input bar on top, the output bar below it, blue ground and red VDD caps.",
        )
        .detail(
            "Only one network conducts at a time, so the output is always driven to a rail.",
            &["PMOS on top (pull-up), NMOS below (pull-down) (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("input 0: PMOS on, output to VDD", BEAT_MS)
        .note(
            "With the input low, the PMOS gate is below its source, so the PMOS turns on while the NMOS stays off. Holes flow from VDD through the PMOS into the output, charging it to VDD: the output reads 1.",
            "An orange channel under the PMOS gate and orange holes running from the red VDD contact across to the PMOS drain and up into the output bar; the NMOS has no channel.",
        )
        .detail(
            "There is never a direct VDD-to-ground path except briefly mid-switch.",
            &["Input 0: PMOS on, output charged to VDD (CHIP_PMOS.txt, section 3)"],
        ),
    Beat::new("input 1: NMOS on, output to ground", BEAT_MS)
        .note(
            "With the input high, both gates glow, the PMOS turns off and the NMOS turns on. Electrons flow from ground through the NMOS to the output, discharging it to 0 V: the output reads 0.",
            "Both gates amber, a cyan channel under the NMOS gate, cyan electrons running from the blue ground contact to the NMOS drain; the PMOS has no channel.",
        )
        .detail(
            "Switching energy per cycle is about C V^2, which is why lower supply voltage matters so much.",
            &["Input 1: NMOS on, output discharged (CHIP_PMOS.txt, section 3)", "CMOS power ~ C V^2 f plus a small short-circuit term (CHIP_PMOS.txt, section 3)"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("a standard cell: PMOS over NMOS", BEAT_MS)
        .note(
            "Chips are tiled from standard cells, seen here from above. The top half is the n-well with the PMOS (pink active), the bottom half the p-well with the NMOS (blue active). Grey gate lines run down through both, so one input drives a PMOS and an NMOS, and a copper M1 strap collects the output.",
            "Top-down view, one cell outlined in yellow: a pink active strip on a slate n-well above, a blue strip on a tan p-well below, grey vertical gates through both, grey contacts and a copper strap in the middle.",
        )
        .detail(
            "Standard cells let tools place billions of transistors automatically.",
            &["Std cell: PMOS strip on top, NMOS below, shared gate (CHIP_PMOS.txt, section 4)"],
        ),
    Beat::new("rails: VDD on top, ground below", BEAT_MS)
        .note(
            "Power arrives on two rails along the cell edges: VDD on top feeds the PMOS sources, ground along the bottom feeds the NMOS sources. Cell height is counted in metal tracks between the rails; fewer tracks save area, more give room for faster, stronger cells.",
            "The pale red VDD rail across the top and the pale blue ground rail across the bottom, both outlined in yellow, with the cells between them.",
        )
        .detail(
            "Cell height = tracks x metal-2 pitch.",
            &["ASAP7: 9-track and 7.5-track cells (CHIP_PMOS.txt, section 4)", "7-8 tracks favour area, 11-12 favour speed (CHIP_PMOS.txt, section 4)"],
        ),
    Beat::new("rows and tap cells", BEAT_MS)
        .note(
            "Cells snap together in rows. Every other row is flipped so neighbours share a rail. Tap cells, placed at intervals, tie the n-well to VDD and the p-well to ground with n+ and p+ taps, which stops latch-up.",
            "Two rows of cells, the upper one flipped so both share the red VDD rail in the middle; yellow outlines on the tap cells at each end, which hold only small blue and pink tap squares.",
        )
        .detail(
            "Tap spacing is a design rule every placer must respect.",
            &["Tap cells tie wells to rails, preventing latch-up (CHIP_PMOS.txt, section 4)"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("same size, uneven strength", BEAT_MS)
        .note(
            "Holes move about a third as fast as electrons in silicon. Built the same size, a PMOS delivers much less current than its NMOS partner, so the output would rise more slowly than it falls.",
            "An NMOS and a PMOS of equal size, both on: cyan electrons stream quickly through the NMOS while orange holes crawl slowly through the PMOS.",
        )
        .detail(
            "Equal rise and fall times need equal currents.",
            &["Holes ~450, electrons ~1400 cm2/Vs in bulk Si (CHIP_PMOS.txt, section 5)"],
        ),
    Beat::new("make the PMOS wider", BEAT_MS)
        .note(
            "The classic fix is width: to balance mu_n x Wn = mu_p x Wp, the PMOS is drawn about two to two-and-a-half times wider than the NMOS. Strain closes part of the gap, so modern ratios are smaller.",
            "Three-quarter view: the NMOS on the left is shallow, the PMOS on the right runs more than twice as far back into the picture, with a broad orange channel and more holes.",
        )
        .detail(
            "Width costs area, which is why strain and new channel materials matter.",
            &["Wp/Wn ~2-2.5 for equal rise and fall (CHIP_PMOS.txt, section 5)"],
        ),
    Beat::new("in FinFETs, width comes in whole fins", BEAT_MS)
        .note(
            "A fin has a fixed height, so a transistor can only be made wider by adding fins (or, in GAA, using wider or more sheets). A PMOS might get three fins where its NMOS has two.",
            "Two FinFETs cut across the gate: the NMOS with two fins and cyan channels, the PMOS with three fins and orange channels, each fin wrapped in teal high-k and metal.",
        )
        .detail(
            "Quantised width is one more constraint on cell design.",
            &["FinFET/GAA: PMOS gets more fins or wider sheets (CHIP_PMOS.txt, section 5)"],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("SiGe:B source and drain", BEAT_MS)
        .note(
            "Modern PMOS source and drain are etched out and regrown as silicon-germanium with boron added during growth. In-situ boron gives very high active doping; the germanium is there for strain.",
            "Yellow outlines on the orange SiGe:B raised epitaxy on both sides, and white dots (boron atoms) through it and the pink p+ regions below.",
        )
        .detail(
            "Grown-in boron avoids a separate implant and anneal.",
            &["Boron grown into the epitaxy in place (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("germanium is bigger: the channel is squeezed", BEAT_MS)
        .note(
            "Germanium atoms are about 4% larger than silicon's, so the SiGe source and drain push in on the silicon channel between them. This compressive strain along the channel changes the silicon's band structure so holes move faster.",
            "Pale yellow arrows pressing inward from the source and drain toward the channel centre, with the orange hole channel lit under the dark gate.",
        )
        .detail(
            "PMOS wants compressive strain; NMOS wants tensile.",
            &["PMOS: compressive (SiGe S/D); NMOS: tensile (CHIP_PMOS.txt, section 6)", "Ge lattice ~4% larger than Si (textbook)"],
        ),
    Beat::new("faster holes, more drive", BEAT_MS)
        .note(
            "Strained, the same channel carries more current. Intel's first strained node, 90 nm, gained about 25% PMOS drive for a few percent more process cost, and every node since has used SiGe stressors.",
            "The whole device: orange holes streaming quickly from the right contact through the squeezed channel to the left, the yellow strain arrows still pressing in.",
        )
        .detail(
            "Strain was one of the cheapest speed-ups in transistor history.",
            &["Intel 90 nm: PMOS +25%, NMOS +10% drive, ~2% cost (CHIP_PMOS.txt, section 6)", "0.72 mA/um PMOS drive at 1.2 V, 2004 (CHIP_PMOS.txt, section 6)"],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("GAA PMOS: stacked sheets, gate all round", BEAT_MS)
        .note(
            "At 2 nm-class nodes the channel becomes a stack of thin horizontal sheets, cut here across the gate. The gate wraps all four sides of each sheet, and the source and drain are SiGe:B grown at the sheet ends.",
            "Three-quarter view of three grey silicon sheets in the cut face, each ringed by teal high-k and gold metal inside the grey gate, with the orange SiGe:B epitaxy beyond the green spacer.",
        )
        .detail(
            "Gate-all-around gives the best electrostatic control yet.",
            &["Graded SiGe S/D at 55-60% Ge for stacked sheets (patent, CHIP_PMOS.txt, section 7)"],
        ),
    Beat::new("SiGe sheets: built-in strain", BEAT_MS)
        .note(
            "Making the sheets themselves from SiGe builds compressive strain into the channel. IBM's stacked SiGe nanosheet pFET, at about 1 GPa of strain, showed roughly double the peak hole mobility and 40% lower channel resistance.",
            "The same stack with the sheets now orange-tan SiGe, still ringed by teal high-k and gold metal.",
        )
        .detail(
            "Strain moves from the source and drain into the channel itself.",
            &["~1 GPa strain, +100% peak hole mobility, -40% channel resistance (CHIP_PMOS.txt, section 7)", "Swing under 70 mV/decade (CHIP_PMOS.txt, section 7)"],
        ),
    Beat::new("germanium channels: the end goal", BEAT_MS)
        .note(
            "Pure germanium has about four times silicon's hole mobility. Germanium-rich channels would close the PMOS gap, but germanium's oxide is poor, its junctions leak more, and boron diffuses into it.",
            "Pale teal germanium sheets, each wrapped in a bright orange hole channel on all four sides inside the gate.",
        )
        .detail(
            "Germanium is research and early development, not yet volume production for logic.",
            &["Ge hole mobility ~1900 vs Si ~450 cm2/Vs (CHIP_PMOS.txt, section 7)", "Hard parts: Ge oxide, junction leakage, boron diffusion (CHIP_PMOS.txt, section 7)"],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("TSMC, Intel, Samsung: stressors in every node", BEAT_MS)
        .note(
            "The three leading-edge foundries all build SiGe stressors into their PMOS: TSMC in its FinFET nodes and N2 nanosheets, Intel in 18A RibbonFET, Samsung in its gate-all-around nodes.",
            "Three PMOS cross-sections side by side, cut across the gate: a FinFET with two fins and two nanosheet stacks, each tagged with its maker.",
        )
        .detail(
            "Every leading-edge PMOS depends on strain engineering.",
            &["TSMC, Intel, Samsung build PMOS stressors (CHIP_PMOS.txt, section 8)"],
        ),
    Beat::new("Applied Materials, ASM: the epi tools", BEAT_MS)
        .note(
            "The SiGe:B is grown one atomic layer after another in epitaxy reactors. Applied Materials (AMAT) led that market, with 53% in 2004 per Gartner; ASM International and Kokusai also make epi and furnace tools.",
            "The PMOS cut face with yellow outlines on the orange SiGe:B epitaxy on both sides of the gate.",
        )
        .detail(
            "Epi quality sets strain, doping and defects in every PMOS.",
            &["Applied: 53% of epi market in 2004 (Gartner via Applied)", "Applied claimed >65% drive gain at 65 nm (vendor claim)"],
        ),
    Beat::new("Synopsys, Cadence, Arm: cells and layout", BEAT_MS)
        .note(
            "Arm (ARM) and others sell standard-cell libraries; Synopsys (SNPS) and Cadence (CDNS) sell the tools that place, route and characterise them. NVIDIA and AMD are fabless and design with what the foundry and these tools give them.",
            "A row of standard cells from above, red VDD rail on top, blue ground rail below, tap cells at each end.",
        )
        .detail(
            "Design tools turn PMOS and NMOS pairs into whole chips.",
            &["Synopsys and Cadence: layout, P&R, characterisation (CHIP_PMOS.txt, section 8)", "Arm sells cell libraries (CHIP_PMOS.txt, section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("holes stay the weaker carrier", BEAT_MS)
        .note(
            "Whatever the node, holes stay slower than electrons, so each generation needs new strain or new channel materials just to keep the PMOS level with the NMOS.",
            "A few orange holes crawling slowly from the right contact through the orange channel.",
        )
        .detail(
            "PMOS drive is a recurring bottleneck in every node.",
            &["Hole mobility ~1/3 of electron mobility in bulk Si (textbook)"],
        ),
    Beat::new("boron diffuses into the channel", BEAT_MS)
        .note(
            "Boron is a small atom and diffuses fast during hot process steps. If it creeps from the heavily doped source and drain into the channel, it shifts the threshold and raises leakage. Germanium-rich channels make this harder to control.",
            "White boron dots in the source and drain, a line of them drifting inward under the gate, and the channel region tinted red.",
        )
        .detail(
            "Thermal budget is tightly limited after the SiGe:B is grown.",
            &["Boron diffusion limits Ge-rich channels (CHIP_PMOS.txt, section 9)", "Ge oxide quality also limits them (CHIP_PMOS.txt, section 9)"],
        ),
    Beat::new("few epitaxy tool vendors", BEAT_MS)
        .note(
            "The SiGe:B regions come from epitaxy tools made by only a few vendors. Current market shares are not public in the sources found, so the size of this chokepoint is uncertain.",
            "The orange SiGe:B epitaxy on both sides tinted red.",
        )
        .detail(
            "A tooling chokepoint, but an unquantified one.",
            &["Applied 53% of epi in 2004 (Gartner via Applied)", "Current epi shares not found (CHIP_PMOS.txt, section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-2: Intel 90 nm and VLSI 2004", BEAT_MS)
        .note(
            "Intel's 90 nm strain gains and its 2004 PMOS drive figure come from these two sources.",
            "The PMOS cut face with yellow strain arrows pressing in on the orange channel.",
        )
        .detail(
            "The strain gain and the drive figure are measured values, not a model.",
            &[
                "[1] siliconsemiconductor.net/article/66624/Intel_strains_ahead_with_90nm",
                "[2] archive.vlsisymposium.org/14web/2004/technology/tec_pdf/SESSION 6.pdf",
            ],
        ),
    Beat::new("sources 3 and 6: IBM SiGe nanosheet, GAA patent", BEAT_MS)
        .note(
            "IBM's SiGe nanosheet pFET gives the strain and mobility figures; the USPTO patent gives the graded SiGe source/drain.",
            "The nanosheet stack cut across the gate, with orange SiGe sheets and the SiGe:B epitaxy behind.",
        )
        .detail(
            "Its abstract reports about 1 GPa of strain and +100% peak hole mobility.",
            &[
                "[3] researcher.draco.res.ibm.com/publications/stacked-gate-all-around-nanosheet-pfet-with-highly-compressive-strained-silessinfgreater1-xlessinfgreatergelessinfgreaterxlessinfgreaterchannel",
                "[6] image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11776998",
            ],
        ),
    Beat::new("sources 4-5: UCSB lecture and Applied", BEAT_MS)
        .note(
            "The inverter sizing comes from a UCSB lecture; the epi market share and drive-gain claim come from Applied's release.",
            "The inverter pair, with a yellow outline on the PMOS epitaxy.",
        )
        .detail(
            "The inverter ratio and the epi market share are both cited on the page.",
            &[
                "[4] ece.ucsb.edu/courses/ECE122/122_F14Banerjee/Slides/Lecture 9.pdf",
                "[5] ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-extends-leadership-position-epitaxy",
            ],
        ),
    Beat::new("sources 7-8: ASAP7 and the cell library", BEAT_MS)
        .note(
            "The ASAP7 cell paper and the standard-cell library lecture back the cell-height and tap-cell figures.",
            "A row of standard cells from above.",
        )
        .detail(
            "Each is cited on the page for the claim it supports.",
            &["[7] arxiv.org/pdf/1807.11396", "[8] eng.biu.ac.il/temanad/files/2017/02/Lecture-4-Standard-Cell-Libraries.pdf"],
        ),
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SECS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_pmos_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

static SECS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

/// One picture per `# ` section of the page, in order.
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
    page: "PMOS",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};
    use super::*;

    #[test]
    fn zoom_keys_and_beat_counts() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "zoom {}", z.key);
            explained(s.as_ref(), &format!("zoom {}", z.key));
            draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 5, 3, 3, 3, 3, 3, 3, 3, 4]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            explained(s.as_ref(), &format!("section {}", i + 1));
            draws_every_beat(s.as_ref(), &format!("section {}", i + 1));
        }
    }
}
