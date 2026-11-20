// PACKAGING tab, INTERPOSER: the overview is the Blender scene tools/pbr3d/blender/interposer_overview.py,
// played through pbr3d in the picture-and-panel template: seven beats, the text from
// diagrams_pkg_nodes.rs. Zoom-ins a-e are one frozen state of that scene each, shown for their three
// beats (tools/pbr3d/blender/pkg_zooms.py). Sections 1-9 are the zoom pictures they point at
// (tools/pbr3d/sections.json).

use super::super::Node;
use super::super::blender::{Cell, Page, page};
use crate::screens::diagrams_pkg_nodes::{I_B, IA_B, IB_B, IC_B, ID_B, IE_B};
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
        glb: include_bytes!("../../../../../tools/pbr3d/assets/interposer_overview.glb"),
        beats: I_B,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/interposer_zoom_a.glb"),
        IA_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/interposer_zoom_b.glb"),
        IB_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/interposer_zoom_c.glb"),
        IC_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/interposer_zoom_d.glb"),
        ID_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/interposer_zoom_e.glb"),
        IE_B,
    )
}

const ZOOMS: &[Zoom] = &[
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

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    zoom_a, zoom_a, zoom_b, zoom_a, zoom_a, zoom_c, zoom_b, zoom_e, zoom_e,
];

pub const NODE: Node = Node {
    page: "INTERPOSER",
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
