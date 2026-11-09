//! 3D scenes for the Packaging tab, on the Chip tab's keyframe pattern: each scene is
//! a list of keyframes (camera, package state, labels, title), glided between so every
//! scene is continuous and loops without a cut. The scenes live with their text on the
//! TUI side.

mod rig;

pub use rig::{pkg_part_at, PkgPart, PkgState};

use image::RgbaImage;

use super::stage::{self, text, Clock, Shot, GLASS, TEXT};
use super::{callout, rasterize, to_image, Notes};
use crate::{Canvas, Tri, View};

/// One beat of a Packaging-tab scene.
#[derive(Clone, Copy, Debug)]
pub struct PkgKey {
    /// camera look-at point, distance, yaw and pitch
    pub target: [f64; 3],
    pub dist: f64,
    pub yaw: f64,
    pub pitch: f64,
    pub state: PkgState,
    /// names on the parts while this beat is on
    pub labels: &'static [(PkgPart, &'static str)],
    /// a line of text at the top of the picture, and a smaller one under it
    pub title: &'static str,
    pub sub: &'static str,
    /// overview only: the parts the beat's notes point at
    pub what: PkgPart,
    pub why: Option<PkgPart>,
}

impl PkgKey {
    /// A keyframe with no labels or titles, looking at `target` from `dist`.
    pub const fn at(target: [f64; 3], dist: f64, yaw: f64, pitch: f64, state: PkgState) -> PkgKey {
        PkgKey { target, dist, yaw, pitch, state, labels: &[], title: "", sub: "", what: PkgPart::Logic, why: None }
    }
    pub const fn labels(mut self, l: &'static [(PkgPart, &'static str)]) -> PkgKey {
        self.labels = l;
        self
    }
    pub const fn title(mut self, t: &'static str, sub: &'static str) -> PkgKey {
        self.title = t;
        self.sub = sub;
        self
    }
    pub const fn notes(mut self, what: PkgPart, why: Option<PkgPart>) -> PkgKey {
        self.what = what;
        self.why = why;
        self
    }
}

/// How long the glide into each beat lasts, as a fraction of the beat.
const GLIDE: f64 = 0.35;

/// One frame of a Packaging-tab scene at `beat` and `local` (0..1 through it). `view` is
/// the user's orbit; `notes`, if given, are drawn as boxes beside the parts (overview).
pub fn render_pkg(
    keys: &[PkgKey],
    beat: usize,
    local: f64,
    view: &View,
    notes: Option<&Notes>,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> RgbaImage {
    let n = keys.len().max(1);
    let beat = beat % n;
    let local = local.clamp(0.0, 1.0);
    let (a, b) = (&keys[(beat + n - 1) % n], &keys[beat]);
    let k = stage::smooth_step(0.0, GLIDE, local);
    let s = PkgState::lerp(&a.state, &b.state, k);
    let shots: Vec<Shot> = keys.iter().map(|k| Shot { target: k.target, dist: k.dist, yaw: k.yaw, pitch: k.pitch }).collect();
    let shot = stage::shot_glide(&shots, beat, local, GLIDE);
    let mut cam = stage::camera(&shot, view, w, h);
    if notes.is_some() && w as f64 > h as f64 * 1.3 {
        cam.cx -= w as f64 * 0.13;
    }
    let c = Clock { beat, local };
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    let mut tris: Vec<Tri> = Vec::new();
    rig::solids(&s, &mut tris);
    rasterize(&mut cv, &cam, tris);
    rig::overlay(&mut cv, &cam, &s, c.u() * 1.2 + beat as f64 * 0.0);
    let mut avoid = Vec::new();
    rig::labels(&mut cv, &cam, &s, a.labels, 1.0 - k, &mut avoid);
    rig::labels(&mut cv, &cam, &s, b.labels, k, &mut avoid);
    let (fw, fh) = (cv.w as f64, cv.h as f64);
    for (key, alpha) in [(a, 1.0 - k), (b, k)] {
        if notes.is_none() {
            text(&mut cv, (fw * 0.04) as i64, (fh * 0.04) as i64, key.title, TEXT, alpha);
            text(&mut cv, (fw * 0.04) as i64, (fh * 0.10) as i64, key.sub, GLASS, alpha * 0.85);
        }
    }
    if let Some(nt) = notes {
        let mut boxes = Vec::new();
        if !nt.what.is_empty() {
            boxes.push(callout::Callout { title: "what's happening", body: vec![nt.what.to_string()], col: stage::ORANGE, anchor: Some(pkg_part_at(b.what, &s)), prefer: (0.7, 0.2) });
        }
        if !nt.why.is_empty() {
            boxes.push(callout::Callout { title: "why it matters", body: vec![nt.why.to_string()], col: stage::CYAN, anchor: b.why.map(|p| pkg_part_at(p, &s)), prefer: (0.75, 0.55) });
        }
        if !nt.facts.is_empty() {
            boxes.push(callout::Callout { title: "key numbers", body: nt.facts.iter().map(|f| format!("- {f}")).collect(), col: stage::PURPLE, anchor: None, prefer: (1.0, 1.0) });
        }
        callout::draw(&mut cv, &cam, &boxes, &avoid, super::notes_alpha(local));
    }
    to_image(&cv)
}

