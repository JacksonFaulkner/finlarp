// ARRAY page in the MELT + PULL template (blender::Page): the overview, zoom-ins a-e and sections
// 1-10, all Blender scenes (tools/pbr3d/blender/array_*.py, built on array_kit.py).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "ARRAY",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
