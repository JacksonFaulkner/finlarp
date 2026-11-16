// POWER tab, VRM: the page's overview, lettered zoom-ins a-e and numbered sections 1-9. Lead-owned wiring: overview.rs
// (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from tools/pbr3d/blender/power_vrm_*.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "VRM",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
