//! Shared kit for the cell scenes: the beat clock, camera moves between beats,
//! glowing particles, glass wireframes and on-picture labels.
//!
//! Everything here is continuous in time, so a scene built from it has no cuts:
//! levels come from `Clock::ramp`, the camera from `shot_at`, and particles fade
//! in and out at the ends of their paths.

use super::{lerp, smooth};
use crate::{add, mul, sub, Cam, Canvas, Col, View, V3};

/// Where a three-beat scene is: `u` runs 0..3 over the loop.
#[derive(Clone, Copy, Debug)]
pub(super) struct Clock {
    pub beat: usize,
    pub local: f64,
}

impl Clock {
    pub fn u(&self) -> f64 {
        self.beat as f64 + self.local
    }

    /// 0 before the window [a, b] of `beat`, 1 after it, eased inside. A level built
    /// from these is continuous across beats.
    pub fn ramp(&self, beat: usize, a: f64, b: f64) -> f64 {
        smooth(beat as f64 + a, beat as f64 + b, self.u())
    }

    /// 1 inside the window [a, b] of `beat`, with soft edges.
    pub fn during(&self, beat: usize, a: f64, b: f64) -> f64 {
        let edge = ((b - a) * 0.2).min(0.12);
        self.ramp(beat, a, a + edge) * (1.0 - self.ramp(beat, b - edge, b))
    }
}

/// A camera position for one beat. `yaw` and `pitch` are where the user's orbit starts.
#[derive(Clone, Copy, Debug)]
pub(super) struct Shot {
    pub target: V3,
    pub dist: f64,
    pub yaw: f64,
    pub pitch: f64,
}

/// Smoothstep from `a` to `b`, for levels computed outside a `Clock`.
pub(super) fn smooth_step(a: f64, b: f64, x: f64) -> f64 {
    smooth(a, b, x)
}

/// The camera at `beat` and `local`: it glides from the previous beat's shot during
/// the first part of the beat, then holds. The last beat glides on into the first.
pub(super) fn shot_at(keys: &[Shot], beat: usize, local: f64) -> Shot {
    shot_glide(keys, beat, local, 0.5)
}

/// As `shot_at`, with the glide taking the first `glide` of the beat.
pub(super) fn shot_glide(keys: &[Shot], beat: usize, local: f64, glide: f64) -> Shot {
    let n = keys.len();
    let (a, b) = (keys[(beat + n - 1) % n], keys[beat % n]);
    let k = smooth(0.0, glide, local);
    Shot {
        target: std::array::from_fn(|i| lerp(a.target[i], b.target[i], k)),
        dist: lerp(a.dist, b.dist, k),
        yaw: lerp(a.yaw, b.yaw, k),
        pitch: lerp(a.pitch, b.pitch, k),
    }
}

/// The camera for `shot`, turned by the user's orbit (measured from the default view).
pub(super) fn camera(shot: &Shot, view: &View, w: usize, h: usize) -> Cam {
    let home = View::default();
    let turned = View {
        yaw: shot.yaw + view.yaw - home.yaw,
        pitch: shot.pitch + view.pitch - home.pitch,
        ..*view
    };
    let mut cam = Cam::orbit_at(&turned, shot.target, shot.dist, w, h);
    fit_width(&mut cam, w, h);
    cam
}

/// The lens is sized by frame height. In a narrow pane (the zoom beside its notes is
/// about 1.16:1) scale it down so a scene framed for that shape still fits the width.
pub(super) fn fit_width(cam: &mut Cam, w: usize, h: usize) {
    cam.focal *= (w as f64 / (h as f64 * 1.16)).min(1.0);
}

// the palette every scene shares
pub(super) const ORANGE: Col = [1.0, 0.72, 0.42];
pub(super) const CYAN: Col = [0.55, 0.91, 0.99];
pub(super) const PINK: Col = [1.0, 0.47, 0.78];
pub(super) const PURPLE: Col = [0.74, 0.58, 0.98];
pub(super) const GREEN: Col = [0.31, 0.92, 0.50];
pub(super) const YELLOW: Col = [0.95, 0.98, 0.40];
pub(super) const TEXT: Col = [0.97, 0.97, 0.95];
pub(super) const GLASS: Col = [0.62, 0.80, 0.92];
pub(super) const PLATE: Col = [0.86, 0.87, 0.84];
pub(super) const METAL: Col = [0.55, 0.56, 0.60];
pub(super) const STEEL: Col = [0.20, 0.21, 0.24];
pub(super) const QUIET: Col = [0.33, 0.35, 0.42];
pub(super) const NO_GLOW: Col = [0.0; 3];

pub(super) fn mix(a: Col, b: Col, k: f64) -> Col {
    let k = k.clamp(0.0, 1.0) as f32;
    std::array::from_fn(|i| a[i] + (b[i] - a[i]) * k)
}

pub(super) fn scaled(c: Col, k: f64) -> Col {
    c.map(|v| v * k as f32)
}

/// Position at fraction `s` (0..1) of the length of a polyline.
pub(super) fn along(pts: &[V3], s: f64) -> V3 {
    let len = |a: V3, b: V3| crate::dot(sub(b, a), sub(b, a)).sqrt();
    let total: f64 = pts.windows(2).map(|w| len(w[0], w[1])).sum();
    let mut left = s.clamp(0.0, 1.0) * total;
    for w in pts.windows(2) {
        let l = len(w[0], w[1]);
        if left <= l && l > 0.0 {
            return add(w[0], mul(sub(w[1], w[0]), left / l));
        }
        left -= l;
    }
    *pts.last().unwrap_or(&[0.0; 3])
}

/// An anti-aliased glowing dot of world radius `r`, hidden by solids in front of it.
pub(super) fn dot(cv: &mut Canvas, cam: &Cam, p: V3, r: f64, col: Col, alpha: f64) {
    if alpha <= 0.004 {
        return;
    }
    let Some((x, y, inv)) = cam.project(p) else {
        return;
    };
    let pr = (r * cam.focal * inv).max(1.2);
    let depth = (1.0 / inv) as f32;
    let (x0, x1) = ((x - pr - 1.0).floor().max(0.0), (x + pr + 1.0).ceil());
    let (y0, y1) = ((y - pr - 1.0).floor().max(0.0), (y + pr + 1.0).ceil());
    for py in y0 as usize..(y1 as usize).min(cv.h) {
        for px in x0 as usize..(x1 as usize).min(cv.w) {
            let d = ((px as f64 + 0.5 - x).powi(2) + (py as f64 + 0.5 - y).powi(2)).sqrt();
            let cover = (pr + 0.5 - d).clamp(0.0, 1.0);
            let idx = py * cv.w + px;
            if cover <= 0.0 || depth >= cv.z[idx] {
                continue;
            }
            let a = (cover * alpha) as f32;
            for k in 0..3 {
                cv.rgb[idx][k] = cv.rgb[idx][k] * (1.0 - a) + col[k] * a;
            }
        }
    }
}

/// How much beat `i` of `n` holds the spotlight: rises as the beat starts and falls as
/// the next one starts, so the focus crossfades instead of cutting.
pub(super) fn spotlight(c: &Clock, i: usize, n: usize) -> f64 {
    if c.beat == i {
        smooth(0.0, 0.25, c.local)
    } else if (i + 1) % n == c.beat {
        1.0 - smooth(0.0, 0.25, c.local)
    } else {
        0.0
    }
}

/// `n` particles travelling along `pts` from start to end. `clock` moves them (one
/// path length per unit); each fades in at the start and out at the end of the path.
pub(super) fn particles(
    cv: &mut Canvas,
    cam: &Cam,
    pts: &[V3],
    n: usize,
    clock: f64,
    r: f64,
    col: Col,
    strength: f64,
) {
    if strength <= 0.004 {
        return;
    }
    for i in 0..n {
        let s = (clock + i as f64 / n as f64).rem_euclid(1.0);
        let fade = (std::f64::consts::PI * s).sin().sqrt();
        dot(cv, cam, along(pts, s), r, col, strength * fade);
    }
}

/// A horizontal circle in glass.
pub(super) fn ring(cv: &mut Canvas, cam: &Cam, c: V3, r: f64, col: Col, alpha: f32) {
    const SEG: usize = 64;
    let at = |i: usize| {
        let th = std::f64::consts::TAU * i as f64 / SEG as f64;
        [c[0] + r * th.cos(), c[1], c[2] + r * th.sin()]
    };
    for i in 0..SEG {
        cv.line(cam, at(i), at(i + 1), col, alpha);
    }
}

/// A glass cylinder standing on `base`, height `h`: rings and meridians, as the bell jar.
pub(super) fn glass_cyl(cv: &mut Canvas, cam: &Cam, base: V3, r: f64, h: f64, col: Col, alpha: f32) {
    let rings = ((h / 60.0).round() as usize).clamp(2, 8);
    for k in 0..=rings {
        let y = base[1] + h * k as f64 / rings as f64;
        ring(cv, cam, [base[0], y, base[2]], r, col, alpha);
    }
    for k in 0..16 {
        let th = std::f64::consts::TAU * k as f64 / 16.0;
        let (x, z) = (base[0] + r * th.cos(), base[2] + r * th.sin());
        cv.line(cam, [x, base[1], z], [x, base[1] + h, z], col, alpha);
    }
}

/// The edges of an axis-aligned box, in glass.
pub(super) fn glass_box(cv: &mut Canvas, cam: &Cam, lo: V3, hi: V3, col: Col, alpha: f32) {
    let c = |x: bool, y: bool, z: bool| {
        [
            if x { hi[0] } else { lo[0] },
            if y { hi[1] } else { lo[1] },
            if z { hi[2] } else { lo[2] },
        ]
    };
    for a in [false, true] {
        for b in [false, true] {
            cv.line(cam, c(false, a, b), c(true, a, b), col, alpha);
            cv.line(cam, c(a, false, b), c(a, true, b), col, alpha);
            cv.line(cam, c(a, b, false), c(a, b, true), col, alpha);
        }
    }
}

/// Sphere centres on a square lattice inside a disc of radius `r`, one layer per
/// entry of `ys`, nearest the axis first. Charge fills from the centre and drains
/// from the rim, so losing it looks like it leaving through the edges.
pub(super) fn disc_lattice(r: f64, pitch: f64, ys: &[f64]) -> Vec<V3> {
    let n = (r / pitch).ceil() as i32;
    let mut pts = Vec::new();
    for &y in ys {
        for i in -n..=n {
            for j in -n..=n {
                let (x, z) = (i as f64 * pitch, j as f64 * pitch);
                if x * x + z * z <= r * r {
                    pts.push([x, y, z]);
                }
            }
        }
    }
    pts.sort_by(|a, b| {
        let (da, db) = (a[0] * a[0] + a[2] * a[2], b[0] * b[0] + b[2] * b[2]);
        da.partial_cmp(&db).unwrap_or(std::cmp::Ordering::Equal)
    });
    pts
}

/// How lit slot `rank` of `n` is at charge `level`: 0 empty .. 1 full. Several slots
/// are part-lit at once, so charge changes gradually and no sphere pops.
pub(super) fn slot_fill(rank: usize, n: usize, level: f64) -> f64 {
    let soft = (n as f64 * 0.08).max(1.5);
    ((level * (n as f64 + soft) - rank as f64) / soft).clamp(0.0, 1.0)
}

// ---- labels ------------------------------------------------------------------

/// 5 x 7 glyphs, one row per byte, low 5 bits, top row first.
fn glyph(c: char) -> [u8; 9] {
    match c {
        'A' => [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11, 0x00, 0x00],
        'B' => [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E, 0x00, 0x00],
        'C' => [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E, 0x00, 0x00],
        'D' => [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E, 0x00, 0x00],
        'E' => [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F, 0x00, 0x00],
        'F' => [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10, 0x00, 0x00],
        'G' => [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F, 0x00, 0x00],
        'H' => [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11, 0x00, 0x00],
        'I' => [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E, 0x00, 0x00],
        'J' => [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C, 0x00, 0x00],
        'K' => [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11, 0x00, 0x00],
        'L' => [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F, 0x00, 0x00],
        'M' => [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11, 0x00, 0x00],
        'N' => [0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11, 0x00, 0x00],
        'O' => [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E, 0x00, 0x00],
        'P' => [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10, 0x00, 0x00],
        'Q' => [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D, 0x00, 0x00],
        'R' => [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11, 0x00, 0x00],
        'S' => [0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E, 0x00, 0x00],
        'T' => [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x00],
        'U' => [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E, 0x00, 0x00],
        'V' => [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04, 0x00, 0x00],
        'W' => [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11, 0x00, 0x00],
        'X' => [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11, 0x00, 0x00],
        'Y' => [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04, 0x00, 0x00],
        'Z' => [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F, 0x00, 0x00],
        '0' => [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E, 0x00, 0x00],
        '1' => [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E, 0x00, 0x00],
        '2' => [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F, 0x00, 0x00],
        '3' => [0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E, 0x00, 0x00],
        '4' => [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02, 0x00, 0x00],
        '5' => [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E, 0x00, 0x00],
        '6' => [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E, 0x00, 0x00],
        '7' => [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08, 0x00, 0x00],
        '8' => [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E, 0x00, 0x00],
        '9' => [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C, 0x00, 0x00],
        '/' => [0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10, 0x00, 0x00],
        '-' => [0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00],
        '+' => [0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00, 0x00, 0x00],
        ':' => [0x00, 0x04, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00],
        '.' => [0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C, 0x00, 0x00],
        '^' => [0x04, 0x0A, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        '=' => [0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x00],
        '(' => [0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02, 0x00, 0x00],
        ')' => [0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08, 0x00, 0x00],
        ',' => [0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08, 0x00, 0x00],
        'a' => [0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F, 0x00, 0x00],
        'b' => [0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x1E, 0x00, 0x00],
        'c' => [0x00, 0x00, 0x0E, 0x10, 0x10, 0x11, 0x0E, 0x00, 0x00],
        'd' => [0x01, 0x01, 0x0D, 0x13, 0x11, 0x11, 0x0F, 0x00, 0x00],
        'e' => [0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E, 0x00, 0x00],
        'f' => [0x06, 0x09, 0x08, 0x1C, 0x08, 0x08, 0x08, 0x00, 0x00],
        'g' => [0x00, 0x00, 0x0F, 0x11, 0x11, 0x11, 0x0F, 0x01, 0x0E],
        'h' => [0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x11, 0x00, 0x00],
        'i' => [0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E, 0x00, 0x00],
        'j' => [0x02, 0x00, 0x06, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C],
        'k' => [0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12, 0x00, 0x00],
        'l' => [0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E, 0x00, 0x00],
        'm' => [0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15, 0x00, 0x00],
        'n' => [0x00, 0x00, 0x16, 0x19, 0x11, 0x11, 0x11, 0x00, 0x00],
        'o' => [0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E, 0x00, 0x00],
        'p' => [0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x1E, 0x10, 0x10],
        'q' => [0x00, 0x00, 0x0F, 0x11, 0x11, 0x11, 0x0F, 0x01, 0x01],
        'r' => [0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10, 0x00, 0x00],
        's' => [0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E, 0x00, 0x00],
        't' => [0x08, 0x08, 0x1C, 0x08, 0x08, 0x09, 0x06, 0x00, 0x00],
        'u' => [0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D, 0x00, 0x00],
        'v' => [0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04, 0x00, 0x00],
        'w' => [0x00, 0x00, 0x11, 0x11, 0x15, 0x15, 0x0A, 0x00, 0x00],
        'x' => [0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x00, 0x00],
        'y' => [0x00, 0x00, 0x11, 0x11, 0x11, 0x11, 0x0F, 0x01, 0x0E],
        'z' => [0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F, 0x00, 0x00],
        '\'' => [0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        '"' => [0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        ';' => [0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08, 0x00, 0x00],
        '!' => [0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04, 0x00, 0x00],
        '?' => [0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04, 0x00, 0x00],
        '%' => [0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03, 0x00, 0x00],
        '*' => [0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00, 0x00, 0x00],
        '<' => [0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02, 0x00, 0x00],
        '>' => [0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08, 0x00, 0x00],
        '[' => [0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E, 0x00, 0x00],
        ']' => [0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E, 0x00, 0x00],
        '&' => [0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D, 0x00, 0x00],
        '_' => [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x00, 0x00],
        '~' => [0x00, 0x00, 0x08, 0x15, 0x02, 0x00, 0x00, 0x00, 0x00],
        _ => [0; 9],
    }
}

fn blend(cv: &mut Canvas, x: i64, y: i64, col: Col, a: f32) {
    if x < 0 || y < 0 || x >= cv.w as i64 || y >= cv.h as i64 {
        return;
    }
    let c = &mut cv.rgb[y as usize * cv.w + x as usize];
    for k in 0..3 {
        c[k] = c[k] * (1.0 - a) + col[k] * a;
    }
}

/// Text pixel size for this frame: labels stay a similar size on the screen.
pub(super) fn text_scale(cv: &Canvas) -> i64 {
    ((cv.h as f64 / 300.0).round() as i64).max(1)
}

pub(super) fn text_w(s: &str, scale: i64) -> i64 {
    s.chars().count() as i64 * 6 * scale - scale
}

/// Glyphs at pixel `x`, `y` (top left), `scale` pixels per font pixel, as written.
pub(super) fn glyphs(cv: &mut Canvas, x: i64, y: i64, s: &str, col: Col, a: f32, scale: i64) {
    for (i, c) in s.chars().enumerate() {
        let rows = glyph(c);
        let gx = x + i as i64 * 6 * scale;
        for (ry, bits) in rows.iter().enumerate() {
            for rx in 0..5 {
                if bits >> (4 - rx) & 1 == 0 {
                    continue;
                }
                for sy in 0..scale {
                    for sx in 0..scale {
                        blend(cv, gx + rx * scale + sx, y + ry as i64 * scale + sy, col, a);
                    }
                }
            }
        }
    }
}

/// A filled rectangle, blended.
pub(super) fn fill_rect(cv: &mut Canvas, x0: i64, y0: i64, x1: i64, y1: i64, col: Col, a: f32) {
    for py in y0.max(0)..y1.min(cv.h as i64) {
        for px in x0.max(0)..x1.min(cv.w as i64) {
            blend(cv, px, py, col, a);
        }
    }
}

/// Text at pixel `x`, `y` (top left), upper-cased, over a dim plate so it reads on anything.
pub(super) fn text(cv: &mut Canvas, x: i64, y: i64, s: &str, col: Col, alpha: f64) {
    let scale = text_scale(cv);
    let a = alpha.clamp(0.0, 1.0) as f32;
    if a <= 0.004 {
        return;
    }
    let s = s.to_ascii_uppercase();
    let pad = 2 * scale;
    fill_rect(cv, x - pad, y - pad, x + text_w(&s, scale) + pad, y + 7 * scale + pad, BG, 0.72 * a);
    glyphs(cv, x, y, &s, col, a, scale);
}

/// The frame's background, for plates behind text.
pub(super) const BG: Col = [0.157, 0.165, 0.212];

/// A flat line in screen pixels, for labels and the on-picture traces.
pub(super) fn screen_line(cv: &mut Canvas, a: (f64, f64), b: (f64, f64), col: Col, alpha: f64, w: i64) {
    let n = (b.0 - a.0).abs().max((b.1 - a.1).abs()).ceil().max(1.0) as usize;
    for i in 0..=n {
        let t = i as f64 / n as f64;
        let (x, y) = (lerp(a.0, b.0, t) as i64, lerp(a.1, b.1, t) as i64);
        for dy in 0..w {
            for dx in 0..w {
                blend(cv, x + dx, y + dy, col, alpha as f32);
            }
        }
    }
}

/// Screen rectangle in pixels: x0, y0, x1, y1.
pub(super) type Rect = (i64, i64, i64, i64);

/// A name on a part: text offset from world point `at` by `off` (fractions of the
/// frame height), joined to the part by a thin leader, and kept inside the frame.
/// Returns where the text went, so callouts can keep clear of it.
pub(super) fn label(
    cv: &mut Canvas,
    cam: &Cam,
    at: V3,
    off: (f64, f64),
    s: &str,
    col: Col,
    alpha: f64,
) -> Option<Rect> {
    let (ax, ay, _) = cam.project(at)?;
    // a part out of frame keeps its name off, rather than piling it on the edge
    if ax < 0.0 || ay < 0.0 || ax >= cv.w as f64 || ay >= cv.h as f64 {
        return None;
    }
    let scale = text_scale(cv);
    let h = cv.h as f64;
    let w = text_w(s, scale);
    let tall = 7 * scale;
    let x = ((ax + off.0 * h) as i64).clamp(3 * scale, (cv.w as i64 - w - 3 * scale).max(3 * scale));
    let y = ((ay + off.1 * h) as i64).clamp(3 * scale, (cv.h as i64 - tall - 3 * scale).max(3 * scale));
    let rect = (x - 2 * scale, y - 2 * scale, x + w + 2 * scale, y + tall + 2 * scale);
    if alpha <= 0.004 {
        return None;
    }
    // the leader meets the text at whichever end is nearer the part
    let end_x = if (ax as i64) < x { x - 2 * scale } else { x + w + scale };
    let end = (end_x as f64, (y + tall / 2) as f64);
    if (end.0 - ax).abs() + (end.1 - ay).abs() > 4.0 {
        screen_line(cv, (ax, ay), end, col, 0.55 * alpha, 1);
    }
    text(cv, x, y, s, col, alpha);
    Some(rect)
}
