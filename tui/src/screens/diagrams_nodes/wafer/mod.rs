// WAFER page in the picture-and-panel template: an overview drawn in Blender through pbr3d
// (tools/pbr3d/blender/wafer_overview.py), zoom-ins a-d (wafer_zooms.py) and nine section pictures
// (wafer_sections.py; section 9 is the sources page).

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "WAFER",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
