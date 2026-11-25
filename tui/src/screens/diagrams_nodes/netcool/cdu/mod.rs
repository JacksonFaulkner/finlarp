// NETWORK+COOL tab, CDU: the page's overview, lettered zoom-ins a-e and numbered sections 1-9. overview.rs (the
// Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from tools/pbr3d/blender/net_cdu_*.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "CDU",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
