// CHIP tab, FINFET: the overview is the whole-chip scene (tools/pbr3d/blender/chip_finfet.py,
// built on chip_kit.py) zoomed in on the NMOS, which is a FinFET here. Six beats: the whole chip,
// the planar channel it replaces, the fin standing up, the gate wrapping three sides, the channel
// on with current along the fin, and the gate low with the channel pinched shut.
//
// Zoom-ins a-e and sections 1-10 are the same silicon and fin, the camera on the part each one
// explains (chip_finfet.py, zoom_* and sec* builders). Three beats each.
//
// Sources: Intel 22 nm Tri-Gate, realworldtech.com/?p=1082 and techradar.com (2011 press); TSMC 16FF+,
// pr.tsmc.com/english/news/1835; SAQP fin patterning, USPTO 10121785; TSMC FinFlex, tsmc.com blog
// 2022-06-16. Textbook items are marked as such.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("whole chip: the NMOS is a FinFET", BEAT_MS)
        .note(
            "This transistor is the NMOS of the chip, and at this node it is a FinFET: the same chip as the hero, with this one picked out.",
            "the cyan box round the NMOS, a narrow fin standing where the planar NMOS sits in the hero",
        )
        .detail(
            "Intel shipped the first volume FinFET, the 22 nm Tri-Gate, in 2012; TSMC's 16FF+ followed in 2015.",
            &[
                "Intel 22 nm Tri-Gate: announced 2011, Ivy Bridge 2012 (realworldtech.com/?p=1082)",
                "TSMC 16FF+: risk production, November 2014 (pr.tsmc.com/english/news/1835)",
            ],
        ),
    Beat::new("planar: the channel lies flat under one face of the gate", BEAT_MS)
        .note(
            "A planar gate sits on top of a flat channel, so it controls the channel from one face. As the gate shrinks, that one face loses its grip and the channel leaks.",
            "a translucent gate lying flat over the cyan channel in the silicon, with no fin yet",
        )
        .detail(
            "One gated face, against three for a fin (textbook). Press coverage of the 2011 announcement compared 22 nm with 32 nm planar.",
            &[
                "One gated face against three (textbook)",
                "Intel 22 nm vs 32 nm planar: up to 37% lower gate delay at low voltage (techradar.com)",
            ],
        ),
    Beat::new("rise: the channel stands up as a fin", BEAT_MS)
        .note(
            "The planar gate goes, and the channel is stood up as a thin silicon fin rising out of the substrate. The source and drain are raised at its two ends.",
            "the blue fin growing out of the silicon, with raised source and drain blocks at either end",
        )
        .detail(
            "The fin's height and width set the channel's effective width. The fins are patterned at a quarter of the litho pitch by SAQP.",
            &[
                "Weff = 2 x Hfin + Wfin per fin (textbook)",
                "Fins patterned by SAQP, a quarter of the litho pitch (USPTO 10121785)",
            ],
        ),
    Beat::new("wrap: the gate wraps the fin on three sides", BEAT_MS)
        .note(
            "The gate drapes over the fin's top and both sidewalls, with a thin high-k dielectric between, so it touches the channel on three faces. The bottom stays ungated.",
            "a grey cap over the fin, the gate wall behind it, and the glass front wall the fin shows through",
        )
        .detail(
            "Three gated faces give the gate more control of the channel, which suppresses short-channel effects such as drain-induced barrier lowering (textbook).",
            &[
                "Three gated faces against one planar face (textbook)",
                "High-k dielectric and work-function metal over the top and sidewalls (textbook)",
            ],
        ),
    Beat::new("on: the channel fills the fin and current runs source to drain", BEAT_MS)
        .note(
            "With the gate high, the channel forms through the whole height of the fin, and electrons run along it from the source to the drain.",
            "the gate cap glowing orange, the channel glowing cyan under the gate, and dots running along the fin",
        )
        .detail(
            "Drive comes in whole fins, so a device is 1, 2 or 3 fins wide. TSMC's FinFlex on N3 lets each block pick its fin count.",
            &[
                "Width in whole fins: 1, 2 or 3 per device (textbook)",
                "TSMC FinFlex on N3: 1, 2 or 3 fins per block (tsmc.com blog, 2022)",
            ],
        ),
    Beat::new("off: the three faces pinch the channel shut, so less leaks", BEAT_MS)
        .note(
            "With the gate low, the wrapped channel is pinched shut from three sides, so less current leaks. The path left under the fin is blocked by a punch-through stop dopant.",
            "the channel gone, the gate cap dark, the fin blue again, and the chip back to the hero's whole view",
        )
        .detail(
            "Intel's 22 nm Tri-Gate was reported at more than 50% less power than planar at the same performance. Sub-fin leakage is the path left under the fin.",
            &[
                "Intel 22 nm: more than 50% less power at the same performance (press, 2011)",
                "Sub-fin leakage blocked by punch-through stop doping (textbook)",
            ],
        ),
];

// ---- zoom-ins a-e ----------------------------------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("SAQP: masks at a quarter of the litho pitch", BEAT_MS)
        .note(
            "Self-aligned quadruple patterning prints a mask, then splits each line into four with spacers, so the fins come out finer than lithography could print.",
            "a row of thin grey mask stripes standing on the flat silicon, seen in cross-section across the fins",
        )
        .detail(
            "The spacers are deposited and etched twice, so one printed line becomes four.",
            &["SAQP fin patterning (USPTO 10121785)"],
        ),
    Beat::new("FIN FORM: the silicon between the masks is etched", BEAT_MS)
        .note(
            "Etching between the masks leaves silicon fins standing. The masks go, and the fins rise out of the surface to their full height.",
            "the grey masks gone, the blue fins grown up from the silicon, each one as tall as the gate will wrap",
        )
        .detail(
            "The fin is silicon tens of nm tall; its height and width set the channel's effective width.",
            &["Hfin tens of nm, Wfin single-digit to about 10 nm (page text, section 2)"],
        ),
    Beat::new("FIN REVEAL: oxide fills and is etched back", BEAT_MS)
        .note(
            "Oxide fills the gaps between the fins and is recessed to expose their tops. The oxide isolates the fins from one another below.",
            "the see-through oxide sinking to about half the fin height, with the upper part of each fin standing clear",
        )
        .detail(
            "The reveal height sets how much of each fin the gate can wrap.",
            &["FIN REVEAL: oxide recessed to expose the fin tops (page text, section 1)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("high-k: the dielectric coats the top and both sidewalls", BEAT_MS)
        .note(
            "A thin high-k dielectric coats the top and both sidewalls of the fin, between the silicon and the gate metal.",
            "the pale high-k over the fin top and its two sidewalls, the fin's blue showing under it",
        )
        .detail(
            "The dielectric is what lets the gate hold charge in the channel without leaking through.",
            &["High-k dielectric, HfO2-based (page text, section 2)"],
        ),
    Beat::new("gate metal: three sides, not four", BEAT_MS)
        .note(
            "Work-function metal and fill metal drape over the top and both sidewalls. The gate touches the channel on three faces.",
            "the grey gate cap on top, the back wall behind the fin, and the glass front wall with the fin showing through",
        )
        .detail(
            "Each fin's gated width counts twice its height plus its width, so a taller fin is a wider device.",
            &["Weff = 2 x Hfin + Wfin per fin (page text, section 2)"],
        ),
    Beat::new("on: current runs along the fin, the bottom stays ungated", BEAT_MS)
        .note(
            "With the gate high the channel turns on through the fin's height, and electrons run from source to drain. The fin's bottom has no gate, so a path is left under it.",
            "the gate cap and the channel glowing, electron dots along the fin, and faint dots along the fin base",
        )
        .detail(
            "The gate keeps control at short lengths; the path under the fin is blocked by a punch-through stop doping.",
            &[
                "Intel 22 nm tri-gate, 2011 (realworldtech.com/?p=1082)",
                "Sub-fin leakage blocked by punch-through stop doping (page text, section 2)",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("one fin: the smallest device", BEAT_MS)
        .note(
            "The smallest FinFET is one fin wide. It is dense, but gives the least drive.",
            "a single fin seen from above, its gate across it",
        )
        .detail(
            "Width is quantised: one fin is the smallest step.",
            &["Width in whole fins: 1, 2 or 3 per device (page text, section 1)"],
        ),
    Beat::new("two fins: twice the drive", BEAT_MS)
        .note(
            "Two fins side by side under one gate double the drive. Two is the common logic width.",
            "two fins side by side, their gate lines running across both",
        )
        .detail(
            "Drive comes in whole fins, not in steps of width.",
            &["QUANTIZED W, FIN COUNT 1-3 (page text, section 1)"],
        ),
    Beat::new("three fins: for the fastest cells", BEAT_MS)
        .note(
            "Three fins give the most drive of the three widths, for the fastest cells.",
            "three fins side by side, the gate across all of them",
        )
        .detail(
            "A device is 1, 2 or 3 fins wide, never a fraction of a fin.",
            &["FIN COUNT 1-3 (page text, section 1)"],
        ),
];

const FINFLEX_BEATS: &[Beat] = &[
    Beat::new("FinFlex 3-2: speed", BEAT_MS)
        .note(
            "Blocks built from three-fin and two-fin cells on one N3 die, for the fastest logic.",
            "a block of three-fin cells beside a block of two-fin cells, seen from above",
        )
        .detail(
            "FinFlex lets each block pick its fin count.",
            &["FINFLEX on N3: 3-2, 2-2 or 2-1 fins per block (tsmc.com blog, 2022)"],
        ),
    Beat::new("FinFlex 2-2: balanced", BEAT_MS)
        .note(
            "Two-fin cells throughout. Every FinFlex option uses two-fin cells as its base.",
            "two blocks of two-fin cells of the same height",
        )
        .detail(
            "The balanced option sits between speed and density.",
            &["All options use 2-fin cells as the base (page text, section 5)"],
        ),
    Beat::new("FinFlex 2-1: low power, dense", BEAT_MS)
        .note(
            "Two-fin and one-fin cells for the densest, lowest-power blocks, at 0.64x to 0.85x of N5's 2-2 cell area.",
            "a two-fin block beside a shorter one-fin block",
        )
        .detail(
            "The density range is TSMC's claim, not a measurement.",
            &["0.64x to 0.85x of N5's 2-2 cell area (TSMC claim, page text, section 5)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("fin limits: thinner and taller", BEAT_MS)
        .note(
            "To shrink, fins get thinner and taller. Thin fins vary from device to device, and tall fins bend and taper.",
            "one tall, thin fin, narrower and taller than the fins before it",
        )
        .detail(
            "Fin limits are textbook limits; no sourced figure is given here.",
            &["FIN LIMITS: thin fins vary, tall fins bend and taper (textbook)"],
        ),
    Beat::new("leakage: sub-fin, GIDL and tunnelling", BEAT_MS)
        .note(
            "More leakage paths open as the fin shrinks: under the fin, at the gate-to-drain edge and through the thin oxide.",
            "dots leaking along the silicon at the fin base, under the gate",
        )
        .detail(
            "The bottom of the fin stays ungated, so the leak under it grows.",
            &["LEAKAGE: sub-fin, GIDL and tunnelling grow (textbook)"],
        ),
    Beat::new("nanosheets: the answer is gate on four sides", BEAT_MS)
        .note(
            "The fin splits into stacked sheets wrapped on all four sides: gate-all-around, the industry's answer below 3 nm.",
            "three sheets inside the glass gate wall, the gate round every face of each one",
        )
        .detail(
            "Nanosheets come at N2; Samsung already has its first GAA at 3 nm.",
            &["Nanosheets (GAA) at N2 (page text, section 7)", "Samsung GAA at 3 nm (page text, section 7)"],
        ),
];

// ---- sections 1-10 --------------------------------------------------------------------------

const SEC1_BEATS: &[Beat] = &[
    Beat::new("fins: the channel stands up", BEAT_MS)
        .note(
            "The channel is stood up as a fin, and the planar gate on top of it goes. The source and drain are raised at the fin's ends.",
            "the blue fin rising from the silicon, with the raised source and drain blocks at either end",
        )
        .detail(
            "Planar ran out at 22 and 28 nm, where the flat channel lost control of the gate.",
            &["FIN FORM: the channel stands up as a fin (page text, section 1)"],
        ),
    Beat::new("gate wrap: three sides", BEAT_MS)
        .note(
            "The high-k and gate metal wrap the top and both sidewalls of the fin, so the gate controls the channel from three faces.",
            "the grey gate over the fin, its glass front wall with the fin showing through",
        )
        .detail(
            "Three gated faces against one for planar (textbook).",
            &["GATE WRAP: three sides (page text, section 1)"],
        ),
    Beat::new("width: 1, 2 or 3 fins", BEAT_MS)
        .note(
            "A device is one, two or three fins wide, so its drive steps in whole fins: one fin, then two, then three.",
            "one fin, then two, then three fins side by side under the gate",
        )
        .detail(
            "Width is quantised, so the fin count is the design choice.",
            &["QUANTIZED W, FIN COUNT 1-3 (page text, section 1)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("Hfin and Wfin: the fin is tens of nm tall", BEAT_MS)
        .note(
            "The fin is silicon, tens of nanometres tall (Hfin) and single-digit to about 10 nm wide (Wfin). Cut across, it is a tall narrow bar.",
            "one fin cut across, tall and narrow, with the labels on its height and its width",
        )
        .detail(
            "The effective width per fin is 2 x Hfin + Wfin, so the height counts twice.",
            &[
                "Hfin tens of nm, Wfin single-digit to about 10 nm (page text, section 2)",
                "Weff = 2 x Hfin + Wfin per fin (page text, section 2)",
            ],
        ),
    Beat::new("high-k and gate metal wrap the fin", BEAT_MS)
        .note(
            "The high-k dielectric (HfO2-based) and the gate metal wrap the top and both sidewalls of the fin, the gate ring around it.",
            "the fin cut through its gate: the high-k and the gate ring around the fin, the front wall in glass",
        )
        .detail(
            "Planar had one gated face; the fin has three.",
            &[
                "High-k dielectric, HfO2-based (page text, section 2)",
                "One gated face for planar, three for the fin (page text, section 2)",
            ],
        ),
    Beat::new("the bottom is not gated: sub-fin leakage", BEAT_MS)
        .note(
            "Below the fin the gate has no grip, so a path is left under it. Punch-through-stop doping under the STI oxide blocks most of the leak.",
            "faint dots along the silicon at the fin base, the gate ring above and the fin standing up from the surface",
        )
        .detail(
            "The bottom is the one face the gate does not reach.",
            &["Sub-fin leakage blocked by punch-through stop doping under STI oxide (page text, section 2)"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("INTEL 22 and TSMC 16: the FinFET goes to volume", BEAT_MS)
        .note(
            "Intel's 22 nm tri-gate was announced in 2011 and shipped in Ivy Bridge in 2012. TSMC's 16FF+ followed in 2015, with a 90 nm gate pitch.",
            "a row of gates along one fin at the N16 spacing; the spacing is to scale in ratio, not in nanometres",
        )
        .detail(
            "The fin was stretched from 22 nm to N3E, not replaced.",
            &[
                "Intel 22 nm: 2011 tri-gate, Ivy Bridge (page text, section 3)",
                "TSMC 16FF+ against 20 nm planar, 2015 (page text, section 3)",
                "TSMC N16 contacted gate pitch 90 nm (page text, section 4)",
            ],
        ),
    Beat::new("TSMC N7 and N5: the gate pitch tightens", BEAT_MS)
        .note(
            "N7 has a 57 nm gate pitch and N5 has 51 nm; the two rows are drawn together, the lower one the tighter.",
            "two gate rows along their fins, the N5 row at the tighter spacing below the N7 row",
        )
        .detail(
            "The N7 pitch is a WikiChip estimate; the N5 figures come from an Apple A15 SEM.",
            &[
                "N7 gate pitch 57 nm and fin pitch 30 nm (est, WikiChip)",
                "N5 gate pitch 51 nm and fin pitch 28 nm (A15 SEM, angstronomics.com)",
            ],
        ),
    Beat::new("TSMC N3: 45 nm gate pitch", BEAT_MS)
        .note(
            "N3 has a 45 nm gate pitch, the tightest of the three rows. The fin was stretched to get here, not replaced.",
            "one row at the N3 spacing, its gates the narrowest of the three",
        )
        .detail(
            "Samsung went from 14 nm FinFET to its first GAA at 3 nm.",
            &[
                "N3 gate pitch 45 nm (techinsights.com, semiengineering.com)",
                "Samsung: 14 nm FinFET, first GAA at 3 nm (page text, section 3)",
            ],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("N7: about 91 million transistors per mm2 (est)", BEAT_MS)
        .note(
            "A fixed square holds a grid of transistor tiles. N7 fits the fewest tiles of the three.",
            "a 6-by-6 grid of tiles in a fixed frame, seen from above; the tile count is a picture, not a count",
        )
        .detail(
            "Density is a WikiChip estimate.",
            &["N7 about 91.2 MTr/mm2 (est, WikiChip)"],
        ),
    Beat::new("N5: about 138 million transistors per mm2", BEAT_MS)
        .note(
            "N5 packs more tiles into the same square than N7 does.",
            "a denser 7-by-8 grid in the same frame",
        )
        .detail(
            "The N5 figure is measured on an Apple A15 die.",
            &["N5 about 137.6-138.2 MTr/mm2 (A15 SEM)"],
        ),
    Beat::new("N3: 1.6x N5", BEAT_MS)
        .note(
            "TSMC claims N3E packs about 1.6 times the density of N5, blending cell types. The grid is the densest of the three.",
            "a 9-by-10 grid in the same frame, the most tiles of the three",
        )
        .detail(
            "This is a TSMC claim, not a measurement.",
            &["N3E 1.6x N5 density (TSMC claim, blends cell types)"],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("7 nm and below: 74% of 2025", BEAT_MS)
        .note(
            "TSMC's FinFET nodes at 7 nm and below were 74% of its 2025 wafer revenue, up from 69% in 2024.",
            "the tallest bar lit, 7 nm and below, beside two shorter bars for 5 nm and 3 nm",
        )
        .detail(
            "The quarterly share ran from 73% to 77%.",
            &["7 nm and below: 74% of 2025, 69% in 2024 (TSMC mix, page text, section 6)"],
        ),
    Beat::new("5 nm: about 35 to 37%", BEAT_MS)
        .note(
            "5 nm was the largest single node, at 35 to 37% of revenue each quarter.",
            "the middle bar lit, about half the height of the tallest",
        )
        .detail(
            "Q4 2025 was 35%.",
            &["5 nm by quarter: 36, 36, 37, 35% (page text, section 6)"],
        ),
    Beat::new("3 nm: 28% in Q4, up from 22% in Q1", BEAT_MS)
        .note(
            "3 nm rose through 2025, from 22% of revenue in Q1 to 28% in Q4.",
            "the right-hand bar lit, the shortest of the three",
        )
        .detail(
            "All of these are FinFET nodes.",
            &["3 nm: Q1 22%, Q4 28% (page text, section 6)"],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("fins bend and vary below 3 nm", BEAT_MS)
        .note(
            "Thin fins vary from one device to the next, and tall fins bend and taper when they are etched.",
            "one tall, thin fin, its profile narrowing toward the top",
        )
        .detail(
            "These are textbook limits; no sourced figure is given.",
            &["FIN LIMITS: thin fins vary, tall fins bend and taper (textbook)"],
        ),
    Beat::new("leakage paths multiply", BEAT_MS)
        .note(
            "Sub-fin leakage, gate-induced drain leakage and tunnelling all grow as the fin shrinks.",
            "dots leaking along the silicon at the fin base",
        )
        .detail(
            "The bottom of the fin is the one place the gate cannot reach.",
            &["LEAKAGE: sub-fin, GIDL and tunnelling grow (textbook)"],
        ),
    Beat::new("nanosheets: gate on four sides", BEAT_MS)
        .note(
            "The industry's answer is the nanosheet: the fin becomes stacked sheets with the gate on all four sides. It comes at N2.",
            "three sheets inside the glass gate wall, the gate round each one",
        )
        .detail(
            "Samsung already has its first GAA at 3 nm.",
            &["Nanosheets (GAA) at N2; Samsung GAA at 3 nm (page text, section 7)"],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("TSMC: FinFET rows from N16 to N3", BEAT_MS)
        .note(
            "TSMC makes FinFETs from N16 to N3, for NVIDIA, Apple and AMD. It is the volume leader.",
            "a row of fins under one gate, the TSMC rows seen in three-quarter view",
        )
        .detail(
            "TSMC is the volume leader for the FinFET nodes.",
            &["TSMC (TSM): N16 to N3 for NVIDIA, Apple and AMD (page text, section 8)"],
        ),
    Beat::new("Intel and Samsung: FinFETs too", BEAT_MS)
        .note(
            "Intel made FinFETs from 22 nm to Intel 3, and Samsung from 14 nm. Both are now moving to GAA.",
            "a single fin under its gate, the other maker's FinFET",
        )
        .detail(
            "Both are now moving to gate-all-around.",
            &["Intel from 22 nm to Intel 3; Samsung from 14 nm (page text, section 8)"],
        ),
    Beat::new("litho and etch tools", BEAT_MS)
        .note(
            "SAQP and the fin etch run on litho and etch tools from ASML, Applied Materials, Lam Research and Tokyo Electron.",
            "two grey tool cabinets either side of the fins; the cabinets stand for the tool makers",
        )
        .detail(
            "The tool makers are named on the page; the cabinets are not drawn to any one tool.",
            &["ASML, Applied Materials (AMAT), Lam Research (LRCX), Tokyo Electron (TEL) (page text, section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("fins run out of room below 3 nm", BEAT_MS)
        .note(
            "Fins cannot get much thinner or taller below 3 nm, and moving to GAA resets the yields.",
            "one tall, thin fin, the limit it is near",
        )
        .detail(
            "The move to GAA costs yield while the process is new.",
            &["Fins have run out of room below 3 nm; the move to GAA resets yields (page text, section 9)"],
        ),
    Beat::new("cost per wafer rises with every FinFET node", BEAT_MS)
        .note(
            "Each FinFET node costs more per wafer. TSMC does not publish prices, only rumoured ranges.",
            "three wafer stacks, each taller than the last, with no figures on them",
        )
        .detail(
            "The stacks are schematic: they show the trend, not a price.",
            &[
                "Cost per wafer keeps rising with every FinFET node (page text, section 9)",
                "TSMC prices are not public; only labelled rumour ranges exist (page text, section 7)",
            ],
        ),
    Beat::new("pitches marked est are estimates", BEAT_MS)
        .note(
            "Several pitches here are WikiChip estimates. The N5 numbers are Apple A15 SEM measurements, and the Intel 22 nm fin dimensions were not confirmed.",
            "a fin cut across, with the estimate labels beside it",
        )
        .detail(
            "Read the numbers with care.",
            &["est = WikiChip; N5 = Apple A15 SEM; Intel 22 nm fin dimensions not confirmed (page text, section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1 to 3: Intel 22 nm, TSMC 16FF+, SAQP", BEAT_MS)
        .note(
            "The first sources cover the Intel 22 nm tri-gate, TSMC 16FF+ and the SAQP patent.",
            "the whole chip, the camera pulling slowly back",
        )
        .detail(
            "The full list is on the page.",
            &[
                "[1] Intel 22nm: realworldtech.com/?p=1082 ; semiaccurate.com/2011/05/04/like-semiaccurate-said-intel-goes-finfet3d-on-22nm/",
                "[2] TSMC 16FF+: pr.tsmc.com/english/news/1835 ; semiwiki.com/semiconductor-manufacturers/tsmc/1789-16nm-finfet-versus-20nm-planar/",
                "[3] SAQP: image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10121785 ; cadence blog on imec 5nm takeout",
            ],
        ),
    Beat::new("sources 4 to 6: WikiChip, N3 and FinFlex", BEAT_MS)
        .note(
            "The next sources cover the WikiChip N7 and N5 pages, the N3 detail and the FinFlex announcement.",
            "the whole chip, pulled back a little further",
        )
        .detail(
            "Each figure on the page cites one of these.",
            &[
                "[4] WikiChip N7/N5: en.wikichip.org/wiki/N7 ; en.wikichip.org/wiki/N5 ; angstronomics.com/p/the-truth-of-tsmc-5nm",
                "[5] N3: techinsights.com/blog/tsmc-reveals-3nm-process-details ; semiengineering.com/iedm-tsmc-n3-details",
                "[6] FinFlex: tsmc.com/english/news-events/blog-article-20220616 ; semianalysis.com/p/iedm2022p1",
            ],
        ),
    Beat::new("sources 7 and 8: Samsung and the TSMC mix", BEAT_MS)
        .note(
            "The last sources cover Samsung's 3 nm process and the 2025 TSMC revenue mix.",
            "the whole chip, at its widest view",
        )
        .detail(
            "Revenue shares are quarterly reports, not audited node data.",
            &[
                "[7] Samsung: club386.com/samsung-starts-mass-production-on-3nm-process-node ; news.samsung.com/global/samsung-foundry-innovations-power-the-future-of-big-data-ai-ml-and-smart-connected-devices",
                "[8] TSMC mix: anysilicon.com/tsmcs-financial-results-2025-q1/ ; webull.com/news/13698287613906944 ; finance.yahoo.com/news/chip-giant-set-strong-2026-195908674.html",
            ],
        ),
];

// ---- the picture scenes ---------------------------------------------------------------------

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
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet_zoom_d.glb"),
        FINFLEX_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_finfet_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "making fins: SAQP, form, reveal",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "the gate wraps three sides",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "fin count: width in whole fins",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "FinFlex on N3",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "fin limits and what comes next",
        build: zoom_e,
    },
];

/// One picture per `# ` section of the page, in order. Section 5 shares the FinFlex beats.
macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_finfet_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, SEC3_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, FINFLEX_BEATS),
    section!(6, SEC6_BEATS),
    section!(7, SEC7_BEATS),
    section!(8, SEC8_BEATS),
    section!(9, SEC9_BEATS),
    section!(10, SEC10_BEATS),
];

pub const NODE: Node = Node {
    page: "FINFET",
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
        for z in ZOOMS {
            let s = (z.build)();
            let what = format!("zoom {}", z.key);
            assert_eq!(s.beats().len(), 3, "{what}");
            super::super::super::blender::explained(s.as_ref(), &what);
            super::super::super::blender::draws_every_beat(s.as_ref(), &what);
        }
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, vec![3; 10]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            let what = format!("section {}", i + 1);
            super::super::super::blender::explained(s.as_ref(), &what);
            super::super::super::blender::draws_every_beat(s.as_ref(), &what);
        }
    }
}
