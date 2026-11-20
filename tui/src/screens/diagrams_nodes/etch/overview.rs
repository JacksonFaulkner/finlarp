// ETCH: the page's overview, a Blender scene (tools/pbr3d/blender/etch_overview.py, GLB
// tools/pbr3d/assets/etch_overview.glb). One plasma etch chamber cut open: gas in at the showerhead, an
// RF coil round the lid, the wafer on the chuck, and a slice of wafer with a trench that deepens to the
// etch stop while radicals and ions work on it.

use super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/etch_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match etch_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("carve film in a plasma chamber", BEAT_MS)
        .note(
            "Etch carves the pattern into the film. The wafer sits in a vacuum chamber, and gas that a radio-frequency field has turned into plasma attacks the film. Where the hard mask does not protect it, the film is removed, leaving the pattern cut into the wafer.",
            "A steel chamber cut open down the middle. Gas comes in at the showerhead on top, a copper RF coil wraps the lid, and the wafer sits on the chuck at the bottom under a dark hard mask. The turbo pump on the right pulls gas out. Purple plasma fills the chamber once it lights.",
        )
        .detail(
            "Remove film only where the mask does not protect it.",
            &[
                "Capacitive RIE runs at about 10-100 mTorr (MKS)",
                "Vertical walls: see beats 2 to 4",
            ],
        ),
    Beat::new("ignite: gas becomes plasma", BEAT_MS)
        .note(
            "A strong radio-frequency field strips electrons off the gas molecules. Those electrons break more molecules apart, and the mix of electrons, neutral radicals and charged ions is the plasma. In an inductive (ICP) etcher a coil sets the plasma density, and a separate bias on the wafer sets how hard the ions hit.",
            "The purple glow fills the chamber, lit from the copper coil round the lid. Gas jets fall from the showerhead into it, and the cut-open chuck and pump stay below.",
        )
        .detail(
            "The chemistry etches; the ions aim it.",
            &[
                "ICP: coil sets ion density, bias sets ion energy (US 7771562)",
                "ICP and bias run on separate RF supplies (MKS)",
            ],
        ),
    Beat::new("radicals and ions: two halves", BEAT_MS)
        .note(
            "Radicals are neutral fragments of the gas, such as fluorine from CF4. With no charge they drift in every direction and can etch sideways. Ions carry energy and are pulled across the sheath straight down onto the wafer, so they hit the floor head-on and break the film there.",
            "Pale green radical blobs drift across the top of the wafer from every side. White ion beads fall in straight lines onto the mask and into the trench opening.",
        )
        .detail(
            "Radicals spread out; ions go straight down.",
            &[
                "Ion-enhanced etch: directional ions, chemical selectivity (Berkeley EE247B)",
                "Radical-only etch is isotropic and undercuts the mask (textbook)",
            ],
        ),
    Beat::new("the trench deepens to the etch stop", BEAT_MS)
        .note(
            "Each ion that lands on the floor breaks the film there, so the trench goes down. The etch stop underneath barely reacts, so the trench ends there. The mask erodes too, but far more slowly than the film, and that selectivity sets how deep the trench can go.",
            "A dark trench grows down through the film in the middle of the wafer slice, from the mask opening to the pale etch-stop layer that halts it. The chamber's pump carries the byproducts away.",
        )
        .detail(
            "Selectivity sets how deep the trench can go.",
            &[
                "NAND channel holes: about 10 um deep through a ~100 nm opening (semiengineering)",
                "Aspect ratio approaching 70:1 today (semiengineering)",
            ],
        ),
    Beat::new("sidewall polymer keeps walls straight", BEAT_MS)
        .note(
            "Fluorocarbon gas leaves a thin polymer film on every surface. Ions knock it off the floor, where they land, while the walls see few ions, so the polymer stays and blocks sideways attack. Balance matters: too little polymer bows the walls, and too much closes the mouth of the trench.",
            "A violet film coats both trench walls, thickest near the mask. The floor is clear of it, and the walls stay vertical down to the etch stop.",
        )
        .detail(
            "The floor gets cleared; the walls keep the film.",
            &[
                "Too little passivation causes feature bowing (semiengineering)",
                "Too much polymer at the mouth stops ions reaching the bottom (semiengineering)",
            ],
        ),
    Beat::new("strip, clean, then the next layer", BEAT_MS)
        .note(
            "Once the trench reaches the etch stop, the plasma goes off. The mask and polymer are stripped, and residues that would corrode metal are cleaned away. The wafer then moves to the next step, and the next litho layer is printed and etched the same way.",
            "The plasma glow fades. The hard mask and the violet polymer are gone, leaving a clean trench in the wafer slice, and a label points to the next layer.",
        )
        .detail(
            "Strip and clean remove the helpers.",
            &[
                "Atomic layer etch: two self-limiting half-steps (Wikipedia, atomic layer etching)",
                "About one atomic layer per second is the state of the art (Wikipedia)",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "ETCH overview");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "ETCH overview");
    }
}
