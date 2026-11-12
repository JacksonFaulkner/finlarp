//! Shared pieces for the MELT + PULL close-ups: points along paths, streams of particles,
//! bars, the ground, arcs and the argon route. All built from the primitives in `mesh.rs`.
//! Units are millimetres, Y up, the crystal axis is X = Z = 0.

use crate::math::{self, V3};
use crate::mesh::{hash01, Mat, Mesh};

/// The point a fraction `t` of the way along the polyline `path` (by arc length, wrapping).
pub fn along(path: &[V3], t: f32) -> V3 {
    if path.len() < 2 {
        return path.first().copied().unwrap_or([0.0; 3]);
    }
    let lens: Vec<f32> = path
        .windows(2)
        .map(|w| math::len(math::sub(w[1], w[0])))
        .collect();
    let total: f32 = lens.iter().sum();
    if total <= 0.0 {
        return path[0];
    }
    let mut d = t.rem_euclid(1.0) * total;
    for (i, &l) in lens.iter().enumerate() {
        if d <= l || i + 1 == lens.len() {
            let u = (d / l.max(1e-6)).clamp(0.0, 1.0);
            return math::add(path[i], math::scale(math::sub(path[i + 1], path[i]), u));
        }
        d -= l;
    }
    path[path.len() - 1]
}

/// `n` particles spread evenly along `path` and wrapping at its end, shifted by `phase`
/// (0..1), so a stream moves as `phase` runs. `seed` keeps each particle's shape its own.
pub fn stream(out: &mut Mesh, path: &[V3], n: usize, phase: f32, size: f32, seed: u32, m: &Mat) {
    for k in 0..n {
        let t = phase + k as f32 / n as f32;
        out.shard(
            along(path, t),
            size,
            seed.wrapping_mul(131).wrapping_add(k as u32),
            m,
        );
    }
}

/// `n` particles scattered in a cylinder of radius `r` and height `h`, from height `y0`.
pub fn cloud(out: &mut Mesh, n: usize, y0: f32, r: f32, h: f32, seed: u32, size: f32, m: &Mat) {
    for k in 0..n as u32 {
        let a = std::f32::consts::TAU * hash01(seed + k * 3);
        let rr = r * hash01(seed + k * 3 + 1).sqrt();
        let y = y0 + h * hash01(seed + k * 3 + 2);
        out.shard([rr * a.cos(), y, rr * a.sin()], size, seed + k, m);
    }
}

/// Points on a circle of radius `r` about the Y axis at height `y`, from angle `a0` to `a1`.
pub fn arc(r: f32, y: f32, a0: f32, a1: f32, n: usize) -> Vec<V3> {
    (0..=n)
        .map(|i| {
            let a = a0 + (a1 - a0) * i as f32 / n as f32;
            [r * a.cos(), y, r * a.sin()]
        })
        .collect()
}

/// A straight run of points from `a` to `b`, `n` steps.
pub fn line(a: V3, b: V3, n: usize) -> Vec<V3> {
    (0..=n)
        .map(|i| math::add(a, math::scale(math::sub(b, a), i as f32 / n as f32)))
        .collect()
}

/// A flat ground disc of radius `r` at height `y`.
pub fn ground(out: &mut Mesh, y: f32, r: f32) {
    let m = Mat::new([0.15, 0.16, 0.18], 0.0, 0.85);
    out.disc(r, y, true, 96, &m);
}

/// A vertical bar on the ground plane at (`x`, `z`): width `w`, from height `y0` up `h`.
pub fn bar(out: &mut Mesh, x: f32, z: f32, w: f32, y0: f32, h: f32, m: &Mat) {
    out.cuboid([x, y0 + h * 0.5, z], [w * 0.5, h * 0.5, w * 0.5], m);
}

/// The argon route: in at the top of the pull chamber, down past the crystal, out the base.
pub fn argon_route() -> Vec<V3> {
    vec![
        [-300.0, 1900.0, 0.0],
        [-300.0, 900.0, 0.0],
        [-520.0, 650.0, 0.0],
        [-760.0, 200.0, 0.0],
        [-820.0, -350.0, 0.0],
        [-900.0, -1000.0, 0.0],
        [-1400.0, -1060.0, 0.0],
    ]
}

/// Argon as cool, faint particles, and the SiO and CO that leave with it at the base.
pub const ARGON: Mat = Mat::new([0.8, 0.9, 1.0], 0.0, 0.3).emit([0.55, 0.85, 1.4]);
pub const GAS_CO: Mat = Mat::new([0.9, 0.9, 0.95], 0.0, 0.4).emit([1.2, 1.2, 1.3]);
/// Heat and hot gas: orange, emissive.
pub const HOT: Mat = Mat::new([1.0, 0.5, 0.2], 0.0, 0.3).emit([2.2, 0.9, 0.3]);
/// Magnetic field lines: blue, emissive.
pub const FIELD: Mat = Mat::new([0.3, 0.5, 1.0], 0.0, 0.3).emit([0.4, 0.9, 2.2]);
/// Dislocations: red, emissive.
pub const DISLOC: Mat = Mat::new([0.8, 0.05, 0.05], 0.0, 0.4).emit([2.6, 0.15, 0.1]);
/// Dopant atoms: violet, emissive.
pub const DOPANT: Mat = Mat::new([0.6, 0.3, 0.9], 0.0, 0.3).emit([1.3, 0.5, 2.0]);
/// Silicon atoms: silver, lit from inside when they attach.
pub const ATOM: Mat = Mat::new([0.55, 0.6, 0.66], 0.8, 0.25);
pub const ATOM_LIT: Mat = Mat::new([0.9, 0.95, 1.0], 0.8, 0.2).emit([0.9, 1.0, 1.4]);
/// Quartz glass, as fragments.
pub const QUARTZ: Mat = Mat::new([0.9, 0.92, 0.95], 0.0, 0.1)
    .alpha(0.5)
    .kind(crate::mesh::Kind::Glass);
/// Bright metal for markers and gauges.
pub const METAL: Mat = Mat::new([0.75, 0.76, 0.8], 1.0, 0.3);
