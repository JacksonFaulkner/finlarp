// Sandboxes for the Packaging tab's pages: a model you push on with keys, pictures that follow it,
// the numbers, and a sentence saying what the current setup runs into. Each page's sandbox is a
// `Lab`; this module holds the frame they share (border, headline, verdict) and the drawing kit
// (half-block pixel painting, legends, bars, the wafer and package-from-above pictures).
//
// One file per page: die.rs (LOGIC DIE), bump.rs (MICROBUMP), interposer.rs (INTERPOSER),
// substrate.rs (SUBSTRATE), assembly.rs (ASSEMBLY), board.rs (BOARD).

mod assembly;
mod board;
mod bump;
mod die;
mod interposer;
mod substrate;

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph, Wrap};

use crate::ui::theme::Theme;

/// One page's sandbox.
pub trait Lab: Send {
    /// The menu row: what the sandbox lets you try.
    fn menu(&self) -> &'static str;
    /// The border title after the page name, e.g. "die-size sandbox".
    fn name(&self) -> &'static str;
    /// The keys, for the bottom border.
    fn hint(&self) -> &'static str;
    /// The headline (preset name or "your design") and the one-line goal beside it.
    fn head(&self) -> (String, &'static str);
    /// What the current setup runs into; true when it is a hard limit (drawn red).
    fn verdict(&self) -> (String, bool);
    /// Handles a key; false when it is not the sandbox's.
    fn key(&mut self, code: KeyCode) -> bool;
    /// The pictures and numbers under the verdict.
    fn body(&self, frame: &mut Frame, r: Rect, t: &Theme);
    /// One line for Claude's view of the screen.
    fn summary(&self) -> String;
}

/// A fresh sandbox for `page`, if it has one.
pub fn new_lab(page: &str) -> Option<Box<dyn Lab>> {
    Some(match page {
        "LOGIC DIE" => Box::new(die::DieLab::default()),
        "MICROBUMP" => Box::new(bump::BumpLab::default()),
        "INTERPOSER" => Box::new(interposer::InterposerLab::default()),
        "SUBSTRATE" => Box::new(substrate::SubstrateLab::default()),
        "ASSEMBLY" => Box::new(assembly::AssemblyLab::default()),
        "BOARD" => Box::new(board::BoardLab::default()),
        _ => return None,
    })
}

pub fn has_lab(page: &str) -> bool {
    matches!(
        page,
        "LOGIC DIE" | "MICROBUMP" | "INTERPOSER" | "SUBSTRATE" | "ASSEMBLY" | "BOARD"
    )
}

/// The whole sandbox in `r`: border, headline, verdict, then the lab's own body.
pub fn draw(frame: &mut Frame, r: Rect, label: &str, lab: &dyn Lab, t: &Theme) {
    frame.render_widget(Clear, r);
    let hint = format!(" {}  esc menu ", lab.hint());
    let block = Block::new()
        .borders(Borders::ALL)
        .border_style(t.accent())
        .title(Span::styled(
            format!(" {label} \u{00B7} {} ", lab.name()),
            t.title(),
        ))
        .title_bottom(Span::styled(hint, t.dim()))
        .padding(ratatui::widgets::Padding::new(2, 2, 1, 0));
    let inner = block.inner(r);
    frame.render_widget(block, r);
    let [head_r, verdict_r, _, body_r] = Layout::vertical([
        Constraint::Length(1),
        Constraint::Length(3),
        Constraint::Length(1),
        Constraint::Min(0),
    ])
    .areas(inner);
    let (title, goal) = lab.head();
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled(title, t.title()),
            Span::styled(format!("   {goal}"), t.dim()),
        ])),
        head_r,
    );
    let (verdict, bad) = lab.verdict();
    let style = if bad {
        Style::new().fg(C_BAD).add_modifier(Modifier::BOLD)
    } else {
        t.accent()
    };
    frame.render_widget(
        Paragraph::new(Line::from(Span::styled(verdict, style))).wrap(Wrap { trim: true }),
        verdict_r,
    );
    lab.body(frame, body_r, t);
}

// ---- shared kit ----

pub(super) const C_DIE: Color = Color::Rgb(0xa9, 0x8b, 0xe0);
pub(super) const C_BAD: Color = Color::Rgb(0xe0, 0x5c, 0x5c);
pub(super) const C_OK: Color = Color::Rgb(0x50, 0xc8, 0x7b);
pub(super) const C_WAFER: Color = Color::Rgb(0x4a, 0x4e, 0x62);
pub(super) const C_DEFECT: Color = Color::Rgb(0xf1, 0xfa, 0x8c);
pub(super) const C_HBM: Color = Color::Rgb(0x8f, 0xbc, 0xdb);
pub(super) const C_TSV: Color = Color::Rgb(0xd0, 0x8a, 0x4a);
pub(super) const C_BRIDGE: Color = Color::Rgb(0x8b, 0xe9, 0xfd);
pub(super) const C_INTERPOSER: Color = Color::Rgb(0x55, 0x70, 0x62);
pub(super) const C_ORGANIC: Color = Color::Rgb(0x8a, 0x6e, 0x4a);
pub(super) const C_RETICLE: Color = Color::Rgb(0xff, 0x79, 0xc6);
pub(super) const C_COPPER: Color = Color::Rgb(0xd0, 0x8a, 0x4a);
pub(super) const C_SOLDER: Color = Color::Rgb(0xc8, 0xcc, 0xd4);
pub(super) const C_BOARD: Color = Color::Rgb(0x2f, 0x6b, 0x45);
pub(super) const C_POWER: Color = Color::Rgb(0xf1, 0xd0, 0x5c);
pub(super) const C_GREY: Color = Color::Rgb(0x8a, 0x8e, 0x9a);

/// One scanner exposure: the largest die that can be printed in one go.
pub(super) const RETICLE_W: f64 = 26.0;
pub(super) const RETICLE_H: f64 = 33.0;
pub(super) const RETICLE_MM2: f64 = RETICLE_W * RETICLE_H;
pub(super) const WAFER_D: f64 = 300.0;
/// No whole die within this much of the wafer's rim.
const EDGE_EXCLUSION: f64 = 3.0;
/// Saw street between dies.
const SCRIBE: f64 = 0.2;
/// Edge length one HBM stack takes along the die (footprint ~10 x 11 mm, plus a gap).
pub(super) const HBM_PITCH: f64 = 10.5;
pub(super) const HBM_DEPTH: f64 = 11.0;

/// Fills `r` with half-block pixels (two per cell, square-ish) from `px(col, row)`, None = blank.
pub(super) fn paint(buf: &mut Buffer, r: Rect, bg: Color, px: impl Fn(u16, u16) -> Option<Color>) {
    for cy in 0..r.height {
        for cx in 0..r.width {
            let top = px(cx, cy * 2);
            let bot = px(cx, cy * 2 + 1);
            if top.is_none() && bot.is_none() {
                continue;
            }
            let cell = &mut buf[(r.x + cx, r.y + cy)];
            cell.set_symbol("\u{2580}");
            cell.set_fg(top.unwrap_or(bg));
            cell.set_bg(bot.unwrap_or(bg));
        }
    }
}

/// Maps pixels of `r` onto a `span_w` x `span_h` mm field centred on (0, 0), keeping it square and
/// fitting the whole field; returns mm per pixel. Pixel (px, py) is at ((px+.5)*s - ox, (py+.5)*s - oy).
pub(super) fn fit(r: Rect, span_w: f64, span_h: f64) -> (f64, f64, f64) {
    let (pw, ph) = (r.width.max(1) as f64, r.height.max(1) as f64 * 2.0);
    let s = (span_w / pw).max(span_h / ph);
    (s, pw * s / 2.0, ph * s / 2.0)
}

/// A square drawing area (in pixels: 1 per column, 2 per row) centred in `r`, and its side.
pub(super) fn square(r: Rect) -> (Rect, u16) {
    let side = r.width.min(r.height * 2);
    let h = side.div_ceil(2);
    let x = r.x + (r.width - side) / 2;
    let y = r.y + (r.height - h) / 2;
    (Rect::new(x, y, side, h), side)
}

pub(super) fn swatch(c: Color, text: &str, t: &Theme) -> Vec<Span<'static>> {
    vec![
        Span::styled("\u{2588}\u{2588} ", Style::new().fg(c)),
        Span::styled(format!("{text}   "), t.dim()),
    ]
}

/// Legend rows: swatches packed into lines no wider than `w`.
pub(super) fn legend(items: &[(Color, &str)], w: u16, t: &Theme) -> Vec<Line<'static>> {
    let mut lines = Vec::new();
    let mut cur: Vec<Span> = Vec::new();
    let mut used = 0usize;
    for (c, text) in items {
        let len = text.chars().count() + 6;
        if used + len > w as usize && !cur.is_empty() {
            lines.push(Line::from(std::mem::take(&mut cur)));
            used = 0;
        }
        cur.extend(swatch(*c, text, t));
        used += len;
    }
    if !cur.is_empty() {
        lines.push(Line::from(cur));
    }
    lines
}

/// A filled bar: `pct` of `width` cells in `col`.
pub(super) fn bar(pct: f64, width: usize, col: Color, t: &Theme) -> Vec<Span<'static>> {
    let filled = ((pct / 100.0).clamp(0.0, 1.0) * width as f64).round() as usize;
    vec![
        Span::styled("\u{2595}", t.dim()),
        Span::styled("\u{2588}".repeat(filled), Style::new().fg(col)),
        Span::styled("\u{2591}".repeat(width - filled), t.dim()),
        Span::styled("\u{258F}", t.dim()),
    ]
}

pub(super) fn money(v: f64) -> String {
    if !v.is_finite() {
        return "n/a".into();
    }
    format!("${}", thousands(v))
}

pub(super) fn thousands(v: f64) -> String {
    let s = (v.round() as i64).to_string();
    let mut out = String::new();
    for (i, ch) in s.chars().enumerate() {
        if i > 0 && (s.len() - i) % 3 == 0 && ch != '-' {
            out.push(',');
        }
        out.push(ch);
    }
    out
}

/// A titled picture panel: "TITLE · subtitle" on top, legend at the foot; returns the picture area.
pub(super) fn panel(
    frame: &mut Frame,
    r: Rect,
    title: &str,
    sub: &str,
    legend_items: &[(Color, &str)],
    t: &Theme,
) -> Rect {
    let leg = legend(legend_items, r.width, t);
    let [tr, pr, lr] = Layout::vertical([
        Constraint::Length(1),
        Constraint::Min(3),
        Constraint::Length(leg.len() as u16),
    ])
    .areas(r);
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled(title.to_string(), t.accent()),
            Span::styled(format!(" \u{00B7} {sub}"), t.dim()),
        ])),
        tr,
    );
    frame.render_widget(Paragraph::new(leg), lr);
    pr
}

/// The numbers table: rows of (key, spans).
pub(super) fn numbers(frame: &mut Frame, r: Rect, rows: Vec<Line<'static>>) {
    frame.render_widget(Paragraph::new(rows).wrap(Wrap { trim: false }), r);
}

/// Row helpers for the numbers table.
pub(super) fn k(s: &str, t: &Theme) -> Span<'static> {
    Span::styled(format!("{s:<11}"), t.accent())
}
pub(super) fn v(s: impl Into<String>, t: &Theme) -> Span<'static> {
    Span::styled(s.into(), t.base())
}
pub(super) fn d(s: impl Into<String>, t: &Theme) -> Span<'static> {
    Span::styled(s.into(), t.dim())
}
pub(super) fn red(s: impl Into<String>) -> Span<'static> {
    Span::styled(s.into(), Style::new().fg(C_BAD))
}
pub(super) fn good_or_bad(s: impl Into<String>, bad: bool, t: &Theme) -> Span<'static> {
    if bad { red(s) } else { v(s, t) }
}

/// The body split used by most labs: one picture on the left, a second picture over the numbers on
/// the right (wide), or the two pictures side by side over the numbers (narrow).
pub(super) fn three_way(r: Rect, left_pct: u16) -> (Rect, Rect, Rect) {
    if r.width >= 100 {
        let [a, _, b] = Layout::horizontal([
            Constraint::Percentage(left_pct),
            Constraint::Length(2),
            Constraint::Min(0),
        ])
        .areas(r);
        let [p, n] = Layout::vertical([Constraint::Percentage(50), Constraint::Min(0)]).areas(b);
        (a, p, n)
    } else {
        let [top, n] = Layout::vertical([Constraint::Percentage(55), Constraint::Min(0)]).areas(r);
        let [a, b] =
            Layout::horizontal([Constraint::Percentage(50), Constraint::Min(0)]).areas(top);
        (a, b, n)
    }
}

// ---- wafers ----

/// Whole `w` x `h` mm sites on a 300 mm wafer (grid corner on the wafer centre): their corners.
pub(super) fn wafer_sites(w: f64, h: f64) -> Vec<(f64, f64)> {
    let (px, py) = (w + SCRIBE, h + SCRIBE);
    let r = WAFER_D / 2.0 - EDGE_EXCLUSION;
    let nx = (r / px).ceil() as i32 + 1;
    let ny = (r / py).ceil() as i32 + 1;
    let mut out = Vec::new();
    for j in -ny..ny {
        for i in -nx..nx {
            let (x0, y0) = (i as f64 * px, j as f64 * py);
            let inside = [(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h)]
                .iter()
                .all(|(x, y)| x * x + y * y <= r * r);
            if inside {
                out.push((x0, y0));
            }
        }
    }
    out
}

/// A 300 mm wafer cut into `w` x `h` sites; `colour(i)` colours site i (in `wafer_sites` order);
/// `dots` are points lit in `C_DEFECT`.
pub(super) fn draw_wafer(
    buf: &mut Buffer,
    r: Rect,
    w: f64,
    h: f64,
    colour: impl Fn(usize) -> Color,
    dots: &[(f64, f64)],
    bg: Color,
) {
    let (area, side) = square(r);
    if side < 8 {
        return;
    }
    let (px, py) = (w + SCRIBE, h + SCRIBE);
    let grid: std::collections::HashMap<(i64, i64), usize> = wafer_sites(w, h)
        .iter()
        .enumerate()
        .map(|(i, &(x0, y0))| (((x0 / px).round() as i64, (y0 / py).round() as i64), i))
        .collect();
    let scale = WAFER_D / side as f64;
    let rad = WAFER_D / 2.0;
    let to_mm = |p: u16| (p as f64 + 0.5) * scale - rad;
    let dot_px: std::collections::HashSet<(i64, i64)> = dots
        .iter()
        .map(|&(x, y)| (((x + rad) / scale) as i64, ((rad - y) / scale) as i64))
        .collect();
    paint(buf, area, bg, |cx, cy| {
        let x = to_mm(cx);
        let y = -to_mm(cy);
        if x * x + y * y > rad * rad {
            return None;
        }
        if dot_px.contains(&(cx as i64, cy as i64)) {
            return Some(C_DEFECT);
        }
        let (i, j) = ((x / px).floor() as i64, (y / py).floor() as i64);
        let Some(&site) = grid.get(&(i, j)) else {
            return Some(C_WAFER);
        };
        // a pixel-wide gap at each site's left and top edge keeps neighbours apart
        let (fx, fy) = (x - i as f64 * px, y - j as f64 * py);
        if fx >= scale.min(w * 0.3) && fx < w && fy < h - scale.min(h * 0.3) {
            Some(colour(site))
        } else {
            Some(C_WAFER)
        }
    });
}

// ---- the package from above ----

/// The dies in a row with HBM along the top and bottom edges: the layout LOGIC DIE and
/// INTERPOSER draw. A lone die lies landscape (long edges carry HBM); split dies stand portrait
/// and join along their long edges (Blackwell).
#[derive(Debug, Clone)]
pub(super) struct PkgLayout {
    pub dies: u32,
    pub w: f64,
    pub h: f64,
    pub row_w: f64,
    /// Stacks that fit (both edges) and stacks drawn.
    pub hbm_fit: u32,
    pub hbm: u32,
}

pub(super) const DIE_GAP: f64 = 1.0;

impl PkgLayout {
    pub fn new(total_mm2: f64, dies: u32, hbm: u32) -> Self {
        let a = total_mm2 / dies as f64;
        let short = (a * RETICLE_W / RETICLE_H).sqrt();
        let long = (a * RETICLE_H / RETICLE_W).sqrt();
        let (w, h) = if dies == 1 {
            (long, short)
        } else {
            (short, long)
        };
        let row_w = dies as f64 * w + (dies as f64 - 1.0) * DIE_GAP;
        let hbm_fit = 2 * (dies as f64 * w / HBM_PITCH).floor() as u32;
        Self {
            dies,
            w,
            h,
            row_w,
            hbm_fit,
            hbm: hbm.min(hbm_fit),
        }
    }

    /// The interposer under it all: dies, HBM and a 2 mm margin.
    pub fn interposer(&self) -> (f64, f64) {
        let hbm_rows = if self.hbm > 0 {
            2.0 * (HBM_DEPTH + 1.0)
        } else {
            0.0
        };
        let wide = self.row_w.max((self.hbm.div_ceil(2)) as f64 * HBM_PITCH);
        (wide + 4.0, self.h + hbm_rows + 4.0)
    }

    pub fn die_x(&self, i: u32) -> f64 {
        -self.row_w / 2.0 + i as f64 * (self.w + DIE_GAP)
    }
}

/// How to draw a `PkgLayout`.
pub(super) struct PkgStyle {
    pub die: Color,
    pub interposer: Color,
    /// Draw the reticle field around each die.
    pub reticle: bool,
    /// Silicon bridges under each seam (CoWoS-L) or not.
    pub bridges: bool,
    /// Extra mm around the interposer kept in view (so a growing interposer reads as growing).
    pub span: Option<(f64, f64)>,
}

/// The package from above, to scale: interposer, dies, bridges, HBM stacks (each with its TSV
/// band down the middle, as in the 3D HBM model), the reticle field dashed around each die.
pub(super) fn draw_package(buf: &mut Buffer, r: Rect, l: &PkgLayout, st: &PkgStyle, bg: Color) {
    if r.width < 8 || r.height < 4 {
        return;
    }
    let ret = if l.dies == 1 {
        (RETICLE_H, RETICLE_W)
    } else {
        (RETICLE_W, RETICLE_H)
    };
    let (iw, ih) = l.interposer();
    let n = l.dies as f64;
    let (span_w, span_h) = st.span.unwrap_or((
        iw.max(n * ret.0 + (n - 1.0) * DIE_GAP) + 4.0,
        ih.max(ret.1) + 4.0,
    ));
    let (scale, ox, oy) = fit(r, span_w, span_h);
    let top_n = l.hbm.div_ceil(2);
    let bot_n = l.hbm - top_n;
    let row = |count: u32| -> Vec<f64> {
        let used = count as f64 * HBM_PITCH;
        (0..count)
            .map(|k| -used / 2.0 + k as f64 * HBM_PITCH + 0.25)
            .collect()
    };
    let (tops, bots) = (row(top_n), row(bot_n));
    // at least a pixel between neighbouring stacks so they read as separate parts
    let hbm_w = HBM_PITCH - scale.max(0.5);
    let line = scale * 0.9;
    let top_y = -l.h / 2.0 - 1.0 - HBM_DEPTH;
    let bot_y = l.h / 2.0 + 1.0;
    let hbm_px = |x: f64, y: f64, hx: f64, y0: f64| -> Option<Color> {
        if x >= hx && x < hx + hbm_w && y >= y0 && y < y0 + HBM_DEPTH {
            // the TSV band runs across the stack's middle
            let mid = (y - (y0 + HBM_DEPTH / 2.0)).abs() < HBM_DEPTH * 0.12;
            Some(if mid { C_TSV } else { C_HBM })
        } else {
            None
        }
    };
    paint(buf, r, bg, |px, py| {
        let x = (px as f64 + 0.5) * scale - ox;
        let y = (py as f64 + 0.5) * scale - oy;
        if st.reticle {
            for i in 0..l.dies {
                let cx = l.die_x(i) + l.w / 2.0;
                let (rx0, rx1) = (cx - ret.0 / 2.0, cx + ret.0 / 2.0);
                let (ry0, ry1) = (-ret.1 / 2.0, ret.1 / 2.0);
                let on_v =
                    ((x - rx0).abs() < line || (x - rx1).abs() < line) && y >= ry0 && y <= ry1;
                let on_h =
                    ((y - ry0).abs() < line || (y - ry1).abs() < line) && x >= rx0 && x <= rx1;
                if (on_v || on_h) && ((x + y) / 2.0).rem_euclid(2.0) < 1.2 {
                    return Some(C_RETICLE);
                }
            }
        }
        for i in 0..l.dies {
            let x0 = l.die_x(i);
            if x >= x0 && x < x0 + l.w && y >= -l.h / 2.0 && y < l.h / 2.0 {
                return Some(st.die);
            }
            if st.bridges && i + 1 < l.dies {
                let sx = x0 + l.w;
                if x >= sx - 1.5 && x < sx + DIE_GAP + 1.5 && y.abs() < l.h * 0.3 {
                    return Some(C_BRIDGE);
                }
            }
        }
        for &hx in &tops {
            if let Some(c) = hbm_px(x, y, hx, top_y) {
                return Some(c);
            }
        }
        for &hx in &bots {
            if let Some(c) = hbm_px(x, y, hx, bot_y) {
                return Some(c);
            }
        }
        if x.abs() < iw / 2.0 && y.abs() < ih / 2.0 {
            return Some(st.interposer);
        }
        None
    });
}

/// Steps through `list` from `cur`'s position by `by` (clamped at the ends).
pub(super) fn step_in<T: PartialEq + Copy>(list: &[T], cur: T, by: i32) -> T {
    let i = list.iter().position(|&x| x == cur).unwrap_or(0) as i32;
    list[(i + by).clamp(0, list.len() as i32 - 1) as usize]
}

/// Cycles to the next entry of `list` after `cur`.
pub(super) fn cycle<T: PartialEq + Copy>(list: &[T], cur: T) -> T {
    let i = list.iter().position(|&x| x == cur).unwrap_or(0);
    list[(i + 1) % list.len()]
}

#[cfg(test)]
pub(super) fn renders(lab: &mut dyn Lab, keys: &[KeyCode]) {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    for (w, h) in [(60, 20), (120, 40), (200, 60)] {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| draw(f, f.area(), "PAGE", lab, &Theme::default()))
            .unwrap();
        for &k in keys {
            for _ in 0..30 {
                lab.key(k);
                term.draw(|f| draw(f, f.area(), "PAGE", lab, &Theme::default()))
                    .unwrap();
            }
        }
    }
}

/// Text dump of a lab at 150 x 46, for eyeballing the layout in a test run.
#[cfg(test)]
pub(super) fn dump(lab: &dyn Lab) -> String {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    let mut term = Terminal::new(TestBackend::new(150, 46)).unwrap();
    term.draw(|f| draw(f, f.area(), "PAGE", lab, &Theme::default()))
        .unwrap();
    let b = term.backend().buffer().clone();
    (0..b.area.height)
        .map(|y| {
            (0..b.area.width)
                .map(|x| b[(x, y)].symbol().to_string())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// PNG of a lab at 150 x 46 cells (4 x 8 px each): half-blocks as their two colours, text as dim
/// marks. For eyeballing the pictures: `cargo test -q lab_pngs -- --ignored`, with LAB_PNG_DIR set.
#[cfg(test)]
#[test]
#[ignore]
fn lab_pngs() {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    let dir = std::env::var("LAB_PNG_DIR").expect("LAB_PNG_DIR");
    let rgb = |c: Color, dflt: [u8; 3]| match c {
        Color::Rgb(r, g, b) => [r, g, b],
        Color::Reset => dflt,
        _ => [200, 200, 200],
    };
    for page in [
        "LOGIC DIE",
        "MICROBUMP",
        "INTERPOSER",
        "SUBSTRATE",
        "ASSEMBLY",
        "BOARD",
    ] {
        let lab = new_lab(page).unwrap();
        let mut term = Terminal::new(TestBackend::new(150, 46)).unwrap();
        term.draw(|f| draw(f, f.area(), page, lab.as_ref(), &Theme::default()))
            .unwrap();
        let b = term.backend().buffer().clone();
        let (cw, ch) = (4u32, 8u32);
        let bg = [0x28, 0x2a, 0x36];
        let mut img = image::RgbImage::from_pixel(150 * cw, 46 * ch, image::Rgb(bg));
        for y in 0..46u16 {
            for x in 0..150u16 {
                let c = &b[(x, y)];
                let (top, bot) = if c.symbol() == "\u{2580}" {
                    (rgb(c.fg, bg), rgb(c.bg, bg))
                } else if c.symbol().trim().is_empty() {
                    (bg, bg)
                } else {
                    let f = rgb(c.fg, [220, 220, 220]);
                    let m = [
                        f[0] / 2 + bg[0] / 2,
                        f[1] / 2 + bg[1] / 2,
                        f[2] / 2 + bg[2] / 2,
                    ];
                    (m, m)
                };
                for py in 0..ch {
                    for px in 0..cw {
                        let col = if py < ch / 2 { top } else { bot };
                        img.put_pixel(x as u32 * cw + px, y as u32 * ch + py, image::Rgb(col));
                    }
                }
            }
        }
        img.save(format!("{dir}/{}.png", page.replace(' ', "_")))
            .unwrap();
    }
}
