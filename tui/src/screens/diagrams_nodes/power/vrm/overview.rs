// POWER tab, VRM: the page's overview, a Blender scene (tools/pbr3d/blender/power_vrm_overview.py, GLB
// tools/pbr3d/assets/power_vrm_overview.glb). Seven beats: a GPU board, 50 V in and 12 V out, 12 V to each phase,
// about 0.8 V at over a thousand amps, the losses of every millimetre, vertical power under the GPU, and the
// whole chain from the grid to the transistor.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_vrm_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a GPU board", BEAT_MS)
        .note(
            "A GPU sits in the middle of its board, ringed by the regulator that feeds it. Eight phases run down each side, a controller sits behind them, and the 50 V to 12 V brick waits at the left edge.",
            "A cut-open green board: a grey GPU package in the centre with a purple die, rows of dark power stages and copper inductors down each side, a grey controller block behind, and a grey brick at the left edge.",
        )
        .detail(
            "One regulator per GPU, built from many phases.",
            &["MULTIPHASE: 16 phases, 8 a side", "One regulator per GPU"],
        ),
    Beat::new("50 V in, 12 V out", BEAT_MS)
        .note(
            "Rack power arrives as about 50 V DC on the busbar. A bus converter brick steps it down to 12 V, the intermediate bus that the phases run from.",
            "A copper busbar runs in from the left edge with yellow beads riding it into the grey brick, cut open to show its transformer; amber beads leave the brick toward the bare plane.",
        )
        .detail(
            "The intermediate bus splits one large step into two.",
            &["~50 V > 12 V", "INTERMEDIATE BUS"],
        ),
    Beat::new("12 V to each phase", BEAT_MS)
        .note(
            "The 12 V spreads across the bare plane to every phase. A controller sends each power stage its switching timing over thin traces, one stage after another.",
            "Amber dots spread across the tan 12 V plane; thin green traces run from the controller to a row of dark power stage chips on each side.",
        )
        .detail(
            "Each phase switches many times a second.",
            &["MULTIPHASE: phases in turn", "~100,000s of switches a second"],
        ),
    Beat::new("~0.8 V at over a thousand amps", BEAT_MS)
        .note(
            "The inductors smooth the pulses into steady current at about 0.8 V, and that current runs up into the GPU die. A GPU drawing 1,000 to 1,200 W takes about 1,250 to 1,500 A at that voltage.",
            "Dark inductor blocks with copper windings; hot red current streams from them across the middle of the board and up into the purple GPU die, which glows amber.",
        )
        .detail(
            "P = V x I: a low voltage means a huge current.",
            &["CORE VOLTAGE ~0.8 V", "~1,250-1,500 A"],
        ),
    Beat::new("every millimetre costs watts", BEAT_MS)
        .note(
            "Loss goes with the current squared, so at 1,500 A even a tenth of a milliohm of copper wastes about 225 W. The heat rises from the inductors and the GPU's edge.",
            "Orange heat shimmer over the inductor row and the GPU package; short red bars mark the copper path between them.",
        )
        .detail(
            "I2R loss grows with the square of the current.",
            &["I2R LOSS: current squared", "~225 W at 0.1 mOhm, 1,500 A"],
        ),
    Beat::new("vertical power: under the GPU", BEAT_MS)
        .note(
            "Vertical power moves the regulators under the GPU, onto the back of the board, so the current goes straight up through the board instead of across it. The side phases go, and modules sit under the package.",
            "The phases slide off the sides of the board; below the purple GPU a row of grey modules sits on the back, and amber current climbs straight up through the board.",
        )
        .detail(
            "The high-current path shrinks to millimetres.",
            &["VERTICAL POWER: on the back", "Infineon modules: 2026"],
        ),
    Beat::new("from the grid to the transistor", BEAT_MS)
        .note(
            "The whole board runs at once: the busbar, the brick, the phases and the GPU all carry current together. The chain from a 50 V busbar down to a 0.8 V transistor steps the voltage down about 60 times.",
            "Every path lit at once: the busbar and brick at the left, the phases down both sides, and the GPU package in the middle with its die glowing.",
        )
        .detail(
            "One board, one chain, one set of losses.",
            &["50 V busbar > 0.8 V core", "~60x step-down (50 / 0.8)"],
        ),
];
