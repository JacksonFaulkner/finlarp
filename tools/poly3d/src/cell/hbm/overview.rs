//! The HBM STACK overview, seven beats: the package (GPU and four HBM stacks on a
//! silicon interposer); one stack, a base logic die under eight DRAM dies; the stack
//! pulled apart to show the microbumps; a read running down the TSVs; data crossing
//! the interposer to the GPU; taller stacks for more capacity; and heat leaving the top,
//! after which the stack settles back to eight dies, closing the loop.

use super::super::stage::{Clock, Shot};
use super::rig::{Part, Rig, FOCUS};

pub(super) const BEATS: usize = 7;

pub(super) fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.explode = c.ramp(2, 0.1, 0.6) * (1.0 - c.ramp(4, 0.0, 0.35));
    r.tsv = c.during(3, 0.1, 0.95);
    r.link = 0.35 * (1.0 - c.during(2, 0.0, 1.0)) * (1.0 - c.during(3, 0.0, 1.0)) + 0.65 * c.during(4, 0.2, 1.0);
    r.dies = 8.0 + 8.0 * c.ramp(5, 0.1, 0.8) * (1.0 - c.ramp(6, 0.6, 0.92));
    r.heat = c.during(6, 0.05, 0.9);
    r
}

pub(super) struct Stop {
    pub shot: Shot,
    pub what: Part,
    pub why: Option<Part>,
}

pub(super) fn stops() -> [Stop; BEATS] {
    let s = |target: [f64; 3], dist: f64, yaw: f64, pitch: f64| Shot { target, dist, yaw, pitch };
    let f = |y: f64| [FOCUS[0], y, FOCUS[1]];
    [
        Stop { shot: s([0.0, 40.0, 0.0], 1700.0, 0.35, 0.65), what: Part::Gpu, why: Some(Part::Interposer) },
        Stop { shot: s(f(100.0), 750.0, 0.55, 0.35), what: Part::Stack, why: Some(Part::Base) },
        Stop { shot: s(f(170.0), 850.0, 0.70, 0.25), what: Part::Bumps, why: Some(Part::Stack) },
        Stop { shot: s(f(170.0), 850.0, 0.35, 0.20), what: Part::Tsv, why: Some(Part::Base) },
        Stop { shot: s([180.0, 60.0, 60.0], 1100.0, 0.45, 0.55), what: Part::Interposer, why: Some(Part::Gpu) },
        Stop { shot: s(f(150.0), 950.0, 0.60, 0.30), what: Part::Stack, why: None },
        Stop { shot: s(f(180.0), 900.0, 0.40, 0.30), what: Part::Stack, why: Some(Part::Base) },
    ]
}
