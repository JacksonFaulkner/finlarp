// DEVELOP: the lone overview scene (overview.rs). No zoom-ins or numbered sections for this page.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "DEVELOP",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
