//! Software rasterizer for the polysilicon Siemens bell-jar scene.
//!
//! Shared by the offline GIF tool (`src/main.rs`) and the TUI's full-screen
//! view. Pure: no terminal, no file IO. Units are millimetres, Y is up.
//! Solids are z-buffered, flat-shaded triangles. The glass jar is an
//! alpha-blended wireframe drawn last.

use image::{Rgb, RgbaImage};

mod cell;
pub use cell::{
    clip_cell_anim, clip_cell_view, notes_alpha, overview_params, render_cell, render_overview, Notes, render_zoom, CellAnim, CellParams,
    CellZoom, render_litho_overview, render_litho_zoom, LithoZoom, LITHO_OVERVIEW_BEATS,
    render_array_overview, render_array_zoom, ArrayZoom, ARRAY_OVERVIEW_BEATS,
    render_bank_overview, render_bank_zoom, BankZoom, BANK_OVERVIEW_BEATS,
    render_bw_overview, render_bw_zoom, BwZoom, BW_OVERVIEW_BEATS,
    render_hbm_overview, render_hbm_zoom, HbmZoom, HBM_OVERVIEW_BEATS,
    part_at, render_chip, ChipKey, ChipPart, ChipState,
    pkg_part_at, render_pkg, PkgKey, PkgPart, PkgState,
};

type V3 = [f64; 3];
type Col = [f32; 3];

fn add(a: V3, b: V3) -> V3 {
    [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
}
fn sub(a: V3, b: V3) -> V3 {
    [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
}
fn mul(a: V3, s: f64) -> V3 {
    [a[0] * s, a[1] * s, a[2] * s]
}
fn dot(a: V3, b: V3) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}
fn cross(a: V3, b: V3) -> V3 {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}
fn norm(a: V3) -> V3 {
    let l = dot(a, a).sqrt();
    if l < 1e-12 {
        a
    } else {
        mul(a, 1.0 / l)
    }
}
fn lerp(a: f64, b: f64, t: f64) -> f64 {
    a + (b - a) * t
}
fn smoothstep(e0: f64, e1: f64, x: f64) -> f64 {
    let t = ((x - e0) / (e1 - e0)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Scene dimensions, mm. Values marked `sourced` come from the finlarp
/// POLYSILICON / BellJar scenes. Everything else is schematic.
#[derive(Clone, Copy, Debug)]
pub struct Params {
    /// sourced: start rods about 20 mm across
    pub rod_start_d: f64,
    /// sourced: rods end 150-180 mm, midpoint used
    pub rod_final_d: f64,
    /// schematic: centre-to-centre spacing of the two rod legs
    pub leg_gap: f64,
    /// schematic: height of the U-bridge above the base plate
    pub rod_top: f64,
    /// schematic: inner radius of the jar
    pub jar_radius: f64,
    /// schematic: straight wall height above the base plate
    pub wall_height: f64,
    /// schematic: dome height above the wall
    pub dome_height: f64,
    /// schematic: base plate radius and thickness
    pub base_radius: f64,
    pub base_thick: f64,
    /// schematic: graphite electrode stub radius
    pub chuck_radius: f64,
}

impl Default for Params {
    fn default() -> Self {
        Params {
            rod_start_d: 20.0,
            rod_final_d: 160.0,
            leg_gap: 300.0,
            rod_top: 1100.0,
            jar_radius: 500.0,
            wall_height: 1500.0,
            dome_height: 450.0,
            base_radius: 560.0,
            base_thick: 60.0,
            chuck_radius: 40.0,
        }
    }
}

/// Process flows drawn over the scene as directions of travel, each 0 (off) .. 1.
#[derive(Clone, Copy, Debug, PartialEq, Default)]
pub struct Flow {
    /// evacuation: the pump draws gas out at the base
    pub pump: f64,
    /// feed: TCS and H2 rise from the nozzles in the base plate
    pub feed: f64,
    /// off-gas: HCl, H2 and STC leave through the base ports
    pub exhaust: f64,
    /// current up one rod, across the bridge, down the other
    pub power: f64,
}

/// What the scene shows at one instant: rod glow (0 cold .. 1 white-hot), rod
/// diameter in mm, the flows, and `phase` (0..1) which moves the flow dashes.
#[derive(Clone, Copy, Debug, PartialEq, Default)]
pub struct Anim {
    pub heat: f64,
    pub rod_d: f64,
    pub flow: Flow,
    pub phase: f64,
}

/// Where the camera is. `pan` is in pixels, `zoom` scales the lens.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct View {
    pub yaw: f64,
    pub pitch: f64,
    pub zoom: f64,
    pub pan: [f64; 2],
}

impl Default for View {
    fn default() -> Self {
        View {
            yaw: 0.10,
            pitch: 0.20,
            zoom: 1.0,
            pan: [0.0, 0.0],
        }
    }
}

impl View {
    /// Pitch stays between a slight dip and a high look-down, so the jar
    /// never flips over.
    pub fn orbit(&mut self, dyaw: f64, dpitch: f64) {
        self.yaw += dyaw;
        self.pitch = (self.pitch + dpitch).clamp(-0.3, 1.3);
    }
    pub fn zoom_by(&mut self, factor: f64) {
        self.zoom = (self.zoom * factor).clamp(0.3, 6.0);
    }
    pub fn pan_by(&mut self, dx: f64, dy: f64) {
        self.pan[0] += dx;
        self.pan[1] += dy;
    }
}

/// Animation at clip position `t` (0..1): the offline GIF's timeline.
pub fn clip_anim(p: &Params, t: f64) -> Anim {
    Anim {
        heat: smoothstep(0.10, 0.28, t),
        rod_d: lerp(p.rod_start_d, p.rod_final_d, smoothstep(0.30, 0.90, t)),
        ..Anim::default()
    }
}

/// The offline GIF's turntable at clip position `t` (0..1).
pub fn clip_view(t: f64) -> View {
    View {
        yaw: 0.10 + 0.95 * t,
        pitch: 0.20 + 0.04 * (std::f64::consts::TAU * t).sin(),
        ..View::default()
    }
}

/// One flat-shaded triangle in world space.
struct Tri {
    p: [V3; 3],
    base: Col,
    emit: Col,
}

const NEAR: f64 = 10.0;
const LIGHT: V3 = [-0.45, 0.85, 0.55];
const TARGET_DIST: f64 = 3600.0;

struct Cam {
    eye: V3,
    r: V3,
    u: V3,
    f: V3,
    focal: f64,
    cx: f64,
    cy: f64,
}

impl Cam {
    fn orbit(view: &View, p: &Params, w: usize, h: usize) -> Cam {
        Cam::orbit_at(view, [0.0, p.wall_height * 0.48, 0.0], TARGET_DIST, w, h)
    }

    /// Camera on a sphere of radius `dist` around `target`, turned by `view`.
    fn orbit_at(view: &View, target: V3, dist: f64, w: usize, h: usize) -> Cam {
        let dir = [
            view.pitch.cos() * view.yaw.sin(),
            view.pitch.sin(),
            view.pitch.cos() * view.yaw.cos(),
        ];
        let eye = add(target, mul(dir, dist));
        let f = norm(sub(target, eye));
        let r = norm(cross(f, [0.0, 1.0, 0.0]));
        let u = cross(r, f);
        Cam {
            eye,
            r,
            u,
            f,
            focal: h as f64 * 1.30 * view.zoom,
            cx: w as f64 * 0.5 + view.pan[0],
            cy: h as f64 * 0.5 + view.pan[1],
        }
    }

    fn view(&self, p: V3) -> V3 {
        let d = sub(p, self.eye);
        [dot(d, self.r), dot(d, self.u), dot(d, self.f)]
    }

    /// Screen x, y and 1/z. None when the point is behind the near plane.
    fn project(&self, p: V3) -> Option<(f64, f64, f64)> {
        let v = self.view(p);
        if v[2] <= NEAR {
            return None;
        }
        let inv = 1.0 / v[2];
        Some((
            self.cx + self.focal * v[0] * inv,
            self.cy - self.focal * v[1] * inv,
            inv,
        ))
    }
}

struct Canvas {
    w: usize,
    h: usize,
    rgb: Vec<Col>,
    z: Vec<f32>,
}

impl Canvas {
    /// Alpha-blended line drawn over everything: no depth test. Used for the flow
    /// directions, which must read even where they run through a solid.
    fn overlay(&mut self, cam: &Cam, a: V3, b: V3, col: Col, alpha: f32) {
        let (Some(pa), Some(pb)) = (cam.project(a), cam.project(b)) else {
            return;
        };
        let dx = pb.0 - pa.0;
        let dy = pb.1 - pa.1;
        let n = dx.abs().max(dy.abs()).ceil().max(1.0) as usize;
        for i in 0..=n {
            let t = i as f64 / n as f64;
            let x = lerp(pa.0, pb.0, t).floor();
            let y = lerp(pa.1, pb.1, t).floor();
            if x < 0.0 || y < 0.0 || x >= self.w as f64 || y >= self.h as f64 {
                continue;
            }
            let c = &mut self.rgb[y as usize * self.w + x as usize];
            for k in 0..3 {
                c[k] = c[k] * (1.0 - alpha) + col[k] * alpha;
            }
        }
    }

    /// Flat background: must match the terminal background so the image sits in the TUI unseen.
    fn new(w: usize, h: usize, bg: Col) -> Canvas {
        Canvas {
            w,
            h,
            rgb: vec![bg; w * h],
            z: vec![f32::INFINITY; w * h],
        }
    }

    fn fill_tri(&mut self, cam: &Cam, p: [V3; 3], col: Col) {
        let mut s = [(0.0f64, 0.0f64, 0.0f64); 3];
        for i in 0..3 {
            match cam.project(p[i]) {
                Some(v) => s[i] = v,
                None => return,
            }
        }
        let a = (s[0].0, s[0].1);
        let b = (s[1].0, s[1].1);
        let c = (s[2].0, s[2].1);
        let area = edge(a, b, c);
        if area.abs() < 1e-9 {
            return;
        }
        let minx = s
            .iter()
            .map(|v| v.0)
            .fold(f64::INFINITY, f64::min)
            .floor()
            .max(0.0);
        let maxx = s
            .iter()
            .map(|v| v.0)
            .fold(f64::NEG_INFINITY, f64::max)
            .ceil()
            .min(self.w as f64 - 1.0);
        let miny = s
            .iter()
            .map(|v| v.1)
            .fold(f64::INFINITY, f64::min)
            .floor()
            .max(0.0);
        let maxy = s
            .iter()
            .map(|v| v.1)
            .fold(f64::NEG_INFINITY, f64::max)
            .ceil()
            .min(self.h as f64 - 1.0);
        if maxx < 0.0 || maxy < 0.0 || minx > maxx || miny > maxy {
            return;
        }
        for y in miny as usize..=maxy as usize {
            for x in minx as usize..=maxx as usize {
                let px = (x as f64 + 0.5, y as f64 + 0.5);
                let w0 = edge(b, c, px) / area;
                let w1 = edge(c, a, px) / area;
                let w2 = 1.0 - w0 - w1;
                if w0 < 0.0 || w1 < 0.0 || w2 < 0.0 {
                    continue;
                }
                let iz = w0 * s[0].2 + w1 * s[1].2 + w2 * s[2].2;
                let depth = (1.0 / iz) as f32;
                let idx = y * self.w + x;
                if depth < self.z[idx] {
                    self.z[idx] = depth;
                    self.rgb[idx] = col;
                }
            }
        }
    }

    /// Alpha-blended line. Depth-tested against solids, does not write depth.
    fn line(&mut self, cam: &Cam, a: V3, b: V3, col: Col, alpha: f32) {
        let (Some(pa), Some(pb)) = (cam.project(a), cam.project(b)) else {
            return;
        };
        let dx = pb.0 - pa.0;
        let dy = pb.1 - pa.1;
        let n = dx.abs().max(dy.abs()).ceil().max(1.0) as usize;
        for i in 0..=n {
            let t = i as f64 / n as f64;
            let x = lerp(pa.0, pb.0, t).floor();
            let y = lerp(pa.1, pb.1, t).floor();
            let inv = lerp(pa.2, pb.2, t);
            if x < 0.0 || y < 0.0 || x >= self.w as f64 || y >= self.h as f64 {
                continue;
            }
            let idx = y as usize * self.w + x as usize;
            if ((1.0 / inv) as f32) < self.z[idx] {
                let c = &mut self.rgb[idx];
                for k in 0..3 {
                    c[k] = c[k] * (1.0 - alpha) + col[k] * alpha;
                }
            }
        }
    }
}

fn edge(a: (f64, f64), b: (f64, f64), p: (f64, f64)) -> f64 {
    (b.0 - a.0) * (p.1 - a.1) - (b.1 - a.1) * (p.0 - a.0)
}

/// Flat shade: two-sided lambert plus ambient, plus self-emission for hot rods.
fn shade(tri: &Tri) -> Col {
    let n = norm(cross(sub(tri.p[1], tri.p[0]), sub(tri.p[2], tri.p[0])));
    let diff = dot(n, norm(LIGHT)).abs();
    let k = (0.28 + 0.72 * diff) as f32;
    [
        (tri.base[0] * k + tri.emit[0]).min(1.0),
        (tri.base[1] * k + tri.emit[1]).min(1.0),
        (tri.base[2] * k + tri.emit[2]).min(1.0),
    ]
}

/// Side walls (and optional caps) of a cylinder from a to b.
fn push_tube(
    out: &mut Vec<Tri>,
    a: V3,
    b: V3,
    r: f64,
    seg: usize,
    base: Col,
    emit: Col,
    caps: bool,
) {
    let axis = norm(sub(b, a));
    let reference = if axis[1].abs() < 0.9 {
        [0.0, 1.0, 0.0]
    } else {
        [1.0, 0.0, 0.0]
    };
    let e1 = norm(cross(axis, reference));
    let e2 = cross(axis, e1);
    let ring = |c: V3, i: usize| {
        let th = std::f64::consts::TAU * i as f64 / seg as f64;
        add(c, mul(add(mul(e1, th.cos()), mul(e2, th.sin())), r))
    };
    for i in 0..seg {
        let a0 = ring(a, i);
        let a1 = ring(a, i + 1);
        let b0 = ring(b, i);
        let b1 = ring(b, i + 1);
        out.push(Tri {
            p: [a0, b0, b1],
            base,
            emit,
        });
        out.push(Tri {
            p: [a0, b1, a1],
            base,
            emit,
        });
        if caps {
            out.push(Tri {
                p: [a, a1, a0],
                base,
                emit,
            });
            out.push(Tri {
                p: [b, b0, b1],
                base,
                emit,
            });
        }
    }
}

fn build_scene(p: &Params, anim: Anim) -> Vec<Tri> {
    let mut m = Vec::new();
    let plate_col = [0.20, 0.21, 0.24];
    let zero = [0.0f32; 3];

    // base plate: y from -base_thick to 0
    push_tube(
        &mut m,
        [0.0, -p.base_thick, 0.0],
        [0.0, 0.0, 0.0],
        p.base_radius,
        72,
        plate_col,
        zero,
        true,
    );

    // graphite electrode stubs, one per leg, below the plate surface
    let legs = [-p.leg_gap / 2.0, p.leg_gap / 2.0];
    for &x in &legs {
        push_tube(
            &mut m,
            [x, -160.0, 0.0],
            [x, 0.0, 0.0],
            p.chuck_radius,
            24,
            [0.10, 0.10, 0.11],
            zero,
            true,
        );
    }

    // rods: silicon from cool grey to glowing orange as heat rises
    let r = anim.rod_d / 2.0;
    let h = anim.heat as f32;
    let base: Col = [
        lerp(0.36, 0.95, h as f64) as f32,
        lerp(0.39, 0.52, h as f64) as f32,
        lerp(0.44, 0.22, h as f64) as f32,
    ];
    let emit: Col = [0.95 * h, 0.50 * h, 0.18 * h];
    for &x in &legs {
        push_tube(
            &mut m,
            [x, 0.0, 0.0],
            [x, p.rod_top, 0.0],
            r,
            20,
            base,
            emit,
            true,
        );
    }
    push_tube(
        &mut m,
        [legs[0], p.rod_top, 0.0],
        [legs[1], p.rod_top, 0.0],
        r,
        20,
        base,
        emit,
        true,
    );

    m
}

/// Wireframe of the water-cooled jar: meridians and rings on wall and dome.
fn draw_jar(cv: &mut Canvas, cam: &Cam, p: &Params) {
    let col: Col = [0.62, 0.80, 0.92];
    let alpha = 0.28;
    let meridians = 28;
    let rings_wall = 6;
    let rings_dome = 4;
    let r = p.jar_radius;
    let y1 = p.wall_height;

    // profile: wall then dome, each point (radius, height)
    let mut profile: Vec<(f64, f64)> = Vec::new();
    for k in 0..=rings_wall {
        profile.push((r, lerp(0.0, y1, k as f64 / rings_wall as f64)));
    }
    for k in 1..=rings_dome {
        let phi = std::f64::consts::FRAC_PI_2 * k as f64 / rings_dome as f64;
        profile.push((r * phi.cos(), y1 + p.dome_height * phi.sin()));
    }

    // rings: each profile point as a circle
    let seg = 96;
    for &(rad, y) in &profile {
        let mut prev: Option<V3> = None;
        for i in 0..=seg {
            let th = std::f64::consts::TAU * i as f64 / seg as f64;
            let pt = [rad * th.cos(), y, rad * th.sin()];
            if let Some(q) = prev {
                cv.line(cam, q, pt, col, alpha);
            }
            prev = Some(pt);
        }
    }

    // meridians through the profile
    for m in 0..meridians {
        let th = std::f64::consts::TAU * m as f64 / meridians as f64;
        let (c, s) = (th.cos(), th.sin());
        let mut prev: Option<V3> = None;
        for &(rad, y) in &profile {
            let pt = [rad * c, y, rad * s];
            if let Some(q) = prev {
                cv.line(cam, q, pt, col, alpha);
            }
            prev = Some(pt);
        }
    }
}

fn render_canvas(p: &Params, anim: Anim, view: &View, w: usize, h: usize, bg: Col) -> Canvas {
    let mut cv = Canvas::new(w, h, bg);
    let cam = Cam::orbit(view, p, w, h);

    // opaque solids first, depth-tested
    let mut tris = build_scene(p, anim);
    tris.sort_by(|a, b| {
        let da: f64 = a.p.iter().map(|q| cam.view(*q)[2]).sum();
        let db: f64 = b.p.iter().map(|q| cam.view(*q)[2]).sum();
        db.partial_cmp(&da).unwrap_or(std::cmp::Ordering::Equal)
    });
    for tri in &tris {
        let col = shade(tri);
        cv.fill_tri(&cam, tri.p, col);
    }

    // glass jar, as a translucent wireframe
    draw_jar(&mut cv, &cam, p);
    // process flows last, so the directions read over the glass
    draw_flows(&mut cv, &cam, p, anim);
    cv
}

const PUMP: Col = [0.40, 0.80, 1.00];
const FEED: Col = [0.60, 1.00, 0.50];
const EXHAUST: Col = [1.00, 0.60, 0.30];
const POWER: Col = [1.00, 0.95, 0.40];

/// Position at arc length `s` along a polyline with cumulative lengths `lens`.
fn point_at(pts: &[V3], lens: &[f64], s: f64) -> V3 {
    for i in 0..pts.len() - 1 {
        if s <= lens[i + 1] {
            let span = lens[i + 1] - lens[i];
            let t = if span > 0.0 {
                (s - lens[i]) / span
            } else {
                0.0
            };
            return add(pts[i], mul(sub(pts[i + 1], pts[i]), t.clamp(0.0, 1.0)));
        }
    }
    *pts.last().unwrap()
}

/// One flow route: a faint line along it, with bright dashes marching from start to end.
fn route(cv: &mut Canvas, cam: &Cam, pts: &[V3], col: Col, strength: f64, phase: f64) {
    if strength <= 0.0 || pts.len() < 2 {
        return;
    }
    let s = strength as f32;
    for seg in pts.windows(2) {
        cv.overlay(cam, seg[0], seg[1], col, 0.18 * s);
    }
    let mut lens = vec![0.0f64];
    for seg in pts.windows(2) {
        let d = sub(seg[1], seg[0]);
        lens.push(lens.last().unwrap() + dot(d, d).sqrt());
    }
    let total = *lens.last().unwrap();
    const DASHES: usize = 5;
    const DASH: f64 = 0.10;
    const STEPS: usize = 6;
    for k in 0..DASHES {
        let head = ((phase + k as f64 / DASHES as f64) % 1.0) * total;
        let tail = (head - DASH * total).max(0.0);
        let mut prev = point_at(pts, &lens, tail);
        for i in 1..=STEPS {
            let at = point_at(pts, &lens, tail + (head - tail) * i as f64 / STEPS as f64);
            cv.overlay(cam, prev, at, col, 0.95 * s);
            prev = at;
        }
    }
}

fn draw_flows(cv: &mut Canvas, cam: &Cam, p: &Params, anim: Anim) {
    let f = anim.flow;
    let ph = anim.phase;
    let (r, leg) = (p.jar_radius, p.leg_gap / 2.0);
    // pump-down: gas leaves the jar sideways, at the base
    route(
        cv,
        cam,
        &[[-r * 0.95, 60.0, 0.0], [-r * 1.5, 60.0, 0.0]],
        PUMP,
        f.pump,
        ph,
    );
    // feed: three nozzles in the base plate, flow up through the jar
    for x in [-260.0, 0.0, 260.0] {
        route(
            cv,
            cam,
            &[[x, 0.0, 0.0], [x, p.wall_height * 0.6, 0.0]],
            FEED,
            f.feed,
            ph,
        );
    }
    // off-gas: out through the base port on the right
    route(
        cv,
        cam,
        &[[r * 0.98, 60.0, 0.0], [r * 1.3, p.wall_height * 0.2, 0.0]],
        EXHAUST,
        f.exhaust,
        ph,
    );
    // current: up one rod, across the bridge, down the other
    route(
        cv,
        cam,
        &[
            [-leg, 0.0, 0.0],
            [-leg, p.rod_top, 0.0],
            [leg, p.rod_top, 0.0],
            [leg, 0.0, 0.0],
        ],
        POWER,
        f.power,
        ph,
    );
}

/// Render one frame at `w` x `h` pixels on a flat `bg` (RGB).
pub fn render(p: &Params, anim: Anim, view: &View, w: usize, h: usize, bg: [u8; 3]) -> RgbaImage {
    let bg_f = bg.map(|c| c as f32 / 255.0);
    let cv = render_canvas(p, anim, view, w, h, bg_f);
    let mut img = RgbaImage::new(w as u32, h as u32);
    for (i, px) in cv.rgb.iter().enumerate() {
        let c = Rgb(px.map(|c| (c.clamp(0.0, 1.0) * 255.0).round() as u8));
        let (x, y) = ((i % w) as u32, (i / w) as u32);
        img.put_pixel(x, y, image::Rgba([c.0[0], c.0[1], c.0[2], 255]));
    }
    img
}

#[cfg(test)]
mod tests {
    use super::*;

    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    #[test]
    fn flat_background_and_solid_scene() {
        let p = Params::default();
        let img = render(&p, clip_anim(&p, 1.0), &View::default(), 160, 90, BG);
        assert_eq!(img.get_pixel(0, 0).0, [BG[0], BG[1], BG[2], 255]);
        assert!(
            img.pixels().any(|px| px.0[..3] != BG),
            "the scene draws something"
        );
    }

    #[test]
    fn hot_rods_glow_and_cold_rods_do_not() {
        let p = Params::default();
        let cold = render(
            &p,
            Anim {
                heat: 0.0,
                rod_d: 20.0,
                ..Default::default()
            },
            &View::default(),
            160,
            90,
            BG,
        );
        let hot = render(
            &p,
            Anim {
                heat: 1.0,
                rod_d: 160.0,
                ..Default::default()
            },
            &View::default(),
            160,
            90,
            BG,
        );
        let warm = |img: &RgbaImage| {
            img.pixels()
                .filter(|px| px.0[0] as u16 > px.0[2] as u16 + 60)
                .count()
        };
        assert!(warm(&hot) > warm(&cold) + 20, "hot rods are orange");
    }

    #[test]
    fn flows_draw_their_routes_in_colour() {
        let p = Params::default();
        let rest = Anim {
            heat: 0.0,
            rod_d: 20.0,
            ..Default::default()
        };
        let flowing = Anim {
            flow: Flow {
                pump: 1.0,
                feed: 1.0,
                exhaust: 1.0,
                power: 1.0,
            },
            phase: 0.3,
            ..rest
        };
        let plain = render(&p, rest, &View::default(), 160, 90, BG);
        let with = render(&p, flowing, &View::default(), 160, 90, BG);
        assert_ne!(plain.as_raw(), with.as_raw(), "the flows change the frame");
        // the pump route is cyan: blue and green high, red low
        assert!(with
            .pixels()
            .any(|px| px.0[0] < 140 && px.0[1] > 120 && px.0[2] > 150));
    }

    #[test]
    fn orbit_clamps_and_zoom_pan_move_the_frame() {
        let mut v = View::default();
        v.orbit(0.0, 10.0);
        assert!(v.pitch <= 1.3);
        v.zoom_by(100.0);
        assert!(v.zoom <= 6.0);
        let p = Params::default();
        let a = render(&p, clip_anim(&p, 1.0), &View::default(), 160, 90, BG);
        let mut panned = View::default();
        panned.pan_by(30.0, 0.0);
        let b = render(&p, clip_anim(&p, 1.0), &panned, 160, 90, BG);
        assert_ne!(a.as_raw(), b.as_raw());
    }
}
