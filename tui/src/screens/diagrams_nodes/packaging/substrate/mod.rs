// PACKAGING tab, SUBSTRATE: the page's overview, lettered zoom-ins a-e and numbered sections 1-9. overview.rs
// (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from
// tools/pbr3d/blender/pkg_substrate_*.py on the part kit pkg_substrate_detail.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "SUBSTRATE",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
