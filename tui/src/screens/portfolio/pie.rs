// Positions tab: one container, holding card + table on the left (see
// holding.rs), weights pie on the right sized to the height, joined by an
// arrow from the card to the selected slice. Each row carries its slice's
// color, and the selected row lights up its slice while the rest dim. Real data (DuckDB, filled by the
// E*TRADE pull), largest position first, cash last. The pie itself lives in
// ui/pie.rs; this file maps positions onto its slices.

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Color;
use ratatui::text::{Line, Span};
use ratatui::widgets::Block;

use super::data::{Position, Totals, Txn};
use super::holding::{self, Closes};
use super::overview::money;
use crate::ui::pie::{self as ring, Pie, Slice, slice_color};
use crate::ui::theme::Theme;

const CASH: Color = Color::Rgb(0x6b, 0x70, 0x89);
/// Most of the width the pie may take, in percent.
const PIE_MAX_PCT: u16 = 45;
/// Columns between the card and the pie, for the arrow.
const GAP: u16 = 5;
/// Card height (border + text + a readable chart) the table won't eat into.
const CARD_MIN: u16 = holding::TEXT_ROWS + 2 + 6;
/// How much of an unselected slice's color survives (1.0 = full).
const DIM: f64 = 0.75;

pub struct Entry<'a> {
    pub label: &'a str,
    pub value: f64,
    pub color: Color,
    /// None for the cash row.
    pub pos: Option<&'a Position>,
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

/// Rotation (degrees clockwise) that puts entry `sel`'s slice centre at
/// 9 o'clock, facing the side panel.
pub fn facing_left(positions: &[Position], cash: f64, sel: usize) -> f64 {
    let values: Vec<f64> = entries(positions, cash).iter().map(|e| e.value).collect();
    ring::facing_left(&values, sel)
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
    let slices: Vec<Slice> = rows
        .iter()
        .map(|e| Slice {
            value: e.value,
            color: e.color,
        })
        .collect();
    frame.render_widget(
        Pie {
            slices: &slices,
            sel,
            bg: t.bg.unwrap_or(Color::Rgb(0x28, 0x2a, 0x36)),
            dim: DIM,
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
        let to = ring::left_edge(pie_area);
        // Elbow connector from the card to the pie's left edge.
        ring::arrow(frame.buffer_mut(), from, to, rows[sel].color);
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
}
