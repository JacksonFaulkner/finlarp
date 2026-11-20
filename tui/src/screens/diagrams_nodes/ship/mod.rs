// SHIP tab, SHIP: the page's overview, a Blender scene (overview.rs; GLB tools/pbr3d/assets/ship_overview.glb).
// The overview only: the lettered zoom-ins and numbered sections are not written for this page.

mod overview;

use super::Node;

pub const NODE: Node = Node {
    page: "SHIP",
    overview: Some(overview::build),
    sections: &[],
    clips: false,
};
