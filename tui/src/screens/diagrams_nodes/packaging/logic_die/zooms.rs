// PACKAGING tab, LOGIC DIE: lettered zoom-ins a-e, each its own Blender scene with its own camera and motion
// (tools/pbr3d/blender/pkg_logic_die_zooms.py, GLBs tools/pbr3d/assets/pkg_logic_die_zoom_<letter>.glb):
// a the reticle limit, b yield and known-good dies, c chiplets and the bridge, d HBM shoreline, e power and heat.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

macro_rules! zoom {
    ($f:ident, $cell:ident, $file:literal, $beats:ident) => {
        static $cell: Cell = std::sync::OnceLock::new();
        fn $f() -> Box<dyn Scene> {
            page(&$cell, include_bytes!(concat!("../../../../../../tools/pbr3d/assets/", $file)), $beats)
        }
    };
}

zoom!(zoom_a, ZA, "pkg_logic_die_zoom_a.glb", A_B);
zoom!(zoom_b, ZB, "pkg_logic_die_zoom_b.glb", B_B);
zoom!(zoom_c, ZC, "pkg_logic_die_zoom_c.glb", C_B);
zoom!(zoom_d, ZD, "pkg_logic_die_zoom_d.glb", D_B);
zoom!(zoom_e, ZE, "pkg_logic_die_zoom_e.glb", E_B);

pub const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "the reticle limit", build: zoom_a },
    Zoom { key: 'b', label: "yield and known-good dies", build: zoom_b },
    Zoom { key: 'c', label: "chiplets and the bridge", build: zoom_c },
    Zoom { key: 'd', label: "HBM shoreline", build: zoom_d },
    Zoom { key: 'e', label: "power and heat", build: zoom_e },
];

const A_B: &[Beat] = &[
    Beat::new("a wafer of fields", BEAT_MS)
        .note(
            "A 300 mm wafer is printed one reticle field at a time, stepping across the disc. Only whole fields that fit inside the edge become dies.",
            "A dark round wafer seen from above, tiled with purple rectangles, one of them outlined in pink.",
        )
        .detail("The field is the unit the scanner prints.", &["300 mm wafer", "One field per exposure"]),
    Beat::new("the slit sweeps the field", BEAT_MS)
        .note(
            "The scanner lights a slit 26 mm wide and sweeps it 33 mm along the field. Those two numbers set the largest die anyone can print: 858 mm2.",
            "Close on the pink-outlined field: a glowing violet band the field's width slides from one end of it to the other.",
        )
        .detail("26 mm slit x 33 mm scan.", &["RETICLE LIMIT: 26 x 33 mm", "858 mm2"]),
    Beat::new("High-NA halves it", BEAT_MS)
        .note(
            "High-NA EUV scanners print a field only 16.5 mm long, half the area. A die as large as H100's 814 mm2 would no longer fit in one exposure, so big designs must split or be stitched.",
            "Looking straight down at the field: a yellow outline covers only its near half.",
        )
        .detail("Single dies get smaller, not larger.", &["High-NA: 26 x 16.5 mm", "Half the area"]),
];

const B_B: &[Beat] = &[
    Beat::new("defects land", BEAT_MS)
        .note(
            "Defects land at random across the wafer, at about the same density everywhere. Each one is tiny, but it ruins whatever die it falls on.",
            "The wafer of purple fields from above, with small red dots appearing scattered across it.",
        )
        .detail("Defect density is set by the fab, not the design.", &["Random defects", "Same density everywhere"]),
    Beat::new("big dies lost", BEAT_MS)
        .note(
            "With one die per field, every defect scraps a whole reticle-sized die. The tag counts how many good dies remain on this wafer.",
            "The same wafer with every field that holds a red dot turned solid red; the rest stay purple.",
        )
        .detail("Big dies pay for every defect in full.", &["YIELD falls with die area", "~45% at ~800 mm2 (est.)"]),
    Beat::new("chiplets lose less", BEAT_MS)
        .note(
            "Cut each field into four smaller dies and the same defects now scrap only a quarter-field each, so a larger share of the silicon survives. Each small die is tested before packaging: a KNOWN GOOD DIE.",
            "The wafer now tiled with four times as many small purple dies; only the few under red dots turn red.",
        )
        .detail("Smaller dies plus testing raise package yield.", &["CHIPLETS", "KNOWN GOOD DIE"]),
];

const C_B: &[Beat] = &[
    Beat::new("two dies over a bridge", BEAT_MS)
        .note(
            "The facing edges of the two dies sit over a small slab of silicon sunk into the interposer: the bridge. It exists only to connect them.",
            "A cut block: two purple dies with pale wiring layers underneath, a gap between them, and a teal slab set into the grey interposer below the gap.",
        )
        .detail("A bridge is a tiny interposer just for the link.", &["Silicon bridge (CoWoS-L)", "Two dies"]),
    Beat::new("fine bumps, fine wires", BEAT_MS)
        .note(
            "Over the bridge the bumps are packed several times tighter than elsewhere, and the bridge carries layers of fine copper wires straight from one die's edge to the other's.",
            "Close on the cut face: a row of thin copper pillars over the bridge beside fatter ones further out, and copper lines stacked inside the teal slab.",
        )
        .detail("Bump pitch sets how many wires fit.", &["Fine-pitch bumps", "Bridge wiring layers"]),
    Beat::new("traffic both ways", BEAT_MS)
        .note(
            "Data crosses in both directions at once on thousands of parallel wires. On B200 the link runs about 10 TB/s, fast enough that the pair behaves as one GPU.",
            "Green beads drop from each die, run across the bridge wires and climb into the other die.",
        )
        .detail("The link must be wide and short.", &["DIE-TO-DIE ~10 TB/s", "One GPU to software"]),
];

const D_B: &[Beat] = &[
    Beat::new("the edge strip", BEAT_MS)
        .note(
            "Along the die's outer edge runs a strip of HBM interface circuits, the PHY. The HBM stacks sit right beside it on the interposer.",
            "Looking down at the left die's edge: a gold strip along the edge of the tiled purple die, with two gold HBM stacks just beyond.",
        )
        .detail("Memory interfaces live on the edge.", &["HBM PHY", "Stacks beside it"]),
    Beat::new("data to the stacks", BEAT_MS)
        .note(
            "Each HBM3 stack has a 1,024-bit bus. Its wires run down through microbumps, along the interposer's fine copper layers, and up into the stack's base die.",
            "Close on the cut face: cyan beads drop from the die edge, run along copper lines in the interposer and rise into a stack, then return.",
        )
        .detail("Thousands of short wires, not a few fast ones.", &["1,024 bits per stack", "~8 TB/s (B200)"]),
    Beat::new("the edge is a budget", BEAT_MS)
        .note(
            "Only the outer edge is free for memory; the inner edge faces the other die. Edge length caps how many stacks fit, one reason packages keep growing.",
            "Top view of both dies with their outer edges lit yellow and HBM stacks lined up beside them.",
        )
        .detail("More memory needs more shoreline.", &["HBM SHORELINE", "Edge length limits stacks"]),
];

const E_B: &[Beat] = &[
    Beat::new("from the board", BEAT_MS)
        .note(
            "The core supply, around 0.8 V, leaves the board's power planes and climbs through the BGA balls into the substrate.",
            "The cut face from the side: yellow beads rise in columns out of the green board and through the silver balls.",
        )
        .detail("Power enters from below.", &["Board planes", "BGA balls"]),
    Beat::new("through every layer", BEAT_MS)
        .note(
            "It crosses the substrate core in plated holes, a C4 bump, a copper TSV through the silicon interposer and a microbump, then spreads through the thick top metal levels to the transistors.",
            "Close on one column: a yellow bead passes a large solder bump, a thin copper rod through grey silicon, and a small pillar into the die.",
        )
        .detail("Each joint adds resistance at 1,000+ A.", &["C4 > TSV > microbump", "Thick global metal"]),
    Beat::new("heat out the top", BEAT_MS)
        .note(
            "Nearly all that power becomes heat in the die. It flows up through the thin TIM into the lid and on to a cold plate.",
            "The dies glow orange under a see-through lid; orange beads rise from its top.",
        )
        .detail("Heat leaves through the backside.", &["HEAT ~1,000 W", "TIM + lid"]),
];
