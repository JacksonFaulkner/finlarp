//! Section 8: who makes it. Three wafers, one per maker, with the camera visiting each.
//! They are the same size on purpose: market share is on the market pages, not here.

use super::stage::{self, label, spotlight, text, Clock, Shot, GLASS, METAL, NO_GLOW, ORANGE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const R: f64 = 215.0;
const SPACE: f64 = 500.0;
const Y: f64 = 110.0;
const MAKERS: [(&str, &str); 3] = [
    ("Micron", "MU"),
    ("SK hynix", "000660.KS"),
    ("Samsung", "005930.KS"),
];

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot {
        target: [x(i) * 0.18, Y - 30.0, 0.0],
        dist: 1780.0,
        yaw: 0.05 * (i as f64 - 1.0),
        pitch: 0.58,
    });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    for i in 0..3 {
        let k = spotlight(c, i, 3);
        let px = x(i);
        crate::push_tube(m, [px, 0.0, 0.0], [px, Y - 6.0, 0.0], 40.0, 20, METAL, NO_GLOW, false);
        crate::push_tube(m, [px, -12.0, 0.0], [px, 0.0, 0.0], 110.0, 32, STEEL, NO_GLOW, true);
        let col = stage::mix(QUIET, [0.84, 0.86, 0.92], 0.35 + 0.65 * k);
        crate::push_tube(m, [px, Y - 6.0, 0.0], [px, Y + 6.0, 0.0], R, 64, col, stage::scaled(ORANGE, 0.08 * k), true);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    // each wafer's die grid turns slowly, one full turn per loop
    let th = c.u() * std::f64::consts::TAU / 3.0;
    let (cs, sn) = (th.cos(), th.sin());
    for i in 0..3 {
        let k = spotlight(c, i, 3);
        let px = x(i);
        let a = (0.30 + 0.45 * k) as f32;
        let turn = |u: f64, v: f64| [px + u * cs - v * sn, Y + 9.0, u * sn + v * cs];
        let pitch = 42.0;
        for n in -5..=5 {
            let t = n as f64 * pitch;
            let half = (R * R - t * t).max(0.0).sqrt();
            cv.line(cam, turn(t, -half), turn(t, half), ORANGE, a);
            cv.line(cam, turn(-half, t), turn(half, t), ORANGE, a);
        }
        stage::ring(cv, cam, [px, Y + 9.0, 0.0], R, GLASS, a);
        let (name, ticker) = MAKERS[i];
        label(cv, cam, [px, Y, R], (-0.04, 0.06), name, TEXT, 0.5 + 0.5 * k);
        label(cv, cam, [px, 0.0, R], (-0.05, 0.12), ticker, ORANGE, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "commodity DRAM makers", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "same size: not market share", TEXT, 0.7);
}
