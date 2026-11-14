// CELL page in the picture-and-panel template: the overview, zoom-ins a-e and sections 1-10, all
// Blender scenes (tools/pbr3d/blender/cell_*.py, built on cell_kit.py).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "CELL",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
