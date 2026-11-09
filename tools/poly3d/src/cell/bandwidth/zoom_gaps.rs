//! Zoom d: where peak bandwidth goes. Close on one channel: reads stream steadily;
//! switching to writes and back leaves the bus empty while it turns around; a refresh
//! stops the stream while every bank refreshes. Real traffic runs below the peak.

use super::super::stage::{self, label, text, Clock, Shot, GREEN, ORANGE, PINK, TEXT};
use super::rig::{self, Part, Rig};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-20.0, 10.0, -270.0], dist: 1000.0, yaw: 0.30, pitch: 0.45 },
        Shot { target: [0.0, 10.0, -270.0], dist: 950.0, yaw: 0.15, pitch: 0.50 },
        Shot { target: [-40.0, 10.0, -270.0], dist: 1000.0, yaw: 0.40, pitch: 0.45 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.chan[0] = 1.0;
    r.flow[0] = 1.0;
    r.gbps = 25.6;
    r.dir = 1.0 - 2.0 * c.ramp(1, 0.15, 0.3) + 2.0 * c.ramp(1, 0.65, 0.8);
    r.gaps = c.during(2, 0.15, 0.85);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    let at = rig::at(Part::Channel(0), &r);
    label(cv, cam, at, (0.0, 0.08), "reads: data to the processor", GREEN, c.during(0, 0.05, 1.0));
    label(cv, cam, at, (0.0, 0.08), "writes: data to the DIMM", ORANGE, c.during(1, 0.32, 0.62));
    let turn = c.during(1, 0.12, 0.33) + c.during(1, 0.62, 0.83);
    label(cv, cam, at, (0.0, -0.10), "turnaround: bus empty", PINK, turn.min(1.0));
    label(cv, cam, at, (0.0, 0.08), "refresh: no data at all", PINK, r.gaps);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "peak 25.6 GB/s; real traffic gets less", TEXT, 0.9);
}
