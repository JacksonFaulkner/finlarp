// IMPLANT, the ion implanter that dopes the silicon. Lead-owned wiring: the scene file is
// overview.rs (the page's overview). The page has no zoom-ins or numbered sections.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "IMPLANT",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
