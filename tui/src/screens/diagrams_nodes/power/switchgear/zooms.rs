// SWITCHGEAR: lettered zoom-ins a-e. Each is the overview's campus with the camera held on one subject
// (tools/pbr3d/blender/power_switchgear_zooms.py, GLBs in tools/pbr3d/assets/power_switchgear_zoom_<letter>.glb):
// a a feed from MV to 480 V, b breaking a fault, c redundancy: 2N, d generators and the ATS, e arc flash.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the feeder breakers", BEAT_MS)
        .note(
            "Each feeder breaker is its own circuit. The main bus is split into feeds here, and each feed heads for its own unit substation.",
            "A row of grey cabinets with their breaker compartments open. Amber beads drop from the copper bus bar through each breaker and on down the feed.",
        )
        .detail(
            "Separate breakers keep the feeds apart.",
            &["CIRCUIT BREAKER", "One breaker per feed"],
        ),
    Beat::new("the unit substation: to 480 V", BEAT_MS)
        .note(
            "A unit substation is a transformer and its switchgear in one package. It steps the medium voltage down to 480 V for the hall.",
            "A transformer tank with its bushings on top. Amber beads enter it from the feed, and cyan beads leave for the low-voltage side.",
        )
        .detail(
            "480 V is the low-voltage level the hall uses.",
            &["480 V in the US", "415 V in much of the world"],
        ),
    Beat::new("480 V to the hall", BEAT_MS)
        .note(
            "Low-voltage cable carries the 480 V from the substation to the hall's switchboards, then on to the UPS and the busways.",
            "Cyan beads run along the 480 V cables and cable trays toward the hall, one lit run for each path.",
        )
        .detail(
            "The last step before the racks.",
            &["480 V", "Then the UPS and busways"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("its relay sees the fault", BEAT_MS)
        .note(
            "A short on feeder 1 draws a surge of current. The protection relay measures it and decides the fault is real, in a fraction of a cycle.",
            "The cabinet's front panel lit, its relay screen showing the trip. Red fault beads run from the cable into the cabinet.",
        )
        .detail(
            "The relay decides; the breaker acts.",
            &["PROTECTION RELAY", "Within a cycle"],
        ),
    Beat::new("the vacuum bottle opens", BEAT_MS)
        .note(
            "The breaker's contacts part inside a vacuum bottle. With no air in the gap, the arc cannot sustain itself, and the current stops.",
            "The three bottles, cut open on their axes, with their contacts drawn apart. A small arc glows between the contacts as they open.",
        )
        .detail(
            "Vacuum breakers are used at medium voltage.",
            &["Vacuum breakers at MV", "Contacts part in the bottle"],
        ),
    Beat::new("the fault: tens of thousands of amps", BEAT_MS)
        .note(
            "A short circuit can draw tens of thousands of amps. Only the faulted feed drops: the breakers upstream wait a little longer, and the other feeders stay on.",
            "The fault point in red at the cable, the other feeders' amber beads still flowing past it, and the cabinets in a row around it.",
        )
        .detail(
            "Selective trips keep the rest of the hall up.",
            &["Other feeders stay on", "Tens of thousands of amps"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("path A", BEAT_MS)
        .note(
            "Path A runs from the utility through lineup A, its feeders and its unit substation, and into the hall. It can carry the whole load on its own.",
            "Amber and cyan beads run along lineup A's bus and feeder breakers and down the A feed into the hall.",
        )
        .detail(
            "One path carries the whole hall.",
            &["2N: each path can carry the whole load"],
        ),
    Beat::new("path B", BEAT_MS)
        .note(
            "Path B is the mirror image: its own lineup, its own feeders, its own substation. Nothing is shared between A and B except the hall itself.",
            "The mirror lineup B with its beads running from its bus and feeders into the hall, from the other side of the room.",
        )
        .detail(
            "Two paths, no shared parts.",
            &["2N / N+1", "Separate lineups, separate feeds"],
        ),
    Beat::new("each rack fed from A and B", BEAT_MS)
        .note(
            "Each rack's two power supplies take one feed each, one from path A and one from path B. Lose either path and the rack keeps running.",
            "Racks in rows along the hall, each with beads on two feeds: one from A, one from B.",
        )
        .detail(
            "Each server takes one feed from each path.",
            &["Two supplies per server", "One feed from each path"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("standby generators", BEAT_MS)
        .note(
            "The standby generators wait between the transformers, their breakers held open. The ATS watches the utility feed, ready to move the load.",
            "Two generator sets with their exhaust stacks, the ATS controller on the house wall, and amber beads still running from the utility.",
        )
        .detail(
            "The generators sit idle until the utility drops.",
            &["ATS: automatic transfer switch", "Generator breakers open"],
        ),
    Beat::new("utility lost: the ATS moves the load", BEAT_MS)
        .note(
            "The utility drops. The ATS opens the mains and closes the generator breakers, so the lineups run on the generators' power.",
            "The utility lines turn dark red. Green beads leave the generators and run into the lineups; the mains go quiet.",
        )
        .detail(
            "The UPS covers the seconds before the generators take over.",
            &["~10 s to start"],
        ),
    Beat::new("utility back: transfer back", BEAT_MS)
        .note(
            "When the utility returns, the ATS moves the load back and the generators run down and cool off.",
            "The utility line glows amber again. The green beads thin out as the generator breakers open, and the exhaust fades.",
        )
        .detail(
            "A routine transfer for a data center.",
            &["Transfer back", "Generators cool down"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("arc flash: thousands of degrees", BEAT_MS)
        .note(
            "A fault arc in open air reaches thousands of degrees and blows out molten metal. That energy is why switchgear is enclosed and rated for arc flash.",
            "A bright white-orange flash at the fault point, with the cabinet's front shown in red along the edge of the arc.",
        )
        .detail(
            "Switchgear is built to contain the blast.",
            &["ARC FLASH", "Thousands of degrees"],
        ),
    Beat::new("molten metal", BEAT_MS)
        .note(
            "The arc melts the copper it touches. The gear is designed to vent the gas and metal through its back or top, away from the people in front.",
            "Glowing orange drops and a plume of red-hot gas leave the cabinet's vent, with the front door held shut.",
        )
        .detail(
            "Arc-resistant cabinets vent through a set path.",
            &["ARC FLASH", "Rated to vent or contain arcs"],
        ),
    Beat::new("enclosed gear", BEAT_MS)
        .note(
            "Technicians work on this gear only when it is de-energized, or in protective clothing. The cabinet's enclosure is what keeps the arc inside.",
            "The grey enclosed cabinet with its breaker compartment shut, its front panel dark, and the status light off.",
        )
        .detail(
            "De-energized work is the safe default.",
            &["ARC FLASH", "De-energize or wear protection"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "a feed: MV to 480 V",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "breaking a fault",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "redundancy: 2N",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "generators and the ATS",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "arc flash",
        build: zoom_e,
    },
];
