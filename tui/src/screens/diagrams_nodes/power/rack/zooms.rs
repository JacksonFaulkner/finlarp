// RACK POWER: lettered zoom-ins a-e. Each is the overview's scene with the camera held on one subject
// (tools/pbr3d/blender/power_rack_zooms.py, GLBs in tools/pbr3d/assets/power_rack_zoom_<letter>.glb):
// a AC in, DC down the back; b power shelves; c kilowatts per rack; d 800 V DC and the sidecar; e why so many amps.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the AC inlet", BEAT_MS)
        .note(
            "The busway's tap-off box feeds the rack's PDU. Each power shelf has an AC inlet at its front, and an AC whip runs from the PDU to it.",
            "A grey tap-off box under the busway, and warm yellow beads running down the whips into each shelf's inlet.",
        )
        .detail(
            "AC goes in; DC comes out.",
            &["415/480 V AC", "AC whip into each shelf"],
        ),
    Beat::new("DC out of the PSUs", BEAT_MS)
        .note(
            "Inside each shelf the PSUs convert AC to about 50 V DC and push it through their clips onto the busbar.",
            "The shelf's PSU modules glow in a row; orange beads leave their clips and run onto the copper bar.",
        )
        .detail(
            "The shelves are the converters.",
            &["PSU: 5.5 kW each", "~50 V DC"],
        ),
    Beat::new("the bar and its return", BEAT_MS)
        .note(
            "The +50 V bar carries the current out to the trays, and the return bar carries it back. Both run down the back of the rack.",
            "Two copper bars side by side: orange beads on the +50 V bar, and the return bar beside it.",
        )
        .detail(
            "Two bars make a circuit: out and back.",
            &["+50 V busbar", "Return bar"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("four shelves at the top", BEAT_MS)
        .note(
            "The rack carries power shelves at its top and bottom, four each, with the trays between them. Each shelf is a 1U unit of power supplies.",
            "The grey shelves at the top of the rack, their PSU modules lit in a row above the trays.",
        )
        .detail(
            "Each shelf is 33 kW in an NVL72.",
            &["1U shelf", "33 kW per shelf"],
        ),
    Beat::new("four at the bottom", BEAT_MS)
        .note(
            "The bottom shelves do the same job, feeding the same busbar from the other end of the rack.",
            "The bottom shelves glowing in a row under the trays, their beads running into the bar.",
        )
        .detail(
            "Shelves top and bottom share the busbar.",
            &["Busbar down the back", "8 x 33 kW shelves (N+N)"],
        ),
    Beat::new("six PSUs per shelf", BEAT_MS)
        .note(
            "Each shelf holds six 5.5 kW PSU modules, and each module can be pulled and replaced while the rack keeps running.",
            "One shelf close up: six PSU modules in a row, one slid partly out of its bay.",
        )
        .detail(
            "Modules swap while the rack runs.",
            &["6 x 5.5 kW = 33 kW", "Replaced while running"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("~120 kW per rack", BEAT_MS)
        .note(
            "A GB200 NVL72 rack draws about 120 kW. HPE lists 132 kW design power, with peaks near 192 kW.",
            "One rack, its busbar lit along the back and its trays glowing with the power they take.",
        )
        .detail(
            "Cloud racks drew 10-20 kW.",
            &["KILOWATTS PER RACK: ~120 kW", "Cloud racks: 10-20 kW"],
        ),
    Beat::new("eight racks: about 1 MW", BEAT_MS)
        .note(
            "A row of eight of these racks draws about 1 MW, fed from an overhead busway that runs above them.",
            "Eight racks in a row under the overhead busway, with a cable dropping from a tap-off box into each.",
        )
        .detail(
            "A row is a megawatt-class load.",
            &["~1 MW per row", "1 MW racks: NVIDIA's aim"],
        ),
    Beat::new("one rack: ~120 kW", BEAT_MS)
        .note(
            "Up close, one NVL72-class rack: the busway tap feeds its power, and the busbar carries the current down its back.",
            "The rack's side, its trays and shelves lit, with the busbar tap drawn in beads.",
        )
        .detail(
            "Each generation pushes the number up.",
            &["~120 kW per rack", "Next racks: 600 kW to 1 MW"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("800 V DC feed", BEAT_MS)
        .note(
            "NVIDIA's 800 VDC plan feeds 1 MW racks from 2027. The feed runs along an overhead tray to a sidecar power rack beside the compute rack.",
            "A violet 800 V feed along an overhead tray, dropping to a slim sidecar rack beside the compute rack.",
        )
        .detail(
            "The feed skips the 50 V busbar.",
            &["800 VDC from 2027", "1 MW racks"],
        ),
    Beat::new("DC link into the rack", BEAT_MS)
        .note(
            "A short copper link carries the converted DC across into the compute rack. The sidecar does the final conversion beside the rack.",
            "A copper link bar between the sidecar and the compute rack, with orange beads crossing it.",
        )
        .detail(
            "Higher voltage needs far less current.",
            &["Sixteen times less current than 50 V"],
        ),
    Beat::new("compute rack", BEAT_MS)
        .note(
            "The compute rack keeps its trays and busbar. Only the way its power arrives changes.",
            "The compute rack beside the sidecar, its trays lit and its busbar running down the back.",
        )
        .detail(
            "Only the power path changes.",
            &["SIDECAR: a separate power rack", "Final conversion beside the rack"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("~2,400 A at 120 kW", BEAT_MS)
        .note(
            "120 kW at about 50 V is about 2,400 A. The busbar is a thick copper bar, not a cable, because no cable could carry that much current.",
            "The busbar lit along its length, with the clips beside it and the copper bar standing out from the cables.",
        )
        .detail(
            "Power is voltage times current.",
            &["P = V x I", "~2,400 A"],
        ),
    Beat::new("every clip carries its share", BEAT_MS)
        .note(
            "Each tray's clip takes its share of the current off the bar. Every connector in the path is rated for hundreds of amps.",
            "Clips along the bar, each with beads flowing into it from the copper.",
        )
        .detail(
            "Connectors are rated for hundreds of amps.",
            &["Hundreds of amps per connector"],
        ),
    Beat::new("thousands of amps", BEAT_MS)
        .note(
            "A 192 kW peak at 50 V is over 3,800 A, and every bar and connector along the path is sized for it.",
            "The whole rack, the bar packed with beads and glowing warm.",
        )
        .detail(
            "Peaks set the connector rating.",
            &["192 kW peak: over 3,800 A", "Thick copper"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "AC in, DC down the back",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "power shelves",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "kilowatts per rack",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "800 V DC and the sidecar",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "why so many amps",
        build: zoom_e,
    },
];
