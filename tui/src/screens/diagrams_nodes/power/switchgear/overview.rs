// POWER tab, SWITCHGEAR: the page's overview, a Blender scene (tools/pbr3d/blender/power_switchgear_overview.py,
// GLB tools/pbr3d/assets/power_switchgear_overview.glb). Seven beats: the medium-voltage feed into the house, the
// split into feeds, a fault cleared by its breaker, two paths to the hall, the generators waiting, the utility
// dropping, and the utility's return.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_switchgear_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_switchgear_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("from the yard to the switchgear house", BEAT_MS)
        .note(
            "Medium-voltage cable runs from the utility's transformers into a building full of breakers. The two transformers stand at the back, fed from the line; the switchgear house sits in front of them.",
            "Amber beads ride the three grey line conductors from the H-frame, through the two transformer tanks, and along the MV cables into the house's two metal-clad lineups, A and B.",
        )
        .detail(
            "Medium voltage is what the campus carries into the house.",
            &["MEDIUM VOLTAGE", "13.8-34.5 kV"],
        ),
    Beat::new("split into feeds", BEAT_MS)
        .note(
            "Breakers split the supply into feeds. Each feeder runs to a unit substation, which steps the power down to 480 V for the data hall.",
            "Copper bus bars run along the top of each lineup. Amber beads drop through the feeder breakers, and cyan 480 V beads leave each substation for the hall.",
        )
        .detail(
            "Each feed has its own breaker, so one can be isolated.",
            &["CIRCUIT BREAKER", "480 V in the US, 415 V elsewhere"],
        ),
    Beat::new("a fault: breakers open in milliseconds", BEAT_MS)
        .note(
            "A short on feeder 1 draws a surge of current. Its relay sees the fault within a cycle and trips the vacuum breaker, while the other feeders stay on.",
            "Red fault beads arc from feeder 1's cable to a glowing flash at its cabinet. The relay and the breaker's bottles light up; the other feeders keep their amber beads.",
        )
        .detail(
            "The breaker opens before the fault can wreck the gear.",
            &["PROTECTION RELAY", "Vacuum breakers at MV"],
        ),
    Beat::new("two of everything", BEAT_MS)
        .note(
            "Two complete paths, A and B, both feed the hall. When A's main opens for service, B carries the whole load without a break.",
            "Two mirror-image lineups with amber beads down both paths into the hall. The A main opens and its beads stop, while the B beads keep flowing into every rack row.",
        )
        .detail(
            "Each server takes one feed from each path.",
            &["2N / N+1", "Each path carries the whole load"],
        ),
    Beat::new("generators wait outside", BEAT_MS)
        .note(
            "A row of standby generators waits between the transformers, its breakers held open. The utility keeps feeding the house, and the transfer switch watches it.",
            "Two generator sets on the yard, each with an exhaust stack, and an ATS controller on the house wall. Amber beads still run down the utility line.",
        )
        .detail(
            "The generators sit idle until the utility drops.",
            &["ATS", "Generator breakers stay open"],
        ),
    Beat::new("outage: generators take over", BEAT_MS)
        .note(
            "The utility drops. The generators start, and the transfer switch opens the mains and closes the generator breakers, so the lineups run on green power.",
            "The utility line goes dark red. Green beads come from both generators into the lineups, and exhaust rises from their stacks.",
        )
        .detail(
            "The UPS batteries bridge the seconds before the generators take the load.",
            &["~10 s to start", "ATS moves the load"],
        ),
    Beat::new("utility back", BEAT_MS)
        .note(
            "When the grid returns, the transfer switch moves the load back to the utility and the generators run down and cool.",
            "The utility line glows amber again. The green beads thin out as the generator breakers open, and the exhaust fades.",
        )
        .detail(
            "A routine transfer for a data center.",
            &["Transfer back", "Generators cool down"],
        ),
];
