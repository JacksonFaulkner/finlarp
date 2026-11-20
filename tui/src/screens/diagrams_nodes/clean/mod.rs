// CLEAN, the strip-and-rinse step. The overview is a Blender scene (overview.rs). Overview only for
// now: no zoom-ins or numbered sections yet.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "CLEAN",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
