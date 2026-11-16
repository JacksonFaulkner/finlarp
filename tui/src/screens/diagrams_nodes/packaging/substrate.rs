// PACKAGING tab, SUBSTRATE: the overview is the Blender scene tools/pbr3d/blender/substrate_overview.py,
// played through pbr3d in the picture-and-panel template: seven beats, the text from
// diagrams_pkg_nodes.rs. Zoom-ins a-e are one frozen state of that scene each, shown for their three
// beats (tools/pbr3d/blender/pkg_zooms.py). Sections 1-9 are the zoom pictures they point at
// (tools/pbr3d/sections.json).

use super::super::blender::{page, Cell, Page};
use super::super::Node;
use crate::screens::diagrams_pkg_nodes::{SA_B, SB_B, SC_B, SD_B, SE_B, S_B};
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
        glb: include_bytes!("../../../../../tools/pbr3d/assets/substrate_overview.glb"),
        beats: S_B,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/substrate_zoom_a.glb"),
        SA_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/substrate_zoom_b.glb"),
        SB_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/substrate_zoom_c.glb"),
        SC_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/substrate_zoom_d.glb"),
        SD_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/substrate_zoom_e.glb"),
        SE_B,
    )
}

const ZOOMS: &[Zoom] = &[
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

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [zoom_b, zoom_a, zoom_a, zoom_d, zoom_d, zoom_c, zoom_b, zoom_d, zoom_c];

pub const NODE: Node = Node {
    page: "SUBSTRATE",
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
