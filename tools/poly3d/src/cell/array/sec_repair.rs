//! Section 7: redundancy and yield. A wafer of dies. Test finds defects (pink); spare
//! rows and columns repair the dies with a few (they turn green); dies with more
//! defects than spares stay bad. The next wafer comes in clean, closing the loop.

use super::super::push_box;
use super::super::push_sphere;
use super::super::stage::{self, label, text, Clock, Shot, GLASS, GREEN, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const R: f64 = 330.0;
const DIE: f64 = 80.0;
const SPARES: usize = 2;

fn dies() -> Vec<(f64, f64, usize)> {
    let mut out = Vec::new();
    for j in -3i32..=3 {
        for i in -3i32..=3 {
            let (x, z) = (i as f64 * 90.0, j as f64 * 90.0);
            if (x.abs() + DIE / 2.0).hypot(z.abs() + DIE / 2.0) > R {
                continue;
            }
            // defects per die: mostly 0-2, a few 3 or more
            let h = ((i + 7) * 31 + (j + 7) * 17) as usize;
            let n = match h % 9 {
                0 | 1 | 2 | 3 => 0,
                4 | 5 => 1,
                6 => 2,
                _ => 3,
            };
            out.push((x, z, n));
        }
    }
    out
}

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 0.0, 0.0], dist: 1150.0, yaw: 0.25, pitch: 0.80 },
    Shot { target: [0.0, 0.0, 0.0], dist: 1100.0, yaw: 0.45, pitch: 0.90 },
    Shot { target: [0.0, 0.0, 60.0], dist: 1050.0, yaw: 0.15, pitch: 0.85 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn tested(c: &Clock) -> f64 {
    c.ramp(0, 0.2, 0.6) * (1.0 - c.ramp(2, 0.85, 0.99))
}

fn repaired(c: &Clock) -> f64 {
    c.ramp(1, 0.2, 0.7) * (1.0 - c.ramp(2, 0.85, 0.99))
}

fn judged(c: &Clock) -> f64 {
    c.ramp(2, 0.05, 0.4) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    crate::push_tube(m, [0.0, -14.0, 0.0], [0.0, 0.0, 0.0], R, 72, STEEL, NO_GLOW, true);
    let (t, r, j) = (tested(c), repaired(c), judged(c));
    for (x, z, n) in dies() {
        let fixable = n <= SPARES;
        let mut col = stage::mix(QUIET, ORANGE, 0.35);
        if fixable {
            col = stage::mix(col, GREEN, 0.7 * r);
        } else {
            col = stage::mix(col, [0.55, 0.12, 0.18], j);
        }
        push_box(m, [x - DIE / 2.0, 0.0, z - DIE / 2.0], [x + DIE / 2.0, 10.0, z + DIE / 2.0], col, NO_GLOW);
        for k in 0..n {
            let fade = if fixable { 1.0 - r } else { 1.0 };
            let a = t * fade;
            if a > 0.01 {
                let p = [x - 20.0 + k as f64 * 20.0, 14.0, z + ((k * 13) % 3) as f64 * 12.0 - 12.0];
                push_sphere(m, p, 7.0 * a, 8, PINK, stage::scaled(PINK, 0.5 * a));
            }
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    stage::ring(cv, cam, [0.0, 1.0, 0.0], R, GLASS, 0.4);
    let all = dies();
    let good = all.iter().filter(|d| d.2 <= SPARES).count();
    label(cv, cam, [R * 0.7, 10.0, -R * 0.5], (0.04, -0.08), "test: defects found", PINK, c.during(0, 0.2, 1.0));
    label(cv, cam, [R * 0.7, 10.0, R * 0.5], (0.04, 0.06), &format!("{SPARES} spares per die: repaired"), GREEN, c.during(1, 0.2, 1.0));
    label(cv, cam, [0.0, 10.0, R], (0.0, 0.08), &format!("{good} of {} dies good", all.len()), TEXT, judged(c));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "redundancy turns bad dies into good ones", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "spares cost area: rows that hold no data", GLASS, judged(c));
}
