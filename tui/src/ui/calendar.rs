// Calendar: month, week and day views over a list of dated events. Knows
// nothing about what the events are (catalysts, earnings, filings): a screen
// hands it `Event`s and forwards keys to `on_key`.
//
//   m / w / d     month / week / day view
//   W             hide or show Sat + Sun (month and week views; Mon-first)
//   h/l  ←/→      previous / next day (skips hidden weekend days)
//   j/k  ↓/↑      previous / next week (day view: next / previous event)
//   [ ]  PgUp/Dn  previous / next month, week or day
//   t             jump to today

use std::collections::BTreeMap;

use chrono::{Datelike, Duration, NaiveDate, Weekday};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph};

use crate::ui::help::{Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

pub const KEYS: &[Key] = &[
    key("m/w/d", "month / week / day view"),
    key("W", "hide / show weekends"),
    key("h/l", "previous / next day"),
    key("j/k", "previous / next week (day view: event)"),
    key("[ ]", "previous / next month, week or day"),
    key("t", "jump to today"),
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum View {
    Month,
    Week,
    Day,
}

/// How an event is coloured; mapped to the theme at draw time.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tone {
    Plain,
    Accent,
    Up,
    Down,
    Dim,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Event {
    pub date: NaiveDate,
    /// "HH:MM" (sorts lexically); None = all day.
    pub time: Option<String>,
    pub label: String,
    pub detail: Option<String>,
    pub tone: Tone,
    /// Where Enter on this event in the day view should go (a URL), if anywhere.
    pub link: Option<String>,
}

pub struct Calendar {
    view: View,
    cursor: NaiveDate,
    today: NaiveDate,
    weekends: bool,
    by_day: BTreeMap<NaiveDate, Vec<Event>>,
    /// Selected event in the day view.
    sel: usize,
    theme: Theme,
    /// Dim text after the title: which layer or filter is on.
    status: String,
}

/// Events grouped by day, each day ordered by time (all-day first) then label.
fn group(events: Vec<Event>) -> BTreeMap<NaiveDate, Vec<Event>> {
    let mut by_day: BTreeMap<NaiveDate, Vec<Event>> = BTreeMap::new();
    for e in events {
        by_day.entry(e.date).or_default().push(e);
    }
    for day in by_day.values_mut() {
        day.sort_by(|a, b| a.time.cmp(&b.time).then_with(|| a.label.cmp(&b.label)));
    }
    by_day
}

impl Calendar {
    pub fn new(today: NaiveDate, events: Vec<Event>, theme: Theme) -> Self {
        Self {
            view: View::Month,
            cursor: today,
            today,
            weekends: true,
            by_day: group(events),
            sel: 0,
            theme,
            status: String::new(),
        }
    }

    /// Replace the events, keeping the view, cursor and weekend setting. The day-view selection is clamped.
    pub fn set_events(&mut self, events: Vec<Event>) {
        self.by_day = group(events);
        let n = self.events_on(self.cursor).len();
        self.sel = self.sel.min(n.saturating_sub(1));
    }

    /// Short text shown after the title, e.g. which layer or filter is on.
    pub fn set_status(&mut self, status: impl Into<String>) {
        self.status = status.into();
    }

    pub fn with_view(mut self, view: View) -> Self {
        self.view = view;
        self
    }

    pub fn with_cursor(mut self, date: NaiveDate) -> Self {
        self.cursor = self.snap(date, 1);
        self
    }

    pub fn view(&self) -> View {
        self.view
    }

    pub fn set_view(&mut self, view: View) {
        self.view = view;
    }

    pub fn cursor(&self) -> NaiveDate {
        self.cursor
    }

    pub fn weekends(&self) -> bool {
        self.weekends
    }

    pub fn events_on(&self, date: NaiveDate) -> &[Event] {
        self.by_day.get(&date).map_or(&[], Vec::as_slice)
    }

    /// The event under the cursor: the selected one in the day view, else
    /// the first of the cursor day.
    pub fn selected_event(&self) -> Option<&Event> {
        let day = self.events_on(self.cursor);
        match self.view {
            View::Day => day.get(self.sel),
            _ => day.first(),
        }
    }

    /// Returns whether the key was a calendar key.
    pub fn on_key(&mut self, key: KeyEvent) -> bool {
        if key
            .modifiers
            .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
        {
            return false;
        }
        match key.code {
            KeyCode::Char('m') => self.view = View::Month,
            KeyCode::Char('w') => self.view = View::Week,
            KeyCode::Char('d') => self.view = View::Day,
            KeyCode::Char('W') => {
                self.weekends = !self.weekends;
                self.cursor = self.snap(self.cursor, 1);
            }
            KeyCode::Char('t') => self.go(self.today),
            KeyCode::Char('h') | KeyCode::Left => self.go_by_days(-1),
            KeyCode::Char('l') | KeyCode::Right => self.go_by_days(1),
            KeyCode::Char('j') | KeyCode::Down => self.vertical(1),
            KeyCode::Char('k') | KeyCode::Up => self.vertical(-1),
            KeyCode::Char(']') | KeyCode::PageDown => self.go_by_period(1),
            KeyCode::Char('[') | KeyCode::PageUp => self.go_by_period(-1),
            _ => return false,
        }
        true
    }

    fn is_hidden(&self, d: NaiveDate) -> bool {
        !self.weekends && matches!(d.weekday(), Weekday::Sat | Weekday::Sun)
    }

    /// First visible day at or after `d` (before it for dir < 0).
    fn snap(&self, mut d: NaiveDate, dir: i64) -> NaiveDate {
        while self.is_hidden(d) {
            d += Duration::days(dir.signum());
        }
        d
    }

    fn go(&mut self, d: NaiveDate) {
        self.cursor = self.snap(d, 1);
        self.sel = 0;
    }

    fn go_by_days(&mut self, n: i64) {
        let d = self.snap(self.cursor + Duration::days(n), n);
        self.cursor = d;
        self.sel = 0;
    }

    fn vertical(&mut self, dir: i64) {
        if self.view == View::Day {
            let n = self.events_on(self.cursor).len();
            self.sel = match dir {
                1 => (self.sel + 1).min(n.saturating_sub(1)),
                _ => self.sel.saturating_sub(1),
            };
        } else {
            self.go(self.cursor + Duration::days(7 * dir));
        }
    }

    fn go_by_period(&mut self, n: i64) {
        match self.view {
            View::Month => self.go(add_months(self.cursor, n as i32)),
            View::Week => self.go(self.cursor + Duration::days(7 * n)),
            View::Day => self.go_by_days(n),
        }
    }

    /// Visible weekday columns, as offsets from Monday.
    fn cols(&self) -> usize {
        if self.weekends { 7 } else { 5 }
    }

    fn title(&self) -> String {
        let c = self.cursor;
        match self.view {
            View::Month => c.format("%B %Y").to_string(),
            View::Week => {
                let first = week_start(c);
                let last = first + Duration::days(self.cols() as i64 - 1);
                format!("{} – {}", first.format("%b %-d"), last.format("%b %-d, %Y"))
            }
            View::Day => c.format("%A, %B %-d, %Y").to_string(),
        }
    }

    // --- drawing ---------------------------------------------------------

    pub fn draw(&self, frame: &mut Frame, area: Rect) {
        let [head, body] =
            Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(area);
        self.draw_head(frame, head);
        match self.view {
            View::Month => self.draw_month(frame, body),
            View::Week => self.draw_week(frame, body),
            View::Day => self.draw_day(frame, body),
        }
    }

    fn draw_head(&self, frame: &mut Frame, area: Rect) {
        let th = self.theme;
        let mut tabs: Vec<Span> = Vec::new();
        for (v, name) in [
            (View::Month, "Month"),
            (View::Week, "Week"),
            (View::Day, "Day"),
        ] {
            let style = if v == self.view {
                th.accent().add_modifier(Modifier::BOLD)
            } else {
                th.dim()
            };
            tabs.push(Span::styled(format!(" {name} "), style));
        }
        if self.view != View::Day && !self.weekends {
            tabs.push(Span::styled(" · weekends hidden", th.dim()));
        }
        let tabs_w: usize = tabs.iter().map(|s| text::width(&s.content)).sum();
        let [left, right] = Layout::horizontal([
            Constraint::Fill(1),
            Constraint::Length((tabs_w as u16).min(area.width)),
        ])
        .areas(area);
        let mut head = vec![Span::styled(format!(" {}", self.title()), th.title())];
        if !self.status.is_empty() {
            head.push(Span::styled(format!("   {}", self.status), th.dim()));
        }
        frame.render_widget(Paragraph::new(Line::from(head)).style(th.base()), left);
        frame.render_widget(Paragraph::new(Line::from(tabs)).style(th.base()), right);
    }

    fn tone_style(&self, tone: Tone) -> Style {
        let th = self.theme;
        let color = match tone {
            Tone::Plain => th.fg,
            Tone::Accent => th.accent,
            Tone::Up => th.up,
            Tone::Down => th.down,
            Tone::Dim => th.dim,
        };
        Style::new().fg(color)
    }

    fn cell_style(&self, d: NaiveDate) -> Style {
        if d == self.cursor {
            self.theme.selected()
        } else {
            self.theme.base()
        }
    }

    fn day_number_style(&self, d: NaiveDate, in_month: bool) -> Style {
        let th = self.theme;
        if d == self.today {
            Style::new().fg(th.accent).add_modifier(Modifier::BOLD)
        } else if in_month {
            Style::new().fg(th.fg)
        } else {
            Style::new().fg(th.dim)
        }
    }

    fn weekday_header(&self, frame: &mut Frame, area: Rect) {
        let th = self.theme;
        let cols = Layout::horizontal(vec![Constraint::Fill(1); self.cols()]).split(area);
        for (i, rect) in cols.iter().enumerate() {
            let name = weekday_name(i);
            frame.render_widget(
                Paragraph::new(Line::styled(
                    format!(
                        " {}",
                        text::truncate(name, rect.width.saturating_sub(1) as usize)
                    ),
                    th.dim(),
                ))
                .style(th.base()),
                *rect,
            );
        }
    }

    fn draw_month(&self, frame: &mut Frame, area: Rect) {
        let th = self.theme;
        frame.render_widget(Block::new().style(th.base()), area);
        let [names, grid] =
            Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(area);
        self.weekday_header(frame, names);

        let c = self.cursor;
        let first = c.with_day(1).unwrap_or(c);
        let last = first
            .with_day(days_in_month(first.year(), first.month()))
            .unwrap_or(first);
        let start = week_start(first);
        let weeks = ((week_start(last) - start).num_days() / 7 + 1) as usize;

        let rows = Layout::vertical(vec![Constraint::Fill(1); weeks]).split(grid);
        for (r, row) in rows.iter().enumerate() {
            let cells = Layout::horizontal(vec![Constraint::Fill(1); self.cols()]).split(*row);
            for (col, cell) in cells.iter().enumerate() {
                let d = start + Duration::days((r * 7 + col) as i64);
                self.draw_month_cell(frame, *cell, d, d.month() == first.month());
            }
        }
    }

    fn draw_month_cell(&self, frame: &mut Frame, rect: Rect, d: NaiveDate, in_month: bool) {
        let th = self.theme;
        let style = self.cell_style(d);
        let block = Block::new()
            .borders(Borders::TOP | Borders::LEFT)
            .border_style(th.border())
            .style(style);
        let inner = block.inner(rect);
        frame.render_widget(block, rect);
        if inner.is_empty() {
            return;
        }
        let w = inner.width as usize;
        let events = self.events_on(d);
        let mut lines = vec![Line::from(vec![
            Span::styled(format!("{}", d.day()), self.day_number_style(d, in_month)),
            Span::styled(
                if events.is_empty() {
                    String::new()
                } else {
                    format!(" ·{}", events.len())
                },
                Style::new().fg(th.dim),
            ),
        ])];
        let avail = inner.height as usize - 1;
        let shown = if events.len() > avail {
            avail.saturating_sub(1)
        } else {
            events.len()
        };
        for e in &events[..shown] {
            lines.push(Line::styled(
                text::truncate(&e.label, w),
                self.tone_style(if in_month { e.tone } else { Tone::Dim }),
            ));
        }
        if shown < events.len() && avail > 0 {
            lines.push(Line::styled(
                text::truncate(&format!("+{} more", events.len() - shown), w),
                Style::new().fg(th.dim),
            ));
        }
        frame.render_widget(Paragraph::new(lines).style(style), inner);
    }

    fn draw_week(&self, frame: &mut Frame, area: Rect) {
        let th = self.theme;
        frame.render_widget(Block::new().style(th.base()), area);
        let start = week_start(self.cursor);
        let cols = Layout::horizontal(vec![Constraint::Fill(1); self.cols()]).split(area);
        for (i, rect) in cols.iter().enumerate() {
            let d = start + Duration::days(i as i64);
            let style = self.cell_style(d);
            let block = Block::new()
                .borders(Borders::LEFT)
                .border_style(th.border())
                .style(style);
            let inner = block.inner(*rect);
            frame.render_widget(block, *rect);
            if inner.is_empty() {
                continue;
            }
            let w = inner.width as usize;
            let mut lines = vec![Line::from(vec![
                Span::styled(format!("{} ", weekday_name(i)), Style::new().fg(th.dim)),
                Span::styled(
                    format!("{}", d.day()),
                    self.day_number_style(d, true).add_modifier(Modifier::BOLD),
                ),
            ])];
            lines.push(Line::default());
            let room = (inner.height as usize).saturating_sub(lines.len());
            let events = self.events_on(d);
            let mut used = 0;
            let mut shown = 0;
            for e in events {
                let t = e
                    .time
                    .as_deref()
                    .map(|t| format!("{t} "))
                    .unwrap_or_default();
                let wrapped = text::wrap(&format!("{t}{}", e.label), w);
                // keep a line free for "+N more" unless this is the last event that fits
                if used + wrapped.len() > room.saturating_sub(usize::from(shown + 1 < events.len()))
                {
                    break;
                }
                used += wrapped.len();
                shown += 1;
                for l in wrapped {
                    lines.push(Line::styled(l, self.tone_style(e.tone)));
                }
            }
            if shown < events.len() && room > 0 {
                lines.push(Line::styled(
                    text::truncate(&format!("+{} more", events.len() - shown), w),
                    Style::new().fg(th.dim),
                ));
            }
            frame.render_widget(Paragraph::new(lines).style(style), inner);
        }
    }

    fn draw_day(&self, frame: &mut Frame, area: Rect) {
        let th = self.theme;
        frame.render_widget(Block::new().style(th.base()), area);
        let events = self.events_on(self.cursor);
        let detail_h = if events.is_empty() {
            0
        } else {
            4.min(area.height / 3)
        };
        let [list, detail] =
            Layout::vertical([Constraint::Min(0), Constraint::Length(detail_h)]).areas(area);
        if events.is_empty() {
            let msg = if self.cursor == self.today {
                "nothing scheduled today"
            } else {
                "nothing scheduled"
            };
            frame.render_widget(
                Paragraph::new(Line::styled(format!("  {msg}"), th.dim())).style(th.base()),
                list,
            );
            return;
        }
        let w = list.width as usize;
        // keep the selected event on screen when the day has more events than rows
        let rows = (list.height as usize).max(1);
        let top = self.sel.saturating_sub(rows - 1);
        let lines: Vec<Line> = events
            .iter()
            .enumerate()
            .skip(top)
            .take(rows)
            .map(|(i, e)| {
                let time = e.time.as_deref().unwrap_or("all day");
                let row = format!("  {time:<7} {}", e.label);
                let base = if i == self.sel {
                    th.selected()
                } else {
                    th.base()
                };
                Line::styled(
                    format!("{:<w$}", text::truncate(&row, w), w = w),
                    base.patch(self.tone_style(e.tone)),
                )
            })
            .collect();
        frame.render_widget(Paragraph::new(lines).style(th.base()), list);

        if let Some(text) = events.get(self.sel).and_then(|e| e.detail.as_deref()) {
            let block = Block::new()
                .borders(Borders::TOP)
                .border_style(th.border())
                .style(th.base());
            let inner = block.inner(detail);
            frame.render_widget(block, detail);
            let lines: Vec<Line> = text::wrap(text, inner.width.saturating_sub(2) as usize)
                .into_iter()
                .map(|l| Line::styled(format!("  {l}"), th.base()))
                .collect();
            frame.render_widget(Paragraph::new(lines).style(th.base()), inner);
        }
    }
}

fn weekday_name(i: usize) -> &'static str {
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i % 7]
}

/// The Monday on or before `d`.
pub fn week_start(d: NaiveDate) -> NaiveDate {
    d - Duration::days(d.weekday().num_days_from_monday() as i64)
}

pub fn days_in_month(year: i32, month: u32) -> u32 {
    let (ny, nm) = if month == 12 {
        (year + 1, 1)
    } else {
        (year, month + 1)
    };
    let first = NaiveDate::from_ymd_opt(year, month, 1).expect("valid month");
    let next = NaiveDate::from_ymd_opt(ny, nm, 1).expect("valid month");
    (next - first).num_days() as u32
}

/// `d` moved by `n` months, clamping the day (Jan 31 + 1 month = Feb 28/29).
pub fn add_months(d: NaiveDate, n: i32) -> NaiveDate {
    let total = d.year() * 12 + d.month0() as i32 + n;
    let (y, m) = (total.div_euclid(12), total.rem_euclid(12) as u32 + 1);
    NaiveDate::from_ymd_opt(y, m, d.day().min(days_in_month(y, m))).expect("clamped day is valid")
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn date(y: i32, m: u32, d: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(y, m, d).unwrap()
    }

    fn ev(d: NaiveDate, time: Option<&str>, label: &str) -> Event {
        Event {
            date: d,
            time: time.map(Into::into),
            label: label.into(),
            detail: Some(format!("{label} detail")),
            tone: Tone::Accent,
            link: None,
        }
    }

    fn cal() -> Calendar {
        // Tue 2026-10-06
        Calendar::new(
            date(2026, 10, 6),
            vec![
                ev(date(2026, 10, 6), Some("16:05"), "MRVL earnings call"),
                ev(date(2026, 10, 6), None, "MRVL analyst day"),
                ev(date(2026, 10, 10), None, "Saturday thing"),
            ],
            Theme::default(),
        )
    }

    fn press(c: &mut Calendar, ch: char) -> bool {
        c.on_key(KeyEvent {
            code: KeyCode::Char(ch),
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn render(c: &Calendar, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| c.draw(f, f.area())).unwrap();
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
    fn month_math() {
        assert_eq!(add_months(date(2026, 1, 31), 1), date(2026, 2, 28));
        assert_eq!(add_months(date(2028, 1, 31), 1), date(2028, 2, 29));
        assert_eq!(add_months(date(2026, 12, 15), 1), date(2027, 1, 15));
        assert_eq!(add_months(date(2026, 1, 15), -1), date(2025, 12, 15));
        assert_eq!(week_start(date(2026, 10, 11)), date(2026, 10, 5)); // Sun -> Mon
        assert_eq!(week_start(date(2026, 10, 5)), date(2026, 10, 5));
    }

    #[test]
    fn events_sort_all_day_first() {
        let c = cal();
        let day = c.events_on(date(2026, 10, 6));
        assert_eq!(day[0].label, "MRVL analyst day");
        assert_eq!(day[1].time.as_deref(), Some("16:05"));
    }

    #[test]
    fn day_steps_skip_hidden_weekends() {
        let mut c = cal();
        assert!(press(&mut c, 'W'));
        assert!(!c.weekends());
        c.cursor = date(2026, 10, 9); // Fri
        press(&mut c, 'l');
        assert_eq!(c.cursor(), date(2026, 10, 12)); // Mon
        press(&mut c, 'h');
        assert_eq!(c.cursor(), date(2026, 10, 9)); // back to Fri
        // weekends shown: plain +/-1
        press(&mut c, 'W');
        press(&mut c, 'l');
        assert_eq!(c.cursor(), date(2026, 10, 10));
    }

    #[test]
    fn hiding_weekends_moves_cursor_off_a_weekend() {
        let mut c = cal();
        c.cursor = date(2026, 10, 10); // Sat
        press(&mut c, 'W');
        assert_eq!(c.cursor(), date(2026, 10, 12));
        let mut c = cal().with_cursor(date(2026, 10, 11));
        press(&mut c, 'W');
        assert_eq!(c.cursor(), date(2026, 10, 12));
    }

    #[test]
    fn jk_week_and_period_keys() {
        let mut c = cal();
        press(&mut c, 'j');
        assert_eq!(c.cursor(), date(2026, 10, 13));
        press(&mut c, 'k');
        press(&mut c, ']');
        assert_eq!(c.cursor(), date(2026, 11, 6)); // month view: next month
        press(&mut c, 'w');
        press(&mut c, '[');
        assert_eq!(c.cursor(), date(2026, 10, 30)); // week view: -7 days
        press(&mut c, 'd');
        press(&mut c, ']');
        assert_eq!(c.cursor(), date(2026, 10, 31));
        press(&mut c, 't');
        assert_eq!(c.cursor(), date(2026, 10, 6));
        assert!(!press(&mut c, 'z'));
    }

    #[test]
    fn day_view_jk_selects_events() {
        let mut c = cal();
        press(&mut c, 'd');
        assert_eq!(c.selected_event().unwrap().label, "MRVL analyst day");
        press(&mut c, 'j');
        assert_eq!(c.selected_event().unwrap().label, "MRVL earnings call");
        press(&mut c, 'j'); // clamps
        assert_eq!(c.selected_event().unwrap().label, "MRVL earnings call");
        press(&mut c, 'k');
        assert_eq!(c.selected_event().unwrap().label, "MRVL analyst day");
    }

    #[test]
    fn month_renders_grid_with_and_without_weekends() {
        let mut c = cal();
        let out = render(&c, 100, 30);
        assert!(out.contains("October 2026"), "{out}");
        assert!(out.contains("Sat") && out.contains("Sun"), "{out}");
        assert!(out.contains("MRVL analyst"), "{out}");
        assert!(out.contains("Saturday thing"), "{out}");
        press(&mut c, 'W');
        let out = render(&c, 100, 30);
        assert!(!out.contains("Sat") && !out.contains("Sun"), "{out}");
        assert!(!out.contains("Saturday thing"), "{out}");
        assert!(out.contains("weekends hidden"), "{out}");
    }

    #[test]
    fn week_and_day_render() {
        let mut c = cal();
        press(&mut c, 'w');
        let out = render(&c, 100, 20);
        assert!(out.contains("Oct 5 – Oct 11, 2026"), "{out}");
        assert!(out.contains("16:05 MRVL"), "{out}");
        press(&mut c, 'W');
        let out = render(&c, 100, 20);
        assert!(out.contains("Oct 5 – Oct 9, 2026"), "{out}");
        press(&mut c, 'd');
        let out = render(&c, 100, 20);
        assert!(out.contains("Tuesday, October 6, 2026"), "{out}");
        assert!(out.contains("analyst day"), "{out}");
        assert!(out.contains("MRVL analyst day detail"), "{out}");
        press(&mut c, 'l');
        assert!(render(&c, 100, 20).contains("nothing scheduled"));
    }

    #[test]
    fn overflow_shows_more_and_tiny_areas_do_not_panic() {
        let d = date(2026, 10, 6);
        let many: Vec<Event> = (0..12)
            .map(|i| ev(d, Some("09:00"), &format!("event {i}")))
            .collect();
        let mut c = Calendar::new(d, many, Theme::default());
        assert!(render(&c, 100, 30).contains("more"));
        for view in ['m', 'w', 'd'] {
            press(&mut c, view);
            for weekends in [true, false] {
                if c.weekends() != weekends {
                    press(&mut c, 'W');
                }
                for (w, h) in [(0, 0), (1, 1), (10, 3), (40, 8), (200, 60)] {
                    render(&c, w, h);
                }
            }
        }
    }

    #[test]
    fn set_events_keeps_view_cursor_and_clamps_selection() {
        let mut c = cal().with_cursor(date(2026, 10, 6));
        c.set_view(View::Day);
        press(&mut c, 'j');
        assert_eq!(
            c.selected_event().map(|e| e.label.as_str()),
            Some("MRVL earnings call")
        );
        c.set_events(vec![ev(date(2026, 10, 6), None, "only one")]);
        assert_eq!((c.view(), c.cursor()), (View::Day, date(2026, 10, 6)));
        assert_eq!(
            c.selected_event().map(|e| e.label.as_str()),
            Some("only one")
        );
        c.set_events(Vec::new());
        assert!(c.selected_event().is_none());
    }

    #[test]
    fn day_view_scrolls_so_the_selection_stays_visible() {
        let many: Vec<Event> = (0..40)
            .map(|i| {
                ev(
                    date(2026, 10, 6),
                    Some(&format!("10:{i:02}")),
                    &format!("row {i:02}"),
                )
            })
            .collect();
        let mut c =
            Calendar::new(date(2026, 10, 6), many, Theme::default()).with_cursor(date(2026, 10, 6));
        c.set_view(View::Day);
        for _ in 0..30 {
            press(&mut c, 'j');
        }
        let screen = render(&c, 60, 12);
        assert!(
            screen.contains("row 30"),
            "selected row must be on screen:\n{screen}"
        );
        assert!(
            !screen.contains("row 00"),
            "the top rows have scrolled away:\n{screen}"
        );
    }

    #[test]
    fn status_text_shows_next_to_the_title() {
        let mut c = cal();
        c.set_status("tweets on · MU");
        assert!(render(&c, 80, 10).contains("tweets on · MU"));
    }
}
