//! Section 3: one read, in order. A timing diagram in 3D: word line, bit line and cell
//! as walls whose height is their level, drawn by a playhead through the five steps.

use super::push_box;
use super::stage::{self, label, smooth_step, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, PINK, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 5;
const X0: f64 = -600.0;
const X1: f64 = 600.0;
const TALL: f64 = 195.0;
const THICK: f64 = 16.0;
const SEGS: usize = 150;
const WL_Z: f64 = -270.0;
const BL_Z: f64 = 0.0;
const CELL_Z: f64 = 270.0;

const STEPS: [&str; BEATS] = ["1 precharge", "2 word line", "3 share", "4 sense", "5 restore"];

/// (word line, bit line, cell) at `u`, 0..5 through the read.
fn levels(u: f64) -> (f64, f64, f64) {
    let r = |a: f64, b: f64| smooth_step(a, b, u);
    let wl = r(1.1, 1.8);
    let bl = 0.5 + 0.07 * r(2.1, 2.9) + 0.43 * r(3.1, 3.8);
    let cell = 1.0 - 0.43 * r(2.1, 2.9) + 0.43 * r(4.1, 4.8);
    (wl, bl, cell)
}

fn x_at(u: f64) -> f64 {
    X0 + (X1 - X0) * u / BEATS as f64
}

/// The drawing erases itself at the end of the loop, so the next read starts clean.
fn fade(c: &Clock) -> f64 {
    1.0 - c.ramp(BEATS - 1, 0.86, 1.0)
}

pub(super) fn shot(c: &Clock) -> Shot {
    // high enough that each signal has its own lane and none hides another
    let keys = [Shot { target: [0.0, 40.0, 30.0], dist: 1780.0, yaw: 0.12, pitch: 0.72 }; BEATS];
    stage::shot_at(&keys, c.beat, c.local)
}

/// A wall under the curve `f` from time 0 to `u`.
fn wall(m: &mut Vec<Tri>, z: f64, u: f64, k: f64, col: Col, f: impl Fn(f64) -> f64) {
    let glow = stage::scaled(col, 0.25);
    let side = stage::scaled(col, 0.72);
    let n = ((u / BEATS as f64) * SEGS as f64).ceil() as usize;
    for i in 0..n {
        let (a, b) = (u * i as f64 / n as f64, u * (i + 1) as f64 / n as f64);
        let (xa, xb) = (x_at(a), x_at(b));
        let (ya, yb) = (f(a) * TALL * k, f(b) * TALL * k);
        // the front face, the back face, and the top edge in full colour
        for zz in [z - THICK, z + THICK] {
            let (p, q, r, s) = ([xa, 0.0, zz], [xb, 0.0, zz], [xb, yb, zz], [xa, ya, zz]);
            m.push(Tri { p: [p, q, r], base: side, emit: stage::scaled(glow, 0.6) });
            m.push(Tri { p: [p, r, s], base: side, emit: stage::scaled(glow, 0.6) });
        }
        let (p, q, r, s) = ([xa, ya, z - THICK], [xb, yb, z - THICK], [xb, yb, z + THICK], [xa, ya, z + THICK]);
        m.push(Tri { p: [p, q, r], base: col, emit: glow });
        m.push(Tri { p: [p, r, s], base: col, emit: glow });
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [X0 - 30.0, -14.0, -350.0], [X1 + 30.0, 0.0, 350.0], STEEL, NO_GLOW);
    let u = c.u();
    let k = fade(c);
    if u > 0.01 && k > 0.01 {
        wall(m, WL_Z, u, k, PINK, |s| levels(s).0);
        wall(m, BL_Z, u, k, CYAN, |s| levels(s).1);
        wall(m, CELL_Z, u, k, ORANGE, |s| levels(s).2);
    }
    // a floor tile per step, lit while it plays
    for i in 0..BEATS {
        let lit = stage::spotlight(c, i, BEATS);
        let (a, b) = (x_at(i as f64) + 6.0, x_at(i as f64 + 1.0) - 6.0);
        let col = stage::mix([0.26, 0.27, 0.32], TEXT, 0.75 * lit);
        push_box(m, [a, 0.0, 356.0], [b, 8.0, 412.0], col, stage::scaled(TEXT, 0.15 * lit));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let u = c.u();
    let k = fade(c);
    let (wl, bl, cell) = levels(u);

    // VDD and VDD/2 marks on each wall's back line, then the moving playhead
    for z in [WL_Z, BL_Z, CELL_Z] {
        cv.line(cam, [X0, TALL, z], [X1, TALL, z], GLASS, 0.3);
    }
    cv.line(cam, [X0, TALL * 0.5, BL_Z], [X1, TALL * 0.5, BL_Z], GLASS, 0.6);
    label(cv, cam, [X1, TALL * 0.5, BL_Z], (-0.05, 0.03), "VDD/2", GLASS, 0.9);
    // the step numbers on their floor tiles
    for i in 0..BEATS {
        let lit = stage::spotlight(c, i, BEATS);
        let at = [(x_at(i as f64) + x_at(i as f64 + 1.0)) / 2.0, 8.0, 384.0];
        if let Some((px, py, _)) = cam.project(at) {
            let n = (b'1' + i as u8) as char;
            let mut buf = [0u8; 4];
            let col = stage::mix(GLASS, ORANGE, lit);
            text(cv, px as i64 - 4, py as i64 - 6, n.encode_utf8(&mut buf), col, 0.95);
        }
    }
    let x = x_at(u);
    let a = (0.7 * k * c.ramp(0, 0.0, 0.05)) as f32;
    for (p, q) in [
        ([x, 0.0, -350.0], [x, 0.0, 350.0]),
        ([x, TALL + 20.0, -350.0], [x, TALL + 20.0, 350.0]),
        ([x, 0.0, -350.0], [x, TALL + 20.0, -350.0]),
        ([x, 0.0, 350.0], [x, TALL + 20.0, 350.0]),
    ] {
        cv.overlay(cam, p, q, TEXT, a);
    }
    stage::dot(cv, cam, [x, wl * TALL * k + 6.0, WL_Z], 15.0, PINK, k);
    stage::dot(cv, cam, [x, bl * TALL * k + 6.0, BL_Z], 15.0, CYAN, k);
    stage::dot(cv, cam, [x, cell * TALL * k + 6.0, CELL_Z], 15.0, ORANGE, k);

    label(cv, cam, [X0, TALL, WL_Z], (0.0, -0.05), "word line", PINK, 0.95);
    label(cv, cam, [X0, TALL, BL_Z], (0.0, -0.05), "bit line", CYAN, 0.95);
    label(cv, cam, [X0, TALL, CELL_Z], (0.0, -0.05), "cell", ORANGE, 0.95);

    // the steps, in order along the foot of the frame
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, s) in STEPS.iter().enumerate() {
        let lit = stage::spotlight(c, i, BEATS);
        if lit > 0.01 {
            text(cv, (w * 0.04) as i64, (h * 0.04) as i64, s, TEXT, lit);
        }
    }
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "the read drains the cell: restore is part of it", ORANGE, c.during(BEATS - 1, 0.25, 0.9));
}
