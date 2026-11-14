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
            "The whole chip, with the PMOS picked out: the p-channel transistor that pulls the output up to VDD.",
            "A pink outline around the PMOS in the silicon; the gate is low, so it is not lit.",
        )
        .detail(
            "The PMOS is the pull-up half of the CMOS pair.",
            &["PMOS conducts with holes when the gate is low (textbook)"],
        ),
    Beat::new("gate low: holes form a channel", BEAT_MS)
        .note(
            "The camera moves in. The gate is pulled low, below the source, and holes gather under it into a channel joining source to drain.",
            "A gold channel glows at the silicon surface between the p+ source and drain; the gate is grey.",
        )
        .detail(
            "Holes are slower than electrons in silicon.",
            &["Si hole mobility ~450 vs electrons ~1400 cm2/Vs (textbook)"],
        ),
    Beat::new("holes flow from VDD to the output", BEAT_MS)
        .note(
            "Holes come down from VDD into the source, cross the channel to the drain and rise to the output wire.",
            "Orange dots run from the top into the right-hand p+ source, across the gold channel and up the left-hand drain.",
        )
        .detail(
            "With the input low the output is pulled to VDD.",
            &["In = 0 -> Out = 1 (textbook)"],
        ),
    Beat::new("gate high: the channel closes, PMOS off", BEAT_MS)
        .note(
            "The gate rises to VDD. The channel disappears and the holes stop: the PMOS is off and no current passes.",
            "The gate turns solid orange; the channel is gone and no dots flow.",
        )
        .detail(
            "A high input switches the PMOS off.",
            &["In = 1 -> PMOS off (textbook)"],
        ),
    Beat::new("CMOS: one of the pair is always off", BEAT_MS)
        .note(
            "The camera pulls back to the pair. The gates are tied and high: the NMOS conducts to ground and the PMOS is off.",
            "Both gates are orange; the NMOS on the left is lit, the PMOS on the right is dark.",
        )
        .detail(
            "Only the switching itself draws current: CMOS power ~ C x V^2 x f.",
            &["CMOS power ~ C x V^2 x f (textbook)"],
        ),
    Beat::new("gate low again: back to the PMOS on", BEAT_MS)
        .note(
            "The input falls again and the camera returns to the whole chip. The PMOS turns back on, and the NMOS turns off.",
            "The gate loses its orange and the PMOS outline shows again, as at the start.",
        )
        .detail(
            "Each input change flips which of the pair conducts.",
            &["In = 0 -> Out = 1 (textbook)"],
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
            "The PMOS sits in an n-type well inside the p-type substrate. The well is what makes its source and drain p-type junctions in an n-type tub.",
            "A translucent blue well under and around the pink source and drain, with the grey gate above it.",
        )
        .detail(
            "The PMOS lives in an n-well; the NMOS sits in the p-substrate or a p-well tied to ground.",
            &["N-well: n-type region in which PMOS devices sit (textbook)", "NMOS sits in the p-substrate or a p-well (textbook)"],
        ),
    Beat::new("a tap ties the well to VDD", BEAT_MS)
        .note(
            "An n+ tap at the edge of the well is plugged up to the metal above, so the well sits at VDD and the junctions stay reverse-biased.",
            "A blue n+ block at the right-hand edge of the well, with a tungsten plug running up to the thin metal.",
        )
        .detail(
            "Taps along each row stop latch-up, the p-n-p-n path between VDD and ground.",
            &["Well tied to Vdd through n+ taps (textbook)", "Poor tap spacing can trigger latch-up (textbook)"],
        ),
    Beat::new("only the channel conducts", BEAT_MS)
        .note(
            "With the well reverse-biased, current flows only through the channel when the gate is low. The well itself stays dark.",
            "The gold channel lights at the surface under the gate; the well stays a pale blue tint.",
        )
        .detail(
            "Well-proximity effects shift the threshold of transistors near the well edge.",
            &["Well-proximity effect (textbook)", "Latch-up prevention depends on the taps (textbook)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("boron-doped SiGe source and drain", BEAT_MS)
        .note(
            "The source and drain are etched out and regrown as boron-doped SiGe, with the boron grown in rather than implanted.",
            "Pale pink SiGe blocks with boron atoms glowing in them, on either side of the channel.",
        )
        .detail(
            "Boron is light and diffuses fast, especially after implant damage, so junctions are less abrupt.",
            &["Boron diffuses fast; transient-enhanced diffusion after implants (patent descriptions)"],
        ),
    Beat::new("SiGe is bigger, so it squeezes the channel", BEAT_MS)
        .note(
            "Germanium atoms are larger than silicon, so the regrown SiGe wants more room. Confined by the silicon around it, it pushes on the channel along the current direction.",
            "White arrows press inward on the channel from both sides, and the channel glows under the gate.",
        )
        .detail(
            "Compressive strain along the channel raises hole mobility.",
            &["Compressive stress along the channel raises hole mobility (patent description, CHIP_PMOS.details.txt)"],
        ),
    Beat::new("faster holes, more drive", BEAT_MS)
        .note(
            "Strain raises hole mobility. Intel's 90 nm process used SiGe source and drain for about 25% more PMOS drive, at about 2% more process cost.",
            "A burst of holes races across the squeezed channel, faster than in the beat before.",
        )
        .detail(
            "Intel reported 0.72 mA/um of PMOS drive at 1.2 V in 2004.",
            &[
                "Intel 90 nm: +25% PMOS drive for ~2% process cost (siliconsemiconductor.net, Intel strains ahead with 90nm)",
                "0.72 mA/um PMOS drive at 1.2 V (VLSI 2004, Intel, session 6)",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("PMOS pull-up, NMOS pull-down", BEAT_MS)
        .note(
            "An inverter: the PMOS pulls the output up to VDD, the NMOS pulls it down to ground, and the gates and drains are tied together.",
            "The two transistors side by side in cut-away, both idle, with the output wire above them.",
        )
        .detail(
            "The inverter is the unit that NAND, NOR and flip-flops are built from.",
            &["Inverter: PMOS pull-up, NMOS pull-down (UCSB ECE122 lecture 9)"],
        ),
    Beat::new("input 0: PMOS on, output high", BEAT_MS)
        .note(
            "A low input turns the PMOS on and the NMOS off. Holes flow from VDD into the output and charge it high.",
            "The gold channel lights under the PMOS gate, orange holes run from the VDD side to the output, and the NMOS stays dark.",
        )
        .detail(
            "No path runs from VDD to ground, so the pair draws current only while it switches.",
            &["In = 0 -> Out = 1 (textbook)", "No static path from VDD to ground (UCSB ECE122 lecture 9)"],
        ),
    Beat::new("input 1: NMOS on, output low", BEAT_MS)
        .note(
            "A high input turns the PMOS off and the NMOS on. The output is pulled down to ground through the NMOS.",
            "The NMOS gate is orange and its channel lights; blue electron dots run down to ground while the PMOS stays dark.",
        )
        .detail(
            "Only the switching draws power: P = alpha x C x Vdd^2 x f, plus a short-circuit term.",
            &["In = 1 -> Out = 0 (textbook)", "CMOS power: alpha C Vdd^2 f (allaboutcircuits, power dissipation of a CMOS inverter)"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("holes are about 3x slower", BEAT_MS)
        .note(
            "In silicon holes move at about a third of electrons' mobility, so the narrow PMOS carries less current than the NMOS beside it.",
            "Blue electrons race through the NMOS, while the narrow PMOS carries a slow stream of orange holes.",
        )
        .detail(
            "Holes have a heavier effective mass and more scattering, so they are the weaker carrier.",
            &["Electrons ~1400 cm2/Vs, holes ~450 cm2/Vs in bulk Si (textbook)", "Holes: heavier effective mass, more scattering (textbook)"],
        ),
    Beat::new("make the PMOS wider", BEAT_MS)
        .note(
            "Equal drive needs mu_n x Wn = mu_p x Wp, so the PMOS is drawn about 2 to 2.5 times wider than the NMOS.",
            "The PMOS widens to about twice the NMOS width, its source and drain pushed out, and its holes run faster across it.",
        )
        .detail(
            "Equal rise and fall times need this ratio, which costs area and gate capacitance.",
            &["Wp/Wn about 2-2.5 for equal rise and fall (UCSB ECE122 lecture 9, b = 2.4)", "A 2-2.5x pull-up costs area and gate capacitance (UCSB ECE122 lecture 9)"],
        ),
    Beat::new("in fins, width comes in whole fins", BEAT_MS)
        .note(
            "In FinFET and GAA, width is counted in whole fins or sheets, so the PMOS gets more of them. Strain narrows the ratio that is needed.",
            "Two fins stand on the NMOS and three on the PMOS, on the silicon surface.",
        )
        .detail(
            "Width is quantised by fin or sheet count, so the PMOS steps up in whole units.",
            &["Width in whole fins or sheets (CHIP_PMOS.txt, section 5)", "Strain narrows the Wp/Wn gap (CHIP_PMOS.txt, section 5)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("PMOS as stacked sheets", BEAT_MS)
        .note(
            "In gate-all-around, the PMOS channel is a stack of thin sheets, and the gate wraps around every one of them.",
            "Three grey silicon sheets stacked between the pink source and drain, with the transparent gate around them.",
        )
        .detail(
            "Wrapping the gate on all four sides gives the best control of the channel.",
            &["GAA PFET: the channel is a stack of nanosheets (IBM stacked GAA nanosheet pFET)", "Gate control on all sides (textbook)"],
        ),
    Beat::new("SiGe sheets, about 1 GPa of strain", BEAT_MS)
        .note(
            "IBM's SiGe nanosheet pFET puts the sheets under about 1 GPa of compressive strain, which lifts hole mobility.",
            "The sheets turn pink SiGe, and white arrows press on them from the source side.",
        )
        .detail(
            "The paper reports +100% peak hole mobility and -40% channel resistance.",
            &[
                "~1 GPa compressive strain, +100% peak hole mobility, -40% channel resistance (IBM, stacked GAA nanosheet pFET)",
                "Swing under 70 mV/decade (same IBM abstract)",
            ],
        ),
    Beat::new("germanium: even faster holes", BEAT_MS)
        .note(
            "Germanium holes move at about 1900 cm2/Vs against silicon's 450, but germanium oxide and junction leakage are hard to manage.",
            "The sheets turn teal germanium, and a row of holes runs along each sheet.",
        )
        .detail(
            "The hard parts are germanium oxide quality, junction leakage and boron diffusing into the channel.",
            &["Ge ~1900 vs Si ~450 cm2/Vs bulk (textbook)", "No production Ge-channel node in the sources (CHIP_PMOS.details.txt, GE CHANNEL)"],
        ),
];

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

const SEC1_BEATS: &[Beat] = &[
    Beat::new("a PMOS at rest: gate high, off", BEAT_MS)
        .note(
            "The PMOS is the p-channel transistor: p+ source and drain in an n-type well, switched on by pulling the gate low.",
            "The gate is solid orange (high) and the PMOS is dark, with no channel and no holes.",
        )
        .detail(
            "A PMOS is the mirror image of an NMOS, carrying holes where the NMOS carries electrons.",
            &["PMOS conducts with holes when the gate is low (textbook)", "Mirror image of the NMOS (CHIP_PMOS.txt, section 1)"],
        ),
    Beat::new("gate low: holes flow source to drain", BEAT_MS)
        .note(
            "Pulling the gate below the source opens a channel of holes, and they flow from the VDD side to the output.",
            "A gold channel at the surface, with orange holes flowing down from VDD across it and up to the output.",
        )
        .detail(
            "Holes are the weak carrier: about 450 cm2/Vs against 1400 for electrons.",
            &["Si hole mobility ~450 vs electrons ~1400 cm2/Vs (textbook)"],
        ),
    Beat::new("paired with an NMOS: the CMOS inverter", BEAT_MS)
        .note(
            "A PMOS on top of an NMOS, gates and drains tied, makes the CMOS inverter at the heart of logic.",
            "The PMOS and NMOS side by side in cut-away, both idle, with the output wire above.",
        )
        .detail(
            "One of the pair is always off, so the pair draws current only while it switches.",
            &["INVERTER: out = NOT in (textbook)", "CMOS power ~ C V^2 f (allaboutcircuits power dissipation)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("p+ SOURCE: SiGe:B on the Vdd side", BEAT_MS)
        .note(
            "The p+ source supplies the holes. It is boron-doped SiGe on the Vdd side of the channel.",
            "The source block outlined in pink, on the VDD side under the bump.",
        )
        .detail(
            "Its contact resistance is a main series term in PMOS drive.",
            &["p+ source: heavily boron-doped, low-resistance contact (textbook)", "SiGe stressor on the source side (CHIP_PMOS.txt, section 2)"],
        ),
    Beat::new("PMOS CHANNEL: holes flow when the gate is low", BEAT_MS)
        .note(
            "Holes flow in this channel when the gate is low. The stressors squeeze it, which speeds the holes.",
            "The gold strip at the silicon surface between the source and the drain.",
        )
        .detail(
            "Strain, interface roughness and BTI set the channel's mobility.",
            &["Inversion layer of holes under a gate pulled below the source (textbook)", "Channel length tens of nm at leading nodes (textbook)"],
        ),
    Beat::new("p+ DRAIN: the output", BEAT_MS)
        .note(
            "The drain is the output: holes leave the channel here and charge the load node in a pull-up.",
            "The drain block outlined on the output side, under the wire that rises to the output.",
        )
        .detail(
            "Drain junction capacitance is part of the load the next stage sees, which feeds C V^2 f.",
            &["Drain-side junction capacitance counts toward C V^2 f (CHIP_PMOS.txt, section 2)", "SiGe:B stressor on the drain (patent description)"],
        ),
    Beat::new("PMOS GATE: high-k metal", BEAT_MS)
        .note(
            "The gate sits over the channel on a high-k hafnium dielectric with a metal gate. Its work function sets the threshold.",
            "The gate block lit orange while it is high; the channel below it is dark.",
        )
        .detail(
            "Work-function drift and NBTI show up as threshold spread.",
            &["HKMG: high-k hafnium dielectric and metal gate (textbook)", "NBTI, a PMOS bias instability (textbook)"],
        ),
    Beat::new("N-WELL: n-type silicon tied to VDD", BEAT_MS)
        .note(
            "The n-well is n-type silicon in which the PMOS sits. Tied to VDD, it keeps the junctions reverse-biased.",
            "The blue well under and around the PMOS, shown translucent.",
        )
        .detail(
            "Taps and well spacing set latch-up robustness.",
            &["Well tied to Vdd through n+ taps (textbook)", "Latch-up patent (US 10872190, CHIP_PMOS.details.txt, N-WELL)"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("standard cell: PMOS over NMOS", BEAT_MS)
        .note(
            "Logic is tiled from standard cells: a PMOS strip over an NMOS strip, with a shared gate running across them.",
            "The pair as one cell, idle, with its contacts and the output wire.",
        )
        .detail(
            "Cell height is counted in metal-2 tracks: ASAP7 has 9-track and 7.5-track cells.",
            &["ASAP7 9-track and 7.5-track cells (arxiv.org/pdf/1807.11396)", "Standard cell libraries (eng.biu.ac.il, lecture 4)"],
        ),
    Beat::new("rails: Vdd and ground", BEAT_MS)
        .note(
            "The Vdd and ground rails run along the edges of the cell in the thin metal, feeding the source and the well.",
            "The thin-metal band lit pink, with rails running across the pair.",
        )
        .detail(
            "The rails set the cell's height and how it joins its neighbours.",
            &["Rails along the cell edges (CHIP_PMOS.txt, section 4)", "Cell height = tracks x metal-2 pitch (CHIP_PMOS.txt, section 4)"],
        ),
    Beat::new("tap cells tie the wells to the rails", BEAT_MS)
        .note(
            "Cells tile in rows, and tap cells tie each well to the rails to stop latch-up.",
            "The whole chip, with the bumps at the top and rows of cells below the wiring.",
        )
        .detail(
            "7 to 8 tracks favour area; 11 to 12 favour speed.",
            &["7-8 tracks favour area, 11-12 favour speed (CHIP_PMOS.txt, section 4)", "Tap cells prevent latch-up (textbook)"],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("TSMC, Intel, Samsung: stressors in every node", BEAT_MS)
        .note(
            "The leading foundries build PMOS stressors into every FinFET and GAA node.",
            "The whole chip, with its bumps and wiring; no part is picked out.",
        )
        .detail(
            "Foundries spend process effort on PMOS strain at every node.",
            &["TSMC (TSM), Intel (INTC), Samsung build PMOS stressors (CHIP_PMOS.txt, section 8)"],
        ),
    Beat::new("Applied Materials: the epi tools", BEAT_MS)
        .note(
            "The SiGe is grown in epitaxy tools. Applied Materials held 53% of the epi market in 2004, per Gartner.",
            "The PMOS source and drain, the place where the epi tool works.",
        )
        .detail(
            "ASM International and Kokusai also make epi and furnace tools.",
            &["Applied Materials 53% of the epi market in 2004, Gartner via Applied release (ir.appliedmaterials.com)", "ASM International and Kokusai (textbook)"],
        ),
    Beat::new("Synopsys, Cadence, Arm: cells and layout", BEAT_MS)
        .note(
            "Layout, place-and-route and cell characterisation turn the pairs into chips. Arm sells cell libraries.",
            "The inverter pair as a standard cell, idle.",
        )
        .detail(
            "NVIDIA and AMD are fabless and take whatever PMOS drive the foundry gives.",
            &["Synopsys (SNPS) and Cadence (CDNS) do layout and characterisation (CHIP_PMOS.txt, section 8)", "Arm (ARM) sells cell libraries (CHIP_PMOS.txt, section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("holes stay the weaker carrier", BEAT_MS)
        .note(
            "Every node needs new strain or materials to keep the PMOS up, because holes stay the weaker carrier.",
            "Slow orange holes crawl through an unstrained channel.",
        )
        .detail(
            "Hole mobility is about a third of electron mobility in bulk silicon.",
            &["Holes ~450, electrons ~1400 cm2/Vs (textbook)"],
        ),
    Beat::new("boron and germanium are hard", BEAT_MS)
        .note(
            "Boron diffusion and germanium oxide quality limit the Ge-rich channels.",
            "Boron atoms drift from the source toward the channel.",
        )
        .detail(
            "Heavy boron can diffuse into the channel and roll off the threshold voltage.",
            &["Boron diffusion and TED (patent descriptions)", "Germanium oxide quality and junction leakage (CHIP_PMOS.txt, section 9)"],
        ),
    Beat::new("few epi tool vendors", BEAT_MS)
        .note(
            "Epitaxy tools come from few vendors, and current market shares are not public in the sources found.",
            "The SiGe source and drain highlighted in pink.",
        )
        .detail(
            "A tooling chokepoint: Applied held 53% of epi in 2004, and no current share was found.",
            &["Applied 53% of the epi market in 2004 (Gartner via Applied release)", "Current epi shares not found (CHIP_PMOS.txt, section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-2: Intel 90 nm and VLSI 2004", BEAT_MS)
        .note(
            "The first two sources: Intel's 90 nm strain gain and its 2004 PMOS drive figure.",
            "The whole chip pulls back, with the source tag on the screen.",
        )
        .detail(
            "The strain gain and the drive figure are measured values, not a model.",
            &[
                "[1] siliconsemiconductor.net/article/66624/Intel_strains_ahead_with_90nm",
                "[2] archive.vlsisymposium.org/14web/2004/technology/tec_pdf/SESSION 6.pdf",
            ],
        ),
    Beat::new("source 3: IBM SiGe nanosheet pFET", BEAT_MS)
        .note(
            "The IBM SiGe nanosheet pFET gives the strain and mobility figures for the gate-all-around PMOS.",
            "The whole chip, with the source tag on the screen.",
        )
        .detail(
            "Its abstract reports about 1 GPa of strain and +100% peak hole mobility.",
            &["[3] researcher.draco.res.ibm.com/publications/stacked-gate-all-around-nanosheet-pfet-with-highly-compressive-strained-silessinfgreater1-xlessinfgreatergelessinfgreaterxlessinfgreaterchannel"],
        ),
    Beat::new("sources 4-5: UCSB lecture and Applied", BEAT_MS)
        .note(
            "The inverter sizing comes from a UCSB lecture; the epi share comes from Applied's release.",
            "The whole chip, with the source tag on the screen.",
        )
        .detail(
            "The inverter ratio and the epi market share are both cited on the page.",
            &[
                "[4] ece.ucsb.edu/courses/ECE122/122_F14Banerjee/Slides/Lecture 9.pdf",
                "[5] ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-extends-leadership-position-epitaxy",
            ],
        ),
    Beat::new("sources 6-8: USPTO, ASAP7 and the cell library", BEAT_MS)
        .note(
            "The GAA source-drain patent, the ASAP7 cell paper and the standard-cell lecture close the list.",
            "The whole chip, with the source tag on the screen.",
        )
        .detail(
            "Each is cited on the page for the claim it supports.",
            &[
                "[6] image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11776998",
                "[7] arxiv.org/pdf/1807.11396",
                "[8] eng.biu.ac.il/temanad/files/2017/02/Lecture-4-Standard-Cell-Libraries.pdf",
            ],
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

/// One picture per `# ` section of the page, in order. Sections 3, 5, 6 and 7 are the same scenes as
/// zoom-ins c, d, b and e (CMOS pair, width ratio, SiGe strain, GAA).
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, ZC_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, ZD_BEATS),
    section!(6, ZB_BEATS),
    section!(7, ZE_BEATS),
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
