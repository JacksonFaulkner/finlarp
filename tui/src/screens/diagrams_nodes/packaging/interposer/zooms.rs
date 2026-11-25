// PACKAGING tab, INTERPOSER: lettered zoom-ins a-e, each its own Blender scene with its own camera and beads
// (tools/pbr3d/blender/pkg_interposer_zooms.py, GLBs tools/pbr3d/assets/pkg_interposer_zoom_<letter>.glb):
// a CoWoS-S and -L, b a signal from HBM to GPU, c growing past the reticle, d TSVs and power, e interposers per wafer.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("CoWoS-S: one silicon slab", BEAT_MS)
        .note(
            "CoWoS-S puts the GPU die and its HBM on one piece of silicon. The slab reaches past the die and the stacks on every side and sits on the substrate on C4 bumps.",
            "The whole cut-away from above and to the side: a wide grey silicon slab under the purple die and two orange stacks, silver balls under it, the brown substrate and green board below.",
        )
        .detail("One slab, up to about 3.3 reticles.", &["COWOS-S", "~2,700 mm2 max"]),
    Beat::new("its wiring up close", BEAT_MS)
        .note(
            "The top of the slab is the wiring: four levels of copper lines in oxide, made with chip-fab tools on an old node. Below them, the silicon body is crossed by copper TSVs.",
            "Close on the slab's cut face: a pale band of oxide with rows of short copper dashes on four levels, and the grey silicon underneath with copper columns running down to the balls.",
        )
        .detail("Fab-made wiring is what makes silicon fine.", &["BEOL: M1-M4", "TSVs below"]),
    Beat::new("CoWoS-L: bridges in an organic slab", BEAT_MS)
        .note(
            "CoWoS-L replaces the silicon slab with an organic one and buries small silicon bridge chips only where two dies, or a die and a stack, meet. Data crosses through the bridge.",
            "The interposer turns dark with a tan wiring layer; cyan bridge chips sit under the seams between two purple dies and the stacks, and cyan beads cross through them.",
        )
        .detail("NVIDIA's Blackwell uses CoWoS-L.", &["COWOS-L", "LSI BRIDGE"]),
];

const B_B: &[Beat] = &[
    Beat::new("out of the HBM base die", BEAT_MS)
        .note(
            "A bit leaves the stack from its base logic die, the blue layer at the bottom, through a copper microbump into the interposer's top wiring layer.",
            "Close on the right stack's foot: cyan beads leave the blue base die, drop through the short copper pillars and into the pale wiring band below.",
        )
        .detail("Microbumps sit on a pitch of tens of microns.", &["HBM base die", "Microbumps"]),
    Beat::new("across the fine wiring", BEAT_MS)
        .note(
            "It then runs sideways along a copper line a few millimetres long, inside the interposer, toward the GPU's edge. The camera follows the beads left.",
            "The camera slides left along the pale band; cyan beads ride the copper lines between the stack and the die.",
        )
        .detail("Short lines keep power per bit low.", &["A few mm of copper", "WIRING DENSITY"]),
    Beat::new("up into the GPU, in parallel", BEAT_MS)
        .note(
            "At the die edge the bit climbs back up a microbump into the GPU. Each HBM3 stack runs 1,024 such data lines and HBM4 runs 2,048, all in parallel.",
            "The camera pulls back over both stacks and the die; streams of cyan beads cross from each stack into the purple die at once.",
        )
        .detail("Wide and slow, not narrow and fast.", &["1,024 bits per HBM3 stack", "2,048 in HBM4"]),
];

const C_B: &[Beat] = &[
    Beat::new("one reticle and CoWoS-S", BEAT_MS)
        .note(
            "A scanner prints one reticle field at a time, about 26 x 33 mm or 858 mm2. A CoWoS-S interposer is stitched from several fields and reaches about 3.3 of them.",
            "Seen from above: a single die-sized purple rectangle next to a CoWoS-S package with one die and four stacks inside a 2x2 grid of glowing reticle outlines.",
        )
        .detail("Size is counted in reticles.", &["858 mm2 per reticle", "COWOS-S ~3.3x"]),
    Beat::new("9.5 reticles, 12 stacks", BEAT_MS)
        .note(
            "TSMC's roadmap has a 9.5-reticle interposer with 12 HBM stacks in 2027, built as CoWoS-L.",
            "A much bigger dark organic slab inside a 4x3 grid of reticle outlines, with two purple dies and two rows of six orange stacks.",
        )
        .detail("Tom's Hardware, TSMC roadmap.", &["9.5x (2027)", "12 HBM stacks"]),
    Beat::new("over 14 reticles by 2029", BEAT_MS)
        .note(
            "The 2029 plan goes past 14 reticles with room for up to 24 HBM5E stacks. Sixteen are drawn here, around four compute dies.",
            "A slab almost filling a 4x4 grid of reticle outlines: four purple dies across the middle and rows of orange stacks above and below.",
        )
        .detail("Packages are growing faster than dies.", &[">14x (2029)", "Up to 24 HBM5E"]),
];

const D_B: &[Beat] = &[
    Beat::new("one TSV cut open", BEAT_MS)
        .note(
            "A through-silicon via is a hole etched through the interposer and filled with copper. An oxide liner insulates it from the silicon and a thin barrier keeps the copper from diffusing into it.",
            "One TSV drawn large and cut in half: a copper core inside a thin dark barrier and a white liner, in grey silicon, with a copper pad above and a silver ball below.",
        )
        .detail("Liner, barrier, fill.", &["TSV", "Oxide liner + Ta/TaN barrier"]),
    Beat::new("power climbs through it", BEAT_MS)
        .note(
            "Current comes up from the substrate pad through the C4 ball, the backside pad and the copper column, and lands on the first wiring level on top.",
            "Yellow beads rise from the brown substrate through the silver ball and up the copper core into the copper line at the top.",
        )
        .detail("Each TSV carries a small share.", &["Backside pad", "Lands on M1"]),
    Beat::new("the TSV array to the C4s", BEAT_MS)
        .note(
            "Back on the package, a whole row of TSVs carries power and signals between the C4 bumps and the wiring on top. Many share the current, because a GPU draws over a thousand amps.",
            "The package cut-away: yellow beads climbing through the substrate, the silver C4 row and many copper columns into the purple die.",
        )
        .detail("Every amp passes through the array.", &["TSV array", "C4 ~150 um pitch"]),
];

const E_B: &[Beat] = &[
    Beat::new("CoWoS-S slabs on a wafer", BEAT_MS)
        .note(
            "Interposers are cut from 300 mm wafers. Only about eleven 3.3-reticle slabs fit whole on one wafer in this drawing; the rest of the round edge is wasted.",
            "A round grey wafer from above with a block of pale rectangles in its middle and empty edges around them.",
        )
        .detail("Big rectangles waste a round wafer.", &["300 mm wafer", "~11 at 3.3x"]),
    Beat::new("fewer as they grow", BEAT_MS)
        .note(
            "At 9.5 reticles only about five slabs fit. Every step up in size cuts the number of packages per wafer of CoWoS capacity.",
            "The same wafer, now holding only a few large pale squares in a cross shape.",
        )
        .detail("Packages per wafer fall fast.", &["~5 at 9.5x", "Per wafer"]),
    Beat::new("capacity caps AI output", BEAT_MS)
        .note(
            "Each slab becomes one package with its lid on, ready for a board. Because nearly every top accelerator needs CoWoS, its capacity, not wafers of logic, has capped how many ship.",
            "The lidded CoWoS-L package cut open on its board, die glowing and heat rising out of the lid.",
        )
        .detail("Cerebras' 2026 results call CoWoS supply-limited.", &["CoWoS capacity", "TSMC + OSATs"]),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "CoWoS-S and -L",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "a signal from HBM to GPU",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "growing past the reticle",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "TSVs and power",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "interposers per wafer",
        build: zoom_e,
    },
];
