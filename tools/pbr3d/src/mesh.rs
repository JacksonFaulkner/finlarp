//! Triangle meshes for the GPU: every vertex carries its material, so one buffer holds
//! a whole scene and one draw call covers it.

use bytemuck::{Pod, Zeroable};
use std::f32::consts::TAU;

use crate::math::{self, V3};

/// What a surface is made of. `kind` picks the special shading in the shader.
#[derive(Clone, Copy, Debug)]
pub struct Mat {
    pub albedo: [f32; 3],
    pub metal: f32,
    pub rough: f32,
    pub emit: [f32; 3],
    pub alpha: f32,
    pub kind: Kind,
    /// The cutaway removes this surface's half that faces the camera.
    pub cut: bool,
    /// Procedural surface texture: 0 none, see `shaders.wgsl` (`tex_id`).
    pub tex: f32,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Kind {
    Plain = 0,
    Melt = 2,
    Felt = 3,
    Silicon = 4,
    Glass = 5,
    /// Clear glass: transmits nearly all light, adds only a faint Fresnel reflection.
    ClearGlass = 6,
}

impl Mat {
    pub const fn new(albedo: [f32; 3], metal: f32, rough: f32) -> Mat {
        Mat { albedo, metal, rough, emit: [0.0; 3], alpha: 1.0, kind: Kind::Plain, cut: false, tex: 0.0 }
    }
    pub const fn cut(mut self) -> Mat {
        self.cut = true;
        self
    }
    pub const fn emit(mut self, e: [f32; 3]) -> Mat {
        self.emit = e;
        self
    }
    pub const fn kind(mut self, k: Kind) -> Mat {
        self.kind = k;
        self
    }
    pub const fn tex(mut self, t: f32) -> Mat {
        self.tex = t;
        self
    }
    pub const fn alpha(mut self, a: f32) -> Mat {
        self.alpha = a;
        self
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default, Pod, Zeroable)]
pub struct Vertex {
    pub pos: [f32; 4],
    pub nrm: [f32; 4],
    /// rgb albedo, metallic
    pub alb: [f32; 4],
    /// roughness, alpha, kind, cut flag
    pub mat: [f32; 4],
    /// rgb emission
    pub emi: [f32; 4],
}

#[derive(Default, Clone)]
pub struct Mesh {
    pub v: Vec<Vertex>,
    pub i: Vec<u32>,
}

impl Mesh {
    pub fn new() -> Mesh {
        Mesh::default()
    }

    fn vert(&mut self, p: V3, n: V3, m: &Mat) -> u32 {
        let idx = self.v.len() as u32;
        self.v.push(Vertex {
            pos: [p[0], p[1], p[2], 1.0],
            nrm: [n[0], n[1], n[2], 0.0],
            alb: [m.albedo[0], m.albedo[1], m.albedo[2], m.metal],
            mat: [m.rough, m.alpha, m.kind as u32 as f32, if m.cut { 1.0 } else { 0.0 }],
            emi: [m.emit[0], m.emit[1], m.emit[2], m.tex],
        });
        idx
    }

    pub fn tri(&mut self, a: u32, b: u32, c: u32) {
        self.i.extend_from_slice(&[a, b, c]);
    }

    /// A copy with X and Y swapped: a column about +Y becomes one about +X.
    pub fn swapped_xy(&self) -> Mesh {
        Mesh {
            v: self
                .v
                .iter()
                .map(|v| {
                    let mut v = *v;
                    v.pos.swap(0, 1);
                    v.nrm.swap(0, 1);
                    v
                })
                .collect(),
            i: self.i.clone(),
        }
    }

    /// Adds `other` into this mesh, moved by `d`.
    pub fn append_at(&mut self, other: &Mesh, d: V3) {
        let base = self.v.len() as u32;
        self.v.extend(other.v.iter().map(|v| {
            let mut v = *v;
            v.pos[0] += d[0];
            v.pos[1] += d[1];
            v.pos[2] += d[2];
            v
        }));
        self.i.extend(other.i.iter().map(|k| k + base));
    }

    /// Adds `other` into this mesh.
    pub fn append(&mut self, other: &Mesh) {
        let base = self.v.len() as u32;
        self.v.extend_from_slice(&other.v);
        self.i.extend(other.i.iter().map(|k| k + base));
    }

    /// A surface of revolution about +Y. `prof` is (radius, height) points from the
    /// bottom up, swept from angle `a0` to `a1` (radians) in `seg` steps. With `smooth`
    /// the normals are averaged across each profile point (curves); without it every
    /// segment keeps its own normal, so corners stay sharp.
    pub fn lathe(&mut self, prof: &[(f32, f32)], a0: f32, a1: f32, seg: usize, smooth: bool, m: &Mat) {
        if prof.len() < 2 {
            return;
        }
        // Normal of each profile segment, in the (r, y) plane, pointing away from the axis
        // for a profile that runs upward.
        let seg_n: Vec<(f32, f32)> = prof
            .windows(2)
            .map(|w| {
                let (dr, dy) = (w[1].0 - w[0].0, w[1].1 - w[0].1);
                let l = (dr * dr + dy * dy).sqrt().max(1e-9);
                (dy / l, -dr / l)
            })
            .collect();
        // Per profile point: its normal (smooth: averaged neighbours; else the segment's).
        let pt_n: Vec<(f32, f32)> = (0..prof.len())
            .map(|j| {
                if smooth {
                    let a = seg_n[j.saturating_sub(1)];
                    let b = seg_n[j.min(seg_n.len() - 1)];
                    let (x, y) = (a.0 + b.0, a.1 + b.1);
                    let l = (x * x + y * y).sqrt().max(1e-9);
                    (x / l, y / l)
                } else {
                    seg_n[j.min(seg_n.len() - 1)]
                }
            })
            .collect();
        let steps = seg.max(1);
        let ring = |vs: &mut Mesh, r: f32, y: f32, nr: f32, ny: f32, a: f32| -> u32 {
            let (s, c) = a.sin_cos();
            vs.vert([r * c, y, r * s], [nr * c, ny, nr * s], m)
        };
        if smooth {
            let mut rings: Vec<Vec<u32>> = Vec::with_capacity(prof.len());
            for (j, p) in prof.iter().enumerate() {
                let row: Vec<u32> = (0..=steps)
                    .map(|k| {
                        let a = a0 + (a1 - a0) * k as f32 / steps as f32;
                        ring(self, p.0, p.1, pt_n[j].0, pt_n[j].1, a)
                    })
                    .collect();
                rings.push(row);
            }
            for j in 0..prof.len() - 1 {
                for k in 0..steps {
                    let (a, b) = (rings[j][k], rings[j][k + 1]);
                    let (c, d) = (rings[j + 1][k], rings[j + 1][k + 1]);
                    self.tri(a, c, b);
                    self.tri(b, c, d);
                }
            }
        } else {
            for j in 0..prof.len() - 1 {
                let (p0, p1) = (prof[j], prof[j + 1]);
                let (nr, ny) = seg_n[j];
                for k in 0..steps {
                    let a0k = a0 + (a1 - a0) * k as f32 / steps as f32;
                    let a1k = a0 + (a1 - a0) * (k + 1) as f32 / steps as f32;
                    let a = ring(self, p0.0, p0.1, nr, ny, a0k);
                    let b = ring(self, p0.0, p0.1, nr, ny, a1k);
                    let c = ring(self, p1.0, p1.1, nr, ny, a0k);
                    let d = ring(self, p1.0, p1.1, nr, ny, a1k);
                    self.tri(a, c, b);
                    self.tri(b, c, d);
                }
            }
        }
    }

    /// A solid cylinder or cone between heights `y0` and `y1`, radii `r0` and `r1`.
    pub fn frustum(&mut self, r0: f32, y0: f32, r1: f32, y1: f32, seg: usize, m: &Mat) {
        self.lathe(&[(r0, y0), (r1, y1)], 0.0, TAU, seg, false, m);
    }

    /// A flat disc at height `y` facing up (`up`) or down.
    pub fn disc(&mut self, r: f32, y: f32, up: bool, seg: usize, m: &Mat) {
        let prof = if up { [(r, y), (0.0, y)] } else { [(0.0, y), (r, y)] };
        self.lathe(&prof, 0.0, TAU, seg, false, m);
    }

    /// A jittered box (a shard): six faces, flat normals, deterministic per `seed`.
    pub fn shard(&mut self, centre: V3, size: f32, seed: u32, m: &Mat) {
        let mut rng = seed.wrapping_mul(2654435761).wrapping_add(12345);
        let mut next = || {
            rng ^= rng << 13;
            rng ^= rng >> 17;
            rng ^= rng << 5;
            (rng % 10000) as f32 / 10000.0
        };
        let mut c = [[0.0f32; 3]; 8];
        for (k, p) in c.iter_mut().enumerate() {
            let sx = if k & 1 == 0 { -1.0 } else { 1.0 };
            let sy = if k & 2 == 0 { -1.0 } else { 1.0 };
            let sz = if k & 4 == 0 { -1.0 } else { 1.0 };
            let j = |r: f32| 0.72 + 0.4 * r;
            *p = [
                centre[0] + sx * size * j(next()) * 0.5,
                centre[1] + sy * size * j(next()) * 0.5,
                centre[2] + sz * size * j(next()) * 0.5,
            ];
        }
        // corner index bits: x = 1, y = 2, z = 4
        let faces: [[usize; 4]; 6] = [
            [0, 2, 3, 1],
            [4, 5, 7, 6],
            [0, 1, 5, 4],
            [2, 6, 7, 3],
            [0, 4, 6, 2],
            [1, 3, 7, 5],
        ];
        for f in faces {
            let (p0, p1, p2, p3) = (c[f[0]], c[f[1]], c[f[2]], c[f[3]]);
            for tri in [[p0, p1, p2], [p0, p2, p3]] {
                let n = math::norm(math::cross(math::sub(tri[1], tri[0]), math::sub(tri[2], tri[0])));
                let a = self.vert(tri[0], n, m);
                let b = self.vert(tri[1], n, m);
                let cc = self.vert(tri[2], n, m);
                self.tri(a, b, cc);
            }
        }
    }

    /// An axis-aligned box centred on `c` with half sizes `h`: flat faces.
    pub fn cuboid(&mut self, c: V3, h: V3, m: &Mat) {
        let faces: [(V3, V3, V3); 6] = [
            ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]),
            ([-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]),
            ([0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]),
            ([0.0, -1.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]),
            ([0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
            ([0.0, 0.0, -1.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
        ];
        for (n, u, v) in faces {
            let ctr = [c[0] + n[0] * h[0], c[1] + n[1] * h[1], c[2] + n[2] * h[2]];
            // half extents along the face's two in-plane axes
            let eu = (u[0].abs() * h[0] + u[1].abs() * h[1] + u[2].abs() * h[2]).abs();
            let ev = (v[0].abs() * h[0] + v[1].abs() * h[1] + v[2].abs() * h[2]).abs();
            let p = |a: f32, b: f32| {
                [ctr[0] + u[0] * a + v[0] * b, ctr[1] + u[1] * a + v[1] * b, ctr[2] + u[2] * a + v[2] * b]
            };
            let quad = [p(-eu, -ev), p(eu, -ev), p(eu, ev), p(-eu, ev)];
            let idx: Vec<u32> = quad.iter().map(|q| self.vert(*q, n, m)).collect();
            self.tri(idx[0], idx[1], idx[2]);
            self.tri(idx[0], idx[2], idx[3]);
        }
    }

    /// A rectangular panel on a cylinder of radius `r`, from angle `a0` to `a1`, heights
    /// `y0` to `y1`, subdivided `nx` x `ny`. Double-sided through the shader.
    pub fn panel(&mut self, r: f32, y0: f32, y1: f32, a0: f32, a1: f32, nx: usize, ny: usize, m: &Mat) {
        let mut rows = Vec::new();
        for j in 0..=ny {
            let y = y0 + (y1 - y0) * j as f32 / ny as f32;
            let row: Vec<u32> = (0..=nx)
                .map(|i| {
                    let a = a0 + (a1 - a0) * i as f32 / nx as f32;
                    let (s, c) = a.sin_cos();
                    self.vert([r * c, y, r * s], [c, 0.0, s], m)
                })
                .collect();
            rows.push(row);
        }
        for j in 0..ny {
            for i in 0..nx {
                let (a, b) = (rows[j][i], rows[j][i + 1]);
                let (c, d) = (rows[j + 1][i], rows[j + 1][i + 1]);
                self.tri(a, c, b);
                self.tri(b, c, d);
            }
        }
    }

    /// A tube of radius `r` around the polyline `path`, `seg` sides around. The frame is
    /// carried along the path (parallel transport), so the tube does not twist.
    pub fn tube(&mut self, path: &[V3], r: f32, seg: usize, m: &Mat) {
        if path.len() < 2 || seg < 3 {
            return;
        }
        let n = path.len();
        let tang: Vec<V3> = (0..n)
            .map(|i| math::norm(math::sub(path[(i + 1).min(n - 1)], path[i.saturating_sub(1)])))
            .collect();
        let helper = if tang[0][1].abs() < 0.9 { [0.0, 1.0, 0.0] } else { [1.0, 0.0, 0.0] };
        let mut u = math::norm(math::cross(tang[0], helper));
        let mut rows: Vec<Vec<u32>> = Vec::with_capacity(n);
        for (i, &t) in tang.iter().enumerate() {
            u = math::norm(math::sub(u, math::scale(t, math::dot(u, t))));
            let v = math::cross(t, u);
            let row: Vec<u32> = (0..=seg)
                .map(|k| {
                    let a = TAU * k as f32 / seg as f32;
                    let dir = math::add(math::scale(u, a.cos()), math::scale(v, a.sin()));
                    self.vert(math::add(path[i], math::scale(dir, r)), dir, m)
                })
                .collect();
            rows.push(row);
        }
        for i in 0..n - 1 {
            for k in 0..seg {
                let (a, b) = (rows[i][k], rows[i][k + 1]);
                let (c, d) = (rows[i + 1][k], rows[i + 1][k + 1]);
                self.tri(a, c, b);
                self.tri(b, c, d);
            }
        }
    }
}

/// Deterministic pseudo-random in [0, 1) from integer `n`.
pub fn hash01(n: u32) -> f32 {
    let mut x = n.wrapping_mul(0x9E37_79B9) ^ 0x85EB_CA6B;
    x ^= x >> 15;
    x = x.wrapping_mul(0x2C1B_3C6D);
    x ^= x >> 12;
    (x & 0xFFFF) as f32 / 65536.0
}
