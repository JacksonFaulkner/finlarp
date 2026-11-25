//! Scenes described as data rather than code: the Z screen's diagrams, which Claude writes
//! as JSON while it explains something. A scene is a list of primitive parts (boxes,
//! cylinders, spheres; solid or glass) in any units, plus flows (animated dashes along a
//! path). The scene is scaled to a fixed size and centred, so the camera fits it whatever
//! units the author used.

use image::RgbaImage;

use super::stage::{glass_box, label_w, text_scale, text_w};
use super::push_box;
use crate::{add, cross, mul, norm, sub, Cam, Canvas, Tri, View, V3};

/// The shape of one part, in the author's units, Y up.
#[derive(Clone, Debug, PartialEq)]
pub enum SpecShape {
    /// Axis-aligned box between two corners.
    Box { lo: [f64; 3], hi: [f64; 3] },
    /// Cylinder from `a` to `b`, radius `r`.
    Cyl { a: [f64; 3], b: [f64; 3], r: f64 },
    /// Sphere at `c`, radius `r`.
    Sphere { c: [f64; 3], r: f64 },
}

#[derive(Clone, Debug, PartialEq)]
pub struct SpecPart {
    pub shape: SpecShape,
    /// Linear RGB, 0..1.
    pub color: [f32; 3],
    /// 0 (lit by the scene light) .. 1 (glows its own colour).
    pub glow: f32,
    /// Drawn as a translucent wireframe, so parts inside show through.
    pub glass: bool,
    /// The name labelled on the picture; what notes and rings pin to.
    pub name: Option<String>,
    /// Where the label sits from the part, as fractions of the frame height. None picks
    /// a side away from the scene's centre.
    pub label_off: Option<(f64, f64)>,
}

/// Dashes marching along `path`, start to end.
#[derive(Clone, Debug, PartialEq)]
pub struct SpecFlow {
    pub path: Vec<[f64; 3]>,
    pub color: [f32; 3],
    pub name: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Default)]
pub struct SpecScene {
    pub parts: Vec<SpecPart>,
    pub flows: Vec<SpecFlow>,
}

/// Scenes are scaled so their bounding sphere has this radius before the camera sees them,
/// which keeps perspective the same whatever units the author used.
const NORM_R: f64 = 1000.0;
/// How much of the frame the scene may cover, each way: the rest is room for labels.
const FRAME_X: f64 = 0.92;
const FRAME_Y: f64 = 0.92;
const DIST: f64 = 3600.0;
const SEG: usize = 28;

impl SpecShape {
    fn bounds(&self) -> ([f64; 3], [f64; 3]) {
        match *self {
            SpecShape::Box { lo, hi } => (
                [lo[0].min(hi[0]), lo[1].min(hi[1]), lo[2].min(hi[2])],
                [lo[0].max(hi[0]), lo[1].max(hi[1]), lo[2].max(hi[2])],
            ),
            SpecShape::Cyl { a, b, r } => (
                [a[0].min(b[0]) - r, a[1].min(b[1]) - r, a[2].min(b[2]) - r],
                [a[0].max(b[0]) + r, a[1].max(b[1]) + r, a[2].max(b[2]) + r],
            ),
            SpecShape::Sphere { c, r } => ([c[0] - r, c[1] - r, c[2] - r], [c[0] + r, c[1] + r, c[2] + r]),
        }
    }

    fn center(&self) -> V3 {
        let (lo, hi) = self.bounds();
        mul(add(lo, hi), 0.5)
    }
}

/// Maps the author's coordinates into the renderer's: centred on the scene, radius NORM_R.
struct Fit {
    c: V3,
    k: f64,
}

impl Fit {
    fn new(s: &SpecScene) -> Fit {
        let mut lo = [f64::INFINITY; 3];
        let mut hi = [f64::NEG_INFINITY; 3];
        let mut grow = |a: [f64; 3], b: [f64; 3]| {
            for i in 0..3 {
                lo[i] = lo[i].min(a[i]);
                hi[i] = hi[i].max(b[i]);
            }
        };
        for p in &s.parts {
            let (a, b) = p.shape.bounds();
            grow(a, b);
        }
        for f in &s.flows {
            for &q in &f.path {
                grow(q, q);
            }
        }
        if !lo[0].is_finite() {
            return Fit { c: [0.0; 3], k: 1.0 };
        }
        let c = mul(add(lo, hi), 0.5);
        let half = mul(sub(hi, lo), 0.5);
        let r = (half[0] * half[0] + half[1] * half[1] + half[2] * half[2]).sqrt();
        Fit { c, k: NORM_R / r.max(1e-9) }
    }
    fn p(&self, q: [f64; 3]) -> V3 {
        mul(sub(q, self.c), self.k)
    }
    fn len(&self, r: f64) -> f64 {
        r * self.k
    }
}

fn push_sphere(m: &mut Vec<Tri>, c: V3, r: f64, base: [f32; 3], emit: [f32; 3]) {
    let (rings, seg) = (12, SEG);
    let at = |i: usize, j: usize| {
        let phi = std::f64::consts::PI * i as f64 / rings as f64;
        let th = std::f64::consts::TAU * j as f64 / seg as f64;
        add(c, mul([phi.sin() * th.cos(), phi.cos(), phi.sin() * th.sin()], r))
    };
    for i in 0..rings {
        for j in 0..seg {
            let (a, b, cc, d) = (at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1));
            m.push(Tri { p: [a, b, cc], base, emit });
            m.push(Tri { p: [a, cc, d], base, emit });
        }
    }
}

/// Two unit vectors square to `axis` and to each other.
fn basis(axis: V3) -> (V3, V3) {
    let reference = if axis[1].abs() < 0.9 { [0.0, 1.0, 0.0] } else { [1.0, 0.0, 0.0] };
    let e1 = norm(cross(axis, reference));
    (e1, cross(axis, e1))
}

fn circle(cv: &mut Canvas, cam: &Cam, c: V3, axis: V3, r: f64, col: [f32; 3], alpha: f32) {
    let (e1, e2) = basis(axis);
    let at = |i: usize| {
        let th = std::f64::consts::TAU * i as f64 / 48.0;
        add(c, mul(add(mul(e1, th.cos()), mul(e2, th.sin())), r))
    };
    for i in 0..48 {
        cv.line(cam, at(i), at(i + 1), col, alpha);
    }
}

fn glass_part(cv: &mut Canvas, cam: &Cam, fit: &Fit, part: &SpecPart) {
    let (col, alpha) = (part.color, 0.45);
    match part.shape {
        SpecShape::Box { lo, hi } => glass_box(cv, cam, fit.p(lo), fit.p(hi), col, alpha),
        SpecShape::Cyl { a, b, r } => {
            let (a, b, r) = (fit.p(a), fit.p(b), fit.len(r));
            let axis = norm(sub(b, a));
            let rings = 4;
            for k in 0..=rings {
                let c = add(a, mul(sub(b, a), k as f64 / rings as f64));
                circle(cv, cam, c, axis, r, col, alpha);
            }
            let (e1, e2) = basis(axis);
            for k in 0..12 {
                let th = std::f64::consts::TAU * k as f64 / 12.0;
                let off = mul(add(mul(e1, th.cos()), mul(e2, th.sin())), r);
                cv.line(cam, add(a, off), add(b, off), col, alpha);
            }
        }
        SpecShape::Sphere { c, r } => {
            let (c, r) = (fit.p(c), fit.len(r));
            for axis in [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]] {
                circle(cv, cam, c, axis, r, col, alpha);
            }
        }
    }
}

fn solids(fit: &Fit, s: &SpecScene) -> Vec<Tri> {
    let mut m = Vec::new();
    for part in s.parts.iter().filter(|p| !p.glass) {
        let g = part.glow.clamp(0.0, 1.0);
        let base = part.color.map(|c| c * (1.0 - 0.6 * g));
        let emit = part.color.map(|c| c * g);
        match part.shape {
            SpecShape::Box { lo, hi } => {
                let (a, b) = (fit.p(lo), fit.p(hi));
                let lo = [a[0].min(b[0]), a[1].min(b[1]), a[2].min(b[2])];
                let hi = [a[0].max(b[0]), a[1].max(b[1]), a[2].max(b[2])];
                push_box(&mut m, lo, hi, base, emit);
            }
            SpecShape::Cyl { a, b, r } => {
                crate::push_tube(&mut m, fit.p(a), fit.p(b), fit.len(r), SEG, base, emit, true)
            }
            SpecShape::Sphere { c, r } => push_sphere(&mut m, fit.p(c), fit.len(r), base, emit),
        }
    }
    m
}

/// How thick, in pixels, the line from a label to its part is: thin ones got lost.
const LEADER: i64 = 3;

/// How bright a label must be (relative luminance) to read on the dark background.
const LABEL_LUMA: f32 = 0.6;

/// A part's label colour: the part's own colour, so the name says which part it is, lifted
/// toward white until it reads on the dark background (a dark blue part gets a light blue name).
fn label_col(c: [f32; 3]) -> [f32; 3] {
    let c = c.map(|v| v.clamp(0.0, 1.0));
    let luma = |c: [f32; 3]| 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    let l = luma(c);
    if l >= LABEL_LUMA {
        return c;
    }
    let k = (LABEL_LUMA - l) / (1.0 - l);
    c.map(|v| v + (1.0 - v) * k)
}

/// One frame of `s` seen from `view`. `phase` (0..1, wrapping) moves the flow dashes.
pub fn render_spec(s: &SpecScene, view: &View, phase: f64, w: usize, h: usize, bg: [u8; 3]) -> RgbaImage {
    let fit = Fit::new(s);
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    // part names grow and shrink with the zoom, as the parts do
    cv.text_zoom = view.zoom;
    let cam = framed_cam(s, &fit, view, w, h);
    crate::rasterize(&mut cv, &cam, solids(&fit, s));
    for part in s.parts.iter().filter(|p| p.glass) {
        glass_part(&mut cv, &cam, &fit, part);
    }
    for f in &s.flows {
        let pts: Vec<V3> = f.path.iter().map(|&q| fit.p(q)).collect();
        crate::route(&mut cv, &cam, &pts, f.color, 1.0, phase.rem_euclid(1.0));
    }
    // names last, so they read over glass and flows
    let mut names: Vec<(V3, &str, [f32; 3], Option<(f64, f64)>)> = Vec::new();
    for part in &s.parts {
        if let Some(name) = part.name.as_deref() {
            let col = label_col(part.color);
            names.push((fit.p(part.shape.center()), name, col, part.label_off));
        }
    }
    for f in &s.flows {
        if let (Some(name), Some(&q)) = (f.name.as_deref(), f.path.get(f.path.len() / 2)) {
            names.push((fit.p(q), name, f.color, None));
        }
    }
    let mut placed: Vec<Rect> = Vec::new();
    for (at, name, col, fixed) in names {
        let off = fixed.or_else(|| free_spot(&cv, &cam, at, name, &placed));
        if let Some(off) = off {
            if let Some(r) = label_w(&mut cv, &cam, at, off, name, col, 1.0, LEADER) {
                placed.push(r);
            }
        }
    }
    crate::to_image(&cv)
}

type Rect = (i64, i64, i64, i64);

/// Every point the scene's outline passes through, in renderer units.
fn outline(s: &SpecScene, fit: &Fit) -> Vec<V3> {
    let mut pts = Vec::new();
    for p in &s.parts {
        let (lo, hi) = p.shape.bounds();
        for i in 0..8 {
            let pick = |k: usize| if i >> k & 1 == 1 { hi[k] } else { lo[k] };
            pts.push(fit.p([pick(0), pick(1), pick(2)]));
        }
    }
    for f in &s.flows {
        pts.extend(f.path.iter().map(|&q| fit.p(q)));
    }
    pts
}

/// The camera for `view`, its lens set so the scene fills FRAME_X x FRAME_Y of the frame
/// at zoom 1. The fit is the tightest over eight headings at the view's pitch, so turning
/// the scene never pushes it out of frame and its size holds steady while it turns.
fn framed_cam(s: &SpecScene, fit: &Fit, view: &View, w: usize, h: usize) -> Cam {
    let pts = outline(s, fit);
    let (hw, hh) = (w as f64 * 0.5 * FRAME_X, h as f64 * 0.5 * FRAME_Y);
    let mut scale = f64::INFINITY;
    for i in 0..8 {
        let probe = View {
            yaw: view.yaw + std::f64::consts::TAU * i as f64 / 8.0,
            zoom: 1.0,
            pan: [0.0, 0.0],
            ..*view
        };
        let cam = Cam::orbit_at(&probe, [0.0; 3], DIST, w, h);
        for &q in &pts {
            let Some((x, y, _)) = cam.project(q) else { continue };
            let (dx, dy) = ((x - cam.cx).abs(), (y - cam.cy).abs());
            if dx > 1e-6 {
                scale = scale.min(hw / dx);
            }
            if dy > 1e-6 {
                scale = scale.min(hh / dy);
            }
        }
    }
    let mut cam = Cam::orbit_at(view, [0.0; 3], DIST, w, h);
    if scale.is_finite() {
        cam.focal *= scale;
    }
    cam
}

/// A label offset for `name` at `at` whose text clears every label already placed: the
/// side away from the frame's centre first, then the other, stepping up and down.
/// None (no label) when the part is off screen.
fn free_spot(cv: &Canvas, cam: &Cam, at: V3, name: &str, placed: &[Rect]) -> Option<(f64, f64)> {
    let (ax, ay, _) = cam.project(at)?;
    let (w, h) = (cv.w as f64, cv.h as f64);
    let scale = text_scale(cv);
    let tw = text_w(name, scale) as f64;
    let tall = (7 * scale) as f64;
    let pad = (3 * scale) as f64;
    // the rectangle `label` will use for this offset (same clamping)
    let rect = |off: (f64, f64)| -> Rect {
        let x = (ax + off.0 * h).clamp(pad, (w - tw - pad).max(pad));
        let y = (ay + off.1 * h).clamp(pad, (h - tall - pad).max(pad));
        let m = 2.0 * scale as f64;
        ((x - m) as i64, (y - m) as i64, (x + tw + m) as i64, (y + tall + m) as i64)
    };
    let clear = |r: Rect| placed.iter().all(|p| r.2 < p.0 || r.0 > p.2 || r.3 < p.1 || r.1 > p.3);
    let right = ax >= w / 2.0;
    let gap = 0.08;
    // text left of the part ends `gap` before it
    let side_x = |r: bool| if r { gap } else { -gap - tw / h };
    let rises = [-0.03, -0.08, 0.03, -0.13, 0.08, -0.18, 0.13, -0.23, 0.18];
    for r in [right, !right] {
        for &dy in &rises {
            let off = (side_x(r), dy);
            if clear(rect(off)) {
                return Some(off);
            }
        }
    }
    Some((side_x(right), -0.03))
}

#[cfg(test)]
mod tests {
    use super::*;

    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn part(shape: SpecShape, name: &str) -> SpecPart {
        SpecPart {
            shape,
            color: [0.4, 0.6, 0.9],
            glow: 0.0,
            glass: false,
            name: Some(name.into()),
            label_off: None,
        }
    }

    #[test]
    fn labels_take_their_parts_colour_bright_enough_to_read() {
        // a light part keeps its colour exactly
        assert_eq!(label_col([0.4, 0.85, 0.95]), [0.4, 0.85, 0.95]);
        // a dark blue part's name stays blue (blue still leads) but bright enough to read
        let c = label_col([0.27, 0.45, 0.78]);
        let luma = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
        assert!(luma >= LABEL_LUMA - 1e-4, "{c:?}");
        assert!(c[2] > c[1] && c[1] > c[0], "{c:?}");
        // different parts get different label colours
        assert_ne!(label_col([0.55, 0.35, 0.75]), label_col([1.0, 0.65, 0.25]));
    }

    #[test]
    fn any_units_fill_the_frame_and_names_register() {
        // the same scene in microns and in metres draws the same picture
        let scene = |k: f64| SpecScene {
            parts: vec![
                part(SpecShape::Box { lo: [-k, 0.0, -k], hi: [k, 0.2 * k, k] }, "base"),
                part(SpecShape::Cyl { a: [0.0, 0.2 * k, 0.0], b: [0.0, k, 0.0], r: 0.1 * k }, "post"),
                part(SpecShape::Sphere { c: [0.0, 1.2 * k, 0.0], r: 0.2 * k }, "ball"),
            ],
            flows: vec![SpecFlow { path: vec![[-k, k, 0.0], [k, k, 0.0]], color: [1.0, 0.8, 0.3], name: None }],
        };
        let a = render_spec(&scene(1e-6), &View::default(), 0.3, 200, 120, BG);
        let b = render_spec(&scene(5.0), &View::default(), 0.3, 200, 120, BG);
        let drawn = a.pixels().filter(|p| p.0[..3] != BG).count();
        assert!(drawn > 200 * 120 / 20, "scene covers the frame: {drawn}");
        let diff = a.pixels().zip(b.pixels()).filter(|(x, y)| x != y).count();
        assert!(diff < 200 * 120 / 100, "scale independent: {diff}");
        let names = crate::seen_names();
        for n in ["base", "post", "ball"] {
            assert!(names.iter().any(|x| x == n), "{n} in {names:?}");
        }
    }

    #[test]
    fn empty_scene_is_background() {
        let img = render_spec(&SpecScene::default(), &View::default(), 0.0, 40, 20, BG);
        assert!(img.pixels().all(|p| p.0[..3] == BG));
    }
}
