// BANDWIDTH page in the picture-and-panel template: the overview with zoom-ins a-e, and sections
// 1-10 (section 10 is the sources page). Blender scenes live in tools/pbr3d/blender/bandwidth_*.py.

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "BANDWIDTH",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
