// CHIP tab, THIN METAL: the overview opens on the whole chip (tools/pbr3d/blender/chip_kit.py),
// then glides into a detailed cut-away of the M1-M4 levels set in the thin band; zoom-ins a-e and
// sections 1-10 are detailed cut-aways too (tools/pbr3d/blender/chip_thin_metal.py,
// chip_thin_metal_detail.py).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the whole chip, thin wiring lit", BEAT_MS)
        .note(
            "Just above the transistors sit four levels of very fine copper wiring, M1 to M4, that join neighbouring cells. They are the densest and the most resistive wires on the chip.",
            "The whole chip, with the cyan band of thin levels just above the transistors.",
        )
        .detail(
            "Each thin level is one damascene loop.",
            &["M1-M4 pitch ~20-40 nm (CHIP_THIN_METAL section 1)"],
        ),
    Beat::new("in on the dense local wires", BEAT_MS)
        .note(
            "The camera goes into the band and the schematic gives way to a cut-away of the real stack. Each level is a row of copper lines in a low-k insulator, alternate levels run at right angles, and tungsten contacts below reach the transistors.",
            "A stepped cut-away: brown copper lines in thin blue skins set in grey low-k, long brown bars on the levels that run across, and the dark contact layer at the bottom.",
        )
        .detail(
            "Thin levels are printed at the tightest pitch the node allows.",
            &[
                "M1-M4 pitch ~20-40 nm (CHIP_THIN_METAL section 1)",
                "EUV 0.33 NA: ~26 nm pitch single exposure (section 7)",
            ],
        ),
    Beat::new("a short local hop", BEAT_MS)
        .note(
            "A signal leaves one transistor through a tungsten contact, climbs an M1 line, rises through a via, runs along M2 and drops back down to the next cell. Most wiring inside and between cells is short hops like this, and their RC delay now outweighs the transistors' own delay.",
            "Cyan beads rising from a contact up an M1 line, back across its top, up a via, along the long M2 bar and down again.",
        )
        .detail(
            "Local hops are most of the wiring inside a cell.",
            &["RC delay of thin wires dominates gate delay (CHIP_THIN_METAL section 9)"],
        ),
    Beat::new("narrow wire, high resistance", BEAT_MS)
        .note(
            "Close on one M1 line. About 2 nm of TaN barrier and cobalt liner wraps three sides and does not shrink with the line, so a 16 nm line keeps only about a 12 nm copper core. Electrons also scatter off the walls, so resistance climbs faster than the line shrinks.",
            "One line cut end-on: the amber-glowing skin round the brown copper core, with beads zigzagging down between its walls.",
        )
        .detail(
            "The fixed barrier is what makes narrow lines resistive.",
            &[
                "Core ~12-15 nm after barrier (CHIP_THIN_METAL section 2)",
                "Barrier + liner 1-2 nm per side (section 2)",
            ],
        ),
    Beat::new("EUV prints the tight pitch", BEAT_MS)
        .note(
            "Every level's lines are printed by lithography. An EUV scanner sweeps an exposure slit across the wafer; at 0.33 NA it prints lines at about 26 nm pitch in one pass, and tighter levels need two exposures or a self-aligned scheme.",
            "A violet slit of EUV light sweeping across the top of the stack.",
        )
        .detail(
            "Pitch is set by lithography; the wire width then follows from the pitch and the barrier.",
            &[
                "EUV 0.33 NA: ~26 nm pitch single exposure (CHIP_THIN_METAL section 7)",
                "High-NA 0.55: ~16 nm pitch reported (section 7)",
                "TSMC N3E minimum metal pitch 23 nm (IEDM 2022 via WikiChip)",
            ],
        ),
    Beat::new("whole chip again", BEAT_MS)
        .note(
            "Back out to the whole chip. The thin levels are the densest and most resistive wiring, and the first place ruthenium or molybdenum may replace copper.",
            "The whole chip, the thin band lit again.",
        )
        .detail(
            "Copper's barrier is the problem at the thinnest levels.",
            &[
                "Ru may beat Cu at ~17 nm width and below, one analysis (CHIP_THIN_METAL section 4)",
                "RuCo liner: line R down up to 25% (Applied claim, section 4)",
            ],
        ),
];

// ---- zoom-ins a-e (three beats each) ----------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("litho and trench etch", BEAT_MS)
        .note(
            "EUV light through the reticle exposes a resist layer on a hard mask. The pattern is transferred into the mask, and a plasma etches trenches through it into the low-k below.",
            "Pink resist under a violet column of light from a grey reticle, then open trenches under dark hard-mask strips.",
        )
        .detail(
            "The trench sets the line's width and pitch.",
            &["EUV at ~26-30 nm pitch, or 193i multipatterning (CHIP_THIN_METAL section 1)"],
        ),
    Beat::new("barrier, liner and copper fill", BEAT_MS)
        .note(
            "A TaN barrier and a cobalt or ruthenium liner, together about 2 nm, coat each trench. Copper is then electroplated; additives in the bath make it fill from the bottom up so no voids are trapped, and it overfills the top.",
            "Blue-and-silver lining in the trenches, cyan ions raining in, copper rising from the trench floors, then a copper blanket over everything.",
        )
        .detail(
            "The lining keeps copper out of the insulator and helps it fill.",
            &[
                "Barrier + liner 1-2 nm (CHIP_THIN_METAL section 1)",
                "Copper plated or reflowed; or Ru, Mo (section 1)",
            ],
        ),
    Beat::new("CMP, cap and via", BEAT_MS)
        .note(
            "Chemical-mechanical polishing removes the extra copper and the hard mask, leaving lines inlaid flush with the low-k. An SiCN cap seals the copper, the next insulator goes on, and a via is opened down onto a line to start the next level.",
            "A dark pad sweeping across the copper, then a white cap, then a new grey layer with a copper via down to the middle line.",
        )
        .detail(
            "The loop then repeats for the next level.",
            &[
                "CMP stops on the dielectric (CHIP_THIN_METAL section 1)",
                "CAP + VIA to the next level (section 1)",
            ],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("copper core, 12-15 nm", BEAT_MS)
        .note(
            "Current flows in the copper core of each line. Here it runs along the long M2 line, above a row of M1 lines about 16 nm wide whose cores are only about 12 nm once the skin is counted.",
            "Cyan beads running along the long brown M2 bar, with M1 cut ends below it.",
        )
        .detail(
            "The barrier does not shrink, so the copper core is what is left.",
            &["Core ~12-15 nm after barrier (CHIP_THIN_METAL section 2)"],
        ),
    Beat::new("low-k dielectric between the lines", BEAT_MS)
        .note(
            "The insulator between lines is SiOCH, with a dielectric constant of about 2.5-3 against about 3.9 for SiO2. With lines this close, the capacitance to the neighbours is a large part of each wire's load, so a lower k means faster, lower-power wires.",
            "Two amber-lit low-k spaces between M1 lines.",
        )
        .detail(
            "Air gaps (k = 1) go further where they can be used.",
            &["SiOCH k ~2.5-3, optional air gaps (CHIP_THIN_METAL section 2)", "SiO2 k ~3.9"],
        ),
    Beat::new("the barrier takes a growing share", BEAT_MS)
        .note(
            "A TaN barrier and a cobalt liner, about 2 nm together, wrap three sides of every line. That skin stays the same as lines narrow, so it takes a bigger share of each smaller line, and electrons scatter off the walls as well.",
            "One line cut end-on, its skin glowing amber, beads zigzagging down the brown core.",
        )
        .detail(
            "A fixed skin takes a bigger share as the line narrows.",
            &[
                "Barrier 1-2 nm on three sides (CHIP_THIN_METAL section 2)",
                "A 16 nm line keeps a ~12 nm core",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("DAMASCENE: copper inlaid in low-k", BEAT_MS)
        .note(
            "Copper forms no volatile compounds, so a plasma can't etch it into lines. Instead trenches are cut in the low-k, lined, overfilled with copper and polished back.",
            "A low-k block: open trenches under a dark hard mask, a blue lining, a copper blanket, then a flat polished top under a white cap.",
        )
        .detail(
            "Every copper node is damascene.",
            &["DAMASCENE: copper can't be dry-etched (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("SUBTRACTIVE: metal etched to lines", BEAT_MS)
        .note(
            "Ruthenium, molybdenum and tungsten form volatile etch products, so a blanket of metal can be etched straight into lines. The gaps are then filled with dielectric, and pinching the fill off early leaves air gaps.",
            "A teal ruthenium slab under hard-mask strips, then three free-standing teal lines, then grey fill with dark air-gap slots between them.",
        )
        .detail(
            "The subtractive route allows air gaps and needs no liner.",
            &["Ru, Mo and W etch to volatile products (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("Ru and Mo: beyond copper", BEAT_MS)
        .note(
            "At the same 14 nm width, copper loses about a third of the line to its skin, while ruthenium and molybdenum need no barrier and lose less to thin-line scattering. One analysis has ruthenium beating copper at about 17 nm width and below.",
            "Three 14 nm lines in grey low-k: brown copper in a blue skin, teal ruthenium and gold-grey molybdenum.",
        )
        .detail(
            "This is one analysis, not a production choice.",
            &[
                "Ru beats Cu at ~17 nm width and below, one analysis (CHIP_THIN_METAL section 4)",
                "imec direct-etched Ru and Mo at 32 nm pitch and below (section 4)",
            ],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("a via placed by overlay alone", BEAT_MS)
        .note(
            "A via is printed in its own lithography step and has to line up with the line below. Here it does: the signal comes along the upper line, drops through the via and lands on its own line.",
            "Cyan beads running along the long top line, down the brown via and into the middle line below.",
        )
        .detail(
            "Overlay error has to stay within about a quarter of the via pitch.",
            &[
                "Overlay needs ~1/4 of the via pitch (CHIP_THIN_METAL section 5)",
                "Tightest via pitches are below EUV resolution (section 5)",
            ],
        ),
    Beat::new("shifted: a short or a wall hit", BEAT_MS)
        .note(
            "Shift the same via by half a space and its foot touches the next line over, so the signal leaks into the wrong wire: a short. If it only just misses, the thin sliver of insulator left can break down early.",
            "The via moved right; red beads go down it and into the neighbouring line, with a red glow where they meet.",
        )
        .detail(
            "Edge placement error shorts or opens lines at this pitch.",
            &["Edge placement error shorts or opens lines (CHIP_THIN_METAL details, failure modes)"],
        ),
    Beat::new("SELF-ALIGNED VIA: lands on its own line", BEAT_MS)
        .note(
            "In a self-aligned scheme, dielectric is grown selectively on top of the neighbouring lines, or a metal-selective etch is used. The via can be printed off-centre and still only reach its own line.",
            "White dielectric blocks on the two neighbours; the shifted via narrows between them, and cyan beads land on the middle line only.",
        )
        .detail(
            "The line below, not the overlay, sets where the via lands.",
            &["SELF-ALIGNED VIA: the hole is bounded by the line below (CHIP_THIN_METAL section 5)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("PIN ACCESS on M1 and M2", BEAT_MS)
        .note(
            "Logic is built from standard cells with power rails along the top and bottom and gates between them. Each cell's inputs and output are short M1 pins, and the router has to reach them from the M2 tracks above.",
            "Seen from above: gold VDD and VSS rails, dark red gates, three copper M1 pins (A, B and Y) and faint cyan M2 tracks crossing the cell.",
        )
        .detail(
            "Libraries require a minimum number of reachable tracks per pin.",
            &["PIN ACCESS on M1 and M2 (CHIP_THIN_METAL section 6)"],
        ),
    Beat::new("more pins, fewer tracks", BEAT_MS)
        .note(
            "A pin can only be reached where an M2 track crosses it. Shrinking cells from 7.5 to 6 to 5 tracks leaves each pin fewer crossings, and a track already used by another net blocks its access points.",
            "Green dots where tracks cross each pin; one track carries an orange wire from another net, and the dots on it are red.",
        )
        .detail(
            "Congestion grows as cells shrink.",
            &[
                "7.5 to 6 to 5 tracks raises pin density (CHIP_THIN_METAL section 6)",
                "Blockages can leave pins unreachable (section 6)",
            ],
        ),
    Beat::new("routers join the pins", BEAT_MS)
        .note(
            "Place-and-route software picks free tracks, drops vias onto the pins and joins them. Here an M2 wire ties pins A and B together and another carries output Y out of the cell, with signals riding both.",
            "Two copper M2 wires with vias onto the pins, cyan beads running along them.",
        )
        .detail(
            "Pin placement and routing are planned together.",
            &["Synopsys (SNPS) and Cadence (CDNS) place-and-route (CHIP_THIN_METAL section 6)"],
        ),
];

// ---- sections 1-10 (one picture per `# ` heading of CHIP_THIN_METAL.txt) --------------------
// The pictures are detailed cut-aways (chip_thin_metal_detail.py), not the schematic chip.

const SEC1_BEATS: &[Beat] = &[
    Beat::new("M1-M4: four thin copper levels", BEAT_MS)
        .note(
            "The thin metal levels are the first four layers of wiring above the transistors. Each level is a row of copper lines set in a low-k insulator, and alternate levels run at right angles so a signal can turn corners. Tungsten contacts below connect them down to the transistors.",
            "A stepped cut-away block. Brown copper lines with a thin blue skin (the barrier) sit in grey low-k; the long brown bars are levels running across the cut. The dark slab at the bottom is the contact layer and silicon.",
        )
        .detail(
            "These are the densest and most resistive wires on the chip.",
            &[
                "M1-M4 pitch ~20-40 nm (CHIP_THIN_METAL section 1)",
                "Four levels, one damascene loop each",
                "Alternate levels run at 90 degrees",
            ],
        ),
    Beat::new("one damascene loop: etch, line, fill, polish", BEAT_MS)
        .note(
            "Each level is built the same way. Trenches are etched into the low-k through a hard mask, lined with a TaN barrier and a cobalt or ruthenium liner, then overfilled with plated copper. Polishing (CMP) removes the excess and an SiCN cap seals the top.",
            "A small low-k block: open trenches under a dark hard mask, then a blue lining, then a copper blanket over everything, then a flat polished top under a white cap with three inlaid lines.",
        )
        .detail(
            "Copper can't be dry-etched, so it is inlaid rather than cut.",
            &[
                "Barrier + liner ~1-2 nm (CHIP_THIN_METAL section 1)",
                "EUV at ~26-30 nm pitch, or 193i multipatterning (section 1)",
                "The loop repeats once per level",
            ],
        ),
    Beat::new("M1 to M4, named", BEAT_MS)
        .note(
            "Back on the stack with each level named. M1 and M3 run into the picture, so their cut ends show as small rectangles; M2 and M4 run across it, so you see them lengthwise. Short vias between levels join a line to the one above.",
            "Tags M1 to M4 on the four steps: small brown rectangles on M1 and M3, long brown bars on M2 and M4, and short brown vias between the steps.",
        )
        .detail(
            "Each level up is a little wider and taller, because resistance falls with cross-section.",
            &[
                "Drawn: M1 ~32 nm pitch, M2 and M3 ~28 nm, M4 ~36 nm (illustrative)",
                "Real pitches vary by node; N2 and 14A are not public",
            ],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("a 16 nm line at a 32 nm pitch", BEAT_MS)
        .note(
            "Close on the M1 cut face. Each line is about 16 nm wide and twice as tall, and the next line sits one pitch away with insulator of about the same width between them. Only the inside of each line is copper.",
            "Brown rectangles (copper) with a thin blue rim, evenly spaced in grey low-k; above them a long M2 bar and its vias.",
        )
        .detail(
            "Pitch is line plus space; the space is roughly half the pitch.",
            &[
                "Line ~16 nm, pitch ~32 nm as drawn",
                "Copper core ~12-15 nm once the barrier is in (CHIP_THIN_METAL section 2)",
            ],
        ),
    Beat::new("low-k between the lines, sometimes air", BEAT_MS)
        .note(
            "The grey between lines is SiOCH, a porous carbon-doped oxide with a dielectric constant of about 2.5-3, against about 3.9 for plain SiO2. Lower k means less capacitance between neighbours, so less delay and power. Some processes leave air gaps (k = 1) in the spaces.",
            "The grey spaces between the copper lines, and two dark slots in the spaces on the right: air gaps.",
        )
        .detail(
            "Capacitance rises as lines get closer; low-k and air gaps push it back down.",
            &[
                "SiOCH k ~2.5-3 (CHIP_THIN_METAL section 2)",
                "SiO2 k ~3.9; air k = 1",
                "Air gaps are optional (section 2)",
            ],
        ),
    Beat::new("the barrier skin does not shrink", BEAT_MS)
        .note(
            "Each line is wrapped on three sides by a TaN barrier, which stops copper diffusing into the insulator, and a thin Co or Ru liner that helps the copper stick and fill. Together they are about 2 nm, and that stays the same as lines narrow, so the skin takes a bigger share of every smaller line.",
            "One line up close: the blue outer skin (TaN), a thin silver layer inside it (the liner) and the brown copper core. Halfway through, the skin glows amber.",
        )
        .detail(
            "The skin conducts poorly, so the copper core sets the resistance.",
            &[
                "Barrier + liner ~1-2 nm per side (CHIP_THIN_METAL section 2)",
                "A 16 nm line keeps a ~12 nm copper core",
                "Barrier on 3 sides; the SiCN cap closes the top",
            ],
        ),
    Beat::new("a via drops onto the line below", BEAT_MS)
        .note(
            "M2 runs across M1. Where the two must connect, a via fills a hole through the SiCN cap and lands on the M1 line beneath. Vias carry the same barrier and liner, so small vias are resistive too.",
            "A brown via column between the long M2 bar above and a cut M1 line below, passing through the thin white SiCN cap.",
        )
        .detail(
            "Via resistance climbs as vias shrink, for the same reason lines do.",
            &[
                "Via and line are filled together (dual damascene)",
                "SiCN cap: etch stop and copper seal",
            ],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("DAMASCENE: cut the insulator, inlay copper", BEAT_MS)
        .note(
            "Copper forms no volatile compounds, so a plasma can't etch it into lines. Instead trenches are etched in the low-k, lined, overfilled with copper and polished back. Every production copper level is built this way.",
            "A low-k block: open trenches under a dark hard mask, a blue lining, a copper blanket, then a flat polished top under a white cap.",
        )
        .detail(
            "The barrier must line three sides of every trench.",
            &["DAMASCENE: copper can't be dry-etched (CHIP_THIN_METAL section 3)"],
        ),
    Beat::new("SUBTRACTIVE: etch the metal itself", BEAT_MS)
        .note(
            "Ruthenium, molybdenum and tungsten do form volatile etch products, so a blanket of metal can be patterned directly, as aluminium wiring once was. The gaps are then filled with dielectric, and pinching the fill off early leaves air gaps.",
            "A teal ruthenium slab under dark hard-mask strips, then three free-standing teal lines, then grey fill with dark air-gap slots between the lines.",
        )
        .detail(
            "The subtractive route needs no liner and allows air gaps.",
            &[
                "Ru, Mo and W etch to volatile products (CHIP_THIN_METAL section 3)",
                "Allows air gaps and no liner (section 3)",
            ],
        ),
    Beat::new("same pitch, two routes", BEAT_MS)
        .note(
            "Side by side: inlaid copper with its barrier on three sides, and etched ruthenium lines with no liner and air gaps between. The etched line keeps all of its width as metal, which matters most at the smallest widths.",
            "Left block: brown copper lines in blue skins. Right block: teal ruthenium lines with dark air gaps between them.",
        )
        .detail(
            "Both routes print the same pitch; they differ in what fills the line and the space.",
            &["Ru lines need no barrier", "Air gaps cut line-to-line capacitance"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("the barrier eats a narrowing line", BEAT_MS)
        .note(
            "Three copper lines 40, 24 and 14 nm wide, each with the same 2 nm skin. At 40 nm copper fills about 88% of the line; at 14 nm only about 66%. Copper also gets more resistive in thin lines, because electrons scatter off its surfaces and grain boundaries.",
            "Three cut lines, big to small, in grey low-k: brown copper cores inside the same thin blue skin.",
        )
        .detail(
            "Less copper and worse copper: resistance rises much faster than the line shrinks.",
            &[
                "Copper share at 2 nm skin, 2:1 aspect: ~88%, ~80%, ~66% (geometry)",
                "Cu bulk ~1.7 uOhm-cm; electron mean free path ~39 nm",
            ],
        ),
    Beat::new("ruthenium: all metal, no barrier", BEAT_MS)
        .note(
            "Ruthenium doesn't diffuse into the insulator, so it needs no barrier, and its short electron mean free path means thin lines lose less to surface scattering. Its bulk resistivity is about four times copper's, but one analysis has it beating copper at about 17 nm width and below.",
            "The 14 nm copper line (brown core, blue skin) beside a 14 nm ruthenium line that is teal metal all the way across.",
        )
        .detail(
            "This is one analysis, not a production choice.",
            &[
                "Ru beats Cu at ~17 nm width and below, one analysis (CHIP_THIN_METAL section 4)",
                "Ru bulk ~7.1 vs Cu ~1.7 uOhm-cm (approximate)",
            ],
        ),
    Beat::new("molybdenum: a short mean free path", BEAT_MS)
        .note(
            "Molybdenum is the other candidate. Like ruthenium, its electrons travel only a short way between collisions, so narrow lines lose less to scattering, and imec has etched both directly at 32 nm pitch and below. Its electromigration data are less complete than copper's.",
            "Three 14 nm lines: brown copper in a blue skin, teal ruthenium and gold-grey molybdenum, the last two all metal.",
        )
        .detail(
            "Reliability data decide adoption as much as resistance does.",
            &[
                "imec direct-etched Ru and Mo at 32 nm pitch and below (CHIP_THIN_METAL section 4)",
                "Mo bulk ~5.3 uOhm-cm (approximate)",
            ],
        ),
    Beat::new("a thinner liner buys back copper", BEAT_MS)
        .note(
            "Until a new metal takes over, the fix is to thin the skin. A TaN plus cobalt skin of about 3 nm leaves a 14 nm line about half copper; a RuCo liner of about 2 nm leaves about two thirds. Applied Materials says its RuCo liner cuts line resistance by up to 25%. Cobalt costs yield and resistance at 3 nm and below.",
            "Two 14 nm copper lines: on the left a thick blue-and-silver skin round a narrow brown core, on the right a thin skin (teal liner) round a wider core.",
        )
        .detail(
            "The 25% figure is a company claim, not an independent measurement.",
            &[
                "RuCo liner ~2 nm, line R down up to 25% (Applied claim, section 4)",
                "As drawn: 3 nm skin ~50% Cu, 2 nm skin ~66% Cu (geometry)",
            ],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("a via placed by lithography overlay", BEAT_MS)
        .note(
            "A via is printed in its own lithography step and has to line up with the line below it. The overlay error must stay within about a quarter of the via pitch, which at these pitches is only a few nanometres.",
            "Three cut lines in grey low-k, a long copper line across the top, and a brown via between them landing on the middle line, with a green glow where it lands.",
        )
        .detail(
            "Overlay is the alignment between two separately printed layers.",
            &[
                "Overlay budget ~1/4 of the via pitch (CHIP_THIN_METAL section 5)",
                "At a 28 nm pitch that is ~7 nm",
            ],
        ),
    Beat::new("shifted: a short to the neighbour", BEAT_MS)
        .note(
            "Shift the same via by half a space and its foot touches the next line over. That is a short circuit; if it only just misses, the thin sliver of insulator left can break down early. Adding masks to prevent it raises cost.",
            "The via moved to the right, with a red glow where its foot meets the neighbouring line.",
        )
        .detail(
            "Edge placement error shorts or opens lines at this pitch.",
            &[
                "Shifted via: short or wall hit (CHIP_THIN_METAL section 5)",
                "The tightest via pitches are below EUV resolution (section 5)",
            ],
        ),
    Beat::new("SELF-ALIGNED VIA: hemmed in", BEAT_MS)
        .note(
            "In a self-aligned scheme, dielectric is grown selectively on top of the neighbouring lines, or a metal-selective etch is used. The via hole can then be printed oversize and off-centre, and it still reaches only its own line.",
            "White dielectric blocks raised on the two neighbouring lines; the via, still shifted, narrows between them and lands only on the middle line (green glow).",
        )
        .detail(
            "The line below, not the overlay, sets where the via lands.",
            &[
                "Hole bounded by the line below (CHIP_THIN_METAL section 5)",
                "Selective dielectric or metal-selective etch (section 5)",
            ],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("a standard cell from above", BEAT_MS)
        .note(
            "Logic is built from standard cells: fixed-height tiles with power rails along the top and bottom and gates running between them. A cell's inputs and output are short M1 pins inside it, and the router has to reach them from the M2 tracks above.",
            "Seen from above: gold VDD and VSS rails, dark red gates, three copper M1 pins (A, B and Y), and faint cyan M2 tracks crossing the cell.",
        )
        .detail(
            "Cell height is counted in M2 tracks.",
            &[
                "PIN ACCESS on M1 and M2 (CHIP_THIN_METAL section 6)",
                "Libraries require a minimum of reachable tracks per pin (section 6)",
            ],
        ),
    Beat::new("fewer tracks, fewer ways in", BEAT_MS)
        .note(
            "A pin can only be reached where an M2 track crosses it. Shrinking cells from 7.5 to 6 to 5 tracks leaves each pin fewer crossings, and if another net already uses a track, that access point is lost. Blocked pins can make a cell unroutable.",
            "Green dots where tracks cross each pin; one track now carries an orange wire from another net, and the dots on it are red.",
        )
        .detail(
            "Congestion grows as cells shrink.",
            &[
                "7.5 to 6 to 5 tracks raises pin density (CHIP_THIN_METAL section 6)",
                "Blockages can leave pins unreachable (section 6)",
            ],
        ),
    Beat::new("the router joins the pins", BEAT_MS)
        .note(
            "Place-and-route software picks free tracks, drops vias onto the pins and joins them. Here one M2 wire ties pins A and B together and another leaves from pin Y. Some M2 pins are still placed by hand.",
            "Two glowing cyan M2 wires, one between pins A and B and one from pin Y to the cell edge, with vias down onto the pins.",
        )
        .detail(
            "Pin placement and routing are planned together.",
            &[
                "Synopsys (SNPS) and Cadence (CDNS) place-and-route (CHIP_THIN_METAL section 6)",
                "Some M2 pins are hand-placed (section 6)",
            ],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("EUV 0.33 NA: ~26 nm pitch in one pass", BEAT_MS)
        .note(
            "An EUV scanner images the reticle onto resist with 13.5 nm light. With today's 0.33 numerical-aperture optics, the finest lines it prints reliably in one exposure are at about 26 nm pitch. Tighter levels need two exposures or a self-aligned spacer scheme.",
            "Pink resist lines on a dark hard mask and silicon, under a violet column of EUV light from the grey reticle above.",
        )
        .detail(
            "Pitch is set by lithography; line width then follows.",
            &[
                "0.33 NA: ~26 nm pitch, 13 nm half-pitch (CHIP_THIN_METAL section 7)",
                "EUV wavelength 13.5 nm",
            ],
        ),
    Beat::new("High-NA 0.55: ~16 nm reported", BEAT_MS)
        .note(
            "High-NA EUV uses larger 0.55 NA optics, which resolve finer lines: about 16 nm pitch in one exposure has been reported. The trade-off is an exposure field half the size, so the largest dies need two fields stitched together.",
            "A narrower violet beam over a tighter array of thin pink resist lines.",
        )
        .detail(
            "A reported figure, not one measured on a shipping node.",
            &[
                "High-NA ~16 nm pitch reported (CHIP_THIN_METAL section 7)",
                "Field 26 x 16.5 mm, half of 26 x 33 mm",
            ],
        ),
    Beat::new("published pitches", BEAT_MS)
        .note(
            "What has been published: TSMC's N3E has a 23 nm minimum metal pitch, and imec has printed 28 nm pitch ruthenium lines in one 0.33 NA exposure. Pitches for TSMC N2 and Intel 14A were not found in public sources.",
            "Two line arrays at their published pitches: copper lines at 23 nm and teal ruthenium lines at 28 nm.",
        )
        .detail(
            "Public pitch figures are scarce.",
            &[
                "TSMC N3E minimum metal pitch 23 nm (IEDM 2022 via WikiChip)",
                "imec 28 nm pitch Ru, single 0.33 NA exposure (section 7)",
            ],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("fabs set the pitch and the metal", BEAT_MS)
        .note(
            "TSMC, Intel and Samsung decide the pitch of each level and what it is made of. Those choices fix how dense the logic can be and how fast its wires are.",
            "The M1-M4 stack, with the fabs tagged on M2 and M3.",
        )
        .detail(
            "Pitch and metal are the fabs' decisions.",
            &["TSMC (TSM), Intel (INTC) and Samsung (CHIP_THIN_METAL section 8)"],
        ),
    Beat::new("the tool makers, step by step", BEAT_MS)
        .note(
            "Applied Materials sells the deposition tools for the barrier, liner, seed and ruthenium. Lam Research and Tokyo Electron supply etch and copper plating. ASML is the only maker of the EUV scanners that print the lines.",
            "The stack with tags on the blue barrier of an M1 line, on an M3 line and on top of M4.",
        )
        .detail(
            "A few suppliers cover each step.",
            &[
                "AMAT, LRCX, 8035.T and ASML (CHIP_THIN_METAL section 8)",
                "ASML: sole supplier of EUV scanners",
            ],
        ),
    Beat::new("designers and routers", BEAT_MS)
        .note(
            "NVIDIA, AMD and Arm design cells that have to route at these pitches, and Synopsys and Cadence write the routers that connect them. Pin access problems show up here first.",
            "The standard cell from above with a cyan M2 route between two pins, tagged with the designers and EDA firms.",
        )
        .detail(
            "Designers and routers have to meet the fabs' pitches.",
            &["NVDA, AMD, ARM, SNPS and CDNS (CHIP_THIN_METAL section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("ruthenium and molybdenum aren't mature", BEAT_MS)
        .note(
            "Etched ruthenium and molybdenum lines are promising, but their etch, CMP and cost are still being worked out. Defects such as residue or broken lines cost yield until the process matures.",
            "Teal ruthenium lines in grey fill with dark air gaps; two red dots mark defects on the lines.",
        )
        .detail(
            "Adoption depends on etch and CMP maturity.",
            &["Ru and Mo cost, CMP and etch maturity (CHIP_THIN_METAL section 9)"],
        ),
    Beat::new("RC: thin wires set the speed", BEAT_MS)
        .note(
            "A wire's delay grows with its resistance times its capacitance. Halving a line's width and height raises its resistance per length about four times while its capacitance per length barely falls, so a signal crosses a thin wire far more slowly than a thick one. At these levels wire delay now outweighs gate delay.",
            "Two copper wires seen lengthwise: a thin one below where cyan pulses crawl, and a thick one above where they race across.",
        )
        .detail(
            "The wires, not the transistors, set the speed here.",
            &[
                "RC delay of thin wires dominates (CHIP_THIN_METAL section 9)",
                "R per length ~ 1 / (width x height)",
            ],
        ),
    Beat::new("upper levels thicken; next pitches unknown", BEAT_MS)
        .note(
            "That is why each level up is a little wider and taller, and long routes climb to the thick metal higher in the stack. The metal pitches for TSMC N2 and Intel 14A were not found in public sources.",
            "The stack, with the thicker M4 bars on top and the thin M1 lines at the bottom.",
        )
        .detail(
            "Numbers without a source are left out.",
            &[
                "Higher levels thicken because RC falls with cross-section (section 9)",
                "N2 and 14A metal pitches not public (section 9)",
            ],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-4", BEAT_MS)
        .note(
            "Semiengineering on ruthenium interconnects and the end of copper; semiengineering on ruthenium liners; Applied Materials on chip wiring; a US patent on self-aligned vias.",
            "The M1-M4 cut-away, turning slowly.",
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
            "The M1-M4 cut-away, turning slowly.",
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
            "The M1-M4 cut-away, turning slowly.",
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
