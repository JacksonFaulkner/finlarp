// R&D tab, 3D DRAM: the overview (tools/pbr3d/blender/rnd_3d_dram_overview.py on rnd_3d_dram_kit.py),
// zoom-ins a-e (zooms/) and numbered sections 1-9 (sections/). Section 10 (Sources) is text only.

mod overview;
mod sections;
mod zooms;

use super::Node;

pub const NODE: Node = Node {
    page: "3D DRAM",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};
