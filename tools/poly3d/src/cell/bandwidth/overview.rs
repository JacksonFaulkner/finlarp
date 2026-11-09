//! The BANDWIDTH overview: how a peak bandwidth is built, seven beats. One pin's data
//! rate; a 64-pin channel; four channels; the gaps that keep real traffic below peak;
//! the bus turning around between reads and writes; an HBM stack, very wide and close;
//! and the memory wall: compute has grown far faster than DRAM bandwidth. The system
//! then returns to the one-pin start, closing the loop.

use super::super::stage::{Clock, Shot};
use super::rig::{Part, Rig, CH};

pub(super) const BEATS: usize = 7;

/// Log-space blend from `a` to `b` GB/s.
fn logmix(a: f64, b: f64, k: f64) -> f64 {
    (a.ln() + (b.ln() - a.ln()) * k).exp()
}

pub(super) fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    let back = c.ramp(6, 0.6, 0.92);
    r.chan[0] = 1.0;
    r.width0 = 1.0 / 8.0 + 7.0 / 8.0 * c.ramp(1, 0.1, 0.6) * (1.0 - back);
    for k in 1..CH {
        let a = 0.05 + 0.15 * (k - 1) as f64;
        r.chan[k] = c.ramp(2, a, a + 0.3) * (1.0 - back);
    }
    for k in 0..CH {
        r.flow[k] = 1.0;
    }
    r.gaps = 0.6 * c.during(3, 0.1, 0.95);
    r.dir = 1.0 - 2.0 * c.ramp(4, 0.3, 0.42) + 2.0 * c.ramp(4, 0.75, 0.87);
    r.hbm = c.ramp(5, 0.05, 0.5) * (1.0 - back);
    r.wall = c.ramp(6, 0.05, 0.35) * (1.0 - c.ramp(6, 0.75, 0.95));
    let mut g = 0.4;
    g = logmix(g, 25.6, c.ramp(1, 0.1, 0.6));
    g = logmix(g, 102.4, c.ramp(2, 0.05, 0.65));
    g = logmix(g, 819.2, c.ramp(5, 0.3, 0.8));
    g = logmix(g, 0.4, back);
    r.gbps = g;
    r
}

pub(super) struct Stop {
    pub shot: Shot,
    pub what: Part,
    pub why: Option<Part>,
}

pub(super) fn stops() -> [Stop; BEATS] {
    let s = |target: [f64; 3], dist: f64, yaw: f64, pitch: f64| Shot { target, dist, yaw, pitch };
    [
        Stop { shot: s([-80.0, 10.0, -250.0], 1300.0, 0.25, 0.55), what: Part::Pin, why: Some(Part::Gauge) },
        Stop { shot: s([-80.0, 10.0, -200.0], 1400.0, 0.35, 0.60), what: Part::Channel(0), why: Some(Part::Gauge) },
        Stop { shot: s([-60.0, 10.0, 0.0], 1900.0, 0.30, 0.75), what: Part::Dimm(3), why: Some(Part::Gauge) },
        Stop { shot: s([0.0, 10.0, -40.0], 1700.0, 0.15, 0.80), what: Part::Channel(2), why: Some(Part::Cpu) },
        Stop { shot: s([0.0, 10.0, -60.0], 1600.0, -0.20, 0.65), what: Part::Channel(1), why: Some(Part::Dimm(1)) },
        Stop { shot: s([-260.0, 10.0, 200.0], 1700.0, -0.35, 0.60), what: Part::Hbm, why: Some(Part::Gauge) },
        Stop { shot: s([-420.0, 100.0, -150.0], 1500.0, -0.55, 0.30), what: Part::Gauge, why: None },
    ]
}
