//! Section 4: the timing rules between banks, one lane per beat: tRRD between
//! ACTIVATEs to different banks, tCCD between READs (short across groups, long
//! within one), and tFAW, no more than four ACTIVATEs in its window. DDR4-3200
//! module values from SPD: tRRD_S 3.7, tRRD_L 5.3, tCCD_S 2.5, tCCD_L 5.36, tFAW 21 ns.

use super::super::stage::{text, Clock, Shot, CYAN, GLASS, GREEN, ORANGE, PINK, TEXT};
use super::timeline::{self, Block};
use crate::{Cam, Canvas, Tri};

const SPAN: f64 = 22.0;
const LANES: [&str; 3] = ["ACT, ACT (tRRD)", "RD, RD (tCCD)", "4 ACTs (tFAW)"];

fn blocks() -> Vec<Block> {
    let mut v = vec![
        Block { lane: 0, t0: 0.0, len: 1.0, col: ORANGE, name: "ACT", beat: 0 },
        Block { lane: 0, t0: 3.7, len: 1.0, col: ORANGE, name: "ACT 3.7", beat: 0 },
        Block { lane: 0, t0: 9.0, len: 1.0, col: ORANGE, name: "same group 5.3", beat: 0 },
        Block { lane: 1, t0: 0.0, len: 2.5, col: GREEN, name: "RD", beat: 1 },
        Block { lane: 1, t0: 2.5, len: 2.5, col: CYAN, name: "other BG 2.5", beat: 1 },
        Block { lane: 1, t0: 10.36, len: 2.5, col: GREEN, name: "same BG 5.36", beat: 1 },
        Block { lane: 2, t0: 0.0, len: 21.0, col: PINK, name: "tFAW 21", beat: 2 },
    ];
    for k in 0..4 {
        v.push(Block { lane: 2, t0: k as f64 * 3.7, len: 1.0, col: ORANGE, name: "", beat: 2 });
    }
    v
}

pub(super) fn shot(c: &Clock) -> Shot {
    timeline::shot(c, SPAN, LANES.len())
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    timeline::solids(c, &blocks(), LANES.len(), SPAN, 2, m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    timeline::overlay(cv, cam, c, &blocks(), &LANES, SPAN, 2.0, 2);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "rules between banks (DDR4-3200, ns)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "module SPD values", GLASS, 0.8);
}
