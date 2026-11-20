// ETCH tab page: the overview is a Blender scene (tools/pbr3d/blender/etch_overview.py, its beats in
// overview.rs). The numbered sections are not written yet, so the page has no close-ups.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "ETCH",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
