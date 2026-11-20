// DICE, the BACK END wafer step: the wafer is thinned, cut into die and the good die are picked.
// The page is the overview (its Blender scene in overview.rs); the lettered zoom-ins and the
// numbered sections are not built for this page.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "DICE",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
