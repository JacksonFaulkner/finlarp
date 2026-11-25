// NETWORK+COOL tab, CDU: lettered zoom-ins a-e. Each is the overview's CDU and rack with the camera held on one
// subject (tools/pbr3d/blender/net_cdu_zooms.py, GLBs in tools/pbr3d/assets/net_cdu_zoom_<letter>.glb):
// a plate heat exchanger, b pumps, c filter and reservoir, d sensors and controls, e in-rack vs in-row.

use super::super::super::blender::{page, Cell};
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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the plate stack", BEAT_MS)
        .note(
            "The exchanger is a stack of pressed stainless plates clamped between two frame plates. Secondary water enters warm at the bottom and leaves cool at the top.",
            "A blue frame holding a grey accordion of plates; cyan beads zig-zag up across its face from a pipe at the lower right.",
        )
        .detail(
            "Thin plates give a huge area in a small box.",
            &["PLATE HEAT EXCHANGER"],
        ),
    Beat::new("facility in the other gaps", BEAT_MS)
        .note(
            "Facility water runs through the alternate gaps, entering cold at the top and leaving warmer at the bottom. The two fluids never mix.",
            "Blue beads drop into the top-left port of the stack and zig-zag down its face to the lower-left port.",
        )
        .detail(
            "Two fluids, alternate gaps, opposite directions.",
            &["FACILITY LOOP", "Counterflow"],
        ),
    Beat::new("heat crosses the steel", BEAT_MS)
        .note(
            "Heat passes through roughly half a millimetre of steel from each warm gap to the cold gap beside it. Running the fluids in counterflow lets the supply leave within a few degrees of the facility water.",
            "Both bead streams at once, with small orange sparks hopping sideways between plates; tie bolts glint along the top and bottom.",
        )
        .detail(
            "The approach is the gap between the two streams.",
            &["APPROACH: ~2-4 C"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("pump A running", BEAT_MS)
        .note(
            "Pump A pushes the secondary loop round. Its volute is cut open to show the impeller; a motor with a variable-speed drive sits behind it.",
            "A blue pump body, cut open with a gold six-bladed impeller spinning inside; a grey finned motor behind it with a small grey drive box and a green LED.",
        )
        .detail(
            "The pump sets the loop's flow.",
            &["PUMP: variable speed"],
        ),
    Beat::new("pump B on standby", BEAT_MS)
        .note(
            "A second identical pump shares the suction header and waits on standby. Either pump alone can carry the full flow, the N+1 arrangement.",
            "Two blue pumps side by side on a copper header; the second pump's amber LED blinks.",
        )
        .detail(
            "One spare pump for every duty pump.",
            &["N+1 pumps"],
        ),
    Beat::new("B takes over", BEAT_MS)
        .note(
            "If pump A trips, the controller starts pump B within seconds and flow to the rack is held. Pumps can then be swapped while the CDU keeps running.",
            "The second pump's impeller now spins and orange beads run through it and up the discharge pipe.",
        )
        .detail(
            "Redundancy keeps the GPUs cooled.",
            &["N+1 pumps", "Hot-swap"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("the strainer", BEAT_MS)
        .note(
            "On the pump discharge, a canister filter strains particles out of the coolant before it reaches the exchanger and the cold plates' fine channels.",
            "A grey canister cut open down its middle, showing a cream pleated element; orange beads pass up through it; a white gauge sits at its top.",
        )
        .detail(
            "Cold plate channels are fractions of a millimetre wide.",
            &["FILTER: ~25-50 micron"],
        ),
    Beat::new("the reservoir", BEAT_MS)
        .note(
            "A reservoir, or expansion tank, holds spare coolant and takes up its swelling as it warms. A sight glass shows the level.",
            "A tall pale tank beside the controller with orange beads dropping into its top; a dark strip runs down its side.",
        )
        .detail(
            "The tank keeps the pumps fed and the pressure steady.",
            &["RESERVOIR"],
        ),
    Beat::new("clean coolant", BEAT_MS)
        .note(
            "Clean, treated coolant protects the cold plates. A rising pressure drop across the filter tells the controller it needs changing.",
            "Wide view: the filter canister in the cabinet, the rack's trays and cold plates beyond it.",
        )
        .detail(
            "Filtration is routine maintenance.",
            &["FILTER", "COLD PLATE"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("sensors report", BEAT_MS)
        .note(
            "Supply and return temperature, pressure and flow sensors report to the controller, a PLC with a touch screen.",
            "Green LEDs blink on sensor stubs along the pipes; yellow beads run up to a white box with a blue screen.",
        )
        .detail(
            "The controller sees every pipe.",
            &["CONTROLLER (PLC)", "T / P / flow"],
        ),
    Beat::new("the valve trims", BEAT_MS)
        .note(
            "To hold the supply temperature, the controller opens or closes the valve on the facility supply, letting more or less cold water through the exchanger.",
            "A red valve body with a yellow actuator on the blue facility pipe; a small flag on top turns as blue beads pass.",
        )
        .detail(
            "More facility flow, more heat removed.",
            &["Control valve", "Supply temp setpoint"],
        ),
    Beat::new("leak detection", BEAT_MS)
        .note(
            "A drip from a tray falls onto a leak-sensing rope on the floor. The controller raises an alarm and can isolate the loop.",
            "Red drops fall from a tray in the rack; a glowing amber strip lines the cabinet floor; a red LED on the controller blinks.",
        )
        .detail(
            "Water near servers is the main fear.",
            &["Leak detection"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("in-rack CDU", BEAT_MS)
        .note(
            "An in-rack CDU is a 4U box at the bottom of one rack, with its own small brazed-plate exchanger, two pumps and a reservoir.",
            "A low grey box under the bottom tray, lid off: a copper and steel plate block, two blue pump cylinders and a small tank; blue and cyan beads flow through it.",
        )
        .detail(
            "One rack, one CDU.",
            &["IN-RACK CDU"],
        ),
    Beat::new("one rack", BEAT_MS)
        .note(
            "It serves only its own rack, about 100 to 250 kW, and takes no floor space. Supermicro sells a 250 kW in-rack unit.",
            "The full rack with its in-rack unit at the base; cyan beads rise through the trays and orange beads return.",
        )
        .detail(
            "No floor space, but a fixed capacity.",
            &["IN-RACK CDU", "~100-250 kW"],
        ),
    Beat::new("in-row: the whole row", BEAT_MS)
        .note(
            "An in-row CDU stands in the row and feeds many racks through a header over the top. Large units are rated around 1 to 2 MW or more.",
            "The view pulls back: the CDU cabinet at the left, four racks to its right, cyan and orange beads riding headers over the row and down each rack.",
        )
        .detail(
            "One unit, many racks, a megawatt or more.",
            &["IN-ROW CDU", "~1-2 MW+"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "plate heat exchanger",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "pumps",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "filter and reservoir",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "sensors and controls",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "in-rack vs in-row",
        build: zoom_e,
    },
];
