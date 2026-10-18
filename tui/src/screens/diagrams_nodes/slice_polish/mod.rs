// SLICE + POLISH page in the MELT + PULL template. An overview with zoom-ins a-d; no per-section close-ups yet.

use super::Node;

mod overview;
mod zoom;

pub const NODE: Node = Node {
    page: "SLICE + POLISH",
    overview: Some(overview::build),
    sections: &[],
};
