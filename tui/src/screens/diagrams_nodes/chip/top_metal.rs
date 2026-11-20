// CHIP tab, TOP METAL (tools/pbr3d/blender/chip_top_metal.py). The overview opens and closes on the
// whole-chip scene (chip_kit.py) and in between works on a detailed cut-away of M10-M14, the pad and
// the bump (chip_top_metal_detail.py), with beads riding the copper. Zoom a builds the M14 loop step
// by step; zooms b-e and sections 1-10 are cut-aways of the same parts.
//
// Sources: CHIP_TOP_METAL.txt sections 2-4, CHIP_TOP_METAL.details.txt (POWER GRID, CLOCK TRUNK,
// LONG WIRES, IR DROP, C4 BUMP), with the citations kept in each beat's `detail`.

use super::super::Node;
use super::super::blender::{BEAT_MS, Cell, Page, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the thick top: M10-M14", BEAT_MS)
        .note(
            "The top levels, M10-M14, are the thickest and widest copper on the chip. They carry power and the clock across the whole die, and the package bumps sit on top of them.",
            "The whole chip: the top tier lit amber across the top, the row of bumps above it, the thin wiring and transistors below.",
        )
        .detail(
            "Wires get fatter going up, because a wire's resistance falls with its cross-section.",
            &["M10-M14: thick, wide copper for the power grid and clock trunk (CHIP_TOP_METAL.txt, section 2)"],
        ),
    Beat::new("power comes in through a bump", BEAT_MS)
        .note(
            "Inside the top of the stack: supply current comes from the package substrate through a C4 solder bump, down through the aluminium bond pad and two thick vias, and onto an M14 VDD stripe. Bumps are spread over the whole die, so power enters right above the logic that uses it.",
            "Amber beads falling from the green substrate through the cut solder ball, the grey UBM and Al pad, and down the vias into the copper M14 stripe.",
        )
        .detail(
            "Flip-chip bumps feed power over the whole die, not only at the edge.",
            &[
                "C4 bumps at about 150 um pitch, alternating power, ground and signal (patent 8896118)",
                "The bump is drawn far smaller than life next to the wiring",
            ],
        ),
    Beat::new("the grid spreads it out", BEAT_MS)
        .note(
            "The M14 stripes alternate VDD and VSS across the die. The M13 rail under them ties the VDD stripes together, and current spreads along it both ways and drops through vias toward every cell.",
            "Orange VDD and blue VSS stripes across M14, the M13 rail glowing orange, and amber beads running out both ways and down the vias.",
        )
        .detail(
            "A wide, thick mesh keeps the grid's resistance low.",
            &["Power on thick upper layers; drop bounded by top-layer thickness (patent 11681854)"],
        ),
    Beat::new("the clock spine", BEAT_MS)
        .note(
            "The clock trunk runs on low-resistance upper metal so it reaches every block at nearly the same moment. Taps drop from it to the local clock trees in the levels below.",
            "A green spine along an M11 wire, short green taps down to M10, and green beads spreading out from the middle.",
        )
        .detail(
            "Low skew needs low resistance.",
            &["H-tree or mesh on low-resistance upper metal (CLOCK TRUNK, textbook)"],
        ),
    Beat::new("thick wire, low resistance", BEAT_MS)
        .note(
            "Resistance is R = rho x L / (W x T): for the same length, a wider, thicker wire has far less. Signals and current cross the fat M13 rail much faster than the narrower M11 wire below it.",
            "The same length of M11 wire glowing orange with beads crawling along it, and the M13 rail above glowing green with beads racing across.",
        )
        .detail(
            "Thickness and width are the levers.",
            &[
                "R = rho x L / (W x T) (CHIP_TOP_METAL.txt, section 3)",
                "Top-metal pitch and thickness are foundry-confidential",
            ],
        ),
    Beat::new("the return path: VSS", BEAT_MS)
        .note(
            "Every amp that comes in on VDD goes back out on VSS. Back on the whole chip, the return current climbs the ground grid to its own bumps.",
            "The whole chip again, the top tier lit and blue beads climbing to a VSS bump.",
        )
        .detail(
            "Power and ground bumps alternate across the die.",
            &["Bumps alternate power, ground and signal across the die (C4 BUMP, textbook)"],
        ),
];

const ZA_BEATS: &[Beat] = &[
    Beat::new("trench, barrier and seed", BEAT_MS)
        .note(
            "M14 is made like every other level, only bigger. Plasma etches wide trenches and via holes into the dielectric, then a thin TaN barrier and a copper seed coat every wall so the copper can neither escape nor fail to stick.",
            "The purple plasma in the openings, then empty trenches lined with dark blue barrier shells, and the via openings down to M13.",
        )
        .detail(
            "The same damascene loop as the thin levels.",
            &["TRENCH ETCH, BARRIER + SEED (TaN plus Cu PVD) (CHIP_TOP_METAL.txt, section 1)"],
        ),
    Beat::new("plate copper, then polish", BEAT_MS)
        .note(
            "Copper electroplates into the trenches and vias and keeps going past the top. The CMP pad then grinds the excess away down to the dielectric, leaving separate thick stripes, and a SiCN cap seals them.",
            "A copper slab growing over M14, the dark CMP pad sweeping across, and the pale green cap left on the polished stripes.",
        )
        .detail(
            "Plate, polish, cap.",
            &[
                "CU PLATE, then CMP (CHIP_TOP_METAL.txt, section 1)",
                "Top-metal thickness is foundry-confidential",
            ],
        ),
    Beat::new("pad, passivation and bump", BEAT_MS)
        .note(
            "Vias lift the top copper to an aluminium bond pad. SiN and polyimide seal the die, open only over the pad, and under-bump metal plus a solder ball turn the pad into a C4 bump.",
            "The grey Al pad on two vias, lilac SiN and amber polyimide around it, and the solder ball dropping onto the UBM.",
        )
        .detail(
            "The chip's last steps before packaging.",
            &["PAD + PASSIV, BUMP (patents 11189538, 12040293; C4 ~150 um pitch, patent 8896118)"],
        ),
];

// b-e play sections 3-6 seen from the other side, so they share those beats.
const ZB_BEATS: &[Beat] = S3_BEATS;
const ZC_BEATS: &[Beat] = S4_BEATS;
const ZD_BEATS: &[Beat] = S5_BEATS;
const ZE_BEATS: &[Beat] = S6_BEATS;

const S1_BEATS: &[Beat] = &[
    Beat::new("M14: the thick copper loop", BEAT_MS)
        .note(
            "The top levels are built with the same damascene loop as the thin ones, only wider and thicker: etch the trench, line it with a TaN barrier and copper seed, electroplate, then polish. Copper overfills the trenches and the CMP pad grinds it back to the dielectric.",
            "M13 and M14 copper in cut-away, a copper slab growing over the top, the grey CMP pad sweeping it off, and the pale green cap left on M14.",
        )
        .detail(
            "Same loop, bigger wires.",
            &[
                "TRENCH ETCH, BARRIER + SEED (TaN plus Cu PVD), CU PLATE, CMP (CHIP_TOP_METAL.txt, section 1)",
                "Top-metal pitch and thickness are foundry-confidential",
            ],
        ),
    Beat::new("bond pad and passivation", BEAT_MS)
        .note(
            "Thick vias carry the top copper up to an aluminium bond pad. Silicon nitride and then polyimide cover the whole die to seal it against moisture and scratches, with an opening left over each pad.",
            "Two thick vias from an M14 stripe up to the grey Al pad, the lilac SiN round it, and the amber polyimide with a gap over the pad.",
        )
        .detail(
            "The chip is sealed except at its pads.",
            &["PAD + PASSIV: bond pads, SiN and polyimide with openings (patents 11189538 and 12040293)"],
        ),
    Beat::new("UBM and the C4 bump", BEAT_MS)
        .note(
            "Under-bump metal (titanium, copper, nickel) fills the opening so solder can wet it without eating the pad. A solder ball goes on top: the C4 bump that joins the die to the package.",
            "The grey UBM plug and silver nickel cap filling the opening, and the solder ball dropping onto it, shown cut in half.",
        )
        .detail(
            "The last steps before packaging.",
            &[
                "C4 bumps at about 150 um pitch (patent 8896118)",
                "The bump is drawn far smaller than life next to the wiring",
            ],
        ),
];

const S2_BEATS: &[Beat] = &[
    Beat::new("transistors, contacts and M1-M4", BEAT_MS)
        .note(
            "At the bottom of the stack sit the transistors in the silicon, tungsten contacts down to their sources and drains, and the thin M1-M4 copper that wires up each logic cell. These are the densest wires on the chip.",
            "Pink and blue source/drain blocks and grey gates in the dark silicon, thin tungsten plugs above them, and rows of tiny copper lines.",
        )
        .detail(
            "Thin wires for density.",
            &[
                "M1-M4 thin copper for cell wiring (CHIP_TOP_METAL.txt, section 2)",
                "Intel 4 M0 pitch: 30 nm (WikiChip)",
            ],
        ),
    Beat::new("M5-M9: block wiring", BEAT_MS)
        .note(
            "The middle levels are about twice as wide and tall and carry signals between blocks. Each level runs at right angles to the one below, and vias join them.",
            "The cut-away alternating between rows of copper cross-sections and long copper bars, joined by vertical vias.",
        )
        .detail("Medium wires for reach.", &["M5-M9 medium copper for block signals (CHIP_TOP_METAL.txt, section 2)"]),
    Beat::new("M10-M14, pad and bump", BEAT_MS)
        .note(
            "The top levels are the widest and thickest: M10-M12 for long wires and the clock, M13-M14 for the power grid. The pad and the C4 bump sit on top, and every transistor below gets its power through them.",
            "A few big copper lines at the top of the column, the amber polyimide and grey UBM, and the solder ball cut in half.",
        )
        .detail(
            "Thick wires for current.",
            &[
                "M10-M14 thick, wide copper for power grid and clock trunk (CHIP_TOP_METAL.txt, section 2)",
                "C4 bumps at about 150 um pitch",
            ],
        ),
];

const S3_BEATS: &[Beat] = &[
    Beat::new("POWER GRID", BEAT_MS)
        .note(
            "Power enters at the bump, runs along the redistribution layer to the pad and down into the grid. The thick M14 stripes alternate VDD and VSS; the M13 rail under them ties the VDD stripes together and feeds the vias down to every cell.",
            "Orange VDD and blue VSS stripes across M14, the M13 rail glowing orange, and amber dots running down from the bump and out both ways along the rail.",
        )
        .detail(
            "Wide, thick rails keep the grid's resistance low.",
            &[
                "Power on thick upper layers; drop bounded by top-layer thickness (patent 11681854)",
                "R = rho x L / (W x T): thicker, wider wires cut R",
            ],
        ),
    Beat::new("CLOCK spine and LONG WIRES", BEAT_MS)
        .note(
            "The clock trunk runs on low-resistance upper metal so it reaches every block with little skew; taps drop down to the local clock trees. Long buses crossing the die use the same thick levels.",
            "A green spine along the M11 wire with taps glowing down to M10, green dots spreading out from the middle, and cyan dots along an M12 bus.",
        )
        .detail(
            "Reach and skew both need low resistance.",
            &["H-tree or mesh on low-resistance upper metal (CLOCK TRUNK, textbook)"],
        ),
    Beat::new("RDL and UNDERFILL", BEAT_MS)
        .note(
            "A redistribution layer is a copper trace on the polyimide that moves a connection from the pad to wherever the bump pattern needs it. Underfill epoxy then fills the gap between die and substrate and shares the strain, so the joints last.",
            "The copper RDL trace running right from the pad to the bump, olive underfill round the cut solder ball, and the green package substrate above.",
        )
        .detail(
            "The package side.",
            &[
                "RDL re-routes pads to the bump pattern (patent 11798904)",
                "Underfill: >10x flip-chip fatigue life (Semiconductor History Museum of Japan)",
            ],
        ),
];

const S4_BEATS: &[Beat] = &[
    Beat::new("from the VRM to the transistor", BEAT_MS)
        .note(
            "Current comes from the voltage regulator on the board through the package, into the bump and pad, then down the via stack through M14, M13, M12 and below to the cell rails and the transistors. Every stage has resistance.",
            "Amber dots falling from the green substrate through the solder ball, the pad and the vias, down the column at the centre of the block.",
        )
        .detail(
            "A long path, every step resistive.",
            &[
                "VRM, package planes, bumps, M14 down to M1, cell rail (CHIP_TOP_METAL.txt, section 4)",
                "0.9 V is an illustrative supply",
            ],
        ),
    Beat::new("IR DROP along the rail", BEAT_MS)
        .note(
            "Every stage loses V = I x R. Along the M13 rail the voltage is highest under the bump and falls with distance from it. Designers tolerate roughly 10% total droop from supply to transistor.",
            "The M13 rail coloured pale yellow under the bump, fading to red at both ends, with amber dots flowing outward.",
        )
        .detail(
            "The die sees what is left.",
            &["Roughly 10% total droop tolerated (IR DROP, secondary)"],
        ),
    Beat::new("EM LIMIT at the vias", BEAT_MS)
        .note(
            "The vias under the bump carry the most current per area. Copper takes only so much current density before electromigration opens a void, so designers widen wires and put many vias in parallel.",
            "The via stack glowing orange-red with dense dots, and a black void growing at the foot of the M14 via.",
        )
        .detail(
            "Wider wires and redundant vias are the fix.",
            &[
                "Damascene Cu about 1-3e6 A/cm2 (secondary)",
                "Copper about 5x aluminium's limit (Synopsys glossary)",
            ],
        ),
];

const S5_BEATS: &[Beat] = &[
    Beat::new("C4 BUMP: about 150 um", BEAT_MS)
        .note(
            "A C4 bump is a solder ball joining the die to an organic package substrate, at about 150 um pitch. It is cheap and robust, but only a few dozen fit in each square millimetre.",
            "Two grey solder balls, cut in half, between the dark die above and the green layered substrate below.",
        )
        .detail(
            "The classic flip-chip joint.",
            &[
                "C4 about 150 um pitch (patent 8896118)",
                "About 44 per mm2 at 150 um pitch",
            ],
        ),
    Beat::new("MICROBUMP: about 40 um", BEAT_MS)
        .note(
            "Chiplets sit on a silicon interposer on copper pillars with a solder cap, at about 40 um pitch: 20-25 um bumps with 15 um gaps. The pitch is expected to hit a wall near 10 um.",
            "A row of copper pillars with grey solder caps between the chiplet above and the grey interposer below, at the same scale as the C4 balls.",
        )
        .detail(
            "Over ten times the density of C4.",
            &[
                "40 um pitch = 20-25 um bump + 15 um space (SemiEngineering)",
                "About 625 per mm2 at 40 um pitch",
            ],
        ),
    Beat::new("HYBRID BOND: 10 um and below", BEAT_MS)
        .note(
            "In hybrid bonding two dies are polished flat and pressed face to face. Copper pads bond straight to copper and oxide to oxide, with no solder, at 10 um pitch and below.",
            "Two dies face to face, a thin band of copper pads alternating with pale oxide where they meet.",
        )
        .detail(
            "Smaller pitch, more connections per mm2.",
            &[
                "Direct Cu-Cu, 10 um pitch and below (SemiEngineering)",
                "About 10,000 per mm2 at 10 um pitch",
            ],
        ),
];

const S6_BEATS: &[Beat] = &[
    Beat::new("front-side power: one shared stack", BEAT_MS)
        .note(
            "Today power and signals share the front stack. Power enters at bumps on top and must travel down every level to reach the transistors, taking routing tracks from signals and losing voltage on the way.",
            "The left column: solder bumps on top, amber dots falling through the whole wiring stack to the devices, cyan signal dots on a thin level.",
        )
        .detail(
            "Congestion and droop come from sharing.",
            &["Today power and signals share the front stack (CHIP_TOP_METAL.txt, section 6)"],
        ),
    Beat::new("BSPDN: power from behind", BEAT_MS)
        .note(
            "With backside power the wafer is bonded face down to a carrier and its silicon thinned from the back. Backside metal levels are built there, nano-TSVs pass up through the thin silicon to the devices, and the bumps go on the back.",
            "The right column: the grey carrier wafer on top, copper nano-TSVs through the thin silicon, the BM levels and bumps underneath, and amber dots rising from below.",
        )
        .detail(
            "Intel PowerVia and TSMC A16 both move power to the back.",
            &[
                "Intel PowerVia (18A): nano-TSVs; TSMC A16: contacts to source/drain (intel.com, tomshardware.com)",
                "Drawn: BM0-BM2; Intel lists BM0-BM5",
            ],
        ),
    Beat::new("the gains", BEAT_MS)
        .note(
            "With power on the back, the front levels carry signals only and the power path is short and fat. Intel's PowerVia test chip showed over 30% lower droop and over 6% higher speed.",
            "Both columns side by side: power falling the length of the left one, rising a short way in the right one, signals on the front of each.",
        )
        .detail(
            "Less droop, more room for signals.",
            &[
                "PowerVia test chip: >30% lower droop, >6% performance (Intel 4 test chip)",
                "Intel 18A brief: about 10x lower worst-case dynamic droop (vendor claim)",
            ],
        ),
];

const S7_BEATS: &[Beat] = &[
    Beat::new("pitches: C4 to hybrid", BEAT_MS)
        .note(
            "The same width of die edge, three ways to connect it: one C4 ball at about 150 um pitch, a few microbumps at 40 um, a dense row of hybrid-bonded pads at 10 um and below.",
            "Three windows at one scale: one solder ball on green substrate, a row of copper pillars, and a fine stripe of copper pads between two dies.",
        )
        .detail(
            "Smaller pitch, more connections per mm2.",
            &["C4 ~150 um, microbump 40 um, hybrid bond 10 um and below (patent 8896118, SemiEngineering)"],
        ),
    Beat::new("Intel 4: 16 metal layers", BEAT_MS)
        .note(
            "Intel 4 stacks 16 metal layers, from M0 at 30 nm pitch up to thick top levels. Each level is another pass of the damascene loop, so the layer count drives the number of etch, plating and CMP steps.",
            "One cut-away column of sixteen copper levels, tiny lines at the bottom widening to a few thick bars at the top.",
        )
        .detail(
            "Pitches between M0 and the top are drawn schematically.",
            &[
                "Intel 4: M0 pitch 30 nm, 16 metal layers (WikiChip)",
                "PowerVia relaxes M0 from 30 to 36 nm (SemiAnalysis)",
            ],
        ),
    Beat::new("money", BEAT_MS)
        .note(
            "The foundries that build these stacks dwarf the companies whose software checks them: TSMC took about US$122B in 2025 and Intel $52.9B, while Synopsys and Cadence took $7.1B and $5.3B.",
            "Four bars on one scale: TSMC tallest, Intel about half its height, and two small blue bars for Synopsys and Cadence.",
        )
        .detail(
            "Foundries against tool vendors.",
            &["Intel FY2025 $52.9B; TSMC 2025 about US$122B; Synopsys FY2025 $7.1B; Cadence 2025 $5.3B (filings, section 10)"],
        ),
];

const S8_BEATS: &[Beat] = &[
    Beat::new("TSMC and Intel: backside contacts", BEAT_MS)
        .note(
            "Both big foundries now offer backside power, wired differently. Intel's PowerVia runs a nano-TSV up beside the transistor to its front contact. TSMC's A16 Super Power Rail goes further and contacts the source directly from the back.",
            "Top: Intel, a copper nano-TSV rising beside the transistor to the front contact. Bottom: TSMC, a short copper contact straight up into the pink source. Amber dots climb both.",
        )
        .detail(
            "TSMC (TSM) and Intel (INTC) are the two fabs.",
            &[
                "Intel PowerVia on 18A in Panther Lake (SemiAnalysis teardown)",
                "TSMC A16: volume ~Q4 2026; +8-10% speed or -15-20% power vs N2P",
            ],
        ),
    Beat::new("NVIDIA, AMD, Arm: huge currents", BEAT_MS)
        .note(
            "The biggest GPUs and CPUs set the current the grid must carry: around a kilowatt at under a volt is over a thousand amps. NVIDIA and AMD build them on TSMC; Arm core IP has to fit each foundry's power grid.",
            "Three thick streams of amber dots pouring down the via stack under the bump, the VDD and VSS stripes lit.",
        )
        .detail(
            "Designers set the load.",
            &["~1 kW at under 1 V means over 1,000 A (estimate)"],
        ),
    Beat::new("Synopsys, Cadence: sign-off", BEAT_MS)
        .note(
            "Before tape-out the whole grid is simulated for IR drop and electromigration. Synopsys (which now owns Ansys RedHawk-SC) and Cadence (Voltus) sell the sign-off tools that produce maps like this one.",
            "Looking down on the top of the grid: a map of tiles, pale near the two bump sites and red where they are furthest from both.",
        )
        .detail(
            "Software checks every rail.",
            &["Synopsys FY2025 $7.1B; Cadence 2025 $5.3B (filings)"],
        ),
];

const S9_BEATS: &[Beat] = &[
    Beat::new("IR drop and electromigration", BEAT_MS)
        .note(
            "Droop builds from the grid down to the cell rail, worse with fast changes in current. Meanwhile electromigration slowly opens voids in the vias and thin wires that carry the most current.",
            "The M13 rail fading from pale yellow to red at its ends, and a black void growing at the foot of a via on the right.",
        )
        .detail(
            "Wider grids, more bumps, capacitors, redundant vias.",
            &["Every stage drops V = I x R (IR DROP, secondary); EM in wires and vias (Synopsys glossary)"],
        ),
    Beat::new("bridging at fine pitch", BEAT_MS)
        .note(
            "At microbump pitch there is little room between joints. If too much solder flows, two neighbouring caps run together and short. Copper pillars and then hybrid bonds, with no solder, are the fix.",
            "Four copper pillars on their solder caps, two of the caps merging into one red-glowing bridge.",
        )
        .detail(
            "Less solder, smaller pitch.",
            &["Bump bridging at fine pitch: Cu pillars, hybrid bonds (CHIP_TOP_METAL.txt, section 9)"],
        ),
    Beat::new("thermal-cycle fatigue", BEAT_MS)
        .note(
            "Silicon and the organic substrate expand by different amounts as the chip heats and cools, so every cycle shears the C4 joints. Cracks start at the neck by the die. Underfill shares the load and gives over ten times the life.",
            "The green substrate sliding back and forth under the die, a red crack spreading at the top of the solder ball, then olive underfill filling the gap.",
        )
        .detail(
            "Underfill is the standard fix.",
            &[
                "Si ~3 ppm/K vs organic substrate ~15 ppm/K (typical values)",
                "Underfill: over 10x fatigue life (Semiconductor History Museum of Japan)",
            ],
        ),
];

const S10_BEATS: &[Beat] = &[
    Beat::new("sources: backside power, Intel and TSMC", BEAT_MS)
        .note(
            "The sources behind this page, in four groups. The first cover backside power and the TSMC A16 claims in sections 6 and 8.",
            "The top of the stack from the front right: M10-M14 in cut-away, the pad, the bump and the substrate.",
        )
        .detail(
            "Vendor pages and tech press.",
            &[
                "[1] intel.com/content/www/us/en/foundry/process/18a.html; tomshardware.com/news/intel-details-powervia-backside-power-delivery-network",
                "[2] anandtech.com/show/21369; tomshardware.com/tech-industry/tsmc-unveils-16nm-process-technology-with-backside-power-delivery-rivals-intels-competing-design",
            ],
        ),
    Beat::new("sources: bump pitch and power delivery", BEAT_MS)
        .note(
            "These cover the bump pitches and the power-delivery claims in sections 4 and 5.",
            "Close on the C4 bump, the UBM and the pad.",
        )
        .detail(
            "Patents and SemiEngineering.",
            &[
                "[3] image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8896118",
                "[4] semiengineering.com/scaling-bump-pitches-in-advanced-packaging; semiengineering.com/bumps-vs-hybrid-bonding-for-advanced-packaging",
                "[5] semiengineering.com/current-problems-grow-for-power-delivery/; patsnap.com/resources/blog/articles/back-side-power-delivery-networks-cut-ir-drop-by-10/",
            ],
        ),
    Beat::new("sources: stacks, EM, bonding", BEAT_MS)
        .note(
            "These cover the Panther Lake teardown, TSMC's power rail, the Intel 4 stack, imec's backside work and the electromigration limits.",
            "The power grid seen from above and to the left: the thick M14 stripes and the M13 rail.",
        )
        .detail(
            "Teardowns, process pages and EM references.",
            &[
                "[6] newsletter.semianalysis.com/p/intel-panther-lake-teardown",
                "[7] trendforce.com/news/?p=19205",
                "[8] fuse.wikichip.org/news/6720/a-look-at-intel-4-process-technology/3; anandtech.com/show/17448",
                "[9] imec-int.com/en/articles/how-power-chips-backside",
                "[10] synopsys.com/glossary/what-is-electromigration.html; rfessentials.com/rf-knowledge-base/what-is-the-electromigration-limit-of-a-gold-or-copper-interconnect-in-an-rf-mmi/",
            ],
        ),
    Beat::new("sources: revenue, C4 history, EDA", BEAT_MS)
        .note(
            "The last group covers the revenue figures, the C4 and underfill history and the EDA tools.",
            "The whole top of the stack nearly face on, substrate to M10.",
        )
        .detail(
            "Filings and history.",
            &[
                "[11] intc.com/news-events/press-releases/detail/1759; news.synopsys.com/2025-12-10-Synopsys-Posts-Financial-Results-for-Fourth-Quarter-and-Fiscal-Year-2025; businesswire.com/news/home/20260216202086/en",
                "[12] seas.ucla.edu/ethinfilm/Pb-freeWorkshop/abs/totta.html; shmj.or.jp/english/pdf/pkg/exhibi515E.pdf",
                "[13] synopsys.com; cadence.com (tool names are vendor products, textbook)",
            ],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal_zoom_d.glb"),
        ZD_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_top_metal_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the top loop: metal, pads, bumps",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "jobs of the thick levels",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "power delivery and IR drop",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "bumps to hybrid bonds",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "backside power (BSPDN)",
        build: zoom_e,
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_top_metal_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, S1_BEATS),
    section!(2, S2_BEATS),
    section!(3, S3_BEATS),
    section!(4, S4_BEATS),
    section!(5, S5_BEATS),
    section!(6, S6_BEATS),
    section!(7, S7_BEATS),
    section!(8, S8_BEATS),
    section!(9, S9_BEATS),
    section!(10, S10_BEATS),
];

pub const NODE: Node = Node {
    page: "TOP METAL",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            super::super::super::blender::explained(s.as_ref(), z.label);
            super::super::super::blender::draws_every_beat(s.as_ref(), z.label);
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3, 3, 3, 3, 3, 4]);
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
