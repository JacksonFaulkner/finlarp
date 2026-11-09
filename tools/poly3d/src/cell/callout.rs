//! Text boxes on the picture: a beat's notes drawn beside the parts they are about.
//!
//! Each box wraps its text to a width, then goes wherever the frame is empty near
//! its part. "Empty" is read from the z-buffer (anything solid is taken), plus the
//! part names and any boxes already placed, so the boxes keep finding room as the
//! camera turns. A thin leader joins a box to its part.

use super::stage::{self, fill_rect, glyphs, screen_line, Rect, BG};
use crate::{Cam, Canvas, Col, V3};

/// One box: a heading, paragraphs of body text, and the part it points at.
pub(super) struct Callout<'a> {
    pub title: &'a str,
    pub body: Vec<String>,
    pub col: Col,
    /// the part it is about, or None for a free box
    pub anchor: Option<V3>,
    /// where a free box would rather sit, as fractions of the frame
    pub prefer: (f64, f64),
}

/// Body text size: about the terminal's own text at the usual pixel density.
fn body_scale(cv: &Canvas) -> i64 {
    ((cv.h as f64 / 480.0).round() as i64).max(1)
}

/// Greedy word wrap to `cols` characters. A paragraph starting with "- " hangs its
/// following lines under the text.
fn wrap(par: &str, cols: usize) -> Vec<String> {
    let cols = cols.max(8);
    let (first, hang) = match par.strip_prefix("- ") {
        Some(rest) => ("- ", (rest, "  ")),
        None => ("", (par, "")),
    };
    let (text, indent) = hang;
    let mut out = Vec::new();
    let mut line = first.to_string();
    let mut empty = true;
    for word in text.split_whitespace() {
        let need = line.chars().count() + usize::from(!empty) + word.chars().count();
        if !empty && need > cols {
            out.push(std::mem::replace(&mut line, indent.to_string()));
            empty = true;
        }
        if !empty {
            line.push(' ');
        }
        line.push_str(word);
        empty = false;
    }
    if !empty {
        out.push(line);
    }
    out
}

/// A box's laid-out text and size in pixels.
struct Laid {
    lines: Vec<(String, bool)>,
    w: i64,
    h: i64,
}

fn lay(c: &Callout, cols: usize, s: i64) -> Laid {
    let mut lines = vec![(c.title.to_ascii_uppercase(), true)];
    for (i, par) in c.body.iter().enumerate() {
        if i > 0 && !par.starts_with("- ") {
            lines.push((String::new(), false));
        }
        lines.extend(wrap(par, cols).into_iter().map(|l| (l, false)));
    }
    let longest = lines.iter().map(|(l, _)| l.chars().count()).max().unwrap_or(0) as i64;
    let pad = 4 * s;
    Laid {
        w: longest * 6 * s - s + 2 * pad,
        h: lines.len() as i64 * line_h(s) - 2 * s + 2 * pad,
        lines,
    }
}

fn line_h(s: i64) -> i64 {
    11 * s
}

/// Where the frame is taken, on a coarse grid with a summed-area table for fast
/// "how much of this rectangle is taken" queries.
struct Taken {
    cell: i64,
    gw: usize,
    gh: usize,
    sat: Vec<u32>,
}

impl Taken {
    fn new(cv: &Canvas, extra: &[Rect]) -> Taken {
        let cell = (cv.h as i64 / 120).max(2);
        let gw = (cv.w as i64 / cell + 1) as usize;
        let gh = (cv.h as i64 / cell + 1) as usize;
        let mut grid = vec![0u32; gw * gh];
        for y in 0..cv.h {
            for x in 0..cv.w {
                if cv.z[y * cv.w + x].is_finite() {
                    grid[(y as i64 / cell) as usize * gw + (x as i64 / cell) as usize] = 1;
                }
            }
        }
        for r in extra {
            for gy in (r.1.max(0) / cell)..=(r.3.max(0) / cell).min(gh as i64 - 1) {
                for gx in (r.0.max(0) / cell)..=(r.2.max(0) / cell).min(gw as i64 - 1) {
                    grid[gy as usize * gw + gx as usize] = 1;
                }
            }
        }
        let mut t = Taken { cell, gw, gh, sat: vec![0; (gw + 1) * (gh + 1)] };
        for gy in 0..gh {
            for gx in 0..gw {
                let i = (gy + 1) * (gw + 1) + gx + 1;
                t.sat[i] = grid[gy * gw + gx] + t.sat[i - 1] + t.sat[i - gw - 1] - t.sat[i - gw - 2];
            }
        }
        t
    }

    /// Taken cells under rectangle `r`, in grid cells.
    fn count(&self, r: Rect) -> u32 {
        let c = |v: i64, n: usize| (v.div_euclid(self.cell)).clamp(0, n as i64) as usize;
        let (x0, y0) = (c(r.0, self.gw), c(r.1, self.gh));
        let (x1, y1) = (c(r.2 + self.cell - 1, self.gw), c(r.3 + self.cell - 1, self.gh));
        let at = |x: usize, y: usize| self.sat[y * (self.gw + 1) + x];
        (at(x1, y1) + at(x0, y0)).saturating_sub(at(x0, y1) + at(x1, y0))
    }
}

fn overlap(a: Rect, b: Rect) -> i64 {
    let w = (a.2.min(b.2) - a.0.max(b.0)).max(0);
    let h = (a.3.min(b.3) - a.1.max(b.1)).max(0);
    w * h
}

/// Places each box in turn: the spot near its part with the least taken under it.
fn place(cv: &Canvas, cam: &Cam, boxes: &[Callout], avoid: &[Rect]) -> Vec<(Laid, Rect, Option<(f64, f64)>)> {
    let taken = Taken::new(cv, avoid);
    let s = body_scale(cv);
    let (w, h) = (cv.w as i64, cv.h as i64);
    let margin = 3 * s;
    let gap = 6 * s;
    let step = (h / 48).max(2);
    let mut out: Vec<(Laid, Rect, Option<(f64, f64)>)> = Vec::new();
    for b in boxes {
        let anchor = b.anchor.and_then(|p| cam.project(p)).map(|(x, y, _)| (x, y));
        let want = anchor.unwrap_or((b.prefer.0 * w as f64, b.prefer.1 * h as f64));
        let mut best: Option<(f64, Laid, Rect)> = None;
        // try a few widths: narrow boxes fit gaps, wide ones are shorter
        let max_cols = ((w as f64 * 0.34) / (6 * s) as f64) as usize;
        for cols in [26usize, 34, 42, 50] {
            if cols > max_cols.max(26) {
                continue;
            }
            let laid = lay(b, cols, s);
            if laid.w + 2 * margin > w || laid.h + 2 * margin > h {
                continue;
            }
            let mut y = margin;
            while y + laid.h + margin <= h {
                let mut x = margin;
                while x + laid.w + margin <= w {
                    let r = (x, y, x + laid.w, y + laid.h);
                    let halo = (r.0 - gap, r.1 - gap, r.2 + gap, r.3 + gap);
                    let solid = taken.count(halo) as f64;
                    let boxes: i64 = out.iter().map(|(_, o, _)| overlap(halo, *o)).sum();
                    let (cx, cy) = (
                        want.0.clamp(r.0 as f64, r.2 as f64),
                        want.1.clamp(r.1 as f64, r.3 as f64),
                    );
                    let dist = ((cx - want.0).powi(2) + (cy - want.1).powi(2)).sqrt();
                    let score = solid * 40.0 + boxes as f64 * 4.0 + dist + laid.h as f64 * 0.15;
                    if best.as_ref().is_none_or(|(s, _, _)| score < *s) {
                        best = Some((score, lay(b, cols, s), r));
                    }
                    x += step;
                }
                y += step;
            }
        }
        if let Some((_, laid, r)) = best {
            out.push((laid, r, anchor));
        }
    }
    out
}

/// Draws the boxes at `alpha` (they fade in once the camera has settled).
pub(super) fn draw(cv: &mut Canvas, cam: &Cam, boxes: &[Callout], avoid: &[Rect], alpha: f64) {
    if alpha <= 0.004 || boxes.is_empty() {
        return;
    }
    let s = body_scale(cv);
    let a = alpha.clamp(0.0, 1.0) as f32;
    let placed = place(cv, cam, boxes, avoid);
    for ((laid, r, anchor), b) in placed.iter().zip(boxes) {
        if let Some((ax, ay)) = anchor {
            let ex = ax.clamp(r.0 as f64, r.2 as f64);
            let ey = ay.clamp(r.1 as f64, r.3 as f64);
            screen_line(cv, (*ax, *ay), (ex, ey), b.col, 0.6 * alpha, 1);
            fill_rect(cv, *ax as i64 - s, *ay as i64 - s, *ax as i64 + 2 * s, *ay as i64 + 2 * s, b.col, a);
        }
        fill_rect(cv, r.0, r.1, r.2, r.3, BG, 0.88 * a);
        // a bar down the left edge in the box's colour
        fill_rect(cv, r.0, r.1, r.0 + s.max(2), r.3, b.col, 0.9 * a);
        let pad = 4 * s;
        for (i, (line, head)) in laid.lines.iter().enumerate() {
            let col = if *head { b.col } else { stage::TEXT };
            glyphs(cv, r.0 + pad, r.1 + pad + i as i64 * line_h(s), line, col, a, s);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wrap_keeps_words_whole_and_hangs_bullets() {
        let l = wrap("the word line selects a whole row of cells", 12);
        assert!(l.iter().all(|x| x.chars().count() <= 12), "{l:?}");
        assert_eq!(l.join(" "), "the word line selects a whole row of cells");
        let b = wrap("- one two three four five", 10);
        assert!(b[0].starts_with("- ") && b[1].starts_with("  "), "{b:?}");
    }
}
