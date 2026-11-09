//! Zoom d: step and scan. Looking down on the wafer: the slit sweeps one field while
//! the reticle above runs the other way, 4x as far; then the stage steps field to
//! field, alternating the scan direction. Last, High-NA: each field is half as tall,
//! so the same wafer takes about twice as many exposures.

use super::super::stage::{self, label, text, Clock, Shot, GLASS, ORANGE, PINK, TEXT};
use super::rig::{self, Rig, FIELD, N_FIELDS, WAFER_Y};
use crate::{Cam, Canvas, Tri};

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 200.0, 0.0], dist: 1700.0, yaw: 0.70, pitch: 0.42 },
    Shot { target: [60.0, 60.0, 190.0], dist: 1550.0, yaw: 0.40, pitch: 0.58 },
    Shot { target: [40.0, 60.0, 200.0], dist: 1350.0, yaw: 0.25, pitch: 0.66 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let p = match c.beat {
        0 => stage::smooth_step(0.05, 0.95, c.local),
        1 => 1.0 + (N_FIELDS as f64 - 1.0) * stage::smooth_step(0.0, 0.9, c.local),
        _ => N_FIELDS as f64,
    };
    rig::walk(&mut r, p);
    let on = c.ramp(0, 0.0, 0.05) * (1.0 - c.ramp(1, 0.9, 1.0));
    r.light = on;
    r.project = on;
    if c.beat == 2 {
        let (w, rz) = rig::walk_end();
        let k = c.ramp(2, 0.0, 0.3);
        r.wafer = [w[0] * (1.0 - k), w[1] * (1.0 - k)];
        r.reticle_z = rz * (1.0 - k);
    }
    let clear = 1.0 - c.ramp(2, 0.78, 0.98);
    for e in r.exposed.iter_mut() {
        e.0 *= clear;
    }
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    let half = c.during(2, 0.25, 1.0);
    if half > 0.01 {
        let [wx, wz] = r.wafer;
        for f in rig::fields() {
            let (x, z, y) = (f[0] + wx, f[1] + wz, WAFER_Y + 2.5);
            cv.line(cam, [x - FIELD / 2.0, y, z], [x + FIELD / 2.0, y, z], ORANGE, (0.9 * half) as f32);
        }
    }
    let scan = c.during(0, 0.05, 1.0);
    label(cv, cam, [0.0, rig::RETICLE_Y + 8.0, r.reticle_z], (0.08, -0.06), "reticle runs 4x as far", TEXT, scan);
    label(cv, cam, rig::at(rig::Part::Slit, &r), (0.08, 0.06), "slit sweeps one field", PINK, scan);
    let done = r.exposed.iter().filter(|e| e.0 > 0.99).count();
    let step = c.during(1, 0.0, 1.0);
    label(cv, cam, rig::at(rig::Part::Resist, &r), (0.05, 0.05), &format!("{done} of {N_FIELDS} fields"), PINK, step);
    label(cv, cam, [FIELD / 2.0, WAFER_Y, 0.0], (0.10, -0.10), "High-NA: half fields, 2x exposures", ORANGE, half);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "scans alternate direction: no flyback", GLASS, 0.8 * step);
}
