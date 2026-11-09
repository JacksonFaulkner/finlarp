//! Section 4: DDR, GDDR and HBM per device, as bars on a log scale (80 units a
//! decade from 1 GB/s): a DDR5-4800 DIMM, 38.4 GB/s; a GDDR6 chip at 16 Gb/s, 64 GB/s;
//! an HBM3 stack, 819 GB/s. The camera visits one per beat.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GLASS, GREEN, NO_GLOW, ORANGE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const KINDS: [(&str, &str, f64, Col); 3] = [
    ("DDR5-4800 DIMM", "2 x 32 pins x 4.8 Gbit/s", 38.4, GREEN),
    ("GDDR6 chip", "32 pins x 16 Gbit/s", 64.0, CYAN),
    ("HBM3 stack", "1024 pins x 6.4 Gbit/s", 819.2, ORANGE),
];

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * 360.0
}

fn hgt(v: f64) -> f64 {
    120.0 * v.log10()
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i) * 0.6, 160.0, 0.0], dist: 1250.0, yaw: 0.20 + 0.05 * i as f64, pitch: 0.25 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-520.0, -20.0, -150.0], [520.0, 0.0, 150.0], STEEL, NO_GLOW);
    for (i, (_, _, v, col)) in KINDS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        push_box(m, [x(i) - 55.0, 0.0, -55.0], [x(i) + 55.0, hgt(*v), 55.0], stage::mix(QUIET, *col, 0.35 + 0.65 * k), stage::scaled(*col, 0.15 * k));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for (i, (name, how, v, col)) in KINDS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        label(cv, cam, [x(i), hgt(*v), 55.0], (-0.04, -0.07), &format!("{v} GB/s"), *col, 0.5 + 0.5 * k);
        label(cv, cam, [x(i), 0.0, 55.0], (-0.05, 0.08), name, TEXT, 0.5 + 0.5 * k);
        let (w, h) = (cv.w as f64, cv.h as f64);
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, how, *col, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "per device, log scale", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "GB/s = pins x Gbit/s / 8", GLASS, 0.8);
}
