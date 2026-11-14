// CHIP tab, GATE STACK: the node's pictures in the picture-and-panel template, from the Blender
// scenes in tools/pbr3d/blender/chip_gate_stack.py. The overview is the whole-chip scene with the
// camera zooming in on the NMOS gate stack. Zoom-ins a-e are the layers, the gate-last flow, EOT,
// the work-function metals and the nanosheet gap. Sections 1-10 follow the page's headings; 2, 3
// and 5 reuse the scenes of zooms b, a and c, and section 10 lists the sources.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("NMOS gate: a stack of thin films", BEAT_MS)
        .note(
            "The gate of one NMOS transistor is a stack of thin films, each laid down by atomic layer deposition (ALD), one atomic layer per cycle.",
            "The whole chip, with the NMOS gate highlighted in cyan in the middle of the silicon.",
        )
        .detail(
            "The stack is built with gate-last high-k metal gate (HKMG), first put into production by Intel at 45 nm.",
            &["Intel 45 nm HKMG, Penryn 2007 (newelectronics.co.uk)"],
        ),
    Beat::new("In on the gate: four films", BEAT_MS)
        .note(
            "Four films sit on the channel: a chemical SiOx interlayer about 0.5 nm thick, hafnium oxide (HfO2) at 1.5-2 nm, the TiAlC(N) work-function metal for NMOS, and a tungsten fill that sets the gate resistance.",
            "Thin bands on the silicon: a grey interlayer, a bright yellow high-k, a dark metal band, and the tall grey tungsten block on top. The layers are drawn thicker than life.",
        )
        .detail(
            "The interlayer has a low k, so it adds to the equivalent oxide thickness (EOT); the high-k sits on a clean interface.",
            &[
                "Intel 45 nm: HfO2 at about 1.0 nm EOT, TiAlN for NMOS (edn.com)",
                "IL SiOx adds to EOT (MRS; IEEE technav)",
                "W fill sets gate resistance (Lam ALD tungsten, siliconsemiconductor)",
            ],
        ),
    Beat::new("Gate up: the field runs down", BEAT_MS)
        .note(
            "The gate goes positive. Its field runs down through the HfO2 and the thin interlayer to the silicon. No current crosses the insulator; the field does the work.",
            "Gold field lines drop from the gate through the stack, and the gate glows.",
        )
        .detail(
            "A thin SiO2 gate oxide leaks by direct tunnelling, so the field has to cross a thicker film that passes almost no charge.",
            &["SiO2 below about 1.2 nm tunnels at the 90 nm node (IEEE technav)"],
        ),
    Beat::new("The field inverts the channel", BEAT_MS)
        .note(
            "Electrons are pulled up out of the silicon to the surface under the gate. They form a thin inversion layer that links source to drain.",
            "Dots rise from the silicon below and gather in the cyan band at the surface under the gate, which lights up.",
        )
        .detail(
            "This band switches the transistor on. The work-function metal sets the threshold voltage (Vt).",
            &["Work-function metal sets Vt; TiAlN for NMOS at Intel 45 nm (edn.com)"],
        ),
    Beat::new("Thick in fact, thin in effect", BEAT_MS)
        .note(
            "HfO2 is 1.5-2 nm thick, but its equivalent oxide thickness (EOT) is about 1 nm: the same capacitance as a thin SiO2 film. The pale bar above the gate is that SiO2 equivalent.",
            "The stack below stays thick; the translucent bar above is about half as thick and labelled as the EOT.",
        )
        .detail(
            "EOT = t_hk x 3.9/k_hk + t_IL x 3.9/k_IL, so a high-k film can be physically thick for the same capacitance, and tunnelling falls.",
            &[
                "EOT formula (MRS; IEEE technav)",
                "HfO2 k about 30 in one MRS source",
                "Intel 45 nm: over 10x less gate leakage (Intel claim, newelectronics.co.uk)",
            ],
        ),
    Beat::new("Field off: back to the whole chip", BEAT_MS)
        .note(
            "The gate returns to zero. The field drops, the inversion layer empties and the gate goes dark. This NMOS is one small part of the same chip.",
            "The whole chip again, with the NMOS highlighted and the gate dark.",
        )
        .detail(
            "Each Chip-tab node is the same whole chip, zoomed in on one part.",
            &["Gate-last: Intel 45 nm, TSMC 28 nm (edn.com; bit-tech.net)"],
        ),
];

// ---- zoom a: the layers, from interlayer to fill -----------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("IL and HfO2: the first two films", BEAT_MS)
        .note(
            "The first films on the channel are a chemical SiOx interlayer about 0.5 nm thick, then HfO2 about 1.5-2 nm. Each is laid down by ALD.",
            "The thin grey interlayer on the silicon, and the yellow HfO2 band above it, both lit cyan.",
        )
        .detail(
            "The interlayer gives the high-k a clean interface to the silicon; its low k still costs EOT.",
            &[
                "IL SiOx ~0.5 nm; HfO2 1.5-2 nm (page text, section 1)",
                "IL adds to EOT (MRS; IEEE technav)",
            ],
        ),
    Beat::new("TiAlC(N): the work-function metal", BEAT_MS)
        .note(
            "The NMOS work-function metal, TiAlC(N), sits on the HfO2. Its work function sets the threshold voltage.",
            "The blue-grey metal band under the cyan light, with the gold TiN glue beside it.",
        )
        .detail(
            "TiN caps the stack against the anneal; TiAlC(N) is the NMOS metal.",
            &[
                "TiAlC(N) for NMOS (page text, section 3)",
                "TiN CAP: protection during anneal (page text, section 1)",
            ],
        ),
    Beat::new("W fill: the gate metal", BEAT_MS)
        .note(
            "Tungsten fills the rest of the trench and is polished flat. It sets the gate resistance.",
            "The tall grey tungsten block, lit cyan, on top of the stack.",
        )
        .detail(
            "The fill is the low-resistance path to the gate contact.",
            &["W fill sets gate resistance (Lam ALD tungsten, siliconsemiconductor)"],
        ),
    Beat::new("The whole gate: four films", BEAT_MS)
        .note(
            "The gate is the films together: interlayer, high-k, work-function metal and fill, with a TiN glue between the metal and the fill.",
            "The whole stack with no highlight; the labels tag each layer.",
        )
        .detail(
            "Each film is one ALD step, one atomic layer per cycle.",
            &[
                "ALD, one atomic layer per cycle (page text, section 1)",
                "HKMG, gate-last (page text, section 1)",
            ],
        ),
];

// ---- zoom b: gate-last, dummy poly out, stack in -----------------------------------------------

const ZB_BEATS: &[Beat] = &[
    Beat::new("dummy poly: a placeholder gate", BEAT_MS)
        .note(
            "Gate-last starts with a polysilicon placeholder, the dummy poly, standing on a thin oxide.",
            "The brown poly block on the silicon, with the contact pads around it.",
        )
        .detail(
            "The placeholder takes the hot steps that would damage a metal gate.",
            &["DUMMY POLY: polysilicon placeholder on SiO2 (page text, section 2)"],
        ),
    Beat::new("S/D anneal, then the ILD fill", BEAT_MS)
        .note(
            "The source and drain are made and annealed at about 1000 C. Oxide fills around the gate and is polished down to the top of the poly.",
            "The orange-lit source and drain, and the grey ILD walls on each side of the poly.",
        )
        .detail(
            "All the hot source and drain work happens before the high-k and metal exist.",
            &[
                "SPACER + S/D anneal about 1000 C (page text, section 2)",
                "ILD + CMP: oxide polished to the poly top (page text, section 2)",
            ],
        ),
    Beat::new("poly pull leaves a trench", BEAT_MS)
        .note(
            "The dummy poly is etched out, leaving a trench between the ILD walls.",
            "The poly block drops away and the empty trench shows its thin oxide floor.",
        )
        .detail(
            "The trench is the space the real gate stack will fill.",
            &["POLY PULL: etch out the dummy, leaving a trench (page text, section 2)"],
        ),
    Beat::new("the stack goes into the trench", BEAT_MS)
        .note(
            "The high-k, work-function metals and fill go into the trench in the gate-first order.",
            "The HfO2 band, the gold metal and the grey tungsten fill in the trench.",
        )
        .detail(
            "The stack never sees the heat: it goes in after the source and drain.",
            &[
                "RMG STACK: IL, HfO2 and work-function metals in the trench (page text, section 2)",
                "Gate-last: Intel 45 nm, TSMC 28 nm (edn.com; bit-tech.net)",
            ],
        ),
];

// ---- zoom c: EOT, why the oxide had to go -------------------------------------------------------

const ZC_BEATS: &[Beat] = &[
    Beat::new("a thin SiO2 film leaks", BEAT_MS)
        .note(
            "Below about 1.2 nm, SiO2 leaks by direct tunnelling, so the gate current climbs.",
            "Purple dots tunnel down through the thin pale film to the silicon.",
        )
        .detail(
            "The 90 nm node hit this limit, so the oxide could not keep getting thinner.",
            &["SiO2 below about 1.2 nm tunnels at the 90 nm node (IEEE technav)"],
        ),
    Beat::new("HfO2: thick, with the same EOT", BEAT_MS)
        .note(
            "HfO2 is 1.5-2 nm thick, but its EOT is about 1 nm: the same capacitance as a thin SiO2 film.",
            "The yellow HfO2 film, with the translucent reference SiO2 film above it.",
        )
        .detail(
            "EOT = t_hk x 3.9/k_hk + t_IL x 3.9/k_IL: a thick high-k film gives the same capacitance with less tunnelling.",
            &[
                "EOT formula (MRS; IEEE technav)",
                "HfO2 k about 30 in one MRS source",
            ],
        ),
    Beat::new("Intel 45 nm: over 10x less leakage", BEAT_MS)
        .note(
            "Intel's 45 nm HKMG, with HfO2 at about 1.0 nm EOT, cut gate leakage by over 10x (Intel claim).",
            "The gate lit orange, with few leak dots.",
        )
        .detail(
            "The same film also gave about 20% more drive current (Intel claim).",
            &[
                "Intel 45 nm: HfO2 at about 1.0 nm EOT, TiAlN for NMOS (edn.com)",
                "Intel 45 nm: over 10x less gate leakage (Intel claim, newelectronics.co.uk)",
                "+20% drive current (Intel claim)",
            ],
        ),
    Beat::new("EOT: the thickness that counts", BEAT_MS)
        .note(
            "EOT is the electrical thickness that sets the capacitance, and it is what scales.",
            "The reference SiO2 film floats above the gate, labelled with the EOT formula.",
        )
        .detail(
            "The IL has a low k, so each 0.1 nm of IL uses up EOT budget.",
            &[
                "IL SiOx adds to EOT (MRS; IEEE technav)",
                "EOT formula (MRS; IEEE technav)",
            ],
        ),
];

// ---- zoom d: work-function metals and dipoles -------------------------------------------------

const ZD_BEATS: &[Beat] = &[
    Beat::new("TiAlC(N): the NMOS metal", BEAT_MS)
        .note(
            "On an NMOS the work-function metal is TiAlC(N), Al-rich, near silicon's conduction band.",
            "The blue-grey metal band of the NMOS gate, lit cyan.",
        )
        .detail(
            "The metal's work function sets the NMOS threshold voltage.",
            &[
                "TiAlC(N) for NMOS (page text, section 3)",
                "Work-function metal sets Vt; TiAlN for NMOS at Intel 45 nm (edn.com)",
            ],
        ),
    Beat::new("TiN: the PMOS metal", BEAT_MS)
        .note(
            "On a PMOS the metal is TiN, near the valence band.",
            "The PMOS gate beside it, its gold metal band lit cyan.",
        )
        .detail(
            "The two metals sit on the same high-k but set opposite thresholds.",
            &["PMOS WFM: TiN near the valence band (page text, section 3)"],
        ),
    Beat::new("La dipole: a cap shifts the threshold", BEAT_MS)
        .note(
            "A thin La cap drives a dipole into the high-k, which shifts the nFET threshold lower.",
            "A thin purple band just above the metal, in front of the NMOS gate.",
        )
        .detail(
            "La caps lower nFET Vt and Al-based caps raise pFET Vt. Recipes vary by foundry (textbook).",
            &[
                "La or Al cap driven in to shift the threshold (page text, section 1)",
                "Dipole recipes vary by foundry (textbook)",
            ],
        ),
    Beat::new("two gates, two thresholds", BEAT_MS)
        .note(
            "NMOS and PMOS side by side. Mixing metals and dipole caps gives several threshold options on one chip.",
            "Both gates at the same height, each with its own metal.",
        )
        .detail(
            "Thresholds come from dipole caps and metal thickness and composition (textbook).",
            &["Multi-Vt from dipole caps and metal thickness (general literature, not verified by a source here)"],
        ),
];

// ---- zoom e: the stack in a nanosheet gap -------------------------------------------------------

const ZE_BEATS: &[Beat] = &[
    Beat::new("sheets, gate on four sides", BEAT_MS)
        .note(
            "In GAA the channel is stacked nanosheets, and the gate wraps all four sides of each sheet.",
            "Three grey-blue sheets, each with the gold and blue gate layers around it.",
        )
        .detail(
            "Wrapping the whole sheet gives the best control of the channel.",
            &["GAA: the gate wraps all four sides of each sheet (page text, section 6)"],
        ),
    Beat::new("IL, HfO2 and metal fit the gap", BEAT_MS)
        .note(
            "The interlayer, high-k and metal must all fit in the gap between sheets, a few nm across.",
            "A close view of one gap: the bands stacked, lit cyan.",
        )
        .detail(
            "ALD fills gaps this size one atomic layer at a time.",
            &[
                "Gaps a few nm (page text, section 6)",
                "ALD, one atomic layer per cycle (page text, section 1)",
            ],
        ),
    Beat::new("tight gaps: Vt varies", BEAT_MS)
        .note(
            "Small thickness changes in a tiny gap shift the threshold from sheet to sheet.",
            "The gap at the top, lit cyan, next to the sheet below it.",
        )
        .detail(
            "Threshold variability in the gaps is a chokepoint for GAA.",
            &["Threshold variability in tiny GAA gaps (page text, section 9)"],
        ),
    Beat::new("the channel carries current", BEAT_MS)
        .note(
            "With the gate on, the sheets form the channel that carries the current.",
            "The three sheets lit, the channel on.",
        )
        .detail(
            "Each sheet adds drive, and the one gate controls all of them (textbook).",
            &["GAA channel: stacked sheets under one gate (textbook)"],
        ),
];

// ---- sections ------------------------------------------------------------------------------------

// 1 what happens: the whole chip, the layers grown by ALD, then the metal.
const S1_BEATS: &[Beat] = &[
    Beat::new("the whole chip, the NMOS gate still bare", BEAT_MS)
        .note(
            "The whole chip. The NMOS gate is still bare silicon, highlighted in cyan.",
            "The whole chip, with the NMOS box in cyan and no gate films yet.",
        )
        .detail(
            "The stack is built here, one film at a time, on this one transistor.",
            &["Gate-last HKMG (page text, section 1)"],
        ),
    Beat::new("ALD grows the dielectric", BEAT_MS)
        .note(
            "ALD grows the interlayer, then the HfO2, one atomic layer per cycle.",
            "The grey interlayer and the yellow HfO2 appear on the silicon.",
        )
        .detail(
            "The thickness is set by the number of cycles.",
            &[
                "ALD, one atomic layer per cycle (page text, section 1)",
                "IL ~0.5 nm; HfO2 1.5-2 nm (page text, section 1)",
            ],
        ),
    Beat::new("metal grows, and the fill closes it", BEAT_MS)
        .note(
            "The TiN cap, the work-function metal and the tungsten fill go on top, and the fill is polished flat.",
            "The gold and blue metal bands and the grey tungsten block.",
        )
        .detail(
            "The metal sets Vt, and the fill sets the gate resistance.",
            &["TiN CAP, WORK-FUNCTION, METAL FILL (page text, section 1)"],
        ),
];

// 2 the replacement-metal-gate flow: the scene of zoom b.
const S2_BEATS: &[Beat] = ZB_BEATS;

// 3 one replacement gate in section: the scene of zoom a.
const S3_BEATS: &[Beat] = ZA_BEATS;

// 4 gate-first versus gate-last.
const S4_BEATS: &[Beat] = &[
    Beat::new("gate-first: the stack in before the anneal", BEAT_MS)
        .note(
            "Gate-first puts the stack in before the source and drain anneal, so the high-k sees about 1000 C.",
            "The full gate in place, the source and drain glowing orange.",
        )
        .detail(
            "Vt shifts with the thermal budget, which is why gate-first lost ground.",
            &["GATE-FIRST: high-k sees about 1000 C (IBM Common Platform, 32/28 nm)"],
        ),
    Beat::new("gate-last: dummy poly takes the heat", BEAT_MS)
        .note(
            "Gate-last puts a poly placeholder in while the source and drain anneal runs.",
            "The brown poly stands where the stack will go, and the source and drain glow.",
        )
        .detail(
            "The stack never sees the hot steps.",
            &["GATE-LAST: dummy poly first (Intel 45 nm, TSMC 28 nm)"],
        ),
    Beat::new("gate-last: the finished stack", BEAT_MS)
        .note(
            "After the anneal the poly is pulled out and the stack goes in.",
            "The finished HKMG gate, with no glow.",
        )
        .detail(
            "Gate-last won as nodes shrank, for its stable Vt.",
            &["Gate-last: Intel 45 nm, TSMC 28 nm (edn.com; bit-tech.net)"],
        ),
];

// 5 EOT and leakage: the scene of zoom c.
const S5_BEATS: &[Beat] = ZC_BEATS;

// 6 threshold tuning in a nanosheet gate.
const S6_BEATS: &[Beat] = &[
    Beat::new("a La cap on one sheet lowers Vt", BEAT_MS)
        .note(
            "A thin La dipole cap on one sheet's metal pulls its nFET threshold lower.",
            "The purple La band in the bottom gap, in front of the sheets.",
        )
        .detail(
            "La-based caps lower Vt on nFETs (textbook; not verified by a source here).",
            &["La or Al cap driven in to shift the threshold (page text, section 1)"],
        ),
    Beat::new("an Al cap on another raises it", BEAT_MS)
        .note(
            "On another sheet an Al cap raises the threshold.",
            "The purple band in the upper gap.",
        )
        .detail(
            "Al-based caps raise pFET Vt (textbook; not verified by a source here).",
            &["Recipes vary by foundry (textbook)"],
        ),
    Beat::new("several Vt on one gate stack", BEAT_MS)
        .note(
            "Mixing caps and metal thickness gives several thresholds in one nanosheet stack.",
            "Both dipoles lit in their gaps across the sheets.",
        )
        .detail(
            "Thresholds come from metal thickness and composition, which vary by foundry.",
            &["Multi-Vt from dipole caps and metal thickness (general literature, not verified here)"],
        ),
];

// 7 by the numbers.
const S7_BEATS: &[Beat] = &[
    Beat::new("SiO2 limit: about 1.2 nm", BEAT_MS)
        .note(
            "The SiO2 gate oxide reached its limit near 1.2 nm at the 90 nm node, where direct tunnelling leaked too much.",
            "The thin pale SiO2 film, with the leak dots below it.",
        )
        .detail(
            "Past this point the leakage was no longer acceptable.",
            &["SiO2 below about 1.2 nm tunnels at the 90 nm node (IEEE technav)"],
        ),
    Beat::new("HfO2: about 1.0 nm EOT at 45 nm", BEAT_MS)
        .note(
            "Intel's 45 nm HKMG used HfO2 at about 1.0 nm EOT, with HfO2 k about 20-25 in practice.",
            "The yellow HfO2 film, with the gate lit.",
        )
        .detail(
            "HfO2 k is about 30 in one MRS source, against 3.9 for SiO2.",
            &[
                "Intel 45 nm: HfO2 at about 1.0 nm EOT (edn.com)",
                "HfO2 k about 30 in one MRS source; 20-25 in practice (page text, section 7)",
            ],
        ),
    Beat::new("ALD market: $3.0B in 2024", BEAT_MS)
        .note(
            "Single-wafer ALD was a $3.0B market in 2024, and ASM forecasts $5.1-6.1B by 2030.",
            "The finished gate, with the ALD glow over it.",
        )
        .detail(
            "ASM reported 2025 revenue of about EUR 3.2B and a 51.8% gross margin, driven by 2 nm GAA.",
            &[
                "ASM FY2025: EUR 3.2B revenue, 51.8% gross margin (investegate)",
                "Single-wafer ALD $3.0B in 2024; $5.1-6.1B by 2030 (page text, section 7)",
            ],
        ),
];

// 8 who makes it.
const S8_BEATS: &[Beat] = &[
    Beat::new("ASM International (ASM.AS)", BEAT_MS)
        .note(
            "ASM International leads in ALD and makes the HKMG reactors. It claims the lead in single-wafer ALD.",
            "The interlayer and the HfO2 lit, the ALD layers.",
        )
        .detail(
            "The single-wafer share is the company's claim, not an independent figure.",
            &[
                "ASM: HKMG reactors, claimed single-wafer ALD share (page text, section 8)",
                "ASM FY2025 results (investegate)",
            ],
        ),
    Beat::new("Applied Materials, Lam Research", BEAT_MS)
        .note(
            "Applied: the Centura dielectric stack and Endura TiN. Lam: ALD tungsten (ALTUS), and ALTUS Halo molybdenum aimed at GAA.",
            "The metal bands and the tungsten fill lit.",
        )
        .detail(
            "Their tools lay down the metal that sets Vt and fill the gate.",
            &[
                "Applied Endura PVD/ALD (appliedmaterials.com)",
                "Lam ALTUS Halo for GAA (siliconsemiconductor)",
            ],
        ),
    Beat::new("TEL, TSMC, Intel", BEAT_MS)
        .note(
            "Tokyo Electron makes furnace and ALD tools. TSMC and Intel integrate the stack in production.",
            "The whole gate lit, as a finished device.",
        )
        .detail(
            "The foundries choose the gate flow, gate-first or gate-last.",
            &[
                "Tokyo Electron (8035.T): furnace and ALD tools (page text, section 8)",
                "TSMC 28 nm gate-last; Intel 45 nm (page text, section 8)",
            ],
        ),
];

// 9 chokepoints and risks.
const S9_BEATS: &[Beat] = &[
    Beat::new("Vt variation in tiny gaps", BEAT_MS)
        .note(
            "In GAA gaps of a few nm, small thickness changes move the threshold from sheet to sheet.",
            "The gaps around the sheets, the top one lit.",
        )
        .detail(
            "Threshold variability is the main GAA gate risk.",
            &["Threshold variability in tiny GAA gaps (page text, section 9)"],
        ),
    Beat::new("IL thickness: 0.1 nm matters", BEAT_MS)
        .note(
            "Each 0.1 nm of interlayer uses up EOT budget, so ALD uniformity has to hold across the wafer.",
            "The thin interlayer band in the gap, lit.",
        )
        .detail(
            "Atomic control of the interlayer is a chokepoint.",
            &[
                "Low-k IL: every 0.1 nm eats EOT (page text, section 5)",
                "ALD uniformity and interlayer control (page text, section 9)",
            ],
        ),
    Beat::new("fill voids as gates shrink", BEAT_MS)
        .note(
            "As gates shrink, the tungsten fill can leave a void.",
            "The dark void in the fill, in the gap.",
        )
        .detail(
            "Voids raise the gate resistance.",
            &["Fill voids as gates shrink (page text, section 9)"],
        ),
];

// 10 sources: the whole chip, a slow pull-back, the source numbers as labels.
const S10_BEATS: &[Beat] = &[
    Beat::new("sources 1-2: Intel 45 nm", BEAT_MS)
        .note(
            "The whole chip, slowly pulling back. Sources 1 and 2 are the Intel 45 nm HKMG.",
            "The whole chip, with the NMOS gate lit and the source label.",
        )
        .detail(
            "Intel put HKMG into production at 45 nm (Penryn, 2007).",
            &[
                "[1] newelectronics.co.uk/content/news/intel-uses-high-k-and-metal-gates-in-45nm-process",
                "[2] EDN Intel 45 nm HKMG recipe: edn.com/?p=4005680",
            ],
        ),
    Beat::new("sources 3-4: HfO2, EOT, gate-last", BEAT_MS)
        .note(
            "Sources 3 and 4 cover the HfO2 and interlayer, the EOT, and the gate-first and gate-last comparison.",
            "The whole chip, pulled back a little further.",
        )
        .detail(
            "The HfO2 and EOT facts come from MRS and IEEE technav; the gate-last comparison from IEDM 2010.",
            &[
                "[3] MRS 'Scalability of MOCVD-deposited hafnium oxide'; technav.ieee.org/topic/high-k-gate-dielectrics/",
                "[4] bit-tech.net/reviews/tech/global-foundries-gtc-2010/3/; realworldtech.com/iedm-2010/5",
            ],
        ),
    Beat::new("sources 5-8: ASM, Lam, Applied", BEAT_MS)
        .note(
            "Sources 5 to 8 are the company filings and product pages for ASM, Lam and Applied.",
            "The whole chip, pulled back to its widest.",
        )
        .detail(
            "Company figures are the companies' own reports; the market size is ASM's forecast.",
            &[
                "[5] ASM FY2025 results: investegate.co.uk (ASM International)",
                "[6] Lam FY2025 10-K: sec.gov/Archives/edgar/data/707549/000070754925000075/lrcx-20250629.htm",
                "[7] Applied: appliedmaterials.com/us/en/product-library/endura-ilb-pvd-ald.html",
                "[8] Lam Halo: siliconsemiconductor.net/article/121172/Lam_Research_ushers_in_new_era_of_semiconductor_metallisation_",
            ],
        ),
];

// ---- the pictures ----------------------------------------------------------------------------

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

pub fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_a.glb"),
        ZA_BEATS,
    )
}

pub fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_b.glb"),
        ZB_BEATS,
    )
}

pub fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_c.glb"),
        ZC_BEATS,
    )
}

pub fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_d.glb"),
        ZD_BEATS,
    )
}

pub fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the layers, from interlayer to fill",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "gate-last: dummy poly, pull, replace",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "EOT: why the oxide had to go",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "work-function metals and dipoles",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "the stack in a nanosheet gap",
        build: zoom_e,
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_gate_stack_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of CHIP_GATE_STACK.txt, in order.
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

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "GATE STACK",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_keys_are_abcde() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
    }

    #[test]
    fn beat_counts_match_the_scripts() {
        let zooms: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(zooms, [4, 4, 4, 4, 4]);
        let secs: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(secs, [3, 4, 4, 3, 4, 3, 3, 3, 3, 3]);
        assert_eq!(build().beats().len(), BEATS.len());
    }

    #[test]
    fn every_scene_is_explained_and_draws() {
        super::super::super::blender::explained(build().as_ref(), "overview");
        super::super::super::blender::draws_every_beat(build().as_ref(), "overview");
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
