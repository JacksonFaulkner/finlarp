// Chart helpers shared by screens. Missing data is drawn as a gap, never
// as zero. Each helper is a Widget (usable with render_widget or inside
// other widgets) plus a thin `fn` wrapper taking a Frame.
//
//   GroupedBars  vertical bars, `value` beside `compare`; BarChart::grouped
//                when all values are >= 0, a two-sided custom bar around a
//                zero axis when any are negative
//   SparkBars    Sparkline with SparklineBar per point (None = absent symbol),
//                stretched to fill the width, cursor point highlighted
//   LineChart    Chart with Braille/Octant lines; None splits the line into
//                segments; optional colour-by-sign split at zero crossings;
//                the cursor point (and optional guide line) are own datasets

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::symbols::Marker;
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    Axis, Bar, BarChart, BarGroup, Block, Chart, Dataset, GraphType, Sparkline, SparklineBar,
    Widget,
};

use crate::model::{BarItem, Point};
use crate::ui::text;
use crate::ui::theme::Theme;

/// Grouped bars: `value` (signed colour) beside `compare` (dim) per item,
/// with the selected index highlighted. Handles negative values.
pub fn grouped_bars(
    frame: &mut Frame,
    area: Rect,
    items: &[BarItem],
    selected: Option<usize>,
    theme: &Theme,
) {
    frame.render_widget(
        GroupedBars {
            items,
            selected,
            theme,
        },
        area,
    );
}

/// One-line sparkline; None points render as absent (gap symbol).
pub fn sparkline(frame: &mut Frame, area: Rect, points: &[Point], theme: &Theme) {
    frame.render_widget(
        SparkBars {
            points,
            selected: None,
            theme,
        },
        area,
    );
}

/// Line chart over points with a cursor at `selected`; x labels from Point.x.
pub fn line_chart(
    frame: &mut Frame,
    area: Rect,
    title: &str,
    points: &[Point],
    selected: Option<usize>,
    theme: &Theme,
) {
    frame.render_widget(
        LineChart::new(points, theme)
            .title(title)
            .selected(selected),
        area,
    );
}

// ---------------------------------------------------------------- bars

pub struct GroupedBars<'a> {
    pub items: &'a [BarItem],
    pub selected: Option<usize>,
    pub theme: &'a Theme,
}

/// Resolution the f64 values are scaled to for BarChart's u64 bars.
const SCALE: f64 = 10_000.0;

impl Widget for GroupedBars<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        buf.set_style(area, self.theme.base());
        if self.items.is_empty() || area.is_empty() {
            return;
        }
        if self
            .items
            .iter()
            .any(|i| i.value < 0.0 || i.compare.is_some_and(|c| c < 0.0))
        {
            two_sided(&self, area, buf);
        } else {
            grouped(&self, area, buf);
        }
    }
}

fn per_group(items: &[BarItem]) -> u16 {
    if items.iter().any(|i| i.compare.is_some()) {
        2
    } else {
        1
    }
}

/// Bar width that fits n groups of g bars with 1-cell group gaps.
fn bar_width(area: Rect, n: usize, g: u16) -> u16 {
    let n = n as u16;
    let avail = area.width.saturating_sub(n.saturating_sub(1));
    (avail / (n * g).max(1)).clamp(1, 9)
}

fn grouped(w: &GroupedBars, area: Rect, buf: &mut Buffer) {
    let th = w.theme;
    let max = w
        .items
        .iter()
        .flat_map(|i| [Some(i.value), i.compare])
        .flatten()
        .fold(0.0_f64, f64::max);
    let scale = |v: f64| {
        if max > 0.0 {
            (v / max * SCALE).round() as u64
        } else {
            0
        }
    };
    let g = per_group(w.items);
    let bw = bar_width(area, w.items.len(), g);
    let groups: Vec<BarGroup> = w
        .items
        .iter()
        .enumerate()
        .map(|(i, it)| {
            let sel = w.selected == Some(i);
            let style = if sel {
                th.accent()
            } else {
                th.signed(it.value)
            };
            let mut bars = vec![
                Bar::new(scale(it.value))
                    .style(style)
                    .value_style(th.selected())
                    .text_value(text::fmt_num(it.value)),
            ];
            if g == 2 {
                bars.push(match it.compare {
                    Some(c) => Bar::new(scale(c))
                        .style(th.dim())
                        .value_style(th.selected())
                        .text_value(text::fmt_num(c)),
                    None => Bar::new(0).text_value(""),
                });
            }
            let label = text::truncate(&it.label, (bw * g) as usize);
            BarGroup::new(bars)
                .label(Line::styled(label, if sel { th.accent() } else { th.dim() }).centered())
        })
        .collect();
    BarChart::grouped(groups)
        .bar_width(bw)
        .bar_gap(0)
        .group_gap(1)
        .max(SCALE as u64)
        .style(th.base())
        .render(area, buf);
}

/// Mixed-sign bars: a zero axis row, positive bars grow up (1/8 cell
/// resolution), negative bars grow down (1/2 cell). Labels on the last row.
fn two_sided(w: &GroupedBars, area: Rect, buf: &mut Buffer) {
    let th = w.theme;
    let [plot, labels] = area.layout(&Layout::vertical([
        Constraint::Fill(1),
        Constraint::Length(1),
    ]));
    if plot.height < 2 {
        return;
    }
    let vals = w
        .items
        .iter()
        .flat_map(|i| [Some(i.value), i.compare])
        .flatten();
    let (lo, hi) = vals.fold((0.0_f64, 0.0_f64), |(l, h), v| (l.min(v), h.max(v)));
    let span = (hi - lo).max(f64::EPSILON);
    // rows above the axis for positives, below for negatives (axis row itself separate)
    let rows = plot.height.saturating_sub(1) as f64;
    let up_rows = ((hi / span) * rows).round() as u16;
    let axis_y = plot.y + up_rows;
    let down_rows = plot.bottom().saturating_sub(axis_y + 1);
    let unit = if up_rows > 0 {
        hi / up_rows as f64
    } else {
        -lo / down_rows.max(1) as f64
    };
    for x in plot.left()..plot.right() {
        buf[(x, axis_y)].set_symbol("─").set_style(th.border());
    }
    let g = per_group(w.items);
    let bw = bar_width(area, w.items.len(), g);
    let mut x = plot.x;
    for (i, it) in w.items.iter().enumerate() {
        let sel = w.selected == Some(i);
        let bars = [Some(it.value), if g == 2 { it.compare } else { None }];
        for (bi, v) in bars.iter().take(g as usize).enumerate() {
            let style = match (sel, bi) {
                (true, _) => th.accent(),
                (false, 0) => th.signed(it.value),
                _ => th.dim(),
            };
            if let Some(v) = *v {
                let r = Rect {
                    x,
                    width: bw,
                    ..plot
                }
                .intersection(plot);
                draw_signed_bar(buf, r, axis_y, v, unit, style);
            }
            x = x.saturating_add(bw);
        }
        let group = Rect {
            x: x.saturating_sub(bw * g),
            width: bw * g,
            ..labels
        }
        .intersection(labels);
        let label = text::truncate(&it.label, group.width as usize);
        Line::styled(label, if sel { th.accent() } else { th.dim() })
            .centered()
            .render(group, buf);
        x = x.saturating_add(1);
        if x >= plot.right() {
            break;
        }
    }
}

fn draw_signed_bar(
    buf: &mut Buffer,
    r: Rect,
    axis_y: u16,
    v: f64,
    unit: f64,
    style: ratatui::style::Style,
) {
    if r.is_empty() || unit <= 0.0 {
        return;
    }
    const EIGHTHS: [&str; 9] = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"];
    let cells = v.abs() / unit;
    if v >= 0.0 {
        let mut e = (cells * 8.0).round() as u32; // eighths remaining
        let mut y = axis_y;
        while e > 0 && y > r.y {
            y -= 1;
            let s = EIGHTHS[e.min(8) as usize];
            for x in r.left()..r.right() {
                buf[(x, y)].set_symbol(s).set_style(style);
            }
            e = e.saturating_sub(8);
        }
    } else {
        let mut halves = (cells * 2.0).round() as u32;
        let mut y = axis_y + 1;
        while halves > 0 && y < r.bottom() {
            let s = if halves >= 2 { "█" } else { "▀" };
            for x in r.left()..r.right() {
                buf[(x, y)].set_symbol(s).set_style(style);
            }
            halves = halves.saturating_sub(2);
            y += 1;
        }
    }
}

// ---------------------------------------------------------------- sparkline

/// Widest a single point is stretched to.
const MAX_PER_POINT: usize = 3;

pub struct SparkBars<'a> {
    pub points: &'a [Point],
    /// Highlighted point (the block_view cursor).
    pub selected: Option<usize>,
    pub theme: &'a Theme,
}

impl SparkBars<'_> {
    /// Columns per point when stretched over `width` (>= 1), and the index
    /// of the first point shown (the most recent points win when they don't fit).
    pub fn geometry(&self, width: u16) -> (u16, usize) {
        let n = self.points.len().max(1);
        let per = (width as usize / n).clamp(1, MAX_PER_POINT) as u16;
        let first = self.points.len().saturating_sub(width as usize);
        (per, first)
    }
}

impl Widget for SparkBars<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if self.points.is_empty() || area.is_empty() {
            return;
        }
        // min..max scaling: a sparkline shows shape (the values sit beside it)
        let ys = self
            .points
            .iter()
            .filter_map(|p| p.y)
            .filter(|y| y.is_finite());
        let (lo, hi) = ys.fold((f64::MAX, f64::MIN), |(l, h), y| (l.min(y), h.max(y)));
        let span = hi - lo;
        let (per, first) = self.geometry(area.width);
        let mut data: Vec<SparklineBar> = Vec::new();
        for (i, p) in self.points.iter().enumerate().skip(first) {
            // the floor of 100 keeps the minimum visible (▁), distinct from absent (·)
            let v = p.y.map(|y| {
                if span > 0.0 {
                    ((y - lo) / span * 900.0) as u64 + 100
                } else {
                    500
                }
            });
            let style = if self.selected == Some(i) {
                th.accent()
            } else {
                match p.y {
                    Some(y) if y < 0.0 => th.down(),
                    _ => th.up(),
                }
            };
            for _ in 0..per {
                data.push(SparklineBar::from(v).style(Some(style)));
            }
        }
        Sparkline::default()
            .data(data)
            .max(1000)
            .style(th.up())
            .absent_value_symbol("·")
            .absent_value_style(th.dim())
            .render(area, buf);
    }
}

// ---------------------------------------------------------------- line chart

/// Line chart widget. Build with `LineChart::new(points, theme)` and the
/// builder methods; `line_chart()` is the plain default.
///
///   .signed(true)       colour by sign (up >= 0, down < 0), splitting the
///                       line at zero crossings; 0 is kept in the y range
///   .marker(m)          Braille (default) or Octant / HalfBlock ...
///   .unit("%")          suffix on y-axis labels
///   .cursor_line(true)  vertical guide through the selected point
pub struct LineChart<'a> {
    pub title: &'a str,
    pub points: &'a [Point],
    pub selected: Option<usize>,
    pub theme: &'a Theme,
    pub signed: bool,
    pub marker: Marker,
    pub unit: &'a str,
    pub cursor_line: bool,
}

impl<'a> LineChart<'a> {
    pub fn new(points: &'a [Point], theme: &'a Theme) -> Self {
        Self {
            title: "",
            points,
            selected: None,
            theme,
            signed: false,
            marker: Marker::Braille,
            unit: "",
            cursor_line: false,
        }
    }
    pub fn title(mut self, title: &'a str) -> Self {
        self.title = title;
        self
    }
    pub fn selected(mut self, selected: Option<usize>) -> Self {
        self.selected = selected;
        self
    }
    pub fn signed(mut self, signed: bool) -> Self {
        self.signed = signed;
        self
    }
    pub fn marker(mut self, marker: Marker) -> Self {
        self.marker = marker;
        self
    }
    pub fn unit(mut self, unit: &'a str) -> Self {
        self.unit = unit;
        self
    }
    pub fn cursor_line(mut self, on: bool) -> Self {
        self.cursor_line = on;
        self
    }
}

/// Contiguous runs of Some points (None splits the line so it's a gap).
fn runs(points: &[Point]) -> Vec<Vec<(f64, f64)>> {
    let mut runs: Vec<Vec<(f64, f64)>> = vec![Vec::new()];
    for (i, p) in points.iter().enumerate() {
        match (p.y, runs.last_mut()) {
            (Some(y), Some(run)) if y.is_finite() => run.push((i as f64, y)),
            _ => runs.push(Vec::new()),
        }
    }
    runs.retain(|r| !r.is_empty());
    runs
}

/// Split a run into same-sign segments; each crossing gets an interpolated
/// (x, 0) point shared by both sides so the line stays continuous.
fn split_by_sign(run: &[(f64, f64)]) -> Vec<(bool, Vec<(f64, f64)>)> {
    let mut out: Vec<(bool, Vec<(f64, f64)>)> = Vec::new();
    for &(x, y) in run {
        let up = y >= 0.0;
        match out.last_mut() {
            Some((seg_up, seg)) if *seg_up == up => seg.push((x, y)),
            Some((_, seg)) => {
                let (x0, y0) = seg.last().copied().unwrap_or((x, y));
                let xc = if y != y0 {
                    x0 + (0.0 - y0) * (x - x0) / (y - y0)
                } else {
                    x
                };
                seg.push((xc, 0.0));
                out.push((up, vec![(xc, 0.0), (x, y)]));
            }
            None => out.push((up, vec![(x, y)])),
        }
    }
    out
}

impl Widget for LineChart<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if area.is_empty() {
            return;
        }
        let runs = runs(self.points);
        let ys = runs.iter().flatten().map(|&(_, y)| y);
        let init = if self.signed {
            (0.0, 0.0)
        } else {
            (f64::MAX, f64::MIN)
        };
        let (lo, hi) = ys.fold(init, |(l, h): (f64, f64), y| (l.min(y), h.max(y)));
        let (lo, hi) = if lo > hi {
            (0.0, 1.0)
        } else if lo == hi {
            (lo - 1.0, hi + 1.0)
        } else {
            (lo, hi)
        };
        let pad = (hi - lo) * 0.05;
        let bounds = [lo - pad, hi + pad];
        let n = self.points.len();
        let xmax = n.saturating_sub(1).max(1) as f64;

        let cursor: Vec<(f64, f64)> = self
            .selected
            .and_then(|i| self.points.get(i).and_then(|p| p.y).map(|y| (i as f64, y)))
            .into_iter()
            .collect();
        let guide: Vec<(f64, f64)> = match self.selected {
            Some(i) if self.cursor_line && i < n => {
                vec![(i as f64, bounds[0]), (i as f64, bounds[1])]
            }
            _ => vec![],
        };
        let segments: Vec<(bool, Vec<(f64, f64)>)> = if self.signed {
            runs.iter().flat_map(|r| split_by_sign(r)).collect()
        } else {
            runs.iter().map(|r| (true, r.clone())).collect()
        };

        // guide first so the data draws over it
        let mut datasets = vec![
            Dataset::default()
                .marker(Marker::Braille)
                .graph_type(GraphType::Line)
                .style(th.border())
                .data(&guide),
        ];
        for (up, seg) in &segments {
            let style = if *up { th.up() } else { th.down() };
            // a lone point between gaps would be invisible as a line: scatter it
            let kind = if seg.len() == 1 {
                GraphType::Scatter
            } else {
                GraphType::Line
            };
            datasets.push(
                Dataset::default()
                    .marker(self.marker)
                    .graph_type(kind)
                    .style(style)
                    .data(seg),
            );
        }
        datasets.push(
            Dataset::default()
                .marker(Marker::Dot)
                .graph_type(GraphType::Scatter)
                .style(th.accent())
                .data(&cursor),
        );

        let x_labels: Vec<Line> = match n {
            0 => vec![],
            1 => vec![Line::from(self.points[0].x.clone())],
            _ => vec![
                Line::from(self.points[0].x.clone()),
                Line::from(self.points[n / 2].x.clone()),
                Line::from(self.points[n - 1].x.clone()),
            ],
        };
        let lbl = |v: f64| Line::from(format!("{}{}", text::fmt_num(v), self.unit));
        let y_labels = if self.signed && lo < 0.0 && hi > 0.0 {
            vec![lbl(lo), lbl(0.0), lbl(hi)]
        } else {
            vec![lbl(lo), lbl(hi)]
        };
        let sel_note = self.selected.and_then(|i| self.points.get(i)).map(|p| {
            let v =
                p.y.map(|y| format!("{}{}", text::fmt_num(y), self.unit))
                    .unwrap_or_else(|| "–".into());
            let style = if self.signed {
                p.y.map_or(th.dim(), |y| th.signed(y))
            } else {
                th.accent()
            };
            Line::from(vec![
                Span::styled(format!("{} ", p.x), th.dim()),
                Span::styled(v, style),
            ])
            .right_aligned()
        });
        let mut block = Block::new();
        if !self.title.is_empty() {
            block = block.title_top(Line::styled(self.title.to_string(), th.title()));
        }
        if let Some(note) = sel_note {
            block = block.title_top(note);
        }
        Chart::new(datasets)
            .block(block)
            .style(th.base())
            .x_axis(
                Axis::default()
                    .bounds([0.0, xmax])
                    .labels(x_labels)
                    .style(th.dim()),
            )
            .y_axis(
                Axis::default()
                    .bounds(bounds)
                    .labels(y_labels)
                    .style(th.dim()),
            )
            .render(area, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn pts(ys: &[Option<f64>]) -> Vec<Point> {
        ys.iter()
            .enumerate()
            .map(|(i, y)| Point {
                x: format!("Q{i}"),
                y: *y,
                src: None,
            })
            .collect()
    }
    fn bars(vs: &[(f64, Option<f64>)]) -> Vec<BarItem> {
        vs.iter()
            .enumerate()
            .map(|(i, (v, c))| BarItem {
                label: format!("L{i}"),
                value: *v,
                compare: *c,
                src: None,
            })
            .collect()
    }
    fn draw(w: u16, h: u16, f: impl Fn(&mut Frame)) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|fr| f(fr)).unwrap();
        let b = t.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn sparkline_gaps_for_none() {
        let th = Theme::default();
        let p = pts(&[Some(1.0), None, Some(3.0)]);
        let out = draw(3, 1, |f| sparkline(f, f.area(), &p, &th));
        assert_eq!(out.chars().nth(1), Some('·'), "{out}");
        assert_ne!(out.chars().nth(2), Some(' '));
        // stretched: 2 columns per point
        let out = draw(6, 1, |f| sparkline(f, f.area(), &p, &th));
        assert_eq!(&out.chars().skip(2).take(2).collect::<String>(), "··");
    }

    #[test]
    fn grouped_bars_positive_and_negative() {
        let th = Theme::default();
        let b = bars(&[(1.0, Some(0.8)), (2.0, Some(2.5))]);
        let out = draw(20, 8, |f| grouped_bars(f, f.area(), &b, Some(1), &th));
        assert!(out.contains("L0") && out.contains("L1"), "{out}");
        assert!(out.contains('█'));
        let b = bars(&[(1.0, None), (-2.0, None)]);
        let out = draw(12, 7, |f| grouped_bars(f, f.area(), &b, None, &th));
        let rows: Vec<&str> = out.lines().collect();
        let axis = rows.iter().position(|r| r.contains('─')).expect("axis row");
        assert!(
            rows[..axis]
                .iter()
                .any(|r| r.chars().any(|c| "▁▂▃▄▅▆▇█".contains(c))),
            "{out}"
        );
        assert!(
            rows[axis + 1..]
                .iter()
                .any(|r| r.contains('█') || r.contains('▀')),
            "{out}"
        );
    }

    #[test]
    fn line_chart_draws_and_labels_cursor() {
        let th = Theme::default();
        let p = pts(&[Some(1.0), Some(2.0), None, Some(4.0), Some(3.0)]);
        let out = draw(40, 10, |f| {
            line_chart(f, f.area(), "Revenue", &p, Some(3), &th)
        });
        assert!(out.contains("Revenue"), "{out}");
        assert!(out.contains("Q3 4"), "{out}");
        assert!(out.contains('•'), "{out}");
    }

    #[test]
    fn signed_line_splits_at_zero() {
        let segs = split_by_sign(&[(0.0, 1.0), (1.0, -1.0), (2.0, -2.0), (3.0, 2.0)]);
        assert_eq!(segs.len(), 3);
        assert_eq!(segs[0], (true, vec![(0.0, 1.0), (0.5, 0.0)]));
        assert!(!segs[1].0);
        assert_eq!(segs[1].1.first(), Some(&(0.5, 0.0)));
        assert_eq!(segs[2].1.first().map(|p| p.1), Some(0.0));
        let th = Theme::default();
        let p = pts(&[Some(1.0), Some(-2.0), Some(3.0)]);
        let out = draw(40, 10, |f| {
            f.render_widget(
                LineChart::new(&p, &th)
                    .signed(true)
                    .marker(Marker::Octant)
                    .unit("%")
                    .selected(Some(1))
                    .cursor_line(true),
                f.area(),
            )
        });
        assert!(out.contains("0%"), "{out}");
        assert!(out.contains("Q1 -2%"), "{out}");
    }

    #[test]
    fn tiny_and_empty() {
        let th = Theme::default();
        let p = pts(&[Some(-1.0), None, Some(3.0)]);
        let b = bars(&[(1.0, Some(-0.5)), (0.0, None)]);
        for (w, h) in [(10, 3), (1, 1), (0, 0), (3, 2)] {
            draw(w, h, |f| {
                sparkline(f, f.area(), &p, &th);
                sparkline(f, f.area(), &[], &th);
                grouped_bars(f, f.area(), &b, Some(0), &th);
                grouped_bars(f, f.area(), &[], None, &th);
                line_chart(f, f.area(), "t", &p, Some(9), &th);
                line_chart(f, f.area(), "", &[], None, &th);
                line_chart(f, f.area(), "", &pts(&[None, None]), Some(0), &th);
                f.render_widget(
                    LineChart::new(&p, &th)
                        .signed(true)
                        .cursor_line(true)
                        .selected(Some(2)),
                    f.area(),
                );
            });
        }
    }
}
