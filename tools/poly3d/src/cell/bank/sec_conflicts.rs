//! Section 5: conflicts and parallelism. Requests spread over many banks overlap
//! and finish fast. The same requests all aimed at one bank, each at a different
//! row, queue up: every one has to precharge and reopen. A controller that reorders
//! them serves the same-row requests together and spreads the rest.

use super::super::stage::{self, text, Clock, Shot, GREEN, ORANGE, PINK, TEXT};
use super::rig::{self, Rig, N};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 0.0, 30.0], dist: 1900.0, yaw: 0.20, pitch: 0.85 },
        Shot { target: [-250.0, 0.0, -150.0], dist: 1300.0, yaw: 0.10, pitch: 0.70 },
        Shot { target: [0.0, 0.0, 0.0], dist: 1800.0, yaw: 0.30, pitch: 0.80 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    // beat 0: eight banks open and read in a quick stagger
    for k in 0..8 {
        let i = (k * 5) % N;
        let a = 0.05 + k as f64 * 0.08;
        r.open[i] += c.ramp(0, a, a + 0.08) * (1.0 - c.ramp(0, a + 0.3, a + 0.4));
        r.read[i] += c.during(0, a + 0.1, a + 0.3);
    }
    // beat 1: bank 0 reopened row after row; the queue waits
    for k in 0..4 {
        let a = 0.03 + k as f64 * 0.24;
        r.open[0] += c.ramp(1, a, a + 0.06) * (1.0 - c.ramp(1, a + 0.14, a + 0.2));
        r.pre[0] += c.during(1, a + 0.14, a + 0.22);
        r.read[0] += c.during(1, a + 0.07, a + 0.14);
    }
    r.row[0] = 0.2 + 0.6 * ((c.u() - 1.0).clamp(0.0, 1.0) * 4.0).floor() / 4.0;
    r.wait[0] = c.during(1, 0.05, 0.95);
    // beat 2: same-row requests together in bank 0, the rest spread
    r.open[0] += c.ramp(2, 0.05, 0.2) * (1.0 - c.ramp(2, 0.75, 0.9));
    r.read[0] += c.during(2, 0.2, 0.75);
    for (k, i) in [4usize, 8, 12].iter().enumerate() {
        let a = 0.1 + k as f64 * 0.12;
        r.open[*i] += c.ramp(2, a, a + 0.1) * (1.0 - c.ramp(2, 0.75, 0.9));
        r.read[*i] += c.during(2, a + 0.15, 0.8);
    }
    for i in 0..N {
        r.open[i] = r.open[i].min(1.0);
        r.read[i] = r.read[i].min(1.0);
        r.pre[i] = r.pre[i].min(1.0);
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
    rig::bank_label(cv, cam, 0, "one bank, a new row each time", PINK, r.wait[0]);
    let (title, col) = match c.beat {
        0 => ("spread over banks: they overlap", GREEN),
        1 => ("all on one bank: PRE + ACT every time", PINK),
        _ => ("reordered: same-row hits together, the rest spread", ORANGE),
    };
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, col, c.during(c.beat, 0.0, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "bank conflicts serialize; banks in parallel overlap", TEXT, 0.85);
}
