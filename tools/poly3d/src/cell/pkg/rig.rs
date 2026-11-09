//! The package every Packaging-tab scene shares: server board, BGA balls, organic
//! substrate, C4 bumps, silicon (or RDL) interposer, microbumps, the logic die (one,
//! or two chiplets) and up to eight HBM stacks, with a lid and a cold plate on top.
//! Every quantity is a float so scenes blend without cuts.
//!
//! Geometry, schematic units (not to scale), Y up: board top at y = 0, substrate
//! 20..60, interposer 72..84, dies from 90. `explode` lifts each level apart.

use super::super::push_box;
use super::super::push_sphere;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, TEXT, YELLOW};
use crate::{Cam, Canvas, Col, Tri, V3};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PkgPart {
    Board,
    Bga,
    Substrate,
    C4,
    Interposer,
    Bridge,
    Ubump,
    Logic,
    Hbm,
    Lid,
    Cooler,
    Underfill,
    Reticle,
}

pub const PKG_PARTS: usize = 13;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PkgState {
    /// HBM stacks shown, 0..8
    pub stacks: f64,
    /// DRAM dies per stack, 4..16
    pub dies: f64,
    /// logic die split into two chiplets with a gap, 0..1
    pub split: f64,
    /// logic die size factor (1 = about one reticle)
    pub die: f64,
    /// interposer present, 0..1
    pub interposer: f64,
    /// interposer kind: 0 silicon (CoWoS-S), 1 organic RDL with silicon bridges (CoWoS-L)
    pub bridges: f64,
    /// interposer size factor
    pub isize: f64,
    /// substrate present, 0..1, and build-up layers shown in section, 0..1
    pub substrate: f64,
    pub layers: f64,
    /// board and BGA balls, 0..1
    pub board: f64,
    /// bump rows shown: microbumps, C4, BGA, 0..1
    pub ubump: f64,
    pub c4: f64,
    pub bga: f64,
    /// hybrid bonding instead of microbumps, 0..1
    pub hybrid: f64,
    /// levels pulled apart, 0..1
    pub explode: f64,
    /// underfill between die and interposer and interposer and substrate, 0..1
    pub underfill: f64,
    /// lid and cold plate, 0..1
    pub lid: f64,
    pub cooler: f64,
    /// data between HBM and logic, power up from the board, heat off the top, 0..1
    pub data: f64,
    pub power: f64,
    pub heat: f64,
    /// a reticle-size outline drawn over the logic die, 0..1
    pub reticle: f64,
    /// substrate warpage, 0..1
    pub warp: f64,
    /// front half cut away, 0..1
    pub cut: f64,
    /// packages in a row on a carrier (assembly), 1..4
    pub count: f64,
    pub dim: f64,
    pub hi: [f64; PKG_PARTS],
}

impl PkgState {
    /// A finished CoWoS-S package with four stacks, assembled, on its board.
    pub const BASE: PkgState = PkgState {
        stacks: 4.0,
        dies: 8.0,
        split: 0.0,
        die: 1.0,
        interposer: 1.0,
        bridges: 0.0,
        isize: 1.0,
        substrate: 1.0,
        layers: 0.0,
        board: 1.0,
        ubump: 0.0,
        c4: 0.0,
        bga: 1.0,
        hybrid: 0.0,
        explode: 0.0,
        underfill: 0.0,
        lid: 0.0,
        cooler: 0.0,
        data: 0.0,
        power: 0.0,
        heat: 0.0,
        reticle: 0.0,
        warp: 0.0,
        cut: 0.0,
        count: 1.0,
        dim: 0.0,
        hi: [0.0; PKG_PARTS],
    };

    pub const fn spot(mut self, p: PkgPart) -> PkgState {
        self.dim = 0.85;
        self.hi[p as usize] = 1.0;
        self
    }

    pub(super) fn lerp(a: &PkgState, b: &PkgState, k: f64) -> PkgState {
        let l = |x: f64, y: f64| x + (y - x) * k;
        let mut hi = [0.0; PKG_PARTS];
        for i in 0..PKG_PARTS {
            hi[i] = l(a.hi[i], b.hi[i]);
        }
        PkgState {
            stacks: l(a.stacks, b.stacks),
            dies: l(a.dies, b.dies),
            split: l(a.split, b.split),
            die: l(a.die, b.die),
            interposer: l(a.interposer, b.interposer),
            bridges: l(a.bridges, b.bridges),
            isize: l(a.isize, b.isize),
            substrate: l(a.substrate, b.substrate),
            layers: l(a.layers, b.layers),
            board: l(a.board, b.board),
            ubump: l(a.ubump, b.ubump),
            c4: l(a.c4, b.c4),
            bga: l(a.bga, b.bga),
            hybrid: l(a.hybrid, b.hybrid),
            explode: l(a.explode, b.explode),
            underfill: l(a.underfill, b.underfill),
            lid: l(a.lid, b.lid),
            cooler: l(a.cooler, b.cooler),
            data: l(a.data, b.data),
            power: l(a.power, b.power),
            heat: l(a.heat, b.heat),
            reticle: l(a.reticle, b.reticle),
            warp: l(a.warp, b.warp),
            cut: l(a.cut, b.cut),
            count: l(a.count, b.count),
            dim: l(a.dim, b.dim),
            hi,
        }
    }
}

const BOARD: Col = [0.16, 0.34, 0.22];
const SUBSTRATE: Col = [0.42, 0.36, 0.22];
const SILICON: Col = [0.55, 0.58, 0.66];
const RDL: Col = [0.48, 0.40, 0.30];
const LOGIC: Col = [0.52, 0.44, 0.78];
const DRAM: Col = [0.78, 0.55, 0.36];
const BASE_DIE: Col = [0.42, 0.62, 0.78];
const SOLDER: Col = [0.80, 0.80, 0.76];
const COPPER: Col = [0.95, 0.62, 0.30];
const UNDERFILL: Col = [0.30, 0.30, 0.36];

pub(super) const PKG_DX: f64 = 1500.0;

fn col(s: &PkgState, p: PkgPart, c: Col) -> Col {
    stage::mix(QUIET, c, (1.0 - s.dim).max(s.hi[p as usize]))
}

fn glow(s: &PkgState, p: PkgPart, c: Col) -> Col {
    stage::scaled(c, 0.3 * s.hi[p as usize] * s.dim)
}

/// Heights of each level, with the explode lift.
pub(super) struct Levels {
    pub sub0: f64,
    pub sub1: f64,
    pub int0: f64,
    pub int1: f64,
    pub die0: f64,
    pub lid0: f64,
}

pub(super) fn levels(s: &PkgState) -> Levels {
    let e = s.explode;
    let sub0 = 20.0 + 40.0 * e;
    let sub1 = sub0 + 40.0 * s.substrate;
    let int0 = sub1 + 12.0 + 70.0 * e;
    let int1 = int0 + 12.0 * s.interposer;
    let die0 = int1 + 6.0 * (1.0 - s.hybrid) + 70.0 * e;
    let lid0 = die0 + 16.0 * s.dies.max(4.0) * 0.6 + 20.0 + 80.0 * e;
    Levels { sub0, sub1, int0, int1, die0, lid0 }
}

/// Logic dies: (x0, x1) spans in x; z half depth.
pub(super) fn logic_spans(s: &PkgState) -> (Vec<(f64, f64)>, f64) {
    let hx = 200.0 * s.die;
    let hz = 240.0 * s.die.sqrt();
    let gap = 14.0 * s.split;
    if s.split < 0.02 {
        (vec![(-hx, hx)], hz)
    } else {
        (vec![(-hx - gap, -gap), (gap, hx + gap)], hz)
    }
}

/// HBM stack centres (x, z) for `n` stacks beside the logic.
pub(super) fn stack_xz(s: &PkgState) -> Vec<(f64, f64, f64)> {
    let (sp, hz) = logic_spans(s);
    let edge = sp.last().map_or(200.0, |x| x.1) + 90.0;
    let n = s.stacks.max(0.0);
    // four stacks sit at the corners; eight run four down each side
    let zs: [f64; 8] = if n > 4.5 { [-0.75, -0.75, 0.75, 0.75, -0.25, -0.25, 0.25, 0.25] } else { [-0.62, -0.62, 0.62, 0.62, 0.0, 0.0, 0.0, 0.0] };
    (0..8)
        .filter_map(|i| {
            let p = (n - i as f64).clamp(0.0, 1.0);
            let sx = if i % 2 == 0 { -1.0 } else { 1.0 };
            (p > 0.01).then_some((sx * edge, zs[i] * hz, p))
        })
        .collect()
}

pub(super) fn interposer_half(s: &PkgState) -> (f64, f64) {
    let (sp, hz) = logic_spans(s);
    let w = sp.last().map_or(200.0, |x| x.1) + 170.0;
    (w * s.isize.max(0.6), (hz + 70.0) * s.isize.max(0.6))
}

fn package(s: &PkgState, m: &mut Vec<Tri>, ox: f64, k: f64) {
    let lv = levels(s);
    let zc = s.cut; // cut keeps z <= front
    let zf = |z1: f64| if zc > 0.01 { z1.min(z1 * (1.0 - zc)) } else { z1 };
    let (ix, iz) = interposer_half(s);
    // substrate, slightly warped
    if s.substrate > 0.01 {
        let sx = ix + 160.0;
        let sz = iz + 160.0;
        let n = 16;
        for i in 0..n {
            let x0 = -sx + 2.0 * sx * i as f64 / n as f64;
            let x1 = x0 + 2.0 * sx / n as f64;
            let xm = (x0 + x1) / 2.0 / sx;
            let bow = -s.warp * 70.0 * xm * xm; // edges curl down
            let c = col(s, PkgPart::Substrate, SUBSTRATE);
            push_box(m, [ox + x0, lv.sub0 + bow, -sz], [ox + x1, lv.sub0 + bow + (lv.sub1 - lv.sub0) * k, zf(sz)], c, glow(s, PkgPart::Substrate, SUBSTRATE));
        }
        // build-up layers shown on the cut face
        if s.layers > 0.01 {
            let nl = (14.0 * s.layers).round() as usize;
            for j in 0..nl {
                let y = lv.sub0 + 3.0 + j as f64 * 2.6;
                push_box(m, [ox - sx, y, zf(sz) - 1.0], [ox + sx, y + 1.0, zf(sz) + 0.5], col(s, PkgPart::Substrate, COPPER), NO_GLOW);
            }
        }
        // BGA balls under the substrate
        if s.bga > 0.01 && s.board > 0.01 {
            let pitch = 100.0;
            let nx = (sx / pitch) as i32;
            let nz = (sz / pitch) as i32;
            for i in -nx..=nx {
                for j in -nz..=nz {
                    let z = j as f64 * pitch;
                    if z > zf(sz) {
                        continue;
                    }
                    let y = (lv.sub0 + 0.0) / 2.0;
                    push_sphere(m, [ox + i as f64 * pitch, y, z], 12.0 * s.bga, 6, col(s, PkgPart::Bga, SOLDER), glow(s, PkgPart::Bga, SOLDER));
                }
            }
        }
    }
    // C4 bumps between substrate and interposer
    if s.c4 > 0.01 && s.interposer > 0.01 {
        let pitch = 60.0;
        for i in -((ix / pitch) as i32)..=((ix / pitch) as i32) {
            for j in -((iz / pitch) as i32)..=((iz / pitch) as i32) {
                let z = j as f64 * pitch;
                if z > zf(iz) {
                    continue;
                }
                push_sphere(m, [ox + i as f64 * pitch, (lv.sub1 + lv.int0) / 2.0, z], 7.0 * s.c4, 6, col(s, PkgPart::C4, SOLDER), glow(s, PkgPart::C4, SOLDER));
            }
        }
    }
    // underfill
    if s.underfill > 0.01 {
        let uc = col(s, PkgPart::Underfill, UNDERFILL);
        push_box(m, [ox - ix - 10.0, lv.sub1, -iz - 10.0], [ox + ix + 10.0, lv.sub1 + (lv.int0 - lv.sub1) * s.underfill, zf(iz + 10.0)], uc, NO_GLOW);
    }
    // interposer: silicon, or organic RDL with silicon bridges under the die edges
    if s.interposer > 0.01 {
        let ic = col(s, PkgPart::Interposer, stage::mix(SILICON, RDL, s.bridges));
        push_box(m, [ox - ix, lv.int0, -iz], [ox + ix, lv.int0 + (lv.int1 - lv.int0) * k, zf(iz)], ic, glow(s, PkgPart::Interposer, SILICON));
        if s.bridges > 0.01 {
            let (sp, hz) = logic_spans(s);
            let mut xs: Vec<f64> = Vec::new();
            for (x, _, _) in stack_xz(s) {
                xs.push(x * 0.82);
            }
            if sp.len() > 1 {
                xs.push(0.0);
            }
            for x in xs {
                push_box(m, [ox + x - 40.0, lv.int1 - 4.0, -hz * 0.5], [ox + x + 40.0, lv.int1 + 1.0, zf(hz * 0.5)], col(s, PkgPart::Bridge, stage::mix(SILICON, CYAN, 0.4)), stage::scaled(CYAN, 0.2 * s.bridges));
            }
        }
    }
    // microbumps (or hybrid bonds): dense grid under each die
    let (sp, hz) = logic_spans(s);
    let stacks = stack_xz(s);
    if s.ubump > 0.01 && s.hybrid < 0.95 {
        let pitch = 24.0;
        let r = 4.0 * s.ubump * (1.0 - s.hybrid);
        let y = (lv.int1 + lv.die0) / 2.0;
        let mut feet: Vec<(f64, f64, f64, f64)> = sp.iter().map(|&(a, b)| (a, b, -hz, hz)).collect();
        for &(x, z, _) in &stacks {
            feet.push((x - 50.0, x + 50.0, z - 38.0, z + 38.0));
        }
        for (x0, x1, z0, z1) in feet {
            let nx = ((x1 - x0) / pitch) as i32;
            let nz = ((z1 - z0) / pitch) as i32;
            for i in 0..nx {
                for j in 0..nz {
                    let z = z0 + (j as f64 + 0.5) * pitch;
                    if z > zf(z1) {
                        continue;
                    }
                    let x = x0 + (i as f64 + 0.5) * pitch;
                    push_box(m, [ox + x - r, y - r, z - r], [ox + x + r, y + r, z + r], col(s, PkgPart::Ubump, SOLDER), glow(s, PkgPart::Ubump, SOLDER));
                }
            }
        }
    }
    // logic die(s)
    let lh = 30.0;
    for (x0, x1) in &sp {
        let lc = col(s, PkgPart::Logic, LOGIC);
        let hot = stage::scaled([1.0, 0.4, 0.2], 0.4 * s.heat);
        push_box(m, [ox + x0, lv.die0, -hz], [ox + x1, lv.die0 + lh * k, zf(hz)], stage::mix(lc, [1.0, 0.45, 0.3], 0.4 * s.heat), [hot[0] + glow(s, PkgPart::Logic, LOGIC)[0], hot[1], hot[2]]);
    }
    // HBM stacks: base die + DRAM dies
    for (x, z, p) in stacks {
        if z - 38.0 > zf(400.0) {
            continue;
        }
        let z1 = zf(z + 38.0).max(z - 38.0 + 1.0);
        push_box(m, [ox + x - 50.0, lv.die0, z - 38.0], [ox + x + 50.0, lv.die0 + 8.0 * p, z1], col(s, PkgPart::Hbm, BASE_DIE), NO_GLOW);
        let n = s.dies.round().max(1.0) as usize;
        for d in 0..n {
            let y = lv.die0 + 9.0 + d as f64 * 6.0 * 0.6 * 1.6;
            push_box(m, [ox + x - 48.0, y, z - 36.0], [ox + x + 48.0, y + 4.5 * p, z1 - 2.0], col(s, PkgPart::Hbm, DRAM), glow(s, PkgPart::Hbm, DRAM));
        }
    }
    // lid and cold plate
    if s.lid > 0.01 {
        let (lx, lz) = (ix + 40.0, iz + 40.0);
        push_box(m, [ox - lx, lv.lid0, -lz], [ox + lx, lv.lid0 + 14.0 * s.lid, zf(lz)], col(s, PkgPart::Lid, [0.78, 0.74, 0.70]), NO_GLOW);
    }
    if s.cooler > 0.01 {
        let (lx, lz) = (ix + 60.0, iz + 60.0);
        let y = lv.lid0 + 20.0 + 60.0 * s.explode;
        push_box(m, [ox - lx, y, -lz], [ox + lx, y + 30.0 * s.cooler, zf(lz)], col(s, PkgPart::Cooler, COPPER), glow(s, PkgPart::Cooler, COPPER));
        for i in 0..10 {
            let fx = -lx + 20.0 + i as f64 * (2.0 * lx - 40.0) / 9.0;
            push_box(m, [ox + fx - 6.0, y + 30.0 * s.cooler, -lz], [ox + fx + 6.0, y + 30.0 * s.cooler + 50.0 * s.cooler, zf(lz)], col(s, PkgPart::Cooler, COPPER), NO_GLOW);
        }
    }
}

fn cells(s: &PkgState) -> Vec<(f64, f64)> {
    let n = s.count.max(1.0);
    (0..n.ceil() as usize).map(|i| ((i as f64 - (n - 1.0) / 2.0) * PKG_DX, (n - i as f64).clamp(0.0, 1.0))).collect()
}

pub(super) fn solids(s: &PkgState, m: &mut Vec<Tri>) {
    if s.board > 0.01 {
        let span = (s.count.max(1.0) - 1.0) * PKG_DX / 2.0 + 1000.0;
        push_box(m, [-span, -30.0, -900.0], [span, -2.0 + 2.0 * s.board, 900.0 * (1.0 - 0.5 * s.cut)], col(s, PkgPart::Board, BOARD), NO_GLOW);
    }
    for (x, k) in cells(s) {
        if k > 0.01 {
            package(s, m, x, k);
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, s: &PkgState, u: f64) {
    let lv = levels(s);
    let (sp, hz) = logic_spans(s);
    for (ox, k) in cells(s) {
        if k < 0.5 {
            continue;
        }
        // data: each stack down into the interposer, across, up into the logic
        for (i, (x, z, _)) in stack_xz(s).iter().enumerate() {
            let edge = if *x < 0.0 { sp[0].0 } else { sp.last().unwrap().1 };
            let path = [[ox + x, lv.die0, *z], [ox + x, lv.int1 - 3.0, *z], [ox + edge, lv.int1 - 3.0, z * 0.8], [ox + edge * 0.7, lv.die0, z * 0.8]];
            particles(cv, cam, &path, 5, u * 2.0 + i as f64 * 0.13, 7.0, CYAN, s.data);
        }
        // die to die across a bridge when split
        if s.split > 0.5 {
            let path = [[ox - 60.0, lv.die0, 0.0], [ox - 10.0, lv.int1 - 2.0, 0.0], [ox + 10.0, lv.int1 - 2.0, 0.0], [ox + 60.0, lv.die0, 0.0]];
            particles(cv, cam, &path, 6, u * 2.4, 8.0, GREEN, s.data);
        }
        // power: up from the board through every level into the logic
        for (j, dx) in [-120.0, 0.0, 120.0].iter().enumerate() {
            let path = [[ox + dx * 1.6, -10.0, 60.0], [ox + dx * 1.3, lv.sub1, 60.0], [ox + dx, lv.int1, 60.0], [ox + dx, lv.die0 + 20.0, 60.0]];
            particles(cv, cam, &path, 4, u * 1.4 + j as f64 * 0.3, 8.0, YELLOW, s.power);
        }
        // heat off the top
        if s.heat > 0.01 {
            for j in 0..6 {
                let x = ox + ((j * 37) % 7) as f64 * 50.0 - 150.0;
                let z = ((j * 53) % 5) as f64 * 70.0 - 140.0;
                particles(cv, cam, &[[x, lv.die0 + 30.0, z], [x * 1.1, lv.lid0 + 240.0, z]], 3, u * 0.8 + j as f64 * 0.17, 9.0, [1.0, 0.45, 0.25], s.heat);
            }
        }
        // the reticle: one exposure field, 26 x 33 mm, drawn over the logic die
        if s.reticle > 0.01 {
            let (rx, rz) = (200.0, 250.0);
            let y = lv.die0 + 32.0;
            let a = (0.9 * s.reticle) as f32;
            let c = [[ox - rx, y, -rz], [ox + rx, y, -rz], [ox + rx, y, rz], [ox - rx, y, rz]];
            for i in 0..4 {
                cv.overlay(cam, c[i], c[(i + 1) % 4], PINK, a);
            }
        }
        let _ = hz;
    }
    let _ = (GLASS, METAL, ORANGE, PURPLE, TEXT);
}

pub fn pkg_part_at(p: PkgPart, s: &PkgState) -> V3 {
    let lv = levels(s);
    let (ix, iz) = interposer_half(s);
    let (sp, hz) = logic_spans(s);
    let front = |z: f64| if s.cut > 0.01 { z * (1.0 - s.cut) } else { z };
    let st = stack_xz(s);
    match p {
        PkgPart::Board => [ix + 300.0, -2.0, front(600.0)],
        PkgPart::Bga => [ix + 100.0, lv.sub0 / 2.0, front(iz + 100.0)],
        PkgPart::Substrate => [ix + 160.0, lv.sub1, front(iz + 160.0)],
        PkgPart::C4 => [ix, (lv.sub1 + lv.int0) / 2.0, front(iz)],
        PkgPart::Interposer => [ix, lv.int1, front(iz)],
        PkgPart::Bridge => [st.last().map_or(250.0, |x| x.0 * 0.82), lv.int1, front(hz * 0.5)],
        PkgPart::Ubump => [sp.last().map_or(200.0, |x| x.1), (lv.int1 + lv.die0) / 2.0, front(hz)],
        PkgPart::Logic => [sp.last().map_or(200.0, |x| x.1) * 0.6, lv.die0 + 30.0, front(hz)],
        PkgPart::Hbm => st.iter().max_by(|a, b| (a.0 + a.1).partial_cmp(&(b.0 + b.1)).unwrap()).map_or([300.0, lv.die0 + 40.0, 200.0], |x| [x.0 + 50.0, lv.die0 + 40.0, front(x.1 + 38.0)]),
        PkgPart::Lid => [ix + 40.0, lv.lid0 + 14.0, front(iz + 40.0)],
        PkgPart::Cooler => [ix + 60.0, lv.lid0 + 80.0 + 60.0 * s.explode, front(iz + 60.0)],
        PkgPart::Underfill => [ix + 10.0, (lv.sub1 + lv.int0) / 2.0, front(iz + 10.0)],
        PkgPart::Reticle => [200.0, lv.die0 + 32.0, 250.0],
    }
}

pub fn pkg_part_col(p: PkgPart) -> Col {
    match p {
        PkgPart::Logic => [0.78, 0.68, 0.98],
        PkgPart::Hbm => ORANGE,
        PkgPart::Interposer => [0.80, 0.84, 0.92],
        PkgPart::Bridge => CYAN,
        PkgPart::Ubump | PkgPart::C4 | PkgPart::Bga => [0.92, 0.92, 0.86],
        PkgPart::Substrate => [0.90, 0.78, 0.50],
        PkgPart::Board => GREEN,
        PkgPart::Cooler => COPPER,
        PkgPart::Reticle => PINK,
        _ => TEXT,
    }
}

pub(super) fn labels(cv: &mut Canvas, cam: &Cam, s: &PkgState, list: &[(PkgPart, &str)], a: f64, out: &mut Vec<Rect>) {
    for (i, (p, t)) in list.iter().enumerate() {
        let at = pkg_part_at(*p, s);
        let left = cam.project(at).is_some_and(|(x, _, _)| x < cv.w as f64 * 0.5);
        let w = stage::text_w(&t.to_ascii_uppercase(), stage::text_scale(cv)) as f64 / cv.h as f64;
        let dx = if left { -0.05 - w } else { 0.05 };
        let dy = if i % 2 == 0 { -0.07 } else { 0.06 };
        out.extend(label(cv, cam, at, (dx, dy), t, pkg_part_col(*p), a));
    }
}
