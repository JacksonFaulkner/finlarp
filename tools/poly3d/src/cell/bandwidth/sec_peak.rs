//! Section 1: what happens. Peak bandwidth is the data rate per pin times the number
//! of pins times the number of channels: one pin, then a 64-pin channel, then four.

use super::super::stage::{self, Clock, Shot};
use super::rig::{self, Rig, CH};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-80.0, 10.0, -250.0], dist: 1300.0, yaw: 0.25, pitch: 0.55 },
        Shot { target: [-80.0, 10.0, -200.0], dist: 1400.0, yaw: 0.35, pitch: 0.60 },
        Shot { target: [-80.0, 10.0, 0.0], dist: 1900.0, yaw: 0.30, pitch: 0.75 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn logmix(a: f64, b: f64, k: f64) -> f64 {
    (a.ln() + (b.ln() - a.ln()) * k).exp()
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    let back = c.ramp(2, 0.8, 0.98);
    r.chan[0] = 1.0;
    r.width0 = 1.0 / 8.0 + 7.0 / 8.0 * c.ramp(1, 0.1, 0.6) * (1.0 - back);
    for k in 1..CH {
        let a = 0.05 + 0.15 * (k - 1) as f64;
        r.chan[k] = c.ramp(2, a, a + 0.25) * (1.0 - back);
    }
    r.flow = [1.0; CH];
    let mut g = 0.4;
    g = logmix(g, 25.6, c.ramp(1, 0.1, 0.6));
    g = logmix(g, 102.4, c.ramp(2, 0.05, 0.6));
    r.gbps = logmix(g, 0.4, back);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
}
