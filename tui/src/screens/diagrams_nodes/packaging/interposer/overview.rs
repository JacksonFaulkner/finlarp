// PACKAGING tab, INTERPOSER: the page's overview, a Blender scene (tools/pbr3d/blender/pkg_interposer_overview.py,
// GLB tools/pbr3d/assets/pkg_interposer_overview.glb). One CoWoS package cut open along its front face. Seven beats:
// the whole stack, data across the interposer, power up through the TSVs, the layers named, CoWoS-L's bridges,
// growing past the reticle, and the lidded package on its board.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_interposer_overview.py).
pub const BEATS: &[Beat] = &[
    Beat::new("the interposer: wiring under the dies", BEAT_MS)
        .note(
            "A GPU die and its HBM stacks do not sit on the package substrate directly. They sit side by side on an interposer, a slab of very fine wiring, which sits on the substrate, which sits on the board. TSMC calls the assembly CoWoS: chip on wafer on substrate.",
            "The package cut open along its front face: a green board, a brown substrate with a pale core, a row of silver C4 balls, the grey silicon interposer, then a purple GPU die between two striped orange HBM stacks.",
        )
        .detail(
            "The interposer is the only layer fine enough to join GPU and HBM.",
            &["CoWoS = chip on wafer on substrate", "Board > substrate > interposer > dies"],
        ),
    Beat::new("data runs across it", BEAT_MS)
        .note(
            "Each HBM stack talks to the GPU over a very wide, slow bus: 1,024 data wires per HBM3 stack, 2,048 in HBM4. The bits leave the stack's base die through microbumps, drop into the interposer's copper wiring, run a few millimetres sideways and climb into the GPU.",
            "Close on the right stack and the die edge: cyan beads drop out of the blue base die, run left through the copper lines in the interposer's top layer and rise into the purple die.",
        )
        .detail(
            "Thousands of short wires in parallel give HBM its bandwidth.",
            &["1,024 bits per HBM3 stack", "2,048 bits per HBM4 stack"],
        ),
    Beat::new("power climbs up through TSVs", BEAT_MS)
        .note(
            "Power goes the other way. It comes from the board through the BGA balls, up plated holes in the substrate core, through the C4 bumps and then through-silicon vias: copper columns straight through the interposer, into the die.",
            "Yellow beads climb from the board through the substrate's copper, through the silver C4 balls and up the copper columns that cross the grey silicon, into the die.",
        )
        .detail(
            "Every amp the GPU draws passes through the TSV array.",
            &["TSV: copper through silicon", "C4 bumps: interposer to substrate"],
        ),
    Beat::new("layer by layer", BEAT_MS)
        .note(
            "Each layer has a job. The interposer's top is a back-end-of-line stack: four copper wiring levels in oxide. Below it, the silicon body carries the TSVs. C4 bumps join it to the substrate, which is ABF build-up film with copper lines around a glass-fibre core.",
            "Low and close on the left: the pale oxide band with copper dashes on top of the interposer, grey silicon with copper columns, silver C4 balls, and the substrate's dark build-up layers around its pale core.",
        )
        .detail(
            "Pitch gets coarser at every step down the stack.",
            &["BEOL: M1-M4 copper in oxide", "Substrate: ABF build-up + core"],
        ),
    Beat::new("CoWoS-L: silicon bridges", BEAT_MS)
        .note(
            "A full silicon slab gets expensive and hard to make past about 3.3 reticles. CoWoS-L swaps it for an organic interposer of polymer and copper layers, with small silicon bridge chips sunk only under the joints between dies and between dies and HBM. NVIDIA's Blackwell uses it.",
            "The same cut, but the interposer is dark with a tan wiring layer and copper pillars; cyan bridge chips sit under the gaps between two purple dies and each stack, and cyan beads cross through them.",
        )
        .detail(
            "Silicon only where the finest wires are needed.",
            &["COWOS-L: organic + LSI bridges", "Blackwell: ~10 TB/s die to die"],
        ),
    Beat::new("growing past the reticle", BEAT_MS)
        .note(
            "A lithography reticle prints at most about 26 x 33 mm, so interposer size is counted in reticles. CoWoS-S reaches about 3.3 (about 2,700 mm2). TSMC's roadmap has 9.5-reticle interposers with 12 HBM stacks in 2027 and over 14 reticles by 2029.",
            "Seen from above, to one scale: a single die-sized reticle, a CoWoS-S package in a 2x2 grid of glowing reticle outlines, and a much larger organic package with two dies and twelve stacks inside a 4x3 grid.",
        )
        .detail(
            "Bigger interposers carry more HBM.",
            &["COWOS-S ~3.3x reticle", "9.5x, 12 HBM (2027 plan)"],
        ),
    Beat::new("the lidded package on its board", BEAT_MS)
        .note(
            "Finally a thermal interface material and a metal lid go on top, and the package sits on its board on a grid of BGA balls. The GPU's heat leaves through the lid into the cold plate above it.",
            "The full cut-away again, now under a grey lid with a pale TIM layer over the die and stacks; the die glows orange and heat beads rise out of the lid's top.",
        )
        .detail(
            "Almost every top AI accelerator uses CoWoS, so its capacity limits shipments.",
            &["TIM + lid, then the cold plate", "CoWoS capacity"],
        ),
];
