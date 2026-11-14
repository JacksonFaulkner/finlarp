// POLYSILICON page in the MELT + PULL template. An overview drawn in Blender through pbr3d, with
// zoom-ins a-d and ten section pictures (section 10 is the sources page).

use super::Node;

mod overview;
mod sections;

pub const NODE: Node = Node {
    page: "POLYSILICON",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
