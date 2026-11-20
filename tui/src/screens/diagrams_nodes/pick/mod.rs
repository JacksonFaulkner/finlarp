// PICK page in the BACK END tab: the overview is a Blender scene (tools/pbr3d/blender/pick_overview.py,
// GLB tools/pbr3d/assets/pick_overview.glb). No lettered zoom-ins or numbered sections for this page.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "PICK",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
