//! Section 3: computing peak bandwidth, in order. 3200 MT/s per pin, times 64 pins,
//! divided by 8 bits per byte, is 25.6 GB/s per channel; four channels make 102.4.
//! The sum builds up line by line at the top while the gauge follows.

use super::super::stage::{self, text, Clock, Shot, CYAN, GLASS, GREEN, ORANGE};
use super::rig::{self, Rig, CH};
use crate::{Cam, Canvas, Tri};

pub(super) const BEATS: usize = 5;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-80.0, 10.0, -250.0], dist: 1200.0, yaw: 0.25, pitch: 0.50 },
        Shot { target: [-80.0, 10.0, -220.0], dist: 1350.0, yaw: 0.35, pitch: 0.55 },
        Shot { target: [-300.0, 60.0, -260.0], dist: 1300.0, yaw: -0.30, pitch: 0.35 },
        Shot { target: [-300.0, 60.0, -260.0], dist: 1350.0, yaw: -0.40, pitch: 0.35 },
        Shot { target: [-80.0, 10.0, 0.0], dist: 1900.0, yaw: 0.25, pitch: 0.75 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn logmix(a: f64, b: f64, k: f64) -> f64 {
    (a.ln() + (b.ln() - a.ln()) * k).exp()
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    let back = c.ramp(4, 0.82, 0.98);
    r.chan[0] = 1.0;
    r.width0 = 1.0 / 8.0 + 7.0 / 8.0 * c.ramp(1, 0.1, 0.6) * (1.0 - back);
    for k in 1..CH {
        let a = 0.05 + 0.12 * (k - 1) as f64;
        r.chan[k] = c.ramp(4, a, a + 0.25) * (1.0 - back);
    }
    r.flow = [1.0; CH];
    let mut g = 0.4;
    g = logmix(g, 25.6, c.ramp(3, 0.1, 0.6));
    g = logmix(g, 102.4, c.ramp(4, 0.05, 0.5));
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
    let lines = [
        ("1  3200 MT/s on one pin", GREEN),
        ("2  x 64 pins = 204,800 Mbit/s", GREEN),
        ("3  / 8 bits per byte", CYAN),
        ("4  = 25.6 GB/s per channel", CYAN),
        ("5  x 4 channels = 102.4 GB/s", ORANGE),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    let sc = stage::text_scale(cv);
    let clear = 1.0 - c.ramp(4, 0.8, 0.97);
    for (i, (s, col)) in lines.iter().enumerate() {
        let k = c.ramp(i, 0.05, 0.25) * clear;
        let now = stage::spotlight(c, i, BEATS);
        text(cv, (w * 0.04) as i64, (h * 0.04) as i64 + i as i64 * 11 * sc, s, stage::mix(GLASS, *col, 0.5 + 0.5 * now), k);
    }
}
