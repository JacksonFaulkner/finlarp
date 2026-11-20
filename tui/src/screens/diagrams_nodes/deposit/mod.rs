// DEPOSIT page in the MELT + PULL template. The overview is a Blender scene (overview.rs); the page
// has no numbered sections yet.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "DEPOSIT",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
