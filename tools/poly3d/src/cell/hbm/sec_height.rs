//! Section 5: height and heat. The stack grows from 8 to 12 to 16 dies; a plane marks
//! the height limit (raised from 720 to 775 um for 16-high HBM4); the taller the stack,
//! the further heat from the lower dies has to travel to leave the top.

use super::super::stage::{self, label, text, Clock, Shot, GLASS, PINK, TEXT};
use super::rig::{self, top_y, Rig, BASE_Y, FOCUS};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let f = |y: f64| [FOCUS[0], y, FOCUS[1]];
    let keys = [
        Shot { target: f(110.0), dist: 800.0, yaw: 0.55, pitch: 0.25 },
        Shot { target: f(140.0), dist: 850.0, yaw: 0.45, pitch: 0.22 },
        Shot { target: f(170.0), dist: 950.0, yaw: 0.35, pitch: 0.22 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.dies = 8.0 + 4.0 * c.ramp(1, 0.1, 0.6) + 4.0 * c.ramp(2, 0.1, 0.5) - 8.0 * c.ramp(2, 0.86, 0.99);
    r.heat = c.during(2, 0.3, 0.95) + 0.4 * c.during(1, 0.3, 1.0);
    r.heat = r.heat.min(1.0);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    // the limit plane, scaled so a 16-high stack just fits under 775 um
    let sixteen = Rig { dies: 16.0, ..Rig::default() };
    let full = top_y(&sixteen) - BASE_Y;
    let um = c.ramp(2, 0.1, 0.5) * (1.0 - c.ramp(2, 0.86, 0.99));
    let lim = 720.0 + 55.0 * um;
    let y = BASE_Y + full * lim / 770.0;
    let [x, z] = FOCUS;
    stage::glass_box(cv, cam, [x - 110.0, y, z - 90.0], [x + 110.0, y, z + 90.0], PINK, 0.7);
    label(cv, cam, [x + 110.0, y, z + 90.0], (0.03, -0.04), &format!("height limit {lim:.0} um"), PINK, 0.9);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "taller stacks: more capacity, more height, more heat", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "limit raised 720 -> 775 um for 16-high (press reports)", GLASS, 0.8);
}
