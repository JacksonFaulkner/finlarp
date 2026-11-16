// PACKAGING tab, ASSEMBLY: the overview is the Blender scene tools/pbr3d/blender/assembly_overview.py,
// played through pbr3d in the picture-and-panel template: seven beats, the text from
// diagrams_pkg_nodes.rs. Zoom-ins a-e are one frozen state of that scene each, shown for their three
// beats (tools/pbr3d/blender/pkg_zooms.py). Sections 1-9 are the zoom pictures they point at
// (tools/pbr3d/sections.json).

use super::super::blender::{page, Cell, Page};
use super::super::Node;
use crate::screens::diagrams_pkg_nodes::{AA_B, AB_B, AC_B, AD_B, AE_B, A_B};
use crate::ui::anim::{Scene, Zoom};

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/assembly_overview.glb"),
        beats: A_B,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/assembly_zoom_a.glb"),
        AA_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/assembly_zoom_b.glb"),
        AB_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/assembly_zoom_c.glb"),
        AC_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/assembly_zoom_d.glb"),
        AD_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/assembly_zoom_e.glb"),
        AE_B,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "chip on the wafer",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "on substrate",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "yield stackup",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "capacity",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "the lid goes on",
        build: zoom_e,
    },
];

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [zoom_a, zoom_b, zoom_a, zoom_c, zoom_d, zoom_d, zoom_e, zoom_d, zoom_c];

pub const NODE: Node = Node {
    page: "ASSEMBLY",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

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
            super::super::super::blender::explained(s.as_ref(), z.label);
            super::super::super::blender::draws_every_beat(s.as_ref(), z.label);
        }
    }
}
