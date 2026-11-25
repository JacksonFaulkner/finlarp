// PACKAGING tab, BOARD: the overview, a Blender scene (tools/pbr3d/blender/pkg_board_overview.py, GLB
// tools/pbr3d/assets/pkg_board_overview.glb). Seven beats: the module cut open, the BGA balls, power climbing
// the levels, heat, the thermal stack, liquid cooling, and trays linked by NVLink.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_board_overview.py).
pub const BEATS: &[Beat] = &[
    Beat::new("the package on its module", BEAT_MS)
        .note(
            "The finished GPU package sits on a module board, cut through its middle here. Regulator phases line both sides, a cold plate covers the package, and an NVLink connector waits at the right edge.",
            "A green multilayer board cut open at the front: dark inductors and power stages down each side, a grey cold plate with blue and orange hoses over the package in the middle, and a black connector with teal cables at the right.",
        )
        .detail(
            "One module carries the package, its power and its links.",
            &["MODULE: package + power + connectors", "Cut through the middle"],
        ),
    Beat::new("BGA balls underneath", BEAT_MS)
        .note(
            "On the cut face, a row of solder balls joins the substrate to the board, each on a gold-finished copper pad. Plated vias drop from the board pads into the planes below.",
            "A low view of the cut face: half balls of silver solder in a row between the brown substrate above and the striped board below, copper vias running down from each pad.",
        )
        .detail(
            "Every amp and every signal crosses the ball field.",
            &["BGA BALLS: ~1 mm pitch", "Thousands per package"],
        ),
    Beat::new("power climbs the levels", BEAT_MS)
        .note(
            "Current leaves the inductors, runs through the board's thick power plane, and climbs a via, a ball, a through-hole in the substrate core, C4 bumps and the interposer's TSVs into the die.",
            "The substrate and interposer turn see-through; red beads drop from the inductors into a copper plane inside the board, run under the package and climb straight up through every layer into the purple dies.",
        )
        .detail(
            "Hundreds of amps at under a volt, up six levels.",
            &["POWER DELIVERY: plane > BGA > core > C4 > TSV", "Under 1 V at the die"],
        ),
    Beat::new("all of it becomes heat", BEAT_MS)
        .note(
            "Nearly every watt the GPU draws turns to heat in the dies. It climbs through TIM1, the lid and TIM2 into the cold plate.",
            "The dies glow amber; orange beads rise from them through the thin grey TIM layer, the silver lid and a pale pad into the copper plate above.",
        )
        .detail(
            "The die is the heat source; the stack above it is the way out.",
            &["~1,000 W per GPU (Blackwell class)", "Heat path: die > TIM1 > lid > TIM2"],
        ),
    Beat::new("lid, TIM and cold plate", BEAT_MS)
        .note(
            "The thermal stack, named layer by layer: TIM1 on the dies, a nickel-plated copper lid glued to the substrate, TIM2 on the lid, and a copper cold plate with skived fins.",
            "A close side view of the cut face above the dies: a thin grey layer, a thick silver lid with legs down to the substrate, a pale pad, a copper base and a comb of copper fins under a grey cover.",
        )
        .detail(
            "Each interface adds thermal resistance.",
            &["TIM1 + LID + TIM2", "COLD PLATE: skived copper fins"],
        ),
    Beat::new("liquid cooling", BEAT_MS)
        .note(
            "Coolant enters at the back, runs forward between the fins and leaves warm. At these power densities liquid replaces air.",
            "The plate's cover turns see-through; blue beads stream between the copper fins toward the cut face, a blue hose goes in and an orange hose comes out.",
        )
        .detail(
            "Water carries far more heat than air.",
            &["LIQUID COOLING: direct to chip", "Cool in, warm out"],
        ),
    Beat::new("trays linked by NVLink", BEAT_MS)
        .note(
            "Four modules sit on a compute tray. NVLink cables run from each module's connector at the back up to a switch tray, so many GPUs act as one.",
            "A tray from above: four brown modules with copper plates, blue and red coolant manifolds at the back, teal cables rising to a grey switch tray, cyan beads riding them.",
        )
        .detail(
            "Links tie modules into one big GPU.",
            &["NVLINK: GPU to switch", "Trays fill a RACK"],
        ),
];
