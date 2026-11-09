//! Section 4: resolution. CD = k1 x wavelength / NA, worked for three scanners at the
//! same k1. Each stands as a tile of printed lines, the line width to scale, with a
//! bar behind it as tall as its CD. The camera visits one per beat.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT, YELLOW};
use super::rig::FILM;
use crate::{Cam, Canvas, Tri};

const K1: f64 = 0.4;
/// name, wavelength (nm), NA
pub(super) const SCANNERS: [(&str, f64, f64); 3] = [
    ("DUV ArF immersion", 193.0, 1.35),
    ("EUV", 13.5, 0.33),
    ("High-NA EUV", 13.5, 0.55),
];
const SPACE: f64 = 560.0;
const HALF: f64 = 230.0;
/// world units per nm
const NM: f64 = 2.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn cd(i: usize) -> f64 {
    let (_, wl, na) = SCANNERS[i];
    K1 * wl / na
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i) * 0.55, 120.0, 0.0], dist: 1500.0, yaw: 0.25, pitch: 0.42 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    for i in 0..3 {
        let k = spotlight(c, i, 3);
        let cx = x(i);
        push_box(m, [cx - HALF, -20.0, -HALF], [cx + HALF, 0.0, HALF], STEEL, NO_GLOW);
        let w = cd(i) * NM;
        let n = (HALF / (2.0 * w)).floor() as i32;
        let col = stage::mix(stage::mix(QUIET, FILM, 0.5), stage::mix(FILM, PINK, 0.35), k);
        for j in -n..=n {
            let lx = cx + j as f64 * 2.0 * w;
            push_box(m, [lx - w / 2.0, 0.0, -HALF + 20.0], [lx + w / 2.0, 6.0, HALF - 20.0], col, stage::scaled(PINK, 0.12 * k));
        }
        let bar = stage::mix(QUIET, ORANGE, 0.3 + 0.7 * k);
        push_box(m, [cx - 30.0, 0.0, -HALF - 40.0], [cx + 30.0, cd(i) * 5.0, -HALF + 20.0], bar, stage::scaled(ORANGE, 0.2 * k));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for (i, (name, wl, na)) in SCANNERS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        let cx = x(i);
        label(cv, cam, [cx, 0.0, HALF], (-0.06, 0.07), name, TEXT, 0.5 + 0.5 * k);
        label(cv, cam, [cx, cd(i) * 5.0, -HALF - 10.0], (0.03, -0.06), &format!("CD {:.0} nm", cd(i)), ORANGE, 0.45 + 0.55 * k);
        let (w, h) = (cv.w as f64, cv.h as f64);
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, &format!("{wl} nm / NA {na}"), YELLOW, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "CD = k1 x wavelength / NA", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "same k1 = 0.4 for all three", CYAN, 0.8);
}
