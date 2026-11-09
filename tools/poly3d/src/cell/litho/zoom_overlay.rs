//! Zoom e: overlay. The layer below is already etched (cyan lines). The new layer is
//! printed over it (pink). If the wafer sits a little off, the new lines miss the old
//! ones; the alignment sensor reads the marks on both, the stage corrects, and the
//! lines land on top. The next wafer comes in with its own offset, closing the loop.

use super::super::push_box;
use super::super::stage::{self, glass_box, label, particles, text, Clock, Shot, CYAN, GLASS, GREEN, METAL, NO_GLOW, PINK, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const LINES: [f64; 7] = [-240.0, -160.0, -80.0, 0.0, 80.0, 160.0, 240.0];
const LW: f64 = 24.0;
const HZ: f64 = 160.0;
const UPPER: f64 = 60.0;
const MARK: [f64; 3] = [330.0, 0.0, 0.0];
const SENSOR: [f64; 3] = [330.0, 330.0, 0.0];
const ERR: f64 = 34.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [40.0, 40.0, 0.0], dist: 1150.0, yaw: 0.30, pitch: 0.55 },
    Shot { target: [120.0, 120.0, 0.0], dist: 1250.0, yaw: 0.60, pitch: 0.35 },
    Shot { target: [0.0, 40.0, 0.0], dist: 800.0, yaw: 0.15, pitch: 0.75 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// How far the new layer sits off: misaligned, corrected in beat 1, the next wafer's
/// offset at the end of beat 2.
fn err(c: &Clock) -> f64 {
    ERR * (1.0 - c.ramp(1, 0.35, 0.85) + c.ramp(2, 0.78, 0.98))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let e = err(c);
    push_box(m, [-320.0, -40.0, -200.0], [400.0, 0.0, 200.0], STEEL, NO_GLOW);
    for x in LINES {
        push_box(m, [x - LW / 2.0, 0.0, -HZ], [x + LW / 2.0, 16.0, HZ], stage::mix(STEEL, CYAN, 0.75), stage::scaled(CYAN, 0.08));
    }
    let ok = 1.0 - (e / ERR).clamp(0.0, 1.0);
    let col = stage::mix(PINK, stage::mix(PINK, GREEN, 0.5), ok);
    for x in LINES {
        push_box(m, [x + e - LW / 2.0, UPPER, -HZ + e * 0.5], [x + e + LW / 2.0, UPPER + 14.0, HZ + e * 0.5], col, stage::scaled(col, 0.15));
    }
    // marks: a cross in the old layer, a frame in the new
    let [mx, _, mz] = MARK;
    push_box(m, [mx - 30.0, 0.0, mz - 5.0], [mx + 30.0, 16.0, mz + 5.0], CYAN, stage::scaled(CYAN, 0.2));
    push_box(m, [mx - 5.0, 0.0, mz - 30.0], [mx + 5.0, 16.0, mz + 30.0], CYAN, stage::scaled(CYAN, 0.2));
    let (fx, fz) = (mx + e, mz + e * 0.5);
    for (lo, hi) in [
        ([fx - 45.0, UPPER, fz - 45.0], [fx + 45.0, UPPER + 8.0, fz - 37.0]),
        ([fx - 45.0, UPPER, fz + 37.0], [fx + 45.0, UPPER + 8.0, fz + 45.0]),
        ([fx - 45.0, UPPER, fz - 45.0], [fx - 37.0, UPPER + 8.0, fz + 45.0]),
        ([fx + 37.0, UPPER, fz - 45.0], [fx + 45.0, UPPER + 8.0, fz + 45.0]),
    ] {
        push_box(m, lo, hi, PINK, stage::scaled(PINK, 0.2));
    }
    let [sx, sy, sz] = SENSOR;
    let read = c.during(1, 0.0, 0.9);
    push_box(m, [sx - 40.0, sy, sz - 30.0], [sx + 40.0, sy + 50.0, sz + 30.0], stage::mix(METAL, GREEN, 0.3 + 0.5 * read), stage::scaled(GREEN, 0.25 * read));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let e = err(c);
    glass_box(cv, cam, [-320.0, 16.0, -200.0], [400.0, UPPER, 200.0], GLASS, 0.18);
    let read = c.during(1, 0.0, 0.9);
    let path = [[SENSOR[0], SENSOR[1], 0.0], [MARK[0], UPPER + 10.0, 0.0], [MARK[0], 18.0, 0.0]];
    particles(cv, cam, &path, 7, c.u() * 1.8, 7.0, GREEN, read);
    // the error, as a bracket between an old line and its new partner
    if e > 1.0 {
        let y = UPPER + 20.0;
        cv.overlay(cam, [0.0, y, HZ], [e, y, HZ + e * 0.5], TEXT, 0.9);
    }
    label(cv, cam, [LINES[0], 16.0, HZ], (-0.10, 0.10), "layer below (etched)", CYAN, 0.9);
    label(cv, cam, [LINES[0] + e, UPPER + 14.0, -HZ], (-0.10, -0.08), "new layer", PINK, 0.9);
    label(cv, cam, [e, UPPER + 20.0, HZ], (0.04, 0.05), &format!("off by {:.0}", e), TEXT, (e / ERR).clamp(0.0, 1.0));
    label(cv, cam, SENSOR, (0.05, -0.05), "alignment sensor", GREEN, 0.5 + 0.5 * read);
    label(cv, cam, [MARK[0] + 30.0, 16.0, 0.0], (0.05, 0.08), "alignment marks", GREEN, 0.8);
    let tol = c.during(2, 0.05, 0.75);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "overlay budget: a few nm", TEXT, tol);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "NXE:3800E matched overlay 0.9 nm (ASML)", GLASS, tol);
}
