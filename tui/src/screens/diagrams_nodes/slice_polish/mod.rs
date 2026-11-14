// SLICE + POLISH page in the picture-and-panel template (blender::Page): the overview, zoom-ins a-d
// and sections 1-10 (the last is the sources page), all Blender scenes from
// tools/pbr3d/blender/slice_*.py, built on slice_kit.py.

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "SLICE + POLISH",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
