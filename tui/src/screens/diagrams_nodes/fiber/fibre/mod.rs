// FIBER tab, OPTICAL FIBER: glass core and cladding with ferrules. Lead-owned wiring: the scene files are overview.rs (the page's overview),
// zooms.rs (the lettered zoom-ins a-e) and sections.rs (the numbered sections 1-9).

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "OPTICAL FIBER",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
