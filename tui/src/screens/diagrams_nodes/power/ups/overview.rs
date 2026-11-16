// POWER tab, UPS: the page's overview, a Blender scene (tools/pbr3d/blender/power_ups_overview.py, GLB
// tools/pbr3d/assets/power_ups_overview.glb). Seven beats: the normal double-conversion flow, the batteries
// charged, the utility dropping, the batteries carrying the load, the generator starting, the transfer
// switch moving the load, and the losses of two conversions.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_ups_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("utility through the UPS to the racks", BEAT_MS)
        .note(
            "Power passes the transfer switch, then the UPS's rectifier and inverter, into the racks. Double conversion means the load always runs from the inverter, so the racks are fed clean AC that has been turned to DC and back.",
            "Yellow beads ride the cables from the utility pole through the transfer switch and the grey UPS cabinets to a row of green-lit racks at the right. Diesel generator and battery cabinets sit beside the site.",
        )
        .detail(
            "Two conversions sit between the grid and the racks.",
            &["AC > DC > AC", "Rectifier, then inverter"],
        ),
    Beat::new("batteries stay charged", BEAT_MS)
        .note(
            "The DC link keeps the lithium-ion battery cabinets topped up. Their module LEDs fill as the cells charge, and cyan beads run from the link out to the cabinets behind the UPS.",
            "Blue battery cabinets in a row, their small green LEDs lighting up module by module; cyan dots travel from the DC link across the cable arcs to them.",
        )
        .detail(
            "Lithium-ion cells replace lead-acid in UPS rooms.",
            &["LITHIUM-ION", "Minutes of runtime, not hours"],
        ),
    Beat::new("the utility drops", BEAT_MS)
        .note(
            "The utility feed fails. The line from the pole goes red, but the inverter keeps running from the batteries, so the racks see no break in their supply.",
            "The utility cable turns red at the pole; orange battery power flows along the arcs to the inverter, which stays lit.",
        )
        .detail(
            "The inverter never stops, so the outage is invisible to the load.",
            &["Battery feeds the DC link", "No break at the racks"],
        ),
    Beat::new("batteries carry the load", BEAT_MS)
        .note(
            "For the next minutes, all the power comes from the battery modules. Their LEDs go out one by one as the cells drain, and the racks stay fed until the generator is up.",
            "The battery cabinets dim module by module; orange dots flow from them to the inverter and out to the racks. A label marks the runtime as minutes.",
        )
        .detail(
            "Runtime is sized for minutes, enough to cover generator start.",
            &["RUNTIME: typically minutes", "Batteries bridge the gap"],
        ),
    Beat::new("the generator starts", BEAT_MS)
        .note(
            "The diesel generator's engine turns over: pistons move, the crankshaft spins and the alternator begins to rotate. Within about ten seconds it reaches the voltage and frequency it needs. Exhaust rises from the stack beside it.",
            "A grey diesel engine with its row of pistons at the left and a copper-wound alternator at the right, both spinning up; a thin exhaust plume rises from the stack.",
        )
        .detail(
            "Standby power within 10 seconds (NFPA 110 Type 10).",
            &["~10 s to voltage", "~2-3 MW per unit"],
        ),
    Beat::new("the transfer switch moves the load", BEAT_MS)
        .note(
            "The transfer switch's blade swings from the utility to the generator, so green generator power flows into the UPS input. Once the generator is carrying the site, the batteries start to recharge.",
            "The transfer switch at the centre of the site changes its position; green beads run from the generator to the UPS, and the battery modules begin to fill again.",
        )
        .detail(
            "The switch moves the UPS input from utility to generator.",
            &["TRANSFER SWITCH", "Batteries recharge"],
        ),
    Beat::new("two conversions cost a few percent", BEAT_MS)
        .note(
            "With the utility back and the load moved home, the UPS runs normally again. Every watt is rectified and inverted, and heat rises off the rectifier and inverter cabinets as the conversions lose a few percent.",
            "Normal running: yellow beads through the cabinets again, with rising heat shimmer and the labels for the rectifier and the inverter.",
        )
        .detail(
            "Eco modes bypass the conversion when the utility is clean.",
            &["3-5% loss (this page's example)", "EFFICIENCY: power out / in"],
        ),
];
