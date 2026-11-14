// LITHO page in the picture-and-panel template: the overview, zoom-ins a-f and sections 1-10, all
// Blender scenes (tools/pbr3d/blender/litho_*.py, built on litho_kit.py).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "LITHO",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
