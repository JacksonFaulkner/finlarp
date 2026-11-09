//! The ARRAY overview: one subarray serving an access, seven beats. An address
//! reaches the row decoder; ACTIVATE raises one word line and the whole row shares its
//! charge onto the bit lines; the sense amps latch it (the row buffer); READ sends a
//! burst of columns to the I/O; a second READ to the open row is a row hit; PRECHARGE
//! closes the row; refresh opens and closes every row in turn, ending idle.

use super::super::stage::{Clock, Shot};
use super::rig::{Part, Rig, NC, NR};

pub(super) const BEATS: usize = 7;
const ROW: usize = 2;

/// Refresh in beat 6: row `k`'s window in the beat, word line up then down.
fn refresh(c: &Clock, k: usize) -> f64 {
    let n = NR as f64;
    let (a, b) = (0.05 + 0.9 * k as f64 / n, 0.05 + 0.9 * (k + 1) as f64 / n);
    let w = b - a;
    c.ramp(6, a, a + 0.25 * w) * (1.0 - c.ramp(6, b - 0.25 * w, b))
}

pub(super) fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    r.addr = c.during(0, 0.25, 1.0);
    let close = c.ramp(5, 0.05, 0.4);
    r.wl[ROW] = c.ramp(1, 0.05, 0.35) * (1.0 - close);
    r.share = c.ramp(1, 0.35, 0.9) * (1.0 - c.ramp(5, 0.2, 0.7));
    r.sense = c.ramp(2, 0.05, 0.6) * (1.0 - c.ramp(5, 0.2, 0.7));
    for col in 0..4 {
        r.read[col] = c.during(3, 0.15, 0.95);
    }
    for col in 8..NC {
        r.read[col] = c.during(4, 0.15, 0.95);
    }
    if c.beat == 6 {
        let mut level = 0.0;
        for k in 0..NR {
            let v = refresh(c, k);
            r.wl[k] = v;
            level += v;
        }
        // each refreshed row is sensed and restored while its word line is up
        r.share = level.min(1.0);
        r.sense = level.min(1.0);
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
    [
        Stop { shot: s([-160.0, 40.0, 0.0], 1500.0, -0.55, 0.55), what: Part::Decoder, why: Some(Part::Cells) },
        Stop { shot: s([0.0, 40.0, 40.0], 1700.0, -0.35, 0.60), what: Part::OpenRow, why: Some(Part::BitLine) },
        Stop { shot: s([0.0, 40.0, 180.0], 1500.0, 0.25, 0.55), what: Part::SenseAmps, why: Some(Part::OpenRow) },
        Stop { shot: s([120.0, 30.0, 260.0], 1500.0, 0.55, 0.60), what: Part::ColDecoder, why: Some(Part::Io) },
        Stop { shot: s([140.0, 30.0, 260.0], 1500.0, 0.70, 0.55), what: Part::Io, why: Some(Part::SenseAmps) },
        Stop { shot: s([0.0, 40.0, 60.0], 1800.0, 0.10, 0.70), what: Part::BitLine, why: Some(Part::SenseAmps) },
        Stop { shot: s([-60.0, 40.0, 60.0], 1800.0, -0.30, 0.80), what: Part::OpenRow, why: Some(Part::Decoder) },
    ]
}
