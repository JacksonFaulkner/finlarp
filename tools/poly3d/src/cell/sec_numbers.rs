//! Section 6: by the numbers. Cell area counted in F squares: 6 with an open bit line,
//! 8 with a folded one. Then the camera lifts and that cell is one in a 512 x 512 array.

use super::push_box;
use super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, PURPLE, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const F: f64 = 120.0;
const GAP: f64 = 5.0;
const COLS: usize = 2;
/// half of the 512 x 512 sheet, in the same units: drawn at scale would be enormous
const SHEET: f64 = 1500.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 10.0, -60.0], dist: 860.0, yaw: 0.50, pitch: 0.72 },
    Shot { target: [0.0, 10.0, -20.0], dist: 960.0, yaw: 0.35, pitch: 0.72 },
    Shot { target: [0.0, 0.0, 0.0], dist: 5000.0, yaw: 0.25, pitch: 0.92 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// The cell's length in F: 3 wide for 6F^2, growing to 4 for 8F^2, back at the loop start.
fn extra(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.0, 0.3)
    } else {
        c.ramp(1, 0.1, 0.6)
    }
}

/// How far the array has appeared.
fn sheet(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.0, 0.3)
    } else {
        c.ramp(2, 0.0, 0.4)
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let e = extra(c);
    let up = 30.0;
    let z0 = -2.0 * F;
    for row in 0..4 {
        for col in 0..COLS {
            let x = -F + col as f64 * F;
            let z = z0 + row as f64 * F;
            // the fourth row is what folding adds
            let k = if row == 3 { e } else { 1.0 };
            if k < 0.01 {
                continue;
            }
            let colr = if row == 3 { CYAN } else { ORANGE };
            let glow = stage::scaled(colr, 0.3);
            push_box(m, [x + GAP, 0.0, z + GAP], [x + F - GAP, up, z + GAP + (F - 2.0 * GAP) * k], colr, glow);
        }
    }
    let s = sheet(c);
    if s > 0.01 {
        let col = stage::mix([0.157, 0.165, 0.212], STEEL, s);
        push_box(m, [-SHEET, -18.0, -SHEET], [SHEET, -6.0, SHEET], col, NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let e = extra(c);
    let s = sheet(c);
    let close = 1.0 - s;

    // F rulers along the near edges
    if close > 0.02 {
        let a = 0.9 * close as f32;
        let (x, z) = (F + 20.0, -2.0 * F);
        let long = 3.0 + e;
        cv.line(cam, [x, 0.0, z], [x, 0.0, z + long * F], TEXT, a);
        for k in 0..=(long.floor() as usize) {
            let t = z + k as f64 * F;
            cv.line(cam, [x - 8.0, 0.0, t], [x + 8.0, 0.0, t], TEXT, a);
        }
    }
    let six = c.during(0, 0.25, 1.0);
    label(cv, cam, [F, 30.0, -F], (0.06, -0.08), "6F^2: open bit line", ORANGE, six);
    label(cv, cam, [F, 30.0, 1.5 * F], (0.03, 0.08), "8F^2: folded bit line", CYAN, c.during(1, 0.45, 1.0));
    label(cv, cam, [-F, 30.0, -2.0 * F], (-0.06, -0.09), "each square is F x F", TEXT, 0.9 * c.during(0, 0.25, 1.0));

    // the array: lines stand in for the 512 word lines and 512 bit lines
    if s > 0.02 {
        let a = 0.42 * s as f32;
        let n = 32;
        for k in 0..=n {
            let t = -SHEET + 2.0 * SHEET * k as f64 / n as f64;
            cv.line(cam, [-SHEET, -5.0, t], [SHEET, -5.0, t], PURPLE, a);
            cv.line(cam, [t, -5.0, -SHEET], [t, -5.0, SHEET], GLASS, a);
        }
        label(cv, cam, [-SHEET, -5.0, -SHEET * 0.5], (0.05, -0.12), "512 word lines", PURPLE, s);
        label(cv, cam, [SHEET * 0.4, -5.0, -SHEET], (-0.10, -0.08), "512 bit lines", GLASS, s);
        label(cv, cam, [0.0, 30.0, 0.0], (0.10, -0.26), "one cell (not to scale)", ORANGE, s);
        let (w, h) = (cv.w as f64, cv.h as f64);
        text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "a typical array", TEXT, s);
        text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "tREFW 64 ms   tREFI 7800 ns", TEXT, s);
    }
}
