// PACKAGING tab, SUBSTRATE: lettered zoom-ins a-e, each its own Blender scene on the overview's cut-open substrate
// (tools/pbr3d/blender/pkg_substrate_zooms.py, GLBs in tools/pbr3d/assets/pkg_substrate_zoom_<letter>.glb):
// a building the layers, b fan-out, c warpage, d ABF film and its makers, e power fans in.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the core", BEAT_MS)
        .note(
            "A substrate starts as a core: glass cloth soaked in epoxy, clad in copper foil. Holes are drilled through it, plated with copper and plugged with resin.",
            "The bare brown core alone above the board, glass-cloth bundles in its cut face and copper-lined holes cut in half, dark resin inside them.",
        )
        .detail("The core gives the stack its stiffness.", &["CORE", "Plated through-holes"]),
    Beat::new("layers laminated on", BEAT_MS)
        .note(
            "ABF film is laminated onto both faces, then copper is plated and patterned on it. Each new layer drops on top of the last, on both sides at once.",
            "Cream film layers and copper layers drop one by one onto the top and bottom of the core until six sit on each side.",
        )
        .detail("Build-up means one layer at a time.", &["ABF FILM", "BUILD-UP LAYERS"]),
    Beat::new("vias, resist, bumps", BEAT_MS)
        .note(
            "Lasers drill microvias through each film so copper can join the layers, stacked one on another. Green solder resist covers the outside, and the pads get their bumps last.",
            "Tapered copper vias appear stacked through the layers, a green resist skin covers top and bottom, then bumps, balls and the package on top arrive.",
        )
        .detail("Then it is ready for the chip.", &["Laser microvias", "Solder resist + pads"]),
];

const B_B: &[Beat] = &[
    Beat::new("the bump field", BEAT_MS)
        .note(
            "On top, bumps stand about 150 um apart, tens of thousands of them under a big GPU package. Every one needs its own path down.",
            "Looking down on the top surface: a dense grid of silver bumps in green resist under the edge of the interposer.",
        )
        .detail("Fine pitch is set by the silicon.", &["C4 pitch ~150 um"]),
    Beat::new("across a layer", BEAT_MS)
        .note(
            "A signal drops from its bump down stacked microvias to a signal layer and runs out sideways. Bumps nearer the middle use deeper layers, so traces never cross another route's via.",
            "The cut face from the right: cyan beads drop down copper via stacks, then race along glowing cyan traces on four different layers.",
        )
        .detail("Each layer carries a ring of bumps outward.", &["FAN-OUT", "Layer per ring"]),
    Beat::new("down to the balls", BEAT_MS)
        .note(
            "At the end of its trace the signal drops through a plated hole in the core and down the bottom layers to a ball. The balls sit about 1 mm apart, several times the bump pitch.",
            "A low view of the right edge: cyan beads come down copper barrels through the core and into big silver balls spread wide on the board.",
        )
        .detail("Coarse pitch the board can use.", &["BGA pitch ~1 mm", "~7x the bump pitch"]),
];

const C_B: &[Beat] = &[
    Beat::new("flat when cool", BEAT_MS)
        .note(
            "At room temperature the laminate is flat. Inside it, copper, resin and glass cloth all expand by different amounts when heated.",
            "A side view of the substrate alone as a straight layered slab with bumps on top and balls under it on the board.",
        )
        .detail("Mixed materials, mixed expansion.", &["WARPAGE starts here"]),
    Beat::new("bowing in reflow", BEAT_MS)
        .note(
            "In the reflow oven, near 250 C, the slab bows: here its middle rises and its ends drop. The balls under its ends are pushed and pulled while the solder is molten.",
            "Heat rises from the slab as it bends into an arch, middle up and ends down, over the flat board.",
        )
        .detail("The bow changes with temperature.", &["Reflow ~250 C", "WARPAGE"]),
    Beat::new("bowing back, strained joints", BEAT_MS)
        .note(
            "As it cools it bows the other way. The balls at the far ends take the most strain and can crack or lift off their pads.",
            "Close on the right end: the slab curves up at its end and the last ball glows red where it is pulled.",
        )
        .detail("Corner joints fail first.", &["Corner joint strain"]),
];

const D_B: &[Beat] = &[
    Beat::new("a roll of ABF", BEAT_MS)
        .note(
            "ABF is a thin epoxy film filled with silica, with no glass cloth. It comes on rolls on a clear PET carrier with a cover film over it, and is pressed onto the substrate in a vacuum laminator.",
            "A cream roll of film on a spool, its end unrolled flat toward the camera, showing three layers: clear carrier, cream film, clear cover.",
        )
        .detail("The insulator between copper layers.", &["ABF FILM", "Ajinomoto Build-up Film"]),
    Beat::new("in every layer", BEAT_MS)
        .note(
            "Every build-up layer starts as a sheet of ABF. Its smooth surface lets very fine copper lines be plated onto it, which a glass-cloth prepreg cannot match.",
            "The top build-up up close: cream film between each copper layer, tapered vias through each film.",
        )
        .detail("Fine lines need a smooth film.", &["~95% of GPU-grade film (est.)"]),
    Beat::new("who makes substrates", BEAT_MS)
        .note(
            "One estimate puts high-end FC-BGA share at Ibiden about 35%, Shinko 18%, Unimicron 14%, AT&S 10% and Nan Ya 5%. Estimates differ by source and by what they measure.",
            "Five bars on a dark base: a tall orange one for Ibiden and shorter blue ones for Shinko, Unimicron, AT&S and Nan Ya.",
        )
        .detail("A handful of makers.", &["SUBSTRATE MAKERS", "Shares are estimates"]),
];

const E_B: &[Beat] = &[
    Beat::new("up from the board", BEAT_MS)
        .note(
            "Core power at under 1 V comes up from the board through hundreds of BGA balls. It runs along a bottom plane and up the plated holes through the core.",
            "A low view at the middle: yellow beads rise from the balls, along a bottom copper layer and up copper barrels through the core.",
        )
        .detail("Many balls share the current.", &["Power balls", "PTH"]),
    Beat::new("across the planes", BEAT_MS)
        .note(
            "Solid ground and power planes spread the current sideways with little resistance. Small antipads cut in the planes let signal vias pass through without touching them.",
            "Two copper planes glow amber across the whole cut face; yellow beads run along them toward the middle.",
        )
        .detail("Planes are wide copper sheets.", &["Power planes", "Antipads"]),
    Beat::new("into the die", BEAT_MS)
        .note(
            "The current climbs the via stacks into the bumps and the die, over a thousand amps on a big GPU package. Capacitors on the underside supply sudden surges faster than the board can.",
            "Yellow beads climb into the bumps under the purple die; heat rises from the die; small capacitors sit under the substrate.",
        )
        .detail("The last stop before silicon.", &["1,000+ A on GPU packages", "Land-side capacitors"]),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "building the layers",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "fan-out: C4 to BGA",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "warpage",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "ABF film and substrate makers",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "power fans in",
        build: zoom_e,
    },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            super::super::super::super::blender::explained(s.as_ref(), z.label);
            super::super::super::super::blender::draws_every_beat(s.as_ref(), z.label);
        }
    }
}
