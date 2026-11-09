//! Section 7: refresh and banks, as timelines. DDR4 all-bank refresh: one long block
//! where no bank can be used. DDR5 same-bank refresh: one bank per group at a time,
//! staggered, while reads to the other banks carry on. Block lengths illustrative.

use super::super::stage::{text, Clock, Shot, CYAN, GLASS, GREEN, PINK, TEXT};
use super::timeline::{self, Block};
use crate::{Cam, Canvas, Tri};

const SPAN: f64 = 20.0;
const LANES: [&str; 4] = ["DDR4 all banks", "DDR5 bank 0 / group", "DDR5 bank 1 / group", "DDR5 reads"];

fn blocks() -> Vec<Block> {
    let mut v = vec![Block { lane: 0, t0: 0.0, len: 14.0, col: PINK, name: "REFab: blocked", beat: 0 }];
    v.push(Block { lane: 1, t0: 0.0, len: 5.0, col: CYAN, name: "REFsb", beat: 1 });
    v.push(Block { lane: 2, t0: 5.0, len: 5.0, col: CYAN, name: "REFsb", beat: 1 });
    for k in 0..7 {
        v.push(Block { lane: 3, t0: k as f64 * 2.6, len: 2.2, col: GREEN, name: if k == 0 { "RD" } else { "" }, beat: 2 });
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
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "refresh: all banks (DDR4) vs one bank per group (DDR5)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "block lengths illustrative", GLASS, 0.8);
}
