//! The LITHO overview: one layer through the scanner, seven beats. The wafer is
//! aligned, the source lights the reticle, the lens projects the image 4x smaller,
//! the slit scans one field, the stage steps across the wafer, develop leaves the
//! pattern, and the wafer leaves for etch while fresh resist comes back for the next
//! layer, so the loop closes without a cut.

use super::rig::{self, Part, Rig, N_FIELDS};
use super::super::stage::{self, Clock, Shot};

pub(super) const BEATS: usize = 7;
pub(super) const ALIGN: usize = 0;
pub(super) const LIGHT: usize = 1;
pub(super) const PROJECT: usize = 2;
pub(super) const SCAN: usize = 3;
pub(super) const STEP: usize = 4;
pub(super) const DEVELOP: usize = 5;
pub(super) const NEXT: usize = 6;

/// The scanner's state at `c`. Every level is built from ramps, so beats join up.
pub(super) fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let off = 1.0 - c.ramp(STEP, 0.85, 1.0);
    r.light = c.ramp(LIGHT, 0.05, 0.35) * off;
    r.project = c.ramp(PROJECT, 0.05, 0.45) * off;
    r.align = c.during(ALIGN, 0.15, 0.95);
    // the walk: field 0 during the scan beat, the other twenty during the step beat
    let p = if c.beat < SCAN {
        0.0
    } else if c.beat == SCAN {
        c.local
    } else if c.beat == STEP {
        1.0 + (N_FIELDS as f64 - 1.0) * stage::smooth_step(0.0, 0.85, c.local)
    } else {
        N_FIELDS as f64
    };
    rig::walk(&mut r, p);
    if c.beat > STEP {
        // the stage parks again for develop
        let (w, rz) = rig::walk_end();
        let k = c.ramp(DEVELOP, 0.0, 0.35);
        r.wafer = [w[0] * (1.0 - k), w[1] * (1.0 - k)];
        r.reticle_z = rz * (1.0 - k);
    }
    // develop, then strip back to fresh resist for the next layer
    let fresh = c.ramp(NEXT, 0.15, 0.85);
    r.develop = c.ramp(DEVELOP, 0.35, 0.9) * (1.0 - fresh);
    for e in r.exposed.iter_mut() {
        e.0 *= 1.0 - fresh;
    }
    r
}

/// One overview beat: the camera and the parts its notes point at.
pub(super) struct Stop {
    pub shot: Shot,
    pub what: Part,
    pub why: Option<Part>,
}

pub(super) fn stops() -> [Stop; BEATS] {
    let s = |target: [f64; 3], dist: f64, yaw: f64, pitch: f64| Shot { target, dist, yaw, pitch };
    [
        Stop { shot: s([60.0, 300.0, 0.0], 2300.0, 0.55, 0.28), what: Part::Sensor, why: Some(Part::Resist) },
        Stop { shot: s([0.0, 640.0, 0.0], 1500.0, 0.40, 0.24), what: Part::Reticle, why: Some(Part::Source) },
        Stop { shot: s([0.0, 370.0, 0.0], 1750.0, 0.60, 0.16), what: Part::Lens, why: Some(Part::Slit) },
        Stop { shot: s([0.0, 330.0, 0.0], 2000.0, 0.85, 0.30), what: Part::Slit, why: Some(Part::Reticle) },
        Stop { shot: s([60.0, 60.0, 170.0], 1650.0, 0.45, 0.55), what: Part::Stage, why: Some(Part::Resist) },
        Stop { shot: s([60.0, 66.0, 200.0], 1250.0, 0.30, 0.62), what: Part::Resist, why: None },
        Stop { shot: s([60.0, 340.0, 0.0], 2300.0, 0.50, 0.28), what: Part::Resist, why: Some(Part::Sensor) },
    ]
}
