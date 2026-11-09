//! Zoom e: refresh and banks. DDR4's all-bank refresh closes every bank at once and
//! blocks the rank while it runs. DDR5 adds same-bank refresh: one bank in every
//! group refreshes while the other banks keep serving reads. (Drawn with the 16-bank
//! layout; DDR5 has 8 groups of 4.)

use super::super::stage::{self, text, Clock, Shot, CYAN, GREEN, PINK, TEXT};
use super::rig::{self, Rig, N};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 0.0, 30.0], dist: 1800.0, yaw: 0.25, pitch: 0.90 },
        Shot { target: [0.0, 0.0, 30.0], dist: 1750.0, yaw: 0.40, pitch: 0.85 },
        Shot { target: [0.0, 0.0, 30.0], dist: 1800.0, yaw: 0.10, pitch: 0.90 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// Same-bank refresh in beats 1-2: bank `b` of every group, b stepping 0..3.
fn same_bank(c: &Clock, i: usize) -> f64 {
    let b = i % 4;
    let u = (c.u() - 1.0).clamp(0.0, 2.0) / 2.0;
    let (a, z) = (b as f64 / 4.0, (b + 1) as f64 / 4.0);
    let w = z - a;
    let inside = stage::smooth_step(a, a + 0.2 * w, u) * (1.0 - stage::smooth_step(z - 0.2 * w, z, u));
    inside * (c.beat >= 1) as i32 as f64
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let all = c.during(0, 0.15, 0.9);
    for i in 0..N {
        let sb = same_bank(c, i);
        r.refresh[i] = all + sb;
        r.wait[i] = 0.0;
        // banks not refreshing serve reads in the same-bank beats
        let serve = c.during(1, 0.05, 1.0) + c.during(2, 0.0, 0.95);
        r.read[i] = if i % 3 == 0 { serve.min(1.0) * (1.0 - sb) } else { 0.0 };
        r.open[i] = r.read[i];
    }
    // reads queued and blocked during the all-bank refresh
    for i in [0, 6, 13] {
        r.wait[i] = all;
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
    let all = c.during(0, 0.15, 0.9);
    let sb = c.during(1, 0.0, 1.0) + c.during(2, 0.0, 1.0);
    rig::bank_label(cv, cam, 13, "reads blocked", PINK, all);
    rig::bank_label(cv, cam, 3, "one bank per group refreshes", CYAN, sb.min(1.0));
    rig::bank_label(cv, cam, 6, "others keep reading", GREEN, sb.min(1.0));
    let (w, h) = (cv.w as f64, cv.h as f64);
    let title = if c.beat == 0 { "DDR4 all-bank refresh: the rank is blocked" } else { "DDR5 same-bank refresh (REFsb)" };
    let k = if c.beat == 0 { c.during(0, 0.0, 1.0) } else { c.during(1, 0.0, 1.0) + c.during(2, 0.0, 1.0) };
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, TEXT, k.min(1.0));
}
