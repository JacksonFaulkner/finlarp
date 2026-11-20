// PACKAGE: the page's overview, a Blender scene (tools/pbr3d/blender/package_overview.py, GLB
// tools/pbr3d/assets/package_overview.glb). One package taken apart beat by beat: die attach
// (wire bond and flip chip), mould and underfill, the substrate on the board, an HBM stack, a GPU
// die and HBM on one silicon interposer, and the lid closing the stack.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/package_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The seven beats of the overview, one per step (match package_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a package", BEAT_MS)
        .note(
            "A finished die does nothing until it is packaged. The package glues it to a substrate, connects it with wires or bumps, seals it, and carries power and signals to the board. For an AI GPU the package also holds memory stacks beside the logic die, so logic and memory share one piece of wiring.",
            "The whole stack cut open, low to high: the green board with its ball grid, the brown substrate, the silicon interposer, the purple GPU die, and grey HBM stacks on either side. The lid is off, so the die and memory are in view.",
        )
        .detail(
            "Logic and memory are joined in one package.",
            &["Only dies that passed WAFER SORT and DICE reach packaging", "AI GPUs: logic die plus HBM stacks on one interposer"],
        ),
    Beat::new("die attach: wire bond or flip chip", BEAT_MS)
        .note(
            "A die is attached in one of two ways. Wire bonding glues it face-up and runs fine wires from its pads to the substrate; it is the older method and still makes roughly 75 to 80 percent of IC interconnections. Flip chip turns the die face-down onto solder bumps, so every connection forms at once.",
            "Left: a copper leadframe pad with a die glued face-up and four gold wires arching from its pads down to the pad. Right: a die flipped face-down over a substrate piece, with a grid of solder bumps between them.",
        )
        .detail(
            "Wire bonding is common; flip chip packs in more connections.",
            &["Wire bonding: roughly 75-80% of IC interconnections (PCBSync)", "Flip chip: all I/O connect at once"],
        ),
    Beat::new("mould and underfill: sealing the die", BEAT_MS)
        .note(
            "Flip chip needs underfill, an epoxy that flows under the die around its bumps, so the joints survive heat cycles and drops. Wire-bonded dies are moulded: epoxy compound is pressed around the die and its wires, at about 175 C and 5 to 10 MPa, to protect them mechanically.",
            "The wire-bond die sits under a clear grey mould block that hides its wires. On the flip-chip side the gap fills with dark underfill, which covers the bumps.",
        )
        .detail(
            "Underfill and mould protect the joints and wires.",
            &["Underfill: needed for thermal cycling and drop shock", "Transfer mould: about 175 C, 5-10 MPa (PCBSync)"],
        ),
    Beat::new("substrate: the board under the chip", BEAT_MS)
        .note(
            "The chip sits on an organic substrate, a multi-layer board built up in thin dielectric films. It routes signals and power between the chip and the system board. C4 bumps join the substrate to the chip side, and BGA balls under it solder the whole package to the board. Big substrates are hard to keep flat, and layers built up unevenly on one side warp them.",
            "The board at the bottom with its grid of BGA balls, the substrate block above it, and rows of C4 bumps on its top face. The rest of the package is hidden so the substrate is alone in view.",
        )
        .detail(
            "A large substrate is a flatness problem.",
            &["Conventional substrates: more than 10 ABF layers per side (iConnect007)", "Uneven build-up on one side causes warpage"],
        ),
    Beat::new("HBM: DRAM dies stacked on TSVs", BEAT_MS)
        .note(
            "An HBM stack is thinned DRAM dies stacked on a base logic die. Copper through-silicon vias run up through the dies, and microbumps join each layer. SK hynix says its 12-high stack is in production and 16-high is in qualification. As stacks approach 20 dies, heat becomes the binding limit on height.",
            "One HBM stack, its near corner cut away to show orange DRAM layers over a blue base die, with gold TSV columns through the middle. A cyan data bead climbs one of the TSVs.",
        )
        .detail(
            "Memory stacks are built one thin die at a time.",
            &["SK hynix: 12-high in production, 16-high in qualification", "HBM4 part: over 20,000 TSVs and 16,148 base microbumps"],
        ),
    Beat::new("CoWoS: GPU and HBM on one interposer", BEAT_MS)
        .note(
            "CoWoS, TSMC's 2.5D packaging, sets the GPU die and the HBM stacks side by side on a silicon interposer: a slab of fine wires and TSVs that carries signals between them. Standard PCB routing cannot carry memory bandwidth this high, so the memory bus runs through silicon instead.",
            "Looking down on the interposer: the purple GPU die in the middle, grey HBM stacks on either side, and cyan data beads running under the die from stack to stack.",
        )
        .detail(
            "The interposer is the wiring between logic and memory.",
            &["CoWoS-S interposer: up to about 3.3 reticles, ~2,700 mm2 (TSMC)", "Reticle limit: about 858 mm2 (NextPCB)"],
        ),
    Beat::new("the lid closes: the package is sealed", BEAT_MS)
        .note(
            "The lid and cold plate come down on the stack to seal it. Packaging is a chokepoint: each die and HBM stack placed on the costly interposer can ruin the package if it is bad, and the interposer is made on a wafer whose size limits the package. Counterpoint Research called CoWoS the main bottleneck for AI shipments in an older report.",
            "The grey lid and the copper cold plate lower in from above and seal the stack. The labels name the closed package.",
        )
        .detail(
            "Packaging limits how many AI chips can ship.",
            &["Stacked-die testing keeps bad memory off the interposer (ServeTheHome)", "CoWoS as the main AI bottleneck (Counterpoint, older)"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "PACKAGE overview");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "PACKAGE overview");
    }
}
