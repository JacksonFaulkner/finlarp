//! Section 2: the parts, one in the spotlight per beat: a pin and its data rate, the
//! channel's width, the DIMM, the memory controller, more channels, and the HBM stack.

use super::super::stage::{self, spotlight, text, Clock, Shot, CYAN, GREEN, ORANGE, PURPLE};
use super::rig::{self, Rig, CH};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 10.0, -280.0], dist: 900.0, yaw: 0.20, pitch: 0.45 },
        Shot { target: [-60.0, 10.0, -270.0], dist: 1100.0, yaw: 0.40, pitch: 0.55 },
        Shot { target: [400.0, 30.0, -200.0], dist: 1000.0, yaw: 0.80, pitch: 0.45 },
        Shot { target: [-460.0, 30.0, -100.0], dist: 1100.0, yaw: -0.60, pitch: 0.45 },
        Shot { target: [-60.0, 10.0, 0.0], dist: 1900.0, yaw: 0.30, pitch: 0.75 },
        Shot { target: [-260.0, 30.0, 250.0], dist: 1300.0, yaw: -0.30, pitch: 0.55 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let s = |i: usize| spotlight(c, i, BEATS);
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    // pins, channel, DIMM, controller, channels, HBM -> colour slots
    r.colour = [
        0.15 + 0.85 * s(0),
        0.15 + 0.85 * (s(1) + s(4)).min(1.0),
        0.15 + 0.85 * s(2),
        0.15 + 0.85 * s(3),
        0.15 + 0.85 * s(5),
        0.4,
    ];
    r.chan[0] = 1.0;
    r.width0 = 1.0 / 8.0 + 7.0 / 8.0 * (1.0 - s(0));
    for k in 1..CH {
        r.chan[k] = s(4);
    }
    r.flow = [1.0; CH];
    r.hbm = s(5);
    r.gbps = 25.6;
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let jobs: [(&str, Col); BEATS] = [
        ("pin: one wire, so many transfers per second", GREEN),
        ("channel: 64 data pins side by side", GREEN),
        ("DIMM: the chips that feed one channel", GREEN),
        ("controller: drives every channel", PURPLE),
        ("channels: more of them, more bandwidth", CYAN),
        ("HBM: 1024 pins, right beside the processor", ORANGE),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, (job, col)) in jobs.iter().enumerate() {
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, *col, spotlight(c, i, BEATS));
    }
}
