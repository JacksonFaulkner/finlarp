// CHIP tab, TOP METAL: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on this part (tools/pbr3d/blender/chip_top_metal.py): the M10-M14
// power grid, clock trunk and bump pads, then the bumps above them. Six beats, one loop.
// Zoom-ins a-e (3 beats each) and sections 1-10 are the same chip, closer or whole, from the same script.
//
// Sources: CHIP_TOP_METAL.txt sections 2-4, CHIP_TOP_METAL.details.txt (POWER GRID, CLOCK TRUNK,
// LONG WIRES, IR DROP, C4 BUMP), with the citations kept in each beat's `detail`.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the thick top: M10-M14, lit", BEAT_MS)
        .note(
            "The top three levels, M10-M14, are the thickest and widest copper on the chip. They carry power and clock across the whole die, and the package bumps sit on top of them.",
            "the three top levels lit in amber across the top of the chip, the row of bumps above them, and the thin wiring and transistors below",
        )
        .detail(
            "Wires get wider going up, because the resistance of a wire falls with its cross-section.",
            &[
                "M10-M14 thick, wide copper for the power grid and clock trunk (CHIP_TOP_METAL.txt, section 2)",
                "Long cross-block wires use M10-M14-class layers (LONG WIRES, textbook)",
            ],
        ),
    Beat::new("power comes in through a bump", BEAT_MS)
        .note(
            "VDD arrives from the package through a bump, then down through a bond pad onto the thick top rail. Bumps alternate power, ground and signal across the die, so power enters right above the logic that needs it.",
            "the VDD bump lit, amber dots falling from it through the square pad onto the top rail, and the rail glowing where the current lands",
        )
        .detail(
            "Flip-chip bumps spread power over the whole die, not only at the edge.",
            &[
                "Bumps alternate power, ground and signal across the whole die (C4 BUMP, textbook)",
                "C4 bumps at about 150 um pitch, one patent example (image-ppubs.uspto.gov, patent 8896118)",
            ],
        ),
    Beat::new("the grid spreads it both ways", BEAT_MS)
        .note(
            "The Vdd stripes on the thick levels run across the chip and feed current out to every cell. Current spreads along the rail in both directions from where it enters.",
            "amber dots running along the full-width top rail away from the bump, toward both ends of the chip, with the rails' thickness standing out against the thin wiring below",
        )
        .detail(
            "Thick, wide rails keep the drop along the grid small, so the cells see close to the full supply.",
            &[
                "A modern CPU or GPU pulls tens to hundreds of amps at about 1 V or less (textbook)",
                "Vdd and Vss stripes alternate and meet bumps from above (POWER GRID, patent 11681854)",
                "Every stage drops V = I x R; designers tolerate roughly 10% total droop (IR DROP, secondary)",
            ],
        ),
    Beat::new("the clock trunk fans out", BEAT_MS)
        .note(
            "The clock tree's top trunk sits on the middle top level and fans out from one point toward both sides of the chip. Local trees below it drive the flip-flops.",
            "a green clock source dot in the gap of the middle top level, and green dots splitting left and right along the lit green band",
        )
        .detail(
            "The clock must reach millions of flip-flops at nearly the same time, so the trunk uses low-resistance upper metal.",
            &[
                "The top-level trunk is an H-tree or mesh on low-resistance upper metal (CLOCK TRUNK, textbook)",
                "Inherent H-tree skew from process variation about 150-200 ps, one patent-derived source (CLOCK TRUNK sources: semiconductor-digest.com/?p=6892, patent US6037822)",
            ],
        ),
    Beat::new("thick wire, low resistance", BEAT_MS)
        .note(
            "Both wires are the same length. R = rho x L / (W x T): the thin wire's small cross-section gives high resistance, and the top rail's wide, tall cross-section gives low resistance. The picture is schematic, not to scale in its proportions.",
            "a short thin copper stub below and a taller, thicker top rail above, both the same length, amber dots moving through each, and the formula tagged between them",
        )
        .detail(
            "Resistance falls as the cross-section grows, so the top levels carry current with the least drop.",
            &[
                "R = rho L / (W T), resistance from resistivity, length, width and thickness (textbook)",
                "Wide, thick upper-layer wires cut R, so buses cross a large die with repeaters far apart (LONG WIRES, textbook)",
                "Thick top metal is treated as nearly zero resistance in simplified patent calculations (IR DROP, secondary)",
            ],
        ),
    Beat::new("back out: the return to the VSS bump", BEAT_MS)
        .note(
            "VSS climbs the top levels back up to its bump, and the whole chip is in view again. Power goes in through one bump, spreads over the top rails and returns through another.",
            "blue-white dots rising from the top rail through the VSS pad to the lit VSS bump, with the whole chip in view and the top tier lit",
        )
        .detail(
            "The loop closes at the package: power in on one bump, return on another.",
            &[
                "Current flows from the regulator through package planes and the bump array into the top metal (CHIP_TOP_METAL.txt, section 4; textbook)",
                "Bumps alternate power, ground and signal across the whole die (C4 BUMP, textbook)",
            ],
        ),
];

const ZA_BEATS: &[Beat] = &[
    Beat::new("trench, barrier and seed", BEAT_MS)
        .note(
            "A trench is etched into the dielectric, then lined with a barrier and a thin copper seed. The barrier keeps copper from reaching the transistors.",
            "a pale barrier layer over the middle top level, the top rails lit amber round it, and the trench label tagged above",
        )
        .detail(
            "Copper diffuses fast into silicon and oxide, so each trench gets a conformal liner before the fill.",
            &[
                "Copper cannot be plasma-etched into lines, so the trench is etched into the dielectric (TRENCH ETCH, UMD damascene slides)",
                "Barrier typically Ta, TaN, TiN or TiW, about 2 to 10 nm (BARRIER + SEED, damascene explainers)",
            ],
        ),
    Beat::new("copper plate, then CMP", BEAT_MS)
        .note(
            "Copper is electroplated bottom-up into the trench, then CMP polishes the excess flat so only the metal in the trench remains.",
            "the trench glowing amber as the copper fills it, the surface level with the rail afterwards",
        )
        .detail(
            "Each metal level needs its own CMP, so the polishing steps add up with stack height.",
            &[
                "Electroplated superfill from a copper sulfate bath with organic additives (CU PLATE, textbook)",
                "Copper tolerates roughly 5x the current density of aluminium (CU PLATE, Synopsys glossary)",
                "Each metal level needs its own CMP (CMP, textbook)",
            ],
        ),
    Beat::new("passivation, the bond pad and the bump", BEAT_MS)
        .note(
            "Bond pads sit over the last copper level, under a passivation stack with openings over them. A solder bump sits on each pad and joins the chip to the package.",
            "the blue passivation over the pads, a pad under it, and the VDD bump glowing amber above",
        )
        .detail(
            "Passivation blocks moisture and ions, and the bump carries power into the package.",
            &[
                "Pads usually aluminium or aluminium-copper, passivation of oxide, nitride and polyimide with openings over the pads (PAD + PASSIV, patents 11189538 and 12040293)",
                "C4 bumps at about 150 um pitch, one patent example (BUMP, patent 8896118)",
            ],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("power grid: Vdd stripes on the thick levels", BEAT_MS)
        .note(
            "Vdd and Vss stripes on the thick levels feed current from the bumps out to every cell. Current spreads along the rail both ways from where it enters.",
            "the top tier lit, amber dots running along the full-width rail away from the VDD bump toward both ends",
        )
        .detail(
            "Thick, wide rails keep the drop along the grid small, so the cells see close to the full supply.",
            &[
                "A modern CPU or GPU pulls tens to hundreds of amps at about 1 V or less (textbook)",
                "Power is carried on thick upper layers; the drop is bounded by top-layer thickness (POWER GRID, patent 11681854)",
            ],
        ),
    Beat::new("clock trunk and long wires", BEAT_MS)
        .note(
            "The clock trunk sits on the middle top level and fans out from one point. Long buses cross the die on the same low-resistance upper metal.",
            "a green clock source in the gap of the middle level, green dots splitting left and right, and purple dots running along the top rail",
        )
        .detail(
            "The clock must reach millions of flip-flops at nearly the same time, so the trunk uses low-resistance upper metal.",
            &[
                "H-tree or mesh on low-resistance upper metal, with local trees below (CLOCK TRUNK, textbook)",
                "Inherent H-tree skew from process variation about 150-200 ps (CLOCK TRUNK, semiconductor-digest.com/?p=6892)",
                "Wide, thick upper-layer wires cut R, so repeaters sit far apart (LONG WIRES, textbook)",
            ],
        ),
    Beat::new("RDL and underfill", BEAT_MS)
        .note(
            "A redistribution layer re-routes a pad to a new bump position. Epoxy underfill fills the gap round the bumps.",
            "a purple trace leaving the VDD pad, and a translucent band of underfill between the bumps, with the VDD and VSS bumps lit",
        )
        .detail(
            "The RDL moves pads to the bump pattern; underfill keeps the solder joints from cracking in thermal cycling.",
            &[
                "RDL re-routes pads to a coarser bump pitch, copper RDL by damascene (RDL, patent 11798904)",
                "Underfill improved flip-chip fatigue life by more than an order of magnitude (UNDERFILL, Semiconductor History Museum of Japan)",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("from the bump, down the stack", BEAT_MS)
        .note(
            "Current enters through a bump, runs down the VDD via column through the stack, and reaches the PMOS source.",
            "amber dots falling from the VDD bump down the via column to the transistor at the bottom",
        )
        .detail(
            "Every stage between the bump and the transistor adds resistance, so the path is long.",
            &[
                "Current runs from the VRM through package planes and the bump array, then M14 down to the cell (CHIP_TOP_METAL.txt, section 4)",
                "0.9 V is an illustrative supply (CHIP_TOP_METAL.txt, section 4)",
            ],
        ),
    Beat::new("IR drop along the top rail", BEAT_MS)
        .note(
            "Each stage drops V = I x R. The top rail heats where the current flows, and the voltage the cells see falls with distance from the bump.",
            "the rail lit orange-red from the bump outward, and orange dots slowing along it",
        )
        .detail(
            "The die sees what is left after the drop, so the top levels are kept low in resistance.",
            &[
                "Every stage drops V = I x R; designers tolerate roughly 10% total droop (IR DROP, secondary)",
                "Top thick layers treated as nearly zero resistance in simplified patent calculations (IR DROP, patent 11681854)",
            ],
        ),
    Beat::new("electromigration in the via", BEAT_MS)
        .note(
            "Too much current through a thin via pushes copper atoms along, and over years the via can open up.",
            "the VDD via lit orange-red and hot dots climbing it",
        )
        .detail(
            "Copper tolerates more current than aluminium, but thin wires and vias are the weak points.",
            &[
                "Copper about 5x the current density of aluminium (EM LIMIT, Synopsys glossary)",
                "Damascene copper about 1-3e6 A/cm2 (EM LIMIT, secondary; rfessentials.com)",
            ],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("C4 bumps, about 150 um", BEAT_MS)
        .note(
            "C4 solder bumps join the die to the package at about 150 um pitch, alternating power, ground and I/O.",
            "the row of bumps across the top, the VDD and VSS bumps lit amber",
        )
        .detail(
            "Bumps spread over the whole die, so power enters above the logic that needs it.",
            &[
                "C4 bumps at about 150 um pitch, one patent example (C4 BUMP, patent 8896118)",
                "Bumps alternate power, ground and signal across the die (C4 BUMP, textbook)",
            ],
        ),
    Beat::new("microbumps, about 40 um", BEAT_MS)
        .note(
            "Microbumps are solder-capped copper pillars at about 40 um pitch, used to stack chiplets and dies.",
            "a close row of fine pillars standing on the top rail",
        )
        .detail(
            "Finer pitch means more connections per mm2, but solder can bridge at fine pitch.",
            &[
                "40 um pitch = 20-25 um bumps with 15 um spacing (MICROBUMP, semiengineering.com/scaling-bump-pitches-in-advanced-packaging)",
                "Solder bridging at fine pitch (MICROBUMP, Onto Innovation yearbook)",
            ],
        ),
    Beat::new("hybrid bond, copper to copper", BEAT_MS)
        .note(
            "Hybrid bonding joins flat copper pads directly, with no solder, at 10 um pitch and below.",
            "a row of flat copper pads lying on the top rail, with nothing between them",
        )
        .detail(
            "Smaller pitch means more connections per mm2; the surface must be flat and clean.",
            &[
                "Direct Cu-Cu and oxide-oxide bonding, 10 um pitch and below (HYBRID BOND, semiengineering.com/hybrid-bonding-basics-what-is-hybrid-bonding)",
                "Copper recess must be nanometers (HYBRID BOND, textbook)",
            ],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("front-side power: a shared stack", BEAT_MS)
        .note(
            "Today power and signals share the front stack, M0 to M14, so the power network competes with the signal wires for space.",
            "power dots falling down the VDD column and signal dots crossing a medium level, on the same stack",
        )
        .detail(
            "Shared wiring causes congestion and droop; moving power off the front is the fix.",
            &[
                "Today power and signals share the front stack (BSPDN, Intel PowerVia, secondary)",
                "Congestion and droop (CHIP_TOP_METAL.details.txt, BSPDN)",
            ],
        ),
    Beat::new("backside power: rails under the silicon", BEAT_MS)
        .note(
            "Backside metals (BM0-BM5) sit under the thinned silicon. Nano-TSVs carry power up to the transistors.",
            "copper rails under the chip, the TSVs rising through the silicon, and amber dots climbing them",
        )
        .detail(
            "Power on the back leaves the front free for signals.",
            &[
                "Intel PowerVia on 18A routes power through backside metals to nano-TSVs (BSPDN, intel.com 18A)",
                "TSMC A16 Super Power Rail contacts source and drain directly (BSPDN, tomshardware.com)",
            ],
        ),
    Beat::new("the gains: signals on the front", BEAT_MS)
        .note(
            "With power behind, the front carries signals only, and droop falls.",
            "cyan signal dots on the front stack, and amber power dots coming up from the rails",
        )
        .detail(
            "The test chip shows the droop gain; the other figures are the vendors' own claims.",
            &[
                "PowerVia test chip: more than 30% lower droop, more than 6% performance (BSPDN, Intel 4 test chip)",
                "Intel 2026 18A brief claims about 10x lower worst-case dynamic droop (BSPDN, vendor claim)",
            ],
        ),
];

const S1_BEATS: &[Beat] = &[
    Beat::new("the top tier: M10-M14 copper", BEAT_MS)
        .note(
            "The top three levels, M10-M14, are the thick, wide copper of the stack. They are built with the same damascene loop as the thin levels, only bigger.",
            "the top tier lit amber across the whole chip, the transistors and thin wiring below",
        )
        .detail(
            "Wires get wider going up, because resistance falls with cross-section.",
            &[
                "The top levels use the same copper damascene loop, only wider and taller (CHIP_TOP_METAL.txt, section 1)",
                "M10-M14 thick, wide copper with big vias between (CHIP_TOP_METAL.txt, section 2)",
            ],
        ),
    Beat::new("bumps and pads on the top", BEAT_MS)
        .note(
            "Bond pads sit on the top metal, and a C4 bump sits on each pad. The bumps carry power and I/O from the package into the top metal.",
            "the row of bumps lit across the top, with the camera in on the top of the chip",
        )
        .detail(
            "The bumps are the link between the chip and the package.",
            &[
                "C4 bumps at about 150 um pitch, alternating power, ground and I/O (CHIP_TOP_METAL.txt, section 5)",
                "Passivation with openings over the pads (PAD + PASSIV, patents 11189538 and 12040293)",
            ],
        ),
    Beat::new("finished: ready for the package", BEAT_MS)
        .note(
            "The finished top of the stack: the bumps are what the package sees.",
            "the whole chip, the bumps above the top tier",
        )
        .detail(
            "Pads and bumps are the last steps before packaging.",
            &["PAD + PASSIV and BUMP, the last steps before packaging (CHIP_TOP_METAL.txt, section 1)"],
        ),
];

const S2_BEATS: &[Beat] = &[
    Beat::new("transistors, contacts and M1-M4", BEAT_MS)
        .note(
            "Transistors, tungsten contacts and M1-M4 thin copper for cell wiring sit at the bottom of the stack.",
            "the thin tier lit cyan, the transistors below it",
        )
        .detail(
            "Thin wires give density for the cells.",
            &["M1-M4 thin copper for cell wiring (CHIP_TOP_METAL.txt, section 2)"],
        ),
    Beat::new("M5-M9 medium copper", BEAT_MS)
        .note(
            "Medium copper, M5-M9, carries block signals between the cells.",
            "the medium tier lit violet in the middle of the stack",
        )
        .detail(
            "Wires get fatter going up: thin for density, thick for current and reach.",
            &["M5-M9 medium copper for block signals (CHIP_TOP_METAL.txt, section 2)"],
        ),
    Beat::new("M10-M14 thick copper and bumps", BEAT_MS)
        .note(
            "M10-M14 are the fattest wires, below the pads and the C4 bumps.",
            "the top tier lit amber and the bumps lit above it",
        )
        .detail(
            "The fattest wires carry power and clock with the least resistance.",
            &["M10-M14 thick, wide copper for the power grid and clock trunk (CHIP_TOP_METAL.txt, section 2)"],
        ),
];

const S3_BEATS: &[Beat] = &[
    Beat::new("POWER GRID", BEAT_MS)
        .note(
            "Vdd and Vss stripes on the thick levels feed every cell. Current spreads along the top rails from the bump.",
            "amber dots along the full-width top rails, away from the VDD bump",
        )
        .detail(
            "Wide, thick rails keep the grid's resistance low.",
            &["Power on thick upper layers, drop bounded by top-layer thickness (POWER GRID, patent 11681854)"],
        ),
    Beat::new("CLOCK TRUNK and LONG WIRES", BEAT_MS)
        .note(
            "The clock's low-skew trunk fans out from one point, and buses cross blocks on the same upper metal.",
            "a green clock source in the middle top level, green dots splitting left and right, purple dots along the top rail",
        )
        .detail(
            "Reach and skew both need low resistance.",
            &[
                "H-tree or mesh on low-resistance upper metal (CLOCK TRUNK, textbook)",
                "Wide, thick upper-layer wires cut R (LONG WIRES, textbook)",
            ],
        ),
    Beat::new("RDL and UNDERFILL", BEAT_MS)
        .note(
            "A redistribution layer re-routes pads to bumps; underfill epoxy spreads the stress.",
            "a purple trace leaving the VDD pad and the underfill band round the bumps",
        )
        .detail(
            "The package side: pad re-routing and stress relief.",
            &[
                "RDL re-routes pads to the bump pattern (RDL, patent 11798904)",
                "Underfill improved flip-chip fatigue life by more than 10x (UNDERFILL, Semiconductor History Museum of Japan)",
            ],
        ),
];

const S4_BEATS: &[Beat] = &[
    Beat::new("from the VRM to the transistor", BEAT_MS)
        .note(
            "Current enters through a bump, runs down the VDD via column through the stack, and reaches the transistor.",
            "amber dots falling from the VDD bump through the via column to the transistor",
        )
        .detail(
            "Each stage between the regulator and the transistor adds resistance.",
            &["Current runs from the VRM through package planes and the bump array, then down M14 to the cell (CHIP_TOP_METAL.txt, section 4)"],
        ),
    Beat::new("IR DROP at every stage", BEAT_MS)
        .note(
            "V = I x R drops the voltage at each stage. The top rail heats where the current flows.",
            "the top rail lit orange-red from the bump outward, and orange dots slowing along it",
        )
        .detail(
            "The die sees what is left after the drop; designers tolerate roughly 10%.",
            &["Every stage drops V = I x R; roughly 10% total droop tolerated (IR DROP, secondary)"],
        ),
    Beat::new("EM LIMIT", BEAT_MS)
        .note(
            "Copper carries a high current density before electromigration bites. The VDD via is where the current is densest.",
            "the VDD via lit orange-red and hot dots climbing it",
        )
        .detail(
            "Wider wires and redundant vias are the fix.",
            &["Copper about 5x the current density of aluminium (EM LIMIT, Synopsys glossary)"],
        ),
];

const S5_BEATS: &[Beat] = &[
    Beat::new("C4 BUMP: about 150 um", BEAT_MS)
        .note(
            "Solder bumps connect the chip to the package substrate, at about 150 um pitch.",
            "the row of bumps across the top of the chip, the VDD and VSS bumps lit",
        )
        .detail(
            "Bumps spread power over the die.",
            &["C4 bumps at about 150 um pitch, one patent example (C4 BUMP, patent 8896118)"],
        ),
    Beat::new("MICROBUMP: about 40 um", BEAT_MS)
        .note(
            "Solder-capped copper pillars join chiplets to an interposer, at about 40 um pitch.",
            "a close row of fine pillars on the top rail",
        )
        .detail(
            "20-25 um bumps with 15 um spacing; a wall is expected near 10 um.",
            &["40 um pitch = 20-25 um bump + 15 um space (MICROBUMP, semiengineering.com/scaling-bump-pitches-in-advanced-packaging)"],
        ),
    Beat::new("HYBRID BOND: 10 um and below", BEAT_MS)
        .note(
            "Direct copper-to-copper and oxide-to-oxide bonds join the dies with no solder.",
            "a row of flat copper pads lying on the top rail",
        )
        .detail(
            "More connections per mm2 at smaller pitch.",
            &["Direct Cu-Cu, 10 um pitch and below (HYBRID BOND, semiengineering.com/hybrid-bonding-basics-what-is-hybrid-bonding)"],
        ),
];

const S6_BEATS: &[Beat] = &[
    Beat::new("front-side power: a shared stack", BEAT_MS)
        .note(
            "Today power and signals share the front stack, M0 to M14.",
            "power dots down the VDD column and signal dots across a medium level",
        )
        .detail(
            "Congestion and droop come from sharing the stack.",
            &["Today power and signals share the front stack (BSPDN, secondary)"],
        ),
    Beat::new("BSPDN: power from behind", BEAT_MS)
        .note(
            "Backside metals (BM0-BM5) sit under the thinned silicon, with nano-TSVs up to the devices.",
            "copper rails under the chip and TSVs rising through the silicon, with amber dots climbing them",
        )
        .detail(
            "Intel PowerVia and TSMC A16 both move power to the back.",
            &["Intel PowerVia (18A) and TSMC A16 Super Power Rail (BSPDN, intel.com and tomshardware.com)"],
        ),
    Beat::new("the gains", BEAT_MS)
        .note(
            "With power on the back the front carries signals only, and droop falls.",
            "cyan signal dots on the front and amber power dots from the rails",
        )
        .detail(
            "The PowerVia test chip shows more than 30% lower droop.",
            &["PowerVia test chip: more than 30% lower droop, more than 6% performance (BSPDN, Intel 4 test chip)"],
        ),
];

const S7_BEATS: &[Beat] = &[
    Beat::new("pitches: C4 to hybrid", BEAT_MS)
        .note(
            "The bump pitches step down: C4 about 150 um, microbump 40 um, hybrid 10 um and below.",
            "the bump row with the three pitches tagged along the top",
        )
        .detail(
            "Smaller pitch means more connections per mm2.",
            &["C4 ~150 um, microbump 40 um, hybrid bond 10 um and below (patents, SemiEngineering)"],
        ),
    Beat::new("Intel stacks", BEAT_MS)
        .note(
            "Intel 4 has a 30 nm M0 pitch and 16 metal layers. The tiers come apart here to show the stack.",
            "the tiers sliding apart, the top tier and the bumps lifted above the rest",
        )
        .detail(
            "The layer count grows the etch and CMP steps.",
            &["Intel 4: M0 30 nm, 16 metal layers (WikiChip); PowerVia moves M0 to 36 nm (SemiAnalysis)"],
        ),
    Beat::new("money", BEAT_MS)
        .note(
            "Revenue: Intel 2025 $52.9B, TSMC about US$122B in 2025. Synopsys FY2025 $7.1B and Cadence 2025 $5.3B are the tool makers.",
            "the stack back together, with the company labels tagged round it",
        )
        .detail(
            "Different scales: foundries against tool vendors.",
            &["Intel FY2025 $52.9B, Synopsys FY2025 $7.1B, Cadence 2025 $5.3B, TSMC about US$122B (revenue, sources in section 10)"],
        ),
];

const S8_BEATS: &[Beat] = &[
    Beat::new("TSMC and Intel: backside power", BEAT_MS)
        .note(
            "TSMC's A16 has backside power due late 2026; Intel ships PowerVia on 18A in Panther Lake.",
            "the backside rails under the chip, lit",
        )
        .detail(
            "TSMC (TSM) and Intel (INTC) are the two fabs.",
            &["TSMC A16 late 2026; Intel PowerVia on 18A in Panther Lake (per teardown)"],
        ),
    Beat::new("NVIDIA, AMD, Arm", BEAT_MS)
        .note(
            "Large GPUs and CPUs draw huge supply currents, with microbump 2.5D and 3D parts. Arm core IP has to fit the foundry's grid.",
            "a thick stream of amber dots coming up the VDD column",
        )
        .detail(
            "The designers set the current the grid must carry.",
            &["NVIDIA, AMD and Arm build the big supply-current parts (textbook, names not sourced this run)"],
        ),
    Beat::new("Synopsys, Cadence: sign-off", BEAT_MS)
        .note(
            "Synopsys and Cadence sell the IR-drop and electromigration sign-off tools that check the top metal.",
            "the top rail lit orange-red for the droop check",
        )
        .detail(
            "Sign-off checks the grid against droop and EM limits.",
            &["Synopsys FY2025 $7.1B, Cadence 2025 $5.3B; sign-off tools (textbook)"],
        ),
];

const S9_BEATS: &[Beat] = &[
    Beat::new("IR drop and electromigration", BEAT_MS)
        .note(
            "Droop runs from the grid to the cell rail, and EM slowly opens thin wires and vias.",
            "the top rail lit orange-red, dots slowing along it",
        )
        .detail(
            "Wider grids and redundant vias are the fixes.",
            &["Every stage drops V = I x R (IR DROP, secondary); EM in thin wires and vias (EM LIMIT, Synopsys glossary)"],
        ),
    Beat::new("voids and bridging", BEAT_MS)
        .note(
            "Voids form in copper vias and barriers during damascene; at fine bump pitch the solder can bridge.",
            "the VDD via lit orange-red with hot dots climbing it",
        )
        .detail(
            "Process control and copper pillars are the fixes.",
            &["Via and barrier voids in damascene; bridging at fine pitch (CHIP_TOP_METAL.txt, section 9; MICROBUMP, Onto Innovation)"],
        ),
    Beat::new("thermal-cycle fatigue", BEAT_MS)
        .note(
            "The C4 joints crack when the die and the substrate expand by different amounts. Underfill gives over ten times the life.",
            "the bumps lit across the top of the chip",
        )
        .detail(
            "Underfill is the standard fix.",
            &["Underfill improved flip-chip fatigue life by more than an order of magnitude (UNDERFILL, Semiconductor History Museum of Japan)"],
        ),
];

const S10_BEATS: &[Beat] = &[
    Beat::new("sources: backside power, Intel and TSMC", BEAT_MS)
        .note(
            "The backside power and TSMC A16 claims in sections 6 and 8 come from these pages.",
            "the whole chip, the top tier lit",
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
            "The bump pitch and power-delivery claims in sections 4 and 5 come from these patents and articles.",
            "the backside rails lit under the chip",
        )
        .detail(
            "Patents and SemiEngineering.",
            &[
                "[3] image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8896118",
                "[4] semiengineering.com/scaling-bump-pitches-in-advanced-packaging; semiengineering.com/bumps-vs-hybrid-bonding-for-advanced-packaging",
                "[5] semiengineering.com/current-problems-grow-for-power-delivery/; patsnap.com/resources/blog/articles/back-side-power-delivery-networks-cut-ir-drop-by-10/",
            ],
        ),
    Beat::new("sources: stacks, EM, bonding, revenue", BEAT_MS)
        .note(
            "The Intel stack, the electromigration limits, the Intel 4 pitch and the TSMC stage come from these pages.",
            "the bumps lit across the top, with the tiers in view",
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
            "The revenue figures, the C4 history and the EDA tool names come from these filings and references.",
            "the whole chip, slowly pulled back",
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
