//! Zoom b: bank groups. READs to banks in the same group must be tCCD_L apart; READs
//! that alternate between groups only tCCD_S, which is the length of one burst, so
//! the data bus stays full. The gaps of the same-group case are idle bus time.
//! DDR4-3200: a burst of 8 is 4 clocks = 2.5 ns; tCCD_L about 5.36 ns (module SPD).

use super::super::stage::{text, Clock, Shot, CYAN, GLASS, GREEN, ORANGE, PINK, TEXT};
use super::timeline::{self, Block};
use crate::{Cam, Canvas, Tri};

const BURST: f64 = 2.5;
const CCD_L: f64 = 5.355;
const SPAN: f64 = 18.0;
const LANES: [&str; 3] = ["same group", "idle bus", "other group"];

fn blocks() -> Vec<Block> {
    let mut v = Vec::new();
    let names = ["RD", "RD", "RD", "RD"];
    for (k, name) in names.iter().enumerate() {
        let t0 = k as f64 * CCD_L;
        v.push(Block { lane: 0, t0, len: BURST, col: ORANGE, name, beat: 0 });
        if k < 3 {
            v.push(Block { lane: 1, t0: t0 + BURST, len: CCD_L - BURST, col: PINK, name: "gap", beat: 2 });
        }
    }
    for k in 0..7 {
        let col = if k % 2 == 0 { GREEN } else { CYAN };
        let name = if k % 2 == 0 { "BG0" } else { "BG1" };
        v.push(Block { lane: 2, t0: k as f64 * BURST, len: BURST, col, name, beat: 1 });
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
    timeline::overlay(cv, cam, c, &blocks(), &LANES, SPAN, BURST, 2);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "same group: tCCD_L 5.36 ns; other group: tCCD_S 2.5 ns", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "one DDR4-3200 burst = 4 clocks = 2.5 ns", GLASS, 0.8);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "alternate groups and the bus never idles", GREEN, c.during(2, 0.3, 1.0));
}
