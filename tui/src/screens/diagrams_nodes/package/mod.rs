// PACKAGE, the back end after PICK: the page's overview scene (bond, mould, substrate, HBM, CoWoS,
// lid). The scene lives in overview.rs; its Blender script is tools/pbr3d/blender/package_overview.py.
// The page has no lettered zoom-ins or numbered sections yet, so sections is empty.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "PACKAGE",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
