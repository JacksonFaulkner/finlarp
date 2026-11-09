//! The BANK overview: sixteen banks sharing one command bus and one data bus, seven
//! beats. ACTIVATE bank A; while it opens, ACTIVATE bank B in another group; READs
//! alternate between them so the data bus never idles; more activates hit the
//! four-activate window and the fifth waits; a request for another row in bank A
//! has to precharge and reopen while the others keep working; an all-bank refresh
//! closes everything, ending idle.

use super::super::stage::{Clock, Rect, Shot, CYAN, ORANGE, PINK};
use super::rig::{self, centre, Part, Rig, N};
use crate::{Cam, Canvas};

pub(super) const BEATS: usize = 7;
pub(super) const A: usize = 0;
pub(super) const B: usize = 4;
pub(super) const C: usize = 8;
pub(super) const D: usize = 12;
pub(super) const E: usize = 1;

/// A command pulse in the window [a, b] of `beat`.
fn pulse(c: &Clock, beat: usize, a: f64, b: f64) -> f64 {
    c.during(beat, a, b)
}

pub(super) fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let close_all = 1.0 - c.ramp(6, 0.0, 0.25);
    // A: open in beat 1, closed and reopened on a new row in beat 5
    r.cmd[A] = pulse(c, 1, 0.0, 0.45) + pulse(c, 5, 0.05, 0.3) + pulse(c, 5, 0.4, 0.65);
    let a_gap = c.ramp(5, 0.1, 0.3) * (1.0 - c.ramp(5, 0.45, 0.75));
    r.open[A] = c.ramp(1, 0.3, 0.7) * (1.0 - a_gap) * close_all;
    r.pre[A] = pulse(c, 5, 0.08, 0.4);
    r.row[A] = if c.u() < 5.38 { 0.25 } else { 0.75 };
    // B: opens during beat 2 while A is open
    r.cmd[B] = pulse(c, 2, 0.0, 0.45);
    r.open[B] = c.ramp(2, 0.3, 0.7) * close_all;
    r.row[B] = 0.6;
    // reads alternate A, B; B keeps reading during A's conflict
    r.read[A] = pulse(c, 3, 0.05, 0.5);
    r.read[B] = pulse(c, 3, 0.5, 0.95) + pulse(c, 5, 0.2, 0.85);
    // beat 4: C and D open, E has to wait for the window
    r.cmd[C] = pulse(c, 4, 0.0, 0.25);
    r.open[C] = c.ramp(4, 0.15, 0.4) * close_all;
    r.cmd[D] = pulse(c, 4, 0.2, 0.45);
    r.open[D] = c.ramp(4, 0.35, 0.6) * close_all;
    r.wait[E] = c.ramp(4, 0.45, 0.55) * (1.0 - c.ramp(4, 0.85, 0.95));
    r.cmd[E] = c.ramp(4, 0.82, 0.92) * (1.0 - c.ramp(5, 0.05, 0.2));
    r.open[E] = c.ramp(5, 0.0, 0.3) * close_all;
    r.row[C] = 0.4;
    r.row[D] = 0.7;
    r.row[E] = 0.35;
    // beat 6: precharge everything, then refresh every bank at once (DDR4 all-bank)
    let pre_all = pulse(c, 6, 0.0, 0.3);
    let refresh = pulse(c, 6, 0.28, 0.95);
    for i in [A, B, C, D, E] {
        r.pre[i] = (r.pre[i] + pre_all).min(1.0);
    }
    for i in 0..N {
        r.refresh[i] = refresh;
    }
    r
}

pub(super) struct Stop {
    pub shot: Shot,
    pub what: Part,
    pub why: Option<Part>,
}

pub(super) fn stops() -> [Stop; BEATS] {
    let s = |target: [f64; 3], dist: f64, yaw: f64, pitch: f64| Shot { target, dist, yaw, pitch };
    let a = centre(A);
    [
        Stop { shot: s([0.0, 0.0, 30.0], 1900.0, 0.30, 0.90), what: Part::Group(0), why: Some(Part::DataBus) },
        Stop { shot: s([a[0] * 0.6, 0.0, a[2] * 0.4], 1500.0, 0.10, 0.70), what: Part::Bank(A), why: Some(Part::CmdBus) },
        Stop { shot: s([0.0, 0.0, -150.0], 1500.0, 0.20, 0.70), what: Part::Bank(B), why: Some(Part::Bank(A)) },
        Stop { shot: s([0.0, 0.0, 120.0], 1700.0, 0.45, 0.65), what: Part::DataBus, why: Some(Part::Io) },
        Stop { shot: s([0.0, 0.0, 30.0], 1900.0, 0.15, 0.85), what: Part::Bank(E), why: Some(Part::Bank(C)) },
        Stop { shot: s([a[0] * 0.6, 0.0, a[2] * 0.3], 1500.0, -0.20, 0.70), what: Part::Bank(A), why: Some(Part::Bank(B)) },
        Stop { shot: s([0.0, 0.0, 30.0], 1950.0, 0.35, 0.95), what: Part::Group(2), why: None },
    ]
}

/// Names for the banks while they act.
pub(super) fn labels(cv: &mut Canvas, cam: &Cam, c: &Clock, r: &Rig) -> Vec<Rect> {
    let mut out = Vec::new();
    let a_new = c.u() >= 5.38;
    out.extend(rig::bank_label(cv, cam, A, if a_new { "bank A: new row" } else { "bank A" }, ORANGE, r.open[A].max(r.pre[A]) * (1.0 - c.during(4, 0.0, 1.0))));
    out.extend(rig::bank_label(cv, cam, B, "bank B", ORANGE, r.open[B] * (1.0 - c.ramp(6, 0.0, 0.2))));
    out.extend(rig::bank_label(cv, cam, E, "5th ACT waits: tFAW", PINK, r.wait[E]));
    out.extend(rig::bank_label(cv, cam, 10, "all banks refreshing", CYAN, r.refresh[10]));
    out
}
