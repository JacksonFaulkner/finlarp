// Positions tab: one container, holding card + table on the left (see
// holding.rs), weights pie on the right sized to the height, joined by an
// arrow from the card to the selected slice. Each row carries its slice's
// color, and the selected row lights up its slice while the rest dim. Real data (DuckDB, filled by the
// E*TRADE pull), largest position first, cash last.

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Widget};

use super::data::{Position, Totals, Txn};
use super::holding::{self, Closes};
use super::overview::money;
use crate::ui::theme::Theme;

const CASH: Color = Color::Rgb(0x6b, 0x70, 0x89);
/// Most of the width the pie may take, in percent.
const PIE_MAX_PCT: u16 = 45;
/// Columns between the card and the pie, for the arrow.
const GAP: u16 = 5;
/// Card height (border + text + a readable chart) the table won't eat into.
const CARD_MIN: u16 = holding::TEXT_ROWS + 2 + 6;
/// Subpixels the selected slice sticks out past the others.
const GROW: f64 = 2.0;
/// How much of an unselected slice's color survives (1.0 = full).
const DIM: f64 = 0.75;

pub struct Entry<'a> {
    pub label: &'a str,
    pub value: f64,
    pub color: Color,
    /// None for the cash row.
    pub pos: Option<&'a Position>,
}

/// Golden-angle hue steps keep neighbouring slices far apart on the wheel;
/// alternating lightness separates the ones that still land close.
fn slice_color(i: usize) -> Color {
    let h = (i as f64 * 137.508) % 360.0;
    let (s, l) = if i % 2 == 0 {
        (0.65, 0.55)
    } else {
        (0.75, 0.68)
    };
    hsl(h, s, l)
}

fn hsl(h: f64, s: f64, l: f64) -> Color {
    let c = (1.0 - (2.0 * l - 1.0).abs()) * s;
    let x = c * (1.0 - ((h / 60.0) % 2.0 - 1.0).abs());
    let m = l - c / 2.0;
    let (r, g, b) = match h as u32 / 60 {
        0 => (c, x, 0.0),
        1 => (x, c, 0.0),
        2 => (0.0, c, x),
        3 => (0.0, x, c),
        4 => (x, 0.0, c),
        _ => (c, 0.0, x),
    };
    let ch = |v: f64| ((v + m) * 255.0).round() as u8;
    Color::Rgb(ch(r), ch(g), ch(b))
}

/// Blend `c` toward `bg` by `keep` (1.0 = unchanged).
fn fade(c: Color, bg: Color, keep: f64) -> Color {
    match (c, bg) {
        (Color::Rgb(r, g, b), Color::Rgb(br, bgc, bb)) => {
            let mix =
                |a: u8, b: u8| (f64::from(a) * keep + f64::from(b) * (1.0 - keep)).round() as u8;
            Color::Rgb(mix(r, br), mix(g, bgc), mix(b, bb))
        }
        _ => c,
    }
}

/// Holdings by value descending, then cash (if any).
pub fn entries(positions: &[Position], cash: f64) -> Vec<Entry<'_>> {
    let mut held: Vec<&Position> = positions.iter().filter(|p| p.value > 0.0).collect();
    held.sort_by(|a, b| {
        b.value
            .total_cmp(&a.value)
            .then_with(|| a.symbol.cmp(&b.symbol))
    });
    let mut out: Vec<Entry> = held
        .into_iter()
        .enumerate()
        .map(|(i, p)| Entry {
            label: &p.symbol,
            value: p.value,
            color: slice_color(i),
            pos: Some(p),
        })
        .collect();
    if cash > 0.0 {
        out.push(Entry {
            label: "Cash",
            value: cash,
            color: CASH,
            pos: None,
        });
    }
    out
}

/// Number of selectable rows on the tab.
pub fn len(positions: &[Position], cash: f64) -> usize {
    entries(positions, cash).len()
}

/// Filled circle made of half-block cells (two square subpixels per cell),
/// sized to the whole area. Slices run clockwise from 12 o'clock.
struct Pie<'a> {
    entries: &'a [Entry<'a>],
    sel: usize,
    bg: Color,
    /// Degrees the whole pie is turned clockwise.
    rot: f64,
}

impl Widget for Pie<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let total: f64 = self.entries.iter().map(|e| e.value).sum();
        if total <= 0.0 || area.width < 2 || area.height < 2 {
            return;
        }
        let (w, h) = (f64::from(area.width), f64::from(area.height) * 2.0);
        // The selected slice grows GROW subpixels past the base radius; the
        // base is shrunk so the grown edge still fits the area.
        let r_full = w.min(h) / 2.0;
        let r = (r_full - GROW).max(1.0);
        let r_sel = r + GROW.min(r_full - r);
        let (cx, cy) = (w / 2.0, h / 2.0);
        let sole = self.entries.len() == 1;
        // Cumulative slice ends in degrees.
        let mut acc = 0.0;
        let ends: Vec<f64> = self
            .entries
            .iter()
            .map(|e| {
                acc += e.value / total * 360.0;
                acc
            })
            .collect();
        let at = |px: f64, py: f64| -> Option<Color> {
            let (dx, dy) = (px + 0.5 - cx, py + 0.5 - cy);
            let d = (dx * dx + dy * dy).sqrt();
            if d > r_sel {
                return None;
            }
            let ang = (dx.atan2(-dy).to_degrees() - self.rot).rem_euclid(360.0);
            let i = ends.iter().position(|e| ang < *e).unwrap_or(ends.len() - 1);
            let e = &self.entries[i];
            if i != self.sel {
                return (d <= r).then(|| fade(e.color, self.bg, DIM));
            }
            // Outline: outer rim plus the two radial edges, ~1 subpixel wide.
            let start = if i == 0 { 0.0 } else { ends[i - 1] };
            let edge = (ang - start).min(ends[i] - ang).to_radians() * d;
            let rim = d > r_sel - 1.0;
            Some(if rim || (!sole && edge < 1.0) {
                fade(e.color, Color::Rgb(255, 255, 255), 0.55)
            } else {
                e.color
            })
        };
        for row in 0..area.height {
            for col in 0..area.width {
                let (x, y) = (f64::from(col), f64::from(row) * 2.0);
                let (top, bot) = (at(x, y), at(x, y + 1.0));
                let (sym, style) = match (top, bot) {
                    (None, None) => continue,
                    (Some(t), Some(b)) => ("▀", Style::new().fg(t).bg(b)),
                    (Some(t), None) => ("▀", Style::new().fg(t)),
                    (None, Some(b)) => ("▄", Style::new().fg(b)),
                };
                buf[(area.x + col, area.y + row)]
                    .set_symbol(sym)
                    .set_style(style);
            }
        }
    }
}

impl Pie<'_> {
    /// Cell just outside the circle's 9 o'clock point, where the selected
    /// slice's centre sits once the pie has turned.
    fn left_edge(area: Rect) -> (u16, u16) {
        let (w, h) = (f64::from(area.width), f64::from(area.height) * 2.0);
        let r = w.min(h) / 2.0;
        let col = (w / 2.0 - r - 0.5).ceil().max(0.0) as u16;
        (area.x + col, area.y + area.height / 2)
    }
}

/// Elbow connector from `from` (just right of the card) to `to` (the pie's
/// left edge), ending in an arrowhead that points at the slice.
fn arrow(buf: &mut Buffer, from: (u16, u16), to: (u16, u16), color: Color) {
    let ((x0, y0), (x1, y1)) = (from, to);
    if x1 < x0 + 3 || y0 >= buf.area.bottom() || y1 >= buf.area.bottom() || x1 >= buf.area.right() {
        return;
    }
    let style = Style::new().fg(color);
    let mut put = |x: u16, y: u16, s: &str| {
        buf[(x, y)].set_symbol(s).set_style(style);
    };
    let xm = x0 + (x1 - x0) / 2;
    for x in x0..xm {
        put(x, y0, "─");
    }
    for x in xm + 1..x1 - 1 {
        put(x, y1, "─");
    }
    if y0 == y1 {
        put(xm, y0, "─");
    } else {
        let down = y1 > y0;
        put(xm, y0, if down { "╮" } else { "╯" });
        put(xm, y1, if down { "╰" } else { "╭" });
        for y in y0.min(y1) + 1..y0.max(y1) {
            put(xm, y, "│");
        }
    }
    put(x1 - 1, y1, "▶");
}

/// Rotation (degrees clockwise) that puts entry `sel`'s slice centre at
/// 9 o'clock, facing the side panel.
pub fn facing_left(positions: &[Position], cash: f64, sel: usize) -> f64 {
    let rows = entries(positions, cash);
    let total: f64 = rows.iter().map(|e| e.value).sum();
    if total <= 0.0 || rows.is_empty() {
        return 0.0;
    }
    let sel = sel.min(rows.len() - 1);
    let before: f64 = rows[..sel].iter().map(|e| e.value).sum();
    let centre = (before + rows[sel].value / 2.0) / total * 360.0;
    270.0 - centre
}

pub struct View<'a> {
    pub theme: &'a Theme,
    pub positions: &'a [Position],
    pub tot: &'a Totals,
    pub txns: &'a [Txn],
    pub closes: &'a Closes,
    pub sel: usize,
    pub rot: f64,
    pub today: NaiveDate,
}

pub fn draw(frame: &mut Frame, area: Rect, v: &View) {
    let t = v.theme;
    let block = Block::bordered()
        .border_style(t.border())
        .title_top(Line::from(vec![
            Span::styled(" Positions ", t.title()),
            Span::styled(format!("· {} ", money(v.tot.value)), t.dim()),
        ]))
        .style(t.base());
    let inner = block.inner(area);
    frame.render_widget(block, area);
    let rows = entries(v.positions, v.tot.cash);
    if rows.is_empty() {
        return;
    }
    let sel = v.sel.min(rows.len() - 1);
    // Cells are ~2:1, so a circle `h` rows tall is `2h` columns wide. Size
    // the pie to that instead of giving it a fixed share of the width.
    let pie_w = (inner.height * 2).min(inner.width * PIE_MAX_PCT / 100);
    let [side, _, pie_col] = inner.layout(&Layout::horizontal([
        Constraint::Fill(1),
        Constraint::Length(GAP),
        Constraint::Length(pie_w),
    ]));
    let pie_area = pie_col.centered_vertically(Constraint::Length(pie_w.div_ceil(2)));
    frame.render_widget(
        Pie {
            entries: &rows,
            sel,
            bg: t.bg.unwrap_or(Color::Rgb(0x28, 0x2a, 0x36)),
            rot: v.rot,
        },
        pie_area,
    );

    // Table gets its full height unless that would squeeze the card below
    // CARD_MIN; then it scrolls.
    let want = rows.len() as u16 + 1;
    let table_h = want
        .min(side.height.saturating_sub(CARD_MIN))
        .max(want.min(side.height / 3));
    let [spot, _, names] = side.layout(&Layout::vertical([
        Constraint::Fill(1),
        Constraint::Length(u16::from(table_h > 0)),
        Constraint::Length(table_h),
    ]));
    let tv = holding::TableView {
        theme: t,
        rows: &rows,
        tot: v.tot,
        txns: v.txns,
        closes: v.closes,
        sel,
        today: v.today,
    };
    if spot.height > 2 {
        holding::spotlight(frame, spot, &tv);
        let from = (spot.right(), spot.y + spot.height / 2);
        let to = Pie::left_edge(pie_area);
        arrow(frame.buffer_mut(), from, to, rows[sel].color);
    }
    holding::table(frame, names, &tv);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pos(sym: &str, value: f64) -> Position {
        Position {
            symbol: sym.into(),
            qty: 1.0,
            price: value,
            price_paid: value,
            total_gain: 0.0,
            value,
            day_gain: 0.0,
            day_pct: 0.0,
            industry: "x".into(),
        }
    }

    #[test]
    fn sorted_by_value_with_cash_last() {
        let ps = [pos("B", 10.0), pos("A", 30.0), pos("C", 0.0)];
        let e = entries(&ps, 5.0);
        let names: Vec<&str> = e.iter().map(|e| e.label).collect();
        assert_eq!(names, ["A", "B", "Cash"]);
        assert_eq!(len(&ps, 0.0), 2);
    }

    #[test]
    fn selected_slice_centre_faces_left() {
        let ps = [pos("A", 50.0), pos("B", 25.0), pos("C", 25.0)];
        // A spans 0..180, centre 90: turn +180 to reach 9 o'clock.
        assert!((facing_left(&ps, 0.0, 0) - 180.0).abs() < 1e-9);
        // B spans 180..270, centre 225: turn +45.
        assert!((facing_left(&ps, 0.0, 1) - 45.0).abs() < 1e-9);
    }

    #[test]
    fn colors_are_distinct() {
        let cs: Vec<Color> = (0..15).map(slice_color).collect();
        for (i, a) in cs.iter().enumerate() {
            assert!(!cs[i + 1..].contains(a));
        }
    }
}
