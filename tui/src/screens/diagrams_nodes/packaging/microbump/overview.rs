// PACKAGING tab, MICROBUMP: the page's overview, a Blender scene (tools/pbr3d/blender/pkg_microbump_overview.py,
// GLB tools/pbr3d/assets/pkg_microbump_overview.glb). Seven beats: the package cut open, its three levels of joints,
// inside one microbump, signals and power through the joints, underfill, heat and stress, and hybrid bonds.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_microbump_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the package cut open", BEAT_MS)
        .note(
            "A 2.5D package sliced through its middle: a logic die and an HBM stack sit on a silicon interposer, which sits on an organic substrate, which sits on the board. Every level is joined to the next by an array of bumps.",
            "A layered cut-away: a purple logic die and a blue HBM stack on top, a grey interposer under them, a green-and-tan substrate below that, and a green board at the bottom, with rows of balls between each level.",
        )
        .detail(
            "Three sizes of joint carry every signal and amp.",
            &["3 levels of joints", "Logic die + HBM on an interposer"],
        ),
    Beat::new("three levels of joints", BEAT_MS)
        .note(
            "Pulled apart, each level shows its own bumps. Microbumps join the dies to the interposer, C4 bumps join the interposer to the substrate, and BGA balls join the substrate to the board. Each step down is coarser.",
            "The levels lift apart: a dense comb of tiny pillars under the dies, a row of mid-size balls under the interposer, and big balls on the board.",
        )
        .detail(
            "Pitch grows about 4x and then about 7x at each step down.",
            &["MICROBUMP ~40 um", "C4 BUMP ~150 um", "BGA ~1 mm"],
        ),
    Beat::new("inside one microbump", BEAT_MS)
        .note(
            "Cut open, each microbump is a copper pillar plated on the die, a nickel barrier, and a tin-silver solder cap that has melted onto a copper pad on the interposer. Under the pads, the RDL wiring and TSVs carry the connections down.",
            "A close row of cut pillars: brown copper posts with grey solder at their feet, standing on copper pads over the interposer's striped wiring layer, with copper TSVs running down through the silicon.",
        )
        .detail(
            "The pillar keeps its shape when the solder melts.",
            &["CU PILLAR ~25 um wide", "SnAg cap, Ni barrier"],
        ),
    Beat::new("signals and power through the joints", BEAT_MS)
        .note(
            "Power climbs from the board through a BGA ball, the substrate's vias and plated through-holes, a C4 bump, a TSV and a microbump into the die. A signal leaves the logic die, runs sideways through the interposer's RDL and climbs into the HBM.",
            "Amber beads climb straight up through every level into the purple die; cyan beads drop out of the die edge, run along a gold wire in the interposer and rise into the HBM stack.",
        )
        .detail(
            "Every amp and every bit passes through the bumps.",
            &["TSV: through the interposer", "RDL: die to HBM"],
        ),
    Beat::new("underfill", BEAT_MS)
        .note(
            "Epoxy underfill is wicked into the gap under the dies and the gap under the interposer, then cured. It locks the joints into a solid layer so they share the load.",
            "Warm beads run along the gaps, and dark fill appears around the pillars under the dies and around the balls under the interposer.",
        )
        .detail(
            "Without it, the outer joints carry most of the strain.",
            &["UNDERFILL", ">10x C4 thermal-cycle life"],
        ),
    Beat::new("heat and stress", BEAT_MS)
        .note(
            "As the die heats, silicon expands about 3 ppm per degree while the organic substrate expands several times more. The mismatch pulls hardest on the joints at the corners, where cracks start.",
            "Heat rises off the purple die; the outermost microbumps and the end C4 balls glow red.",
        )
        .detail(
            "Corner joints fail first under thermal cycling.",
            &["CTE mismatch", "WARPAGE"],
        ),
    Beat::new("hybrid bonds: no bumps at all", BEAT_MS)
        .note(
            "Below about 10 um pitch, solder bumps give way to hybrid bonds: polished copper pads set in oxide, pressed together so the oxide bonds and then the copper fuses. The gap and the solder disappear.",
            "The pillars vanish and the die drops flat onto a thin pale layer striped with copper pads, right on top of the interposer's wiring.",
        )
        .detail(
            "Pitch can fall to a few um; TSMC calls it SoIC.",
            &["HYBRID BOND <=10 um", "SoIC"],
        ),
];
