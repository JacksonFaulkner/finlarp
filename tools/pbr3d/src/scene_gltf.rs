//! A scene authored in Blender (`blender/laser_overview.py`), exported as glTF, and played
//! back as pbr3d meshes. The file's node transforms and their keyframes are sampled at a
//! time in seconds, every visible mesh is moved into world space, and the result is one
//! solid mesh and one glass mesh, as the rigs build them. The camera is two empties,
//! `CamEye` and `CamTarget`, so a shot is whatever the author keyed in Blender.

use crate::math::{self, M4, V3};
use crate::mesh::{Kind, Mesh, Vertex};

/// Local transform: translation, rotation quaternion (x, y, z, w), scale.
#[derive(Clone, Copy, Debug)]
struct Trs {
    t: V3,
    r: [f32; 4],
    s: V3,
}

/// One primitive of a node, with its material already read.
struct Prim {
    pos: Vec<V3>,
    nrm: Vec<V3>,
    idx: Vec<u32>,
    base: [f32; 3],
    metal: f32,
    rough: f32,
    alpha: f32,
    emit: [f32; 3],
}

struct Node {
    parent: Option<usize>,
    rest: Trs,
    prims: Vec<Prim>,
    name: String,
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum Prop {
    T,
    R,
    S,
}

/// One animated property of one node: keyframe times and values (xyz or xyzw).
struct Chan {
    node: usize,
    prop: Prop,
    step: bool,
    times: Vec<f32>,
    vals: Vec<[f32; 4]>,
}

pub struct Scene {
    nodes: Vec<Node>,
    chans: Vec<Chan>,
    roots: Vec<usize>,
    /// the last keyframe time over all channels, in seconds
    pub duration: f32,
}

impl Scene {
    /// Loads a binary glTF (`.glb`), e.g. one embedded with `include_bytes!`.
    pub fn from_glb(bytes: &[u8]) -> Result<Scene, String> {
        let (doc, buffers, _images) = gltf::import_slice(bytes).map_err(|e| e.to_string())?;
        let mut nodes: Vec<Node> = doc
            .nodes()
            .map(|n| {
                let (t, r, s) = n.transform().decomposed();
                let prims = n
                    .mesh()
                    .map(|m| {
                        m.primitives()
                            .filter_map(|p| read_prim(&p, &buffers))
                            .collect::<Vec<Prim>>()
                    })
                    .unwrap_or_default();
                Node {
                    parent: None,
                    rest: Trs { t, r, s },
                    prims,
                    name: n.name().unwrap_or("").to_string(),
                }
            })
            .collect();
        for n in doc.nodes() {
            for c in n.children() {
                nodes[c.index()].parent = Some(n.index());
            }
        }
        let roots = (0..nodes.len())
            .filter(|&i| nodes[i].parent.is_none())
            .collect();

        let mut chans = Vec::new();
        let mut duration = 0.0f32;
        for anim in doc.animations() {
            for ch in anim.channels() {
                let prop = match ch.target().property() {
                    gltf::animation::Property::Translation => Prop::T,
                    gltf::animation::Property::Rotation => Prop::R,
                    gltf::animation::Property::Scale => Prop::S,
                    _ => continue,
                };
                let reader = ch.reader(|b| Some(&buffers[b.index()].0[..]));
                let Some(times) = reader.read_inputs() else {
                    continue;
                };
                let Some(outs) = reader.read_outputs() else {
                    continue;
                };
                let times: Vec<f32> = times.collect();
                let vals: Vec<[f32; 4]> = match outs {
                    gltf::animation::util::ReadOutputs::Translations(it) => {
                        it.map(|v| [v[0], v[1], v[2], 0.0]).collect()
                    }
                    gltf::animation::util::ReadOutputs::Scales(it) => {
                        it.map(|v| [v[0], v[1], v[2], 0.0]).collect()
                    }
                    gltf::animation::util::ReadOutputs::Rotations(it) => it.into_f32().collect(),
                    _ => continue,
                };
                if let Some(&last) = times.last() {
                    duration = duration.max(last);
                }
                let step = ch.sampler().interpolation() == gltf::animation::Interpolation::Step;
                chans.push(Chan {
                    node: ch.target().node().index(),
                    prop,
                    step,
                    times,
                    vals,
                });
            }
        }
        Ok(Scene {
            nodes,
            chans,
            roots,
            duration,
        })
    }

    /// The node with this name (the first one), if any.
    fn find(&self, name: &str) -> Option<usize> {
        self.nodes.iter().position(|n| n.name == name)
    }

    /// The local transform of every node at time `t`.
    fn locals(&self, t: f32) -> Vec<Trs> {
        let mut out: Vec<Trs> = self.nodes.iter().map(|n| n.rest).collect();
        for c in &self.chans {
            let v = sample(c, t);
            let slot = &mut out[c.node];
            match c.prop {
                Prop::T => slot.t = [v[0], v[1], v[2]],
                Prop::S => slot.s = [v[0], v[1], v[2]],
                Prop::R => slot.r = v,
            }
        }
        out
    }

    /// The world matrix of every node at time `t` (parents first).
    fn worlds(&self, locals: &[Trs]) -> Vec<M4> {
        let mut world = vec![math::identity(); self.nodes.len()];
        // nodes can list children before parents, so walk down from the roots
        let mut stack: Vec<usize> = self.roots.clone();
        let mut kids: Vec<Vec<usize>> = vec![Vec::new(); self.nodes.len()];
        for (i, n) in self.nodes.iter().enumerate() {
            if let Some(p) = n.parent {
                kids[p].push(i);
            }
        }
        while let Some(i) = stack.pop() {
            let local = trs_matrix(locals[i]);
            world[i] = match self.nodes[i].parent {
                Some(p) => math::mul(world[p], local),
                None => local,
            };
            stack.extend(kids[i].iter().copied());
        }
        world
    }

    /// The camera at time `t`: eye and look-at target, from the `CamEye` and `CamTarget` empties.
    pub fn camera(&self, t: f32) -> Option<(V3, V3)> {
        let locals = self.locals(t);
        let world = self.worlds(&locals);
        let eye = self.find("CamEye")?;
        let target = self.find("CamTarget")?;
        Some((translation(world[eye]), translation(world[target])))
    }

    /// The opaque and glass meshes of everything visible at time `t`.
    pub fn meshes(&self, t: f32) -> (Mesh, Mesh) {
        let locals = self.locals(t);
        let world = self.worlds(&locals);
        let mut solid = Mesh::new();
        let mut glass = Mesh::new();
        for i in 0..self.nodes.len() {
            // a node scaled to nothing hides its own meshes (its children are skipped by the caller)
            if !visible(&world[i]) {
                continue;
            }
            for p in &self.nodes[i].prims {
                emit(
                    p,
                    &world[i],
                    if p.alpha < 0.99 {
                        &mut glass
                    } else {
                        &mut solid
                    },
                );
            }
        }
        (solid, glass)
    }
}

fn read_prim(p: &gltf::Primitive, buffers: &[gltf::buffer::Data]) -> Option<Prim> {
    let reader = p.reader(|b| Some(&buffers[b.index()].0[..]));
    let pos: Vec<V3> = reader.read_positions()?.collect();
    let nrm: Vec<V3> = match reader.read_normals() {
        Some(it) => it.collect(),
        None => vec![[0.0, 1.0, 0.0]; pos.len()],
    };
    let idx: Vec<u32> = match reader.read_indices() {
        Some(it) => it.into_u32().collect(),
        None => (0..pos.len() as u32).collect(),
    };
    let m = p.material();
    let pbr = m.pbr_metallic_roughness();
    let bc = pbr.base_color_factor();
    let emit = m.emissive_factor();
    let strength = m.emissive_strength().unwrap_or(1.0);
    Some(Prim {
        pos,
        nrm,
        idx,
        base: [bc[0], bc[1], bc[2]],
        metal: pbr.metallic_factor(),
        rough: pbr.roughness_factor(),
        alpha: bc[3],
        emit: [emit[0] * strength, emit[1] * strength, emit[2] * strength],
    })
}

/// Value of one channel at time `t`: a step holds the earlier key, otherwise linear (slerp for rotation).
fn sample(c: &Chan, t: f32) -> [f32; 4] {
    let n = c.times.len();
    if n == 0 {
        return [0.0; 4];
    }
    if t <= c.times[0] || n == 1 {
        return c.vals[0];
    }
    if t >= c.times[n - 1] {
        return c.vals[n - 1];
    }
    let k = c.times.partition_point(|&x| x <= t) - 1;
    if c.step {
        return c.vals[k];
    }
    let (t0, t1) = (c.times[k], c.times[k + 1]);
    let u = if t1 > t0 { (t - t0) / (t1 - t0) } else { 0.0 };
    let (a, b) = (c.vals[k], c.vals[k + 1]);
    if c.prop == Prop::R {
        return nlerp4(a, b, u);
    }
    [0, 1, 2, 3].map(|i| a[i] + (b[i] - a[i]) * u)
}

fn nlerp4(a: [f32; 4], b: [f32; 4], u: f32) -> [f32; 4] {
    let dot: f32 = (0..4).map(|i| a[i] * b[i]).sum();
    let sign = if dot < 0.0 { -1.0 } else { 1.0 };
    let q = [0, 1, 2, 3].map(|i| a[i] + (sign * b[i] - a[i]) * u);
    let l = q.iter().map(|x| x * x).sum::<f32>().sqrt().max(1e-9);
    q.map(|x| x / l)
}

/// Matrix of a local transform: T * R * S, column-major.
fn trs_matrix(x: Trs) -> M4 {
    let [qx, qy, qz, qw] = x.r;
    let r = [
        [
            1.0 - 2.0 * (qy * qy + qz * qz),
            2.0 * (qx * qy + qz * qw),
            2.0 * (qx * qz - qy * qw),
        ],
        [
            2.0 * (qx * qy - qz * qw),
            1.0 - 2.0 * (qx * qx + qz * qz),
            2.0 * (qy * qz + qx * qw),
        ],
        [
            2.0 * (qx * qz + qy * qw),
            2.0 * (qy * qz - qx * qw),
            1.0 - 2.0 * (qx * qx + qy * qy),
        ],
    ];
    let mut m = math::identity();
    for c in 0..3 {
        for row in 0..3 {
            m[c][row] = r[c][row] * x.s[c];
        }
    }
    m[3] = [x.t[0], x.t[1], x.t[2], 1.0];
    m
}

fn translation(m: M4) -> V3 {
    [m[3][0], m[3][1], m[3][2]]
}

/// A node is visible unless one of its axes is scaled to nothing.
fn visible(m: &M4) -> bool {
    (0..3).all(|c| math::len([m[c][0], m[c][1], m[c][2]]) > 1e-4)
}

fn transform_point(m: &M4, p: V3) -> V3 {
    [
        m[0][0] * p[0] + m[1][0] * p[1] + m[2][0] * p[2] + m[3][0],
        m[0][1] * p[0] + m[1][1] * p[1] + m[2][1] * p[2] + m[3][1],
        m[0][2] * p[0] + m[1][2] * p[1] + m[2][2] * p[2] + m[3][2],
    ]
}

/// Normals follow the inverse transpose of the linear part: its cofactor matrix, normalised.
fn transform_normal(m: &M4, n: V3) -> V3 {
    // a[row][col] of the linear part; m is column-major
    let a = [
        [m[0][0], m[1][0], m[2][0]],
        [m[0][1], m[1][1], m[2][1]],
        [m[0][2], m[1][2], m[2][2]],
    ];
    let c = |i: usize, j: usize| {
        let (i1, i2) = ((i + 1) % 3, (i + 2) % 3);
        let (j1, j2) = ((j + 1) % 3, (j + 2) % 3);
        a[i1][j1] * a[i2][j2] - a[i1][j2] * a[i2][j1]
    };
    // cofactor(i, j) multiplies n[j] into row i
    let out = [0, 1, 2].map(|i| (0..3).map(|j| c(i, j) * n[j]).sum::<f32>());
    math::norm(out)
}

fn emit(p: &Prim, world: &M4, into: &mut Mesh) {
    let kind = if p.alpha < 0.99 {
        Kind::Glass
    } else {
        Kind::Plain
    };
    let alpha = p.alpha;
    let base = into.v.len() as u32;
    for (i, &lp) in p.pos.iter().enumerate() {
        let wp = transform_point(world, lp);
        let wn = transform_normal(world, p.nrm.get(i).copied().unwrap_or([0.0, 1.0, 0.0]));
        into.v.push(Vertex {
            pos: [wp[0], wp[1], wp[2], 1.0],
            nrm: [wn[0], wn[1], wn[2], 0.0],
            alb: [p.base[0], p.base[1], p.base[2], p.metal],
            mat: [p.rough, alpha, kind as u32 as f32, 0.0],
            emi: [p.emit[0], p.emit[1], p.emit[2], 0.0],
        });
    }
    for tri in p.idx.chunks_exact(3) {
        into.i
            .extend_from_slice(&[base + tri[0], base + tri[1], base + tri[2]]);
    }
}

/// One frame of the scene at time `t` (seconds), from its own camera. The light is the
/// melt rig's sun, so the two pictures sit together in the same look.
pub fn render(scene: &Scene, t: f32, w: u32, h: u32, bg: [u8; 3]) -> image::RgbaImage {
    let (eye, target) = scene
        .camera(t)
        .unwrap_or(([0.0, 500.0, 3000.0], [0.0, 0.0, 0.0]));
    let (solid, glass) = scene.meshes(t);
    let bgf = [
        bg[0] as f32 / 255.0,
        bg[1] as f32 / 255.0,
        bg[2] as f32 / 255.0,
    ];
    let view = math::look_at(eye, target, [0.0, 1.0, 0.0]);
    let proj = math::perspective(0.52, w as f32 / h.max(1) as f32, 40.0, 40000.0);
    let sun = math::norm([-0.55, 0.8, 0.42]);
    let light_c = target;
    let light_eye = math::add(light_c, math::scale(sun, 15000.0));
    let light_view = math::look_at(light_eye, light_c, [0.0, 1.0, 0.0]);
    let light_proj = math::ortho(-6000.0, 6000.0, -6000.0, 6000.0, 1000.0, 30000.0);
    let f = crate::gpu::Frame {
        view_proj: math::mul(proj, view),
        light_vp: math::mul(light_proj, light_view),
        cam_pos: eye,
        sun_dir: sun,
        sun_col: [3.2, 3.0, 2.7],
        pt_pos: [target[0], target[1] + 400.0, target[2]],
        pt_radius: 2500.0,
        pt_col: [0.5, 0.5, 0.6],
        clip_n: [0.0, 0.0, 0.0],
        clip_d: 0.0,
        sky: [0.5, 0.56, 0.68],
        ground: [0.05, 0.045, 0.04],
        time: t,
        bg: bgf,
        bloom: 0.22,
        exposure: 0.9,
        proj_diag: [
            1.0 / (0.26f32).tan() / (w as f32 / h.max(1) as f32),
            1.0 / (0.26f32).tan(),
        ],
        near_far: [40.0, 40000.0],
        ao_radius: 110.0,
        ao_strength: 0.85,
    };
    crate::gpu::with_renderer(|r| r.render(&f, &solid, &glass, w, h))
}
