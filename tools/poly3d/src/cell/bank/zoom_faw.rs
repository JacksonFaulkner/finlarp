//! Zoom c: the four-activate window. ACTIVATEs to different banks must be tRRD apart,
//! and no more than four may fall in any tFAW window. Four ACTs go out; the fifth,
//! wanted early, has to wait until the window that began with the first one closes.
//! DDR4-3200 module values: tRRD_S about 3.7 ns, tFAW about 21 ns (SPD).

use super::super::stage::{text, Clock, Shot, GLASS, ORANGE, PINK, TEXT};
use super::timeline::{self, Block};
use crate::{Cam, Canvas, Tri};

const RRD: f64 = 3.7;
const FAW: f64 = 21.0;
const SPAN: f64 = 24.0;
const LANES: [&str; 3] = ["ACT commands", "tFAW window", "5th ACT wanted"];

fn blocks() -> Vec<Block> {
    let mut v = Vec::new();
    let names = ["ACT 1", "ACT 2", "ACT 3", "ACT 4"];
    for (k, name) in names.iter().enumerate() {
        v.push(Block { lane: 0, t0: k as f64 * RRD, len: 1.2, col: ORANGE, name, beat: 0 });
    }
    v.push(Block { lane: 1, t0: 0.0, len: FAW, col: PINK, name: "tFAW 21 ns", beat: 1 });
    v.push(Block { lane: 2, t0: 4.0 * RRD, len: 1.2, col: PINK, name: "wanted", beat: 2 });
    v.push(Block { lane: 0, t0: FAW, len: 1.2, col: ORANGE, name: "ACT 5", beat: 2 });
    v
}

pub(super) fn shot(c: &Clock) -> Shot {
    timeline::shot(c, SPAN, LANES.len())
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    timeline::solids(c, &blocks(), LANES.len(), SPAN, 2, m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    timeline::overlay(cv, cam, c, &blocks(), &LANES, SPAN, 3.0, 2);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "ACT to ACT: tRRD 3.7 ns; at most 4 per tFAW 21 ns", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "DDR4-3200 module values (SPD)", GLASS, 0.8);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "the window caps activation current", PINK, c.during(2, 0.3, 1.0));
}
