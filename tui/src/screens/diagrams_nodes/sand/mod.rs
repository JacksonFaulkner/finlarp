// SAND page in the MELT + PULL template. The overview, the zoom-ins a-d and the ten section
// pictures (section 10 is the sources page) all share one layout: the Blender scene on the left
// with tags pinned to its parts, and the beat's text in a panel on the right (pbr3d::caption).

pub use super::blender::{Page, BEAT_MS};
use super::Node;

mod overview;
mod sections;
mod zoom;

pub const NODE: Node = Node {
    page: "SAND",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: true,
};

#[cfg(test)]
mod tests {
    pub use super::super::blender::{draws_every_beat, explained};
}
