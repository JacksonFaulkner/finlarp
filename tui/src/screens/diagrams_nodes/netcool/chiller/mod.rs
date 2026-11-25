// NETWORK+COOL tab, CHILLER PLANT: the page's overview, lettered zoom-ins a-e and numbered sections 1-9. overview.rs
// (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from tools/pbr3d/blender/net_chiller_*.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "CHILLER PLANT",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
