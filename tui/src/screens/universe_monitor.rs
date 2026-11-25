// The AI universe's two panes around the fake oil buffer (screens::universe): the expanded
// view of the ticker under the cursor (top 75%) and the buffer itself drawn as a quote monitor
// (bottom 25%), where directories are rows too.
//
//   ┌ MU  Micron Technology ─────────────── Memory & Storage · Compute & Semis ┐
//   │ $96.42  ▼-3.1% today  -20.4% 1m  mcap $108B  day 94.10–98.70             │
//   │ <chart: daily closes over the range, or today's 1m>   │ peers in basket │
//   ├ Memory & Storage  -23.0%  14 names ─────────────────────────── ‹ 5/46 › ┤
//   │ TICKER  LAST  CHG%  1M%  DAY RANGE  MCAP  NAME                           │
//
// Quotes are the intraday feed (screens::intraday::stream) in Yahoo-only mode, subscribed to
// the first WATCH_MAX names of the listing on screen. The daily
// closes come from the bars (universe's load_fund_series), cached per ticker.

use std::collections::HashMap;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph};

use crate::model::Point;
use crate::screens::intraday::data::Series;
use crate::screens::intraday::stream::{Event, Stream};
use crate::ui::charts::LineChart;
use crate::ui::pic_chart::{PicChart, bars_from_closes};
use crate::ui::text;
use crate::ui::theme::Theme;

/// The monitor's share of the body, in percent; the expanded view takes the rest.
pub const MONITOR_PCT: u16 = 25;
/// The peers column beside the chart, when the view is wide enough for both.
const PEERS_W: u16 = 30;
const DAY_BAR_W: usize = 10;
/// Most names the feed follows at once: a big listing (regions/us/, 449 names) would otherwise
/// seed hundreds of quotes. Names past it show their daily closes only.
const WATCH_MAX: usize = 50;

/// One basket member as the monitor lists it.
pub struct Row {
    /// The ticker, or for a directory its entry name (`memory_storage/`).
    pub ticker: String,
    pub name: String,
    /// Return over the screen's range.
    pub ret: Option<f64>,
    pub cap: Option<f64>,
    /// A directory: how many names it holds. Directories have no quote columns.
    pub names: Option<usize>,
}

/// The basket on screen.
pub struct Basket<'a> {
    pub label: &'a str,
    /// The primary a sub-sector sits under.
    pub parent: Option<&'a str>,
    pub ret: Option<f64>,
    /// (this basket, of how many) at the level, 1-based.
    pub pos: (usize, usize),
    pub spec: &'a str,
    pub from: NaiveDate,
    pub to: NaiveDate,
}

/// How the monitor orders its rows. `s` cycles; the order is taken when chosen, so rows don't
/// jump under the cursor as quotes tick.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Sort {
    Weight,
    Chg,
    Range,
    Ticker,
}

impl Sort {
    pub fn next(self) -> Self {
        match self {
            Sort::Weight => Sort::Chg,
            Sort::Chg => Sort::Range,
            Sort::Range => Sort::Ticker,
            Sort::Ticker => Sort::Weight,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Sort::Weight => "by weight",
            Sort::Chg => "by today's change",
            Sort::Range => "by range return",
            Sort::Ticker => "by ticker",
        }
    }
}

/// What the expanded view charts. `t` toggles.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Chart {
    /// Daily closes over the screen's range.
    Range,
    /// Today's 1-minute closes from the feed.
    Today,
}

pub struct Monitor {
    stream: Option<Stream>,
    series: HashMap<String, Series>,
    /// Daily closes per ticker, oldest first.
    pub closes: HashMap<String, Vec<(NaiveDate, f64)>>,
    watched: Vec<String>,
    pub sort: Sort,
    pub chart: Chart,
    /// The feed's last status line.
    pub status: String,
    /// The expanded chart as a picture (intraday's candles), when the terminal draws them.
    pub pic: Option<PicChart>,
}

impl Default for Monitor {
    fn default() -> Self {
        Self {
            stream: None,
            series: HashMap::new(),
            closes: HashMap::new(),
            watched: Vec::new(),
            sort: Sort::Weight,
            chart: Chart::Range,
            status: String::new(),
            pic: None,
        }
    }
}

/// `$1.2T`, `$108B`, `$950M`.
pub fn money(v: f64) -> String {
    match v.abs() {
        x if x >= 1e12 => format!("${:.1}T", v / 1e12),
        x if x >= 1e9 => format!("${:.0}B", v / 1e9),
        x if x >= 1e6 => format!("${:.0}M", v / 1e6),
        _ => format!("${v:.0}"),
    }
}

/// `├──●───┤`: where `last` sits between the day's low and high, in `w` cells.
pub fn range_bar(lo: f64, hi: f64, last: f64, w: usize) -> String {
    let inner = w.saturating_sub(2).max(1);
    let k = if hi > lo {
        ((last - lo) / (hi - lo)).clamp(0.0, 1.0)
    } else {
        0.5
    };
    let at = ((k * (inner - 1) as f64).round() as usize).min(inner - 1);
    let mid: String = (0..inner)
        .map(|i| if i == at { '●' } else { '─' })
        .collect();
    format!("├{mid}┤")
}

/// A price in its own currency (no symbol: Seoul and Tokyo listings quote in won and yen),
/// cents only where they matter.
pub fn price(v: f64) -> String {
    if v.abs() >= 10_000.0 {
        format!("{v:.0}")
    } else {
        format!("{v:.2}")
    }
}

fn pct(v: Option<f64>) -> String {
    v.map_or("—".into(), |v| format!("{v:+.1}%"))
}

impl Monitor {
    /// Subscribes the feed to `tickers` (the listing on screen, its first WATCH_MAX), starting
    /// it on first use. The feed is Yahoo-only: the monitor never pays for Databento minutes.
    pub fn watch(&mut self, tickers: &[String]) {
        let tickers = &tickers[..tickers.len().min(WATCH_MAX)];
        if self.watched == tickers {
            return;
        }
        self.watched = tickers.to_vec();
        if cfg!(test) {
            return;
        }
        let stream = self.stream.get_or_insert_with(Stream::spawn_yahoo_only);
        stream.set_symbols(tickers);
    }

    /// Takes in whatever the feed sent. True when anything changed.
    pub fn poll(&mut self) -> bool {
        let Some(stream) = &self.stream else {
            return false;
        };
        let mut changed = false;
        while let Ok(ev) = stream.rx.try_recv() {
            changed = true;
            match ev {
                Event::Seed {
                    sym,
                    prev_close,
                    reg,
                    bars,
                } => self
                    .series
                    .entry(sym)
                    .or_default()
                    .seed(prev_close, reg, &bars),
                Event::Bar { sym, bar } => self.series.entry(sym).or_default().apply(bar),
                Event::Status { msg, .. } => self.status = msg,
                Event::Error { sym, msg } => self.status = format!("{sym}: {msg}"),
            }
        }
        changed
    }

    /// The latest price: the feed's, else the last daily close.
    pub fn last(&self, t: &str) -> Option<f64> {
        self.series
            .get(t)
            .and_then(Series::last_close)
            .or_else(|| self.closes.get(t).and_then(|c| c.last()).map(|(_, c)| *c))
    }

    /// Today's change against the previous close, in percent.
    pub fn chg(&self, t: &str) -> Option<f64> {
        let s = self.series.get(t)?;
        let (last, prev) = (s.last_close()?, s.prev_close?);
        (prev > 0.0).then(|| (last / prev - 1.0) * 100.0)
    }

    fn day_range(&self, t: &str) -> Option<(f64, f64)> {
        self.series.get(t).and_then(Series::day_range)
    }

    /// The ticker under the cursor: price line, chart, and its peers among `rows`.
    pub fn draw_expanded(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        row: &Row,
        rows: &[Row],
        basket: &Basket,
        t: &Theme,
    ) {
        let place = match basket.parent {
            Some(p) => format!(" {} · {p} ", basket.label),
            None => format!(" {} ", basket.label),
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.border())
            .title(Line::from(vec![
                Span::styled(format!(" {} ", row.ticker), t.title()),
                Span::styled(format!("{} ", row.name), t.base()),
            ]))
            .title(Line::styled(place, t.dim()).right_aligned());
        let inner = block.inner(area);
        frame.render_widget(block, area);
        if inner.height < 3 {
            return;
        }
        let [stats, _, body] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
        ])
        .areas(inner);

        let mut spans = vec![Span::styled(
            self.last(&row.ticker)
                .map_or(" —  ".into(), |v| format!(" {}  ", price(v))),
            t.title(),
        )];
        if let Some(c) = self.chg(&row.ticker) {
            let arrow = if c >= 0.0 { '▲' } else { '▼' };
            spans.push(Span::styled(
                format!("{arrow}{c:+.1}% today  "),
                t.signed(c),
            ));
        }
        if let Some(r) = row.ret {
            spans.push(Span::styled(
                format!("{r:+.1}% {}  ", basket.spec),
                t.signed(r),
            ));
        }
        if let Some(c) = row.cap {
            spans.push(Span::styled(format!("mcap {}  ", money(c)), t.dim()));
        }
        if let Some((lo, hi)) = self.day_range(&row.ticker) {
            spans.push(Span::styled(
                format!("day {}–{}", price(lo), price(hi)),
                t.dim(),
            ));
        }
        frame.render_widget(Paragraph::new(Line::from(spans)), stats);

        let (chart, peers) = if body.width >= PEERS_W * 3 {
            let [c, _, p] = Layout::horizontal([
                Constraint::Min(1),
                Constraint::Length(1),
                Constraint::Length(PEERS_W),
            ])
            .areas(body);
            (c, Some(p))
        } else {
            (body, None)
        };
        self.draw_chart(frame, chart, &row.ticker, basket, t);
        if let Some(p) = peers {
            draw_peers(frame, p, rows, &row.ticker, basket, t);
        }
    }

    fn draw_chart(&mut self, frame: &mut Frame, area: Rect, ticker: &str, basket: &Basket, t: &Theme) {
        if self.draw_picture(frame, area, ticker, basket, t) {
            return;
        }
        let (points, title): (Vec<Point>, String) = match self.chart {
            Chart::Range => {
                let pts = self
                    .closes
                    .get(ticker)
                    .map(|c| {
                        c.iter()
                            .filter(|(d, _)| *d >= basket.from && *d <= basket.to)
                            .map(|(d, c)| Point {
                                x: d.format("%m/%d").to_string(),
                                y: Some(*c),
                                src: None,
                            })
                            .collect()
                    })
                    .unwrap_or_default();
                (pts, format!("daily · {} → {}", basket.from, basket.to))
            }
            Chart::Today => {
                let pts = self
                    .series
                    .get(ticker)
                    .map(|s| {
                        s.closes()
                            .into_iter()
                            .map(|(tm, c)| Point {
                                x: s.label(tm),
                                y: Some(c),
                                src: None,
                            })
                            .collect()
                    })
                    .unwrap_or_default();
                (pts, "today · 1m".into())
            }
        };
        if points.len() < 2 {
            let msg = match self.chart {
                Chart::Range => format!("no daily closes for {ticker} in the range"),
                Chart::Today if self.status.is_empty() => format!("waiting for {ticker}'s feed"),
                Chart::Today => format!("no bars yet: {}", self.status),
            };
            frame.render_widget(Paragraph::new(Span::styled(msg, t.dim())), area);
            return;
        }
        frame.render_widget(LineChart::new(&points, t).title(&title), area);
    }

    /// The chart as a picture, the way the intraday tiles draw: daily candles over the
    /// range, or today's 1m bars with VWAP and the previous close. False: no picture here.
    fn draw_picture(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        ticker: &str,
        basket: &Basket,
        t: &Theme,
    ) -> bool {
        if self.pic.as_ref().is_none_or(|p| !p.available()) || area.height < 4 {
            return false;
        }
        let (bars, vwap, prev, title) = match self.chart {
            Chart::Range => {
                let closes: Vec<(String, f64)> = self
                    .closes
                    .get(ticker)
                    .into_iter()
                    .flatten()
                    .filter(|(d, _)| *d >= basket.from && *d <= basket.to)
                    .map(|(d, c)| (d.format("%m/%d").to_string(), *c))
                    .collect();
                (
                    bars_from_closes(&closes),
                    None,
                    None,
                    format!("daily · {} → {}", basket.from, basket.to),
                )
            }
            Chart::Today => match self.series.get(ticker) {
                Some(s) => (
                    s.aggregate(1, false).as_ref().clone(),
                    s.vwap(),
                    s.prev_close,
                    "today · 1m · vwap".to_string(),
                ),
                None => return false,
            },
        };
        if bars.len() < 2 {
            return false;
        }
        let [head, body] =
            Layout::vertical([Constraint::Length(1), Constraint::Min(1)]).areas(area);
        let pic = self.pic.as_mut().expect("checked above");
        if !pic.draw(frame, body, &bars, vwap, prev) {
            return false;
        }
        frame.render_widget(Paragraph::new(Span::styled(title, t.dim())), head);
        true
    }

    /// The buffer as a quote monitor; `basket` is the directory it lists.
    pub fn draw_table(
        &self,
        frame: &mut Frame,
        area: Rect,
        rows: &[Row],
        sel: usize,
        basket: &Basket,
        t: &Theme,
    ) {
        let mut head = vec![Span::styled(format!(" {} ", basket.label), t.title())];
        if let Some(r) = basket.ret {
            head.push(Span::styled(format!("{r:+.1}%  "), t.signed(r)));
        }
        head.push(Span::styled(
            format!(
                "{} {} · {} ",
                rows.len(),
                if rows.iter().any(|r| r.names.is_some()) {
                    "entries"
                } else {
                    "names"
                },
                self.sort.label()
            ),
            t.dim(),
        ));
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.border())
            .title(Line::from(head))
            .title(
                Line::styled(
                    if basket.pos.1 > 0 {
                        format!(" ‹ {}/{} › ", basket.pos.0, basket.pos.1)
                    } else {
                        String::new()
                    },
                    t.dim(),
                )
                .right_aligned(),
            );
        let inner = block.inner(area);
        frame.render_widget(block, area);
        if inner.height == 0 {
            return;
        }
        let spec = format!("{}%", basket.spec.to_uppercase());
        // the first column fits the longest entry (directory names run long), within reason
        let first = rows
            .iter()
            .map(|r| text::width(&r.ticker))
            .max()
            .unwrap_or(0)
            .clamp(10, 30)
            + 1;
        let header = format!(
            "  {:<first$}{:>10}{:>8}{:>9}  {:<w$}{:>8}  NAME",
            "TICKER",
            "LAST",
            "CHG%",
            spec,
            "DAY RANGE",
            "MCAP",
            w = DAY_BAR_W
        );
        let mut lines = vec![Line::styled(header, t.dim())];
        let room = usize::from(inner.height).saturating_sub(1).max(1);
        let top = sel.saturating_sub(room - 1);
        for (i, r) in rows.iter().enumerate().skip(top).take(room) {
            let row_style = if i == sel { t.selected() } else { t.base() };
            if let Some(n) = r.names {
                let ret_style = r.ret.map_or(t.dim(), |v| t.signed(v));
                let ret_style = if i == sel {
                    t.on_cursor(ret_style)
                } else {
                    ret_style
                };
                let used = 2 + first + 10 + 8 + 9;
                let name_w = usize::from(inner.width).saturating_sub(used + 2);
                lines.push(Line::from(vec![
                    Span::styled(if i == sel { "▌ " } else { "  " }, row_style),
                    Span::styled(
                        format!("{:<first$}", text::truncate(&r.ticker, first - 1)),
                        row_style.add_modifier(ratatui::style::Modifier::BOLD),
                    ),
                    Span::styled(format!("{:>18}", ""), row_style),
                    Span::styled(format!("{:>9}", pct(r.ret)), ret_style),
                    Span::styled(
                        format!(
                            "  {}",
                            text::truncate(
                                &format!("{} · {n} name{}", r.name, if n == 1 { "" } else { "s" }),
                                name_w
                            )
                        ),
                        row_style,
                    ),
                ]));
                continue;
            }
            let last = self.last(&r.ticker);
            let chg = self.chg(&r.ticker);
            let bar = match (self.day_range(&r.ticker), last) {
                (Some((lo, hi)), Some(l)) => range_bar(lo, hi, l, DAY_BAR_W),
                _ => " ".repeat(DAY_BAR_W),
            };
            let num = |v: Option<f64>| -> Style {
                let s = v.map_or(t.dim(), |v| t.signed(v));
                if i == sel { t.on_cursor(s) } else { s }
            };
            let used = 2 + first + 10 + 8 + 9 + 2 + DAY_BAR_W + 8 + 2;
            let name_w = usize::from(inner.width).saturating_sub(used);
            lines.push(Line::from(vec![
                Span::styled(if i == sel { "▌ " } else { "  " }, row_style),
                Span::styled(format!("{:<first$}", r.ticker), row_style),
                Span::styled(format!("{:>10}", last.map_or("—".into(), price)), row_style),
                Span::styled(format!("{:>8}", pct(chg)), num(chg)),
                Span::styled(format!("{:>9}", pct(r.ret)), num(r.ret)),
                Span::styled(format!("  {bar}"), row_style),
                Span::styled(format!("{:>8}", r.cap.map_or("—".into(), money)), row_style),
                Span::styled(format!("  {}", text::truncate(&r.name, name_w)), row_style),
            ]));
        }
        frame.render_widget(Paragraph::new(lines), inner);
    }
}

/// The basket's members by range return, each with a bar scaled to the widest move; the
/// ticker on screen is marked.
fn draw_peers(frame: &mut Frame, area: Rect, rows: &[Row], on: &str, basket: &Basket, t: &Theme) {
    let block = Block::new()
        .borders(Borders::LEFT)
        .border_style(t.border())
        .title(Span::styled(format!(" peers · {} ", basket.spec), t.dim()));
    let inner = block.inner(area);
    frame.render_widget(block, area);
    let mut ranked: Vec<&Row> = rows.iter().filter(|r| r.names.is_none()).collect();
    ranked.sort_by(|a, b| {
        b.ret
            .unwrap_or(f64::NEG_INFINITY)
            .total_cmp(&a.ret.unwrap_or(f64::NEG_INFINITY))
    });
    let max = ranked
        .iter()
        .filter_map(|r| r.ret)
        .map(f64::abs)
        .fold(0.0, f64::max)
        .max(0.1);
    let bar_w = usize::from(inner.width).saturating_sub(18).max(1);
    // Keep the marked ticker in view when the list is longer than the box.
    let room = usize::from(inner.height);
    let at = ranked.iter().position(|r| r.ticker == on).unwrap_or(0);
    let skip = at
        .saturating_sub(room.saturating_sub(1) / 2)
        .min(ranked.len().saturating_sub(room));
    let lines: Vec<Line> = ranked
        .iter()
        .skip(skip)
        .take(room)
        .map(|r| {
            let mark = r.ticker == on;
            let st = if mark { t.title() } else { t.base() };
            let n = r
                .ret
                .map_or(0, |v| ((v.abs() / max) * bar_w as f64).round() as usize);
            Line::from(vec![
                Span::styled(if mark { "▌" } else { " " }, st),
                Span::styled(format!("{:<9}", text::truncate(&r.ticker, 9)), st),
                Span::styled(
                    format!("{:>7} ", pct(r.ret)),
                    r.ret.map_or(t.dim(), |v| t.signed(v)),
                ),
                Span::styled("█".repeat(n), r.ret.map_or(t.dim(), |v| t.signed(v))),
            ])
        })
        .collect();
    frame.render_widget(Paragraph::new(lines), inner);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn money_reads_like_a_quote_screen() {
        assert_eq!(money(1.23e12), "$1.2T");
        assert_eq!(money(108.4e9), "$108B");
        assert_eq!(money(950e6), "$950M");
    }

    #[test]
    fn prices_drop_cents_when_they_are_noise() {
        assert_eq!(price(96.421), "96.42");
        assert_eq!(price(173_500.0), "173500");
    }

    #[test]
    fn range_bar_puts_the_last_price_between_low_and_high() {
        assert_eq!(range_bar(10.0, 20.0, 10.0, 8), "├●─────┤");
        assert_eq!(range_bar(10.0, 20.0, 20.0, 8), "├─────●┤");
        assert_eq!(range_bar(10.0, 10.0, 10.0, 8).chars().count(), 8);
    }

    #[test]
    fn sort_cycles_through_every_order() {
        let mut s = Sort::Weight;
        for _ in 0..4 {
            s = s.next();
        }
        assert_eq!(s, Sort::Weight);
    }
}
