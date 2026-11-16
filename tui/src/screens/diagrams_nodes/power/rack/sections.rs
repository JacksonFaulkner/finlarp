// RACK POWER: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_RACK.txt, from the Blender
// scenes in tools/pbr3d/blender/power_rack_sections.py (GLBs in tools/pbr3d/assets/power_rack_section_<n>.glb).
// Three beats each. Heading 10 (Sources) is text only.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1 what happens: AC in at the top, DC down the back.
const S1_B: &[Beat] = &[
    Beat::new("power shelves at the top", BEAT_MS)
        .note(
            "Power comes into the rack at the top, where the shelves convert AC to DC, and runs down the back on a copper busbar.",
            "A tall rack cut open: purple compute trays, teal switch trays, grey shelves at the top, and the copper busbar down its back.",
        )
        .detail(
            "AC in at the top, DC down the back.",
            &["KILOWATTS PER RACK: ~120 kW", "415/480 V AC in"],
        ),
    Beat::new("AC whip into each shelf", BEAT_MS)
        .note(
            "AC whips carry 415/480 V into each shelf's inlet, from the busway tap-off box above the rack.",
            "Warm yellow beads down the whips into the shelves, from the tap-off box under the busway.",
        )
        .detail(
            "Shelves take AC.",
            &["415/480 V AC", "Six 5.5 kW PSUs per shelf"],
        ),
    Beat::new("PSU makes ~50 V DC", BEAT_MS)
        .note(
            "Each PSU makes about 50 V DC. The shelf clips onto the bar, which carries the DC down the back of the rack.",
            "Orange DC beads leave the shelf's clips and run along the copper bar.",
        )
        .detail(
            "DC down the back.",
            &["~50 V DC", "BUSBAR"],
        ),
];

/// 2 the parts: the power shelf and busbar, the PDU, the 800 V sidecar.
const S2_B: &[Beat] = &[
    Beat::new("POWER SHELF and BUSBAR", BEAT_MS)
        .note(
            "A POWER SHELF is a 1U shelf of power supplies, 33 kW in an NVL72. Its BUSBAR is a copper bar down the back that carries the DC to every tray.",
            "Grey shelves at the top and bottom of the rack, with the copper bar lit down its back.",
        )
        .detail(
            "33 kW per shelf in an NVL72.",
            &["POWER SHELF: 33 kW", "BUSBAR down the back"],
        ),
    Beat::new("PDU and the busway tap", BEAT_MS)
        .note(
            "The PDU is the rack's power distribution unit: breakers and outlets fed from a busway tap-off box above.",
            "The tap-off box under the busway, and the PDU's breakers at the rack's side.",
        )
        .detail(
            "The PDU feeds the rack.",
            &["PDU: breakers and outlets"],
        ),
    Beat::new("800 V DC and the sidecar", BEAT_MS)
        .note(
            "800 VDC is NVIDIA's plan for 1 MW racks. A SIDECAR is a separate power rack beside the compute rack, doing the final conversion.",
            "The violet 800 V feed along an overhead tray and the slim sidecar rack beside the compute rack.",
        )
        .detail(
            "The sidecar does the final conversion.",
            &["800 VDC from 2027", "SIDECAR"],
        ),
];

/// 3 power through the rack, in order: the PDU, the shelves, the busbar, the trays.
const S3_B: &[Beat] = &[
    Beat::new("1 AC from the PDU", BEAT_MS)
        .note(
            "415/480 V three-phase AC arrives from the PDU and feeds each power shelf.",
            "The tap-off box and PDU, and AC whips running into the shelves.",
        )
        .detail(
            "Three-phase AC in.",
            &["415/480 V three-phase", "AC whip into each shelf"],
        ),
    Beat::new("2 shelf splits it, 3 PSUs make DC", BEAT_MS)
        .note(
            "Each POWER SHELF splits the AC across six PSU modules, and the modules make about 50 V DC.",
            "A shelf's six PSU modules lit in a row, with DC beads leaving the shelf.",
        )
        .detail(
            "Six modules per shelf.",
            &["6 x 5.5 kW", "~50 V DC"],
        ),
    Beat::new("4 busbar, 5 tray clips", BEAT_MS)
        .note(
            "The BUSBAR carries the DC down the back. Each tray clips on and converts the DC again on its own board, see VRM.",
            "The bar with beads running along it, and the trays with their clips gripping it.",
        )
        .detail(
            "Each tray converts again.",
            &["Converted again on each board", "See VRM"],
        ),
];

/// 4 why so many amps: about 2,400 A on a copper bar.
const S4_B: &[Beat] = &[
    Beat::new("~2,400 A at 120 kW", BEAT_MS)
        .note(
            "Power is voltage times current: 120 kW at about 50 V is about 2,400 A.",
            "The busbar lit along its length, the clips beside it carrying the load.",
        )
        .detail(
            "P = V x I.",
            &["P = V x I", "~2,400 A"],
        ),
    Beat::new("copper bar, not a cable", BEAT_MS)
        .note(
            "That is why the busbar is a thick copper bar, not a cable, and why every connector in the path is rated for hundreds of amps.",
            "The thick copper bars beside the trays, drawn heavier than the cables around them.",
        )
        .detail(
            "Connectors are rated for hundreds of amps.",
            &["Hundreds of amps per connector", "Thick copper"],
        ),
    Beat::new("thousands of amps", BEAT_MS)
        .note(
            "A 192 kW peak is over 3,800 A, so the bar and its clips run at their limit when the GPUs all work at once.",
            "The rack's busbar packed with beads and glowing warm.",
        )
        .detail(
            "Peak current.",
            &["192 kW peak: over 3,800 A"],
        ),
];

/// 5 shelves and redundancy: eight 33 kW shelves for N+N, six 5.5 kW PSUs each, hot-swapped.
const S5_B: &[Beat] = &[
    Beat::new("eight 33 kW shelves", BEAT_MS)
        .note(
            "NVIDIA's DGX GB200 guide describes eight 33 kW shelves for N+N redundancy. Other builds use six.",
            "The top shelves in a row, their PSU modules lit.",
        )
        .detail(
            "N+N redundancy.",
            &["8 x 33 kW shelves (N+N)", "6 in other builds"],
        ),
    Beat::new("replaced while running", BEAT_MS)
        .note(
            "Each shelf's six 5.5 kW PSU modules can be pulled and replaced while the rack keeps running.",
            "The bottom shelves, with one PSU module drawn partly out of its bay.",
        )
        .detail(
            "Swapped while the rack runs.",
            &["6 x 5.5 kW = 33 kW", "Replaced while the rack runs"],
        ),
    Beat::new("six PSUs make 33 kW", BEAT_MS)
        .note(
            "One shelf: six 5.5 kW PSU modules make 33 kW, and any one of them can be serviced without a shutdown.",
            "One shelf close up: six modules in a row, one slid partly out.",
        )
        .detail(
            "Six modules per shelf.",
            &["6 x 5.5 kW = 33 kW"],
        ),
];

/// 6 kilowatts per rack keeps rising: one rack, then a row, then the next generation.
const S6_B: &[Beat] = &[
    Beat::new("~120 kW per rack", BEAT_MS)
        .note(
            "Cloud racks drew 10-20 kW. A GB200 NVL72 rack is about 120 kW, with HPE listing 132 kW design power and peaks near 192 kW.",
            "One rack, its busbar lit down the back and its trays glowing.",
        )
        .detail(
            "The number keeps climbing.",
            &["Cloud racks: 10-20 kW", "~120 kW per NVL72"],
        ),
    Beat::new("a row: about 1 MW", BEAT_MS)
        .note(
            "A row of eight of these racks draws about 1 MW, fed from an overhead busway.",
            "Eight racks in a row under the busway, cables dropping into each.",
        )
        .detail(
            "A row is about a megawatt.",
            &["~1 MW per row"],
        ),
    Beat::new("next racks: 600 kW to 1 MW", BEAT_MS)
        .note(
            "NVIDIA's next racks aim at 600 kW to 1 MW. At 1 MW a 54 V bus would need up to 200 kg of copper busbar per rack, according to NVIDIA.",
            "One rack, its copper busbar drawn heavy and thick down the back.",
        )
        .detail(
            "Copper is the limit at 54 V.",
            &["600 kW to 1 MW", "~200 kg copper at 54 V"],
        ),
];

/// 7 800 V DC: the feed, the link into the rack, and the sidecar.
const S7_B: &[Beat] = &[
    Beat::new("800 V DC feed", BEAT_MS)
        .note(
            "NVIDIA's 800 VDC plan converts 13.8 kV AC straight to 800 V DC at the edge of the building, and runs it to the racks.",
            "The violet 800 V feed along an overhead tray, dropping toward the racks.",
        )
        .detail(
            "Fewer conversion steps.",
            &["800 VDC", "13.8 kV AC at the edge"],
        ),
    Beat::new("DC link into the rack", BEAT_MS)
        .note(
            "Higher voltage means sixteen times less current than 50 V, so the copper is far thinner.",
            "A short copper link between the sidecar and the compute rack, with orange beads crossing it.",
        )
        .detail(
            "Sixteen times less current.",
            &["Sixteen times less current than 50 V"],
        ),
    Beat::new("the sidecar power rack", BEAT_MS)
        .note(
            "A SIDECAR power rack can do the final conversion beside the compute rack, so the compute rack takes DC it can use.",
            "The slim sidecar rack beside the compute rack, its converters lit.",
        )
        .detail(
            "Final conversion beside the rack.",
            &["SIDECAR", "Production alongside Kyber racks in 2027"],
        ),
];

/// 8 who makes it: the shelves and PSUs, the PDUs and busways, NVIDIA's reference designs.
const S8_B: &[Beat] = &[
    Beat::new("the shelves and PSUs", BEAT_MS)
        .note(
            "Delta, Lite-On, Vertiv (VRT) and Flex make the power shelves and PSUs for these racks.",
            "The grey power shelves at the top of the rack.",
        )
        .detail(
            "A few makers supply the shelves.",
            &["Delta, Lite-On", "Vertiv (VRT), Flex"],
        ),
    Beat::new("the PDUs and busways", BEAT_MS)
        .note(
            "Vertiv, Schneider, Eaton (ETN) and Legrand make the PDUs and busways that carry AC to the rack.",
            "The overhead busway above a row of racks, with its tap-off boxes.",
        )
        .detail(
            "Busway and PDU makers.",
            &["Schneider, Legrand", "Eaton (ETN)"],
        ),
    Beat::new("NVIDIA's reference designs", BEAT_MS)
        .note(
            "NVIDIA (NVDA) sets the rack reference designs, and around 20 partners support 800 VDC.",
            "The sidecar and the compute rack side by side, the reference design they share.",
        )
        .detail(
            "One reference design, many partners.",
            &["NVIDIA (NVDA)", "Around 20 partners for 800 VDC"],
        ),
];

/// 9 chokepoints and risks: thousands of amps, the clips, the new DC safety practice.
const S9_B: &[Beat] = &[
    Beat::new("thousands of amps", BEAT_MS)
        .note(
            "Thousands of amps per rack strain the connectors and busbars, which are the limit of the design.",
            "The busbar packed with beads and glowing warm, the clips beside it under load.",
        )
        .detail(
            "Connectors and busbars set the limit.",
            &["Thousands of amps per rack"],
        ),
    Beat::new("clips must grip the bar", BEAT_MS)
        .note(
            "Each clip must grip the bar and carry its share of the current, tray after tray.",
            "Clips on the copper bar, each with beads flowing into it.",
        )
        .detail(
            "Connector quality matters.",
            &["Hundreds of amps per connector"],
        ),
    Beat::new("new DC safety practice", BEAT_MS)
        .note(
            "800 VDC needs new safety practice, breakers and connectors. Each rack's power also spikes as its GPUs sync.",
            "The DC link between the sidecar and the compute rack, with its safety housing shown in grey.",
        )
        .detail(
            "New breakers and connectors.",
            &["800 VDC: new safety practice", "Power spikes as GPUs sync"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
