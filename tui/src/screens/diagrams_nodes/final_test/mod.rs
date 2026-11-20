// FINAL TEST, the back-end test page. Its overview is a Blender scene (overview.rs); the lettered
// zoom-ins and numbered sections are not written yet.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "FINAL TEST",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
