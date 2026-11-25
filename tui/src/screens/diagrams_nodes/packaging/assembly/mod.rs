// PACKAGING tab, ASSEMBLY: the page's overview, lettered zoom-ins a-e and numbered sections 1-9, drawn from
// tools/pbr3d/blender/pkg_assembly_*.py (part kit pkg_assembly_detail.py): overview.rs (the Blender overview),
// zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9).

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "ASSEMBLY",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
