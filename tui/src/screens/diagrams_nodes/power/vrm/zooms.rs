// POWER tab, VRM: lettered zoom-ins a-e. Each is the overview's board with the camera held on one subject
// (tools/pbr3d/blender/power_vrm_zooms.py, GLBs in tools/pbr3d/assets/power_vrm_zoom_<letter>.glb):
// a 50 V to 12 V, b multiphase, c why over a thousand amps, d I2R loss, e vertical power.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the busbar", BEAT_MS)
        .note(
            "About 50 V DC rides the busbar at the board's edge and feeds the converter brick. Yellow beads run along the copper bar into the brick's input.",
            "A brown copper bar at the left, with yellow beads on it running into the grey brick's side, which is cut open at its corner.",
        )
        .detail(
            "The busbar is the rack's shared 50 V supply.",
            &["~50 V DC", "Busbar: rack bus"],
        ),
    Beat::new("the brick cut open", BEAT_MS)
        .note(
            "Inside the brick, a transformer and its switches step the 50 V down. Its output leaves as a 12 V tab on the board.",
            "The brick's cover is lifted: a dark primary switch bank at the left, a copper transformer in the middle, and rectifier FETs on the right with a small 12 V tab.",
        )
        .detail(
            "The brick is the intermediate bus converter.",
            &["INTERMEDIATE BUS: 50 V > 12 V", "Transformer, switches, rectifier"],
        ),
    Beat::new("12 V across the bare plane", BEAT_MS)
        .note(
            "The 12 V spreads across a bare copper plane to every power stage. Each stage takes its share from the plane beside it.",
            "A tan plane laid bare, with amber dots spreading out from the 12 V tab to the row of power stages along its edge.",
        )
        .detail(
            "The plane carries 12 V to every phase.",
            &["12 V plane", "12 V to every stage"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("one phase", BEAT_MS)
        .note(
            "A phase is one power stage and one inductor. The stage chops 12 V into pulses, and the inductor smooths them into steady current for the GPU.",
            "A dark power stage chip with its heatsink on top, feeding a copper-wound inductor block in grey beside it; amber dots run from the stage into the inductor.",
        )
        .detail(
            "Each phase carries only tens of amps.",
            &["POWER STAGE: chops 12 V", "INDUCTOR: smooths it", "Tens of amps each"],
        ),
    Beat::new("sixteen phases in turn", BEAT_MS)
        .note(
            "The controller fires the phases in turn, so their pulses are staggered and the current arrives in steps that overlap. Each phase lights up in order around the board.",
            "The row of phases along both sides of the board, lit one after another in a rolling wave of amber; the controller in its grey block glows at the centre.",
        )
        .detail(
            "Staggered phases share the load.",
            &["16 phases", "Fired in turn", "Controller sets the order"],
        ),
    Beat::new("together: 1,000+ A", BEAT_MS)
        .note(
            "All the phases' currents meet at the GPU die. Together they feed more than a thousand amps into the package, far more than any one phase could carry.",
            "Every inductor's current, drawn as a bright amber stream, converging on the purple GPU die at the centre of the board, which glows hot.",
        )
        .detail(
            "One regulator cannot carry this current alone.",
            &["Multiphase: 1,000+ A", "Infineon 16-phase design, 2019"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("the GPU's watts", BEAT_MS)
        .note(
            "A Blackwell-class GPU draws roughly 1,000 to 1,200 W. That is the power the regulator must deliver, and it is the number the board is built around.",
            "The GPU package on top of the board: a grey substrate with a purple die and HBM stacks on either side; the die glows amber.",
        )
        .detail(
            "The GPU is the load the whole board serves.",
            &["~1,000-1,200 W", "HBM beside the die"],
        ),
    Beat::new("the 0.8 V core", BEAT_MS)
        .note(
            "The core runs at about 0.8 V, so the current is the power divided by that low voltage. Current flows up through the package bumps from the board below.",
            "A thin amber plane at the die face, with bumps beneath it in a grid and the substrate as a grey slab underneath.",
        )
        .detail(
            "Core voltage is set low for the transistors.",
            &["CORE VOLTAGE ~0.8 V", "Through the bumps"],
        ),
    Beat::new("the amps that makes", BEAT_MS)
        .note(
            "P = V x I: at about 0.8 V, 1,000 to 1,200 W becomes 1,250 to 1,500 A. Current of that size cannot come through a single regulator, so the phases share it.",
            "The die face lit up, with the current arrows from both sides meeting there; the power equation floats beside the die.",
        )
        .detail(
            "Low volts, high amps.",
            &["~1,250-1,500 A", "P = V x I"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("current squared times R", BEAT_MS)
        .note(
            "Loss in the copper goes with the square of the current: double the amps and the heat goes up four times. At these currents even tiny resistances waste a lot of power.",
            "Two inductors side by side: the one at the right is carrying twice the current and glows far hotter than the one at the left.",
        )
        .detail(
            "Heat goes with the square of the current.",
            &["I2R LOSS: current squared", "2x the amps, 4x the heat"],
        ),
    Beat::new("the 0.8 V plane runs hot", BEAT_MS)
        .note(
            "The copper plane carrying 0.8 V is hot along its length, because the current crosses it on the way to the die. A tenth of a milliohm at 1,500 A wastes about 225 W there.",
            "The bare 0.8 V copper plane glowing orange along its length, with a bright hot spot at the centre where the current crosses it.",
        )
        .detail(
            "The plane's resistance is tiny, but the current is not.",
            &["0.1 mOhm at 1,500 A = 225 W", "Hot 0.8 V plane"],
        ),
    Beat::new("regulators under the GPU", BEAT_MS)
        .note(
            "Every millimetre between the regulator and the chip costs power and voltage. Vertical designs put the regulators under the GPU, so the path is shorter.",
            "The regulator modules sit beneath the purple die on the board's back, with a short amber path running straight up to the package.",
        )
        .detail(
            "The path shrinks to millimetres.",
            &["Regulators under the GPU", "Path: millimetres"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("beside the GPU", BEAT_MS)
        .note(
            "Today the regulators sit beside the GPU, and the current has to cross the whole board to reach the package. That crossing is where much of the loss happens.",
            "The usual layout: a row of dark phases and inductors along the side of the board, with amber current arcing across the green board to the GPU.",
        )
        .detail(
            "The current crosses the board sideways.",
            &["Phases beside the GPU", "Current crosses the board"],
        ),
    Beat::new("modules move under", BEAT_MS)
        .note(
            "The vertical design moves the modules off the sides and onto the back of the board, directly under the package. The side phases slide away as the modules move in.",
            "The side phases fade out; grey vertical modules slide into a row on the board's back beneath the purple GPU package.",
        )
        .detail(
            "Vertical power is on the back of the board.",
            &["VERTICAL POWER: on the back", "Modules under the GPU"],
        ),
    Beat::new("straight up", BEAT_MS)
        .note(
            "Current now goes straight up through the board into the package, a path of millimetres instead of centimetres. Crescendo's 16 stacked regulators showed close to 1,000 A at 0.75 V this way.",
            "A column of amber current rising through the board straight into the purple GPU die; the modules glow at the base of the column.",
        )
        .detail(
            "Crescendo: 16 stacked regulators.",
            &["~1,000 A at 0.75 V", "Infineon modules: 2026"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "50 V to 12 V",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "multiphase",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "why over a thousand amps",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "I2R loss",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "vertical power",
        build: zoom_e,
    },
];
