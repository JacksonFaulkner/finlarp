//! The scanner every LITHO scene shares: light source, reticle on its stage, the
//! projection lens, and the resist-coated wafer on the wafer stage with its grid of
//! exposure fields. A `Rig` is the state at one instant; scenes compute it from their
//! clock and call `solids`, `overlay` and `names`.
//!
//! Geometry, schematic units, Y up: the wafer top sits at y = 66, the lens runs from
//! y = 200 to 520, the reticle at y = 640 and the source at y = 820. The reticle's
//! openings run along z, so the printed lines run along z too, and the scan moves
//! the reticle and the wafer along z in opposite directions, the reticle 4x as far.

use super::super::push_box;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, PINK, PURPLE, QUIET, STEEL, TEXT, YELLOW};
use crate::{Cam, Canvas, Col, Tri, V3};

pub(super) const WAFER_Y: f64 = 66.0;
pub(super) const LENS_BOT: f64 = 200.0;
pub(super) const LENS_TOP: f64 = 520.0;
pub(super) const RETICLE_Y: f64 = 640.0;
pub(super) const SOURCE_Y: f64 = 820.0;
pub(super) const WAFER_R: f64 = 300.0;
/// field size and pitch on the wafer
pub(super) const FIELD: f64 = 90.0;
const PITCH: f64 = 100.0;
/// reticle openings (x centres) and their width; the lens prints them 4x smaller
pub(super) const OPENINGS: [f64; 5] = [-120.0, -60.0, 0.0, 60.0, 120.0];
pub(super) const OPEN_W: f64 = 30.0;
pub(super) const REDUCTION: f64 = 4.0;
const RET_HALF_X: f64 = 200.0;
const RET_HALF_Z: f64 = 190.0;
/// alignment sensor, beside the lens
pub(super) const SENSOR: V3 = [265.0, 300.0, 0.0];
/// the alignment marks sit on the wafer at these offsets from its centre
pub(super) const MARKS: [[f64; 2]; 2] = [[-240.0, 0.0], [240.0, 0.0]];

pub(super) const RESIST: Col = [0.40, 0.30, 0.60];
pub(super) const FILM: Col = [0.22, 0.52, 0.62];
pub(super) const QUARTZ: Col = [0.50, 0.62, 0.74];
pub(super) const CHROME: Col = [0.26, 0.27, 0.31];
pub(super) const LIGHT: Col = YELLOW;

/// The fields on the wafer, in the order the stage visits them: rows along z, each
/// row walked the opposite way to the last.
pub(super) fn fields() -> Vec<[f64; 2]> {
    let mut out = Vec::new();
    for (row, j) in (-2i32..=2).enumerate() {
        let mut cols: Vec<i32> = (-2..=2).filter(|i| i * i + j * j <= 5).collect();
        if row % 2 == 1 {
            cols.reverse();
        }
        out.extend(cols.into_iter().map(|i| [i as f64 * PITCH, j as f64 * PITCH]));
    }
    out
}

pub(super) const N_FIELDS: usize = 21;

/// The parts a spotlight or a note can pick out.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum Part {
    Source,
    Reticle,
    Lens,
    Resist,
    Stage,
    Sensor,
    Slit,
}

/// The scanner at one instant.
#[derive(Clone, Copy, Debug)]
pub(super) struct Rig {
    /// light from the source down to the reticle, 0..1
    pub light: f64,
    /// light on through the lens to the wafer, 0..1
    pub project: f64,
    /// reticle scan offset along z
    pub reticle_z: f64,
    /// wafer (and stage top) offset in x and z
    pub wafer: [f64; 2],
    /// how much of each field is exposed (0..1), and the way its scan ran (+1 or -1)
    pub exposed: [(f64, f64); N_FIELDS],
    /// exposed resist dissolved, 0..1
    pub develop: f64,
    /// alignment beam strength, 0..1
    pub align: f64,
    /// how much each part keeps its colour (1) or goes grey (0): source, reticle,
    /// lens, resist, stage, sensor
    pub colour: [f64; 6],
    /// particle clock
    pub u: f64,
}

impl Default for Rig {
    fn default() -> Self {
        Rig {
            light: 0.0,
            project: 0.0,
            reticle_z: 0.0,
            wafer: [0.0, 0.0],
            exposed: [(0.0, 1.0); N_FIELDS],
            develop: 0.0,
            align: 0.0,
            colour: [1.0; 6],
            u: 0.0,
        }
    }
}

/// Where the stage and reticle are at walk position `p` (0..N_FIELDS): field
/// `floor(p)` is being reached (first 30%) or scanned (the rest). Scans alternate
/// direction, so the reticle never has to fly back between fields. Starts from the
/// parked position (wafer centred, reticle centred).
pub(super) fn walk(r: &mut Rig, p: f64) {
    let fs = fields();
    let p = p.clamp(0.0, N_FIELDS as f64);
    let k = (p.floor() as usize).min(N_FIELDS - 1);
    let f = p - k as f64;
    let dir = |i: usize| if i % 2 == 0 { 1.0 } else { -1.0 };
    let start = |i: usize| [-fs[i][0], dir(i) * FIELD / 2.0 - fs[i][1]];
    let end = |i: usize| [-fs[i][0], -dir(i) * FIELD / 2.0 - fs[i][1]];
    let reach = stage::smooth_step(0.0, 0.3, f);
    let s = stage::smooth_step(0.3, 1.0, f);
    let (from, ret_from) = if k == 0 { ([0.0, 0.0], 0.0) } else { (end(k - 1), -dir(k) * 180.0) };
    let to = start(k);
    let w = [from[0] + (to[0] - from[0]) * reach, from[1] + (to[1] - from[1]) * reach];
    let e = end(k);
    r.wafer = [w[0] + (e[0] - w[0]) * s, w[1] + (e[1] - w[1]) * s];
    let ret_start = -dir(k) * 180.0;
    r.reticle_z = ret_from + (ret_start - ret_from) * reach + dir(k) * 360.0 * s;
    for (i, ex) in r.exposed.iter_mut().enumerate() {
        *ex = (if i < k { 1.0 } else if i == k { s } else { 0.0 }, dir(i));
    }
}

/// Where the walk leaves the stage once every field is done.
pub(super) fn walk_end() -> ([f64; 2], f64) {
    let mut r = Rig::default();
    walk(&mut r, N_FIELDS as f64);
    (r.wafer, r.reticle_z)
}

fn tint(r: &Rig, i: usize, col: Col) -> Col {
    stage::mix(QUIET, col, r.colour[i])
}

/// Lens elements: height and radius.
const ELEMENTS: [(f64, f64); 5] = [(230.0, 120.0), (295.0, 145.0), (360.0, 155.0), (425.0, 145.0), (490.0, 120.0)];

pub(super) fn solids(r: &Rig, m: &mut Vec<Tri>) {
    let [wx, wz] = r.wafer;
    // stage: fixed base, moving top carrying the wafer
    push_box(m, [-560.0, -40.0, -520.0], [560.0, 0.0, 520.0], STEEL, NO_GLOW);
    let top = tint(r, 4, [0.48, 0.50, 0.56]);
    push_box(m, [wx - 350.0, 0.0, wz - 350.0], [wx + 350.0, 44.0, wz + 350.0], top, stage::scaled(top, 0.04));
    crate::push_tube(m, [wx, 44.0, wz], [wx, 58.0, wz], WAFER_R, 72, [0.62, 0.64, 0.68], NO_GLOW, true);
    let resist = tint(r, 3, RESIST);
    crate::push_tube(m, [wx, 58.0, wz], [wx, WAFER_Y - 2.0, wz], WAFER_R - 3.0, 72, stage::scaled(resist, 0.8), NO_GLOW, true);
    // fields: resist squares with the printed lines on them
    let half = FIELD / 2.0;
    for (i, c) in fields().iter().enumerate() {
        let (cx, cz) = (c[0] + wx, c[1] + wz);
        push_box(m, [cx - half, WAFER_Y - 2.0, cz - half], [cx + half, WAFER_Y, cz + half], resist, NO_GLOW);
        let (e, dir) = r.exposed[i];
        if e <= 0.002 {
            continue;
        }
        let latent = stage::mix(resist, PINK, (e * 6.0).min(1.0));
        let col = stage::mix(latent, FILM, r.develop);
        let glow = stage::scaled(PINK, 0.35 * (1.0 - r.develop) * r.colour[3]);
        let (z0, z1) = if dir > 0.0 { (cz - half, cz - half + FIELD * e) } else { (cz + half - FIELD * e, cz + half) };
        for ox in OPENINGS {
            let x = cx + ox / REDUCTION;
            let hw = OPEN_W / REDUCTION / 2.0;
            push_box(m, [x - hw, WAFER_Y, z0], [x + hw, WAFER_Y + 1.5, z1], col, glow);
        }
    }

    // lens elements in their barrel
    let lens = tint(r, 2, stage::mix(STEEL, CYAN, 0.55));
    let glow = stage::scaled(CYAN, 0.12 * r.project * r.colour[2]);
    for (y, rad) in ELEMENTS {
        crate::push_tube(m, [0.0, y - 7.0, 0.0], [0.0, y + 7.0, 0.0], rad, 48, lens, glow, true);
    }
    for y in [LENS_BOT - 10.0, LENS_TOP + 10.0] {
        crate::push_tube(m, [0.0, y - 8.0, 0.0], [0.0, y + 8.0, 0.0], 172.0, 48, tint(r, 2, METAL), NO_GLOW, false);
    }

    // reticle: quartz plate, chrome between the openings, on two rails
    for x in [-RET_HALF_X - 30.0, RET_HALF_X + 30.0] {
        push_box(m, [x - 14.0, RETICLE_Y - 14.0, -330.0], [x + 14.0, RETICLE_Y + 2.0, 330.0], STEEL, NO_GLOW);
    }
    let rz = r.reticle_z;
    let (z0, z1) = (rz - RET_HALF_Z, rz + RET_HALF_Z);
    push_box(m, [-RET_HALF_X, RETICLE_Y - 4.0, z0], [RET_HALF_X, RETICLE_Y + 4.0, z1], tint(r, 1, QUARTZ), NO_GLOW);
    let chrome = tint(r, 1, CHROME);
    let mut x0 = -RET_HALF_X;
    for ox in OPENINGS {
        push_box(m, [x0, RETICLE_Y + 4.0, z0], [ox - OPEN_W / 2.0, RETICLE_Y + 8.0, z1], chrome, NO_GLOW);
        x0 = ox + OPEN_W / 2.0;
    }
    push_box(m, [x0, RETICLE_Y + 4.0, z0], [RET_HALF_X, RETICLE_Y + 8.0, z1], chrome, NO_GLOW);

    // source
    let src = tint(r, 0, stage::mix(METAL, YELLOW, 0.25 + 0.6 * r.light));
    push_box(m, [-90.0, SOURCE_Y, -70.0], [90.0, SOURCE_Y + 80.0, 70.0], src, stage::scaled(YELLOW, 0.35 * r.light * r.colour[0]));

    // alignment sensor
    let [sx, sy, sz] = SENSOR;
    let sen = tint(r, 5, stage::mix(METAL, GREEN, 0.35 + 0.5 * r.align));
    push_box(m, [sx - 30.0, sy - 22.0, sz - 30.0], [sx + 40.0, sy + 22.0, sz + 30.0], sen, stage::scaled(GREEN, 0.25 * r.align));
}

/// Where light from opening `ox` lands on the wafer (world).
pub(super) fn image_x(ox: f64) -> f64 {
    ox / REDUCTION
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, r: &Rig) {
    stage::glass_cyl(cv, cam, [0.0, LENS_BOT - 10.0, 0.0], 172.0, LENS_TOP - LENS_BOT + 20.0, GLASS, 0.16);
    // the illuminator's cone from the source to the slit on the reticle
    let la = (0.10 + 0.25 * r.light) as f32;
    for (x, z) in [(-90.0, -70.0), (90.0, -70.0), (90.0, 70.0), (-90.0, 70.0)] {
        cv.line(cam, [x, SOURCE_Y, z], [x * 1.6, RETICLE_Y + 10.0, z * 0.2], LIGHT, la);
    }
    let u = r.u;
    for (i, ox) in OPENINGS.iter().enumerate() {
        let ph = i as f64 * 0.17;
        let down = [[ox * 0.4, SOURCE_Y, 0.0], [*ox, RETICLE_Y + 10.0, 0.0]];
        particles(cv, cam, &down, 4, u * 1.4 + ph, 7.0, LIGHT, r.light);
        let through = [
            [*ox, RETICLE_Y - 6.0, 0.0],
            [ox * 0.75, LENS_TOP, 0.0],
            [ox * 0.45, LENS_BOT, 0.0],
            [image_x(*ox), WAFER_Y + 2.0, 0.0],
        ];
        particles(cv, cam, &through, 6, u * 1.4 + ph, 6.0, LIGHT, r.light * r.project);
    }
    // the exposure slit on the wafer: long in x, narrow in z
    let a = (0.85 * r.project) as f32;
    if a > 0.01 {
        let (hx, hz, y) = (FIELD / 2.0 + 6.0, 9.0, WAFER_Y + 2.5);
        let c = [[-hx, y, -hz], [hx, y, -hz], [hx, y, hz], [-hx, y, hz]];
        for k in 0..4 {
            cv.line(cam, c[k], c[(k + 1) % 4], PINK, a);
        }
        cv.line(cam, [-hx, y, 0.0], [hx, y, 0.0], LIGHT, a);
    }
    // alignment: marks on the wafer, the sensor's beam reading them
    let [wx, wz] = r.wafer;
    let ma = (0.35 + 0.6 * r.align) as f32;
    for mk in MARKS {
        let (x, z, y) = (wx + mk[0], wz + mk[1], WAFER_Y + 1.0);
        cv.line(cam, [x - 14.0, y, z], [x + 14.0, y, z], GREEN, ma);
        cv.line(cam, [x, y, z - 14.0], [x, y, z + 14.0], GREEN, ma);
    }
    let mk = MARKS[1];
    let beam = [[SENSOR[0] - 20.0, SENSOR[1] - 22.0, 0.0], [wx + mk[0], WAFER_Y + 2.0, wz + mk[1]]];
    particles(cv, cam, &beam, 6, u * 1.8, 6.0, GREEN, r.align);
}

/// A part's point, for labels, notes and leaders.
pub(super) fn at(p: Part, r: &Rig) -> V3 {
    let [wx, wz] = r.wafer;
    match p {
        Part::Source => [90.0, SOURCE_Y + 60.0, 70.0],
        Part::Reticle => [RET_HALF_X, RETICLE_Y + 6.0, r.reticle_z + RET_HALF_Z * 0.6],
        Part::Lens => [-155.0, 360.0, 0.0],
        Part::Resist => [wx + WAFER_R * 0.75, WAFER_Y, wz + WAFER_R * 0.55],
        Part::Stage => [wx + 350.0, 22.0, wz + 350.0],
        Part::Sensor => [SENSOR[0] + 40.0, SENSOR[1], SENSOR[2] + 30.0],
        Part::Slit => [FIELD / 2.0 + 6.0, WAFER_Y + 2.0, 0.0],
    }
}

/// The parts, named on the picture. A part is brightest while it is acting.
pub(super) fn names(cv: &mut Canvas, cam: &Cam, r: &Rig) -> Vec<Rect> {
    let lit = |x: f64| 0.62 + 0.38 * x.clamp(0.0, 1.0);
    let k = |i: usize| r.colour[i];
    let mut out = Vec::new();
    out.extend(label(cv, cam, at(Part::Source, r), (0.06, -0.04), "light source", LIGHT, lit(r.light) * k(0)));
    out.extend(label(cv, cam, at(Part::Reticle, r), (0.06, -0.05), "reticle (mask)", TEXT, lit(r.light) * k(1)));
    out.extend(label(cv, cam, at(Part::Lens, r), (-0.17, 0.02), "projection lens", CYAN, lit(r.project) * k(2)));
    out.extend(label(cv, cam, at(Part::Resist, r), (0.05, 0.06), "resist on the wafer", PURPLE, lit(r.develop + r.project) * k(3)));
    out.extend(label(cv, cam, at(Part::Stage, r), (0.04, 0.08), "wafer stage", TEXT, 0.75 * k(4)));
    out.extend(label(cv, cam, at(Part::Sensor, r), (0.06, -0.03), "alignment sensor", GREEN, lit(r.align) * k(5)));
    out.extend(label(cv, cam, at(Part::Slit, r), (0.08, -0.07), "exposure slit", PINK, r.project * r.light));
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn there_are_n_fields_on_the_wafer() {
        let f = fields();
        assert_eq!(f.len(), N_FIELDS);
        for c in &f {
            let far = (c[0].abs() + FIELD / 2.0).hypot(c[1].abs() + FIELD / 2.0);
            assert!(far <= WAFER_R + 1.0, "field {c:?} hangs off the wafer");
        }
    }

    #[test]
    fn the_walk_is_continuous() {
        let mut prev = Rig::default();
        walk(&mut prev, 0.0);
        let mut p = 0.0;
        while p < N_FIELDS as f64 {
            p += 0.002;
            let mut r = Rig::default();
            walk(&mut r, p);
            let d = (r.wafer[0] - prev.wafer[0]).abs() + (r.wafer[1] - prev.wafer[1]).abs();
            assert!(d < 6.0, "wafer jumps by {d} at {p}");
            assert!((r.reticle_z - prev.reticle_z).abs() < 12.0, "reticle jumps at {p}");
            prev = r;
        }
        assert!(prev.exposed.iter().all(|e| e.0 > 0.999));
    }
}
