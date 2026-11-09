//! Section 8: who makes it. Three scanner makers, each a small scanner on a plinth,
//! the camera visiting one per beat. Only ASML's carries an EUV source; Nikon and
//! Canon make DUV scanners.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, METAL, NO_GLOW, ORANGE, QUIET, STEEL, TEXT, YELLOW};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 520.0;
/// name, ticker, what it makes, EUV?
pub(super) const MAKERS: [(&str, &str, &str, bool); 3] = [
    ("ASML", "ASML", "EUV + DUV scanners", true),
    ("Nikon", "7731.T", "DUV scanners", false),
    ("Canon", "7751.T", "DUV scanners", false),
];

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i) * 0.25, 170.0, 0.0], dist: 1800.0, yaw: 0.05 * (i as f64 - 1.0) + 0.15, pitch: 0.30 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    for (i, (_, _, _, euv)) in MAKERS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        let px = x(i);
        push_box(m, [px - 170.0, 0.0, -140.0], [px + 170.0, 40.0, 140.0], STEEL, NO_GLOW);
        let body = stage::mix(QUIET, [0.80, 0.82, 0.88], 0.35 + 0.65 * k);
        // base, column, top
        push_box(m, [px - 120.0, 40.0, -100.0], [px + 120.0, 110.0, 100.0], body, NO_GLOW);
        crate::push_tube(m, [px, 110.0, 0.0], [px, 260.0, 0.0], 55.0, 32, stage::mix(body, CYAN, 0.35), stage::scaled(CYAN, 0.08 * k), true);
        push_box(m, [px - 90.0, 260.0, -70.0], [px + 90.0, 300.0, 70.0], body, NO_GLOW);
        let src = if *euv { YELLOW } else { ORANGE };
        let h = if *euv { 400.0 } else { 340.0 };
        push_box(m, [px - 50.0, 300.0, -40.0], [px + 50.0, h, 40.0], stage::mix(METAL, src, 0.3 + 0.5 * k), stage::scaled(src, 0.3 * k));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for (i, (name, ticker, what, euv)) in MAKERS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        let px = x(i);
        label(cv, cam, [px, 40.0, 140.0], (-0.04, 0.06), name, TEXT, 0.5 + 0.5 * k);
        label(cv, cam, [px, 0.0, 140.0], (-0.05, 0.12), ticker, ORANGE, k);
        let top = if *euv { 400.0 } else { 340.0 };
        label(cv, cam, [px + 50.0, top, 40.0], (0.03, -0.06), what, if *euv { YELLOW } else { CYAN }, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "lithography scanner makers", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "ASML is the only EUV maker", YELLOW, 0.8);
}
