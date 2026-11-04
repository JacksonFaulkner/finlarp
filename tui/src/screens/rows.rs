// Row search: one structured dataset as a searchable table. The data sources
// screen opens it with Enter on a dataset tile; `fl rows insiders t:NVDA`
// opens it directly. Arg: "<dataset> [query]".
//
// Data: py/derive/row_search.py --serve, one long-lived process (JSON lines,
// see its docstring). The query syntax and every dataset's columns live
// there; rows arrive formatted and this screen lays them out. Typing restarts
// a DEBOUNCE timer and tick() sends the query once it expires; replies with a
// stale id are dropped.
//
// Layout: query line, table, then a detail pane with every field of the
// selected row (the table only shows the useful columns). Enter on a row with
// a SEC filing opens it in the reader (docview).

use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Position, Rect};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};
use serde::{Deserialize, Serialize};
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::app::{Action, Ctx, Route, Screen};
use crate::ui::help::{self, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

const DEBOUNCE: Duration = Duration::from_millis(150);
const FLASH_FOR: Duration = Duration::from_secs(2);
/// Rows per query.
const K: usize = 300;
/// Widest a text column gets before it is truncated.
const TEXT_MAX: usize = 42;
const DETAIL_H: u16 = 7;

const KEYS: &[Key] = &[
    key("type", "query (t:NVDA since:2026 field:value \"phrase\" -word)"),
    key("tab ↓", "input → table"),
    key("/ i", "back to the input"),
    key("j k g G", "move"),
    key("^d ^u", "half page"),
    key("↵", "open the filing in the reader"),
    key("o", "open the filing in the browser"),
    key("y", "copy the filing url"),
    key("esc", "back"),
];

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Column {
    pub name: String,
    #[serde(default)]
    pub kind: String,
}

impl Column {
    fn right(&self) -> bool {
        matches!(self.kind.as_str(), "num" | "int" | "money" | "price")
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Row {
    pub cells: Vec<String>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub detail: Vec<(String, String)>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Reply {
    #[serde(default)]
    pub id: Option<u64>,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub columns: Vec<Column>,
    #[serde(default)]
    pub rows: Vec<Row>,
    #[serde(default)]
    pub more: bool,
    #[serde(default)]
    pub fields: Vec<String>,
    #[serde(default)]
    pub hint: Option<String>,
    #[serde(default)]
    pub ms: Option<u64>,
    #[serde(default)]
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct Request {
    id: u64,
    ds: String,
    q: String,
    k: usize,
}

/// The server process. Dropping it closes the channel, which ends the
/// worker, which kills the child.
struct Client {
    tx: Sender<Request>,
    rx: Receiver<Reply>,
}

impl Client {
    fn spawn() -> Self {
        let (tx, req_rx) = mpsc::channel::<Request>();
        let (reply_tx, rx) = mpsc::channel::<Reply>();
        let plugin = crate::pyrun::plugin_dir();
        let child = Command::new(crate::pyrun::python(&plugin))
            .arg(plugin.join("py/derive/row_search.py"))
            .arg("--serve")
            .current_dir(&plugin)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn();
        match child {
            Ok(mut child) => {
                thread::spawn(move || {
                    let (Some(mut stdin), Some(stdout)) = (child.stdin.take(), child.stdout.take())
                    else {
                        let _ = child.kill();
                        return;
                    };
                    let mut stdout = BufReader::new(stdout);
                    while let Ok(mut req) = req_rx.recv() {
                        // keep only the newest query of a burst
                        loop {
                            match req_rx.try_recv() {
                                Ok(r) => req = r,
                                Err(TryRecvError::Empty) => break,
                                Err(TryRecvError::Disconnected) => return,
                            }
                        }
                        let reply = turn(&mut stdin, &mut stdout, &req);
                        let dead = reply.is_err();
                        let reply = reply.unwrap_or_else(|e| Reply {
                            id: Some(req.id),
                            error: Some(e),
                            ..Reply::default()
                        });
                        if reply_tx.send(reply).is_err() || dead {
                            break;
                        }
                    }
                    let _ = child.kill();
                    let _ = child.wait();
                });
            }
            Err(e) => {
                let _ = reply_tx.send(Reply {
                    error: Some(format!("row_search.py --serve: {e}")),
                    ..Reply::default()
                });
            }
        }
        Self { tx, rx }
    }
}

fn turn(stdin: &mut impl Write, stdout: &mut impl BufRead, req: &Request) -> Result<Reply, String> {
    let line = serde_json::to_string(req).map_err(|e| e.to_string())?;
    writeln!(stdin, "{line}")
        .and_then(|_| stdin.flush())
        .map_err(|e| format!("row_search.py exited: {e}"))?;
    let mut buf = String::new();
    match stdout.read_line(&mut buf) {
        Ok(0) => Err("row_search.py exited".into()),
        Ok(_) => serde_json::from_str(&buf).map_err(|e| format!("bad reply: {e}")),
        Err(e) => Err(format!("row_search.py read: {e}")),
    }
}

#[derive(Clone, Copy, PartialEq)]
enum Focus {
    Input,
    Table,
}

pub struct Rows {
    theme: Theme,
    ds: String,
    client: Option<Client>,
    input: Input,
    focus: Focus,
    next_id: u64,
    sent: Option<u64>,
    edited_at: Option<Instant>,
    loading: bool,
    reply: Reply,
    sel: usize,
    /// First table row on screen.
    top: usize,
    /// Table rows that fit, from the last frame (for ^d/^u and scrolling).
    page: usize,
    flash: Option<(String, Instant)>,
    help: bool,
}

/// "<dataset> [query]" -> (dataset, query).
fn split_arg(arg: Option<String>) -> (String, String) {
    let arg = arg.unwrap_or_default();
    let arg = arg.trim();
    match arg.split_once(char::is_whitespace) {
        Some((ds, q)) => (ds.to_string(), q.trim().to_string()),
        None => (arg.to_string(), String::new()),
    }
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> std::io::Result<Rows> {
    let (ds, q) = split_arg(arg);
    let mut s = Rows::new(ctx.theme, ds, q, Some(Client::spawn()));
    s.send();
    Ok(s)
}

impl Rows {
    fn new(theme: Theme, ds: String, q: String, client: Option<Client>) -> Self {
        Self {
            theme,
            ds,
            client,
            input: Input::new(q),
            focus: Focus::Input,
            next_id: 0,
            sent: None,
            edited_at: None,
            loading: false,
            reply: Reply::default(),
            sel: 0,
            top: 0,
            page: 10,
            flash: None,
            help: false,
        }
    }

    fn send(&mut self) {
        self.edited_at = None;
        self.next_id += 1;
        self.sent = Some(self.next_id);
        self.loading = true;
        if let Some(c) = &self.client {
            let _ = c.tx.send(Request {
                id: self.next_id,
                ds: self.ds.clone(),
                q: self.input.value().to_string(),
                k: K,
            });
        }
    }

    fn accept(&mut self, r: Reply) {
        if r.id.is_some() && r.id != self.sent {
            return;
        }
        self.loading = false;
        if r.error.is_some() {
            // keep the last good table; show the error in the status line
            self.reply.error = r.error;
            return;
        }
        self.reply = r;
        self.sel = 0;
        self.top = 0;
    }

    fn selected(&self) -> Option<&Row> {
        self.reply.rows.get(self.sel)
    }

    fn flash_msg(&mut self, m: &str) -> Action {
        self.flash = Some((m.to_string(), Instant::now()));
        Action::None
    }

    fn url(&mut self) -> Option<String> {
        let u = self.selected().and_then(|r| r.url.clone());
        if u.is_none() {
            self.flash_msg("no filing for this row");
        }
        u
    }

    fn move_by(&mut self, d: isize) {
        let last = self.reply.rows.len().saturating_sub(1) as isize;
        self.sel = (self.sel as isize + d).clamp(0, last.max(0)) as usize;
    }

    /// Column widths that fit `width`: each column as wide as its widest
    /// cell (text capped at TEXT_MAX), then the widest text columns give way.
    fn widths(&self, width: usize) -> Vec<usize> {
        let cols = &self.reply.columns;
        let mut w: Vec<usize> = cols
            .iter()
            .enumerate()
            .map(|(i, c)| {
                let cell = self
                    .reply
                    .rows
                    .iter()
                    .map(|r| r.cells.get(i).map_or(0, |s| text::width(s)))
                    .max()
                    .unwrap_or(0);
                let w = cell.max(text::width(&c.name));
                if c.right() { w } else { w.min(TEXT_MAX) }
            })
            .collect();
        let gaps = cols.len().saturating_sub(1) * 2;
        while w.iter().sum::<usize>() + gaps > width {
            let Some((i, _)) = w
                .iter()
                .enumerate()
                .filter(|&(i, &x)| !cols[i].right() && x > 6)
                .max_by_key(|&(_, &x)| x)
            else {
                break;
            };
            w[i] -= 1;
        }
        w
    }

    fn line(&self, cells: &[String], widths: &[usize]) -> String {
        let mut out = String::new();
        for (i, (w, c)) in widths.iter().zip(&self.reply.columns).enumerate() {
            if i > 0 {
                out.push_str("  ");
            }
            let s = text::truncate(cells.get(i).map_or("", String::as_str), *w);
            let pad = w.saturating_sub(text::width(&s));
            if c.right() {
                out.push_str(&" ".repeat(pad));
                out.push_str(&s);
            } else {
                out.push_str(&s);
                out.push_str(&" ".repeat(pad));
            }
        }
        out
    }

    fn draw_table(&mut self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        if area.height < 2 {
            return;
        }
        let width = area.width.saturating_sub(2) as usize;
        let widths = self.widths(width);
        let names: Vec<String> = self.reply.columns.iter().map(|c| c.name.clone()).collect();
        let mut lines = vec![Line::styled(
            format!(" {}", self.line(&names, &widths)),
            t.dim().add_modifier(Modifier::BOLD),
        )];
        self.page = (area.height - 1) as usize;
        if self.sel < self.top {
            self.top = self.sel;
        } else if self.sel >= self.top + self.page {
            self.top = self.sel + 1 - self.page;
        }
        for (i, r) in self.reply.rows.iter().enumerate().skip(self.top).take(self.page) {
            let s = format!(" {}", self.line(&r.cells, &widths));
            let st = if i == self.sel && self.focus == Focus::Table {
                t.selected()
            } else if i == self.sel {
                t.base().add_modifier(Modifier::BOLD)
            } else {
                t.base()
            };
            let s = format!("{s:<w$}", w = area.width as usize);
            lines.push(Line::styled(s, st));
        }
        if self.reply.rows.is_empty() && !self.loading && self.reply.error.is_none() {
            lines.push(Line::styled(" no rows match", t.dim()));
        }
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn draw_detail(&self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        let Some(r) = self.selected() else { return };
        let fields: Vec<&(String, String)> = r.detail.iter().filter(|(_, v)| !v.is_empty()).collect();
        let per_col = area.height.saturating_sub(1).max(1) as usize;
        let ncols = fields.len().div_ceil(per_col).max(1);
        let col_w = (area.width as usize / ncols).max(20);
        let label_w = fields.iter().map(|(k, _)| text::width(k)).max().unwrap_or(0).min(18);
        let mut lines: Vec<Line> = vec![Line::styled(
            "─".repeat(area.width as usize),
            t.border(),
        )];
        for row in 0..per_col {
            let mut spans = Vec::new();
            for c in 0..ncols {
                if let Some((k, v)) = fields.get(c * per_col + row) {
                    let val_w = col_w.saturating_sub(label_w + 3);
                    let v = text::truncate(v, val_w);
                    spans.push(Span::styled(format!(" {:<label_w$} ", text::truncate(k, label_w)), t.dim()));
                    spans.push(Span::styled(format!("{v:<val_w$} "), t.base()));
                }
            }
            lines.push(Line::from(spans));
        }
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn status(&self) -> Line<'static> {
        let t = self.theme;
        if let Some((m, at)) = &self.flash
            && at.elapsed() < FLASH_FOR
        {
            return Line::styled(format!(" {m}"), t.accent());
        }
        if let Some(e) = &self.reply.error {
            return Line::styled(format!(" {}", e.lines().next().unwrap_or("")), t.down());
        }
        let n = self.reply.rows.len();
        let mut s = if self.loading {
            " searching…".to_string()
        } else {
            format!(
                " {}{n} rows",
                if self.reply.more { "first " } else { "" }
            )
        };
        if let Some(ms) = self.reply.ms {
            s.push_str(&format!(" · {ms}ms"));
        }
        if !self.reply.fields.is_empty() {
            s.push_str(&format!(" · filters t: since: until: {}:", self.reply.fields.join(": ")));
        }
        s.push_str(match self.focus {
            Focus::Input => " · tab table · esc back",
            Focus::Table => " · ↵ read filing · o browser · / query · esc back",
        });
        Line::styled(s, t.dim())
    }
}

impl Screen for Rows {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let detail_h = if area.height > 20 { DETAIL_H } else { 0 };
        let [head, input, hint, table, detail, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(2),
            Constraint::Length(detail_h),
            Constraint::Length(1),
        ])
        .areas(area);
        let title = self.reply.title.clone().unwrap_or_else(|| self.ds.clone());
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" data sources ", t.title()),
                Span::styled(format!(" › {title}"), t.accent()),
            ])),
            head,
        );
        let prompt = " / ";
        let inner_w = input.width.saturating_sub(prompt.len() as u16 + 1) as usize;
        let scroll = self.input.visual_scroll(inner_w);
        let in_style = if self.focus == Focus::Input { t.base() } else { t.dim() };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prompt, t.accent()),
                Span::styled(self.input.value().to_string(), in_style),
            ]))
            .scroll((0, scroll as u16)),
            input,
        );
        if self.focus == Focus::Input {
            let x = (self.input.visual_cursor().max(scroll) - scroll) as u16;
            frame.set_cursor_position(Position::new(input.x + prompt.len() as u16 + x, input.y));
        }
        if let Some(h) = self.reply.hint.as_deref().filter(|h| !h.is_empty()) {
            frame.render_widget(Paragraph::new(Line::styled(format!("   {h}"), t.dim())), hint);
        }
        self.draw_table(frame, table);
        if detail_h > 0 {
            self.draw_detail(frame, detail);
        }
        frame.render_widget(Paragraph::new(self.status()), foot);
        if self.help {
            help::render_overlay(frame, area, "row search", KEYS, &t);
        }
    }

    fn tick(&mut self) -> Action {
        let mut got = Vec::new();
        if let Some(c) = &self.client {
            while let Ok(r) = c.rx.try_recv() {
                got.push(r);
            }
        }
        for r in got {
            self.accept(r);
        }
        if self.edited_at.is_some_and(|at| at.elapsed() >= DEBOUNCE) {
            self.send();
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
    }

    fn leader_ok(&self) -> bool {
        self.focus == Focus::Table
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => return Action::Quit,
            KeyCode::Tab | KeyCode::BackTab => {
                self.focus = match self.focus {
                    Focus::Input => Focus::Table,
                    Focus::Table => Focus::Input,
                };
                return Action::None;
            }
            KeyCode::Char('j' | 'n') if ctrl => {
                self.move_by(1);
                return Action::None;
            }
            KeyCode::Char('k' | 'p') if ctrl => {
                self.move_by(-1);
                return Action::None;
            }
            _ => {}
        }
        match self.focus {
            Focus::Input => match key.code {
                KeyCode::Down => self.focus = Focus::Table,
                KeyCode::Enter => {
                    if self.edited_at.is_some() {
                        self.send();
                    }
                    self.focus = Focus::Table;
                }
                _ => {
                    let before = self.input.value().to_string();
                    self.input.handle_event(&Event::Key(key));
                    if self.input.value() != before {
                        self.edited_at = Some(Instant::now());
                    }
                }
            },
            Focus::Table => {
                let half = (self.page / 2).max(1) as isize;
                match key.code {
                    KeyCode::Char('j') | KeyCode::Down => self.move_by(1),
                    KeyCode::Char('k') | KeyCode::Up => {
                        if self.sel == 0 {
                            self.focus = Focus::Input;
                        }
                        self.move_by(-1);
                    }
                    KeyCode::Char('d') if ctrl => self.move_by(half),
                    KeyCode::Char('u') if ctrl => self.move_by(-half),
                    KeyCode::PageDown => self.move_by(half * 2),
                    KeyCode::PageUp => self.move_by(-half * 2),
                    KeyCode::Char('g') | KeyCode::Home => self.sel = 0,
                    KeyCode::Char('G') | KeyCode::End => {
                        self.sel = self.reply.rows.len().saturating_sub(1);
                    }
                    KeyCode::Char('/' | 'i') => self.focus = Focus::Input,
                    KeyCode::Char('?') => self.help = true,
                    KeyCode::Char('q') => return Action::Quit,
                    KeyCode::Enter => {
                        return match self.url() {
                            Some(u) => Action::Route(Route::Screen {
                                screen: "docview".into(),
                                arg: Some(u),
                            }),
                            None => Action::None,
                        };
                    }
                    KeyCode::Char('o') => {
                        return self.url().map_or(Action::None, Action::OpenBrowser);
                    }
                    KeyCode::Char('y') => return self.url().map_or(Action::None, Action::Copy),
                    _ => {}
                }
            }
        }
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    use super::*;

    fn reply() -> Reply {
        serde_json::from_str(
            r#"{"id": 1, "title": "Insider Forms 3/4/5",
                "columns": [{"name": "filed", "kind": "date"}, {"name": "ticker", "kind": "text"},
                            {"name": "insider", "kind": "text"}, {"name": "value", "kind": "money"}],
                "rows": [
                  {"cells": ["2026-09-23", "NVDA", "Teter Timothy S.", "$3.0M"],
                   "url": "https://www.sec.gov/Archives/edgar/data/1/2/x.xml",
                   "detail": [["owner_name", "Teter Timothy S."], ["code", "S"]]},
                  {"cells": ["2026-09-22", "NVDA", "Huang Jen-Hsun", "$12.1M"], "url": null, "detail": []}
                ],
                "more": true, "fields": ["code", "owner"], "hint": "code:P buys", "ms": 12}"#,
        )
        .expect("fixture")
    }

    fn screen() -> Rows {
        let mut s = Rows::new(Theme::default(), "insiders".into(), String::new(), None);
        s.next_id = 1;
        s.sent = Some(1);
        s.accept(reply());
        s
    }

    fn render(s: &mut Rows) -> String {
        let mut term = Terminal::new(TestBackend::new(110, 30)).expect("terminal");
        term.draw(|f| s.draw(f)).expect("draw");
        term.backend().to_string()
    }

    fn press(s: &mut Rows, code: KeyCode) -> Action {
        s.on_key(KeyEvent::new(code, KeyModifiers::NONE))
    }

    #[test]
    fn arg_splits_into_dataset_and_query() {
        assert_eq!(
            split_arg(Some("insiders t:NVDA code:S".into())),
            ("insiders".into(), "t:NVDA code:S".into())
        );
        assert_eq!(split_arg(Some("13f".into())), ("13f".into(), String::new()));
    }

    #[test]
    fn renders_title_columns_rows_and_detail() {
        let mut s = screen();
        let out = render(&mut s);
        assert!(out.contains("Insider Forms 3/4/5"), "{out}");
        assert!(out.contains("insider"), "{out}");
        assert!(out.contains("Teter Timothy S."), "{out}");
        assert!(out.contains("first 2 rows"), "{out}");
        assert!(out.contains("owner_name"), "detail pane:\n{out}");
    }

    #[test]
    fn money_column_is_right_aligned() {
        let s = screen();
        let w = s.widths(100);
        let line = s.line(&s.reply.rows[0].cells.clone(), &w);
        let line2 = s.line(&s.reply.rows[1].cells.clone(), &w);
        assert!(line.ends_with("  $3.0M"), "{line:?}");
        assert!(line2.ends_with("$12.1M"), "{line2:?}");
        assert_eq!(text::width(&line), text::width(&line2));
    }

    #[test]
    fn enter_opens_the_filing_or_flashes() {
        let mut s = screen();
        press(&mut s, KeyCode::Tab);
        match press(&mut s, KeyCode::Enter) {
            Action::Route(Route::Screen { screen, arg }) => {
                assert_eq!(screen, "docview");
                assert!(arg.unwrap().ends_with("x.xml"));
            }
            _ => panic!("expected docview"),
        }
        press(&mut s, KeyCode::Char('j'));
        assert!(matches!(press(&mut s, KeyCode::Enter), Action::None));
        assert!(render(&mut s).contains("no filing for this row"));
    }

    #[test]
    fn typing_debounces_and_stale_replies_are_dropped() {
        let mut s = screen();
        press(&mut s, KeyCode::Char('t'));
        assert!(s.edited_at.is_some());
        s.edited_at = Some(Instant::now() - DEBOUNCE);
        s.tick();
        assert_eq!(s.sent, Some(2));
        let mut old = reply();
        old.rows.clear();
        s.accept(old); // id 1: stale
        assert_eq!(s.reply.rows.len(), 2);
    }

    #[test]
    fn k_at_the_top_returns_to_the_input() {
        let mut s = screen();
        press(&mut s, KeyCode::Tab);
        press(&mut s, KeyCode::Char('k'));
        assert!(s.focus == Focus::Input);
    }
}
