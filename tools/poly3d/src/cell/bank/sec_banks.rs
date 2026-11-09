//! Section 1: what happens. One bank at a time, the data bus sits idle while each
//! row opens; two banks overlap, one opening while the other reads; four banks in
//! turn keep the bus busy. The chip resets to idle at the end of the loop.

use super::super::stage::{self, text, Clock, Shot, GREEN, ORANGE, TEXT};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-150.0, 0.0, -100.0], dist: 1500.0, yaw: 0.20, pitch: 0.75 },
        Shot { target: [0.0, 0.0, -60.0], dist: 1700.0, yaw: 0.30, pitch: 0.75 },
        Shot { target: [0.0, 0.0, 30.0], dist: 1900.0, yaw: 0.20, pitch: 0.85 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// A bank's cycle inside [a, b] of `beat`: open, read, close.
fn cycle(r: &mut Rig, c: &Clock, i: usize, beat: usize, a: f64, b: f64) {
    let w = b - a;
    r.cmd[i] += c.during(beat, a, a + 0.25 * w);
    r.open[i] += c.ramp(beat, a + 0.1 * w, a + 0.35 * w) * (1.0 - c.ramp(beat, b - 0.15 * w, b));
    r.read[i] += c.during(beat, a + 0.4 * w, b - 0.2 * w);
    r.pre[i] += c.during(beat, b - 0.2 * w, b);
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    // beat 0: bank 0, then bank 0 again (serial)
    cycle(&mut r, c, 0, 0, 0.0, 0.5);
    cycle(&mut r, c, 0, 0, 0.5, 1.0);
    // beat 1: banks 0 and 4 overlap
    cycle(&mut r, c, 0, 1, 0.0, 0.7);
    cycle(&mut r, c, 4, 1, 0.25, 0.98);
    // beat 2: four banks staggered
    for (k, i) in [0usize, 4, 8, 12].iter().enumerate() {
        let a = k as f64 * 0.15;
        cycle(&mut r, c, *i, 2, a, a + 0.5);
    }
    for i in 0..rig::N {
        r.open[i] = r.open[i].min(1.0);
        r.read[i] = r.read[i].min(1.0);
        r.cmd[i] = r.cmd[i].min(1.0);
        r.pre[i] = r.pre[i].min(1.0);
        r.row[i] = 0.3 + 0.1 * (i % 5) as f64;
    }
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let (title, col) = match c.beat {
        0 => ("one bank at a time: the bus waits", ORANGE),
        1 => ("two banks overlap", GREEN),
        _ => ("four banks in turn: the bus stays busy", GREEN),
    };
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, col, c.during(c.beat, 0.0, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "many banks, one command bus, one data bus", TEXT, 0.85);
}
