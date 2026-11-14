// MELT + PULL page in the picture-and-panel template (blender::Page): the overview, zoom-ins a-c
// and sections 1-9, all Blender scenes (tools/pbr3d/blender/melt_*.py, built on melt_kit.py).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "MELT + PULL",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
