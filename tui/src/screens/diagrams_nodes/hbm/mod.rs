// HBM STACK page in the picture-and-panel template: the overview, zoom-ins a-e and sections 1-10,
// all Blender scenes (tools/pbr3d/blender/hbm_*.py, built on hbm_kit.py).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "HBM STACK",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
