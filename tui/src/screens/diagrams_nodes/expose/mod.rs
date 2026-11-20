// EXPOSE page in the MELT + PULL template. The overview is the Blender scene in overview.rs (its
// GLB is built by tools/pbr3d/blender/expose_overview.py). No zoom-ins or numbered sections yet.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "EXPOSE",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
