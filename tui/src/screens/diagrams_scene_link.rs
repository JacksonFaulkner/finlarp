// Fiber tab: every page is a 3D optical-link scene from poly3d (`render_link`), on the
// Memory tab's template: an overview with its notes on the picture, five lettered
// zooms and nine numbered sections. A scene is data: its beats (the text) and one
// `LinkKey` per beat (camera, link state, labels, title). poly3d glides between
// keyframes, so every scene is continuous and loops without a cut.
//
// The pages' data lives in `diagrams_link_nodes.rs`, one file per node.

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::LinkKey;

pub use poly3d::{LinkPart as P, LinkState};

pub const MIN_W: u16 = 84;
pub const MIN_H: u16 = 26;
pub const BEAT_MS: u64 = 6500;
pub const OVERVIEW_MS: u64 = 13000;

/// The starting state every keyframe edits: a working single-mode link, module closed.
pub const BASE: LinkState = LinkState::BASE;

/// Camera targets, matching the stations in poly3d's link rig.
/// LINK: the whole link; TX: the sending module; RX: the receiving module.
pub const LINK: [f64; 3] = [1400.0, 60.0, 0.0];
pub const TX: [f64; 3] = [-60.0, 40.0, 0.0];
pub const RX: [f64; 3] = [2760.0, 40.0, 0.0];
pub const HOST: [f64; 3] = [-400.0, 40.0, 0.0];
pub const GLASS: [f64; 3] = [0.0, 300.0, poly3d::LINK_GLASS_Z];
pub const EML: [f64; 3] = [-1450.0, 80.0, poly3d::LINK_LASER_Z];
pub const SIPH: [f64; 3] = [0.0, 60.0, poly3d::LINK_LASER_Z];
pub const VCSEL: [f64; 3] = [1500.0, 200.0, poly3d::LINK_LASER_Z];
pub const PD: [f64; 3] = [200.0, 150.0, poly3d::LINK_PD_Z];
pub const CPO: [f64; 3] = [500.0, 40.0, poly3d::LINK_CPO_Z];

/// One lettered zoom: key, menu label, beats, keyframes.
pub type ZoomData = (char, &'static str, &'static [Beat], &'static [LinkKey]);
/// One numbered section: beats, keyframes.
pub type SecData = (&'static [Beat], &'static [LinkKey]);

/// A Fiber-tab scene: beats played over keyframes. The overview draws its beat notes
/// on the picture and offers the zooms.
pub struct LinkScene {
    pub beats: &'static [Beat],
    pub keys: &'static [LinkKey],
    pub zooms: &'static [Zoom],
    pub notes: bool,
}

/// A frame of `keys` at `t`, turned by `view`, with `beats`' notes on it when `notes`.
pub fn frame(beats: &[Beat], keys: &'static [LinkKey], notes: bool, t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &beats[t.beat.min(beats.len() - 1)];
    let n = poly3d::Notes { what: b.what, why: b.why, facts: b.facts };
    poly3d::render_link(keys, t.beat, t.local as f64, view, notes.then_some(&n), w as usize, h as usize, px::BG)
}

impl Scene for LinkScene {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }
    fn beats(&self) -> &[Beat] {
        self.beats
    }
    fn draw(&self, _c: &mut Canvas, _t: &Time) {}
    fn zooms(&self) -> &[Zoom] {
        self.zooms
    }
    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
        Some(frame(self.beats, self.keys, self.notes, t, &poly3d::View::default(), w, h))
    }
    fn notes_in_picture(&self) -> bool {
        self.notes
    }
    fn rest_point(&self) -> f32 {
        if self.notes { 0.4 } else { 0.0 }
    }
}

/// Everything one Fiber-tab page needs.
pub struct LinkNode {
    pub page: &'static str,
    pub beats: &'static [Beat],
    pub keys: &'static [LinkKey],
    pub zooms: &'static [Zoom],
    pub zoom_data: &'static [ZoomData],
    pub sections: &'static [fn() -> Box<dyn Scene>; 9],
    pub section_data: &'static [SecData; 9],
}

/// Builds a node's menu entries from its data: `$zooms` (5 `Zoom`s) and `$sections`
/// (9 scene builders) from the consts `$z` (5 `ZoomData`) and `$s` (9 `SecData`).
macro_rules! link_node {
    ($zooms:ident, $sections:ident, $z:ident, $s:ident) => {
        pub const $zooms: [crate::ui::anim::Zoom; 5] = [
            crate::ui::anim::Zoom { key: $z[0].0, label: $z[0].1, build: || Box::new(super::diagrams_scene_link::LinkScene { beats: $z[0].2, keys: $z[0].3, zooms: &[], notes: false }) },
            crate::ui::anim::Zoom { key: $z[1].0, label: $z[1].1, build: || Box::new(super::diagrams_scene_link::LinkScene { beats: $z[1].2, keys: $z[1].3, zooms: &[], notes: false }) },
            crate::ui::anim::Zoom { key: $z[2].0, label: $z[2].1, build: || Box::new(super::diagrams_scene_link::LinkScene { beats: $z[2].2, keys: $z[2].3, zooms: &[], notes: false }) },
            crate::ui::anim::Zoom { key: $z[3].0, label: $z[3].1, build: || Box::new(super::diagrams_scene_link::LinkScene { beats: $z[3].2, keys: $z[3].3, zooms: &[], notes: false }) },
            crate::ui::anim::Zoom { key: $z[4].0, label: $z[4].1, build: || Box::new(super::diagrams_scene_link::LinkScene { beats: $z[4].2, keys: $z[4].3, zooms: &[], notes: false }) },
        ];
        pub const $sections: [fn() -> Box<dyn crate::ui::anim::Scene>; 9] = [
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[0].0, keys: $s[0].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[1].0, keys: $s[1].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[2].0, keys: $s[2].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[3].0, keys: $s[3].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[4].0, keys: $s[4].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[5].0, keys: $s[5].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[6].0, keys: $s[6].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[7].0, keys: $s[7].1, zooms: &[], notes: false }),
            || Box::new(super::diagrams_scene_link::LinkScene { beats: $s[8].0, keys: $s[8].1, zooms: &[], notes: false }),
        ];
    };
}

pub(crate) use link_node;

/// The Fiber-tab pages built on this template.
pub fn nodes() -> Vec<&'static LinkNode> {
    vec![
        &super::diagrams_link_nodes::DSP,
        &super::diagrams_link_nodes::LASER,
        &super::diagrams_link_nodes::FIBER,
        &super::diagrams_link_nodes::PD_NODE,
        &super::diagrams_link_nodes::TRX,
        &super::diagrams_link_nodes::CPO_NODE,
    ]
}

pub fn node(page: &str) -> Option<&'static LinkNode> {
    nodes().into_iter().find(|n| n.page == page)
}

/// The overview scene of a Fiber-tab page.
pub fn overview(page: &str) -> Option<Box<dyn Scene>> {
    let n = node(page)?;
    Some(Box::new(LinkScene { beats: n.beats, keys: n.keys, zooms: n.zooms, notes: true }))
}

/// The keyframes behind zoom `key` (a letter) or section `key` (a digit) of `page`.
pub fn keys_for(page: &str, key: char) -> Option<&'static [LinkKey]> {
    let n = node(page)?;
    if let Some(d) = key.to_digit(10) {
        return n.section_data.get((d as usize).checked_sub(1)?).map(|s| s.1);
    }
    n.zoom_data.iter().find(|z| z.0 == key).map(|z| z.3)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn all_scenes(n: &LinkNode) -> Vec<(String, Box<dyn Scene>)> {
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), overview(n.page).unwrap())];
        for z in n.zooms {
            v.push((z.key.to_string(), (z.build)()));
        }
        for (i, s) in n.sections.iter().enumerate() {
            v.push(((i + 1).to_string(), s()));
        }
        v
    }

    #[test]
    fn every_link_scene_has_one_key_per_beat_and_text() {
        for n in nodes() {
            assert_eq!(n.beats.len(), n.keys.len(), "{} overview", n.page);
            for z in n.zoom_data {
                assert_eq!(z.2.len(), z.3.len(), "{} zoom {}", n.page, z.0);
            }
            for (i, s) in n.section_data.iter().enumerate() {
                assert_eq!(s.0.len(), s.1.len(), "{} section {}", n.page, i + 1);
            }
            let heads = super::super::diagrams_desc::visual(n.page)
                .unwrap()
                .lines()
                .filter(|l| l.starts_with("# "))
                .count();
            assert_eq!(heads, 10, "{}: nine scene sections plus sources", n.page);
            for (_, sc) in all_scenes(n) {
                for b in sc.beats() {
                    assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}: {}", n.page, b.caption);
                }
            }
        }
    }

    #[test]
    fn every_link_frame_is_a_picture_that_moves() {
        for n in nodes() {
            for (name, sc) in all_scenes(n) {
                let p = Player::new(sc, Instant::now());
                let mut seen = std::collections::HashSet::new();
                for ms in (0..p.loop_ms()).step_by(797) {
                    let img = p.pixels(&p.time_at(ms), 120, 72).expect("pixel frame");
                    seen.insert(img.into_raw());
                }
                assert!(seen.len() > 8, "{} {name}: {} distinct frames", n.page, seen.len());
            }
        }
    }

    /// One PNG per beat of every Fiber scene, for a visual check:
    /// `FL_PX_DUMP=/dir FL_LINK=LASER cargo test --release dump_link_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_link_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else { return };
        let only = std::env::var("FL_LINK").ok();
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for n in nodes() {
            if only.as_deref().is_some_and(|o| o != n.page) {
                continue;
            }
            for (name, sc) in all_scenes(n) {
                let beats = sc.beats().len();
                let p = Player::new(sc, Instant::now());
                for beat in 0..beats {
                    let t = Time { ms: 0, beat, local: 0.7, beat_start: 0 };
                    let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                    let img = p.pixels(&t, w, h).unwrap();
                    img.save(dir.join(format!("{}_{name}_{beat}.png", n.page.replace(' ', "_")))).unwrap();
                }
            }
        }
    }
}
