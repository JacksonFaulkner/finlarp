// PACKAGING tab, BOARD: the overview is the Blender scene tools/pbr3d/blender/board_overview.py,
// played through pbr3d in the picture-and-panel template: seven beats, the text from
// diagrams_pkg_nodes.rs. Zoom-ins a-e are one frozen state of that scene each, shown for their three
// beats (tools/pbr3d/blender/pkg_zooms.py). Sections 1-9 are the zoom pictures they point at
// (tools/pbr3d/sections.json).

use super::super::Node;
use super::super::blender::{Cell, Page, page};
use crate::screens::diagrams_pkg_nodes::{B_B, BA_B, BB_B, BC_B, BD_B, BE_B};
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
        glb: include_bytes!("../../../../../tools/pbr3d/assets/board_overview.glb"),
        beats: B_B,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/board_zoom_a.glb"),
        BA_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/board_zoom_b.glb"),
        BB_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/board_zoom_c.glb"),
        BC_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/board_zoom_d.glb"),
        BD_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/board_zoom_e.glb"),
        BE_B,
    )
}

const ZOOMS: &[Zoom] = &[
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

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    zoom_a, zoom_a, zoom_b, zoom_b, zoom_c, zoom_d, zoom_d, zoom_d, zoom_e,
];

pub const NODE: Node = Node {
    page: "BOARD",
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
