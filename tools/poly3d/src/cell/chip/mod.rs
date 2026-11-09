//! 3D scenes for the Chip tab. Every scene is data: a list of keyframes, one per beat,
//! each a camera, a transistor state (`ChipState`), labels and a title. Within a beat
//! the camera and state glide from the previous keyframe to this one, then hold; the
//! first beat glides in from the last, so every scene loops without a cut by
//! construction. The scenes themselves live with their text on the TUI side.

mod rig;

pub use rig::{part_at, ChipPart, ChipState};

use image::RgbaImage;

use super::stage::{self, text, Clock, Shot, GLASS, TEXT};
use super::{callout, rasterize, to_image, Notes};
use crate::{Canvas, Tri, View};

/// One beat of a Chip-tab scene.
#[derive(Clone, Copy, Debug)]
pub struct ChipKey {
    /// camera look-at point, distance, yaw and pitch
    pub target: [f64; 3],
    pub dist: f64,
    pub yaw: f64,
    pub pitch: f64,
    pub state: ChipState,
    /// names on the parts while this beat is on
    pub labels: &'static [(ChipPart, &'static str)],
    /// a line of text at the top of the picture, and a smaller one under it
    pub title: &'static str,
    pub sub: &'static str,
    /// overview only: the parts the beat's notes point at
    pub what: ChipPart,
    pub why: Option<ChipPart>,
}

impl ChipKey {
    /// A keyframe with no labels or titles, looking at `target` from `dist`.
    pub const fn at(target: [f64; 3], dist: f64, yaw: f64, pitch: f64, state: ChipState) -> ChipKey {
        ChipKey { target, dist, yaw, pitch, state, labels: &[], title: "", sub: "", what: ChipPart::Gate, why: None }
    }
    pub const fn labels(mut self, l: &'static [(ChipPart, &'static str)]) -> ChipKey {
        self.labels = l;
        self
    }
    pub const fn title(mut self, t: &'static str, sub: &'static str) -> ChipKey {
        self.title = t;
        self.sub = sub;
        self
    }
    pub const fn notes(mut self, what: ChipPart, why: Option<ChipPart>) -> ChipKey {
        self.what = what;
        self.why = why;
        self
    }
}

/// How long the glide into each beat lasts, as a fraction of the beat.
const GLIDE: f64 = 0.35;

/// One frame of a Chip-tab scene at `beat` and `local` (0..1 through it). `view` is
/// the user's orbit; `notes`, if given, are drawn as boxes beside the parts (overview).
pub fn render_chip(
    keys: &[ChipKey],
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
    let s = ChipState::lerp(&a.state, &b.state, k);
    let shots: Vec<Shot> = keys.iter().map(|k| Shot { target: k.target, dist: k.dist, yaw: k.yaw, pitch: k.pitch }).collect();
    let mut shot = stage::shot_glide(&shots, beat, local, GLIDE);
    // a cut opens the drain side: turn to face the cut
    shot.yaw += 0.95 * s.cut;
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
            boxes.push(callout::Callout { title: "what's happening", body: vec![nt.what.to_string()], col: stage::ORANGE, anchor: Some(part_at(b.what, &s)), prefer: (0.7, 0.2) });
        }
        if !nt.why.is_empty() {
            boxes.push(callout::Callout { title: "why it matters", body: vec![nt.why.to_string()], col: stage::CYAN, anchor: b.why.map(|p| part_at(p, &s)), prefer: (0.75, 0.55) });
        }
        if !nt.facts.is_empty() {
            boxes.push(callout::Callout { title: "key numbers", body: nt.facts.iter().map(|f| format!("- {f}")).collect(), col: stage::PURPLE, anchor: None, prefer: (1.0, 1.0) });
        }
        callout::draw(&mut cv, &cam, &boxes, &avoid, super::notes_alpha(local));
    }
    to_image(&cv)
}

#[cfg(test)]
mod tests {
    use super::*;

    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn mean_diff(a: &RgbaImage, b: &RgbaImage) -> f64 {
        let sum: u64 = a.as_raw().iter().zip(b.as_raw()).map(|(x, y)| u64::from(x.abs_diff(*y))).sum();
        sum as f64 / a.as_raw().len() as f64
    }

    const KEYS: [ChipKey; 4] = [
        ChipKey::at([0.0, 30.0, 0.0], 1100.0, 0.5, 0.35, ChipState::BASE),
        ChipKey::at([0.0, 30.0, 0.0], 1100.0, 0.6, 0.35, ChipState { vg: 1.0, inversion: 1.0, flow: 1.0, ..ChipState::BASE }),
        ChipKey::at([0.0, 60.0, 0.0], 1200.0, 0.4, 0.30, ChipState { arch: 1.0, cut: 1.0, ..ChipState::BASE }),
        ChipKey::at([0.0, 300.0, 0.0], 1800.0, 0.3, 0.30, ChipState { arch: 2.0, contacts: 1.0, metal: 6.0, cells: 3.0, explode: 1.0, ..ChipState::BASE }),
    ];

    #[test]
    #[ignore]
    fn dump_rig() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else { return };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for b in 0..KEYS.len() {
            render_chip(&KEYS, b, 0.7, &View::default(), None, 960, 576, BG).save(dir.join(format!("rig_{b}.png"))).unwrap();
        }
    }

    #[test]
    fn keyframed_scenes_have_no_cut_and_move() {
        let f = |b: usize, l: f64| render_chip(&KEYS, b, l, &View::default(), None, 320, 240, BG);
        for beat in 0..KEYS.len() {
            let d = mean_diff(&f(beat, 0.9995), &f((beat + 1) % KEYS.len(), 0.0));
            assert!(d < 0.6, "beat {beat} jumps by {d}");
            assert!(mean_diff(&f(beat, 0.05), &f(beat, 0.6)) > 0.2, "beat {beat} barely moves");
        }
    }
}
