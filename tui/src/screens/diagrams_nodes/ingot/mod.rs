// INGOT page in the picture-and-panel template: an overview with zoom-ins a-d, and one picture per
// `# ` section of the page (sections 1-9 and the sources), all Blender scenes built by
// tools/pbr3d/blender/ingot_{overview,zooms,sections}.py on ingot_kit.py.

use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "INGOT",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
