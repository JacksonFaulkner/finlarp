//! Section 5: effective vs peak, as a timeline of one channel's data bus. Peak is a
//! solid bar. Real traffic has holes: the bus turning around between reads and writes,
//! a refresh, and waits for rows to open. Block lengths illustrative.

use super::super::bank::timeline::{self, Block};
use super::super::stage::{text, Clock, Shot, CYAN, GLASS, GREEN, ORANGE, PINK, TEXT};
use crate::{Cam, Canvas, Tri};

const SPAN: f64 = 20.0;
const LANES: [&str; 2] = ["peak", "real traffic"];

fn blocks() -> Vec<Block> {
    vec![
        Block { lane: 0, t0: 0.0, len: SPAN, col: CYAN, name: "every slot full", beat: 0 },
        Block { lane: 1, t0: 0.0, len: 4.0, col: GREEN, name: "reads", beat: 0 },
        Block { lane: 1, t0: 4.0, len: 1.5, col: PINK, name: "turnaround", beat: 1 },
        Block { lane: 1, t0: 5.5, len: 3.0, col: ORANGE, name: "writes", beat: 1 },
        Block { lane: 1, t0: 8.5, len: 1.5, col: PINK, name: "", beat: 1 },
        Block { lane: 1, t0: 10.0, len: 2.5, col: GREEN, name: "", beat: 2 },
        Block { lane: 1, t0: 12.5, len: 3.5, col: PINK, name: "refresh", beat: 2 },
        Block { lane: 1, t0: 16.0, len: 1.5, col: PINK, name: "row miss", beat: 2 },
        Block { lane: 1, t0: 17.5, len: 2.5, col: GREEN, name: "", beat: 2 },
    ]
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
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "pink = bus time with no data", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "block lengths illustrative", GLASS, 0.8);
}
