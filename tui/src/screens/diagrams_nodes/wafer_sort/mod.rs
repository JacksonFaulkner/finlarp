// WAFER SORT, in the BACK END row: electrical test of every die on the wafer before dicing. The page is
// the overview scene only (overview.rs, a Blender scene); the numbered sections are not written yet.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "WAFER SORT",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
