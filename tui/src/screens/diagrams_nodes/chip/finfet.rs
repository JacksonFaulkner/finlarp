// CHIP tab, FINFET: the overview is the whole chip (chip_kit.py) with a detailed FinFET drawn at
// the NMOS spot (tools/pbr3d/blender/chip_finfet_detail.py), the camera gliding in on it. Six
// beats: the whole chip, the planar transistor it replaces, the fins rising, the gate wrapping
// three sides, the channel on with electrons riding contact to contact, and back out.
//
// Zoom-ins a-e and sections 1-10 are detailed, cut-away close-ups of the same nanometre-scale fin,
// gate-stack and epi structure (chip_finfet_detail.py), the camera framed on each beat's part.
// Three beats each.
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
            "This is the same chip as the hero: silicon at the bottom, three tiers of copper wiring and the bumps on top. Here its NMOS transistor is a FinFET, drawn at the NMOS spot. FinFETs are what most chips from about 2012 to 2024 were built on.",
            "The cyan box at the left of the silicon, under the wiring: a small FinFET with blue epi and a teal gate cap.",
        )
        .detail(
            "Intel shipped the first volume FinFET; TSMC followed at 16 nm.",
            &[
                "Intel 22 nm Tri-Gate: announced 2011, Ivy Bridge 2012",
                "TSMC 16FF+: risk production Nov 2014, volume 2015",
            ],
        ),
    Beat::new("planar: the channel lies flat under one face of the gate", BEAT_MS)
        .note(
            "Before FinFETs, the transistor was flat. The gate stack lies on the silicon surface and controls a thin channel just under it from one side only. As gates shrank below about 30 nm, that one face could no longer shut the channel off, and current leaked even when the transistor was off.",
            "Blue source and drain implanted flush with the silicon, the gate stack (yellow high-k, bronze metal, dark fill, teal cap) lying flat between them, and the thin cyan channel under it.",
        )
        .detail(
            "One gated face against three for a fin.",
            &["Intel 22 nm vs 32 nm planar: up to 37% lower gate delay at low voltage (press, 2011)"],
        ),
    Beat::new("rise: the channel stands up as a fin", BEAT_MS)
        .note(
            "The FinFET stands the channel on its edge. Thin silicon fins rise out of the substrate, three side by side, and the source and drain are grown back on them as raised, faceted epitaxy that merges across the fins.",
            "Three grey fins growing up out of the silicon, then blue diamond-shaped epi blocks growing over their ends.",
        )
        .detail(
            "Fins are patterned at a quarter of the litho pitch by SAQP.",
            &["Fin ~7 nm wide, ~50 nm tall (textbook)", "Weff per fin = 2 x Hfin + Wfin"],
        ),
    Beat::new("wrap: the gate wraps the fin on three sides", BEAT_MS)
        .note(
            "The gate now drapes over the fins. Cut across it, every fin sits in an upside-down U: a yellow high-k skin, then bronze work-function metal, then fill metal. The gate touches the channel on its top and both sides, which gives it far tighter control.",
            "The transistor cut two ways: on the left face the blue epi, on the cut across the gate three grey fins each wrapped in yellow and bronze, a teal cap above.",
        )
        .detail(
            "Three gated faces suppress short-channel leakage.",
            &["Three gated faces vs one planar (textbook)", "High-k: HfO2-based"],
        ),
    Beat::new("on: the channel fills the fin and current runs source to drain", BEAT_MS)
        .note(
            "With the gate high, the whole fin under the gate conducts. Electrons come down the source contact, through the source epi, along the fin under the gate and up the drain epi to the drain contact.",
            "Cut along the middle fin: the fin under the gate glowing cyan, and white beads riding down the left contact, across through the fin and up the right side.",
        )
        .detail(
            "Drive scales with fin count: 1, 2 or 3 fins per device.",
            &["Width in whole fins (textbook)", "TSMC FinFlex on N3: fin count per block"],
        ),
    Beat::new("off: the three faces pinch the channel shut, so less leaks", BEAT_MS)
        .note(
            "With the gate low, the three gated faces pinch the channel off, so far less current leaks than in a planar transistor of the same size. The camera pulls back out to the whole chip.",
            "The whole chip again: wiring, bumps and silicon, with the FinFET at the NMOS spot under the wiring.",
        )
        .detail(
            "Less leakage at the same speed was the FinFET's selling point.",
            &["Intel 22 nm: >50% less power at the same performance (press, 2011)"],
        ),
];

// ---- zoom-ins a-e ---------------------------------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("SAQP: masks at a quarter of the litho pitch", BEAT_MS)
        .note(
            "Fins are closer together than a scanner can print. So it prints wider lines, the mandrels, and deposits thin spacers on their sidewalls. Doing that twice (self-aligned quadruple patterning) turns one printed line into four spacer lines, one per fin.",
            "Cut across the future fins: tan mandrels between teal spacer lines, on a teal-grey hard mask over a solid grey silicon block.",
        )
        .detail(
            "Pitch is set by the spacer thickness, not the scanner.",
            &["SAQP fin patterning (USPTO 10121785)", "Fin pitch ~30 nm at N7 (est)"],
        ),
    Beat::new("FIN FORM: the silicon between the masks is etched", BEAT_MS)
        .note(
            "The spacer pattern is transferred into the hard mask, and a deep, straight etch cuts trenches into the silicon. Tall thin fins are left standing under the hard-mask caps.",
            "Four grey fins standing on the silicon, each topped by a teal hard-mask cap, with empty trenches between them.",
        )
        .detail(
            "Profile control matters: a tapered fin changes drive from fin to fin.",
            &["Hfin tens of nm, Wfin single-digit to ~10 nm (textbook)"],
        ),
    Beat::new("FIN REVEAL: oxide fills and is etched back", BEAT_MS)
        .note(
            "Oxide fills the trenches and is polished flat, then etched back to expose the top of each fin. The exposed height is the part the gate will wrap; the buried part stays isolated in the oxide.",
            "Cream oxide filling the trenches to the fin tops, then sinking until only the upper part of each fin stands clear.",
        )
        .detail(
            "The recess depth sets the electrical fin height.",
            &["STI oxide recess sets Hfin (textbook)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("high-k: the dielectric coats the top and both sidewalls", BEAT_MS)
        .note(
            "The first layer of the gate is a high-k dielectric, a hafnium-oxide film only a nanometre or two thick. It coats the top and both sidewalls of every fin and the oxide between them.",
            "Cut across the gate: three grey fins standing out of the cream oxide, each wrapped in a bright yellow skin.",
        )
        .detail(
            "High-k lets the gate couple strongly without tunnelling leakage.",
            &["High-k: HfO2-based, ~1-2 nm (drawn thick)"],
        ),
    Beat::new("gate metal: three sides, not four", BEAT_MS)
        .note(
            "Work-function metal goes on next and sets the threshold voltage, then fill metal closes the gaps. The gate now touches each fin on three faces. The bottom of the fin, inside the oxide, is never gated.",
            "Each yellow-skinned fin inside a bronze work-function layer, dark fill metal over everything, a teal cap on top and the fin feet running down into the cream oxide.",
        )
        .detail(
            "Taller fins give more gated width per footprint.",
            &["Weff = 2 x Hfin + Wfin per fin (textbook)"],
        ),
    Beat::new("on: current runs along the fin, the bottom stays ungated", BEAT_MS)
        .note(
            "Turned on, electrons ride from the source contact down through the epi, along the fin under the gate and up to the drain contact. A small leak can still flow under the gate through the fin's ungated foot.",
            "Cut along the middle fin: the gated part glowing cyan, white beads riding contact to contact, and a few faint red beads crossing below the oxide line.",
        )
        .detail(
            "Punch-through-stop doping blocks most of the sub-fin path.",
            &["Sub-fin leakage: blocked by punch-through-stop doping (textbook)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("one fin: the smallest device", BEAT_MS)
        .note(
            "A FinFET's width comes in whole fins. The smallest transistor is one fin under the gate: the densest, with the least drive current.",
            "A one-fin transistor cut open: blue epi, the fin wrapped in yellow and bronze under the gate, white beads riding through it.",
        )
        .detail(
            "Width is quantised: one fin is the smallest step.",
            &["Width in whole fins: 1, 2 or 3 per device (textbook)"],
        ),
    Beat::new("two fins: twice the drive", BEAT_MS)
        .note(
            "Two fins under the same gate carry about twice the current. The epi from the two fins merges into one source and one drain. Two fins is the common width for logic cells.",
            "Two fins wrapped side by side in the gate cut, with merged blue epi in front.",
        )
        .detail(
            "Drive comes in steps of one fin, not in fine width.",
            &["FinFlex base library: 2-fin cells (TSMC N3)"],
        ),
    Beat::new("three fins: for the fastest cells", BEAT_MS)
        .note(
            "Three fins give the most drive of the three widths, for the fastest cells, at the cost of area and gate capacitance. A designer who needs 2.5 fins of current has to pick 2 or 3.",
            "Three fins wrapped in the gate, merged blue epi across all three, beads riding the current path.",
        )
        .detail(
            "Never a fraction of a fin.",
            &["FIN COUNT 1-3 (page text, section 1)"],
        ),
];

const FINFLEX_BEATS: &[Beat] = &[
    Beat::new("FinFlex 3-2: speed", BEAT_MS)
        .note(
            "On N3, TSMC's FinFlex lets each block of a chip pick its fin count. A 3-2 block mixes tall 3-fin cells, which drive hardest, with the 2-fin base cell. More fins means more current but a taller cell.",
            "Two standard cells from above: a tall 3-fin cell and a shorter 2-fin cell, blue n epi at the bottom, pink p epi at the top, copper power rails at the edges.",
        )
        .detail(
            "Fast blocks such as CPU cores pay area for drive.",
            &["FinFlex options: 3-2, 2-2, 2-1 (TSMC, 2022)"],
        ),
    Beat::new("FinFlex 2-2: balanced", BEAT_MS)
        .note(
            "The 2-2 option uses the 2-fin cell everywhere: the base library and the middle ground between speed, power and area.",
            "Two equal 2-fin cells, n fins at the bottom with blue epi and p fins at the top with pink epi, grey gates across them.",
        )
        .detail(
            "Every FinFlex option builds on the 2-fin cell.",
            &["2-fin library is the base (WikiChip on TSMC N3E)"],
        ),
    Beat::new("FinFlex 2-1: low power, dense", BEAT_MS)
        .note(
            "A 2-1 block mixes in 1-fin cells. They are shorter, so more fit in the same area, and leak less, but switch more slowly. It suits always-on and low-power blocks.",
            "A 2-fin cell beside a short 1-fin cell whose copper rails sit much closer together.",
        )
        .detail(
            "The density range is TSMC's claim.",
            &["0.64x-0.85x of N5 2-2 cell area by option (TSMC claim)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("fin limits: thinner and taller", BEAT_MS)
        .note(
            "To keep scaling, fins get taller and thinner at a tighter pitch. Past a point they taper during the etch, bend, and vary from one fin to the next, and every variation shifts how the transistor switches.",
            "Cut across the gate: two fins of today's shape on the right, two taller, thinner, tapering fins on the left.",
        )
        .detail(
            "Textbook limits; no sourced figure.",
            &["Thin fins: more variability; tall fins: bending, taper (textbook)"],
        ),
    Beat::new("leakage: sub-fin, GIDL and tunnelling", BEAT_MS)
        .note(
            "Packing fins closer leaves less room for the gate stack in the gaps, while leakage grows: under the fin, at the gate-to-drain edge and through thin layers.",
            "Three closely packed fins, bronze metal nearly closing the gaps, red glowing leakage in the fin feet below the oxide line.",
        )
        .detail(
            "The ungated fin foot is the weak spot.",
            &["Leakage: sub-fin, GIDL, tunnelling (textbook)"],
        ),
    Beat::new("nanosheets: the answer is gate on four sides", BEAT_MS)
        .note(
            "The industry's answer is gate-all-around: slice the fin into stacked horizontal sheets and fill the gaps with gate, so every channel is gripped on four sides. TSMC moves at N2; Samsung did at 3 nm.",
            "A fin in its yellow and bronze U on the right, and on the left three grey sheets each ringed in yellow inside bronze metal.",
        )
        .detail(
            "Four gated faces instead of three.",
            &["Nanosheets at TSMC N2 and Intel 18A (2025)", "Samsung GAA at 3 nm (2022)"],
        ),
];

// ---- sections 1-10 --------------------------------------------------------------------------
// Detailed close-ups (chip_finfet_detail.py): real fin, gate-stack and epi structure drawn to a
// nanometre scale, cut away so the inside shows. Three beats each.

const SEC1_BEATS: &[Beat] = &[
    Beat::new("fins: the channel stands up out of the oxide", BEAT_MS)
        .note(
            "A FinFET etches the silicon into tall, thin walls called fins. Oxide fills the trenches between them and is etched back, so only the top of each fin sticks out. That exposed top is the channel, and it stands on its edge instead of lying flat.",
            "Three grey silicon fins standing out of the cream STI oxide, on the darker silicon substrate.",
        )
        .detail(
            "Standing the channel up lets the gate grip it from more sides.",
            &[
                "Fin ~7 nm wide, ~50 nm tall (textbook, N7/N5 class)",
                "Fin pitch ~30 nm at N7 (WikiChip estimate)",
            ],
        ),
    Beat::new("the gate wraps the top and both sides", BEAT_MS)
        .note(
            "Cut across the gate, every fin sits inside an upside-down U of gate stack: a thin high-k insulator, then a work-function metal that sets the switching voltage, then fill metal. The gate now controls the channel from three faces instead of one, so it can shut it off much more firmly.",
            "Grey fin cores inside a yellow high-k skin and a bronze work-function metal, with dark fill metal over them and a teal nitride cap on top. Below the cream oxide line the fins carry on, ungated.",
        )
        .detail(
            "Three gated faces is what kept leakage down below 22 nm.",
            &["Intel 22 nm Tri-Gate: announced 2011, shipped 2012", "High-k: HfO2-based"],
        ),
    Beat::new("a whole transistor: source, gate, drain", BEAT_MS)
        .note(
            "Either side of the gate the fins are etched down and epitaxial silicon is grown back on them. The diamond-shaped epi from neighbouring fins merges into one source and one drain, and a tungsten trench contact lands on top. Drive current scales with the number of fins under the gate.",
            "Blue merged diamond epi on the source side, the gate stack cut open in the middle, more blue epi on the drain side, grey trench contacts on top and teal nitride spacers either side of the gate.",
        )
        .detail(
            "Width is set in whole fins: 1, 2 or 3 per transistor.",
            &["3 fins = ~3x the drive of 1 fin", "Weff per fin = 2 x Hfin + Wfin (textbook)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("Hfin, Wfin and the fin pitch", BEAT_MS)
        .note(
            "This is the classic TEM view, cut through the gate and across the fins. Each fin is a few nanometres wide and tens of nanometres tall. Current flows on both sidewalls and the top, so the height counts twice in the effective width.",
            "Three tall grey fins in cross-section, each inside a yellow and bronze U, about 30 nm apart.",
        )
        .detail(
            "Taller fins give more current per footprint.",
            &[
                "Hfin ~50 nm, Wfin ~7 nm (textbook)",
                "Weff = 2 x Hfin + Wfin per fin",
                "Fin pitch: N7 ~30 nm (est), N5 28 nm (A15 SEM)",
            ],
        ),
    Beat::new("the gate stack: high-k, work-function metal, fill", BEAT_MS)
        .note(
            "Closer in, the gate is three layers. The high-k insulator touches the silicon. The work-function metal over it sets the threshold voltage, and the fill metal carries the signal along the gate. Everything has to fit in the gap between two fins.",
            "The middle fin's top: a yellow high-k line hugging the grey fin, a bronze work-function layer over it, and dark grey fill metal filling the rest.",
        )
        .detail(
            "Layer thickness, not just length, now sets how the transistor switches.",
            &["High-k ~1-2 nm (drawn thick here)", "Work-function metals: TiN/TiAl family (textbook)"],
        ),
    Beat::new("the foot of the fin is not gated", BEAT_MS)
        .note(
            "Only the part of the fin above the oxide sees the gate. Below it, current can still sneak from source to drain under the gate: sub-fin leakage. Fabs block that path with a heavily doped punch-through stop near the fin's base.",
            "The channel glowing cyan above the oxide, the sub-fin glowing red below it, and a purple punch-through stop band at the bottom of each fin.",
        )
        .detail(
            "The sub-fin is the face the gate can never reach.",
            &["Sub-fin leakage: blocked by punch-through-stop doping (textbook)"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("Intel 22 nm and TSMC N16: FinFETs go to volume", BEAT_MS)
        .note(
            "Intel's 22 nm Tri-Gate, announced in 2011, was the first FinFET in volume. TSMC followed with 16FF+ in 2015 at a 90 nm contacted gate pitch. Every row in this section is drawn at the same scale.",
            "A row of four gates (teal caps, dark fill) over fins, blue epi between them and a gold bar marking one gate pitch.",
        )
        .detail(
            "The FinFET was stretched from 22 nm to N3E, not replaced.",
            &["Intel 22 nm: 2011 announcement, Ivy Bridge 2012", "TSMC N16 contacted gate pitch 90 nm (WikiChip)"],
        ),
    Beat::new("N7 and N5: the pitch tightens", BEAT_MS)
        .note(
            "Each node packs gates and fins closer. N7's contacted gate pitch is about 57 nm (an estimate); N5 measures 51 nm with a 28 nm fin pitch. At the same scale the row is much shorter.",
            "The same four-gate row, now visibly shorter, the gold pitch bar about half its N16 length.",
        )
        .detail(
            "Pitch shrinks, the fin stays.",
            &["N7: 57 nm gate, 30 nm fin pitch (est, WikiChip)", "N5: 51 nm gate, 28 nm fin pitch (A15 SEM)"],
        ),
    Beat::new("N3: 45 nm gate pitch, the last FinFET", BEAT_MS)
        .note(
            "N3 brings the gate pitch to 45 nm, the tightest of the three rows. It is TSMC's last FinFET node; N2 moves to nanosheets. Samsung went to gate-all-around one node earlier, at 3 nm.",
            "The shortest row of the three, the gold bar at its tightest.",
        )
        .detail(
            "Half the N16 pitch, about seven years later.",
            &["N3 gate pitch 45 nm (TechInsights)", "Samsung: first GAA at 3 nm (2022)"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("N7: about 91 million transistors per mm2 (est)", BEAT_MS)
        .note(
            "The window is a fixed patch of silicon seen from above, tiled with logic cells. Each cell has two gates crossing n and p fins, with source and drain epi between them. At N7 sixteen cells fit.",
            "A gold frame on a dark floor, filled with a 4 x 4 grid of cells: grey gates, light fins, blue n epi and pink p epi.",
        )
        .detail(
            "Density is an estimate, not a TSMC disclosure.",
            &["N7 ~91.2 MTr/mm2 (WikiChip estimate)"],
        ),
    Beat::new("N5: about 138 million per mm2", BEAT_MS)
        .note(
            "N5 shrinks the same cell by roughly a third in area, so about half again as many fit in the window. The figure comes from measuring an Apple A15 die, not from TSMC.",
            "The same frame now holding a 5 x 5 grid of smaller cells.",
        )
        .detail(
            "The grid counts are a picture of the ratio, not a census.",
            &["N5 ~137.6-138.2 MTr/mm2 (A15 SEM)", "~1.5x N7"],
        ),
    Beat::new("N3E: about 1.6x N5 (TSMC claim)", BEAT_MS)
        .note(
            "TSMC claims N3E logic is about 1.6 times as dense as N5. The figure blends cell types, and SRAM barely shrank at N3E, so real chips gain less.",
            "A 6 x 6 grid of the smallest cells in the same frame.",
        )
        .detail(
            "A vendor claim on a logic mix.",
            &["N3E ~1.6x N5 logic density (TSMC claim)"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("FinFlex 3-2: a tall cell for speed", BEAT_MS)
        .note(
            "On N3, TSMC's FinFlex lets each block of a chip pick its fin count. A 3-2 block mixes 3-fin cells, which drive hardest, with the 2-fin base cell. More fins means more current but a taller cell.",
            "Two standard cells side by side: on the left a tall 3-fin cell (blue n epi below, pink p epi above), on the right a shorter 2-fin cell, both bounded by copper power rails.",
        )
        .detail(
            "Fast blocks (CPU cores) pay area for drive.",
            &["FinFlex options: 3-2, 2-2, 2-1 (TSMC, 2022)"],
        ),
    Beat::new("FinFlex 2-2: balanced", BEAT_MS)
        .note(
            "The 2-2 option uses the 2-fin cell everywhere. It is the base library and the middle ground between speed, power and area.",
            "Two equal 2-fin cells, n fins at the bottom with blue epi and p fins at the top with pink epi, grey gates across them.",
        )
        .detail(
            "All FinFlex options build on the 2-fin cell.",
            &["2-fin library is the base (WikiChip on TSMC N3E)"],
        ),
    Beat::new("FinFlex 2-1: low power and dense", BEAT_MS)
        .note(
            "A 2-1 block mixes in 1-fin cells. They are shorter, so more fit per area, and leak less, but switch more slowly. It suits always-on and low-power blocks.",
            "A 2-fin cell on the left and a short 1-fin cell on the right, its copper power rails much closer together.",
        )
        .detail(
            "One die can mix blocks of different fin counts.",
            &["0.64x-0.85x of N5 2-2 cell area by option (TSMC claim)"],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("7 nm and below: 74% of TSMC's 2025 wafer revenue", BEAT_MS)
        .note(
            "Each column is one quarter of 2025, stacked from 7 nm at the bottom to 3 nm on top, with a 100% guide behind. All three nodes are FinFET. Together they rose from 73% of revenue in Q1 to 77% in Q4.",
            "Four columns of stacked wafers: grey 7 nm at the base, blue 5 nm in the middle, teal 3 nm on top, each below a thin 100% bar.",
        )
        .detail(
            "Leading-edge FinFET is most of TSMC's revenue.",
            &["7 nm and below: 74% of 2025, 69% of 2024", "Q4 25: 3 nm 28%, 5 nm 35%, 7 nm 14%"],
        ),
    Beat::new("5 nm: the biggest single node", BEAT_MS)
        .note(
            "5 nm, which includes N4, was the largest single node all year at 35 to 37% of revenue. That is where most of today's AI accelerators are made, including Nvidia's Hopper and Blackwell.",
            "The blue 5 nm band glowing amber in every column, about the same height each quarter.",
        )
        .detail(
            "Steady at about a third of revenue.",
            &["5 nm by quarter: 36, 36, 37, 35%"],
        ),
    Beat::new("3 nm: 22% in Q1, 28% in Q4", BEAT_MS)
        .note(
            "3 nm grew through the year as Apple, and later others, moved to it. It is the last FinFET node; the growth after it goes to N2 nanosheets.",
            "The teal 3 nm cap glowing cyan on each column, tallest in Q4.",
        )
        .detail(
            "The newest FinFET node is still ramping.",
            &["3 nm: Q1 22%, Q2 24%, Q3 23%, Q4 28%"],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("fins can't get much taller or thinner", BEAT_MS)
        .note(
            "Scaling a FinFET means taller, thinner fins at a tighter pitch. Past a point, tall thin fins taper during the etch, bend and vary from one to the next, and each variation shifts how the transistor switches.",
            "Cut across the gate: on the right two fins of today's shape, on the left two taller, thinner fins that taper toward the top.",
        )
        .detail(
            "Textbook limits; no sourced figure.",
            &["Thin fins: more variability; tall fins: bending, taper (textbook)"],
        ),
    Beat::new("leakage, and no room for the gate", BEAT_MS)
        .note(
            "Tighter fins leave less space between them, and the whole gate stack, high-k, work-function metal and fill, has to fit in that gap. Meanwhile sub-fin leakage, gate-induced drain leakage and tunnelling all grow.",
            "Three fins packed close, the bronze metal almost filling the gaps between them, and red glowing sub-fin leakage below the oxide line.",
        )
        .detail(
            "The gap between fins became the limit around N3.",
            &["Leakage: sub-fin, GIDL, tunnelling (textbook)"],
        ),
    Beat::new("the answer: nanosheets, gate on four sides", BEAT_MS)
        .note(
            "Gate-all-around turns the fin on its side and slices it into a stack of thin sheets. The gate fills the gaps between the sheets, so it grips each channel on all four sides. TSMC moves to it at N2; Samsung did at 3 nm.",
            "On the right a fin inside its yellow and bronze U; on the left three grey sheets, each ringed by yellow high-k inside bronze metal.",
        )
        .detail(
            "Four gated faces instead of three.",
            &["Nanosheets at TSMC N2, Intel 18A (2025)", "Samsung GAA at 3 nm (2022)"],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("TSMC and Samsung: FinFET rows", BEAT_MS)
        .note(
            "TSMC builds FinFETs from N16 to N3 for Nvidia, Apple, AMD and most of the industry, and is the volume leader. Samsung Foundry made FinFETs from 14 nm before moving to GAA at 3 nm.",
            "A long row of five gates over three fins, cut open: teal spacers and caps, dark gate metal wrapping the fins, blue merged epi between gates, grey contacts.",
        )
        .detail(
            "Three companies make leading-edge FinFETs.",
            &["TSMC (TSM): N16 to N3", "Samsung: 14 nm FinFET onward"],
        ),
    Beat::new("Intel: tapered fins at 22 nm", BEAT_MS)
        .note(
            "Intel's first fins at 22 nm had a sloped, trapezoid profile that later nodes straightened and stretched taller. Intel used FinFETs from 22 nm through Intel 3, then switched to RibbonFET nanosheets at 18A.",
            "Three wide-based tapered fins cut across the gate, each inside the yellow and bronze stack.",
        )
        .detail(
            "Intel's exact 22 nm fin dimensions were not confirmed for this page.",
            &["Intel (INTC): 22 nm to Intel 3, then 18A RibbonFET"],
        ),
    Beat::new("SAQP: four fins per printed line", BEAT_MS)
        .note(
            "Fins are closer together than one exposure can print. A scanner prints mandrel lines, spacers are deposited on their sidewalls, the mandrels are removed, and the trick is repeated: self-aligned quadruple patterning. The spacers then mask the fin etch.",
            "Tan mandrels between teal spacer lines, sitting on nitride hard-mask caps over grey fins etched into the silicon.",
        )
        .detail(
            "Pitch is set by spacer thickness, not by the scanner.",
            &["Litho: ASML", "Deposition and etch: Applied Materials (AMAT), Lam (LRCX), Tokyo Electron"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("fins have run out of room", BEAT_MS)
        .note(
            "At the tightest pitches, the gap between two fins must hold the high-k, the work-function metal and the fill metal on both walls. Below 3 nm there is no room left to shrink, and the move to GAA resets yield learning.",
            "Two fins close together, the bronze work-function metal nearly closing the gap between them.",
        )
        .detail(
            "The physical limit drives the switch to nanosheets.",
            &["Fins out of room below 3 nm; GAA resets yields (page text)"],
        ),
    Beat::new("cost per wafer rises every node", BEAT_MS)
        .note(
            "Every FinFET node adds patterning steps, more EUV layers and costlier tools, so each wafer costs more. TSMC does not publish prices; only press reports exist.",
            "A 300 mm wafer seen from above, covered in a grid of dies, most green and a few red.",
        )
        .detail(
            "No public price list.",
            &["Cost per wafer rises with every FinFET node", "TSMC prices: only labelled press reports"],
        ),
    Beat::new("which numbers are measured and which are estimated", BEAT_MS)
        .note(
            "Several pitches on this page are estimates. The N5 numbers come from measuring an Apple A15 under an electron microscope; the N7 ones are WikiChip estimates.",
            "The N5 gate row in three-quarter view, a gold bar spanning one 51 nm gate pitch.",
        )
        .detail(
            "Read the 'est' marks.",
            &["N5: A15 SEM (Angstronomics)", "N7: WikiChip estimate", "Intel 22 nm fin size: not confirmed"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1 to 3: Intel 22 nm, TSMC 16FF+, SAQP", BEAT_MS)
        .note(
            "The first sources cover the Intel 22 nm Tri-Gate announcement, TSMC's 16FF+ launch and the SAQP fin-patterning patent.",
            "The finished FinFET row, cut open, the camera turning slowly round it.",
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
            "The next sources cover the WikiChip N7 and N5 pages, the N3 process details and the FinFlex announcement.",
            "The same row from further round, the gate stack and epi on the cut faces.",
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
            "The last sources cover Samsung's 3 nm process and TSMC's 2025 revenue mix.",
            "The row seen from its side, the fins running away from the camera.",
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

/// One picture per `# ` section of the page, in order.
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
    section!(5, SEC5_BEATS),
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
