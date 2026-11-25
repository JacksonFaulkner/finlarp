// PACKAGING tab, LOGIC DIE: the page's overview, a Blender scene (tools/pbr3d/blender/pkg_logic_die_overview.py, GLB
// tools/pbr3d/assets/pkg_logic_die_overview.glb). Seven beats: the package cut open, inside one die, the reticle
// field, the HBM shoreline, two dies and their bridge, power up from the board, and heat out the top.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_logic_die_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_logic_die_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the logic die in its package", BEAT_MS)
        .note(
            "The logic die is the GPU itself. Here two of them sit on a silicon interposer beside their HBM stacks, over an organic substrate, solder balls and the board, all under a lid. The package is cut open along its front edge so every layer shows.",
            "A cut-open package: two purple dies under a see-through lid, gold HBM stacks at the sides, a grey interposer, a layered brown substrate, rows of silver balls and a green board.",
        )
        .detail(
            "Every layer of the package exists to feed and cool the logic die.",
            &["Two logic dies (B200-style)", "Interposer, substrate, board"],
        ),
    Beat::new("inside one die", BEAT_MS)
        .note(
            "The die is mounted flip-chip: its wiring faces down. At the bottom is the metal stack, more than a dozen copper levels, sitting on the microbumps. Above it is the thin transistor layer, and on top is bare bulk silicon that touches the lid.",
            "Close on the cut face of one die: rows of tiny bumps at the bottom, a pale banded metal stack with copper lines, a thin teal transistor layer, and a thick purple slab of silicon on top.",
        )
        .detail(
            "Transistors face the bumps; the backside faces the cooler.",
            &["FLIP-CHIP: wiring down", "Metal stack ~15 levels"],
        ),
    Beat::new("the reticle field", BEAT_MS)
        .note(
            "A scanner prints one field at a time, at most 26 x 33 mm, or 858 mm2. One die fills almost the whole field. Its floorplan shows rows of compute tiles and an L2 cache band across the middle.",
            "Looking down with the lid gone: two purple dies covered in lilac tiles, with a pink rectangle drawn tight around the right-hand die.",
        )
        .detail(
            "No single die can be bigger than one exposure.",
            &["RETICLE LIMIT: 26 x 33 mm", "858 mm2"],
        ),
    Beat::new("the HBM shoreline", BEAT_MS)
        .note(
            "Memory connects along the die's outer edge. A strip of HBM interface circuits sits there, and thousands of fine wires in the interposer's top layers carry data out to the stacks and back.",
            "Close on the left edge: cyan beads drop from the die's edge through the bumps, run along copper lines in the interposer, and climb into the base of a gold HBM stack.",
        )
        .detail(
            "Edge length limits how much memory a die can reach.",
            &["HBM SHORELINE", "~8 TB/s (B200)"],
        ),
    Beat::new("two dies, one GPU", BEAT_MS)
        .note(
            "Two dies are joined by a short silicon bridge sunk into the interposer under the gap. Wires through the bridge carry about 10 TB/s between them, enough that software sees one GPU.",
            "Close on the gap between the dies: a teal bridge inside the grey interposer, with green beads crossing it from one die to the other in both directions.",
        )
        .detail(
            "Chiplets get past the reticle limit at the cost of a link.",
            &["CHIPLETS + DIE-TO-DIE", "~10 TB/s (B200)"],
        ),
    Beat::new("power up from the board", BEAT_MS)
        .note(
            "Current climbs from the board's power planes through a BGA ball, a plated hole in the substrate core, a C4 bump, a TSV in the interposer and a microbump, then fans out through the metal stack to the transistors.",
            "Yellow beads rise in columns from the green board through silver balls, the brown substrate, the grey interposer and the bumps into the purple dies.",
        )
        .detail(
            "A thousand amps or more cross every layer of the stack.",
            &["BGA > core > C4 > TSV > bump", "~0.8 V core"],
        ),
    Beat::new("heat out the top", BEAT_MS)
        .note(
            "The logic die makes most of the package's heat, around a kilowatt for a top GPU. It leaves through the thermal interface material and the lid into a cold plate above.",
            "The dies glow orange under the see-through lid; orange beads rise off the lid's top.",
        )
        .detail(
            "Cooling is the next step, on the BOARD page.",
            &["HEAT: ~1,000 W", "TIM + lid"],
        ),
];
