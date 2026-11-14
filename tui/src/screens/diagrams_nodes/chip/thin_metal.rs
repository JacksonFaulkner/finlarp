// CHIP tab, THIN METAL: the overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on the thin wiring; zoom-ins a-e and sections 1-10 are the same chip
// from other poses (tools/pbr3d/blender/chip_thin_metal.py).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the whole chip, thin wiring lit", BEAT_MS)
        .note(
            "M1-M4 are the thinnest wiring levels, just above the transistors. They carry signals from cell to cell.",
            "The whole chip, with the cyan band of thin copper levels over the transistors.",
        )
        .detail(
            "Each thin level is one damascene loop, printed at about 20-30 nm pitch.",
            &["M1-M4 pitch ~20-30 nm (CHIP_THIN_METAL section 1)"],
        ),
    Beat::new("in on the dense local wires", BEAT_MS)
        .note(
            "The camera glides in. Four levels of copper runs stack close together, each one line in low-k dielectric.",
            "Horizontal copper runs stacked in the lit band, the levels close together.",
        )
        .detail(
            "Thin levels are printed at the tightest pitch the node allows.",
            &["EUV 0.33 NA: ~26 nm pitch single exposure (CHIP_THIN_METAL section 7)"],
        ),
    Beat::new("a short local hop", BEAT_MS)
        .note(
            "A signal climbs from the NMOS drain through a via to M3, runs across one cell and drops down to the PMOS drain.",
            "White pulses rise the column on the left, run across the level and fall the column on the right.",
        )
        .detail(
            "Local hops like this are most of the wiring inside a cell; their RC now dominates gate delay.",
            &["RC delay of thin wires dominates gate delay (CHIP_THIN_METAL section 9)"],
        ),
    Beat::new("narrow wire, high resistance", BEAT_MS)
        .note(
            "Close on one run. Once the barrier is counted, the copper core is only about 12-15 nm wide. The barrier skin does not shrink with the line, so it takes a growing share of the cross-section and resistance rises.",
            "A glassy blue skin around the copper run, with the signal pulses bunched along it.",
        )
        .detail(
            "The fixed barrier is what makes narrow lines resistive.",
            &[
                "Core ~12-15 nm after barrier (CHIP_THIN_METAL section 2)",
                "Barrier 1-2 nm per side; one source says it is too thick below ~15 nm width",
            ],
        ),
    Beat::new("EUV prints the tight pitch", BEAT_MS)
        .note(
            "An EUV exposure slit sweeps across the band. A 0.33 NA scanner prints lines at about 26 nm pitch in one pass; below that the layer needs two exposures or a self-aligned scheme.",
            "A cyan slit moving across the thin levels, the lines under it.",
        )
        .detail(
            "Pitch is set by lithography; the wire width then follows from the pitch and the barrier.",
            &[
                "EUV 0.33 NA: ~26 nm pitch single exposure (CHIP_THIN_METAL section 7)",
                "High-NA 0.55: ~16 nm pitch reported (CHIP_THIN_METAL section 7)",
                "TSMC N3E minimum metal pitch 23 nm (IEDM 2022 via WikiChip)",
            ],
        ),
    Beat::new("whole chip again", BEAT_MS)
        .note(
            "Back out to the whole chip. The thin levels are the densest and the most resistive; ruthenium or molybdenum may replace copper here first.",
            "The whole chip, the thin band still lit.",
        )
        .detail(
            "Ru and Mo are candidates for the thinnest lines; copper's barrier is the problem.",
            &[
                "Ru may beat Cu at ~17 nm width and below (CHIP_THIN_METAL section 4)",
                "AMAT claims RuCo liner cut to 2 nm and line resistance down up to 25% (company claim)",
            ],
        ),
];

// ---- zoom-ins a-e (three beats each) ----------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("litho and trench etch", BEAT_MS)
        .note(
            "The mask prints the level pitch, and the trench is etched down through the low-k dielectric. This is the first step of each thin level.",
            "An amber mask lit over the M3 run, the dielectric around it being cut.",
        )
        .detail(
            "The pitch is set here, and the trench width then sets the line width.",
            &[
                "LITHO PITCH: EUV 26-30 nm, or 193i multipatterning (CHIP_THIN_METAL section 1)",
                "TRENCH ETCH through a hard mask (CHIP_THIN_METAL section 1)",
            ],
        ),
    Beat::new("barrier, liner and copper fill", BEAT_MS)
        .note(
            "A 1-2 nm Ta/TaN barrier, with Co or Ru as the liner, lines the trench. Copper then fills it. The pale dots are the fill moving along the run.",
            "A glassy barrier skin over the M3 run, with bright fill dots streaming along it.",
        )
        .detail(
            "Copper is plated or reflowed into the trench; the barrier does not scale down with the line.",
            &[
                "BARRIER+LINER Ta/TaN with Co or Ru, 1-2 nm (CHIP_THIN_METAL section 1)",
                "The barrier does not shrink with line width (CHIP_THIN_METAL section 2)",
            ],
        ),
    Beat::new("CMP, cap and via", BEAT_MS)
        .note(
            "The copper is polished flat, a cap seals the top, and a via opens up to the next level. The next level is then built on top.",
            "A pale cap slab on the top of the M3 run, and a copper via rising from it to the level above.",
        )
        .detail(
            "Each level repeats the loop, and M1 to M4 together repeat it about four times.",
            &[
                "CMP, then CAP + VIA to the next level (CHIP_THIN_METAL section 1)",
                "M1-M4 repeat the loop about four times at 20-40 nm pitch (CHIP_THIN_METAL section 1)",
            ],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("copper core, 12-15 nm", BEAT_MS)
        .note(
            "Once the barrier is counted, only about 12-15 nm of the line is copper. The rest is the barrier.",
            "Close on the copper run, its core tagged on the wire.",
        )
        .detail(
            "Grain and surface scattering also raise the resistivity of copper as lines narrow.",
            &[
                "Core ~12-15 nm after barrier (CHIP_THIN_METAL section 2)",
                "Resistivity rises from grain and surface scattering (textbook)",
            ],
        ),
    Beat::new("low-k dielectric between the lines", BEAT_MS)
        .note(
            "The spaces between the lines are SiOCH with k about 2.5-3, spaced at half the pitch. Air gaps can lower k further.",
            "A pale cyan slab in the gap above the M3 run, the low-k between the lines.",
        )
        .detail(
            "A lower k means less capacitance between neighbouring lines.",
            &[
                "SiOCH at k about 2.5-3, with optional air gaps (CHIP_THIN_METAL section 2)",
                "Spacing is half the pitch (CHIP_THIN_METAL section 2)",
            ],
        ),
    Beat::new("the barrier takes a growing share", BEAT_MS)
        .note(
            "The 1-2 nm barrier sits on three sides of every line and does not scale down. As the line narrows it takes a bigger share of the cross-section.",
            "A translucent blue skin around the M3 run, with the copper core inside.",
        )
        .detail(
            "A fixed skin is why narrow lines are resistive.",
            &["Barrier 1-2 nm on three sides, not scaling with width (CHIP_THIN_METAL section 2)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("DAMASCENE: copper inlaid in low-k", BEAT_MS)
        .note(
            "Copper cannot be dry-etched, so the trench is cut in the dielectric, filled with copper and polished. The tag marks the inlaid copper.",
            "A cyan dielectric band over the M2 run, with the copper inlaid in it.",
        )
        .detail(
            "Every copper node is damascene.",
            &["DAMASCENE: copper cannot be dry-etched (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("SUBTRACTIVE: metal etched to lines", BEAT_MS)
        .note(
            "Ru, Mo and W etch to volatile products, so the metal can be etched into lines from a blanket, and the gaps filled with dielectric afterwards.",
            "A violet metal band over the M2 run, the lines standing alone.",
        )
        .detail(
            "The subtractive route allows air gaps and needs no liner.",
            &["SUBTRACTIVE: Ru, Mo and W etch to volatile products (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("Ru and Mo: beyond copper", BEAT_MS)
        .note(
            "Ruthenium may beat copper at about 17 nm width and below in one analysis. imec has etched Ru and Mo at 32 nm pitch and below. The dots run along the violet Ru line.",
            "Cyan signal dots running along the violet M2 run.",
        )
        .detail(
            "These are candidates; the electromigration data for Mo are less clear.",
            &[
                "Ru may beat Cu at ~17 nm width and below (CHIP_THIN_METAL section 4)",
                "imec direct-etched Ru and Mo at 32 nm pitch and below (CHIP_THIN_METAL section 4)",
            ],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("a via placed by overlay alone", BEAT_MS)
        .note(
            "A via placed only by lithography overlay can land off its line. The amber column is where overlay alone puts it, beside the copper via.",
            "An amber via column to the right of the real copper via, rising through the levels.",
        )
        .detail(
            "Overlay needs about a quarter of the via pitch, and the tightest via pitches fall below EUV resolution.",
            &[
                "Overlay needs about 1/4 of the via pitch (CHIP_THIN_METAL section 5)",
                "The tightest via pitches fall below EUV resolution (CHIP_THIN_METAL section 5)",
            ],
        ),
    Beat::new("shifted: a short or a wall hit", BEAT_MS)
        .note(
            "A shifted via can short to a neighbouring line or hit the low-k wall. The red column has moved further right, clear of the run it should land on.",
            "A red via column further right, off the end of the copper run it should land on.",
        )
        .detail(
            "Edge placement error shorts or opens lines at this pitch.",
            &["Edge placement error shorts or opens lines (CHIP_THIN_METAL details, failure modes)"],
        ),
    Beat::new("SELF-ALIGNED VIA: lands on its own line", BEAT_MS)
        .note(
            "The via hole is bounded by the line below, by dielectric grown over the neighbours or by a metal-selective etch. The via lands only on its own line.",
            "A cyan via column standing on the end of the M3 run, where it lands on its own line.",
        )
        .detail(
            "Selective dielectric growth or a metal-selective etch sets the boundary.",
            &["SELF-ALIGNED VIA: the hole is bounded by the line below (CHIP_THIN_METAL section 5)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("PIN ACCESS on M1 and M2", BEAT_MS)
        .note(
            "Cell pins sit on M1 and M2 inside the cell, and the router must reach each one from above.",
            "A cyan band over the M1 run in a standard cell, with the pin tag above the M2 run.",
        )
        .detail(
            "Libraries require a minimum number of accessible M1 tracks per pin.",
            &[
                "PIN ACCESS on M1 and M2 (CHIP_THIN_METAL section 6)",
                "Libraries enforce a minimum of accessible M1 tracks per pin (CHIP_THIN_METAL section 6)",
            ],
        ),
    Beat::new("more pins, fewer tracks", BEAT_MS)
        .note(
            "Shrinking from 7.5 to 6 to 5 tracks packs more pins into the same cell, and each pin is covered by fewer tracks. Blockages can strand pins.",
            "Five orange pin dots crowding the M1 run.",
        )
        .detail(
            "Congestion grows as the cell shrinks.",
            &[
                "7.5 to 6 to 5 tracks raises pin density and congestion (CHIP_THIN_METAL section 6)",
                "Blockages can leave pins unreachable (CHIP_THIN_METAL section 6)",
            ],
        ),
    Beat::new("routers join the pins", BEAT_MS)
        .note(
            "Synopsys and Cadence place-and-route tools find the paths from above. Some M2 pins are hand-placed. The dots run along the M2 route.",
            "Cyan signal dots running along the M2 run.",
        )
        .detail(
            "The router has to reach each pin from above, so pin placement and routing are planned together.",
            &[
                "Synopsys (SNPS) and Cadence (CDNS) place-and-route tools (CHIP_THIN_METAL section 6)",
                "Some M2 pins are hand-placed (CHIP_THIN_METAL section 6)",
            ],
        ),
];

// ---- sections 1-10 (one picture per `# ` heading of CHIP_THIN_METAL.txt) --------------------

const SEC1_BEATS: &[Beat] = &[
    Beat::new("M1-M4: the thinnest wiring levels", BEAT_MS)
        .note(
            "The whole chip with the thin band lit. M1-M4 are the thinnest local wiring, just above the transistors.",
            "The whole chip, the cyan thin band over the transistors, tagged thin metal M1-M4.",
        )
        .detail(
            "Each thin level is one damascene loop, at a pitch of about 20-40 nm.",
            &["M1-M4 at about 20-40 nm pitch (CHIP_THIN_METAL section 1)"],
        ),
    Beat::new("one loop per level", BEAT_MS)
        .note(
            "Each level is printed, etched, lined, filled, polished and capped. The amber mask marks the M1 level while its loop runs.",
            "The amber mask on the lowest thin run, tagged one damascene loop per level.",
        )
        .detail(
            "The loop repeats about four times for M1-M4.",
            &["The loop repeats about four times for M1-M4 (CHIP_THIN_METAL section 1)"],
        ),
    Beat::new("M1 to M4 stacked", BEAT_MS)
        .note(
            "The four levels stack in the thin band, each a layer of copper runs in low-k. Each is tagged M1 to M4 at the right.",
            "Four tags, M1 to M4, one beside each level at the right of the band.",
        )
        .detail(
            "Higher levels get thicker and wider, because RC falls with the cross-section.",
            &["Higher levels thicken because RC falls with cross-section (CHIP_THIN_METAL section 9, notes)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("copper core, 12-15 nm", BEAT_MS)
        .note(
            "Once the barrier is counted, the copper in the M3 run is only about 12-15 nm wide.",
            "Close on the M3 copper run, its core tagged on the wire.",
        )
        .detail(
            "The barrier does not shrink, so the copper core is what is left.",
            &["Core ~12-15 nm after barrier (CHIP_THIN_METAL section 2)"],
        ),
    Beat::new("low-k between the lines", BEAT_MS)
        .note(
            "The spaces are SiOCH at k about 2.5-3, with optional air gaps, spaced at half the pitch.",
            "A pale cyan slab in the gap above the M3 run, tagged low-k between lines.",
        )
        .detail(
            "A lower k lowers the capacitance between neighbours.",
            &["SiOCH at k about 2.5-3, with optional air gaps (CHIP_THIN_METAL section 2)"],
        ),
    Beat::new("barrier on three sides", BEAT_MS)
        .note(
            "A 1-2 nm barrier lines three sides of each line. The copper is the core inside it.",
            "A translucent blue skin around the M3 run.",
        )
        .detail(
            "A fixed skin takes a bigger share as the line narrows.",
            &["Barrier 1-2 nm on three sides (CHIP_THIN_METAL section 2)"],
        ),
    Beat::new("vias stack the levels", BEAT_MS)
        .note(
            "Vias connect each thin level to the one above. The two cyan columns are vias standing at the ends of the M3 run.",
            "Two cyan via columns rising through the thin band, tagged vias stack the levels.",
        )
        .detail(
            "Each via lands on a line below and joins the level above, after a cap.",
            &["CAP + VIA to the next level (CHIP_THIN_METAL section 1)"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("DAMASCENE: copper inlaid in low-k", BEAT_MS)
        .note(
            "Copper cannot be dry-etched, so the trench is cut in the dielectric, filled with copper and polished. The tag marks the inlaid copper.",
            "A cyan dielectric band over the M2 run, with the copper inlaid in it.",
        )
        .detail(
            "Every copper node is damascene.",
            &["DAMASCENE: copper cannot be dry-etched (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("SUBTRACTIVE: metal etched to lines", BEAT_MS)
        .note(
            "Ru, Mo and W etch to volatile products, so the metal can be etched into lines from a blanket, and the gaps filled with dielectric afterwards.",
            "A violet metal band over the M2 run, the lines standing alone.",
        )
        .detail(
            "The subtractive route allows air gaps and needs no liner.",
            &["SUBTRACTIVE: Ru, Mo and W etch to volatile products (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("Ru and Mo etch to volatile products", BEAT_MS)
        .note(
            "Ruthenium and molybdenum can be dry-etched, which is what opens the subtractive route to them. The dots run along the violet Ru line.",
            "Cyan signal dots running along the violet M2 run.",
        )
        .detail(
            "Ru and Mo are the metals that make the subtractive route possible.",
            &["Ru, Mo and W form volatile etch products (CHIP_THIN_METAL section 3)"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("copper with a RuCo liner", BEAT_MS)
        .note(
            "Copper needs a barrier and a liner. A RuCo liner can cut the liner to about 2 nm; one company claims line resistance falls by up to 25 percent.",
            "A translucent blue liner band over the M2 run.",
        )
        .detail(
            "The 25 percent figure is a company claim, not an independent measurement.",
            &["Applied claim: RuCo liner to about 2 nm, line resistance down up to 25% (CHIP_THIN_METAL section 4)"],
        ),
    Beat::new("ruthenium: steadier with width", BEAT_MS)
        .note(
            "Ruthenium's resistance depends less on width. One analysis has it beating copper at about 17 nm width and below.",
            "A violet band over the M3 run.",
        )
        .detail(
            "This is one analysis, not a production choice.",
            &["Ru beats Cu at 17 nm width and below in one analysis (CHIP_THIN_METAL section 4)"],
        ),
    Beat::new("molybdenum: low bulk mean free path", BEAT_MS)
        .note(
            "Molybdenum has a low bulk mean free path. imec has etched Ru and Mo directly at 32 nm pitch and below; the electromigration data are less clear.",
            "A violet band over the M1 run in the cell.",
        )
        .detail(
            "Electromigration data for molybdenum are less clear than for copper.",
            &["imec direct-etched Ru and Mo at 32 nm pitch and below (CHIP_THIN_METAL section 4)"],
        ),
    Beat::new("liners for the thinnest levels", BEAT_MS)
        .note(
            "Cobalt, the traditional liner and fill, costs yield and resistance at 3 nm and below. The blue band over the M2 run stands for the liner.",
            "A blue liner band over the M2 run, tagged cobalt yield and R cost at 3 nm.",
        )
        .detail(
            "The liner and fill metal are the choices that matter most at the thinnest levels.",
            &[
                "Cobalt costs yield and resistance at 3 nm and below (CHIP_THIN_METAL section 4)",
                "Liner and fill choice for the thinnest levels (textbook)",
            ],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("a via placed by overlay alone", BEAT_MS)
        .note(
            "A via placed only by lithography overlay can land off its line. The amber column is where overlay alone puts it, beside the copper via.",
            "An amber via column to the right of the real copper via, rising through the levels.",
        )
        .detail(
            "Overlay needs about a quarter of the via pitch, and the tightest via pitches fall below EUV resolution.",
            &[
                "Overlay needs about 1/4 of the via pitch (CHIP_THIN_METAL section 5)",
                "The tightest via pitches fall below EUV resolution (CHIP_THIN_METAL section 5)",
            ],
        ),
    Beat::new("shifted: a short or a wall hit", BEAT_MS)
        .note(
            "A shifted via can short to a neighbouring line or hit the low-k wall. The red column has moved further right, clear of the run it should land on.",
            "A red via column further right, off the end of the copper run it should land on.",
        )
        .detail(
            "Edge placement error shorts or opens lines at this pitch.",
            &["Edge placement error shorts or opens lines (CHIP_THIN_METAL details, failure modes)"],
        ),
    Beat::new("SELF-ALIGNED VIA: lands on its own line", BEAT_MS)
        .note(
            "The via hole is bounded by the line below, by dielectric grown over the neighbours or by a metal-selective etch. The via lands only on its own line.",
            "A cyan via column standing on the end of the M3 run, where it lands on its own line.",
        )
        .detail(
            "Selective dielectric growth or a metal-selective etch sets the boundary.",
            &["SELF-ALIGNED VIA: the hole is bounded by the line below (CHIP_THIN_METAL section 5)"],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("PIN ACCESS on M1 and M2", BEAT_MS)
        .note(
            "Cell pins sit on M1 and M2 inside the cell, and the router must reach each one from above.",
            "A cyan band over the M1 run in a standard cell, with the pin tag above the M2 run.",
        )
        .detail(
            "Libraries require a minimum number of accessible M1 tracks per pin.",
            &[
                "PIN ACCESS on M1 and M2 (CHIP_THIN_METAL section 6)",
                "Libraries enforce a minimum of accessible M1 tracks per pin (CHIP_THIN_METAL section 6)",
            ],
        ),
    Beat::new("more pins, fewer tracks", BEAT_MS)
        .note(
            "Shrinking from 7.5 to 6 to 5 tracks packs more pins into the same cell, and each pin is covered by fewer tracks. Blockages can strand pins.",
            "Five orange pin dots crowding the M1 run.",
        )
        .detail(
            "Congestion grows as the cell shrinks.",
            &[
                "7.5 to 6 to 5 tracks raises pin density and congestion (CHIP_THIN_METAL section 6)",
                "Blockages can leave pins unreachable (CHIP_THIN_METAL section 6)",
            ],
        ),
    Beat::new("routers join the pins", BEAT_MS)
        .note(
            "Synopsys and Cadence place-and-route tools find the paths from above. Some M2 pins are hand-placed. The dots run along the M2 route.",
            "Cyan signal dots running along the M2 run.",
        )
        .detail(
            "The router has to reach each pin from above, so pin placement and routing are planned together.",
            &[
                "Synopsys (SNPS) and Cadence (CDNS) place-and-route tools (CHIP_THIN_METAL section 6)",
                "Some M2 pins are hand-placed (CHIP_THIN_METAL section 6)",
            ],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("EUV 0.33 NA: about 26 nm pitch", BEAT_MS)
        .note(
            "The EUV slit scans across the band and prints lines at about 26 nm pitch in one exposure.",
            "A wide translucent cyan slit sweeping across the thin levels.",
        )
        .detail(
            "Below about 26 nm the layer needs two exposures or a self-aligned scheme.",
            &["EUV 0.33 NA: about 26 nm pitch single exposure, 13 nm half-pitch (CHIP_THIN_METAL section 7)"],
        ),
    Beat::new("High-NA 0.55: about 16 nm pitch", BEAT_MS)
        .note(
            "High-NA is reported to reach about 16 nm pitch in one exposure. Intel uses it on selected 18A layers.",
            "A narrower cyan slit sweeping across the band.",
        )
        .detail(
            "This is a reported figure, not a measured one for any shipping node.",
            &[
                "High-NA 0.55: about 16 nm pitch reported (CHIP_THIN_METAL section 7)",
                "Intel uses High-NA on selected 18A layers (CHIP_THIN_METAL section 7)",
            ],
        ),
    Beat::new("TSMC N3E 23 nm, imec Ru 28 nm", BEAT_MS)
        .note(
            "TSMC N3E has a 23 nm minimum metal pitch. imec patterned 28 nm pitch Ru lines in one 0.33 NA exposure. No slit is shown here.",
            "The thin levels with the pitch tag, and no slit.",
        )
        .detail(
            "Public pitch figures are scarce; N2 and 14A are not public.",
            &[
                "TSMC N3E minimum metal pitch 23 nm (IEDM 2022 via WikiChip)",
                "imec 28 nm pitch Ru in one 0.33 NA exposure (CHIP_THIN_METAL section 7)",
            ],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("fabs set the pitch", BEAT_MS)
        .note(
            "TSMC, Intel and Samsung choose the metal pitch and the metal for each level.",
            "The thin band from a wide view, tagged with the fabs.",
        )
        .detail(
            "Pitch and metal choices are the fabs' decisions.",
            &["TSMC (TSM), Intel (INTC) and Samsung set pitch and metal choices (CHIP_THIN_METAL section 8)"],
        ),
    Beat::new("tool makers", BEAT_MS)
        .note(
            "Applied Materials sells copper barrier and seed and ruthenium CVD tools. Lam Research and Tokyo Electron etch and plate; ASML makes the EUV scanners.",
            "The thin band from a wide view, tagged with the tool makers.",
        )
        .detail(
            "The tools in these steps come from a few suppliers.",
            &["AMAT, LRCX, 8035.T and ASML (CHIP_THIN_METAL section 8)"],
        ),
    Beat::new("designers and routers", BEAT_MS)
        .note(
            "NVIDIA, AMD and Arm design cells that must route at these pitches. Synopsys and Cadence supply the routers.",
            "The thin band from a wide view, tagged with the designers and routers.",
        )
        .detail(
            "The designers and the routers have to meet the fabs' pitches.",
            &["NVDA, AMD, ARM, SNPS and CDNS (CHIP_THIN_METAL section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("new metals: maturity", BEAT_MS)
        .note(
            "CMP, etch and cost for ruthenium and molybdenum are not yet mature. The violet band over the M2 run stands for them.",
            "The violet band over the M2 run, tagged new metals maturity.",
        )
        .detail(
            "Adoption depends on CMP and etch maturity.",
            &["CMP, etch and cost for Ru and Mo are not mature (CHIP_THIN_METAL section 9)"],
        ),
    Beat::new("RC: thin wires slow the signal", BEAT_MS)
        .note(
            "The RC of the thin wires now dominates gate delay, so the wires set the speed more than the transistors do.",
            "Cyan signal dots crossing the M3 run slowly.",
        )
        .detail(
            "At this level the wires, not the transistors, set the speed.",
            &["RC of thin wires dominates gate delay (CHIP_THIN_METAL section 9)"],
        ),
    Beat::new("N2 and 14A pitches not public", BEAT_MS)
        .note(
            "The metal pitches for N2 and 14A were not found in the public sources, so none are shown here.",
            "The whole chip, a slow pull-back, tagged N2 and 14A pitches not public.",
        )
        .detail(
            "Numbers without a source are left out.",
            &["N2 and 14A metal pitches not public in the sources found (CHIP_THIN_METAL section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-4", BEAT_MS)
        .note(
            "Semiengineering on ruthenium interconnects and the end of copper; semiengineering on ruthenium liners; Applied Materials on chip wiring; a US patent on self-aligned vias.",
            "The whole chip, slowly pulling back.",
        )
        .detail(
            "Sources for the interconnect and ruthenium claims.",
            &[
                "[1] semiengineering.com/ruthenium-interconnects-on-tap; semiengineering.com/the-end-of-copper-interconnects",
                "[2] semiengineering.com/ruthenium-liners-give-way-to-ruthenium-lines",
                "[3] investor.appliedmaterials.com (news release; company claims)",
                "[4] US patent 10297467 (self-aligned via and plug patterning)",
            ],
        ),
    Beat::new("sources 5-7", BEAT_MS)
        .note(
            "imec on direct-etched ruthenium and molybdenum; an arXiv paper and an SPIE proceeding; HotHardware and HWBusters on High-NA and Panther Lake.",
            "The whole chip, slowly pulling back.",
        )
        .detail(
            "Sources for the etch, pitch and High-NA figures.",
            &[
                "[5] imec-publications.be (549e1c7f) on Ru and Mo etch",
                "[6] arxiv.org/pdf/2603.13665; SPIE conference proceedings 10148/1014803",
                "[7] hothardware.com (High-NA at Intel); hwbusters.com (Panther Lake High-NA)",
            ],
        ),
    Beat::new("sources 8-10", BEAT_MS)
        .note(
            "A teardown-based report on Intel 18A (unconfirmed); Wikipedia and WikiChip on the 3 nm pitch; an imec publication on the thin levels.",
            "The whole chip, slowly pulling back.",
        )
        .detail(
            "The teardown report is unconfirmed and is marked as such.",
            &[
                "[8] technews.tw (teardown-based, unconfirmed)",
                "[9] en.wikipedia.org/wiki/3nm; fuse.wikichip.org/?p=7375",
                "[10] imec-publications.be (dc425af8)",
            ],
        ),
];

// ---- the scenes -----------------------------------------------------------------------

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_thin_metal_sec",
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

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "one damascene loop",
        build: || -> Box<dyn Scene> {
            page(
                &ZA,
                include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal_zoom_a.glb"),
                ZA_BEATS,
            )
        },
    },
    Zoom {
        key: 'b',
        label: "copper, low-k and the barrier",
        build: || -> Box<dyn Scene> {
            page(
                &ZB,
                include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal_zoom_b.glb"),
                ZB_BEATS,
            )
        },
    },
    Zoom {
        key: 'c',
        label: "damascene vs subtractive; Ru and Mo",
        build: || -> Box<dyn Scene> {
            page(
                &ZC,
                include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal_zoom_c.glb"),
                ZC_BEATS,
            )
        },
    },
    Zoom {
        key: 'd',
        label: "self-aligned vias",
        build: || -> Box<dyn Scene> {
            page(
                &ZD,
                include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal_zoom_d.glb"),
                ZD_BEATS,
            )
        },
    },
    Zoom {
        key: 'e',
        label: "pin access in standard cells",
        build: || -> Box<dyn Scene> {
            page(
                &ZE,
                include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal_zoom_e.glb"),
                ZE_BEATS,
            )
        },
    },
];

static OVERVIEW_SCENE: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW_SCENE,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_thin_metal.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "THIN METAL",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_keys_are_abcde_and_every_beat_is_explained() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert!((3..=4).contains(&s.beats().len()), "zoom {}", z.key);
            super::super::super::blender::explained(s.as_ref(), &format!("zoom {}", z.key));
            super::super::super::blender::draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 4, 3, 4, 3, 3, 3, 3, 3, 3]);
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
