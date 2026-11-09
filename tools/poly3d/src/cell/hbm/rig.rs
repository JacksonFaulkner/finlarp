//! The package every HBM STACK scene shares: a substrate, a silicon interposer on it,
//! a GPU die in the middle and four HBM stacks beside it. The front-right stack is the
//! one the scenes open up: a base logic die and up to 16 DRAM dies, joined by TSVs and
//! microbumps, which can be pulled apart (exploded) to show the joints.
//!
//! Geometry, schematic units, Y up: substrate y = 0..30, interposer 30..40, dies
//! stacked from y = 40. The focus stack sits at x = 330, z = 130.

use super::super::push_box;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT, YELLOW};
use crate::{Cam, Canvas, Col, Tri, V3};

pub(super) const FOCUS: [f64; 2] = [330.0, 130.0];
pub(super) const STACKS: [[f64; 2]; 4] = [[-330.0, -130.0], [-330.0, 130.0], [330.0, -130.0], FOCUS];
const HX: f64 = 70.0;
const HZ: f64 = 55.0;
pub(super) const BASE_Y: f64 = 40.0;
const BASE_T: f64 = 14.0;
pub(super) const DIE_T: f64 = 9.0;
const BUMP_T: f64 = 2.0;
pub(super) const MAX_DIES: usize = 16;
/// TSV columns across the die footprint
pub(super) const TSV: [[f64; 2]; 6] = [[-35.0, -20.0], [0.0, -20.0], [35.0, -20.0], [-35.0, 20.0], [0.0, 20.0], [35.0, 20.0]];

pub(super) const DRAM: Col = [0.78, 0.55, 0.36];
pub(super) const LOGIC: Col = [0.42, 0.62, 0.78];
pub(super) const COPPER: Col = [0.95, 0.62, 0.30];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum Part {
    Stack,
    Base,
    Tsv,
    Bumps,
    Interposer,
    Gpu,
}

#[derive(Clone, Copy, Debug)]
pub(super) struct Rig {
    /// DRAM dies in the focus stack (continuous; 8 = 8-high)
    pub dies: f64,
    /// dies in the other stacks
    pub others: f64,
    /// gap between dies of the focus stack, 0 = bonded, 1 = pulled apart
    pub explode: f64,
    /// a read: data running down the TSVs from die `src` to the base die
    pub tsv: f64,
    pub src: usize,
    /// data running from the stacks across the interposer to the GPU
    pub link: f64,
    /// heat in the stack, 0..1
    pub heat: f64,
    /// microbumps (0) or hybrid bonding (1): bumps shrink and the gaps close
    pub hybrid: f64,
    /// colour kept per part: DRAM dies, base die, TSVs, bumps, interposer, GPU
    pub colour: [f64; 6],
    pub u: f64,
}

impl Default for Rig {
    fn default() -> Self {
        Rig { dies: 8.0, others: 8.0, explode: 0.0, tsv: 0.0, src: 5, link: 0.0, heat: 0.0, hybrid: 0.0, colour: [1.0; 6], u: 0.0 }
    }
}

fn tint(r: &Rig, i: usize, col: Col) -> Col {
    stage::mix(QUIET, col, r.colour[i])
}

/// Bottom of DRAM die `i` (0 = lowest) in the focus stack.
pub(super) fn die_y(r: &Rig, i: usize) -> f64 {
    let gap = BUMP_T * (1.0 - r.hybrid) + 26.0 * r.explode;
    BASE_Y + BASE_T + gap + i as f64 * (DIE_T + gap)
}

/// Top of the focus stack.
pub(super) fn top_y(r: &Rig) -> f64 {
    let n = r.dies.ceil().max(1.0) as usize;
    die_y(r, n - 1) + DIE_T * (r.dies - (n - 1) as f64).clamp(0.0, 1.0)
}

fn stack(m: &mut Vec<Tri>, r: &Rig, c: [f64; 2], dies: f64, focus: bool) {
    let [x, z] = c;
    let base = tint(r, 1, LOGIC);
    push_box(m, [x - HX, BASE_Y, z - HZ], [x + HX, BASE_Y + BASE_T, z + HZ], base, stage::scaled(LOGIC, 0.05));
    for i in 0..MAX_DIES {
        let k = (dies - i as f64).clamp(0.0, 1.0);
        if k < 0.01 {
            continue;
        }
        let y = if focus { die_y(r, i) } else { BASE_Y + BASE_T + BUMP_T + i as f64 * (DIE_T + BUMP_T) };
        let hot = if focus { r.heat * (0.4 + 0.6 * i as f64 / dies.max(1.0)) } else { 0.0 };
        let col = stage::mix(tint(r, 0, DRAM), [1.0, 0.35, 0.2], 0.6 * hot);
        let lit = if focus && r.tsv > 0.01 && i == r.src { 0.35 * r.tsv } else { 0.0 };
        push_box(m, [x - HX * 0.97, y, z - HZ * 0.97], [x + HX * 0.97, y + DIE_T * k, z + HZ * 0.97], col, stage::scaled(stage::mix(DRAM, YELLOW, lit * 2.0), 0.05 + lit + 0.25 * hot));
        if focus {
            // microbumps under the die at each TSV column
            let gap = y - if i == 0 { BASE_Y + BASE_T } else { die_y(r, i - 1) + DIE_T };
            let bump_h = gap.min(4.0);
            if gap > 0.5 && r.hybrid < 0.98 {
                for t in TSV {
                    let s = 5.0 * (1.0 - r.hybrid);
                    push_box(m, [x + t[0] - s, y - bump_h, z + t[1] - s], [x + t[0] + s, y, z + t[1] + s], tint(r, 3, stage::mix(METAL, YELLOW, 0.4)), NO_GLOW);
                }
            }
        }
    }
}

pub(super) fn solids(r: &Rig, m: &mut Vec<Tri>) {
    push_box(m, [-640.0, 0.0, -400.0], [640.0, 30.0, 400.0], [0.14, 0.28, 0.20], NO_GLOW);
    push_box(m, [-470.0, 30.0, -260.0], [470.0, BASE_Y, 260.0], tint(r, 4, stage::mix(STEEL, METAL, 0.6)), NO_GLOW);
    push_box(m, [-170.0, BASE_Y, -200.0], [170.0, BASE_Y + 45.0, 200.0], tint(r, 5, stage::mix(METAL, PURPLE, 0.45)), NO_GLOW);
    for c in STACKS {
        let focus = c == FOCUS;
        stack(m, r, c, if focus { r.dies } else { r.others }, focus);
    }
    // TSVs through the focus stack: copper columns, bright while carrying a read
    let [x, z] = FOCUS;
    let top = top_y(r);
    for t in TSV {
        let col = stage::mix(COPPER, YELLOW, 0.6 * r.tsv);
        crate::push_tube(m, [x + t[0], BASE_Y + BASE_T - 2.0, z + t[1]], [x + t[0], top + 1.0, z + t[1]], 3.0, 8, tint(r, 2, col), stage::scaled(COPPER, 0.15 + 0.3 * r.tsv), false);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, r: &Rig) {
    let u = r.u;
    // interposer wiring from each stack's base die to the GPU's edge
    for c in STACKS {
        let [x, z] = c;
        let gx = if x < 0.0 { -170.0 } else { 170.0 };
        let ex = if x < 0.0 { x + HX } else { x - HX };
        for k in 0..8 {
            let dz = -42.0 + 12.0 * k as f64;
            let (a, b) = ([ex, BASE_Y - 1.0, z + dz], [gx, BASE_Y - 1.0, z * 0.6 + dz]);
            cv.line(cam, a, b, CYAN, (0.15 + 0.3 * r.colour[4]) as f32);
            particles(cv, cam, &[a, b], 3, u * 1.8 + k as f64 * 0.09, 3.0, CYAN, r.link);
        }
    }
    // the read: down the TSVs from the source die to the base die
    let [x, z] = FOCUS;
    let y0 = die_y(r, r.src) + DIE_T / 2.0;
    for t in TSV {
        particles(cv, cam, &[[x + t[0], y0, z + t[1]], [x + t[0], BASE_Y + BASE_T, z + t[1]]], 4, u * 2.2 + t[0] * 0.01, 4.0, YELLOW, r.tsv);
    }
    // heat leaving the top
    if r.heat > 0.01 {
        let top = top_y(r);
        for k in 0..6 {
            let (dx, dz) = (((k * 37) % 7) as f64 * 18.0 - 54.0, ((k * 53) % 5) as f64 * 18.0 - 36.0);
            particles(cv, cam, &[[x + dx, top + 2.0, z + dz], [x + dx * 1.4, top + 160.0, z + dz * 1.4]], 3, u * 0.9 + k as f64 * 0.17, 7.0, [1.0, 0.45, 0.25], r.heat);
        }
    }
    stage::glass_box(cv, cam, [x - HX - 4.0, BASE_Y, z - HZ - 4.0], [x + HX + 4.0, top_y(r) + 2.0, z + HZ + 4.0], GLASS, (0.1 + 0.15 * r.explode) as f32);
}

pub(super) fn at(p: Part, r: &Rig) -> V3 {
    let [x, z] = FOCUS;
    match p {
        Part::Stack => [x + HX, top_y(r), z + HZ],
        Part::Base => [x + HX, BASE_Y + BASE_T / 2.0, z + HZ],
        Part::Tsv => [x + TSV[5][0], top_y(r) + 1.0, z + TSV[5][1]],
        Part::Bumps => [x + TSV[2][0] + 5.0, die_y(r, 3) - 1.0, z + TSV[2][1]],
        Part::Interposer => [470.0, BASE_Y, 260.0],
        Part::Gpu => [0.0, BASE_Y + 45.0, -200.0],
    }
}

pub(super) fn names(cv: &mut Canvas, cam: &Cam, r: &Rig) -> Vec<Rect> {
    let k = |i: usize| r.colour[i];
    let n = r.dies.round() as usize;
    let mut out = Vec::new();
    out.extend(label(cv, cam, at(Part::Stack, r), (0.04, -0.06), &format!("HBM stack: {n} DRAM dies"), ORANGE, 0.9 * k(0)));
    out.extend(label(cv, cam, at(Part::Base, r), (0.05, 0.05), "base logic die", CYAN, 0.85 * k(1)));
    out.extend(label(cv, cam, at(Part::Gpu, r), (-0.02, -0.08), "GPU", PURPLE, 0.85 * k(5)));
    out.extend(label(cv, cam, at(Part::Interposer, r), (0.03, 0.06), "silicon interposer", TEXT, 0.8 * k(4)));
    out.extend(label(cv, cam, at(Part::Tsv, r), (-0.30, -0.02), "TSVs: wires through the dies", stage::mix(COPPER, YELLOW, 0.4), r.explode.max(r.tsv).max(1.0 - r.colour[0].min(1.0)) * k(2)));
    out.extend(label(cv, cam, at(Part::Bumps, r), (0.08, 0.02), "microbumps", YELLOW, r.explode * (1.0 - r.hybrid) * k(3)));
    out
}
