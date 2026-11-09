//! Zoom e: CoWoS. A GPU and its HBM stacks share one silicon interposer. More stacks
//! need a bigger interposer, and a bigger interposer means fewer of them fit on a
//! 300 mm wafer, so each package uses more of the scarce packaging capacity.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, GLASS, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use super::rig::{DRAM, LOGIC};
use crate::{Cam, Canvas, Tri};

const WAFER_X: f64 = 900.0;
const WAFER_R: f64 = 300.0;

/// How many stacks: 4, then 8 in beat 1, back to 4 at the end.
fn eight(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.6) * (1.0 - c.ramp(2, 0.88, 0.99))
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 30.0, 0.0], dist: 1100.0, yaw: 0.35, pitch: 0.65 },
        Shot { target: [0.0, 30.0, 0.0], dist: 1300.0, yaw: 0.45, pitch: 0.70 },
        Shot { target: [WAFER_X * 0.75, 0.0, 0.0], dist: 1500.0, yaw: 0.20, pitch: 0.95 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// Interposer half-size for the current stack count.
fn half(c: &Clock) -> (f64, f64) {
    let e = eight(c);
    (250.0, 160.0 + 140.0 * e)
}

/// Interposers that fit on the wafer: whole rectangles inside the circle.
fn fit(hx: f64, hz: f64, scale: f64) -> Vec<[f64; 2]> {
    let (w, d) = (2.0 * hx * scale, 2.0 * hz * scale);
    let mut v = Vec::new();
    let n = (WAFER_R / w).ceil() as i32 + 1;
    let k = (WAFER_R / d).ceil() as i32 + 1;
    for i in -n..=n {
        for j in -k..=k {
            let (cx, cz) = (i as f64 * w, j as f64 * d);
            let far = (cx.abs() + w / 2.0).hypot(cz.abs() + d / 2.0);
            if far <= WAFER_R {
                v.push([cx, cz]);
            }
        }
    }
    v
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let e = eight(c);
    let (hx, hz) = half(c);
    push_box(m, [-420.0, -20.0, -420.0], [420.0, 0.0, 420.0], [0.14, 0.28, 0.20], NO_GLOW);
    push_box(m, [-hx, 0.0, -hz], [hx, 10.0, hz], stage::mix(STEEL, LOGIC, 0.4), NO_GLOW);
    push_box(m, [-110.0, 10.0, -140.0], [110.0, 55.0, 140.0], stage::mix(STEEL, PURPLE, 0.5), NO_GLOW);
    for s in 0..8 {
        let shown = if s < 4 { 1.0 } else { e };
        if shown < 0.01 {
            continue;
        }
        let x = if s % 2 == 0 { -180.0 } else { 180.0 };
        let row = (s / 2) as f64;
        let z = if s < 4 { -70.0 + 140.0 * (row) } else { -210.0 + 420.0 * (row - 2.0) };
        push_box(m, [x - 55.0, 10.0, z - 50.0], [x + 55.0, 10.0 + 70.0 * shown, z + 50.0], DRAM, NO_GLOW);
    }
    // the wafer of interposers
    crate::push_tube(m, [WAFER_X, -10.0, 0.0], [WAFER_X, 0.0, 0.0], WAFER_R, 72, QUIET, NO_GLOW, true);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let (hx, hz) = half(c);
    let cells = fit(hx, hz, 0.22);
    let a = (0.3 + 0.5 * c.during(2, 0.05, 1.0)) as f32;
    for [cx, cz] in &cells {
        let (w, d) = (hx * 0.22, hz * 0.22);
        stage::glass_box(cv, cam, [WAFER_X + cx - w, 1.0, cz - d], [WAFER_X + cx + w, 1.0, cz + d], ORANGE, a);
    }
    stage::ring(cv, cam, [WAFER_X, 1.0, 0.0], WAFER_R, GLASS, 0.5);
    let e = eight(c);
    label(cv, cam, [hx, 10.0, hz], (0.03, 0.05), "silicon interposer", TEXT, 0.85);
    label(cv, cam, [180.0, 80.0, -70.0], (0.04, -0.06), if e > 0.5 { "8 HBM stacks" } else { "4 HBM stacks" }, ORANGE, 0.85);
    label(cv, cam, [WAFER_X + WAFER_R, 0.0, 0.0], (0.03, 0.05), &format!("{} interposers per wafer", cells.len()), ORANGE, c.during(2, 0.05, 1.0).max(0.4));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "CoWoS: GPU + HBM on one interposer", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "bigger interposer, fewer per wafer (counts illustrative)", GLASS, 0.8);
}
