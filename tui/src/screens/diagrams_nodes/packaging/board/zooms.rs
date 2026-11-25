// PACKAGING tab, BOARD: lettered zoom-ins a-e, each its own scene with its own camera and beads
// (tools/pbr3d/blender/pkg_board_zooms.py, GLBs tools/pbr3d/assets/pkg_board_zoom_<letter>.glb).

use super::super::super::blender::{page, Cell};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("ball field from the side", BEAT_MS)
        .note(
            "At the cut face a row of balls sits on board pads below and substrate pads above, about a millimetre apart. Current climbs every power ball at once.",
            "A low close view: silver half balls in a row between the substrate and the striped board, red beads rising through several of them.",
        )
        .detail(
            "The ball field is the package's whole interface.",
            &["BGA BALLS: ~1 mm pitch", "Pads on both sides"],
        ),
    Beat::new("one joint cut open", BEAT_MS)
        .note(
            "One ball drawn four times larger: a copper pad with a gold finish on the board, the solder ball, the substrate pad, and a plated via dropping to the power plane.",
            "A big silver half ball between two gold pads; below it a copper via with a dark fill runs down through tan dielectric and copper planes.",
        )
        .detail(
            "A joint is pad, solder, pad, via.",
            &["Pad + ball + pad", "Plated via to the plane"],
        ),
    Beat::new("power and signal ride it", BEAT_MS)
        .note(
            "Power uses many balls in parallel so each carries only part of the current. A signal gets a ball of its own and runs off along a trace.",
            "Red beads climb the via and ball from the plane; cyan beads run along a trace at the top of the board and turn up through the joint.",
        )
        .detail(
            "Power shares; signals own.",
            &["Power: many balls in parallel", "Signal: one ball each"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("phases and the plane", BEAT_MS)
        .note(
            "Each phase has a power stage that switches 12 V, an inductor that smooths it and output caps beside the package. Its current drops into a thick copper plane in the board.",
            "A view across the left side: dark power stages, tall grey inductors, small tan caps, and red beads running down into the copper plane inside the cut board.",
        )
        .detail(
            "The regulator sits as close as the board allows.",
            &["VRM: stage + inductor + caps", "Thick copper power plane"],
        ),
    Beat::new("up through the package", BEAT_MS)
        .note(
            "The current climbs a via and a ball, a plated through-hole in the substrate core, stacked microvias, C4 bumps and TSVs into the die.",
            "The substrate and interposer see-through; red beads climb in columns from the board to the purple dies.",
        )
        .detail(
            "Six levels between plane and transistor.",
            &["BGA > PTH > microvias > C4 > TSV", "~1,000 A total"],
        ),
    Beat::new("voltage lost at every level", BEAT_MS)
        .note(
            "Each level has a little resistance, and at a thousand amps a little resistance costs real voltage: I x R at the plane, the ball, the bumps. What is left reaches the die at about 0.8 V.",
            "The 4x column close-up: red beads run along the plane, up the via, ball, through-hole and bumps into the die.",
        )
        .detail(
            "Small resistances, huge currents.",
            &["Loss = I x R per level", "~0.8 V at the die"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("heat off the die", BEAT_MS)
        .note(
            "The dies turn nearly all their power into heat. TIM1, a metal or gel layer, fills the gaps between die and lid.",
            "The dies glow amber; orange beads rise into a thin grey layer above them.",
        )
        .detail(
            "The first interface matters most.",
            &["Die: the heat source", "TIM1: metal or gel"],
        ),
    Beat::new("the lid and TIM2", BEAT_MS)
        .note(
            "The nickel-plated copper lid spreads the heat and protects the dies; its legs are glued to the substrate. TIM2 fills the gap to the cold plate.",
            "Orange beads climb through the silver lid and a pale pad; the lid's legs reach down to the substrate at both ends.",
        )
        .detail(
            "The lid spreads; TIM2 joins.",
            &["LID: nickel-plated copper", "TIM2: grease or pad"],
        ),
    Beat::new("coolant in the fins", BEAT_MS)
        .note(
            "Skived copper fins give the water a huge area to take heat from. Coolant runs between them toward the front and leaves warm.",
            "The plate's cover turns clear; blue beads flow between rows of thin copper fins while heat beads climb into the base.",
        )
        .detail(
            "Fin area sets how much heat the water takes.",
            &["COLD PLATE: skived fins", "LIQUID COOLING"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("die to the board", BEAT_MS)
        .note(
            "NVLink lanes leave the GPU die, drop through the microbumps, interposer, C4s and substrate, and leave through a ball into a trace in the board.",
            "Cyan beads leave the die, step down through the package layers and run right along a copper trace near the top of the board.",
        )
        .detail(
            "High-speed lanes cross the same layers as power.",
            &["NVLINK: SerDes lanes", "Through the package to the board"],
        ),
    Beat::new("the connector and twinax", BEAT_MS)
        .note(
            "The trace ends at a high-speed connector at the board's edge; gold contacts hand the signal to twinax cables.",
            "A black connector block with gold pins on its cut face; teal cables curve away to the right, cyan beads riding into them.",
        )
        .detail(
            "Cables beat board traces over distance.",
            &["High-speed connector", "Twinax copper cables"],
        ),
    Beat::new("tray to switch tray", BEAT_MS)
        .note(
            "On a compute tray four modules send their NVLink cables up to a switch tray. The switch connects every GPU to every other.",
            "A tray seen from the side: four modules, teal cables rising at the back to a grey switch tray above, cyan beads flowing up.",
        )
        .detail(
            "The switch makes many GPUs one.",
            &["NVLINK SWITCH", "Four GPUs per tray"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("a liquid-cooled rack", BEAT_MS)
        .note(
            "Compute trays fill the rack above and below a pair of switch trays. Every module has its own cold plate.",
            "A rack frame with green trays stacked, grey switch trays in the middle, red and blue pipes at the back.",
        )
        .detail(
            "Racks are built around the cooling loop.",
            &["RACK: trays + switches", "Cold plate on every module"],
        ),
    Beat::new("coolant through the manifolds", BEAT_MS)
        .note(
            "Cool water rises up one side manifold, branches into every tray and every plate, and returns warm down the other side.",
            "Seen from the back: blue beads climb the left pipe and run across each tray; orange beads fall down the right pipe.",
        )
        .detail(
            "One loop feeds every plate.",
            &["Supply and return manifolds", "To a CDU"],
        ),
    Beat::new("bigger packages warp", BEAT_MS)
        .note(
            "As packages grow, heating and cooling bend substrate and board differently. The corner balls take the most strain.",
            "Back at the module's cut face, the outermost balls at each end glow red.",
        )
        .detail(
            "Size makes warpage the assembly problem.",
            &["Warpage grows with size", "Corner joints strain most"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "BGA to the board",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "power climbs the levels",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "cooling: cold plate and liquid",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "modules and NVLink",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "size and cooling",
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
