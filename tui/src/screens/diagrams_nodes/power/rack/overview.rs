// POWER tab, RACK POWER: the page's overview, a Blender scene (tools/pbr3d/blender/power_rack_overview.py, GLB
// tools/pbr3d/assets/power_rack_overview.glb). Seven beats: a rack cut open, AC into its power shelves, DC down the
// copper busbar, into every tray, the thousands of amps, a row of racks, and the 800 V DC sidecar.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_rack_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_rack_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("an AI rack", BEAT_MS)
        .note(
            "A GB200 NVL72-style rack: compute and switch trays in the middle, power shelves at the top and bottom. Power comes in at the top and runs down a copper busbar at the back.",
            "The rack cut open lengthwise: purple compute trays, teal switch trays, grey power shelves top and bottom, and the copper busbar running down the back.",
        )
        .detail(
            "A full NVL72 rack draws about 120 kW.",
            &["KILOWATTS PER RACK: ~120 kW", "Design power 132 kW, peaks ~192 kW"],
        ),
    Beat::new("AC into the power shelves", BEAT_MS)
        .note(
            "A busway tap-off box feeds the rack's PDU. AC whips carry 415/480 V three-phase power down into each power shelf.",
            "A grey busway overhead, a tap-off box beside it, and warm yellow beads running down the AC whips into the shelves' inlets.",
        )
        .detail(
            "Each shelf takes AC and turns it into DC.",
            &["415/480 V AC", "6 x 5.5 kW = 33 kW per shelf"],
        ),
    Beat::new("DC down the busbar", BEAT_MS)
        .note(
            "Each shelf's six PSUs convert AC to about 50 V DC and push it out through clips onto a copper busbar that runs down the back of the rack.",
            "Orange beads leave the shelves' clips and run along the long copper bar; the return bar sits beside it.",
        )
        .detail(
            "A copper bar carries the DC, not a cable.",
            &["~50 V DC", "BUSBAR down the back"],
        ),
    Beat::new("into every tray", BEAT_MS)
        .note(
            "Each compute and switch tray clips onto the busbar and takes its share of the DC. Each tray then converts it again on its own board.",
            "Clips grip the bar along the trays' edges, and beads step off into each tray's board, which glows along its length.",
        )
        .detail(
            "Each tray has its own converter.",
            &["Converted again on each board", "~18 compute, 9 switch trays"],
        ),
    Beat::new("thousands of amps", BEAT_MS)
        .note(
            "120 kW at about 50 V is roughly 2,400 A, and a 192 kW peak is over 3,800 A. That is why the busbar is a thick copper bar and why every clip is rated for hundreds of amps.",
            "The busbar lights up along its length with dense beads and a warm glow, and the clips beside it carry the most current.",
        )
        .detail(
            "Current, not voltage, sets the size of the copper.",
            &["~2,400 A at 120 kW", "192 kW peak: over 3,800 A"],
        ),
    Beat::new("a row of racks", BEAT_MS)
        .note(
            "A row of these racks draws a megawatt or more. Each rack has its own tap-off from an overhead busway that runs above the row.",
            "Eight closed racks side by side under a long overhead busway, with a cable dropping from a tap-off box into each rack.",
        )
        .detail(
            "Power per row sets the feeder size.",
            &["~1-2 MW per row", "NVIDIA's next racks: ~1 MW each"],
        ),
    Beat::new("next: 800 V DC", BEAT_MS)
        .note(
            "NVIDIA plans 800 V DC for racks from 2027. A sidecar power rack beside the compute rack makes the final conversion, and a short copper link carries the DC across into the compute rack.",
            "A violet 800 V feed runs along an overhead tray into a slim sidecar rack beside the compute rack, with a short copper link between them.",
        )
        .detail(
            "Higher voltage means far less copper.",
            &["800 VDC from 2027", "Sixteen times less current than 50 V"],
        ),
];
