// Visuals for the PACKAGE, FINAL TEST and SHIP pages (generated from
// scratch data; edit art/spots here). See diagrams_vis.rs for the template.

#[allow(unused_imports)]
use super::diagrams_vis::{Spot, TO_EOL, Visual, spot};

pub fn lookup(page: &str, card: &str, section: &str) -> Option<Visual> {
    match (page, card, section) {
        ("FINAL TEST", "LOAD", "Handler loads the part") => Some(Visual {
            art: ART_0,
            spots: SPOTS_0,
        }),
        ("FINAL TEST", "LOAD", "Index time") => Some(Visual {
            art: ART_1,
            spots: SPOTS_1,
        }),
        ("FINAL TEST", "LOAD", "Contact") => Some(Visual {
            art: ART_2,
            spots: SPOTS_2,
        }),
        ("FINAL TEST", "ATE TEST", "Test order") => Some(Visual {
            art: ART_3,
            spots: SPOTS_3,
        }),
        ("FINAL TEST", "ATE TEST", "Test time is cost") => Some(Visual {
            art: ART_4,
            spots: SPOTS_4,
        }),
        ("FINAL TEST", "ATE TEST", "Who sells it") => Some(Visual {
            art: ART_5,
            spots: SPOTS_5,
        }),
        ("FINAL TEST", "BURN-IN", "Why heat works") => Some(Visual {
            art: ART_6,
            spots: SPOTS_6,
        }),
        ("FINAL TEST", "BURN-IN", "Where it is used") => Some(Visual {
            art: ART_7,
            spots: SPOTS_7,
        }),
        ("FINAL TEST", "BURN-IN", "Wafer-level burn-in") => Some(Visual {
            art: ART_8,
            spots: SPOTS_8,
        }),
        ("FINAL TEST", "SYSTEM TEST", "What SLT catches") => Some(Visual {
            art: ART_9,
            spots: SPOTS_9,
        }),
        ("FINAL TEST", "SYSTEM TEST", "Slots and power") => Some(Visual {
            art: ART_10,
            spots: SPOTS_10,
        }),
        ("FINAL TEST", "SYSTEM TEST", "Titan HP") => Some(Visual {
            art: ART_11,
            spots: SPOTS_11,
        }),
        ("FINAL TEST", "SPEED BIN", "Bell curve") => Some(Visual {
            art: ART_12,
            spots: SPOTS_12,
        }),
        ("FINAL TEST", "SPEED BIN", "Salvage") => Some(Visual {
            art: ART_13,
            spots: SPOTS_13,
        }),
        ("FINAL TEST", "SPEED BIN", "Mix risk") => Some(Visual {
            art: ART_14,
            spots: SPOTS_14,
        }),
        ("FINAL TEST", "MARK + SHIP", "Mark") => Some(Visual {
            art: ART_15,
            spots: SPOTS_15,
        }),
        ("FINAL TEST", "MARK + SHIP", "Pack") => Some(Visual {
            art: ART_16,
            spots: SPOTS_16,
        }),
        ("FINAL TEST", "MARK + SHIP", "Escape cost") => Some(Visual {
            art: ART_17,
            spots: SPOTS_17,
        }),
        ("FINAL TEST", "HANDLER: picks part", "Handler jobs") => Some(Visual {
            art: ART_18,
            spots: SPOTS_18,
        }),
        ("FINAL TEST", "HANDLER: picks part", "Thermal control") => Some(Visual {
            art: ART_19,
            spots: SPOTS_19,
        }),
        ("FINAL TEST", "HANDLER: picks part", "Vendor view") => Some(Visual {
            art: ART_20,
            spots: SPOTS_20,
        }),
        ("FINAL TEST", "SOCKET: pins touch BGA", "What it is") => Some(Visual {
            art: ART_21,
            spots: SPOTS_21,
        }),
        ("FINAL TEST", "SOCKET: pins touch BGA", "Wear") => Some(Visual {
            art: ART_22,
            spots: SPOTS_22,
        }),
        ("FINAL TEST", "SOCKET: pins touch BGA", "Who and risk") => Some(Visual {
            art: ART_23,
            spots: SPOTS_23,
        }),
        ("FINAL TEST", "LOAD BOARD (custom", "Signal path") => Some(Visual {
            art: ART_24,
            spots: SPOTS_24,
        }),
        ("FINAL TEST", "LOAD BOARD (custom", "One per product") => Some(Visual {
            art: ART_25,
            spots: SPOTS_25,
        }),
        ("FINAL TEST", "LOAD BOARD (custom", "Demands and wear") => Some(Visual {
            art: ART_26,
            spots: SPOTS_26,
        }),
        ("FINAL TEST", "TEST HEAD", "What is inside") => Some(Visual {
            art: ART_27,
            spots: SPOTS_27,
        }),
        ("FINAL TEST", "TEST HEAD", "Duopoly") => Some(Visual {
            art: ART_28,
            spots: SPOTS_28,
        }),
        ("FINAL TEST", "TEST HEAD", "Conflicting share") => Some(Visual {
            art: ART_29,
            spots: SPOTS_29,
        }),
        ("FINAL TEST", "infant mortality", "Bathtub curve, left side") => Some(Visual {
            art: ART_30,
            spots: SPOTS_30,
        }),
        ("FINAL TEST", "infant mortality", "What burn-in does") => Some(Visual {
            art: ART_31,
            spots: SPOTS_31,
        }),
        ("FINAL TEST", "infant mortality", "Demand link") => Some(Visual {
            art: ART_32,
            spots: SPOTS_32,
        }),
        ("FINAL TEST", "Titan HP", "Platform") => Some(Visual {
            art: ART_33,
            spots: SPOTS_33,
        }),
        ("FINAL TEST", "Titan HP", "Cooling") => Some(Visual {
            art: ART_34,
            spots: SPOTS_34,
        }),
        ("FINAL TEST", "Titan HP", "Revenue shift") => Some(Visual {
            art: ART_35,
            spots: SPOTS_35,
        }),
        ("FINAL TEST", "TOP BIN", "Top bin") => Some(Visual {
            art: ART_36,
            spots: SPOTS_36,
        }),
        ("FINAL TEST", "TOP BIN", "What moves the bins") => Some(Visual {
            art: ART_37,
            spots: SPOTS_37,
        }),
        ("FINAL TEST", "TOP BIN", "Mix effect") => Some(Visual {
            art: ART_38,
            spots: SPOTS_38,
        }),
        ("FINAL TEST", "Advantest CY25", "Advantest share") => Some(Visual {
            art: ART_39,
            spots: SPOTS_39,
        }),
        ("FINAL TEST", "Advantest CY25", "Why numbers differ") => Some(Visual {
            art: ART_40,
            spots: SPOTS_40,
        }),
        ("FINAL TEST", "Advantest CY25", "What holds") => Some(Visual {
            art: ART_41,
            spots: SPOTS_41,
        }),
        ("FINAL TEST", "Test houses", "OSAT test houses") => Some(Visual {
            art: ART_42,
            spots: SPOTS_42,
        }),
        ("FINAL TEST", "Test houses", "Who owns the tools") => Some(Visual {
            art: ART_43,
            spots: SPOTS_43,
        }),
        ("FINAL TEST", "Test houses", "Risks") => Some(Visual {
            art: ART_44,
            spots: SPOTS_44,
        }),
        ("PACKAGE", "INTERPOSER", "The silicon wiring board") => Some(Visual {
            art: ART_45,
            spots: SPOTS_45,
        }),
        ("PACKAGE", "INTERPOSER", "Reticle limits") => Some(Visual {
            art: ART_46,
            spots: SPOTS_46,
        }),
        ("PACKAGE", "INTERPOSER", "Why it bottlenecks") => Some(Visual {
            art: ART_47,
            spots: SPOTS_47,
        }),
        ("PACKAGE", "CHIP-ON-WAFER", "CoW step") => Some(Visual {
            art: ART_48,
            spots: SPOTS_48,
        }),
        ("PACKAGE", "CHIP-ON-WAFER", "Known-good die") => Some(Visual {
            art: ART_49,
            spots: SPOTS_49,
        }),
        ("PACKAGE", "CHIP-ON-WAFER", "The name") => Some(Visual {
            art: ART_50,
            spots: SPOTS_50,
        }),
        ("PACKAGE", "FLIP ONTO", "Wafer-on-substrate") => Some(Visual {
            art: ART_51,
            spots: SPOTS_51,
        }),
        ("PACKAGE", "FLIP ONTO", "Expansion mismatch") => Some(Visual {
            art: ART_52,
            spots: SPOTS_52,
        }),
        ("PACKAGE", "FLIP ONTO", "Who does it") => Some(Visual {
            art: ART_53,
            spots: SPOTS_53,
        }),
        ("PACKAGE", "MOLD +", "Seal and finish") => Some(Visual {
            art: ART_54,
            spots: SPOTS_54,
        }),
        ("PACKAGE", "MOLD +", "What can fail") => Some(Visual {
            art: ART_55,
            spots: SPOTS_55,
        }),
        ("PACKAGE", "MOLD +", "Materials") => Some(Visual {
            art: ART_56,
            spots: SPOTS_56,
        }),
        ("PACKAGE", "[1] LID", "Lid and cold plate") => Some(Visual {
            art: ART_57,
            spots: SPOTS_57,
        }),
        ("PACKAGE", "[1] LID", "Flatness and warpage") => Some(Visual {
            art: ART_58,
            spots: SPOTS_58,
        }),
        ("PACKAGE", "[1] LID", "Supply") => Some(Visual {
            art: ART_59,
            spots: SPOTS_59,
        }),
        ("PACKAGE", "[2] TIM", "Thermal interface material") => Some(Visual {
            art: ART_60,
            spots: SPOTS_60,
        }),
        ("PACKAGE", "[2] TIM", "Different heights") => Some(Visual {
            art: ART_61,
            spots: SPOTS_61,
        }),
        ("PACKAGE", "[2] TIM", "Slow failure") => Some(Visual {
            art: ART_62,
            spots: SPOTS_62,
        }),
        ("PACKAGE", "[3] HBM", "HBM stack on the package") => Some(Visual {
            art: ART_63,
            spots: SPOTS_63,
        }),
        ("PACKAGE", "[3] HBM", "Share and supply") => Some(Visual {
            art: ART_64,
            spots: SPOTS_64,
        }),
        ("PACKAGE", "[3] HBM", "HBM4 and price") => Some(Visual {
            art: ART_65,
            spots: SPOTS_65,
        }),
        ("PACKAGE", "GPU DIE A", "The compute die") => Some(Visual {
            art: ART_66,
            spots: SPOTS_66,
        }),
        ("PACKAGE", "GPU DIE A", "Why two dies") => Some(Visual {
            art: ART_67,
            spots: SPOTS_67,
        }),
        ("PACKAGE", "GPU DIE A", "Package totals") => Some(Visual {
            art: ART_68,
            spots: SPOTS_68,
        }),
        ("PACKAGE", "[7] NV-HBI", "Die-to-die link") => Some(Visual {
            art: ART_69,
            spots: SPOTS_69,
        }),
        ("PACKAGE", "[7] NV-HBI", "Why it matters") => Some(Visual {
            art: ART_70,
            spots: SPOTS_70,
        }),
        ("PACKAGE", "[7] NV-HBI", "Packaging link") => Some(Visual {
            art: ART_71,
            spots: SPOTS_71,
        }),
        ("PACKAGE", "[6] TSV", "Through-silicon vias") => Some(Visual {
            art: ART_72,
            spots: SPOTS_72,
        }),
        ("PACKAGE", "[6] TSV", "How a TSV is made") => Some(Visual {
            art: ART_73,
            spots: SPOTS_73,
        }),
        ("PACKAGE", "[6] TSV", "Risks") => Some(Visual {
            art: ART_74,
            spots: SPOTS_74,
        }),
        ("PACKAGE", "[4] microbumps", "Pitch ladder") => Some(Visual {
            art: ART_75,
            spots: SPOTS_75,
        }),
        ("PACKAGE", "[4] microbumps", "Hybrid bonding") => Some(Visual {
            art: ART_76,
            spots: SPOTS_76,
        }),
        ("PACKAGE", "[4] microbumps", "Underfill gap") => Some(Visual {
            art: ART_77,
            spots: SPOTS_77,
        }),
        ("PACKAGE", "[8] C4 bumps", "C4 bumps") => Some(Visual {
            art: ART_78,
            spots: SPOTS_78,
        }),
        ("PACKAGE", "[8] C4 bumps", "Shear at the corners") => Some(Visual {
            art: ART_79,
            spots: SPOTS_79,
        }),
        ("PACKAGE", "[8] C4 bumps", "Why it matters") => Some(Visual {
            art: ART_80,
            spots: SPOTS_80,
        }),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "ABF substrate") => Some(Visual {
            art: ART_81,
            spots: SPOTS_81,
        }),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "2026 squeeze") => Some(Visual {
            art: ART_82,
            spots: SPOTS_82,
        }),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "Suppliers") => Some(Visual {
            art: ART_83,
            spots: SPOTS_83,
        }),
        ("PACKAGE", "CoWoS-L", "The scaling route") => Some(Visual {
            art: ART_84,
            spots: SPOTS_84,
        }),
        ("PACKAGE", "CoWoS-L", "Capacity estimates") => Some(Visual {
            art: ART_85,
            spots: SPOTS_85,
        }),
        ("PACKAGE", "CoWoS-L", "Demand and risk") => Some(Visual {
            art: ART_86,
            spots: SPOTS_86,
        }),
        ("PACKAGE", "supply gap", "Allocation, not just capacity") => Some(Visual {
            art: ART_87,
            spots: SPOTS_87,
        }),
        ("PACKAGE", "supply gap", "Capacity forecasts") => Some(Visual {
            art: ART_88,
            spots: SPOTS_88,
        }),
        ("PACKAGE", "supply gap", "Three shortages") => Some(Visual {
            art: ART_89,
            spots: SPOTS_89,
        }),
        ("PACKAGE", "ASE", "OSAT leaders") => Some(Visual {
            art: ART_90,
            spots: SPOTS_90,
        }),
        ("PACKAGE", "ASE", "Role in AI") => Some(Visual {
            art: ART_91,
            spots: SPOTS_91,
        }),
        ("PACKAGE", "ASE", "Investor angle") => Some(Visual {
            art: ART_92,
            spots: SPOTS_92,
        }),
        ("SHIP", "BOARD", "Bianca board") => Some(Visual {
            art: ART_93,
            spots: SPOTS_93,
        }),
        ("SHIP", "BOARD", "Where it can fail") => Some(Visual {
            art: ART_94,
            spots: SPOTS_94,
        }),
        ("SHIP", "BOARD", "Upstream limits") => Some(Visual {
            art: ART_95,
            spots: SPOTS_95,
        }),
        ("SHIP", "TRAY", "Compute tray") => Some(Visual {
            art: ART_96,
            spots: SPOTS_96,
        }),
        ("SHIP", "TRAY", "Who builds trays") => Some(Visual {
            art: ART_97,
            spots: SPOTS_97,
        }),
        ("SHIP", "TRAY", "Failure points") => Some(Visual {
            art: ART_98,
            spots: SPOTS_98,
        }),
        ("SHIP", "RACK", "Rack integration") => Some(Visual {
            art: ART_99,
            spots: SPOTS_99,
        }),
        ("SHIP", "RACK", "Rack totals") => Some(Visual {
            art: ART_100,
            spots: SPOTS_100,
        }),
        ("SHIP", "RACK", "Power and weight") => Some(Visual {
            art: ART_101,
            spots: SPOTS_101,
        }),
        ("SHIP", "NVLINK SWITCH TRAY 1", "All-to-all fabric") => Some(Visual {
            art: ART_102,
            spots: SPOTS_102,
        }),
        ("SHIP", "NVLINK SWITCH TRAY 1", "Why one rack") => Some(Visual {
            art: ART_103,
            spots: SPOTS_103,
        }),
        ("SHIP", "NVLINK SWITCH TRAY 1", "Cables and revenue") => Some(Visual {
            art: ART_104,
            spots: SPOTS_104,
        }),
        ("SHIP", "power shelves", "AC to DC") => Some(Visual {
            art: ART_105,
            spots: SPOTS_105,
        }),
        ("SHIP", "power shelves", "Against other racks") => Some(Visual {
            art: ART_106,
            spots: SPOTS_106,
        }),
        ("SHIP", "power shelves", "Vertiv design") => Some(Visual {
            art: ART_107,
            spots: SPOTS_107,
        }),
        ("SHIP", "coolant manifolds", "Coolant loop") => Some(Visual {
            art: ART_108,
            spots: SPOTS_108,
        }),
        ("SHIP", "coolant manifolds", "CDU sizing") => Some(Visual {
            art: ART_109,
            spots: SPOTS_109,
        }),
        ("SHIP", "coolant manifolds", "Leaks and testing") => Some(Visual {
            art: ART_110,
            spots: SPOTS_110,
        }),
        ("SHIP", "BURN + TEST", "Rack-level checks") => Some(Visual {
            art: ART_111,
            spots: SPOTS_111,
        }),
        ("SHIP", "BURN + TEST", "What it catches") => Some(Visual {
            art: ART_112,
            spots: SPOTS_112,
        }),
        ("SHIP", "BURN + TEST", "Cost") => Some(Visual {
            art: ART_113,
            spots: SPOTS_113,
        }),
        ("SHIP", "crate by", "Route") => Some(Visual {
            art: ART_114,
            spots: SPOTS_114,
        }),
        ("SHIP", "crate by", "Weight and floors") => Some(Visual {
            art: ART_115,
            spots: SPOTS_115,
        }),
        ("SHIP", "crate by", "Volumes") => Some(Visual {
            art: ART_116,
            spots: SPOTS_116,
        }),
        ("SHIP", "DATA CENTER", "Site readiness") => Some(Visual {
            art: ART_117,
            spots: SPOTS_117,
        }),
        ("SHIP", "DATA CENTER", "Reference design") => Some(Visual {
            art: ART_118,
            spots: SPOTS_118,
        }),
        ("SHIP", "DATA CENTER", "Who buys") => Some(Visual {
            art: ART_119,
            spots: SPOTS_119,
        }),
        ("SHIP", "ODM", "Who builds") => Some(Visual {
            art: ART_120,
            spots: SPOTS_120,
        }),
        ("SHIP", "ODM", "Shipments") => Some(Visual {
            art: ART_121,
            spots: SPOTS_121,
        }),
        ("SHIP", "ODM", "Share claims") => Some(Visual {
            art: ART_122,
            spots: SPOTS_122,
        }),
        ("SHIP", "OEM", "OEMs") => Some(Visual {
            art: ART_123,
            spots: SPOTS_123,
        }),
        ("SHIP", "OEM", "HPE spec sheet") => Some(Visual {
            art: ART_124,
            spots: SPOTS_124,
        }),
        ("SHIP", "OEM", "Margin and mix") => Some(Visual {
            art: ART_125,
            spots: SPOTS_125,
        }),
        ("SHIP", "NVL72 peak", "Rack power density") => Some(Visual {
            art: ART_126,
            spots: SPOTS_126,
        }),
        ("SHIP", "NVL72 peak", "Retrofit limits") => Some(Visual {
            art: ART_127,
            spots: SPOTS_127,
        }),
        ("SHIP", "NVL72 peak", "Siting math") => Some(Visual {
            art: ART_128,
            spots: SPOTS_128,
        }),
        ("SHIP", "2026 forecast", "KGI rack forecasts") => Some(Visual {
            art: ART_129,
            spots: SPOTS_129,
        }),
        ("SHIP", "2026 forecast", "Implied GPUs") => Some(Visual {
            art: ART_130,
            spots: SPOTS_130,
        }),
        ("SHIP", "2026 forecast", "Dependencies") => Some(Visual {
            art: ART_131,
            spots: SPOTS_131,
        }),
        ("SHIP", "Azure ND GB200 v6", "Renting a GPU-hour") => Some(Visual {
            art: ART_132,
            spots: SPOTS_132,
        }),
        ("SHIP", "Azure ND GB200 v6", "Rack revenue") => Some(Visual {
            art: ART_133,
            spots: SPOTS_133,
        }),
        ("SHIP", "Azure ND GB200 v6", "Why it matters") => Some(Visual {
            art: ART_134,
            spots: SPOTS_134,
        }),
        _ => None,
    }
}

const ART_0: &str = r##"\
# Load, test, sort

  ┌─────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
  │ TRAY    │     │ PICK      │     │ SOCKET    │     │ SORT      │
  │ or tape │ ──▶ │ and carry │ ──▶ │ test site │ ──▶ │ into bins │
  └─────────┘     └───────────┘     └───────────┘     └───────────┘
   JEDEC tray      handler           tester runs       pass / fail
                                     the test          by result

  (the handler starts the test and sorts on the tester's result)
"##;

const SPOTS_0: &[Spot] = &[
    spot(
        "TRAY",
        0,
        0,
        "Packaged parts arrive in JEDEC trays or on tape, from assembly.",
    ),
    spot(
        "PICK",
        0,
        0,
        "The handler's pick-and-place arm lifts a part and carries it to the test site.",
    ),
    spot(
        "SOCKET",
        0,
        0,
        "The part is pressed into a socket on the load board, which connects every ball to the tester.",
    ),
    spot(
        "SORT",
        0,
        0,
        "When the tester returns its result, the handler drops the part in a pass or fail bin.",
    ),
    spot(
        "(the handler starts the test and sorts on the tester's result)",
        0,
        0,
        "Handler and tester talk to each other: start-test and end-test signals, then a bin code.",
    ),
];

const ART_1: &str = r##"\
# Index time leaves the tester idle

  1 site    ██████████ ░░░ ██████████ ░░░ ██████████ ░░░
            test       idle test      idle test      idle

  4 sites   ██████████ ░░░ ██████████ ░░░ ██████████ ░░░
            parts 1-4      parts 5-8      parts 9-12

  (idle = index time: the handler swapping parts)
"##;

const SPOTS_1: &[Spot] = &[
    spot(
        "1 site",
        0,
        TO_EOL,
        "With one site the tester sits idle during every swap, so its hourly cost is wasted for that gap.",
    ),
    spot(
        "4 sites",
        0,
        TO_EOL,
        "Testing several parts at once means four parts finish per pass, so the same index gap is shared over more good output.",
    ),
    spot(
        "(idle = index time: the handler swapping parts)",
        0,
        0,
        "Index time is the handler's swap time. Fast swaps and more parallel sites are how handlers keep expensive testers busy.",
    ),
];

const ART_2: &str = r##"\
# Press force keeps every ball in contact

      handler pusher  ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼
    ┌──────────────────────────────────────┐
    │ GPU + HBM PACKAGE (warps when hot)   │
    └──────────────────────────────────────┘
         o o o o o o o o o o o o o     BGA balls
         ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃ ┃     spring pins
    ┌──────────────────────────────────────┐
    │ SOCKET body on the LOAD BOARD        │
    └──────────────────────────────────────┘

  (a failed contact looks like a failed chip)
"##;

const SPOTS_2: &[Spot] = &[
    spot(
        "handler pusher",
        0,
        0,
        "The handler presses the package down with enough force to engage thousands of contacts at once.",
    ),
    spot(
        "GPU + HBM PACKAGE",
        0,
        0,
        "Large AI packages warp when hot, which lifts the corner balls away from their pins and causes false failures (textbook).",
    ),
    spot(
        "BGA balls",
        0,
        0,
        "Each ball must touch one socket pin. A modern AI package has thousands.",
    ),
    spot(
        "spring pins",
        0,
        0,
        "Spring-loaded pins in the socket press against the balls and carry the test signals and current to the load board.",
    ),
    spot(
        "(a failed contact looks like a failed chip)",
        0,
        0,
        "A bad contact bins a good part as a failure, or lets a marginal one pass and fail later.",
    ),
];

const ART_3: &str = r##"\
# What ATE runs, in order

  ┌─────────────┐     ┌────────────┐     ┌──────────┐
  │ POWER UP    │     │ CONTINUITY │     │ SCAN     │
  │ rails first │ ──▶ │ + LEAKAGE  │ ──▶ │ patterns │
  └─────────────┘     └────────────┘     └──────────┘
   supply check        shorts and opens   logic defects

  ┌────────┐     ┌──────────────┐     ┌─────────────┐
  │ MEMORY │     │ LOOPBACK     │     │ BIN         │
  │ BIST   │ ──▶ │ serial links │ ──▶ │ pass / fail │
  └────────┘     └──────────────┘     └─────────────┘
   HBM interfaces PCIe / NVLink        to burn-in or reject

  (order and contents are textbook; no counts sourced)
"##;

const SPOTS_3: &[Spot] = &[
    spot(
        "POWER UP",
        0,
        0,
        "Apply supply rails first; a part that draws abnormal current is rejected immediately.",
    ),
    spot(
        "CONTINUITY",
        0,
        0,
        "Quick DC checks for opens and shorts at the pins, and leakage, before spending time on long patterns.",
    ),
    spot(
        "SCAN",
        0,
        0,
        "Scan chains drive structured patterns through the logic to catch manufacturing defects.",
    ),
    spot(
        "MEMORY",
        0,
        0,
        "Built-in self-test exercises the HBM interface logic without needing an external pattern for every cell.",
    ),
    spot(
        "LOOPBACK",
        0,
        0,
        "High-speed serial lanes are tested by looping a transmitter back into a receiver, on the part or the load board.",
    ),
    spot(
        "BIN",
        0,
        0,
        "Passing parts continue to burn-in and speed binning; failures are rejected.",
    ),
];

const ART_4: &str = r##"\
# Test time per die (claims, unverified)

  conventional chip   ██████████                       1x
  AI silicon (claim)  ██████████████████████████████   3-5x test time
  reticle-limit die: 2-3x the patterns of a 7nm SoC (claim)

  tester hour  >  most back-end tools
  so: longer test  =  more testers bought

  (both multipliers are unverified claims)
"##;

const SPOTS_4: &[Spot] = &[
    spot(
        "conventional chip",
        0,
        TO_EOL,
        "The baseline: a conventional chip's test time per die.",
    ),
    spot(
        "AI silicon (claim)",
        0,
        TO_EOL,
        "One source claims leading AI silicon needs 3-5x the test time per die. This is an unverified claim.",
    ),
    spot(
        "reticle-limit die: 2-3x",
        0,
        TO_EOL,
        "A second claim: a reticle-limit die needs 2-3x the test patterns of a 7nm SoC. Also unverified.",
    ),
    spot(
        "tester hour",
        0,
        TO_EOL,
        "A tester costs far more per hour than most fab tools in the back end, so test time per die is the cost lever.",
    ),
    spot(
        "more testers bought",
        0,
        0,
        "Longer test per die means more tester-hours per wafer, which turns into more tester purchases at Advantest and Teradyne.",
    ),
];

const ART_5: &str = r##"\
# Teradyne, Q4 2025

  semiconductor test   ████████████████████  $883M (~81.5% of sales)

  AI share of revenue
    Q4 2025 actual  ████████████████████  above 60%
    Q1 2026 guide   ████████████████████████  up to 70%

  Two big SoC tester vendors:  Advantest  and  Teradyne
"##;

const SPOTS_5: &[Spot] = &[
    spot(
        "semiconductor test",
        0,
        TO_EOL,
        "Teradyne's Q4 2025 semiconductor test revenue was $883M, about 81.5% of its sales.",
    ),
    spot(
        "Q4 2025 actual",
        0,
        TO_EOL,
        "AI was above 60% of Teradyne's revenue in Q4 2025.",
    ),
    spot(
        "Q1 2026 guide",
        0,
        TO_EOL,
        "Teradyne guided AI up to 70% of revenue in Q1 2026.",
    ),
    spot(
        "Advantest",
        0,
        0,
        "Advantest is the other big SoC tester vendor; share estimates differ between sources (see the Advantest card).",
    ),
];

const ART_6: &str = r##"\
# Arrhenius: how much faster than normal use

  junction temp   acceleration vs 50C use   (Ea assumed 0.7 eV)

   75C   █ 6x
  100C   █████ 29x
  125C   ████████████████████ 114x
  150C   ████████████████████████████████████████ 380x

  1000 h at 100C  =  ~29,000 h of use  =  ~3.3 years
  (textbook arithmetic; Ea depends on the failure mechanism)
"##;

const SPOTS_6: &[Spot] = &[
    spot(
        "75C",
        0,
        TO_EOL,
        "At 75C junction temperature the Arrhenius factor against 50C use is about 6x with Ea 0.7 eV.",
    ),
    spot(
        "100C",
        0,
        TO_EOL,
        "About 29x. 1000 hours at 100C ages a part like roughly 3.3 years at 50C.",
    ),
    spot(
        "125C",
        0,
        TO_EOL,
        "About 114x. 125C is the common junction temperature for 1000-hour life tests (vendor qualification reports).",
    ),
    spot(
        "150C",
        0,
        TO_EOL,
        "About 380x, which is why wafer-level systems that reach 150C can screen quickly.",
    ),
    spot(
        "Ea depends on the failure mechanism",
        0,
        0,
        "Typical mechanisms use 0.6-1 eV for dielectric breakdown and electromigration; 0.7 eV is a common assumption, not a measured value for any AI part.",
    ),
];

const ART_7: &str = r##"\
# Cost of a miss grows with each stage

  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
  │ WAFER    │    │ PACKAGE      │    │ RACK TRAY   │    │ DATA CENTRE  │
  │ cheap to │ ─▶ │ scrap a      │ ─▶ │ pull a tray │ ─▶ │ downtime on  │
  │ scrap    │    │ packaged GPU │    │ from a rack │    │ a whole rack │
  └──────────┘    └──────────────┘    └─────────────┘    └──────────────┘

  JESD22-A108 life test: 1000 h, Tj 125C, 77 units, zero fails
  (vendor qualification reports; burn-in is the short production form)
"##;

const SPOTS_7: &[Spot] = &[
    spot(
        "WAFER",
        0,
        0,
        "Defects found at wafer sort scrap only a bare die.",
    ),
    spot(
        "PACKAGE",
        0,
        0,
        "After packaging, a failure scraps an expensive GPU plus HBM assembly.",
    ),
    spot(
        "RACK TRAY",
        0,
        0,
        "A failure in a built rack means pulling a tray out of a liquid-cooled system.",
    ),
    spot(
        "DATA CENTRE",
        0,
        0,
        "A field failure costs downtime on a rack that is the whole unit of capacity, which is why AI parts get burn-in.",
    ),
    spot(
        "JESD22-A108",
        0,
        TO_EOL,
        "The JEDEC life-test method; typical qualification is 1000 hours at 125C junction temperature on 77 units with no failures allowed (vendor reports).",
    ),
];

const ART_8: &str = r##"\
# Package-level vs wafer-level burn-in

  package level   WAFER ─▶ cut ─▶ PACKAGE ─▶ BURN-IN ─▶ keep / scrap
                  (a bad die is already in an expensive package)

  wafer level     WAFER ─▶ BURN-IN (FOX-XP) ─▶ cut ─▶ PACKAGE
                  (bad die found before packaging)

  FOX-XP: 9 wafers in parallel (up to 18, Aehr claim), up to 150C
  Feb 2026: $14M order from its lead AI processor customer (Aehr)
"##;

const SPOTS_8: &[Spot] = &[
    spot(
        "package level",
        0,
        TO_EOL,
        "Package-level burn-in tests after assembly, so an infant-mortality failure wastes the whole package.",
    ),
    spot(
        "wafer level",
        0,
        TO_EOL,
        "Wafer-level burn-in stresses bare die on the wafer, before the expensive packaging steps.",
    ),
    spot(
        "FOX-XP: 9 wafers",
        0,
        TO_EOL,
        "Aehr shipped its first FOX-XP for AI processors in Feb 2025, 9 wafers in parallel in that configuration, up to 18 by its claim, at wafer temperatures up to 150C.",
    ),
    spot(
        "Feb 2026",
        0,
        TO_EOL,
        "Aehr announced a $14M order from its lead AI processor customer. All Aehr figures are company claims.",
    ),
];

const ART_9: &str = r##"\
# ATE patterns vs a real workload

  ATE                           SLT
  ───────────────────────────   ───────────────────────────
  structured test patterns      boots software on a board
  fast, many parts per hour     slow, needs many parallel slots
  finds manufacturing defects   finds interaction faults:
                                  block-to-block behaviour
                                  supply droop under load
                                  firmware and thermal limits

  (textbook contrast; Teradyne launched Titan HP for SLT)
"##;

const SPOTS_9: &[Spot] = &[
    spot(
        "ATE   ",
        0,
        0,
        "ATE runs structured patterns fast and finds manufacturing defects.",
    ),
    spot(
        "SLT",
        0,
        0,
        "System-level test runs the part like the real product, which exposes faults that patterns miss.",
    ),
    spot(
        "block-to-block behaviour",
        0,
        0,
        "Faults that only appear when several blocks work together, which isolated ATE patterns do not exercise.",
    ),
    spot(
        "supply droop under load",
        0,
        0,
        "Real workloads pull current in bursts; a marginal part can droop its supply and crash only under that load.",
    ),
    spot(
        "firmware and thermal limits",
        0,
        0,
        "Boot firmware and temperature behaviour are only exercised by running real software on the part.",
    ),
];

const ART_10: &str = r##"\
# Why slot count and heat limit SLT

  one SLT run is long  ─▶  need many sites at once

   ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐ ... 
   │▓▓││▓▓││▓▓││▓▓││▓▓││▓▓││▓▓││▓▓││▓▓││▓▓│  each slot: socket + cooling
   └──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘

  watts per site  ▲  older cells not built for AI heat
  floor space and socket count become the limit

  (textbook; no slot counts sourced)
"##;

const SPOTS_10: &[Spot] = &[
    spot(
        "one SLT run is long",
        0,
        TO_EOL,
        "SLT runs are slow, so throughput comes from running many parts in parallel.",
    ),
    spot(
        "each slot: socket + cooling",
        0,
        0,
        "Every slot needs its own socket, board and cooling, so capacity is limited by slot count and floor space.",
    ),
    spot(
        "watts per site",
        0,
        TO_EOL,
        "A modern AI package dissipates far more heat than older SLT cells were designed to remove.",
    ),
    spot(
        "floor space and socket count",
        0,
        0,
        "Because each slot is costly and runs long, the bottleneck is physical capacity, not just tester count.",
    ),
];

const ART_11: &str = r##"\
# Teradyne Titan HP (launched 2 Oct 2025)

  power per site
    today    ████████████████████ up to 2 kW
    roadmap  ████████████████████████████████████████ 4 kW

  ┌────────────┐     ┌──────────────┐     ┌─────────────┐
  │ DUT        │     │ COLD PLATE   │     │ PID control │
  │ AI package │ ◀─▶ │ multi-branch │ ◀─▶ │ per site    │
  └────────────┘     └──────────────┘     └─────────────┘

  cold plate cools the DUT and the parts around it
  in production at several large customers (unnamed, Teradyne)
"##;

const SPOTS_11: &[Spot] = &[
    spot(
        "today",
        0,
        TO_EOL,
        "Titan HP supports up to 2 kW per site today.",
    ),
    spot(
        "roadmap",
        0,
        TO_EOL,
        "Teradyne's roadmap goes to 4 kW per site.",
    ),
    spot(
        "COLD PLATE",
        0,
        0,
        "A multi-branch cold plate cools both the device under test and surrounding components.",
    ),
    spot(
        "PID control",
        0,
        0,
        "Asynchronous PID-tuned thermal control per site, with an optional DUT heater.",
    ),
    spot(
        "in production at several",
        0,
        TO_EOL,
        "Teradyne states Titan HP is in production at several large customers, which it did not name.",
    ),
];

const ART_12: &str = r##"\
# Dies spread by fmax and power

                        ▓▓▓▓▓▓▓
                    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
               ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  ─────────┬─────────────┬─────────────┬──────────────▶ fmax
      SCRAP        LOW BIN        MID BIN         TOP BIN

  (shape is illustrative; no bin split is sourced)
"##;

const SPOTS_12: &[Spot] = &[
    spot("SCRAP", 0, 0, "Dies that fail even the lowest spec."),
    spot(
        "LOW BIN",
        0,
        0,
        "Slower or higher-power dies sold as a cut-down SKU.",
    ),
    spot(
        "MID BIN",
        0,
        0,
        "The bulk of the distribution, sold as the mainstream SKU.",
    ),
    spot(
        "TOP BIN",
        0,
        0,
        "The fastest, lowest-power dies, sold as the flagship SKU at the highest price.",
    ),
    spot(
        "─▶ fmax",
        0,
        0,
        "Each die is characterised for its highest stable clock and the power at that clock.",
    ),
];

const ART_13: &str = r##"\
# A bad block does not scrap the die

  full die (all blocks good)       salvaged die (2 blocks fused off)

   ┌────┬────┬────┬────┐             ┌────┬────┬────┬────┐
   │ SM │ SM │ SM │ SM │             │ SM │ ✕✕ │ SM │ SM │
   ├────┼────┼────┼────┤             ├────┼────┼────┼────┤
   │ SM │ SM │ SM │ SM │             │ SM │ SM │ ✕✕ │ SM │
   └────┴────┴────┴────┘             └────┴────┴────┴────┘
      top SKU                          lower SKU, still sold

  (grid is schematic; real dies disable failed SMs or HBM channels)
"##;

const SPOTS_13: &[Spot] = &[
    spot(
        "full die",
        0,
        TO_EOL,
        "Every compute block works: the die can go to the top SKU if its clocks and power are good.",
    ),
    spot(
        "salvaged die",
        0,
        TO_EOL,
        "A failed block is fused off and the die is sold as a lower SKU instead of being scrapped.",
    ),
    spot(
        "✕✕",
        0,
        0,
        "A disabled unit. Large AI dies disable failed SMs or HBM channels this way (textbook practice).",
    ),
    spot(
        "lower SKU, still sold",
        0,
        0,
        "Salvage turns would-be scrap into revenue, which is part of why yield on huge dies is economic.",
    ),
];

const ART_14: &str = r##"\
# If the curve shifts low, the top-bin share falls

  normal                          shifted low
               ▓▓▓                        ▓▓▓
             ▓▓▓▓▓▓▓                    ▓▓▓▓▓▓▓
           ▓▓▓▓▓▓▓▓▓▒▒                ▓▓▓▓▓▓▓▓▓▓▓
         ▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  ──────────────────┬───────────   ──────────────────┬───────────▶ fmax
                     top bin ▶▶                         top bin ▶

  ▒ = beyond the top-bin line
  fewer top-bin parts = less flagship supply = lower average price
  (illustrative; vendors do not publish bin splits)
"##;

const SPOTS_14: &[Spot] = &[
    spot(
        "normal",
        0,
        TO_EOL,
        "A tight, well-centred distribution leaves a healthy share of dies beyond the top-bin line.",
    ),
    spot(
        "shifted low",
        0,
        TO_EOL,
        "If process variation shifts the curve slower, fewer dies reach the top bin.",
    ),
    spot(
        "▒ = beyond the top-bin line",
        0,
        0,
        "The shaded part of each curve is the dies fast enough to be sold as the top SKU.",
    ),
    spot(
        "lower average price",
        0,
        0,
        "The mix is not under the vendor's control, so a low-shifted curve lowers average selling price. No bin split is sourced.",
    ),
];

const ART_15: &str = r##"\
# One mark ties a part to its history

    ┌──────────────────────────────┐
    │ PART NO.  GB200-xxxx         │
    │ LOT       L12345             │
    │ DATE      2604               │
    └──────────────────────────────┘

        │ lot code looks up
        ▼
  ┌───────┐    ┌───────────┐    ┌──────────┐
  │ WAFER │    │ TEST      │    │ HANDLER  │
  │ lot   │ ── │ insertion │ ── │ + socket │
  └───────┘    └───────────┘    └──────────┘

  (part number is made up; marking contents are textbook)
"##;

const SPOTS_15: &[Spot] = &[
    spot(
        "PART NO.",
        0,
        TO_EOL,
        "Laser mark with part number. Made up here for illustration.",
    ),
    spot(
        "LOT",
        0,
        TO_EOL,
        "The lot code is the key that links the part to its wafer and test records.",
    ),
    spot(
        "DATE",
        0,
        TO_EOL,
        "The date code gives when it was made, which helps bound a recall.",
    ),
    spot(
        "WAFER",
        0,
        0,
        "Trace back to the wafer lot the die came from.",
    ),
    spot(
        "TEST",
        0,
        0,
        "Trace to the test insertion that passed the part.",
    ),
    spot(
        "HANDLER",
        0,
        0,
        "Trace to the handler and socket used, to catch a bad contact or fixture.",
    ),
];

const ART_16: &str = r##"\
# From tested part to the next owner

  ┌───────┐     ┌──────────────┐     ┌────────────────┐
  │ MARK  │     │ PACK         │     │ BOARD MAKER    │
  │ laser │ ──▶ │ tray or reel │ ──▶ │ tray assembler │
  └───────┘     └──────────────┘     └────────────────┘
   lot + date    ESD and ball-safe    see the SHIP page

  Packing must protect the BGA balls and prevent static damage.
  A GPU's next stop is a board and tray assembler, not the end customer.

  (textbook; see the SHIP page for the route)
"##;

const SPOTS_16: &[Spot] = &[
    spot(
        "MARK",
        0,
        0,
        "Laser mark with part number, lot and date code.",
    ),
    spot("PACK", 0, 0, "Trays or tape-and-reel for the next owner."),
    spot(
        "BOARD MAKER",
        0,
        0,
        "Board and tray assemblers receive the part, not the end customer.",
    ),
    spot(
        "prevent static damage",
        0,
        0,
        "Electrostatic discharge can kill a finished part, so packing is ESD-safe and keeps balls from being crushed.",
    ),
];

const ART_17: &str = r##"\
# A test escape gets more expensive downstream

  ┌────────────┐    ┌───────────┐    ┌─────────────┐    ┌─────────────┐
  │ FINAL TEST │    │ BOARD     │    │ RACK        │    │ FIELD       │
  │ stop here  │ ─▶ │ rework it │ ─▶ │ pull a tray │ ─▶ │ rack outage │
  └────────────┘    └───────────┘    └─────────────┘    └─────────────┘

  cost of a bad part:    chip  ──▶  tray swap  ──▶  rack outage
                         (no dollar figures sourced)

  So AI buyers accept extra screens: burn-in and SLT.
"##;

const SPOTS_17: &[Spot] = &[
    spot(
        "FINAL TEST",
        0,
        0,
        "Last point where a bad die is cheap to stop; test escape rate is a key quality measure.",
    ),
    spot(
        "BOARD",
        0,
        0,
        "Once on a board, a bad part means rework of the board and its neighbours.",
    ),
    spot(
        "RACK",
        0,
        0,
        "In a built rack, a bad GPU means pulling a tray from a liquid-cooled system.",
    ),
    spot(
        "FIELD",
        0,
        0,
        "In a data centre a failure costs a rack tray swap rather than one chip.",
    ),
    spot(
        "burn-in and SLT",
        0,
        0,
        "The extra screens buyers accept because a failure late costs far more than extra test.",
    ),
];

const ART_18: &str = r##"\
# Four jobs in one machine

  ┌───────────┐     ┌───────────┐     ┌─────────────┐     ┌─────────────┐
  │ PICK      │     │ PRESS     │     │ HEAT / COOL │     │ SORT        │
  │ from tray │ ──▶ │ in socket │ ──▶ │ to set temp │ ──▶ │ pass / fail │
  └───────────┘     └───────────┘     └─────────────┘     └─────────────┘

  It also talks to the tester: start-test, end-test, bin code.
  Mechanical parts wear, so uptime and jam rate set real capacity.

  (jobs per the page diagram and patent descriptions)
"##;

const SPOTS_18: &[Spot] = &[
    spot("PICK", 0, 0, "Lift each part from its tray or tape."),
    spot(
        "PRESS",
        0,
        0,
        "Push the part into the socket with enough force for every contact.",
    ),
    spot(
        "HEAT / COOL",
        0,
        0,
        "Hold the part at a set temperature, hot or cold, to test across its operating range.",
    ),
    spot(
        "SORT",
        0,
        0,
        "Drop the part in a bin based on the tester's result.",
    ),
    spot(
        "uptime and jam rate",
        0,
        0,
        "Handlers are mechanical and wear, so uptime and jam rate drive effective capacity.",
    ),
];

const ART_19: &str = r##"\
# Cohu MT9510 XP temperature range

  -55C                  0C                 +100C            +175C
   ├─────────────────────┼───────────────────┼────────────────┤
   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
   cold                                              hot

  AI parts self-heat in test and can overshoot the target.
  T CORE thermal control + cDragon pin: fast temperature response

  (Cohu catalog figures, via search summary)
"##;

const SPOTS_19: &[Spot] = &[
    spot(
        "-55C",
        0,
        0,
        "Cold end of the MT9510 XP handler's listed range (Cohu catalog).",
    ),
    spot(
        "+175C",
        0,
        0,
        "Hot end of the listed range (Cohu catalog, via search summary).",
    ),
    spot(
        "self-heat",
        0,
        TO_EOL,
        "High-power AI parts heat themselves during test and can overshoot the target temperature.",
    ),
    spot(
        "T CORE",
        0,
        TO_EOL,
        "Cohu lists T CORE thermal control, and its cDragon contactor pin as supporting fast temperature response.",
    ),
];

const ART_20: &str = r##"\
# Handler + contactor as one interface

  ┌─────────────────┐     ┌────────────────────┐
  │ HANDLER         │     │ CONTACTOR          │
  │ thermal + force │ ◀─▶ │ pins and heat path │
  └─────────────────┘     └────────────────────┘

  bundling both = one thermal and mechanical interface (market report)

  Cohu, Q1 2026 call (management commentary):
    5 more customers engaged on Eclipse    ~$200M opportunity
    high-performance computing market      $750M
"##;

const SPOTS_20: &[Spot] = &[
    spot(
        "HANDLER",
        0,
        0,
        "Presses the part and sets its temperature.",
    ),
    spot(
        "CONTACTOR",
        0,
        0,
        "The socket pins that touch each ball and carry heat and current.",
    ),
    spot(
        "bundling both",
        0,
        TO_EOL,
        "A market report says the vendor edge is selling handler and contactor together as one thermal and mechanical interface.",
    ),
    spot(
        "5 more customers",
        0,
        TO_EOL,
        "On Cohu's Q1 2026 call: five more customers engaged on the Eclipse platform, about $200M of incremental revenue opportunity. Management commentary, not independent.",
    ),
    spot(
        "high-performance computing market",
        0,
        TO_EOL,
        "Cohu put the HPC market at $750M. Management commentary.",
    ),
];

const ART_21: &str = r##"\
# Socket cross-section

    ┌──────────────────────────────┐
    │ PACKAGE                      │
    └──────────────────────────────┘
      o  o  o  o  o  o  o  o  o  o  o     BGA balls
      ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃     spring pins
    ┌──────────────────────────────────────┐
    │ SOCKET body (cavity holds the part)  │
    └──────────────────────────────────────┘
      ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓     load board pads

  Pins: pogo, elastomer, or particle interconnect (patents)
"##;

const SPOTS_21: &[Spot] = &[
    spot(
        "PACKAGE",
        0,
        0,
        "The device under test, with a BGA ball per signal and power contact.",
    ),
    spot(
        "BGA balls",
        0,
        0,
        "Each ball touches exactly one socket pin.",
    ),
    spot(
        "spring pins",
        0,
        0,
        "Spring-loaded contacts that press against the balls; types include pogo pins and elastomer contacts.",
    ),
    spot(
        "SOCKET body",
        0,
        0,
        "The base has contacts and a cavity for receiving the device.",
    ),
    spot(
        "load board pads",
        0,
        0,
        "The pins' other ends meet pads on the load board, which route to the tester.",
    ),
];

const ART_22: &str = r##"\
# Pins wear and foul with every insertion

  new pin      worn pin       fouled pin
    ┃            ┃              ┃░░
    ┃            ┃▒             ┃░░░
    ┃            ┃▒▒            ┃░░
   ───          ───            ───

  ▒ = wear   ░ = solder residue

  Sockets are consumables: cleaned, then replaced (textbook).
  Called a quiet bottleneck on the page.
"##;

const SPOTS_22: &[Spot] = &[
    spot(
        "new pin",
        0,
        TO_EOL,
        "A fresh contact has low, stable resistance.",
    ),
    spot(
        "worn pin",
        0,
        TO_EOL,
        "Wear raises contact resistance and can cause false failures.",
    ),
    spot(
        "fouled pin",
        0,
        TO_EOL,
        "Solder residue builds up on pins and must be cleaned off.",
    ),
    spot(
        "consumables",
        0,
        TO_EOL,
        "Sockets are cleaned and replaced after a limited number of insertions (textbook).",
    ),
    spot(
        "quiet bottleneck",
        0,
        0,
        "The page's phrase for socket wear: it rarely makes headlines but limits uptime.",
    ),
];

const ART_23: &str = r##"\
# Two ways a bad contact hurts

  contact bad, die good    ──▶  binned as FAIL   (good part lost)
  contact marginal         ──▶  passes now ──▶ fails in the field

  Suppliers named in the sources:
    WinWay   major AI-socket supplier (market report)
    Cohu     cHybrid, cCompact, Gemini, ICON, MiCon

  contactors are increasingly co-designed with tester + package
"##;

const SPOTS_23: &[Spot] = &[
    spot(
        "contact bad, die good",
        0,
        TO_EOL,
        "A good die is binned as a failure: lost revenue and wasted silicon.",
    ),
    spot(
        "contact marginal",
        0,
        TO_EOL,
        "A marginal contact can pass test and later fail in service.",
    ),
    spot(
        "WinWay",
        0,
        TO_EOL,
        "Named in a market report as a major AI-socket supplier.",
    ),
    spot(
        "Cohu     cHybrid",
        0,
        TO_EOL,
        "Cohu lists contactors such as cHybrid, cCompact, Gemini, ICON and MiCon.",
    ),
    spot(
        "co-designed",
        0,
        TO_EOL,
        "Per a market report, contactors are increasingly designed together with the tester and the package.",
    ),
];

const ART_24: &str = r##"\
# From tester channel to device pin

  ┌───────────┐     ┌──────────────┐     ┌────────┐     ┌────────┐
  │ TEST HEAD │     │ LOAD BOARD   │     │ SOCKET │     │ DEVICE │
  │ channels  │ ──▶ │ traces, caps │ ──▶ │ pins   │ ──▶ │ BGA    │
  └───────────┘     └──────────────┘     └────────┘     └────────┘

  on the board:  decoupling caps, relays, loopback circuits
  also delivers power and grounds to the device

  (patent descriptions; textbook)
"##;

const SPOTS_24: &[Spot] = &[
    spot(
        "TEST HEAD",
        0,
        0,
        "Tester electronics: pattern generators, supplies and instruments.",
    ),
    spot(
        "LOAD BOARD",
        0,
        0,
        "A custom PCB that extends the tester's measurement resources to the device's pins.",
    ),
    spot(
        "SOCKET",
        0,
        0,
        "Mounted on the load board; holds and contacts the device.",
    ),
    spot("DEVICE", 0, 0, "The part under test."),
    spot(
        "decoupling caps",
        0,
        TO_EOL,
        "Support parts on the board: decoupling capacitors, relays and sometimes serial-link loopback.",
    ),
];

const ART_25: &str = r##"\
# New pinout, new board

  product A  (pinout A)  ──▶  LOAD BOARD A
  product B  (pinout B)  ──▶  LOAD BOARD B
  product C  (pinout C)  ──▶  LOAD BOARD C

  board design sits on the critical path to a launch

  boards wear and are repaired, like sockets
  = recurring revenue for tester and board vendors

  (textbook; no market figures sourced)
"##;

const SPOTS_25: &[Spot] = &[
    spot(
        "product A",
        0,
        TO_EOL,
        "Each product has its own pinout and power budget.",
    ),
    spot(
        "product B",
        0,
        TO_EOL,
        "A different package needs a different board.",
    ),
    spot(
        "product C",
        0,
        TO_EOL,
        "Boards are not reused across unrelated devices.",
    ),
    spot(
        "critical path",
        0,
        TO_EOL,
        "Because each new part needs a new board, board design is on the critical path to a product launch.",
    ),
    spot(
        "recurring revenue",
        0,
        TO_EOL,
        "Boards wear and need repair, creating recurring revenue for tester and board vendors (textbook).",
    ),
];

const ART_26: &str = r##"\
# What an AI load board must do

  very high current     ████████████████████  low droop needed
  high-speed lanes      ███████████████       PCIe, NVLink
  layer count           ██████████████████    dense routing
  cost                  ████████████████████  expensive (none sourced)

  Signal-integrity faults on the board can look like device failures,
  so board qualification is part of test development.

  (bars are qualitative, not data)
"##;

const SPOTS_26: &[Spot] = &[
    spot(
        "very high current",
        0,
        TO_EOL,
        "AI devices draw large currents; the board must deliver them with low droop.",
    ),
    spot(
        "high-speed lanes",
        0,
        TO_EOL,
        "The board must carry high-speed lanes such as PCIe and NVLink cleanly.",
    ),
    spot(
        "layer count",
        0,
        TO_EOL,
        "Demanding routing means many layers and expensive materials (textbook).",
    ),
    spot(
        "Signal-integrity faults",
        0,
        TO_EOL,
        "Board problems can mimic device failures, so the board itself must be qualified.",
    ),
    spot(
        "(bars are qualitative, not data)",
        0,
        0,
        "No sourced layer counts or prices; the bars only rank demands.",
    ),
];

const ART_27: &str = r##"\
# Inside the test head

  ┌────────────────────────────────────────────────────────┐
  │ PATTERN GENERATORS  drive and compare digital pins     │
  │ POWER SUPPLIES       big current rails for AI parts    │
  │ ANALOG + RF          instruments                       │
  │ channels: many, one set per pin group                  │
  └────────────────────────────────────────────────────────┘

              │ short path to the load board
              ▼
  ┌────────────────────────────────────────────────────────┐
  │ LOAD BOARD + SOCKET + DEVICE                           │
  └────────────────────────────────────────────────────────┘
"##;

const SPOTS_27: &[Spot] = &[
    spot(
        "PATTERN GENERATORS",
        0,
        TO_EOL,
        "Drive and compare digital signals on many channels.",
    ),
    spot(
        "POWER SUPPLIES",
        0,
        TO_EOL,
        "Large current rails matter for AI parts that draw hundreds of amps at low voltage.",
    ),
    spot(
        "ANALOG + RF",
        0,
        TO_EOL,
        "Instruments for analog and RF measurements.",
    ),
    spot(
        "LOAD BOARD + SOCKET",
        0,
        0,
        "The head sits right next to the load board to keep signal paths short.",
    ),
];

const ART_28: &str = r##"\
# Two vendors, one claim each

  ┌───────────┐      ┌──────────┐
  │ ADVANTEST │      │ TERADYNE │
  │ 6857.T    │  vs  │ TER      │
  └───────────┘      └──────────┘

  Teradyne: ~50% in VIP compute (own claim)
  Teradyne: power-supply capability is the edge
  Teradyne 2025: Semi Test Group +19%, SoC test +23%

  few alternatives for chipmakers = capacity can gate output
"##;

const SPOTS_28: &[Spot] = &[
    spot(
        "ADVANTEST",
        0,
        0,
        "One of the two main SoC tester vendors (ticker 6857.T).",
    ),
    spot(
        "TERADYNE",
        0,
        0,
        "The other main SoC tester vendor (ticker TER).",
    ),
    spot("~50% in VIP compute", 0, TO_EOL, "Teradyne's own claim."),
    spot(
        "power-supply capability",
        0,
        TO_EOL,
        "Teradyne says its power-supply capability is an advantage for AI parts.",
    ),
    spot(
        "Semi Test Group +19%",
        0,
        TO_EOL,
        "Teradyne's 2025 Semiconductor Test Group grew 19% and SoC test 23%, on networking and compute.",
    ),
];

const ART_29: &str = r##"\
# Estimates do not reconcile

  Advantest CY25 (one analysis)    ██████████████████████████████ 66%
  Advantest CY24 (same analysis)   ████████████████████████████ 56%
  Teradyne (a different source)    ███████████████████████ 50-55%
  Teradyne VIP compute (own claim) ██████████████████████ ~50%

  different definitions: compute SoC testers vs all ATE

  treat all of them as ranges
"##;

const SPOTS_29: &[Spot] = &[
    spot(
        "Advantest CY25",
        0,
        TO_EOL,
        "One analysis puts Advantest at 66% of SoC test in CY25.",
    ),
    spot(
        "Advantest CY24",
        0,
        TO_EOL,
        "The same analysis has 56% before.",
    ),
    spot(
        "Teradyne (a different source)",
        0,
        TO_EOL,
        "A different source says Teradyne holds 50-55% of SoC test, which conflicts with the 66% Advantest figure.",
    ),
    spot(
        "Teradyne VIP compute",
        0,
        TO_EOL,
        "Teradyne's own claim for a narrower segment.",
    ),
    spot(
        "different definitions",
        0,
        TO_EOL,
        "Sources count different things (compute SoC only vs all ATE), so shares cannot be compared directly.",
    ),
];

const ART_30: &str = r##"\
# Three zones of a part's life

  failure  │▓
  rate     │▓▓                                             ▓▓▓
           │ ▓▓                                         ▓▓▓
           │   ▓▓▓                                  ▓▓▓
           │      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
           └──────────┬──────────────────────────┬────────────▶ time
            INFANT MORTALITY     USEFUL LIFE         WEAR-OUT

  infant mortality: weak parts fail early, rate falling
  useful life: low, flat random failures
  wear-out: rising (electromigration, oxide breakdown)

  (shape only; no failure rates sourced)
"##;

const SPOTS_30: &[Spot] = &[
    spot(
        "INFANT MORTALITY",
        0,
        0,
        "The early zone, where weak parts with latent defects fail at a falling rate.",
    ),
    spot(
        "USEFUL LIFE",
        0,
        0,
        "The long flat zone with a low random failure rate; where customers want every part to be.",
    ),
    spot(
        "WEAR-OUT",
        0,
        0,
        "Rising failures from ageing mechanisms such as electromigration and oxide breakdown.",
    ),
    spot(
        "infant mortality: weak",
        0,
        TO_EOL,
        "Latent defects like thin oxide, weak vias and marginal solder cause these early failures.",
    ),
    spot(
        "wear-out: rising",
        0,
        TO_EOL,
        "Ageing mechanisms eventually dominate; the part's rated life sits before this zone.",
    ),
];

const ART_31: &str = r##"\
# Burn-in moves the part past the left zone

  without burn-in    ┃▓▓ fails in the field ┃  useful life ─────────▶
  with burn-in       ┃▓▓ fails in factory ┃  ▶ ships here: useful life ─▶

                     ◀──── burn-in hours ────▶

  longer or hotter  =  more weak parts caught
                     =  but some life of good parts is used up

  (reduces early failures; does not remove them entirely)
"##;

const SPOTS_31: &[Spot] = &[
    spot(
        "without burn-in",
        0,
        TO_EOL,
        "Weak parts fail at the customer, in a data centre.",
    ),
    spot(
        "with burn-in",
        0,
        TO_EOL,
        "The same weak parts fail in the factory instead, and the customer starts in the flat zone.",
    ),
    spot(
        "burn-in hours",
        0,
        0,
        "Longer or hotter stress finds more weak parts, at the cost of time and some life of good parts.",
    ),
    spot(
        "(reduces early failures",
        0,
        TO_EOL,
        "Sources note burn-in lowers the early failure rate but never eliminates it.",
    ),
];

const ART_32: &str = r##"\
# More screening, more capacity

  bigger die  ──▶  more places for a latent defect
  more screens ─▶  more burn-in and SLT time per part

  more time per part  ──▶  more capacity needed

     wafer-level burn-in        Aehr (AEHR)
     SLT + burn-in cells        Teradyne and others

  (no hours or temperatures sourced for AI GPUs)
"##;

const SPOTS_32: &[Spot] = &[
    spot(
        "bigger die",
        0,
        TO_EOL,
        "A reticle-size die has more area where a latent defect can sit.",
    ),
    spot(
        "more screens",
        0,
        TO_EOL,
        "Every extra screen takes tester or oven time per part.",
    ),
    spot(
        "more time per part",
        0,
        TO_EOL,
        "More time per part means more burn-in and SLT capacity is needed for the same output.",
    ),
    spot(
        "wafer-level burn-in",
        0,
        TO_EOL,
        "Aehr sells wafer-level burn-in systems for AI processors.",
    ),
    spot(
        "SLT + burn-in cells",
        0,
        TO_EOL,
        "Teradyne and other vendors sell system-level test and burn-in cells.",
    ),
    spot(
        "(no hours or temperatures",
        0,
        TO_EOL,
        "The page says not to trust blog numbers for AI-GPU burn-in conditions.",
    ),
];

const ART_33: &str = r##"\
# Titan HP at a glance

  ┌────────────────────────────────────────────────────────┐
  │ TITAN HP   system-level test, AI + cloud devices       │
  │ announced   2 Oct 2025                                 │
  │ per site    up to 2 kW now, roadmap to 4 kW            │
  │ status      in production at several large customers   │
  └────────────────────────────────────────────────────────┘

  2 kW  ████████████████████
  4 kW  ████████████████████████████████████████

  (customers unnamed; Teradyne statements)
"##;

const SPOTS_33: &[Spot] = &[
    spot(
        "TITAN HP",
        0,
        TO_EOL,
        "Teradyne's system-level test platform for high-power AI and cloud devices.",
    ),
    spot("announced", 0, TO_EOL, "Launched on 2 October 2025."),
    spot(
        "per site",
        0,
        TO_EOL,
        "Up to 2 kW per site today, roadmap to 4 kW.",
    ),
    spot(
        "status",
        0,
        TO_EOL,
        "Teradyne states it is in production at several large customers, not named.",
    ),
    spot(
        "4 kW",
        0,
        TO_EOL,
        "The roadmap figure: double today's power per site.",
    ),
];

const ART_34: &str = r##"\
# How a 2 kW site is cooled

        PID thermal control, per site (asynchronous)
                      │
     ┌────────────────┴───────────────────────┐
     │  MULTI-BRANCH COLD PLATE               │
     └──┬─────────────┬─────────────────┬─────┘
        │             │                 │
   ┌────┴────┐   ┌────┴──────┐   ┌──────┴─────┐
   │ DUT     │   │ parts     │   │ DUT heater │
   │ (AI pkg)│   │ around it │   │ (optional) │
   └─────────┘   └───────────┘   └────────────┘
"##;

const SPOTS_34: &[Spot] = &[
    spot(
        "PID thermal control",
        0,
        TO_EOL,
        "Asynchronous PID-tuned thermal control for each site.",
    ),
    spot(
        "MULTI-BRANCH COLD PLATE",
        0,
        0,
        "One cold plate with several branches that cools the device and the components around it.",
    ),
    spot(
        "DUT     │",
        0,
        0,
        "The device under test, a high-power AI package.",
    ),
    spot(
        "parts     │",
        0,
        0,
        "Surrounding parts are cooled by the same cold plate.",
    ),
    spot(
        "DUT heater",
        0,
        0,
        "An optional heater lets the system hold a set temperature when the part is idle.",
    ),
];

const ART_35: &str = r##"\
# Teradyne: AI share of revenue

  Q4 2025 actual   ████████████████████████  above 60%
  Q1 2026 guide    ████████████████████████████  up to 70%

  risks for SLT
    crowded field: many specialist vendors
    customers can do less SLT if ATE + burn-in coverage improve

  (earnings summary; no SLT share sourced)
"##;

const SPOTS_35: &[Spot] = &[
    spot(
        "Q4 2025 actual",
        0,
        TO_EOL,
        "AI above 60% of Teradyne's revenue.",
    ),
    spot("Q1 2026 guide", 0, TO_EOL, "Guided up to 70%."),
    spot(
        "crowded field",
        0,
        TO_EOL,
        "SLT has many specialist vendors, so share is not secure.",
    ),
    spot(
        "customers can do less SLT",
        0,
        TO_EOL,
        "Better ATE and burn-in coverage could reduce how much SLT customers buy.",
    ),
];

const ART_36: &str = r##"\
# Bins become SKUs

  ┌────────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐
  │ SCRAP      │   │ LOW BIN      │   │ MID BIN  │   │ TOP BIN  │
  │ fails spec │ ◀ │ cut-down SKU │ ◀ │ main SKU │ ◀ │ flagship │
  └────────────┘   └──────────────┘   └──────────┘   └──────────┘

   price:  none        $         $$         $$$
   speed:  below spec  slower    typical    fastest, lowest power

  (price ladder is qualitative)
"##;

const SPOTS_36: &[Spot] = &[
    spot("SCRAP", 0, 0, "Dies that fail even the lowest spec."),
    spot("LOW BIN", 0, 0, "Sold as a cut-down product."),
    spot("MID BIN", 0, 0, "Sold as the mainstream SKU."),
    spot(
        "TOP BIN",
        0,
        0,
        "The fastest, lowest-power dies, sold as the flagship at the highest price.",
    ),
    spot(
        "price:",
        0,
        TO_EOL,
        "Qualitative only: higher bins sell for more.",
    ),
];

const ART_37: &str = r##"\
# Process maturity and die size

  mature node        tight curve    ┃▓┃     top bin share ▲
  new node           wide curve   ┃▓▓▓▓▓┃   top bin share ▼
  large die          wide curve   ┃▓▓▓▓▓┃   top bin share ▼

  bins are set on two axes, not one:
           fmax (speed)   ×   power at that clock

  rack power is the limit for AI, so watts matter as much as GHz
"##;

const SPOTS_37: &[Spot] = &[
    spot(
        "mature node",
        0,
        TO_EOL,
        "A mature process tightens the distribution and lifts the top-bin share.",
    ),
    spot("new node", 0, TO_EOL, "A new process widens the spread."),
    spot(
        "large die",
        0,
        TO_EOL,
        "More area means more variation across one die, which widens the spread.",
    ),
    spot("fmax (speed)", 0, 0, "Highest stable clock."),
    spot(
        "power at that clock",
        0,
        0,
        "Bins are set on both clock and power because rack power is the limit for AI.",
    ),
];

const ART_38: &str = r##"\
# Salvage lowers scrap, mix drives price

  defective die ──▶ fuse off bad SM / HBM channel ──▶ cut-down SKU
                       scrap is lower than the raw defect rate

  top-bin share ▼   ──▶   less flagship supply
                    ──▶   more mix pressure on average price

  bin yields are closely held; none are sourced here
"##;

const SPOTS_38: &[Spot] = &[
    spot(
        "defective die",
        0,
        TO_EOL,
        "A die with a failed block is not necessarily scrap.",
    ),
    spot(
        "fuse off",
        0,
        0,
        "Large AI dies disable failed SMs or HBM channels and sell as cut-down parts (textbook).",
    ),
    spot(
        "top-bin share",
        0,
        TO_EOL,
        "If fewer dies reach the top bin there is less flagship supply.",
    ),
    spot(
        "more mix pressure",
        0,
        0,
        "A lower top-bin share pushes down average selling price.",
    ),
    spot(
        "closely held",
        0,
        0,
        "Chip vendors do not publish bin yields.",
    ),
];

const ART_39: &str = r##"\
# Advantest SoC test share

  2023 report      ████████████████████████ ~50%
  CY24 analysis    ████████████████████████████ 56%
  CY25 analysis    ██████████████████████████████████ 66%

  Advantest (6857.T): analysts call it the SoC test leader
  stock tracks Nvidia: GPU volume drives test demand (KR-Asia)

  (CY24 and CY25 from one analysis; 2023 from an older report)
"##;

const SPOTS_39: &[Spot] = &[
    spot(
        "2023 report",
        0,
        TO_EOL,
        "An older 2023 report put Advantest near 50%.",
    ),
    spot(
        "CY24 analysis",
        0,
        TO_EOL,
        "56% in the analysis that gives 66% for CY25.",
    ),
    spot(
        "CY25 analysis",
        0,
        TO_EOL,
        "66% of SoC test in calendar 2025, in one analysis.",
    ),
    spot(
        "Advantest (6857.T)",
        0,
        TO_EOL,
        "Described by analysts as the leader in SoC test.",
    ),
    spot(
        "stock tracks Nvidia",
        0,
        TO_EOL,
        "A KR-Asia article links the stock closely to Nvidia because GPU volume drives test demand.",
    ),
];

const ART_40: &str = r##"\
# Same market, different definitions

   compute SoC testers only   ◀── one definition
   all ATE                    ◀── another
   VIP compute segment        ◀── Teradyne's claim (~50%)

  Advantest 66%  ┃  Teradyne ~50% in VIP compute  ┃  Teradyne 50-55%
                 ┗━━ they cannot all be summed ━━━┛

  treat each figure as a range, not a measurement
"##;

const SPOTS_40: &[Spot] = &[
    spot(
        "compute SoC testers only",
        0,
        TO_EOL,
        "Some sources count only compute SoC testers.",
    ),
    spot(
        "all ATE",
        0,
        TO_EOL,
        "Others count all automatic test equipment.",
    ),
    spot(
        "VIP compute segment",
        0,
        TO_EOL,
        "Teradyne's own claim of about 50% is for a narrower segment.",
    ),
    spot(
        "Advantest 66%",
        0,
        TO_EOL,
        "These figures come from different definitions, so they do not add up to one market.",
    ),
    spot(
        "a range, not a measurement",
        0,
        0,
        "Share depends on what is counted; no single figure is authoritative.",
    ),
];

const ART_41: &str = r##"\
# What survives the disagreement

   1  two vendors dominate SoC test
   2  AI test intensity is the growth driver for both
         more patterns   longer test   higher power

   Teradyne: gained share in HBM and DRAM final test in 2025
             while memory test was otherwise flat

  the exact split is unknown
"##;

const SPOTS_41: &[Spot] = &[
    spot(
        "two vendors dominate",
        0,
        TO_EOL,
        "Advantest and Teradyne are the two big SoC tester vendors.",
    ),
    spot(
        "AI test intensity",
        0,
        TO_EOL,
        "More patterns, longer tests and higher power per part raise test demand for both vendors.",
    ),
    spot(
        "more patterns",
        0,
        TO_EOL,
        "Each driver of test intensity shows up as more tester time per part.",
    ),
    spot(
        "gained share in HBM",
        0,
        TO_EOL,
        "Teradyne says it gained share in HBM and DRAM final test in 2025.",
    ),
    spot(
        "exact split is unknown",
        0,
        0,
        "Sources conflict, so only the duopoly and the growth driver are safe to rely on.",
    ),
];

const ART_42: &str = r##"\
# Test-focused OSATs, share of 2024 top-10 revenue

  KYEC (2449.TW)  ██ 2.2%
  Hana Micron     ██ 2.2%
  ChipMOS         ▌ 1.7%

  ASE (ASX), Amkor (AMKR): assembly + test together
  (TrendForce 2024 top-10 OSAT ranking, as cited on the page)
"##;

const SPOTS_42: &[Spot] = &[
    spot(
        "KYEC",
        0,
        TO_EOL,
        "Test-focused OSAT, 2.2% of top-10 revenue in TrendForce's 2024 ranking.",
    ),
    spot("Hana Micron", 0, TO_EOL, "2.2% of top-10 revenue."),
    spot("ChipMOS", 0, TO_EOL, "1.7% of top-10 revenue."),
    spot(
        "ASE (ASX), Amkor (AMKR)",
        0,
        0,
        "The two largest OSATs do assembly and test together.",
    ),
];

const ART_43: &str = r##"\
# The OSAT carries the capital cost

  ┌───────────┐     ┌───────────────────┐     ┌───────────────┐
  │ TERADYNE  │     │ OSAT              │     │ CHIP          │
  │ ADVANTEST │ ──▶ │ owns testers,     │ ──▶ │ DESIGNER      │
  │ COHU      │     │ handlers, sockets │     │ pays per part │
  └───────────┘     └───────────────────┘     └───────────────┘
   sell tools        capital cost

  test capacity at the OSAT can gate shipment of AI GPUs
  die size and chiplet count raise test time
"##;

const SPOTS_43: &[Spot] = &[
    spot("TERADYNE", 0, 0, "Tester vendor; sells to OSATs."),
    spot("ADVANTEST", 0, 0, "Tester vendor; sells to OSATs."),
    spot("COHU", 0, 0, "Handler and contactor vendor."),
    spot(
        "OSAT",
        1,
        0,
        "The outsourced test house owns the testers, handlers and sockets and carries the capital cost.",
    ),
    spot(
        "CHIP",
        0,
        0,
        "The chip designer outsources test and depends on OSAT capacity.",
    ),
    spot(
        "gate shipment",
        0,
        0,
        "Larger dies and more chiplets raise test time, so OSAT capacity can limit GPU shipments.",
    ),
];

const ART_44: &str = r##"\
# What can go wrong at a test house

  customer concentration   ████████████████  a few designers fill it
  consumable cost          ████████████      sockets, boards, pins
  tester lead times        ███████████       delays cap ramps

  Chinese firms gained ground in the 2024 OSAT ranking (TrendForce)

  (bars are qualitative, not data)
"##;

const SPOTS_44: &[Spot] = &[
    spot(
        "customer concentration",
        0,
        TO_EOL,
        "A few chip designers fill most of the capacity.",
    ),
    spot(
        "consumable cost",
        0,
        TO_EOL,
        "Sockets, boards and pins wear and must be replaced.",
    ),
    spot(
        "tester lead times",
        0,
        TO_EOL,
        "Late tester delivery limits how fast capacity can grow.",
    ),
    spot(
        "Chinese firms gained ground",
        0,
        TO_EOL,
        "TrendForce reports Chinese firms gaining ground in the 2024 OSAT ranking.",
    ),
];

const ART_45: &str = r##"\
# GPU and HBM talk through the interposer

   ┌─────┐  ┌─────────┐  ┌─────────┐  ┌─────┐
   │ HBM │  │ GPU DIE │  │ GPU DIE │  │ HBM │
   └─────┘  └─────────┘  └─────────┘  └─────┘
     o o o o o o o o o o o o o o o o o o o o o o o   microbumps
  ┌────────────────────────────────────────────────────────┐
  │ SILICON INTERPOSER: wires only, no transistors         │
  │ ║      ║      ║      ║      ║      ║      ║   TSVs     │
  └────────────────────────────────────────────────────────┘
     1024-bit bus per HBM stack, about 1 TB/s (page)

  only silicon can be patterned at micrometre pitch
"##;

const SPOTS_45: &[Spot] = &[
    spot(
        "HBM",
        1,
        0,
        "Each HBM stack connects over a 1024-bit bus, about 1 TB/s per stack on the page.",
    ),
    spot(
        "GPU DIE",
        0,
        0,
        "Compute dies sit beside the memory, so signals travel millimetres.",
    ),
    spot(
        "microbumps",
        0,
        0,
        "Tiny solder joints connect each die to the interposer.",
    ),
    spot(
        "SILICON INTERPOSER",
        0,
        0,
        "A passive slab of silicon with wiring only, no transistors (CoWoS-S).",
    ),
    spot(
        "TSVs",
        0,
        0,
        "Copper-filled vias through the interposer carry power and signals to the layer below.",
    ),
    spot(
        "1024-bit bus",
        0,
        TO_EOL,
        "The wide bus per HBM stack needs thousands of fine wires; only silicon can be patterned that finely.",
    ),
];

const ART_46: &str = r##"\
# Interposer size, in reticles

  one reticle (~800 mm2, page)   ██████ 1x
  CoWoS-L shown at ECTC (8 HBM)  ██████████████████ ~3x
  CoWoS-S maximum (~2,700 mm2)   ████████████████████ 3.3x
  development target             ████████████████████████████████████ 6x

  beyond 3.3x: CoWoS-L (local Si bridges + RDL)
           or  CoWoS-R (RDL only, 4 um min pitch, secondary)

  (reticle ~800 mm2 from the NV-HBI card; sizes are TSMC / ECTC figures)
"##;

const SPOTS_46: &[Spot] = &[
    spot(
        "one reticle",
        0,
        TO_EOL,
        "The largest single exposure a scanner can print, near 800 mm2.",
    ),
    spot(
        "CoWoS-L shown at ECTC",
        0,
        TO_EOL,
        "An ECTC paper shows CoWoS-L with about 3x reticle and 8 HBM.",
    ),
    spot(
        "CoWoS-S maximum",
        0,
        TO_EOL,
        "TSMC's CoWoS-S interposers reach up to 3.3x the reticle, about 2,700 mm2.",
    ),
    spot(
        "development target",
        0,
        TO_EOL,
        "A 6x reticle package is a development target, not a shipping product.",
    ),
    spot(
        "CoWoS-R (RDL only",
        0,
        TO_EOL,
        "CoWoS-R uses RDL only; a secondary source gives a 4 um minimum RDL pitch.",
    ),
];

const ART_47: &str = r##"\
# How an interposer is made

  ┌───────────┐    ┌────────┐    ┌────────────┐    ┌──────────┐
  │ ETCH      │    │ FILL   │    │ THIN       │    │ EXPOSE   │
  │ TSV holes │ ─▶ │ copper │ ─▶ │ wafer back │ ─▶ │ via tips │
  └───────────┘    └────────┘    └────────────┘    └──────────┘

  bigger interposer  =  more wafer area used  =  more warp

  2026 CoWoS wafers (Morgan Stanley via news summary, secondary)
    total  ████████████████████████████████████ 90-95k
    -L     █████████████████████████ ~68k
"##;

const SPOTS_47: &[Spot] = &[
    spot(
        "ETCH",
        0,
        0,
        "Deep narrow holes are etched through the silicon.",
    ),
    spot("FILL", 0, 0, "The holes are lined and filled with copper."),
    spot("THIN", 0, 0, "The wafer is ground thin from the back."),
    spot(
        "EXPOSE",
        0,
        0,
        "Grinding continues until the copper via tips show on the back.",
    ),
    spot(
        "bigger interposer",
        0,
        TO_EOL,
        "Larger interposers waste more wafer area and warp more.",
    ),
    spot(
        "-L     ",
        0,
        TO_EOL,
        "Morgan Stanley, via a news summary, puts CoWoS-L at about 68k of 90-95k wafers in 2026. Secondary source.",
    ),
];

const ART_48: &str = r##"\
# Four moves at wafer level

  ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌─────────────┐
  │ PLACE     │    │ REFLOW     │    │ UNDERFILL │    │ MOLD        │
  │ face-down │ ─▶ │ microbumps │ ─▶ │ capillary │ ─▶ │ compression │
  └───────────┘    └────────────┘    └───────────┘    └─────────────┘

  the interposer is still a full wafer:
  many packages are processed in parallel

  (steps per the page and TSMC's CoWoS description)
"##;

const SPOTS_48: &[Spot] = &[
    spot(
        "PLACE",
        0,
        0,
        "Known-good GPU and HBM dies are placed face-down on the interposer wafer.",
    ),
    spot(
        "REFLOW",
        0,
        0,
        "Heat melts the microbump solder to join die and interposer. Thermal drift here decides yield.",
    ),
    spot(
        "UNDERFILL",
        0,
        0,
        "Epoxy flows between the dies by capillary action.",
    ),
    spot("MOLD", 0, 0, "A compression mold fixes the assembly."),
    spot(
        "full wafer",
        0,
        TO_EOL,
        "Because the interposer is still a whole wafer, handling is wafer-level and many packages go through at once.",
    ),
];

const ART_49: &str = r##"\
# One B200 package = 10 placements

   GPU  GPU  HBM  HBM  HBM  HBM  HBM  HBM  HBM  HBM
   [ok] [ok] [ok] [ok] [XX] [ok] [ok] [ok] [ok] [ok]

   one failed placement  ──▶  the whole package is scrapped
   (every part already on it is lost)

   so dies are sorted BEFORE packaging (see PICK)

  (2 GPU + 8 HBM per B200: 10 placements, simple count)
"##;

const SPOTS_49: &[Spot] = &[
    spot(
        "GPU  GPU",
        0,
        TO_EOL,
        "A B200 has two GPU dies and eight HBM3E stacks on one package.",
    ),
    spot("[XX]", 0, 0, "One bad placement among ten."),
    spot(
        "the whole package is scrapped",
        0,
        0,
        "Expensive parts already mounted are lost with it.",
    ),
    spot(
        "sorted BEFORE packaging",
        0,
        0,
        "Known-good die sorting at wafer sort and PICK is why packaging yield stays economic.",
    ),
    spot(
        "(2 GPU + 8 HBM",
        0,
        TO_EOL,
        "Counting dies: 2 + 8 = 10 placements per package.",
    ),
];

const ART_50: &str = r##"\
# Chip on Wafer on Substrate

  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────┐
  │ 1 interposer │    │ 2 CoW       │    │ 3 thin, bump │    │ 4 oS     │
  │ wafer made   │ ─▶ │ chips on it │ ─▶ │ and dice     │ ─▶ │ to board │
  └──────────────┘    └─────────────┘    └──────────────┘    └──────────┘

       CoWoS  =  steps 2 and 4:
       Chip on Wafer ... on Substrate

  (naming is textbook; step list from the page)
"##;

const SPOTS_50: &[Spot] = &[
    spot(
        "1 interposer",
        0,
        0,
        "The interposer wafer is made first, with TSVs and RDL.",
    ),
    spot(
        "2 CoW",
        0,
        0,
        "Dies are mounted on the wafer: the Chip-on-Wafer part of the name.",
    ),
    spot(
        "3 thin, bump",
        0,
        0,
        "The wafer is thinned, C4-bumped and diced into modules.",
    ),
    spot(
        "4 oS",
        0,
        0,
        "Each module is flipped onto an organic substrate: the on-Substrate part.",
    ),
    spot(
        "CoWoS  =  steps 2 and 4",
        0,
        0,
        "Chip on Wafer on Substrate names two of the steps (textbook).",
    ),
];

const ART_51: &str = r##"\
# From CoW wafer to a finished module

  ┌────────────┐    ┌─────────┐    ┌────────────────┐
  │ THIN       │    │ DICE    │    │ FLIP           │
  │ + C4 bumps │ ─▶ │ modules │ ─▶ │ onto substrate │
  └────────────┘    └─────────┘    └────────────────┘

  ┌─────────────┐    ┌───────────┐    ┌──────────┐
  │ UNDERFILL 2 │    │ LID + TIM │    │ BGA      │
  │ C4 joints   │ ─▶ │ fitted    │ ─▶ │ balls on │
  └─────────────┘    └───────────┘    └──────────┘

  (steps per the page; a second underfill protects the C4 joints)
"##;

const SPOTS_51: &[Spot] = &[
    spot(
        "THIN",
        0,
        0,
        "The CoW wafer is thinned and C4 bumps formed on the underside.",
    ),
    spot(
        "DICE",
        0,
        0,
        "Cut into separate interposer-plus-chip modules.",
    ),
    spot(
        "FLIP",
        0,
        0,
        "Each module is flipped onto an organic substrate and reflowed.",
    ),
    spot(
        "UNDERFILL 2",
        0,
        0,
        "A second underfill protects the C4 joints.",
    ),
    spot(
        "LID + TIM",
        0,
        0,
        "The lid and thermal interface material go on after the underfill.",
    ),
    spot(
        "BGA",
        0,
        0,
        "BGA balls are attached for mounting on a board or socket.",
    ),
];

const ART_52: &str = r##"\
# Thermal expansion, ppm per degree C

  silicon interposer  ███ ~3
  organic substrate   ███████████████ 15-20

  heat  ──▶  substrate grows ~5-7x more  ──▶  package warps
  every power cycle flexes the bumps

  fixes: underfill, stiffener ring, lid

  (textbook values; warpage rises with interposer area, per the page)
"##;

const SPOTS_52: &[Spot] = &[
    spot(
        "silicon interposer",
        0,
        TO_EOL,
        "Silicon expands about 3 ppm per degree C (textbook).",
    ),
    spot(
        "organic substrate",
        0,
        TO_EOL,
        "An organic substrate expands about 15-20 ppm per degree C (textbook).",
    ),
    spot(
        "package warps",
        0,
        0,
        "The mismatch makes a large package warp with every heat cycle.",
    ),
    spot(
        "fixes:",
        0,
        TO_EOL,
        "Underfill, a stiffener ring and the lid keep the bumps from cracking.",
    ),
];

const ART_53: &str = r##"\
# TSMC keeps the front half

  ┌──────────────────┐    ┌───────────────────┐
  │ TSMC             │    │ ASE / SPIL, Amkor │
  │ interposer + CoW │ ─▶ │ oS overflow       │
  └──────────────────┘    └───────────────────┘

  ASE (ASX): SPIL is part of ASE
  Amkor (AMKR): takes overflow on-substrate work

  back half of CoWoS = where OSAT partners gain

  (textbook split; OSAT figures on the ASE card)
"##;

const SPOTS_53: &[Spot] = &[
    spot(
        "TSMC",
        1,
        0,
        "Retains the interposer and chip-on-wafer steps (textbook).",
    ),
    spot(
        "ASE / SPIL, Amkor",
        0,
        0,
        "Overflow oS (on-substrate) work goes to OSAT partners.",
    ),
    spot("ASE (ASX)", 0, TO_EOL, "SPIL is part of ASE."),
    spot(
        "Amkor (AMKR)",
        0,
        TO_EOL,
        "Takes overflow on-substrate work.",
    ),
    spot(
        "OSAT partners gain",
        0,
        0,
        "The back half of CoWoS is where outsourced assembly houses pick up volume.",
    ),
];

const ART_54: &str = r##"\
# Last four steps

  ┌───────────────┐    ┌───────────────┐    ┌───────────┐    ┌───────┐
  │ MOLD          │    │ LID           │    │ TIM       │    │ BGA   │
  │ + underfill 2 │ ─▶ │ or cold plate │ ─▶ │ fills gap │ ─▶ │ ~1 mm │
  └───────────────┘    └───────────────┘    └───────────┘    └───────┘

  mold + underfill lock the structure
  lid spreads heat; TIM removes air gaps under it

  (BGA ball size is textbook)
"##;

const SPOTS_54: &[Spot] = &[
    spot(
        "MOLD",
        0,
        0,
        "Compression mold and the second underfill lock the structure.",
    ),
    spot(
        "LID",
        0,
        0,
        "The lid, or a direct cold plate, spreads heat from the dies.",
    ),
    spot(
        "TIM",
        0,
        0,
        "Thermal interface material fills the microscopic gap between die backs and the lid.",
    ),
    spot(
        "BGA",
        0,
        0,
        "Solder balls, about 1 mm class (textbook), for mounting on the board or socket.",
    ),
];

const ART_55: &str = r##"\
# Late-stage failure modes

      ┌────────────────── LID ──────────────────┐   ◀ lid delamination
      │  ≈≈≈ TIM ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈  │
      └─┬───────────────┬────────────────┬──────┘
     ┌──┴──┐  ○ void   ┌┴────┐ ╱tilt     ┌┴────┐
     │ HBM │ underfill │ GPU │           │ HBM │
     └──┬──┘           └──┬──┘           └──┬──┘
   o  o  o  o  o  X  o  o  o  o  o  o  o  o   ◀ cracked bump (X)
  ──────────── interposer + substrate ──────────

  one scrap here wastes the most expensive work in the package
"##;

const SPOTS_55: &[Spot] = &[
    spot(
        "lid delamination",
        0,
        0,
        "The lid can lift from the stack, breaking the heat path.",
    ),
    spot(
        "void",
        0,
        TO_EOL,
        "Voids in underfill leave unsupported bumps and trap heat.",
    ),
    spot(
        "tilt",
        0,
        TO_EOL,
        "A tilted die breaks the flat contact the TIM and lid need.",
    ),
    spot(
        "cracked bump (X)",
        0,
        0,
        "Thermal cycling cracks bumps; the usual cause is expansion mismatch.",
    ),
    spot(
        "one scrap here",
        0,
        TO_EOL,
        "A B200 package pairs 208B transistors with 192 GB of HBM3E; scrapping it late wastes all of that.",
    ),
];

const ART_56: &str = r##"\
# Why filler size matters

  narrow microbump gap       ┃ ┃ ┃ ┃ ┃ ┃
  small filler flows         ┃·┃·┃·┃·┃·┃  ✔ fills without voids
  coarse filler jams         ┃●┃ ┃●┃ ┃●┃  ✕ voids

  epoxy mold compound + underfill makers: mostly Japanese (page)
  no share figures sourced

  in a liquid-cooled rack the lid becomes a cold plate
"##;

const SPOTS_56: &[Spot] = &[
    spot(
        "small filler flows",
        0,
        TO_EOL,
        "Filler must be small enough to flow through the narrow gaps between microbumps.",
    ),
    spot(
        "coarse filler jams",
        0,
        TO_EOL,
        "Too-big filler blocks the gap and leaves voids.",
    ),
    spot(
        "mostly Japanese",
        0,
        0,
        "The page says epoxy-compound and underfill makers are mostly Japanese (textbook, no share sourced).",
    ),
    spot(
        "lid becomes a cold plate",
        0,
        0,
        "In a liquid-cooled rack the lid doubles as a cold plate.",
    ),
];

const ART_57: &str = r##"\
# Heat leaves through the lid

       coolant in ──▶  ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈  ──▶ coolant out
    ┌────────────────────────────────────────────┐
    │ COLD PLATE (liquid cooled, in the rack)    │
    └────────────────────────────────────────────┘
    ┌────────────────────────────────────────────┐
    │ LID  spreads GPU and HBM hot spots         │
    └────────────────────────────────────────────┘
    ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ TIM ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
    ┌─────┐  ┌───────────┐  ┌───────────┐  ┌─────┐
    │ HBM │  │  GPU DIE  │  │  GPU DIE  │  │ HBM │
    └─────┘  └───────────┘  └───────────┘  └─────┘
"##;

const SPOTS_57: &[Spot] = &[
    spot(
        "COLD PLATE",
        0,
        0,
        "In an AI rack the lid carries liquid-cooled cold plates.",
    ),
    spot(
        "LID",
        0,
        0,
        "Spreads heat from the GPU and HBM hot spots to the cooling plate.",
    ),
    spot(
        "TIM",
        0,
        0,
        "Thermal interface material between the die backs and the lid.",
    ),
    spot("GPU DIE", 0, 0, "The hottest parts of the package."),
    spot(
        "HBM",
        0,
        0,
        "Memory stacks have their own, lower temperature limits.",
    ),
];

const ART_58: &str = r##"\
# Keeping the package flat

   ┌─────────────── LID ───────────────┐
   │   ┌───────────────────────────┐   │   stiffener ring (outer)
   │   │  dies + interposer        │   │
   └───┴───────────────────────────┴───┘
   ┌───────────────────────────────────┐
   │        ORGANIC SUBSTRATE          │   expands ~15-20 ppm/C
   └───────────────────────────────────┘

  lid + stiffener ring + underfill resist warpage
  GPU and HBM sit at different heights: the TIM must touch both

  (textbook; ppm figure from the FLIP ONTO card)
"##;

const SPOTS_58: &[Spot] = &[
    spot(
        "LID",
        0,
        0,
        "Its flatness and stiffness matter for the whole package.",
    ),
    spot(
        "stiffener ring",
        0,
        TO_EOL,
        "A metal ring that stiffens the substrate edge against warpage.",
    ),
    spot(
        "ORGANIC SUBSTRATE",
        0,
        0,
        "Expands about 15-20 ppm/C, several times more than silicon (textbook).",
    ),
    spot(
        "different heights",
        0,
        TO_EOL,
        "The TIM must be soft enough to contact dies of different heights.",
    ),
];

const ART_59: &str = r##"\
# Small part, bigger beneficiaries

  lid + stiffener     copper or alloys     minor cost item
                      precision-metal makers (none sourced)

  larger beneficiaries:
    liquid-cooling vendors in the rack

  (textbook, not sourced)
"##;

const SPOTS_59: &[Spot] = &[
    spot(
        "lid + stiffener",
        0,
        TO_EOL,
        "Metal parts from precision-metal makers; no sourced supplier data.",
    ),
    spot("minor cost item", 0, 0, "A small share of package cost."),
    spot(
        "liquid-cooling vendors",
        0,
        0,
        "The cold plates and loops in the rack are the larger cooling beneficiaries (textbook).",
    ),
];

const ART_60: &str = r##"\
# Why a TIM exists

  no TIM                         with TIM
  ┌────── LID ──────┐            ┌────── LID ──────┐
  └─────────────────┘            └─────────────────┘
   ░ ░ ░ air gaps ░ ░            ≈≈≈≈≈≈ TIM ≈≈≈≈≈≈
  ┌─────── DIE ─────┐            ┌─────── DIE ─────┐
  └─────────────────┘            └─────────────────┘

  air conducts heat poorly       TIM displaces the air
  types: grease, gel, metal pad, indium solder (textbook)
"##;

const SPOTS_60: &[Spot] = &[
    spot(
        "no TIM",
        0,
        TO_EOL,
        "Microscopic gaps between die and lid trap air, which conducts heat poorly.",
    ),
    spot(
        "with TIM",
        0,
        TO_EOL,
        "A thin layer displaces the air so heat can flow into the lid.",
    ),
    spot(
        "air gaps",
        0,
        0,
        "Even polished surfaces leave air-filled gaps.",
    ),
    spot(
        "types: grease",
        0,
        TO_EOL,
        "Greases, gels, and metal-based pads or indium solder (textbook).",
    ),
];

const ART_61: &str = r##"\
# One TIM over dies of different heights

   ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ LID underside ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
   ┌─────┐                                  ┌─────┐
   │ HBM │  ┌──────────────────┐            │ HBM │
   │     │  │     GPU DIE      │            │     │
   └─────┘  └──────────────────┘            └─────┘
   stack height limit: 720 um ──▶ 775 um (JEDEC, via Tom's Hardware)

   the TIM must be soft enough to touch both
"##;

const SPOTS_61: &[Spot] = &[
    spot(
        "HBM",
        0,
        0,
        "HBM stacks add height; JEDEC raised the limit from 720 to 775 um.",
    ),
    spot(
        "GPU DIE",
        0,
        0,
        "The compute die sits at a different height than the memory stacks.",
    ),
    spot(
        "720 um",
        0,
        TO_EOL,
        "The previous HBM stack height limit; raised to 775 um so HBM4 can keep microbumps (Tom's Hardware).",
    ),
    spot(
        "soft enough to touch both",
        0,
        0,
        "A stiff TIM would leave a gap over the shorter part.",
    ),
];

const ART_62: &str = r##"\
# Failure modes build up over years

  voids        ░ gaps in the layer      hot spots
  pump-out     material squeezed out    thinner layer, less cover
  delaminate   layer lifts off a die    heat path breaks

  slow degradation:
    not caught at test  ──▶  GPUs throttle in the field

  (mechanisms textbook; no suppliers or numbers sourced)
"##;

const SPOTS_62: &[Spot] = &[
    spot(
        "voids",
        0,
        TO_EOL,
        "Gaps in the TIM layer raise thermal resistance locally.",
    ),
    spot(
        "pump-out",
        0,
        TO_EOL,
        "Repeated heating and cooling squeezes material out of the gap.",
    ),
    spot(
        "delaminate",
        0,
        TO_EOL,
        "The layer separates from a die or the lid.",
    ),
    spot(
        "throttle in the field",
        0,
        0,
        "Because TIM degrades slowly, it shows up as throttled GPUs in service rather than at test.",
    ),
];

const ART_63: &str = r##"\
# Inside one HBM3E stack (B200: 24 GB)

     ┌──────────────┐
     │ DRAM die  8  │  each die thinned to tens of um
     │ DRAM die  7  │  joined by TSVs (copper vias)
     │  ...         │
     │ DRAM die  1  │
     ├──────────────┤
     │ BASE DIE     │  logic die under the stack
     └──o──o──o──o──┘  microbumps
   ═════ INTERPOSER ═════   1024-bit bus, ~1 TB/s per stack

  8 stacks x ~1 TB/s = about 8 TB/s;  8 x 24 GB = 192 GB
"##;

const SPOTS_63: &[Spot] = &[
    spot(
        "DRAM die  8",
        0,
        0,
        "The top DRAM die; 8 dies make a 24 GB stack in B200 (24 GB / 3 GB per die is simple arithmetic).",
    ),
    spot(
        "joined by TSVs",
        0,
        0,
        "Copper vias run through each thinned die so the stack behaves as one memory.",
    ),
    spot(
        "BASE DIE",
        0,
        0,
        "A logic die sits under the DRAM layers; in HBM4 it is made on a foundry logic process.",
    ),
    spot("microbumps", 0, 0, "Join the stack to the interposer."),
    spot(
        "1024-bit bus",
        0,
        TO_EOL,
        "Per stack about 1 TB/s (Tom's Hardware launch report).",
    ),
    spot(
        "8 stacks x",
        0,
        TO_EOL,
        "B200 carries 8 HBM3E stacks, 4 per GPU die, 192 GB and about 8 TB/s total.",
    ),
];

const ART_64: &str = r##"\
# HBM revenue share (Counterpoint)

  Q1 2026
    SK hynix  ████████████████████████████ 58%
    Samsung   ██████████ 21%
    Micron    ██████████ 21%
  Q2 2026
    SK hynix  █████████████████████████ 50%
    Samsung   ████████████████ 33%
    Micron    █████████ 18%

  2026 HBM sold out at SK hynix, Samsung; Micron mostly 2027
  HBM3E ~two-thirds of 2026 shipments; HBM4 ramps in 2H
"##;

const SPOTS_64: &[Spot] = &[
    spot(
        "SK hynix  ████████████████████████████",
        0,
        TO_EOL,
        "Counterpoint: 58% of HBM revenue in Q1 2026.",
    ),
    spot(
        "Samsung   ██████████ 21%",
        0,
        TO_EOL,
        "Samsung 21% in Q1 2026.",
    ),
    spot(
        "SK hynix  █████████████████████████",
        0,
        TO_EOL,
        "Counterpoint: 50% in Q2 2026, down from 64% a year earlier.",
    ),
    spot(
        "Samsung   ████████████████",
        0,
        TO_EOL,
        "Samsung rose to 33% in Q2 2026 as first HBM4 supplier to NVIDIA.",
    ),
    spot(
        "Micron    █████████ 18%",
        0,
        TO_EOL,
        "Micron fell to 18% from 21% the previous quarter.",
    ),
    spot(
        "sold out",
        0,
        TO_EOL,
        "SK hynix and Samsung say 2026 HBM is sold out; Micron says most of its 2027 HBM bits are contracted.",
    ),
];

const ART_65: &str = r##"\
# HBM3E to HBM4

               HBM3E              HBM4
  bus width    1024-bit           2048-bit
  pin speed    not given here     10-11.7 Gbps reported
  base die     not given here     foundry logic process

  pin speeds: SK hynix 10, Micron up to 11, Samsung 11.7 Gbps

  12-high 36 GB HBM4 stack, estimated price (Korean press)
    2026  ████████ ~$600
    2027  █████████████████ ~$1,300
"##;

const SPOTS_65: &[Spot] = &[
    spot(
        "bus width",
        0,
        TO_EOL,
        "HBM4 doubles the interface from 1024 to 2048 bits.",
    ),
    spot(
        "pin speed",
        0,
        TO_EOL,
        "Pin speeds of 10-11.7 Gbps are reported for HBM4.",
    ),
    spot(
        "base die",
        0,
        TO_EOL,
        "HBM4's base die is made on a foundry logic process.",
    ),
    spot(
        "pin speeds: SK hynix",
        0,
        TO_EOL,
        "SK hynix 10, Micron up to 11, Samsung 11.7 Gbps, as reported.",
    ),
    spot(
        "2026  ████████",
        0,
        TO_EOL,
        "Estimated near $600 for a 12-high 36 GB HBM4 stack in 2026 (Korean press).",
    ),
    spot(
        "2027  █████████████████",
        0,
        TO_EOL,
        "Estimated near $1,300 in 2027; these are press estimates.",
    ),
];

const ART_66: &str = r##"\
# One B200 compute die

    ┌──────────────────────────────────┐
    │ GPU DIE A                        │
    │ TSMC 4NP, ~104B transistors      │
    │ near the reticle limit           │
    │ faces DOWN onto the interposer   │
    └──────────────────────────────────┘
     o o o o o o o o o o o o o o o o   microbumps (die face)

  one reticle = the largest single exposure a scanner prints
  (node name varies by source: 4NP vs N4P)
"##;

const SPOTS_66: &[Spot] = &[
    spot(
        "GPU DIE A",
        0,
        0,
        "One of two Blackwell compute dies in a B200.",
    ),
    spot(
        "TSMC 4NP",
        0,
        TO_EOL,
        "Most sources say TSMC 4NP, a refined 4N; Guru3D writes N4P. About 104B transistors per die.",
    ),
    spot(
        "near the reticle limit",
        0,
        0,
        "Tom's Hardware says B200 uses two full-reticle-size chips.",
    ),
    spot(
        "faces DOWN",
        0,
        TO_EOL,
        "Flipped so the back-end metal stack meets the microbumps.",
    ),
    spot("microbumps", 0, 0, "Join the die to the interposer."),
];

const ART_67: &str = r##"\
# Past the reticle: add a die

  ┌───────────┐    ┌───────────┐
  │ GPU DIE A │    │ GPU DIE B │
  │ 104B tr   │ ◀▶ │ 104B tr   │
  └───────────┘    └───────────┘

   104B + 104B  =  208B transistors
   one die cannot grow past the scanner limit

   so: a second die, joined by a 10 TB/s link (NV-HBI)
   software sees one GPU

  (B200; die and link figures from the page and launch coverage)
"##;

const SPOTS_67: &[Spot] = &[
    spot(
        "GPU DIE A",
        0,
        0,
        "First compute die, about 104B transistors.",
    ),
    spot("GPU DIE B", 0, 0, "Second compute die, identical."),
    spot(
        "208B transistors",
        0,
        0,
        "Two dies of about 104B each (Guru3D); the H100 had 80B.",
    ),
    spot(
        "one die cannot grow",
        0,
        TO_EOL,
        "Each die is already near the reticle limit, so more compute needs more dies.",
    ),
    spot(
        "10 TB/s link",
        0,
        0,
        "NV-HBI joins the two dies so software sees one GPU.",
    ),
];

const ART_68: &str = r##"\
# B200 package, totals

  transistors       ████████████████████████████████████ 208B
  HBM3E capacity    ████████████████████████ 192 GB
  memory bandwidth  ████████████████ ~8 TB/s
  die-to-die link   ████████████████████ 10 TB/s

  big-die yield: one defect scraps the die  ──▶  sort first (PICK)
  one packaging line gates Nvidia, AMD and custom ASICs

  (bars are not on a common scale)
"##;

const SPOTS_68: &[Spot] = &[
    spot("transistors", 0, TO_EOL, "208B across two dies."),
    spot(
        "HBM3E capacity",
        0,
        TO_EOL,
        "192 GB from eight 24 GB stacks.",
    ),
    spot(
        "memory bandwidth",
        0,
        TO_EOL,
        "About 8 TB/s from eight stacks.",
    ),
    spot("die-to-die link", 0, TO_EOL, "NV-HBI at about 10 TB/s."),
    spot(
        "big-die yield",
        0,
        TO_EOL,
        "A defect anywhere on a near-reticle die scraps it, so dies are sorted before packaging.",
    ),
    spot(
        "one packaging line",
        0,
        TO_EOL,
        "The page notes one company's packaging lines gate Nvidia, AMD and custom ASIC output.",
    ),
];

const ART_69: &str = r##"\
# Two dies, one logical GPU

   ┌──────────┐   NV-HBI ~10 TB/s   ┌──────────┐
   │ GPU DIE A│◀═══════════════════▶│ GPU DIE B│
   └────┬─────┘                     └─────┬────┘
        o   o   o   o   o   o   o   o   o   o
  ═══ RDL layers / LSI bridge in CoWoS-L ═══════

  software sees one GPU

  (10 TB/s figure from the page and launch coverage)
"##;

const SPOTS_69: &[Spot] = &[
    spot("GPU DIE A", 0, 0, "First compute die."),
    spot("GPU DIE B", 0, 0, "Second compute die."),
    spot(
        "NV-HBI",
        0,
        0,
        "Nvidia High-Bandwidth Interface: about 10 TB/s aggregate between the two dies.",
    ),
    spot(
        "RDL layers",
        0,
        TO_EOL,
        "The link runs through micrometre-pitch wiring layers; in CoWoS-L, across local silicon bridges.",
    ),
    spot(
        "software sees one GPU",
        0,
        0,
        "The link is fast enough that the two dies act as one logical device.",
    ),
];

const ART_70: &str = r##"\
# 10 TB/s is above memory bandwidth

  HBM to GPU (8 stacks)  ████████████████████████████ ~8 TB/s
  NV-HBI die to die      ███████████████████████████████████ 10 TB/s

  slow link  ──▶  behaves like two chips  ──▶  efficiency drops
  reticle limit (~800 mm2) caps one die: more compute = more dies

  (figures from the page)
"##;

const SPOTS_70: &[Spot] = &[
    spot("HBM to GPU", 0, TO_EOL, "About 8 TB/s from eight stacks."),
    spot(
        "NV-HBI die to die",
        0,
        TO_EOL,
        "About 10 TB/s, above memory bandwidth, so the dies can behave as one.",
    ),
    spot(
        "slow link",
        0,
        TO_EOL,
        "If the link were slow, software would see two separate chips and efficiency would drop.",
    ),
    spot(
        "reticle limit",
        0,
        TO_EOL,
        "Reticle limits cap one die near 800 mm2.",
    ),
];

const ART_71: &str = r##"\
# CoWoS-L carries the link

   [GPU]──[LSI bridge]──[GPU]      LSI = small silicon bridge
   ═══ RDL (organic) ═══════════
   only the bridges are silicon

  beyond ~3.3x reticle (CoWoS-S limit): CoWoS-L
  yield drivers: bridge alignment, warpage
  same bridge technology carries Rubin's multi-die layout

  (textbook yield drivers; Tickers: NVDA, TSM)
"##;

const SPOTS_71: &[Spot] = &[
    spot(
        "LSI bridge",
        0,
        0,
        "A small silicon bridge placed where die-to-die traffic needs micrometre-pitch wiring.",
    ),
    spot(
        "only the bridges are silicon",
        0,
        0,
        "The rest of the interposer is RDL, which lets area scale past the reticle.",
    ),
    spot(
        "3.3x reticle",
        0,
        0,
        "The CoWoS-S maximum; beyond it TSMC points to CoWoS-L.",
    ),
    spot(
        "bridge alignment",
        0,
        TO_EOL,
        "Alignment and warpage control drive yield; a failed link scraps the assembly (textbook).",
    ),
    spot(
        "Rubin",
        0,
        0,
        "The page says the same bridge technology carries Rubin's multi-die layout.",
    ),
];

const ART_72: &str = r##"\
# Two levels of TSVs

  inside the HBM stack          inside the interposer

   microbump                     DRAM / GPU microbumps
      o                           o   o   o   o
   ┌──┼───┐ DRAM die            ┌───┼───┼───┼───┼──┐
   │  Cu  │                     │   Cu  Cu  Cu  Cu │ interposer
   ├──┼───┤                     └───┼───┼───┼───┼──┘
   │  Cu  │ next die                o   o   o   o
   └──┼───┘                         C4 bumps below

  12 layers act as one memory    power + signals pass through
"##;

const SPOTS_72: &[Spot] = &[
    spot(
        "inside the HBM stack",
        0,
        TO_EOL,
        "TSVs run through each thinned DRAM die so the layers act as one memory.",
    ),
    spot(
        "inside the interposer",
        0,
        TO_EOL,
        "TSVs carry power and signals from the top microbumps to the underside C4 bumps.",
    ),
    spot(
        "DRAM die",
        0,
        0,
        "Each die is thinned to tens of um and pierced by TSVs.",
    ),
    spot(
        "interposer",
        1,
        0,
        "A passive silicon slab with TSVs but no transistors.",
    ),
    spot(
        "C4 bumps below",
        0,
        0,
        "The coarser bumps that join the interposer module to the organic substrate.",
    ),
];

const ART_73: &str = r##"\
# Five steps

  ┌───────────┐    ┌─────────────────┐    ┌────────┐
  │ ETCH      │    │ LINE            │    │ FILL   │
  │ deep hole │ ─▶ │ oxide + barrier │ ─▶ │ copper │
  └───────────┘    └─────────────────┘    └────────┘

  ┌────────────┐    ┌──────────┐
  │ THIN       │    │ EXPOSE   │
  │ grind back │ ─▶ │ via tips │
  └────────────┘    └──────────┘

  interposer: no transistors, so TSV density is the constraint
  (process per the page; textbook)
"##;

const SPOTS_73: &[Spot] = &[
    spot(
        "ETCH",
        0,
        0,
        "A deep narrow hole is etched through the silicon.",
    ),
    spot(
        "LINE",
        0,
        0,
        "The hole is lined with oxide and a barrier layer.",
    ),
    spot(
        "FILL",
        0,
        0,
        "Copper fills the hole; voids here are a main risk.",
    ),
    spot("THIN", 0, 0, "The wafer is ground thin from the back."),
    spot(
        "EXPOSE",
        0,
        0,
        "Grinding continues until the via tips show on the back side.",
    ),
    spot(
        "TSV density",
        0,
        0,
        "In an interposer TSV density limits how many signals reach the substrate.",
    ),
];

const ART_74: &str = r##"\
# What goes wrong, and who benefits

  copper void         ░ in the via        open circuit
  Cu-Si stress        ╱ crack in silicon  hidden damage
  thinning breakage   ▒ wafer too thin    scrapped wafer

  more layers  ──▶  more chances for one bad die to kill the stack
    12-high now, 16-high next

  benefit: DRAM makers with good yield; etch + plating tools
"##;

const SPOTS_74: &[Spot] = &[
    spot(
        "copper void",
        0,
        TO_EOL,
        "Gaps in the copper fill break the connection.",
    ),
    spot(
        "Cu-Si stress",
        0,
        TO_EOL,
        "Copper and silicon expand differently; stress can crack the silicon.",
    ),
    spot(
        "thinning breakage",
        0,
        TO_EOL,
        "Thin wafers break during grinding and handling.",
    ),
    spot(
        "more layers",
        0,
        TO_EOL,
        "Each added HBM layer multiplies the chance that one bad die scraps the whole stack.",
    ),
    spot(
        "etch + plating tools",
        0,
        0,
        "Deep-etch and plating tool vendors benefit from TSV volume (textbook).",
    ),
];

const ART_75: &str = r##"\
# Connection pitch, micrometres (smaller is denser)

  old microbump          ████████████████████████████████████████ ~40
  volume standard        █████████████████████████ ~25
  latest memory          ██████████ ~10
  hybrid bonding today   ██████ ~6
  TSMC ask (2H 2028 est) █████ ~5 class
  hybrid bonding next    ████ 4.5  then  ███ 3

  smaller pitch: more connections per mm2, more bandwidth
  but more bridging and void risk
"##;

const SPOTS_75: &[Spot] = &[
    spot(
        "old microbump",
        0,
        TO_EOL,
        "About 40 um pitch historically.",
    ),
    spot(
        "volume standard",
        0,
        TO_EOL,
        "A volume standard cited near 25 um.",
    ),
    spot(
        "latest memory",
        0,
        TO_EOL,
        "About 10 um on the latest memory.",
    ),
    spot(
        "hybrid bonding today",
        0,
        TO_EOL,
        "About 6 um pitch now, copper to copper with no bump.",
    ),
    spot(
        "TSMC ask",
        0,
        TO_EOL,
        "TSMC reportedly asked partners for roughly 5 um class bumps, mass production estimated for 2H 2028 (TrendForce).",
    ),
    spot(
        "hybrid bonding next",
        0,
        TO_EOL,
        "4.5 um and then 3 um are coming.",
    ),
];

const ART_76: &str = r##"\
# Bump vs bump-free

  with microbumps              hybrid bonding
   ┌─────┐                      ┌─────┐
   │ DIE │                      │ DIE │
   └─o─o─┘ solder bumps         └─┬─┬─┘ Cu pad to Cu pad
   ░░░░░░░ underfill gap        ═════════ no gap, no bump
   ┌─────┐                      ┌─┴─┴─┐
   │DIE 2│                      │DIE 2│
   └─────┘                      └─────┘

  lower stack height + lower thermal resistance: 16-high HBM4E
  tools: BESI (BESI.AS) + Applied; TC bonders ASMPT, Hanmi
"##;

const SPOTS_76: &[Spot] = &[
    spot(
        "with microbumps",
        0,
        TO_EOL,
        "Solder-capped copper pillars with an underfill gap between layers.",
    ),
    spot(
        "hybrid bonding",
        0,
        TO_EOL,
        "Copper pads bond directly, no solder.",
    ),
    spot(
        "no gap, no bump",
        0,
        0,
        "Removing the bump and underfill gap cuts stack height and thermal resistance.",
    ),
    spot(
        "16-high HBM4E",
        0,
        0,
        "Lower stack height matters most for 16-high stacks.",
    ),
    spot(
        "BESI (BESI.AS)",
        0,
        0,
        "BESI with Applied Materials is the key hybrid bonder supplier; ASMPT (0522.HK) and Hanmi (042700.KS) lead TC bonders today.",
    ),
];

const ART_77: &str = r##"\
# Why spacing matters

    o   o   o   o        epoxy flows in between by capillary action
    ░░░░░░░░░░░░░░░
    o   o   o   o        gap too small: voids, bridging
    ░░░░░░░░░░░░░░░       gap big enough: full fill

  HBM stack height limit: 720 um ──▶ 775 um (JEDEC)
  so HBM4 can keep microbumps instead of switching to hybrid bonding

  bonder throughput and yield cap HBM supply as much as DRAM wafers
"##;

const SPOTS_77: &[Spot] = &[
    spot(
        "capillary action",
        0,
        0,
        "Underfill epoxy wicks between bumps, so gaps must be large enough.",
    ),
    spot(
        "gap too small",
        0,
        TO_EOL,
        "Bridging and voids rise as pitch shrinks.",
    ),
    spot(
        "720 um",
        0,
        TO_EOL,
        "JEDEC raised the HBM stack height limit from 720 to 775 um so HBM4 can retain microbumps.",
    ),
    spot(
        "bonder throughput",
        0,
        TO_EOL,
        "Bonder throughput and yield cap HBM supply as much as DRAM wafers do.",
    ),
];

const ART_78: &str = r##"\
# Coarser joints under the interposer

  ┌──────────────────────────────────────────────┐
  │ INTERPOSER MODULE (GPU + HBM on silicon)     │
  └──────────────────────────────────────────────┘
    o    o    o    o    o    o    o    o    C4 ~100-150 um
  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  underfill #2
  ┌──────────────────────────────────────────────┐
  │ ORGANIC SUBSTRATE                            │
  └──────────────────────────────────────────────┘

  microbumps ~10-40 um above;  C4 ~100-150 um here (textbook)
  pitch relaxes because the substrate cannot hold fine wiring
"##;

const SPOTS_78: &[Spot] = &[
    spot(
        "INTERPOSER MODULE",
        0,
        0,
        "The diced interposer with GPU and HBM already mounted.",
    ),
    spot(
        "C4 ~100-150 um",
        0,
        TO_EOL,
        "Roughly 100-150 um class pitch (textbook), much coarser than microbumps.",
    ),
    spot(
        "underfill #2",
        0,
        TO_EOL,
        "The second underfill step protects the C4 joints.",
    ),
    spot(
        "ORGANIC SUBSTRATE",
        0,
        0,
        "Cannot hold micrometre-scale wiring, so the pitch must relax at this level.",
    ),
    spot(
        "pitch relaxes",
        0,
        TO_EOL,
        "Fine wiring is possible only in silicon; the substrate fans out to coarser pitch.",
    ),
];

const ART_79: &str = r##"\
# Bumps fail at the edge first

   heat ▲   Si: ~3 ppm/C      organic: 15-20 ppm/C

   ┌──────────────────────────────┐
   │      INTERPOSER MODULE       │
   └─X──o──o──o──o──o──o──o──o──X─┘   X = corner joints: most shear
   ┌──────────────────────────────┐
   │ ORGANIC SUBSTRATE (expands +)│
   └──────────────────────────────┘

  larger interposer  =  more shear  =  more cracks
  mitigation: underfill #2, stiffener ring, lid
"##;

const SPOTS_79: &[Spot] = &[
    spot(
        "Si: ~3 ppm/C",
        0,
        TO_EOL,
        "Silicon expands about 3 ppm per degree C.",
    ),
    spot(
        "X = corner joints",
        0,
        TO_EOL,
        "Corner joints are furthest from the centre, so they take the most shear.",
    ),
    spot(
        "expands +",
        0,
        0,
        "The substrate expands about 15-20 ppm/C, several times more than silicon.",
    ),
    spot(
        "larger interposer",
        0,
        TO_EOL,
        "Larger interposers worsen the mismatch.",
    ),
    spot(
        "mitigation",
        0,
        TO_EOL,
        "Second underfill, stiffener ring and lid reduce the stress.",
    ),
];

const ART_80: &str = r##"\
# Late failure, big loss

  cracked C4 joint  ──▶  the finished GPU + HBM assembly is scrapped

  yield risk grows as packages pass 3x reticle

  materials: underfill and bump chemistry mostly from Japanese
             specialty makers (no share sourced)

  tickers touching this step:  TSM   ASX   AMKR
"##;

const SPOTS_80: &[Spot] = &[
    spot(
        "cracked C4 joint",
        0,
        TO_EOL,
        "A failure here scraps the already assembled GPU and HBM.",
    ),
    spot(
        "3x reticle",
        0,
        0,
        "Warpage and cracked joints are a top yield risk beyond about 3x reticle.",
    ),
    spot(
        "Japanese",
        0,
        0,
        "Underfill and bump materials come mostly from Japanese specialty makers; no share sourced.",
    ),
    spot(
        "tickers touching",
        0,
        TO_EOL,
        "TSMC (TSM) and the OSATs ASE (ASX) and Amkor (AMKR).",
    ),
];

const ART_81: &str = r##"\
# Build-up layers

  ═════════════════════════  top: C4 pitch, ~100-150 um
  ═════ + plated vias ═════  fans the wiring out
  ═════ power planes ══════
  ═══ glass-cloth core ═══   T-glass (low expansion)
  ═════════════════════════  bottom: BGA, ~1 mm
  ▒ decoupling caps on the underside

  insulation: ABF film (Ajinomoto Build-up Film)
  one AI chip uses ~10x the ABF of a PC chip (Counterpoint)
"##;

const SPOTS_81: &[Spot] = &[
    spot(
        "top: C4 pitch",
        0,
        TO_EOL,
        "The top of the substrate matches the fine C4 pitch of the interposer module.",
    ),
    spot(
        "power planes",
        0,
        TO_EOL,
        "Carry the large currents AI packages need.",
    ),
    spot(
        "glass-cloth core",
        0,
        TO_EOL,
        "Low-expansion T-glass cloth gives the board its stiffness and stability.",
    ),
    spot(
        "bottom: BGA",
        0,
        TO_EOL,
        "The underside meets the coarse BGA pitch of the board or socket.",
    ),
    spot(
        "~10x the ABF",
        0,
        0,
        "Counterpoint: a single AI chip uses roughly 10x more ABF material than a PC chip.",
    ),
];

const ART_82: &str = r##"\
# Two shortages (Counterpoint, Mar 2026)

  ABF substrate supply gap   ████████████████████ ~20%
  T-glass supply gap         ██████████ 10%+

  Nittobo (3110.T): ~70% of ABF-grade glass cloth
     investing 150 billion yen to triple capacity

  relief: not before late 2026;  full impact 2027
  new greenfield substrate capacity: 2027
  a missing substrate stops a finished GPU shipping
"##;

const SPOTS_82: &[Spot] = &[
    spot(
        "ABF substrate supply gap",
        0,
        TO_EOL,
        "Counterpoint sees about a 20% gap, with new greenfield capacity not arriving until 2027.",
    ),
    spot(
        "T-glass supply gap",
        0,
        TO_EOL,
        "A 10%+ gap in low-expansion glass cloth.",
    ),
    spot(
        "Nittobo",
        0,
        TO_EOL,
        "Supplies about 70% of ABF-grade cloth and is investing 150 billion yen to triple capacity.",
    ),
    spot(
        "relief:",
        0,
        TO_EOL,
        "Not expected before late 2026, with full impact in 2027.",
    ),
    spot(
        "a missing substrate",
        0,
        TO_EOL,
        "A finished GPU cannot ship without its substrate.",
    ),
];

const ART_83: &str = r##"\
# From film to board

  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐
  │ AJINOMOTO    │    │ NITTOBO         │    │ IBIDEN, UNIMICRON │
  │ 2802.T  film │ ─▶ │ 3110.T  T-glass │ ─▶ │ 4062.T  3037.TW   │
  └──────────────┘    └─────────────────┘    └───────────────────┘

  Unimicron's chairman: AI PCBs pass smartphone PCBs by 2029
  no sourced capacity or share for Ibiden

  watch: panel-level packaging, glass cores (not sourced)
"##;

const SPOTS_83: &[Spot] = &[
    spot("AJINOMOTO", 0, 0, "Makes the ABF film insulation."),
    spot(
        "NITTOBO",
        0,
        0,
        "Glass-cloth supplier; about 70% of ABF-grade cloth.",
    ),
    spot(
        "IBIDEN, UNIMICRON",
        0,
        0,
        "Substrate makers: Ibiden (4062.T), Unimicron (3037.TW) and others.",
    ),
    spot(
        "Unimicron's chairman",
        0,
        TO_EOL,
        "Expects AI-application PCBs to pass smartphone PCBs in value by 2029.",
    ),
    spot(
        "glass cores",
        0,
        0,
        "Panel-level packaging and glass cores (not sourced) would change the vendor map if adopted.",
    ),
];

const ART_84: &str = r##"\
# CoWoS-S vs CoWoS-L

  CoWoS-S: one full silicon interposer (up to 3.3x reticle)
   ┌───────────────────────────────────┐
   │ GPU      GPU      HBM      HBM    │ all on silicon
   └───────────────────────────────────┘

  CoWoS-L: RDL + local silicon bridges only where needed
   [GPU]═[LSI]═[GPU]    [HBM]   [HBM]      RDL elsewhere
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

  area can exceed 3.3x reticle: Blackwell Ultra and Rubin
"##;

const SPOTS_84: &[Spot] = &[
    spot(
        "CoWoS-S",
        1,
        TO_EOL,
        "One full silicon interposer, limited to about 3.3x reticle, about 2,700 mm2.",
    ),
    spot(
        "all on silicon",
        0,
        0,
        "Every wire sits on silicon, which caps the size.",
    ),
    spot(
        "CoWoS-L",
        1,
        TO_EOL,
        "Swaps the full interposer for RDL plus small local silicon interconnect bridges.",
    ),
    spot(
        "LSI",
        0,
        0,
        "Local silicon interconnect: a small bridge only where die-to-die wiring is dense.",
    ),
    spot(
        "3.3x reticle",
        0,
        0,
        "CoWoS-L lets packages exceed this limit; an ECTC paper shows ~3x reticle with 8 HBM.",
    ),
    spot(
        "Blackwell Ultra and Rubin",
        0,
        0,
        "The page says both depend on CoWoS-L.",
    ),
];

const ART_85: &str = r##"\
# End-2026 CoWoS capacity, thousand wafers per month (estimates)

  end-2025 (est.)         ████████████████ ~80
  TSMC total, Morgan Stanley   ██████████████████ 90-95
  CoWoS-L only (same source)   █████████████ ~68
  TrendForce, Jun 2026         ████████████████████████ 120-140
  OSAT add (TrendForce)        ██████████ 50-60

  TSMC does not disclose; all figures are third-party estimates
  capex (Jan 2026 report): ~$56B, partly to double CoWoS
"##;

const SPOTS_85: &[Spot] = &[
    spot(
        "end-2025",
        0,
        TO_EOL,
        "Roughly 80k wafers per month at the end of 2025 (estimate).",
    ),
    spot(
        "TSMC total, Morgan Stanley",
        0,
        TO_EOL,
        "90-95k wafers in 2026, via a news summary; secondary.",
    ),
    spot(
        "CoWoS-L only",
        0,
        TO_EOL,
        "About 68k of that total is CoWoS-L, same summary.",
    ),
    spot(
        "TrendForce, Jun 2026",
        0,
        TO_EOL,
        "TrendForce puts end-2026 at 120-140k wafers per month.",
    ),
    spot(
        "OSAT add",
        0,
        TO_EOL,
        "Outsourced assembly houses are estimated to add 50-60k.",
    ),
    spot(
        "TSMC does not disclose",
        0,
        TO_EOL,
        "All capacity figures are third-party estimates.",
    ),
];

const ART_86: &str = r##"\
# Who needs it

  Nvidia share of 2026 allocation (est.)   ██████████████████ 50-60%
  Morgan Stanley (summary)                 ████████████████████ ~66%

  KGI: most of 2027 expansion = CoWoS-L (Nvidia, Broadcom)
  TSMC CoWoS CAGR above 80%, 2022-2027 (symposium, May 2026)

  risks: bridge alignment, warpage, yield on large packages
  tickers: TSM  NVDA  AVGO
"##;

const SPOTS_86: &[Spot] = &[
    spot(
        "Nvidia share",
        0,
        TO_EOL,
        "Estimated at 50-60% of 2026 allocation.",
    ),
    spot(
        "Morgan Stanley (summary)",
        0,
        TO_EOL,
        "Another summary puts Nvidia near 66% of 2026 CoWoS demand; sources differ.",
    ),
    spot(
        "KGI:",
        0,
        TO_EOL,
        "KGI expects most of the 2027 expansion to be CoWoS-L, benefiting Nvidia and Broadcom.",
    ),
    spot(
        "TSMC CoWoS CAGR",
        0,
        TO_EOL,
        "The page cites above 80% CAGR from 2022 to 2027 (TSMC symposium, May 2026).",
    ),
    spot(
        "risks:",
        0,
        TO_EOL,
        "Bridge alignment, warpage and yield on large packages.",
    ),
];

const ART_87: &str = r##"\
# Demand above supply

  now      demand ██████████████████████████ 100
           supply ████████████████████ ~80    gap ~20%
  end-2026 supply ███████████████████████ ~90  gap ~10% (TrendForce)

  TSMC allocates: Nvidia ~50-60%, then AMD, Broadcom, custom ASICs
  smaller customers wait

  global demand: ~1.3-1.4M wafers (2026) ──▶ 2.5-2.7M (2027)
  (gap bars are drawn from the percentages, not measured data)
"##;

const SPOTS_87: &[Spot] = &[
    spot("demand ████", 0, TO_EOL, "The index: demand set to 100."),
    spot(
        "supply ████████████████████ ~80",
        0,
        TO_EOL,
        "TrendForce puts the supply gap near 20% now.",
    ),
    spot(
        "end-2026 supply",
        0,
        TO_EOL,
        "The gap may narrow to about 10% by end-2026.",
    ),
    spot(
        "TSMC allocates",
        0,
        TO_EOL,
        "With demand above supply, TSMC allocates among Nvidia, AMD, Broadcom and custom ASIC customers.",
    ),
    spot(
        "global demand",
        0,
        TO_EOL,
        "One summary projects demand doubling from 1.3-1.4M wafers in 2026 to 2.5-2.7M in 2027, so the gap does not close on its own.",
    ),
];

const ART_88: &str = r##"\
# End-2026 CoWoS forecasts, thousand wafers per month

  TrendForce, Dec 2024   ██████████████████ 90
  JPM, Sep 2025          ███████████████████ 95
  36Kr                   ████████████████████████ ~120
  equipment view         █████████████████████████ 127
  TrendForce, Jun 2026   ██████████████████████████████ 120-140
  incl. OSAT partners    ████████████████████████████████████████ ~200

  from ~80k at end-2025;  all are estimates, not TSMC disclosures
"##;

const SPOTS_88: &[Spot] = &[
    spot(
        "TrendForce, Dec 2024",
        0,
        TO_EOL,
        "An early forecast of 90k for end-2026.",
    ),
    spot("JPM, Sep 2025", 0, TO_EOL, "95k."),
    spot("36Kr", 0, TO_EOL, "About 120k."),
    spot(
        "equipment view",
        0,
        TO_EOL,
        "127k from an equipment-based estimate.",
    ),
    spot(
        "TrendForce, Jun 2026",
        0,
        TO_EOL,
        "120-140k wafers per month.",
    ),
    spot(
        "incl. OSAT partners",
        0,
        TO_EOL,
        "Industry total could approach 200k including OSAT partners.",
    ),
];

const ART_89: &str = r##"\
# Output follows the scarcest input

  need       ██████████████ 100
  CoWoS      ███████████ ~80  (gap ~20%)
  HBM        ████████████  sold out for 2026
  ABF        ███████████ ~80  (gap ~20%)

  GPU out  =  min( CoWoS, HBM, ABF )

  lead times 36-52 weeks (secondary, unverified)
  tickers: TSM  ASX  AMKR  MU  000660.KS

  (illustrative; estimates only, not company data)
"##;

const SPOTS_89: &[Spot] = &[
    spot(
        "CoWoS      ",
        0,
        TO_EOL,
        "About a 20% supply gap (TrendForce).",
    ),
    spot(
        "HBM        ",
        0,
        TO_EOL,
        "SK hynix and Samsung say 2026 HBM is sold out; Micron says most of its 2027 bits are contracted.",
    ),
    spot(
        "ABF        ",
        0,
        TO_EOL,
        "Counterpoint sees about a 20% ABF substrate gap.",
    ),
    spot(
        "GPU out",
        0,
        TO_EOL,
        "Shipments follow the scarcest of the three, so revenue timing tracks packaging output.",
    ),
    spot(
        "lead times",
        0,
        TO_EOL,
        "A secondary source cites 36-52 weeks; unverified.",
    ),
];

const ART_90: &str = r##"\
# 2024 OSAT revenue, $B (TrendForce)

  ASE (ASX)    ████████████████████████████████████████ 18.54
  Amkor (AMKR) ██████████████ 6.32
  JCET         ███████████ 5.0

  top-10 total $41.56B (+3%);  ASE ~45%,  JCET ~12%
  JCET +19.3%, Amkor -2.8% YoY; Chinese firms grew double digits
  others: Tongfu 8%, Powertech 5.5%, HT-Tech 4.8%, WiseRoad 3.7%
"##;

const SPOTS_90: &[Spot] = &[
    spot(
        "ASE (ASX)",
        0,
        TO_EOL,
        "$18.54B in 2024, about 45% of the top-10 total.",
    ),
    spot(
        "Amkor (AMKR)",
        0,
        TO_EOL,
        "$6.32B, down 2.8% year over year.",
    ),
    spot(
        "JCET",
        0,
        TO_EOL,
        "$5.0B, up 19.3%, about 12% of the top-10 total.",
    ),
    spot("top-10 total", 0, TO_EOL, "$41.56B, up 3%."),
    spot(
        "others:",
        0,
        TO_EOL,
        "Other shares in the 2024 top-10: Tongfu 8%, Powertech 5.5%, HT-Tech 4.8%, WiseRoad 3.7%, Hana Micron 2.2%, KYEC 2.2%, ChipMOS 1.7%.",
    ),
];

const ART_91: &str = r##"\
# Where the OSATs take over

  ┌──────────────────┐    ┌────────────────────┐    ┌──────────┐
  │ TSMC             │    │ ASE / SPIL, AMKR   │    │ SHIP     │
  │ interposer + CoW │ ─▶ │ on-substrate, test │ ─▶ │ to board │
  └──────────────────┘    └────────────────────┘    └──────────┘

  OSAT CoWoS-type add, 2026:  50-60k wafers/month (TrendForce)
                              40k (an equipment view)

  no sourced 2026 advanced-packaging revenue for ASE or Amkor
  use company filings for current figures
"##;

const SPOTS_91: &[Spot] = &[
    spot(
        "TSMC",
        0,
        0,
        "Keeps the interposer and chip-on-wafer steps.",
    ),
    spot(
        "ASE / SPIL, AMKR",
        0,
        0,
        "Take overflow on-substrate (oS) and back-end work; SPIL is part of ASE.",
    ),
    spot(
        "OSAT CoWoS-type add",
        0,
        TO_EOL,
        "TrendForce estimates 50-60k wafers per month in 2026.",
    ),
    spot(
        "40k (an equipment view)",
        0,
        0,
        "A lower estimate from an equipment-based view.",
    ),
    spot(
        "no sourced 2026",
        0,
        TO_EOL,
        "No sourced 2026 advanced-packaging revenue was found for ASE or Amkor.",
    ),
];

const ART_92: &str = r##"\
# Three ways to hold the packaging squeeze

  ASE (ASX)     largest OSAT        volume gain while CoWoS is short
  Amkor (AMKR)  US-listed           US fab plans (textbook)
  JCET          600584.SS           geopolitical risk

  OSAT margins are lower than TSMC's
  but volume rises while CoWoS capacity is short

  (investor framing is textbook; not advice)
"##;

const SPOTS_92: &[Spot] = &[
    spot(
        "ASE (ASX)",
        0,
        TO_EOL,
        "The largest OSAT, so the largest exposure.",
    ),
    spot(
        "Amkor (AMKR)",
        0,
        TO_EOL,
        "US-listed with US fab plans (textbook).",
    ),
    spot(
        "JCET",
        0,
        TO_EOL,
        "A Chinese name, so it carries geopolitical risk.",
    ),
    spot(
        "OSAT margins",
        0,
        TO_EOL,
        "Lower than TSMC's, offset by volume while CoWoS is short.",
    ),
];

const ART_93: &str = r##"\
# One Bianca board

  ┌──────┐    ┌───────┐    ┌──────┐
  │ B200 │    │ GRACE │    │ B200 │
  │ GPU  │ ◀▶ │ CPU   │ ◀▶ │ GPU  │
  └──────┘    └───────┘    └──────┘
          NVLink-C2C 900 GB/s per superchip

  1 board = 2 B200 + 1 Grace
  1 tray  = 2 boards = 4 GPUs + 2 CPUs

  (counts from SemiAnalysis and NVIDIA's DGX GB200 guide)
"##;

const SPOTS_93: &[Spot] = &[
    spot(
        "B200",
        0,
        0,
        "A Blackwell GPU package: two dies and eight HBM3E stacks.",
    ),
    spot(
        "GRACE",
        0,
        0,
        "Nvidia's Arm CPU, with its own memory on the board.",
    ),
    spot(
        "NVLink-C2C",
        0,
        TO_EOL,
        "The chip-to-chip link between Grace and Blackwell, 900 GB/s per Grace-Blackwell superchip.",
    ),
    spot(
        "1 board",
        0,
        TO_EOL,
        "The Bianca board carries 2 B200 GPUs and 1 Grace CPU.",
    ),
    spot(
        "1 tray",
        0,
        TO_EOL,
        "A tray holds two boards: 4 GPUs and 2 CPUs.",
    ),
];

const ART_94: &str = r##"\
# Late in the chain, an expensive loss

   ┌──────────────────────┐
   │  GPU PACKAGE (large) │   warps when hot
   └─o──o──o──o──o──o──o──┘
   ═══ BOARD pads + solder ═══   solder joint problems

  failed package or joint  ──▶  the whole GPU is wasted
  final-test screening pays for itself here

  (warpage and solder issues are textbook failure signs)
"##;

const SPOTS_94: &[Spot] = &[
    spot(
        "GPU PACKAGE",
        0,
        0,
        "A very large package that warps when hot.",
    ),
    spot(
        "solder joint problems",
        0,
        0,
        "A bad solder joint at board attach wastes a finished GPU.",
    ),
    spot(
        "the whole GPU is wasted",
        0,
        0,
        "The GPU is the most expensive part on the board, so board-level yield matters.",
    ),
    spot(
        "final-test screening",
        0,
        TO_EOL,
        "Screening on the FINAL TEST page keeps bad packages off the board.",
    ),
];

const ART_95: &str = r##"\
# What gates the board step

  ┌───────────┐    ┌────────┐    ┌────────────┐
  │ CoWoS     │    │ HBM    │    │ BOARD      │
  │ packaging │ ─▶ │ supply │ ─▶ │ ODM mounts │
  └───────────┘    └────────┘    └────────────┘

  NVIDIA: GPU + board design
  ODMs:   Foxconn, Quanta, Wistron mount the boards

  chokepoints upstream: CoWoS output, then HBM supply
"##;

const SPOTS_95: &[Spot] = &[
    spot(
        "CoWoS",
        0,
        0,
        "Packaging capacity at TSMC and its partners.",
    ),
    spot(
        "HBM",
        0,
        0,
        "Memory supply from SK hynix, Samsung and Micron.",
    ),
    spot(
        "BOARD",
        0,
        0,
        "Where ODMs mount the packaged GPU on a compute board.",
    ),
    spot(
        "NVIDIA: GPU",
        0,
        TO_EOL,
        "NVIDIA supplies the GPU and the board design.",
    ),
    spot(
        "ODMs:",
        0,
        TO_EOL,
        "Foxconn, Quanta and Wistron are named ODMs.",
    ),
];

const ART_96: &str = r##"\
# Inside one 1U compute tray

  ┌──────────────────────────────────────────────────────────┐
  │ BOARD 1  2 B200 + 1 Grace      BOARD 2  2 B200 + 1 Grace │
  │ NICs          cold plates on the chips                   │
  │ power connections     quick-disconnect fittings (liquid) │
  └──────────────────────────────────────────────────────────┘

  4 GPUs + 2 CPUs per tray
  liquid cooled: HPE says NVL72 needs it

  (layout schematic; counts from SemiAnalysis, NVIDIA DGX guide)
"##;

const SPOTS_96: &[Spot] = &[
    spot("BOARD 1", 0, 0, "First Bianca board: 2 B200 + 1 Grace."),
    spot("BOARD 2", 0, 0, "Second Bianca board, the same."),
    spot("NICs", 0, 0, "Network cards for the cluster fabric."),
    spot(
        "cold plates",
        0,
        0,
        "Liquid cold plates sit on the chips; no air-only cooling.",
    ),
    spot(
        "quick-disconnect",
        0,
        0,
        "Fittings that let a tray be pulled from the liquid loop; a leak point.",
    ),
    spot("4 GPUs + 2 CPUs", 0, TO_EOL, "The tray total."),
];

const ART_97: &str = r##"\
# ODM roles named in the sources

  Foxconn    mostly assembles NVL72           (TrendForce)
  Quanta     main assembler for NVL36         (TrendForce)
  Wistron    2Q25 GB200 shipments mainly for Dell   (KGI)

  also named on the page: Wiwynn, Inventec

  ODMs add value in: thermal design, cable routing, testing
"##;

const SPOTS_97: &[Spot] = &[
    spot(
        "Foxconn",
        0,
        TO_EOL,
        "TrendForce says Foxconn mostly assembles NVL72.",
    ),
    spot(
        "Quanta",
        0,
        TO_EOL,
        "TrendForce: the main assembler for NVL36.",
    ),
    spot(
        "Wistron",
        0,
        TO_EOL,
        "KGI says Wistron's GB200 shipments in 2Q25 mainly served Dell.",
    ),
    spot(
        "Wiwynn, Inventec",
        0,
        0,
        "The other two ODMs the page lists.",
    ),
    spot(
        "thermal design",
        0,
        0,
        "Where ODMs add value over a bare board.",
    ),
];

const ART_98: &str = r##"\
# What breaks at tray level

  leak at a fitting       ≈≈≈ drip      found at the liquid test
  NIC seated badly        ▒ loose       found at burn / test
  cable seated badly      ▒ loose       found at burn / test

  caught in the factory: swap a tray
  caught at the customer: downtime on the rack

  (textbook failure modes)
"##;

const SPOTS_98: &[Spot] = &[
    spot(
        "leak at a fitting",
        0,
        TO_EOL,
        "Quick-disconnect fittings are a leak point.",
    ),
    spot(
        "NIC seated badly",
        0,
        TO_EOL,
        "A poorly seated network card shows up under load.",
    ),
    spot(
        "cable seated badly",
        0,
        TO_EOL,
        "Loose cables show up at burn or test.",
    ),
    spot("caught in the factory", 0, TO_EOL, "Costs a tray swap."),
    spot(
        "caught at the customer",
        0,
        TO_EOL,
        "Costs downtime on a rack, the unit of capacity.",
    ),
];

const ART_99: &str = r##"\
# GB200 NVL72, front view

  ┌────────────────────────────────────────────┐
  │ ▒▒▒▒▒ compute trays (upper group) ▒▒▒▒▒▒▒▒ │
  │════════════════════════════════════════════│
  │ ███ NVLink switch trays (9 total) ████████ │
  │════════════════════════════════════════════│
  │ ▒▒▒▒▒ compute trays (lower group) ▒▒▒▒▒▒▒▒ │
  │────────────────────────────────────────────│
  │ power shelves + coolant manifolds          │
  └────────────────────────────────────────────┘
  18 compute trays, 9 switch trays, rear copper spine
  72 GPUs + 36 CPUs acting as one
"##;

const SPOTS_99: &[Spot] = &[
    spot(
        "compute trays (upper",
        0,
        0,
        "Compute trays sit above and below the switch trays; 18 in total.",
    ),
    spot(
        "NVLink switch trays",
        0,
        0,
        "Nine trays that let every GPU talk to every other at full speed.",
    ),
    spot(
        "compute trays (lower",
        0,
        0,
        "The lower group of compute trays.",
    ),
    spot(
        "power shelves",
        0,
        0,
        "Convert facility AC to DC and feed the trays.",
    ),
    spot(
        "coolant manifolds",
        0,
        0,
        "Distribute liquid coolant to cold plates on the chips.",
    ),
    spot(
        "72 GPUs + 36 CPUs",
        0,
        TO_EOL,
        "The whole rack is the unit of sale.",
    ),
];

const ART_100: &str = r##"\
# One rack, in numbers

  GPUs + CPUs          72 Blackwell + 36 Grace
  NVLink bandwidth     130 TB/s all-to-all
  HBM3e                13.4 TB at 576 TB/s
  compute              1.44 exaflops FP4 with sparsity
                       720 PFLOPS dense

  rack yield: any bad GPU or spine fault takes the system down
  (figures from Spheron and SemiAnalysis, via the page)
"##;

const SPOTS_100: &[Spot] = &[
    spot(
        "GPUs + CPUs",
        0,
        TO_EOL,
        "72 Blackwell GPUs and 36 Grace CPUs.",
    ),
    spot(
        "NVLink bandwidth",
        0,
        TO_EOL,
        "130 TB/s of all-to-all NVLink bandwidth.",
    ),
    spot("HBM3e", 0, TO_EOL, "13.4 TB of HBM3e at 576 TB/s."),
    spot(
        "compute",
        0,
        TO_EOL,
        "1.44 exaflops FP4 with sparsity, which is 720 PFLOPS dense.",
    ),
    spot(
        "rack yield",
        0,
        TO_EOL,
        "One bad GPU or spine fault can take the rack down.",
    ),
];

const ART_101: &str = r##"\
# What the site must carry

  power, kW
    nominal      ██████████████████ ~120
    deployed     ████████████████████ 130-132 (Spheron)
    HPE TDP      ████████████████████ 132
    HPE peak     ████████████████████████████ ~192 (1.5x TDP)

  weight  ~1.36 t (3,000 lb);  HPE: ~3,245 lb loaded
  HPE advises provisioning 192 kW per rack
"##;

const SPOTS_101: &[Spot] = &[
    spot("nominal", 0, TO_EOL, "About 120 kW nominal."),
    spot(
        "deployed",
        0,
        TO_EOL,
        "130-132 kW in deployments, per Spheron.",
    ),
    spot("HPE TDP", 0, TO_EOL, "HPE specifies 132 kW TDP."),
    spot("HPE peak", 0, TO_EOL, "Peak at 1.5x TDP, about 192 kW."),
    spot(
        "weight",
        0,
        TO_EOL,
        "About 1.36 t (3,000 lb); HPE lists about 3,245 lb loaded.",
    ),
];

const ART_102: &str = r##"\
# Any GPU to any other, at full speed

   GPU 1   GPU 2   GPU 3   ...   GPU 72
     │  ╲  ╱ │  ╲  ╱ │   ╲      ╱  │
     │   ╲╱  │   ╲╱  │    ╲    ╱   │
     ▼    ▼  ▼    ▼  ▼     ▼  ▼    ▼
  ┌──────────────────────────────────────────────────┐
  │ 9 NVLink switch trays (2 NVSwitch5 ASICs each)   │
  └──────────────────────────────────────────────────┘

  each GPU reaches the other 71 at full speed
  130 TB/s aggregate NVLink bandwidth
"##;

const SPOTS_102: &[Spot] = &[
    spot("GPU 1", 0, 0, "Each GPU has links into the switch trays."),
    spot("GPU 72", 0, 0, "All 72 GPUs connect to the same fabric."),
    spot(
        "9 NVLink switch trays",
        0,
        0,
        "Nine trays with two NVSwitch5 ASICs each (SemiAnalysis).",
    ),
    spot(
        "each GPU reaches",
        0,
        TO_EOL,
        "Every GPU can talk to any of the other 71 at full speed.",
    ),
    spot("130 TB/s", 0, 0, "Aggregate NVLink switch bandwidth."),
];

const ART_103: &str = r##"\
# Copper reach sets the rack size

   GPU ═══ copper spine ═══ SWITCH    short, fast, cheap
   GPU ─── farther ───────── SWITCH   copper reach runs out

  so all 72 GPUs sit in one rack
  rack, not server, = the unit of sale

  (copper spine and reach limit are textbook, per the page)
"##;

const SPOTS_103: &[Spot] = &[
    spot(
        "copper spine",
        0,
        TO_EOL,
        "Each GPU link terminates in the switch trays through a copper cable spine at the rear.",
    ),
    spot(
        "copper reach runs out",
        0,
        0,
        "Copper limits how far NVLink can run.",
    ),
    spot(
        "one rack",
        0,
        TO_EOL,
        "NVIDIA keeps all 72 GPUs in one rack because of copper reach.",
    ),
    spot(
        "unit of sale",
        0,
        TO_EOL,
        "The whole rack is what customers buy.",
    ),
];

const ART_104: &str = r##"\
# Many connectors, many fault points

  18 compute trays x links  ──▶  copper spine  ──▶  9 switch trays
          every connector is a possible fault point

  cable spine assembly + test is labour-heavy

  NVIDIA sells the switches too:
    more revenue per GPU than a bare chip

  (no per-part content or cable-vendor shares sourced)
"##;

const SPOTS_104: &[Spot] = &[
    spot(
        "copper spine",
        0,
        0,
        "Where a large number of cables and connectors concentrate.",
    ),
    spot(
        "every connector",
        0,
        TO_EOL,
        "Each connector is a possible fault point.",
    ),
    spot(
        "labour-heavy",
        0,
        TO_EOL,
        "Assembling and testing the spine takes manual work.",
    ),
    spot(
        "NVIDIA sells the switches",
        0,
        TO_EOL,
        "Selling switches too raises revenue per GPU versus a bare chip.",
    ),
    spot(
        "(no per-part",
        0,
        TO_EOL,
        "No sourced content or vendor shares.",
    ),
];

const ART_105: &str = r##"\
# Facility power to the trays

  ┌──────────┐    ┌───────────────┐    ┌──────────────┐    ┌───────┐
  │ FACILITY │    │ POWER SHELVES │    │ BUSBAR       │    │ TRAYS │
  │ AC feed  │ ─▶ │ AC to DC      │ ─▶ │ rear of rack │ ─▶ │ DC in │
  └──────────┘    └───────────────┘    └──────────────┘    └───────┘

  total draw 123.6 kW per NVL72, incl. conversion losses (SemiAnalysis)
  ~120 kW nominal;  130-132 kW in deployments (page)
"##;

const SPOTS_105: &[Spot] = &[
    spot("FACILITY", 0, 0, "The data hall's AC supply."),
    spot(
        "POWER SHELVES",
        0,
        0,
        "Convert facility AC to DC inside the rack.",
    ),
    spot(
        "BUSBAR",
        0,
        0,
        "Distributes DC to every tray from the back of the rack.",
    ),
    spot("TRAYS", 0, 0, "Compute and switch trays draw DC power."),
    spot(
        "123.6 kW",
        0,
        TO_EOL,
        "SemiAnalysis: total draw per NVL72 including AC-to-DC conversion losses.",
    ),
];

const ART_106: &str = r##"\
# kW per rack

  CPU rack        ██ 12 (up to)
  H100 air-cooled ███████ 40 (typical)
  NVL72 nominal   ████████████████████████ ~120
  NVL72 peak      ██████████████████████████████████████ 192 (HPE)

  NVL72 vs CPU rack:  ~10x       vs H100 air rack:  ~3x

  HPE: 132 kW TDP, peak 1.5x, provision 192 kW
"##;

const SPOTS_106: &[Spot] = &[
    spot(
        "CPU rack",
        0,
        TO_EOL,
        "A general-purpose CPU rack, up to 12 kW.",
    ),
    spot(
        "H100 air-cooled",
        0,
        TO_EOL,
        "A typical air-cooled H100 rack, about 40 kW.",
    ),
    spot("NVL72 nominal", 0, TO_EOL, "About 120 kW nominal."),
    spot(
        "NVL72 peak",
        0,
        TO_EOL,
        "HPE's peak and provisioning figure, 1.5x its 132 kW TDP.",
    ),
    spot(
        "NVL72 vs CPU rack",
        0,
        TO_EOL,
        "Roughly 10x a CPU rack and 3x an air-cooled H100 rack.",
    ),
];

const ART_107: &str = r##"\
# A 7 MW reference block

  7 MW block  ÷  132 kW per rack  ≈  53 racks
  (simple division; not a sourced figure)

  Vertiv + NVIDIA reference design:
    up to 132 kW per NVL72 rack

  power gear that can gate a site:
    feeders   transformers   headroom for peaks above TDP
"##;

const SPOTS_107: &[Spot] = &[
    spot(
        "7 MW block",
        0,
        TO_EOL,
        "Vertiv and NVIDIA's reference design is 7 MW for GB200 NVL72; dividing by 132 kW gives about 53 racks (arithmetic only).",
    ),
    spot(
        "up to 132 kW",
        0,
        0,
        "The reference design supports up to 132 kW per rack.",
    ),
    spot(
        "feeders",
        0,
        TO_EOL,
        "Power equipment can gate a deployment more than the chips.",
    ),
    spot(
        "headroom for peaks",
        0,
        0,
        "Short peaks above TDP need headroom older halls lack.",
    ),
];

const ART_108: &str = r##"\
# Heat out of the chips, in four hops

  ┌──────────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐
  │ COLD PLATES  │    │ RACK      │    │ CDU       │    │ FACILITY │
  │ on the chips │ ─▶ │ MANIFOLDS │ ─▶ │ heat swap │ ─▶ │ LOOP     │
  └──────────────┘    └───────────┘    └───────────┘    └──────────┘

  coolant circulates: tray ─▶ manifold ─▶ CDU ─▶ back to trays
  liquid cooling is mandatory for NVL72 (HPE)
"##;

const SPOTS_108: &[Spot] = &[
    spot(
        "COLD PLATES",
        0,
        0,
        "Mounted on the GPUs and CPUs; coolant picks up the heat here.",
    ),
    spot(
        "MANIFOLDS",
        0,
        0,
        "Rack manifolds distribute coolant to every tray.",
    ),
    spot(
        "CDU",
        0,
        0,
        "A coolant distribution unit exchanges the rack's heat with the facility loop.",
    ),
    spot(
        "FACILITY",
        0,
        0,
        "The building's water loop carries the heat away.",
    ),
    spot(
        "mandatory for NVL72",
        0,
        0,
        "HPE describes NVL72 as needing liquid cooling.",
    ),
];

const ART_109: &str = r##"\
# One in-row CDU serves up to 8 racks

   ┌─────────────────────────┐
   │ CDU  1.3 MW (HPE spec)  │
   └──┬──┬──┬──┬──┬──┬──┬──┬─┘
      R  R  R  R  R  R  R  R      8 racks
      1.3 MW ÷ 8  ≈  160 kW per rack  (arithmetic, not sourced)

  Vertiv reference: liquid + air cooling
  MegaMod CoolChip: turnkey up to 50% faster than onsite build
  (Vertiv's own claim)
"##;

const SPOTS_109: &[Spot] = &[
    spot(
        "CDU",
        1,
        TO_EOL,
        "HPE describes an in-row CDU rated 1.3 MW.",
    ),
    spot(
        "8 racks",
        1,
        TO_EOL,
        "HPE says one such CDU supports up to 8 racks.",
    ),
    spot(
        "1.3 MW ÷ 8",
        0,
        TO_EOL,
        "About 160 kW per rack on average; simple division, and consistent with 132 kW TDP.",
    ),
    spot(
        "Vertiv reference",
        0,
        TO_EOL,
        "Vertiv's design pairs liquid and air cooling.",
    ),
    spot(
        "MegaMod CoolChip",
        0,
        TO_EOL,
        "Vertiv says its factory-integrated approach delivers turnkey infrastructure up to 50% faster than onsite builds. Vendor claim.",
    ),
];

const ART_110: &str = r##"\
# Leaks are the main failure mode

   cold plate ══X══ quick-disconnect ══X══ manifold
                ▲                     ▲
             leak point            leak point

  a leak can destroy a rack worth millions (textbook)
  ──▶ leak-check the loop before shipping

  Boyd + NVIDIA Rack Emulator:
    automates thermal test and validation of liquid cooling
    before connection to data-centre equipment
"##;

const SPOTS_110: &[Spot] = &[
    spot(
        "cold plate",
        0,
        TO_EOL,
        "A leak at a cold plate can destroy a rack worth millions (textbook).",
    ),
    spot(
        "quick-disconnect",
        0,
        TO_EOL,
        "The other common leak point.",
    ),
    spot(
        "leak-check the loop",
        0,
        TO_EOL,
        "The loop is checked for leaks before shipping (textbook).",
    ),
    spot(
        "Boyd + NVIDIA",
        0,
        TO_EOL,
        "Boyd built a Rack Emulator with NVIDIA that automates thermal testing before connection to data-centre equipment.",
    ),
];

const ART_111: &str = r##"\
# Order of rack-level checks (textbook)

  ┌─────────┐    ┌─────────┐    ┌───────┐    ┌────────┐
  │ POWER   │    │ FILL    │    │ LEAK  │    │ LOAD   │
  │ rack on │ ─▶ │ coolant │ ─▶ │ check │ ─▶ │ run it │
  └─────────┘    └─────────┘    └───────┘    └────────┘

                                   then:  firmware loaded and checked

  no sourced procedure or duration
  third screening round: wafer sort, final test, rack test
"##;

const SPOTS_111: &[Spot] = &[
    spot("POWER", 0, 0, "Power the integrated rack."),
    spot("FILL", 0, 0, "Fill the loop with coolant."),
    spot(
        "LEAK",
        0,
        0,
        "Pressure and leak check before running at load.",
    ),
    spot(
        "LOAD",
        0,
        0,
        "Run the rack at load to expose faults that only show under full power.",
    ),
    spot(
        "firmware loaded",
        0,
        TO_EOL,
        "Firmware is loaded and checked as part of the test.",
    ),
];

const ART_112: &str = r##"\
# Faults that only appear at rack level

  loose cable in the NVLink spine    ──▶  link errors
  GPU fails only at full rack power  ──▶  fault under load
  coolant leak                       ──▶  wet tray
  firmware mismatch                  ──▶  GPUs not acting as one

  Boyd + NVIDIA Rack Emulator: automated thermal validation
"##;

const SPOTS_112: &[Spot] = &[
    spot(
        "loose cable",
        0,
        TO_EOL,
        "Loose cables in the NVLink spine cause link errors.",
    ),
    spot(
        "GPU fails only",
        0,
        TO_EOL,
        "Some faults only show under full rack power.",
    ),
    spot(
        "coolant leak",
        0,
        TO_EOL,
        "Leaks show up when the loop is pressurised and running.",
    ),
    spot(
        "firmware mismatch",
        0,
        TO_EOL,
        "Mismatched firmware can stop the 72 GPUs working as one.",
    ),
    spot(
        "Rack Emulator",
        0,
        TO_EOL,
        "Boyd's tool with NVIDIA automates thermal test and validation of liquid cooling.",
    ),
];

const ART_113: &str = r##"\
# Where a failure is cheapest

  caught in the factory   ████ tray swap
  caught at the customer  ████████████████████████████ rack downtime

  120+ kW under load needs a test bay with facility power + cooling
  test capacity at the ODM is itself a constraint

  (bars are qualitative; no costs sourced)
"##;

const SPOTS_113: &[Spot] = &[
    spot("caught in the factory", 0, TO_EOL, "Costs a tray swap."),
    spot(
        "caught at the customer",
        0,
        TO_EOL,
        "Costs downtime on a rack that is the whole unit of capacity.",
    ),
    spot(
        "120+ kW",
        0,
        TO_EOL,
        "A test bay needs facility power and cooling, which limits test capacity at the ODM.",
    ),
];

const ART_114: &str = r##"\
# From the ODM plant to the data hall

  ┌────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────┐
  │ ODM PLANT  │    │ CRATE       │    │ AIR + TRUCK │    │ DATA HALL │
  │ TW, MX, US │ ─▶ │ tested rack │ ─▶ │ to the site │ ─▶ │ installed │
  └────────────┘    └─────────────┘    └─────────────┘    └───────────┘

  Taiwan-to-US AI server shipments set to double in 2025 vs 2024
  (Nikkei, via a blog summary)

  (plant locations are textbook)
"##;

const SPOTS_114: &[Spot] = &[
    spot(
        "ODM PLANT",
        0,
        0,
        "Final assembly is mostly done by Taiwan-based ODMs with plants in Taiwan, Mexico and the US (textbook).",
    ),
    spot("CRATE", 0, 0, "A tested rack is crated for transport."),
    spot("AIR + TRUCK", 0, 0, "Racks travel by air and truck."),
    spot(
        "DATA HALL",
        0,
        0,
        "Must have power, cooling and floor ready.",
    ),
    spot(
        "set to double",
        0,
        TO_EOL,
        "Nikkei, via a blog summary: Taiwan-to-US AI server shipments set to double in 2025 vs 2024.",
    ),
];

const ART_115: &str = r##"\
# One rack on the floor

          ┌──────────────┐
          │   NVL72      │  ~1.36 t (3,000 lb)
          │              │  HPE: ~3,245 lb loaded
          └──────┬───────┘
   ═════════ floor loading ═════════

  matters for: floor rating, lift access, door sizes
  many halls need reinforced floors (textbook)
"##;

const SPOTS_115: &[Spot] = &[
    spot(
        "NVL72",
        0,
        0,
        "About 1.36 t; HPE lists about 3,245 lb loaded.",
    ),
    spot(
        "floor loading",
        0,
        0,
        "Racks this heavy can exceed the rating of older halls.",
    ),
    spot(
        "lift access",
        0,
        0,
        "Weight and height affect lifts and door sizes on the delivery path.",
    ),
    spot(
        "reinforced floors",
        0,
        0,
        "Many halls need them (textbook).",
    ),
];

const ART_116: &str = r##"\
# KGI rack shipments, thousand racks

  2Q25 actual     ██ 4.5            three ODMs combined
  2025 forecast   ████████████ 27-28    raised forecast
  2026 forecast   ████████████████████████ 50-60

  forecasts are not deliveries
  delays: damage, tariffs, customs
  revenue is usually recognised on delivery, so a delay moves quarters
  (bars show ranges; textbook on revenue timing)
"##;

const SPOTS_116: &[Spot] = &[
    spot(
        "2Q25 actual",
        0,
        TO_EOL,
        "KGI: 4.5 thousand GB200/GB300 racks shipped in 2Q25 by three ODMs combined.",
    ),
    spot(
        "2025 forecast",
        0,
        TO_EOL,
        "A raised forecast of 27-28 thousand racks.",
    ),
    spot(
        "2026 forecast",
        0,
        TO_EOL,
        "50-60 thousand racks. A forecast, not deliveries.",
    ),
    spot(
        "delays:",
        0,
        TO_EOL,
        "Transport damage, tariffs and customs affect timing.",
    ),
    spot(
        "recognised on delivery",
        0,
        0,
        "Typically revenue is recognised on delivery, so a delay moves quarters (textbook).",
    ),
];

const ART_117: &str = r##"\
# What the hall must have ready

  ☐ 120-192 kW of power per rack  (HPE: provision 192 kW)
  ☐ CDUs and facility water
  ☐ network
  ☐ a floor that can bear the weight

  the chip maker does not control any of these

  most existing halls need upgrades for NVL72
"##;

const SPOTS_117: &[Spot] = &[
    spot(
        "120-192 kW",
        0,
        TO_EOL,
        "HPE says to provision 192 kW per rack.",
    ),
    spot(
        "CDUs and facility water",
        0,
        TO_EOL,
        "The liquid loop needs CDUs and a facility water supply.",
    ),
    spot(
        "network",
        0,
        TO_EOL,
        "Cluster fabric connections to the rack.",
    ),
    spot(
        "a floor that can bear",
        0,
        TO_EOL,
        "A loaded rack is about 3,245 lb per HPE.",
    ),
    spot(
        "most existing halls",
        0,
        TO_EOL,
        "The page concludes most halls cannot take NVL72 without upgrades.",
    ),
];

const ART_118: &str = r##"\
# kW per rack, and the reference block

  CPU rack        ███ 12
  H100 air        █████████ 40
  NVL72 (ref)     ██████████████████████████████ up to 132
  NVL72 (peak)    ████████████████████████████████████████████ 192

  Vertiv + NVIDIA reference: 7 MW block, up to 132 kW per rack
  HPE in-row CDU: 1.3 MW, up to 8 racks
"##;

const SPOTS_118: &[Spot] = &[
    spot("CPU rack", 0, TO_EOL, "Up to 12 kW."),
    spot(
        "H100 air",
        0,
        TO_EOL,
        "About 40 kW for an air-cooled H100 rack.",
    ),
    spot(
        "NVL72 (ref)",
        0,
        TO_EOL,
        "Vertiv and NVIDIA's reference design supports up to 132 kW per rack.",
    ),
    spot(
        "NVL72 (peak)",
        0,
        TO_EOL,
        "HPE's peak and provisioning figure.",
    ),
    spot(
        "7 MW block",
        0,
        TO_EOL,
        "The Vertiv and NVIDIA reference design for GB200 NVL72.",
    ),
    spot(
        "HPE in-row CDU",
        0,
        TO_EOL,
        "Rated 1.3 MW, supporting up to 8 racks.",
    ),
];

const ART_119: &str = r##"\
# A handful of buyers

  Microsoft   Meta   AWS   Google
      └──────┬───────┴──────┘
             ▼
     NVL72 racks ──▶ need power + cooling suppliers (Vertiv, VRT)

  rent per GPU-hour (Spheron, 22 Mar 2026, indicative):  $10.50 - $27

  power and cooling can gate deployment more than chips
"##;

const SPOTS_119: &[Spot] = &[
    spot(
        "Microsoft",
        0,
        TO_EOL,
        "Named hyperscaler buyers: Microsoft, Meta, AWS, Google.",
    ),
    spot(
        "NVL72 racks",
        0,
        TO_EOL,
        "Each rack shipped creates demand for power and cooling suppliers such as Vertiv (VRT).",
    ),
    spot(
        "rent per GPU-hour",
        0,
        TO_EOL,
        "Indicative prices checked 22 Mar 2026 by Spheron: from $10.50 to $27 per GPU-hour.",
    ),
    spot(
        "power and cooling can gate",
        0,
        0,
        "The page's conclusion: site power and cooling can limit deployments more than chips.",
    ),
];

const ART_120: &str = r##"\
# Build to order

  ┌────────────────┐    ┌──────────────┐    ┌────────────────┐
  │ CLOUD CUSTOMER │    │ ODM          │    │ RACKS          │
  │ design + order │ ─▶ │ builds to it │ ─▶ │ shipped direct │
  └────────────────┘    └──────────────┘    └────────────────┘

  Foxconn (2317.TW)   Quanta (2382.TW)   Wistron (3231.TW)
  Wiwynn (6669.TW)    Inventec (2356.TW)

  Foxconn mostly NVL72; Quanta main for NVL36 (TrendForce)
"##;

const SPOTS_120: &[Spot] = &[
    spot(
        "CLOUD CUSTOMER",
        0,
        0,
        "Often supplies or specifies the design the ODM builds to.",
    ),
    spot(
        "ODM",
        0,
        0,
        "Original design manufacturer: builds to order.",
    ),
    spot(
        "Foxconn (2317.TW)",
        0,
        0,
        "TrendForce says Foxconn mostly assembles NVL72.",
    ),
    spot(
        "Quanta (2382.TW)",
        0,
        0,
        "Main assembler for NVL36 per TrendForce.",
    ),
    spot(
        "Wiwynn (6669.TW)",
        0,
        0,
        "Key supplier for AWS Trainium systems.",
    ),
    spot("Inventec (2356.TW)", 0, 0, "Fifth ODM named on the page."),
];

const ART_121: &str = r##"\
# Growth signals

  Hon Hai    most aggressive on GB200 shipment growth, 3Q25 guide (KGI)
  Wistron    2Q25 GB200 shipments mainly served Dell (KGI)
  Quanta     AI servers on track for 70% of server revenue
             (over 60% mid-2025, CFO)
  Wiwynn     AWS Trainium systems; 2025 revenue NT$950.663bn (page)

  thin margins: ODMs rely on volume and rack content
"##;

const SPOTS_121: &[Spot] = &[
    spot(
        "Hon Hai",
        0,
        TO_EOL,
        "KGI: the most aggressive ODM on GB200 shipment growth in 3Q25 guidance.",
    ),
    spot(
        "Wistron",
        0,
        TO_EOL,
        "KGI: 2Q25 GB200 shipments mainly served Dell.",
    ),
    spot(
        "Quanta",
        0,
        TO_EOL,
        "The CFO said AI servers are on track for 70% of server revenue, over 60% in mid-2025.",
    ),
    spot(
        "Wiwynn",
        0,
        TO_EOL,
        "Key supplier for AWS Trainium; the page gives 2025 revenue of NT$950.663bn.",
    ),
    spot(
        "thin margins",
        0,
        TO_EOL,
        "Margins are thin, so ODMs rely on volume and rack content.",
    ),
];

const ART_122: &str = r##"\
# Shares, none confirmed

  Foxconn, general + AI server   ████████████████████ ~40% (blog)
  top four, Q4 2025 servers      ██████████████████████████ 53.2%
    (Foxconn, Quanta, Wistron, Inventec; aggregator citing
     Taipei Times; not confirmed)

  treat both as unverified claims
"##;

const SPOTS_122: &[Spot] = &[
    spot(
        "Foxconn, general + AI server",
        0,
        TO_EOL,
        "A blog puts Foxconn near 40% of the general plus AI server market. Unverified.",
    ),
    spot(
        "top four",
        0,
        TO_EOL,
        "An aggregator citing the Taipei Times says the top four held 53.2% in Q4 2025. Not confirmed.",
    ),
    spot(
        "treat both",
        0,
        TO_EOL,
        "Neither figure has been checked against a primary source.",
    ),
];

const ART_123: &str = r##"\
# ODM vs OEM

  ODM   builds to a hyperscaler's design, sells direct
  OEM   sells branded systems + support contracts

  ┌──────┐      ┌─────┐      ┌────────────┐
  │ DELL │      │ HPE │      │ SUPERMICRO │
  │ DELL │      │ HPE │      │ SMCI       │
  └──────┘      └─────┘      └────────────┘

  buyers: enterprises, neoclouds, sovereigns
"##;

const SPOTS_123: &[Spot] = &[
    spot(
        "ODM   builds",
        0,
        TO_EOL,
        "Builds to a hyperscaler's design for direct sale.",
    ),
    spot(
        "OEM   sells",
        0,
        TO_EOL,
        "Sells branded systems with support contracts.",
    ),
    spot("DELL", 0, 0, "Dell Technologies (DELL)."),
    spot(
        "HPE",
        1,
        0,
        "Hewlett Packard Enterprise (HPE) publishes an NVL72 spec sheet.",
    ),
    spot("SUPERMICRO", 0, 0, "Super Micro Computer (SMCI)."),
    spot(
        "buyers:",
        0,
        TO_EOL,
        "OEMs serve enterprises, neoclouds and sovereign buyers.",
    ),
];

const ART_124: &str = r##"\
# From reference design to a product spec

  HPE NVL72 spec sheet:
    TDP     ████████████████████████ 132 kW
    peak    ████████████████████████████████████ ~192 kW (1.5x TDP)
    weight  about 3,245 lb loaded

  adds customer guidance: provision 192 kW per rack
  OEM value: documentation, support, integration
"##;

const SPOTS_124: &[Spot] = &[
    spot("TDP", 0, TO_EOL, "HPE gives 132 kW TDP."),
    spot("peak", 0, TO_EOL, "Peak at 1.5x TDP, about 192 kW."),
    spot("weight", 0, TO_EOL, "About 3,245 lb loaded."),
    spot(
        "provision 192 kW",
        0,
        TO_EOL,
        "HPE's guidance to customers.",
    ),
    spot(
        "OEM value",
        0,
        TO_EOL,
        "The OEM turns a reference design into a documented, supported product.",
    ),
];

const ART_125: &str = r##"\
# Thin margin on Nvidia content

  rack content:  GPU + switch + HBM  = Nvidia's
  OEM adds:      financing, support, data-centre integration

  risks:  thin margin   GPU allocation exposure

  Wistron builds for Dell: an ODM often builds for an OEM too (KGI)

  (no OEM AI server revenue or share sourced)
"##;

const SPOTS_125: &[Spot] = &[
    spot(
        "rack content",
        0,
        TO_EOL,
        "The major content in the rack is Nvidia's.",
    ),
    spot(
        "OEM adds",
        0,
        TO_EOL,
        "Financing, support and integration with the customer's data centre.",
    ),
    spot(
        "risks:",
        0,
        TO_EOL,
        "Thin margin and exposure to GPU allocation.",
    ),
    spot(
        "Wistron builds for Dell",
        0,
        TO_EOL,
        "KGI: Wistron's 2Q25 GB200 shipments mainly served Dell.",
    ),
    spot(
        "(no OEM AI server",
        0,
        TO_EOL,
        "No OEM AI server revenue or share is sourced here.",
    ),
];

const ART_126: &str = r##"\
# kW per rack

  CPU rack        ██ up to 12
  H100 air-cooled ███████ ~40
  NVL72 nominal   ████████████████████████ ~120
  NVL72 deployed  ██████████████████████████ 130-132 (Spheron)
  NVL72 peak      ██████████████████████████████████████ 192 (HPE)

  SemiAnalysis: 123.6 kW total draw incl. AC-to-DC losses
  peak = 1.5x the 132 kW TDP
"##;

const SPOTS_126: &[Spot] = &[
    spot(
        "CPU rack",
        0,
        TO_EOL,
        "A general-purpose CPU rack, up to 12 kW.",
    ),
    spot(
        "H100 air-cooled",
        0,
        TO_EOL,
        "About 40 kW for an air-cooled H100 rack.",
    ),
    spot("NVL72 nominal", 0, TO_EOL, "About 120 kW nominal."),
    spot(
        "NVL72 deployed",
        0,
        TO_EOL,
        "Spheron reports 130-132 kW deployed.",
    ),
    spot(
        "NVL72 peak",
        0,
        TO_EOL,
        "HPE's peak or provisioning figure, 1.5x the 132 kW TDP.",
    ),
    spot(
        "SemiAnalysis",
        0,
        TO_EOL,
        "123.6 kW total draw per NVL72, including AC-to-DC conversion losses.",
    ),
];

const ART_127: &str = r##"\
# Why an old hall cannot just take it

  hall built for 10-15 kW racks
    needs: new power feeds    new cooling    floor loading

  air cannot remove this heat from packed trays
    ──▶ liquid cooling needed

  Vertiv + NVIDIA reference: up to 132 kW per rack, 7 MW block
"##;

const SPOTS_127: &[Spot] = &[
    spot(
        "10-15 kW racks",
        0,
        0,
        "Typical of halls built before AI racks.",
    ),
    spot(
        "new power feeds",
        0,
        0,
        "Feeds sized for 120-192 kW per rack.",
    ),
    spot("new cooling", 0, 0, "Liquid cooling infrastructure."),
    spot("floor loading", 0, 0, "A loaded rack is about 3,245 lb."),
    spot(
        "air cannot remove",
        0,
        TO_EOL,
        "Air cooling cannot remove this much heat from packed trays.",
    ),
];

const ART_128: &str = r##"\
# How many racks fit a site

  site budget / 192 kW  =  racks you can safely provision
  site budget / 120 kW  =  racks if you use nominal

  example: 7 MW block (Vertiv reference)
    ÷ 192 kW  ≈  36 racks
    ÷ 132 kW  ≈  53 racks

  (division only; not sourced figures)
"##;

const SPOTS_128: &[Spot] = &[
    spot(
        "192 kW",
        0,
        TO_EOL,
        "HPE's provisioning figure, which sets the safe rack count.",
    ),
    spot(
        "120 kW",
        0,
        TO_EOL,
        "Nominal power; planning to this fits more racks but leaves no headroom.",
    ),
    spot(
        "÷ 192 kW",
        0,
        TO_EOL,
        "7 MW divided by 192 kW is about 36 racks (arithmetic only).",
    ),
    spot(
        "÷ 132 kW",
        0,
        TO_EOL,
        "7 MW divided by 132 kW is about 53 racks (arithmetic only).",
    ),
];

const ART_129: &str = r##"\
# GB200 / GB300 racks, thousand (KGI, Aug 2025)

  2Q25 actual     ██ 4.5          three ODMs combined
  2025 forecast   ████████████ 27-28     (midpoint 27.5)
  2026 forecast   ████████████████████████ 50-60   (midpoint 55)

  forecasts, not deliveries; bars use midpoints for ranges
"##;

const SPOTS_129: &[Spot] = &[
    spot(
        "2Q25 actual",
        0,
        TO_EOL,
        "4.5 thousand racks shipped across three ODMs.",
    ),
    spot(
        "2025 forecast",
        0,
        TO_EOL,
        "KGI's raised forecast: 27-28 thousand racks.",
    ),
    spot(
        "2026 forecast",
        0,
        TO_EOL,
        "50-60 thousand racks. A forecast, not deliveries.",
    ),
    spot(
        "forecasts, not deliveries",
        0,
        TO_EOL,
        "Only 2Q25 is an actual figure.",
    ),
];

const ART_130: &str = r##"\
# Racks to GPUs

  50k racks x 72 GPUs  =  3.6M GPUs
  60k racks x 72 GPUs  =  4.3M GPUs

  (simple arithmetic, not a sourced figure)

  Blackwell: above 80% of Nvidia high-end GPU shipments in 2025
  (TrendForce)
"##;

const SPOTS_130: &[Spot] = &[
    spot("50k racks", 0, TO_EOL, "50,000 x 72 = 3.6 million GPUs."),
    spot(
        "60k racks",
        0,
        TO_EOL,
        "60,000 x 72 = about 4.3 million GPUs.",
    ),
    spot(
        "(simple arithmetic",
        0,
        TO_EOL,
        "These GPU counts are derived, not sourced.",
    ),
    spot(
        "Blackwell: above 80%",
        0,
        TO_EOL,
        "TrendForce says Blackwell is above 80% of Nvidia high-end GPU shipments in 2025.",
    ),
];

const ART_131: &str = r##"\
# Chokepoints, in the page's order

  ┌────────┐    ┌────────┐    ┌─────────────┐    ┌───────┐
  │ CoWoS  │    │ HBM    │    │ RACK        │    │ SITE  │
  │ output │ ─▶ │ supply │ ─▶ │ integration │ ─▶ │ power │
  └────────┘    └────────┘    └─────────────┘    └───────┘

  risk is two-sided:
    liquid-cooling or yield problem   ──▶  ramp delayed
    hyperscaler capex cut             ──▶  demand lower

  KGI: Hon Hai the most aggressive ODM on shipment growth
"##;

const SPOTS_131: &[Spot] = &[
    spot("CoWoS", 0, 0, "Packaging output is the first chokepoint."),
    spot("HBM", 0, 0, "Memory supply is the second."),
    spot("RACK", 0, 0, "Rack integration is the third."),
    spot("SITE", 0, 0, "Data-centre power is the fourth."),
    spot(
        "risk is two-sided",
        0,
        0,
        "A cooling or yield problem delays the ramp; a capex cut would reduce demand.",
    ),
    spot(
        "Hon Hai",
        0,
        0,
        "KGI flagged Hon Hai as the most aggressive ODM on shipment growth.",
    ),
];

const ART_132: &str = r##"\
# $ per GPU-hour (Spheron, 22 Mar 2026, indicative)

  CoreWeave          ████████████████ $10.50
  Oracle Cloud       ████████████████████████ $16
  Azure ND GB200 v6  ████████████████████████████████████████ $27

  same Blackwell hardware, different bundles:
    hyperscaler: networking, storage, SLAs, enterprise contracts
    neocloud:    leaner capacity

  indicative list rates; they change often
"##;

const SPOTS_132: &[Spot] = &[
    spot("CoreWeave", 0, TO_EOL, "$10.50 per GPU-hour, indicative."),
    spot("Oracle Cloud", 0, TO_EOL, "$16 per GPU-hour, indicative."),
    spot(
        "Azure ND GB200 v6",
        0,
        TO_EOL,
        "$27 per GPU-hour, indicative.",
    ),
    spot(
        "hyperscaler:",
        0,
        TO_EOL,
        "Hyperscalers bundle networking, storage, SLAs and enterprise contracts.",
    ),
    spot(
        "neocloud:",
        0,
        TO_EOL,
        "Neoclouds sell leaner capacity at lower prices.",
    ),
];

const ART_133: &str = r##"\
# 72 GPUs x price, per hour, fully rented

  at $10.50   72 x 10.50  =  $756 / rack-hour
  at $16      72 x 16     =  $1,152
  at $27      72 x 27     =  $1,944

  before power, cooling and financing

  (arithmetic from the page's prices; not sourced figures)
"##;

const SPOTS_133: &[Spot] = &[
    spot(
        "at $10.50",
        0,
        TO_EOL,
        "72 x $10.50 = $756 per rack-hour if fully rented.",
    ),
    spot("at $16", 0, TO_EOL, "72 x $16 = $1,152."),
    spot("at $27", 0, TO_EOL, "72 x $27 = $1,944."),
    spot(
        "before power",
        0,
        TO_EOL,
        "Revenue is gross of power, cooling and financing costs.",
    ),
];

const ART_134: &str = r##"\
# What moves the return

  utilisation        ████████████████████
  contract length    ███████████████
  price declines     ████████████████████████  (bars: qualitative)

  a rack failure stops the revenue stream
    ──▶ burn and test before shipping matters
"##;

const SPOTS_134: &[Spot] = &[
    spot("utilisation", 0, TO_EOL, "Idle GPU-hours earn nothing."),
    spot(
        "contract length",
        0,
        TO_EOL,
        "Longer contracts lock in price.",
    ),
    spot("price declines", 0, TO_EOL, "Rental prices change often."),
    spot(
        "a rack failure",
        0,
        TO_EOL,
        "A failure that takes down a rack stops its revenue, which is why rack-level burn and test matter.",
    ),
];

#[cfg(test)]
mod tests {
    use super::super::diagrams_vis::check;
    use super::*;

    #[test]
    fn every_visual_resolves() {
        for (p, c, s) in KEYS {
            let v = lookup(p, c, s).unwrap_or_else(|| panic!("missing {p}/{c}/{s}"));
            check(&v, &format!("{p}/{c}/{s}"));
            assert!(v.spots.len() >= 3, "{p}/{c}/{s}: few spots");
        }
    }

    const KEYS: &[(&str, &str, &str)] = &[
        ("FINAL TEST", "LOAD", "Handler loads the part"),
        ("FINAL TEST", "LOAD", "Index time"),
        ("FINAL TEST", "LOAD", "Contact"),
        ("FINAL TEST", "ATE TEST", "Test order"),
        ("FINAL TEST", "ATE TEST", "Test time is cost"),
        ("FINAL TEST", "ATE TEST", "Who sells it"),
        ("FINAL TEST", "BURN-IN", "Why heat works"),
        ("FINAL TEST", "BURN-IN", "Where it is used"),
        ("FINAL TEST", "BURN-IN", "Wafer-level burn-in"),
        ("FINAL TEST", "SYSTEM TEST", "What SLT catches"),
        ("FINAL TEST", "SYSTEM TEST", "Slots and power"),
        ("FINAL TEST", "SYSTEM TEST", "Titan HP"),
        ("FINAL TEST", "SPEED BIN", "Bell curve"),
        ("FINAL TEST", "SPEED BIN", "Salvage"),
        ("FINAL TEST", "SPEED BIN", "Mix risk"),
        ("FINAL TEST", "MARK + SHIP", "Mark"),
        ("FINAL TEST", "MARK + SHIP", "Pack"),
        ("FINAL TEST", "MARK + SHIP", "Escape cost"),
        ("FINAL TEST", "HANDLER: picks part", "Handler jobs"),
        ("FINAL TEST", "HANDLER: picks part", "Thermal control"),
        ("FINAL TEST", "HANDLER: picks part", "Vendor view"),
        ("FINAL TEST", "SOCKET: pins touch BGA", "What it is"),
        ("FINAL TEST", "SOCKET: pins touch BGA", "Wear"),
        ("FINAL TEST", "SOCKET: pins touch BGA", "Who and risk"),
        ("FINAL TEST", "LOAD BOARD (custom", "Signal path"),
        ("FINAL TEST", "LOAD BOARD (custom", "One per product"),
        ("FINAL TEST", "LOAD BOARD (custom", "Demands and wear"),
        ("FINAL TEST", "TEST HEAD", "What is inside"),
        ("FINAL TEST", "TEST HEAD", "Duopoly"),
        ("FINAL TEST", "TEST HEAD", "Conflicting share"),
        ("FINAL TEST", "infant mortality", "Bathtub curve, left side"),
        ("FINAL TEST", "infant mortality", "What burn-in does"),
        ("FINAL TEST", "infant mortality", "Demand link"),
        ("FINAL TEST", "Titan HP", "Platform"),
        ("FINAL TEST", "Titan HP", "Cooling"),
        ("FINAL TEST", "Titan HP", "Revenue shift"),
        ("FINAL TEST", "TOP BIN", "Top bin"),
        ("FINAL TEST", "TOP BIN", "What moves the bins"),
        ("FINAL TEST", "TOP BIN", "Mix effect"),
        ("FINAL TEST", "Advantest CY25", "Advantest share"),
        ("FINAL TEST", "Advantest CY25", "Why numbers differ"),
        ("FINAL TEST", "Advantest CY25", "What holds"),
        ("FINAL TEST", "Test houses", "OSAT test houses"),
        ("FINAL TEST", "Test houses", "Who owns the tools"),
        ("FINAL TEST", "Test houses", "Risks"),
        ("PACKAGE", "INTERPOSER", "The silicon wiring board"),
        ("PACKAGE", "INTERPOSER", "Reticle limits"),
        ("PACKAGE", "INTERPOSER", "Why it bottlenecks"),
        ("PACKAGE", "CHIP-ON-WAFER", "CoW step"),
        ("PACKAGE", "CHIP-ON-WAFER", "Known-good die"),
        ("PACKAGE", "CHIP-ON-WAFER", "The name"),
        ("PACKAGE", "FLIP ONTO", "Wafer-on-substrate"),
        ("PACKAGE", "FLIP ONTO", "Expansion mismatch"),
        ("PACKAGE", "FLIP ONTO", "Who does it"),
        ("PACKAGE", "MOLD +", "Seal and finish"),
        ("PACKAGE", "MOLD +", "What can fail"),
        ("PACKAGE", "MOLD +", "Materials"),
        ("PACKAGE", "[1] LID", "Lid and cold plate"),
        ("PACKAGE", "[1] LID", "Flatness and warpage"),
        ("PACKAGE", "[1] LID", "Supply"),
        ("PACKAGE", "[2] TIM", "Thermal interface material"),
        ("PACKAGE", "[2] TIM", "Different heights"),
        ("PACKAGE", "[2] TIM", "Slow failure"),
        ("PACKAGE", "[3] HBM", "HBM stack on the package"),
        ("PACKAGE", "[3] HBM", "Share and supply"),
        ("PACKAGE", "[3] HBM", "HBM4 and price"),
        ("PACKAGE", "GPU DIE A", "The compute die"),
        ("PACKAGE", "GPU DIE A", "Why two dies"),
        ("PACKAGE", "GPU DIE A", "Package totals"),
        ("PACKAGE", "[7] NV-HBI", "Die-to-die link"),
        ("PACKAGE", "[7] NV-HBI", "Why it matters"),
        ("PACKAGE", "[7] NV-HBI", "Packaging link"),
        ("PACKAGE", "[6] TSV", "Through-silicon vias"),
        ("PACKAGE", "[6] TSV", "How a TSV is made"),
        ("PACKAGE", "[6] TSV", "Risks"),
        ("PACKAGE", "[4] microbumps", "Pitch ladder"),
        ("PACKAGE", "[4] microbumps", "Hybrid bonding"),
        ("PACKAGE", "[4] microbumps", "Underfill gap"),
        ("PACKAGE", "[8] C4 bumps", "C4 bumps"),
        ("PACKAGE", "[8] C4 bumps", "Shear at the corners"),
        ("PACKAGE", "[8] C4 bumps", "Why it matters"),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "ABF substrate"),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "2026 squeeze"),
        ("PACKAGE", "[9] ORGANIC SUBSTRATE", "Suppliers"),
        ("PACKAGE", "CoWoS-L", "The scaling route"),
        ("PACKAGE", "CoWoS-L", "Capacity estimates"),
        ("PACKAGE", "CoWoS-L", "Demand and risk"),
        ("PACKAGE", "supply gap", "Allocation, not just capacity"),
        ("PACKAGE", "supply gap", "Capacity forecasts"),
        ("PACKAGE", "supply gap", "Three shortages"),
        ("PACKAGE", "ASE", "OSAT leaders"),
        ("PACKAGE", "ASE", "Role in AI"),
        ("PACKAGE", "ASE", "Investor angle"),
        ("SHIP", "BOARD", "Bianca board"),
        ("SHIP", "BOARD", "Where it can fail"),
        ("SHIP", "BOARD", "Upstream limits"),
        ("SHIP", "TRAY", "Compute tray"),
        ("SHIP", "TRAY", "Who builds trays"),
        ("SHIP", "TRAY", "Failure points"),
        ("SHIP", "RACK", "Rack integration"),
        ("SHIP", "RACK", "Rack totals"),
        ("SHIP", "RACK", "Power and weight"),
        ("SHIP", "NVLINK SWITCH TRAY 1", "All-to-all fabric"),
        ("SHIP", "NVLINK SWITCH TRAY 1", "Why one rack"),
        ("SHIP", "NVLINK SWITCH TRAY 1", "Cables and revenue"),
        ("SHIP", "power shelves", "AC to DC"),
        ("SHIP", "power shelves", "Against other racks"),
        ("SHIP", "power shelves", "Vertiv design"),
        ("SHIP", "coolant manifolds", "Coolant loop"),
        ("SHIP", "coolant manifolds", "CDU sizing"),
        ("SHIP", "coolant manifolds", "Leaks and testing"),
        ("SHIP", "BURN + TEST", "Rack-level checks"),
        ("SHIP", "BURN + TEST", "What it catches"),
        ("SHIP", "BURN + TEST", "Cost"),
        ("SHIP", "crate by", "Route"),
        ("SHIP", "crate by", "Weight and floors"),
        ("SHIP", "crate by", "Volumes"),
        ("SHIP", "DATA CENTER", "Site readiness"),
        ("SHIP", "DATA CENTER", "Reference design"),
        ("SHIP", "DATA CENTER", "Who buys"),
        ("SHIP", "ODM", "Who builds"),
        ("SHIP", "ODM", "Shipments"),
        ("SHIP", "ODM", "Share claims"),
        ("SHIP", "OEM", "OEMs"),
        ("SHIP", "OEM", "HPE spec sheet"),
        ("SHIP", "OEM", "Margin and mix"),
        ("SHIP", "NVL72 peak", "Rack power density"),
        ("SHIP", "NVL72 peak", "Retrofit limits"),
        ("SHIP", "NVL72 peak", "Siting math"),
        ("SHIP", "2026 forecast", "KGI rack forecasts"),
        ("SHIP", "2026 forecast", "Implied GPUs"),
        ("SHIP", "2026 forecast", "Dependencies"),
        ("SHIP", "Azure ND GB200 v6", "Renting a GPU-hour"),
        ("SHIP", "Azure ND GB200 v6", "Rack revenue"),
        ("SHIP", "Azure ND GB200 v6", "Why it matters"),
    ];
}
