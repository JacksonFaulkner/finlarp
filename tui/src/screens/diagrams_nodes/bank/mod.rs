// BANK page in the MELT + PULL template: the overview, zoom-ins a-e and sections 1-10, all Blender
// scenes (tools/pbr3d/blender/bank_*.py, built on bank_kit.py). Section 10 is the sources page.

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "BANK",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
