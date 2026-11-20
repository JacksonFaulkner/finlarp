// COAT page in the MELT + PULL template: the resist coat in the track. Lead-owned wiring: the scene file
// is overview.rs (the page's overview). No zoom-ins and no numbered sections for this page.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "COAT",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
