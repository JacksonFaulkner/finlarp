// PACKAGING tab, SUBSTRATE: the page's overview, a Blender scene (tools/pbr3d/blender/pkg_substrate_overview.py, GLB
// tools/pbr3d/assets/pkg_substrate_overview.glb). Seven beats: an FC-BGA substrate cut open along its front edge,
// its C4 bumps, the laminate inside, the BGA balls below, power and signals running through it, and warpage.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_substrate_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the substrate in the package", BEAT_MS)
        .note(
            "The package substrate sits between the silicon and the server board. The interposer, GPU die and HBM sit on top of it, and the board sits under it.",
            "A thick layered slab cut open along its front, drawn far thicker than life: a purple die and HBM stacks on a grey interposer at the top, a metal stiffener ring round the edge, solder balls under it on a green board.",
        )
        .detail(
            "The substrate is a small circuit board for one chip.",
            &["Organic FC-BGA substrate", "Between interposer and board"],
        ),
    Beat::new("C4 bumps on top", BEAT_MS)
        .note(
            "The interposer lands on the substrate through C4 solder bumps at about 150 um pitch. Each bump sits on a copper pad in an opening of the green solder resist, and underfill glues the gap.",
            "A close view of the top edge: a row of solder bumps, the front row cut in half, standing on copper pads in the green resist under the grey interposer, with dark see-through underfill around them.",
        )
        .detail(
            "Fine pitch on top: tens of thousands of bumps.",
            &["C4 pitch ~150 um", "Underfill holds the joints"],
        ),
    Beat::new("inside the laminate", BEAT_MS)
        .note(
            "A stiff core sits in the middle, with plated through-holes drilled through it. Build-up layers of ABF film and copper are laminated on each side; some copper layers are solid ground and power planes, the rest carry signal traces, and laser microvias stack between them.",
            "The cut face up close: a brown core with glass-cloth bundles and copper barrels through it, thin cream ABF films stacked above and below, solid copper planes, rows of copper dots that are traces, and tapered copper vias stacked on pads.",
        )
        .detail(
            "Core in the middle, build-up layers on both faces.",
            &["CORE + plated through-holes", "BUILD-UP LAYERS: ABF FILM + copper"],
        ),
    Beat::new("BGA balls below", BEAT_MS)
        .note(
            "Underneath, solder balls at about 1 mm pitch join the substrate to the board. Small capacitors sit on the underside between the balls, close to the die, as a local charge reserve.",
            "A low view along the bottom: big silver balls, the front row cut in half, between copper pads on the substrate and the green board, with small tan capacitors with silver ends between them.",
        )
        .detail(
            "Coarse pitch below, matched to the board.",
            &["BGA pitch ~1 mm", "Land-side capacitors"],
        ),
    Beat::new("power comes up through it", BEAT_MS)
        .note(
            "Power from the board climbs through the BGA balls and the core's plated holes, then spreads across the copper planes to the bumps under the die. Wide solid planes keep the resistance low at very high currents.",
            "Yellow beads rise from the balls, up copper barrels through the core, run along two glowing copper planes and climb into the bumps under the purple die; orange heat rises off the die.",
        )
        .detail(
            "Planes carry power; through-holes cross the core.",
            &["Power planes", "PTH through the core"],
        ),
    Beat::new("signals fan out", BEAT_MS)
        .note(
            "Each signal drops from its bump down a stack of microvias to its own layer, runs out sideways, drops through the core and lands on a ball. Inner bumps take deeper layers so no trace crosses another's via.",
            "Cyan beads run from the bumps down stacked copper vias, along glowing cyan traces on different layers, down through the core and into balls spread much wider apart.",
        )
        .detail(
            "Fan-out turns 150 um into about 1 mm.",
            &["FAN-OUT", "One layer per group of bumps"],
        ),
    Beat::new("warpage", BEAT_MS)
        .note(
            "The laminate is large and thin, and its copper, resin and glass expand at different rates. In the reflow oven it bows, and as it cools it bows the other way, straining the bumps and balls at its ends.",
            "The substrate alone as a hinged slab over the board: heat rises, it bends with its middle up and ends down, then flexes back with its ends up.",
        )
        .detail(
            "A big laminate fights to stay flat.",
            &["WARPAGE", "Worse as packages grow"],
        ),
];
