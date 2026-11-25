// NETWORK+COOL tab, LEAF: the page's overview, lettered zoom-ins a-e and numbered sections 1-9, drawn from
// tools/pbr3d/blender/net_leaf_*.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "LEAF",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
