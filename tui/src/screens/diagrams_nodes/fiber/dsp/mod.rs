// FIBER tab, PAM4 DSP: the flip-chip DSP package on the board. Lead-owned wiring: the scene files are overview.rs (the page's overview),
// zooms.rs (the lettered zoom-ins a-e) and sections.rs (the numbered sections 1-9).

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "PAM4 DSP",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
