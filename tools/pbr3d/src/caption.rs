//! Beat text set inside the picture with a real font (JetBrains Mono, OFL; assets/fonts), sized
//! from the frame so it reads the same at any resolution. Two pieces:
//!
//! - `compose`: the 3D picture on the left, a text panel on the right with the step counter,
//!   the caption, what is happening, what to look for, and the key numbers. The type size is the
//!   largest that fits the panel (down to a floor), so nothing is cut at small sizes until the
//!   floor is reached; then the last key numbers drop first.
//! - `Tags`: short tags pinned to a point in the picture with a leader line, for the
//!   `label:` empties a Blender scene carries (see `scene_gltf::Scene::labels`).

use ab_glyph::{Font, FontRef, PxScale, ScaleFont};
use image::RgbaImage;
use std::sync::OnceLock;

const INK: [u8; 3] = [222, 226, 232];
const DIM: [u8; 3] = [128, 136, 156];
const HEAD: [u8; 3] = [240, 196, 118];
const LOOK: [u8; 3] = [170, 205, 236];
const PANEL: [u8; 3] = [40, 42, 54];
const RULE: [u8; 3] = [52, 56, 70];
const TAG: [u8; 3] = [16, 18, 24];

/// Share of the frame width the text panel takes.
pub const PANEL_FRAC: f32 = 0.36;

fn font() -> &'static FontRef<'static> {
    static F: OnceLock<FontRef<'static>> = OnceLock::new();
    F.get_or_init(|| {
        FontRef::try_from_slice(include_bytes!("../assets/fonts/JetBrainsMono-Regular.ttf"))
            .expect("JetBrains Mono parses")
    })
}

/// The text for one beat's panel.
pub struct Panel<'a> {
    /// (this beat, beat count), shown 1-based
    pub step: (usize, usize),
    pub head: &'a str,
    pub what: &'a str,
    pub look: &'a str,
    pub facts: &'a [&'a str],
}

/// Width of the 3D area for a frame `w` wide: render the scene at this width, then `compose`.
pub fn scene_width(w: u32) -> u32 {
    ((w as f32) * (1.0 - PANEL_FRAC)).round() as u32
}

/// One line of laid-out text: its colour, size multiplier and indent (in advances).
struct Line {
    text: String,
    col: [u8; 3],
    size: f32,
    indent: f32,
}

/// Lays the panel out at body size `px` for a column `col_w` wide. Returns the lines and the
/// height they take; `gap` lines are empty spacers.
fn layout(p: &Panel, px: f32, col_w: f32, facts: usize) -> (Vec<Option<Line>>, f32) {
    let adv = advance(px);
    let mut out: Vec<Option<Line>> = Vec::new();
    let push = |out: &mut Vec<Option<Line>>, text: &str, col, size: f32, indent: f32, first: &str| {
        let per = ((col_w / (adv * size)) - indent).floor().max(8.0) as usize;
        for (i, l) in wrap(text, per.saturating_sub(first.chars().count())).into_iter().enumerate() {
            let lead = if i == 0 { first.to_string() } else { " ".repeat(first.chars().count()) };
            out.push(Some(Line { text: format!("{lead}{l}"), col, size, indent }));
        }
    };
    push(&mut out, &format!("STEP {} OF {}", p.step.0 + 1, p.step.1), DIM, 0.8, 0.0, "");
    push(&mut out, p.head, HEAD, 1.18, 0.0, "");
    out.push(None);
    push(&mut out, p.what, INK, 1.0, 0.0, "");
    out.push(None);
    push(&mut out, "LOOK FOR", DIM, 0.8, 0.0, "");
    push(&mut out, p.look, LOOK, 1.0, 0.0, "");
    if facts > 0 {
        out.push(None);
        push(&mut out, "KEY NUMBERS", DIM, 0.8, 0.0, "");
        for f in p.facts.iter().take(facts) {
            push(&mut out, f, INK, 0.9, 0.0, "· ");
        }
    }
    let h = out
        .iter()
        .map(|l| match l {
            Some(l) => px * l.size * 1.32,
            None => px * 0.6,
        })
        .sum();
    (out, h)
}

/// The finished frame: `scene` (rendered `scene_width(w)` x `h`) on the left, the panel on the right.
pub fn compose(scene: &RgbaImage, w: u32, h: u32, p: &Panel) -> RgbaImage {
    let mut img = RgbaImage::from_pixel(w, h, image::Rgba([PANEL[0], PANEL[1], PANEL[2], 255]));
    image::imageops::replace(&mut img, scene, 0, 0);
    let x0 = scene.width();
    for y in 0..h {
        for dx in 0..(h / 360).max(1) {
            if x0 + dx < w {
                img.get_pixel_mut(x0 + dx, y).0 = [RULE[0], RULE[1], RULE[2], 255];
            }
        }
    }
    let pad = (h as f32 * 0.045).max(6.0);
    let col_w = (w - x0) as f32 - 2.0 * pad;
    let room = h as f32 - 2.0 * pad;
    if col_w < 40.0 || room < 30.0 {
        return img;
    }
    // Largest body size that fits, from h/26 down to a floor; below the floor drop key numbers.
    let floor = (h as f32 / 62.0).max(9.0);
    let mut px = (h as f32 / 26.0).max(floor);
    let mut facts = p.facts.len();
    let (lines, _) = loop {
        let (lines, used) = layout(p, px, col_w, facts);
        if used <= room {
            break (lines, used);
        }
        if px > floor {
            px = (px * 0.94).max(floor);
        } else if facts > 0 {
            facts -= 1;
        } else {
            break (lines, used);
        }
    };
    let mut y = pad;
    for l in &lines {
        match l {
            Some(l) => {
                let s = px * l.size;
                if y + s * 1.32 > h as f32 - pad * 0.5 {
                    break;
                }
                draw(&mut img, x0 as f32 + pad + l.indent * advance(s), y, s, &l.text, l.col);
                y += s * 1.32;
            }
            None => y += px * 0.6,
        }
    }
    img
}

/// Tags pinned to points in one picture. Each tag takes the first spot around its point that
/// does not cover a tag already placed (up-right, up-left, down-right, down-left, then further
/// out), so tags close together fan out instead of stacking.
pub struct Tags {
    placed: Vec<[f32; 4]>,
}

impl Default for Tags {
    fn default() -> Self {
        Self::new()
    }
}

impl Tags {
    pub fn new() -> Self {
        Tags { placed: Vec::new() }
    }

    /// A tag reading `text` with a leader line from the point (`ax`, `ay`), kept inside the
    /// rectangle (0, 0)-(`max_x`, `img.height()`). `h` is the frame height, for sizing.
    pub fn add(&mut self, img: &mut RgbaImage, ax: f32, ay: f32, text: &str, max_x: u32, h: u32) {
        let px = (h as f32 / 36.0).max(9.0);
        let tw = advance(px) * text.chars().count() as f32;
        let pad = px * 0.45;
        let (bw, bh) = (tw + 2.0 * pad, px * 1.5);
        let lim_x = max_x as f32;
        let lim_y = img.height() as f32;
        if ax < 0.0 || ay < 0.0 || ax >= lim_x || ay >= lim_y {
            return;
        }
        let off = px * 2.2;
        let place = |dx: f32, dy: f32, reach: f32| {
            let bx = if dx > 0.0 { ax + off * 0.6 * reach } else { ax - off * 0.6 * reach - bw };
            let by = if dy < 0.0 { ay - off * reach - bh } else { ay + off * reach };
            [bx.clamp(2.0, (lim_x - bw - 2.0).max(2.0)), by.clamp(2.0, (lim_y - bh - 2.0).max(2.0))]
        };
        let hits = |r: [f32; 2], placed: &[[f32; 4]]| {
            placed.iter().any(|q| r[0] < q[0] + q[2] + 4.0 && q[0] < r[0] + bw + 4.0 && r[1] < q[1] + q[3] + 4.0 && q[1] < r[1] + bh + 4.0)
        };
        let mut spot = place(1.0, -1.0, 1.0);
        'search: for reach in [1.0, 2.0, 3.2] {
            for (dx, dy) in [(1.0, -1.0), (-1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)] {
                let r = place(dx, dy, reach);
                if !hits(r, &self.placed) {
                    spot = r;
                    break 'search;
                }
            }
        }
        let [bx, by] = spot;
        self.placed.push([bx, by, bw, bh]);
        // leader from the point to the nearest corner of the tag
        let cx = if bx > ax { bx } else { bx + bw };
        let cy = if by > ay { by } else { by + bh };
        let lw = (h as f32 / 400.0).max(1.0);
        line(img, ax, ay, cx, cy, lw, HEAD);
        dot(img, ax, ay, lw * 2.6, HEAD);
        rect(img, bx, by, bw, bh, TAG, 0.82);
        rect(img, bx, by + bh - lw, bw, lw, HEAD, 1.0);
        draw(img, bx + pad, by + (bh - px) * 0.5, px, text, INK);
    }
}

fn advance(px: f32) -> f32 {
    let f = font().as_scaled(PxScale::from(px));
    f.h_advance(f.glyph_id('M'))
}

/// Words joined to at most `max` characters a line; a word longer than a line is split.
fn wrap(text: &str, max: usize) -> Vec<String> {
    let max = max.max(1);
    let mut out = Vec::new();
    let mut cur = String::new();
    for word in text.split_whitespace() {
        let mut rest: Vec<char> = word.chars().collect();
        while rest.len() > max {
            if !cur.is_empty() {
                out.push(std::mem::take(&mut cur));
            }
            out.push(rest[..max].iter().collect());
            rest.drain(..max);
        }
        let n = rest.len();
        if n == 0 {
            continue;
        }
        if !cur.is_empty() && cur.chars().count() + 1 + n > max {
            out.push(std::mem::take(&mut cur));
        }
        if !cur.is_empty() {
            cur.push(' ');
        }
        cur.extend(rest);
    }
    if !cur.is_empty() || out.is_empty() {
        out.push(cur);
    }
    out
}

/// Font size (px) at which one monospace character is `cell` px wide, so text sets on a grid of
/// character cells.
pub fn px_for_advance(cell: f32) -> f32 {
    cell / advance(1.0)
}

/// Draws one line of JetBrains Mono with its top at `y`, antialiased, in `col`.
pub fn text(img: &mut RgbaImage, x: f32, y: f32, px: f32, s: &str, col: [u8; 3]) {
    draw(img, x, y, px, s, col);
}

/// Draws `text` with its top at `y`, antialiased.
fn draw(img: &mut RgbaImage, x: f32, y: f32, px: f32, text: &str, col: [u8; 3]) {
    let f = font().as_scaled(PxScale::from(px));
    let base = y + f.ascent();
    let mut pen = x;
    let mut prev = None;
    for c in text.chars() {
        let id = f.glyph_id(c);
        if let Some(p) = prev {
            pen += f.kern(p, id);
        }
        let g = id.with_scale_and_position(PxScale::from(px), ab_glyph::point(pen, base));
        if let Some(o) = font().outline_glyph(g) {
            let b = o.px_bounds();
            o.draw(|gx, gy, a| {
                let (xx, yy) = (b.min.x as i32 + gx as i32, b.min.y as i32 + gy as i32);
                blend(img, xx, yy, col, a);
            });
        }
        pen += f.h_advance(id);
        prev = Some(id);
    }
}

fn blend(img: &mut RgbaImage, x: i32, y: i32, col: [u8; 3], a: f32) {
    if x < 0 || y < 0 || x >= img.width() as i32 || y >= img.height() as i32 || a <= 0.0 {
        return;
    }
    let a = a.min(1.0);
    let p = img.get_pixel_mut(x as u32, y as u32);
    for k in 0..3 {
        p.0[k] = (p.0[k] as f32 * (1.0 - a) + col[k] as f32 * a).round() as u8;
    }
}

fn rect(img: &mut RgbaImage, x: f32, y: f32, w: f32, h: f32, col: [u8; 3], a: f32) {
    for yy in y.floor() as i32..(y + h).ceil() as i32 {
        for xx in x.floor() as i32..(x + w).ceil() as i32 {
            blend(img, xx, yy, col, a);
        }
    }
}

fn dot(img: &mut RgbaImage, cx: f32, cy: f32, r: f32, col: [u8; 3]) {
    for yy in (cy - r - 1.0) as i32..=(cy + r + 1.0) as i32 {
        for xx in (cx - r - 1.0) as i32..=(cx + r + 1.0) as i32 {
            let d = ((xx as f32 + 0.5 - cx).powi(2) + (yy as f32 + 0.5 - cy).powi(2)).sqrt();
            blend(img, xx, yy, col, (r + 0.5 - d).clamp(0.0, 1.0));
        }
    }
}

/// An antialiased line `w` pixels wide.
fn line(img: &mut RgbaImage, x0: f32, y0: f32, x1: f32, y1: f32, w: f32, col: [u8; 3]) {
    let (dx, dy) = (x1 - x0, y1 - y0);
    let len2 = (dx * dx + dy * dy).max(1e-6);
    let (lo_x, hi_x) = (x0.min(x1) - w - 1.0, x0.max(x1) + w + 1.0);
    let (lo_y, hi_y) = (y0.min(y1) - w - 1.0, y0.max(y1) + w + 1.0);
    for yy in lo_y as i32..=hi_y as i32 {
        for xx in lo_x as i32..=hi_x as i32 {
            let (px, py) = (xx as f32 + 0.5, yy as f32 + 0.5);
            let t = (((px - x0) * dx + (py - y0) * dy) / len2).clamp(0.0, 1.0);
            let d = ((px - x0 - t * dx).powi(2) + (py - y0 - t * dy).powi(2)).sqrt();
            blend(img, xx, yy, col, (w * 0.5 + 0.5 - d).clamp(0.0, 1.0));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn panel() -> Panel<'static> {
        Panel {
            step: (2, 6),
            head: "SiO condenses on the cool charge and a crust builds around each cavity",
            what: "Over hours a hard crust grows around each cavity. It thickens, rises, and swells the cavity, and charge can no longer fall into the hot zone, so reactions stall.",
            look: "a dark crust swelling round each cavity, then the stoking bar",
            facts: &["Crust is mainly SiO2", "About once an hour", "After months the furnace may need emptying"],
        }
    }

    #[test]
    fn text_scales_with_the_frame() {
        for (w, h) in [(640u32, 360u32), (1280, 720), (2560, 1440)] {
            let scene = RgbaImage::new(scene_width(w), h);
            let img = compose(&scene, w, h, &panel());
            assert_eq!(img.dimensions(), (w, h));
            let inked = img
                .enumerate_pixels()
                .filter(|(x, _, p)| *x > scene_width(w) && p.0[0] > 150)
                .count() as f64;
            let share = inked / ((w - scene_width(w)) * h) as f64;
            assert!(share > 0.01 && share < 0.4, "{w}x{h}: ink share {share}");
        }
    }

    #[test]
    fn labels_stay_inside_the_scene_area() {
        let mut img = RgbaImage::new(800, 450);
        Tags::new().add(&mut img, 495.0, 5.0, "stoking bar", 500, 450);
        let outside = img.enumerate_pixels().filter(|(x, _, p)| *x >= 500 && p.0[0] > 0).count();
        assert_eq!(outside, 0);
    }

    #[test]
    fn tags_on_one_point_do_not_overlap() {
        let mut img = RgbaImage::new(800, 450);
        let mut tags = Tags::new();
        for t in ["one", "two", "three"] {
            tags.add(&mut img, 400.0, 220.0, t, 800, 450);
        }
        let p = &tags.placed;
        for i in 0..p.len() {
            for j in i + 1..p.len() {
                let (a, b) = (p[i], p[j]);
                let apart = a[0] + a[2] <= b[0] || b[0] + b[2] <= a[0] || a[1] + a[3] <= b[1] || b[1] + b[3] <= a[1];
                assert!(apart, "tags {i} and {j} overlap");
            }
        }
    }

    #[test]
    fn wrap_keeps_words() {
        assert_eq!(wrap("a bb ccc dddd", 6), vec!["a bb", "ccc", "dddd"]);
    }
}
