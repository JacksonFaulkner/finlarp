// NETWORK+COOL tab, CDU: the page's overview, a Blender scene (tools/pbr3d/blender/net_cdu_overview.py, GLB
// tools/pbr3d/assets/net_cdu_overview.glb). Seven beats: an in-row CDU beside its rack, the two loops, the pumps,
// the cold plates, the plate heat exchanger, the controls, and both loops running.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match net_cdu_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("an in-row CDU", BEAT_MS)
        .note(
            "A coolant distribution unit stands in the row beside the liquid-cooled rack it feeds. Inside: a plate heat exchanger, two pumps, a filter, a reservoir and a controller.",
            "A tall dark cabinet cut open at the left, a blue-framed plate stack near its top and two blue pumps at its floor; a rack of green server trays with copper cold plates stands to its right.",
        )
        .detail(
            "The CDU sits between the building's water and the servers.",
            &["CDU: in-row", "Rack: liquid-cooled"],
        ),
    Beat::new("two loops", BEAT_MS)
        .note(
            "Facility water rises from under the floor into the plate heat exchanger and goes straight back down. It never reaches the servers: a separate sealed secondary loop runs from the CDU to the rack.",
            "Blue beads climb a blue pipe from the floor into the plate stack and leave down a second blue pipe; orange beads run along the copper return pipe over the cabinet.",
        )
        .detail(
            "Two loops meet only across the exchanger's plates.",
            &["FACILITY LOOP", "SECONDARY LOOP"],
        ),
    Beat::new("the pumps drive it", BEAT_MS)
        .note(
            "Pump A spins and pushes coolant round the secondary loop: out of the reservoir, through the pump and the filter, up through the exchanger and out to the rack's supply manifold.",
            "The cut-open blue volute shows a spinning gold impeller; orange beads run from the reservoir down to the pump, up through the grey filter canister, and cyan beads leave the plate stack for the rack.",
        )
        .detail(
            "Pumps set the flow; the loop is closed.",
            &["PUMP: variable speed", "~1.5 L/min per kW"],
        ),
    Beat::new("cold plates take the heat", BEAT_MS)
        .note(
            "Cool supply flows through every tray's cold plates, sitting on the GPUs. The coolant leaves each tray about 10 C warmer and rises up the return manifold back to the CDU.",
            "Cyan beads leave the supply manifold at the back of the rack into each tray's copper cold plates; orange beads come out and climb the return manifold; the purple GPU dies glow with heat rising.",
        )
        .detail(
            "About 1 kW per GPU goes into the water.",
            &["COLD PLATE", "~10 C rise"],
        ),
    Beat::new("across the plates", BEAT_MS)
        .note(
            "In the plate heat exchanger the warm secondary water and the cold facility water flow through alternate gaps, in opposite directions. Heat crosses the thin steel plates; facility water leaves warmer, back toward the chiller or cooling tower.",
            "Close on the blue-framed stack of grey plates: cyan beads zig-zag up its face, blue beads zig-zag down, and small orange sparks hop between neighbouring plates.",
        )
        .detail(
            "Counterflow keeps the two streams a few degrees apart.",
            &["PLATE HEAT EXCHANGER", "APPROACH: ~2-4 C"],
        ),
    Beat::new("sensors and the controller", BEAT_MS)
        .note(
            "Temperature, pressure and flow sensors on every pipe report to the controller. It trims the facility valve to hold the supply temperature and keeps pump B ready to take over.",
            "Green LEDs blink on small sensor stubs along the pipes; yellow beads run from each to the white controller box at the top, whose blue screen flickers; a yellow valve actuator sits on the facility pipe.",
        )
        .detail(
            "The controller holds supply temperature and flow.",
            &["CONTROLLER (PLC)", "N+1 pumps"],
        ),
    Beat::new("both loops running", BEAT_MS)
        .note(
            "Everything at once: facility water through the exchanger, the secondary loop through the pump, filter and rack, heat crossing the plates. One in-row CDU like this can serve a row of racks.",
            "The whole cabinet and rack in view: blue beads in the facility pipes, orange and cyan beads round the secondary loop, and sparks across the plate stack.",
        )
        .detail(
            "Heat leaves the GPU and ends up in facility water.",
            &["FACILITY LOOP", "SECONDARY LOOP"],
        ),
];
