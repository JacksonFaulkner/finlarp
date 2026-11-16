// SWITCHGEAR: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_SWG.txt, from the Blender
// scenes in tools/pbr3d/blender/power_switchgear_sections.py (GLBs in tools/pbr3d/assets/power_switchgear_section_<n>.glb).
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

/// 1 what happens: power is split, switched and protected.
const S1_B: &[Beat] = &[
    Beat::new("medium voltage into the house", BEAT_MS)
        .note(
            "Medium-voltage cable runs from the transformers to the switchgear house. The main breaker takes the supply onto the bus, which feeds every circuit in the house.",
            "The grey campus from above: amber beads run down the MV cable into the main breaker of lineup A.",
        )
        .detail(
            "The house is where the power is split.",
            &["MEDIUM VOLTAGE", "13.8-34.5 kV"],
        ),
    Beat::new("feeder breakers split the feed", BEAT_MS)
        .note(
            "Feeder breakers split the supply into circuits. Each one feeds a unit substation, which steps the power down to 480 V.",
            "Feeder breakers in a row, amber beads dropping through each, and a substation transformer at the end of each feed.",
        )
        .detail(
            "One breaker per feed, so each can be isolated.",
            &["CIRCUIT BREAKER", "480 V in the US"],
        ),
    Beat::new("a fault: its relay trips", BEAT_MS)
        .note(
            "A fault on feeder 1 is caught by its relay, which trips that feed's breaker within a cycle. The rest of the house keeps running.",
            "A red fault on feeder 1's cable, its relay lit, the breaker opening; the other feeders keep their amber beads.",
        )
        .detail(
            "Power is switched and protected in one place.",
            &["PROTECTION RELAY", "Within a cycle"],
        ),
];

/// 2 the parts: the vacuum breaker, the unit substation, the relay.
const S2_B: &[Beat] = &[
    Beat::new("CIRCUIT BREAKER: vacuum bottle", BEAT_MS)
        .note(
            "A circuit breaker is a switch that can interrupt a fault current. At medium voltage it is a vacuum breaker, with its contacts sealed inside a bottle.",
            "Three vacuum bottles cut open on their axes, their arms and stabs inside a grey cabinet with its breaker compartment open.",
        )
        .detail(
            "Breakers are rated to interrupt the fault current.",
            &["CIRCUIT BREAKER", "Vacuum breakers at MV"],
        ),
    Beat::new("UNIT SUBSTATION: 480 V out", BEAT_MS)
        .note(
            "A unit substation is a transformer and its switchgear in one package. It steps medium voltage down to 480 V for the low-voltage side.",
            "A transformer tank with its bushings on top: amber beads enter at the top, cyan beads leave on the low-voltage side.",
        )
        .detail(
            "480 V is the US low-voltage level.",
            &["UNIT SUBSTATION", "415 V elsewhere"],
        ),
    Beat::new("PROTECTION RELAY", BEAT_MS)
        .note(
            "The relay measures current and voltage and trips the breaker on a fault. Upstream relays are set to wait a little longer, so only the faulted feed drops.",
            "A cabinet's front panel with its relay screen glowing, and a thin line from the relay to the breaker it trips.",
        )
        .detail(
            "Relays make the trip selective.",
            &["PROTECTION RELAY", "Upstream breakers wait longer"],
        ),
];

/// 3 a feed, in order: the main breaker, the feeder breakers and the unit substation, then 480 V to the hall.
const S3_B: &[Beat] = &[
    Beat::new("1 the cable lands, 2 the main breaker", BEAT_MS)
        .note(
            "Medium-voltage cable arrives from the substation and lands on the main breaker and the switchgear bus.",
            "Amber beads run from the cable into the main breaker's cabinet and up onto the copper bus bars above the lineup.",
        )
        .detail(
            "The main breaker sits at the head of the house.",
            &["MEDIUM VOLTAGE", "Main breaker and bus"],
        ),
    Beat::new("3 feeder breakers, 4 down to 480 V", BEAT_MS)
        .note(
            "Feeder breakers split the bus into circuits. Each circuit feeds a unit substation transformer, which steps it down to 480 V.",
            "Feeder breakers open in a row; amber beads drop through each into a substation, and cyan 480 V beads leave it.",
        )
        .detail(
            "Five steps from the cable to 480 V.",
            &["5 steps", "480 V"],
        ),
    Beat::new("5 switchboards to the hall", BEAT_MS)
        .note(
            "Low-voltage switchboards send the 480 V on to the UPS and the data hall.",
            "Cyan beads run along the low-voltage cables into the hall's switchboards and on toward the racks.",
        )
        .detail(
            "Then the UPS and the racks.",
            &["480 V", "UPS and data hall"],
        ),
];

/// 4 breaking a fault: a short drawn in red; the relay sees it; the vacuum bottle opens.
const S4_B: &[Beat] = &[
    Beat::new("a short: tens of thousands of amps", BEAT_MS)
        .note(
            "A short circuit can draw tens of thousands of amps. Nothing in the path can carry that for long, so the fault has to be cleared fast.",
            "Red fault beads stream from the feeder's cable toward the short, and the cable glows hot at the fault point.",
        )
        .detail(
            "Fault current is far above the working load.",
            &["Tens of thousands of amps"],
        ),
    Beat::new("the relay sees it within a cycle", BEAT_MS)
        .note(
            "The relay measures the fault and tells its breaker to open, within a cycle of the fault starting.",
            "The relay's screen lit, with the trip signal running to the breaker beside it.",
        )
        .detail(
            "A cycle is about 17 ms at 60 Hz.",
            &["PROTECTION RELAY", "~17 ms per cycle at 60 Hz"],
        ),
    Beat::new("the vacuum bottle opens", BEAT_MS)
        .note(
            "The contacts part inside a vacuum bottle, where the arc cannot sustain itself and goes out at the next current zero.",
            "The bottle cut open: the contacts drawn apart, with a short arc between them that dies out.",
        )
        .detail(
            "Vacuum breakers are used at medium voltage.",
            &["Vacuum breakers at MV", "Contacts part inside the bottle"],
        ),
];

/// 5 arc flash: the flash at the fault, the heat, the enclosure.
const S5_B: &[Beat] = &[
    Beat::new("ARC FLASH", BEAT_MS)
        .note(
            "A fault arc in open air reaches thousands of degrees and blows out molten metal. ARC FLASH is that explosive energy.",
            "A bright flash at the fault point with a plume of hot gas rising from it.",
        )
        .detail(
            "The energy is why the gear is enclosed.",
            &["ARC FLASH", "Thousands of degrees"],
        ),
    Beat::new("thousands of degrees", BEAT_MS)
        .note(
            "Switchgear is built to contain the arc, not just to switch current. Its enclosure is rated to vent or contain the arc.",
            "The flash shown inside the cabinet, its red-edged glow pressing against the front panel, which holds.",
        )
        .detail(
            "Rated to vent or contain arcs.",
            &["ARC FLASH", "Rated to vent or contain arcs"],
        ),
    Beat::new("enclosed, so it vents safely", BEAT_MS)
        .note(
            "Technicians work on this gear only de-energized, or in protective gear. The closed cabinet is what keeps a fault arc from reaching them.",
            "The grey cabinet shut with its breaker compartment closed and its front panel dark.",
        )
        .detail(
            "De-energize first.",
            &["De-energized or in protective gear"],
        ),
];

/// 6 redundancy: 2N and N+1, path A and path B, each server fed from both.
const S6_B: &[Beat] = &[
    Beat::new("path A: the whole load", BEAT_MS)
        .note(
            "Path A is one complete route from the utility to the hall. On its own it can carry the whole load.",
            "Lineup A with amber beads along its bus and feeders into the hall.",
        )
        .detail(
            "2N: each path can carry the whole load.",
            &["2N", "Each path carries the whole load"],
        ),
    Beat::new("path B: the whole load", BEAT_MS)
        .note(
            "Path B is a second complete route. Between them, one path can be serviced while the hall keeps running.",
            "Lineup B, its beads running into the hall from the other side of the house.",
        )
        .detail(
            "N+1 spares one unit for every N.",
            &["N+1: one spare for every N", "REDUNDANCY"],
        ),
    Beat::new("each server takes one feed from each", BEAT_MS)
        .note(
            "Each server's two power supplies take one feed from each path. One path can fail or be serviced without losing the server.",
            "Racks with beads on two feeds, one from path A and one from path B.",
        )
        .detail(
            "Two supplies, two paths.",
            &["Two feeds per server", "One feed from each path"],
        ),
];

/// 7 where the generators join: standby, the utility drops, the utility returns.
const S7_B: &[Beat] = &[
    Beat::new("standby generators", BEAT_MS)
        .note(
            "The ATS watches the utility feed. Standby generators sit ready between the transformers, with their breakers held open.",
            "Two generators with their exhaust stacks, and the ATS controller on the house wall.",
        )
        .detail(
            "Generators start if the utility fails.",
            &["ATS", "~10 s to start"],
        ),
    Beat::new("the ATS moves the load", BEAT_MS)
        .note(
            "If the utility fails, the generators start. Once they reach voltage and frequency, the ATS moves the load onto them.",
            "The utility lines turn dark red; green beads flow from the generators into the lineups.",
        )
        .detail(
            "The UPS covers the seconds in between.",
            &["~10 s to start", "UPS covers the gap"],
        ),
    Beat::new("utility back", BEAT_MS)
        .note(
            "When the grid returns, the ATS moves the load back to the utility, and the generators cool down.",
            "Amber beads return to the utility line; the generator beads fade out.",
        )
        .detail(
            "A routine transfer.",
            &["Transfer back"],
        ),
];

/// 8 who makes it: the makers of the transformers, substations and the UPS and busways.
const S8_B: &[Beat] = &[
    Beat::new("the yard transformer", BEAT_MS)
        .note(
            "Eaton, Schneider Electric, ABB, Siemens, Vertiv and GE Vernova make switchgear, breakers and unit substations. Many are assembled into prefabricated power skids.",
            "A squat grey transformer tank with its bushings, standing in the yard beside the line.",
        )
        .detail(
            "The makers sell lineups, breakers and substations.",
            &["Eaton (ETN)", "Schneider Electric, ABB, Siemens"],
        ),
    Beat::new("the unit substation", BEAT_MS)
        .note(
            "A unit substation is often a prefabricated skid: transformer and lineup built together, then set in place on the pad.",
            "A transformer and its lineup together on one pad, with the feed in on top and cyan cables out below.",
        )
        .detail(
            "Prefabricated skids speed construction.",
            &["Prefabricated power skids"],
        ),
    Beat::new("the UPS and busways", BEAT_MS)
        .note(
            "Vertiv (VRT) and GE Vernova (GEV) are among the makers of the power chain from switchgear to the UPS and busways that reach the hall.",
            "The UPS cabinets and the A and B busways running over the rack rows in the hall.",
        )
        .detail(
            "Many makers, one chain.",
            &["Vertiv (VRT)", "GE Vernova (GEV)"],
        ),
];

/// 9 chokepoints and risks: more breakers, more redundancy, the long lead times.
const S9_B: &[Beat] = &[
    Beat::new("more breakers per feed", BEAT_MS)
        .note(
            "Every feed needs its own breakers, relays and bus. More power per rack means more feeders and bigger breakers.",
            "A row of feeder breakers along the bus, the cabinets lined up as far as the eye can see.",
        )
        .detail(
            "More power per rack means more feeders.",
            &["Bigger breakers", "More feeders"],
        ),
    Beat::new("each layer doubles the gear", BEAT_MS)
        .note(
            "Each added layer of REDUNDANCY doubles the equipment. Two full paths mean two of everything.",
            "Racks fed from both lineups, with the beads of both paths running into the hall.",
        )
        .detail(
            "Redundancy costs equipment.",
            &["Every added layer doubles equipment"],
        ),
    Beat::new("transfer switches add up", BEAT_MS)
        .note(
            "Switchgear and transformers both have long lead times, so the extra gear that redundancy needs arrives slowly.",
            "The ATS controller on the house wall, with the generator breakers beside it.",
        )
        .detail(
            "Long lead times are a chokepoint.",
            &["Switchgear: long lead times", "Transformers: long lead times"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
