// Godel-key screen (leader-vm when a result is unseen): every question asked with a leading ">" in the note box, and
// the ten Godel commands the model ranked for it. py/derive/godel_key.py writes <data>/godel/items.json (a row appears
// as "cooking" and flips to "done"/"error"); this screen polls that file, marks rows seen and deletes them. The items
// stay serde_json::Value so fields only Python knows about survive a rewrite.

use std::fs;
use std::io;
use std::path::PathBuf;
use std::time::{Instant, SystemTime};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap};
use serde_json::Value;

use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{self, Key, key};
use crate::ui::theme::Theme;

const RELOAD_EVERY_MS: u128 = 800;

const KEYS: &[Key] = &[
    key("j/k", "move"),
    key("tab", "questions / commands / result"),
    key("enter", "run command: result opens below"),
    key("esc", "back one pane (result > commands)"),
    key("y", "copy command, or result row when in result"),
    key("Y", "copy all ten"),
    key("d", "delete question"),
    key("?", "help"),
    key("q", "close"),
];

#[derive(Clone, Copy, PartialEq)]
enum Focus {
    Questions,
    Commands,
    Result,
}

/// One line of a command's structured answer. `series` (oldest first) drives the trend sparkline.
struct Row {
    label: &'static str,
    value: String,
    series: Vec<f64>,
    src: String,
}

/// The structured answer shown under the command list. FAKE until the commands are wired to real data.
struct ResultView {
    key: String,
    cmd: String,
    tickers: Vec<String>,
    rows: Vec<Row>,
    sel: usize,
}

const SPARK: [char; 8] = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

fn spark(vals: &[f64]) -> String {
    let lo = vals.iter().cloned().fold(f64::MAX, f64::min);
    let hi = vals.iter().cloned().fold(f64::MIN, f64::max);
    vals.iter()
        .map(|v| {
            let i = if hi > lo { ((v - lo) / (hi - lo) * 7.0).round() as usize } else { 3 };
            SPARK[i.min(7)]
        })
        .collect()
}

fn seed_of(s: &str) -> u64 {
    s.bytes()
        .fold(1469598103934665603u64, |h, b| (h ^ b as u64).wrapping_mul(1099511628211))
}

/// Deterministic random-walk of `n` points starting near `base`.
fn walk(seed: u64, base: f64, n: usize) -> Vec<f64> {
    let mut x = base;
    (0..n)
        .map(|i| {
            let step = ((seed >> ((i * 5) % 56)) % 13) as f64 - 4.0; // -4..8 percent
            x *= 1.0 + step / 100.0;
            x
        })
        .collect()
}

fn fake_rows(cmd: &str, key: &str) -> Vec<Row> {
    let seed = seed_of(key);
    let money = |label, base: f64, src: &str, salt: u64| {
        let series = walk(seed ^ salt, base, 8);
        Row {
            label,
            value: format!("${:.1}B", series[7]),
            series,
            src: src.into(),
        }
    };
    let pct = |label, base: f64, src: &str, salt: u64| {
        let series = walk(seed ^ salt, base, 8);
        Row {
            label,
            value: format!("{:.1}%", series[7]),
            series,
            src: src.into(),
        }
    };
    let text = |label, value: &str, src: &str| Row {
        label,
        value: value.into(),
        series: Vec::new(),
        src: src.into(),
    };
    match cmd {
        "FA" => vec![
            money("Revenue", 80.0, "XBRL us-gaap:Revenues (10-K/10-Q)", 1),
            pct("Gross margin", 44.0, "GrossProfit / Revenues", 2),
            money("Operating income", 24.0, "XBRL us-gaap:OperatingIncomeLoss", 3),
            money("Net income", 20.0, "XBRL us-gaap:NetIncomeLoss", 4),
            money("Free cash flow", 22.0, "OCF - capex, cash-flow statement", 5),
        ],
        "GR" => vec![
            pct("Net margin", 24.0, "NetIncomeLoss / Revenues", 1),
            pct("ROIC", 40.0, "NOPAT / (debt + equity - cash)", 2),
            pct("Operating margin", 29.0, "OperatingIncomeLoss / Revenues", 3),
        ],
        "HP" => vec![
            money("Close", 150.0, "bars_1d close", 1),
            pct("Return vs 8 periods ago", 12.0, "bars_1d", 2),
        ],
        "N" => vec![
            text("Headlines (7d)", "3", "news() ROIC snippets"),
            pct("Bullish tweet share", 58.0, "tweet_sentiment stance", 1),
        ],
        "HDS" => vec![
            text("Top 13F holder", "Vanguard (fake)", "13F data sets"),
            pct("Institutional ownership", 62.0, "13F sum / shares outstanding", 1),
            text("Insider net (90d)", "-3 sells, 0 buys", "Form 4"),
        ],
        "EVT" => vec![
            text("Latest 8-K", "item 2.02 earnings (fake)", "EDGAR submissions"),
            text("Next earnings", "2026-10-29 (fake)", "events calendar"),
        ],
        "CF" => vec![
            text("Latest 10-K", "filed 2025-11-03 (fake)", "EDGAR filing index"),
            text("New risk sentences", "4", "YoY-new risk diff"),
        ],
        "DES" => vec![
            text("Sector", "AI universe sub-sector (fake)", "universe table"),
            text("Business", "from 10-K item 1", "10-K business section"),
        ],
        "HMS" => vec![pct("Spread vs peer (rebased)", 8.0, "bars_1d rebased to 100", 1)],
        _ => vec![text("Matches", "17 in universe (fake)", "sql over universe + XBRL")],
    }
}

pub struct GodelScreen {
    theme: Theme,
    path: PathBuf,
    items: Vec<Value>,
    mtime: Option<SystemTime>,
    checked: Instant,
    item: usize,
    cmd: usize,
    focus: Focus,
    result: Option<ResultView>,
    flash: Option<String>,
    help: bool,
}

/// <data dir>/finlarp/godel/items.json, next to the duckdb file (py/sources/universe.py DATA_ROOT).
fn items_path(ctx: &Ctx) -> PathBuf {
    ctx.db_path
        .parent()
        .map(PathBuf::from)
        .unwrap_or_default()
        .join("finlarp/godel/items.json")
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<GodelScreen> {
    let mut s = GodelScreen {
        theme: ctx.theme,
        path: items_path(ctx),
        items: Vec::new(),
        mtime: None,
        checked: Instant::now(),
        item: 0,
        cmd: 0,
        focus: Focus::Questions,
        result: None,
        flash: None,
        help: false,
    };
    s.reload();
    s.mark_seen();
    Ok(s)
}

fn str_of<'a>(v: &'a Value, k: &str) -> &'a str {
    v.get(k).and_then(Value::as_str).unwrap_or("")
}

fn commands(item: &Value) -> &[Value] {
    item.get("commands")
        .and_then(Value::as_array)
        .map_or(&[], Vec::as_slice)
}

/// Rewrites the file atomically with `f` applied to what is on disk now (not to our possibly stale copy), so a
/// Python job finishing at the same moment keeps its result.
fn update_file(path: &PathBuf, f: impl FnOnce(&mut Vec<Value>)) {
    let mut items: Vec<Value> = fs::read_to_string(path)
        .ok()
        .and_then(|t| serde_json::from_str(&t).ok())
        .unwrap_or_default();
    f(&mut items);
    let tmp = path.with_extension("tmp");
    if fs::write(&tmp, Value::Array(items).to_string()).is_ok() {
        let _ = fs::rename(tmp, path);
    }
}

impl GodelScreen {
    fn current(&self) -> Option<&Value> {
        self.items.get(self.item)
    }

    /// Re-reads the file; keeps the cursor on the same question when it is still there.
    fn reload(&mut self) {
        self.checked = Instant::now();
        let mtime = fs::metadata(&self.path).and_then(|m| m.modified()).ok();
        if mtime == self.mtime && !self.items.is_empty() {
            return;
        }
        self.mtime = mtime;
        let keep = self.current().map(|i| str_of(i, "id").to_string());
        self.items = fs::read_to_string(&self.path)
            .ok()
            .and_then(|t| serde_json::from_str(&t).ok())
            .unwrap_or_default();
        if let Some(id) = keep {
            self.item = self
                .items
                .iter()
                .position(|i| str_of(i, "id") == id)
                .unwrap_or(0);
        }
        self.item = self.item.min(self.items.len().saturating_sub(1));
        self.cmd = self.cmd.min(commands_len(self.current()).saturating_sub(1));
    }

    /// A finished question counts as seen once it is on screen (drives leader-vm's choice of viewer).
    fn mark_seen(&mut self) {
        let Some(item) = self.items.get_mut(self.item) else {
            return;
        };
        if str_of(item, "status") != "done"
            || item.get("seen").and_then(Value::as_bool) == Some(true)
        {
            return;
        }
        item["seen"] = Value::Bool(true);
        let id = str_of(item, "id").to_string();
        update_file(&self.path, |items| {
            if let Some(it) = items.iter_mut().find(|i| str_of(i, "id") == id) {
                it["seen"] = Value::Bool(true);
            }
        });
        self.mtime = fs::metadata(&self.path).and_then(|m| m.modified()).ok();
    }

    fn delete_current(&mut self) {
        let Some(id) = self.current().map(|i| str_of(i, "id").to_string()) else {
            return;
        };
        update_file(&self.path, |items| items.retain(|i| str_of(i, "id") != id));
        self.mtime = None; // force the re-read
        self.reload();
        self.cmd = 0;
        self.result = None;
        self.mark_seen();
    }

    fn step(&mut self, delta: isize) {
        match self.focus {
            Focus::Questions => {
                let last = self.items.len().saturating_sub(1);
                self.item = self.item.saturating_add_signed(delta).min(last);
                self.cmd = 0;
                self.result = None;
                self.mark_seen();
            }
            Focus::Commands => {
                let last = commands_len(self.current()).saturating_sub(1);
                self.cmd = self.cmd.saturating_add_signed(delta).min(last);
            }
            Focus::Result => {
                if let Some(r) = self.result.as_mut() {
                    let last = r.rows.len().saturating_sub(1);
                    r.sel = r.sel.saturating_add_signed(delta).min(last);
                }
            }
        }
    }

    /// Enter on a command: build its (fake) structured answer and move the cursor into it.
    fn open_result(&mut self) {
        let Some(c) = self.current().and_then(|i| commands(i).get(self.cmd)).cloned() else {
            return;
        };
        let key = str_of(&c, "key").to_string();
        let cmd = str_of(&c, "cmd").to_string();
        let tickers = c
            .get("tickers")
            .and_then(Value::as_array)
            .map(|a| a.iter().filter_map(|t| t.as_str().map(String::from)).collect())
            .unwrap_or_default();
        self.result = Some(ResultView {
            rows: fake_rows(&cmd, &key),
            key,
            cmd,
            tickers,
            sel: 0,
        });
        self.focus = Focus::Result;
    }

    /// Other questions that touched the same tickers, and how many ranked this exact key: the "have I been here" signal.
    fn seen_before(&self, r: &ResultView) -> (Vec<String>, usize) {
        let mut asked = Vec::new();
        let mut same_key = 0;
        for (i, it) in self.items.iter().enumerate() {
            let cs = commands(it);
            same_key += cs.iter().filter(|c| str_of(c, "key") == r.key).count();
            if i == self.item {
                continue;
            }
            let shares = cs.iter().any(|c| {
                c.get("tickers")
                    .and_then(Value::as_array)
                    .is_some_and(|ts| ts.iter().any(|t| t.as_str().is_some_and(|t| r.tickers.iter().any(|x| x == t))))
            });
            if shares {
                let when = match it.get("date").and_then(Value::as_str) {
                    Some(d) => format!("{d} {}", str_of(it, "ts")),
                    None => str_of(it, "ts").to_string(),
                };
                asked.push(format!("{}  ({when})", str_of(it, "query")));
            }
        }
        (asked, same_key)
    }

    fn draw_result(&self, frame: &mut Frame, area: ratatui::layout::Rect, r: &ResultView) {
        let t = self.theme;
        let focused = self.focus == Focus::Result;
        let [left, right] =
            Layout::horizontal([Constraint::Percentage(55), Constraint::Percentage(45)]).areas(area);
        let [table, detail] = Layout::vertical([Constraint::Min(3), Constraint::Length(3)])
            .areas(left);

        let rows: Vec<ListItem> = r
            .rows
            .iter()
            .map(|row| {
                let (delta, style) = match (row.series.first(), row.series.last()) {
                    (Some(a), Some(b)) if row.series.len() > 1 && *a != 0.0 => {
                        let d = (b / row.series[row.series.len() - 2] - 1.0) * 100.0;
                        (format!("{d:+.1}% vs prev"), if d >= 0.0 { t.up() } else { t.down() })
                    }
                    _ => (String::new(), t.dim()),
                };
                ListItem::new(Line::from(vec![
                    Span::styled(format!("{:<26}", row.label), t.base()),
                    Span::styled(format!("{:>16}  ", row.value), t.accent()),
                    Span::styled(delta, style),
                ]))
            })
            .collect();
        let mut st = ListState::default().with_selected(Some(r.sel));
        frame.render_stateful_widget(
            List::new(rows)
                .block(self.pane(format!(" result · {} · fake data ", r.key), focused))
                .highlight_style(if focused { t.selected() } else { t.base().fg(t.accent) }),
            table,
            &mut st,
        );
        let sel = r.rows.get(r.sel);
        frame.render_widget(
            Paragraph::new(format!("source: {}", sel.map_or("", |x| x.src.as_str())))
                .style(t.dim())
                .wrap(Wrap { trim: true })
                .block(self.pane(" where it came from ".into(), false)),
            detail,
        );

        // right: trend of the selected row, then history
        let mut lines: Vec<Line> = Vec::new();
        match sel {
            Some(row) if !row.series.is_empty() => {
                let (first, last) = (row.series[0], row.series[row.series.len() - 1]);
                lines.push(Line::from(Span::styled(format!("TREND  {}  (last 8 periods)", row.label), t.title())));
                lines.push(Line::from(Span::styled(spark(&row.series), t.accent())));
                let d = (last / first - 1.0) * 100.0;
                lines.push(Line::from(vec![
                    Span::styled(format!("{first:.1} → {last:.1}  "), t.dim()),
                    Span::styled(format!("{d:+.1}%"), if d >= 0.0 { t.up() } else { t.down() }),
                ]));
            }
            _ => lines.push(Line::from(Span::styled("TREND  none for this row", t.dim()))),
        }
        let (asked, same_key) = self.seen_before(r);
        lines.push(Line::raw(""));
        lines.push(Line::from(Span::styled("SEEN BEFORE", t.title())));
        lines.push(Line::from(Span::styled(
            format!("{} ranked in {same_key} question(s)", r.key),
            t.dim(),
        )));
        if asked.is_empty() {
            lines.push(Line::from(Span::styled("no earlier question on these tickers", t.dim())));
        }
        for q in asked.iter().take(5) {
            lines.push(Line::from(vec![Span::styled("• ", t.accent()), Span::raw(q.clone())]));
        }
        frame.render_widget(
            Paragraph::new(lines)
                .wrap(Wrap { trim: true })
                .block(self.pane(format!(" {} · history ", r.cmd), false)),
            right,
        );
    }

    fn jump(&mut self, end: bool) {
        self.step(if end { isize::MAX / 2 } else { isize::MIN / 2 });
    }

    fn copy_current(&self) -> Option<String> {
        if self.focus == Focus::Result {
            let r = self.result.as_ref()?;
            let row = r.rows.get(r.sel)?;
            return Some(format!("{}: {} ({}) [{}]", row.label, row.value, row.src, r.key));
        }
        commands(self.current()?)
            .get(self.cmd)
            .map(|c| str_of(c, "key").to_string())
    }

    fn copy_all(&self) -> Option<String> {
        let keys: Vec<&str> = commands(self.current()?)
            .iter()
            .map(|c| str_of(c, "key"))
            .collect();
        (!keys.is_empty()).then(|| keys.join("\n"))
    }

    fn question_rows(&self) -> Vec<ListItem<'static>> {
        let t = &self.theme;
        self.items
            .iter()
            .map(|it| {
                let (glyph, style) = match str_of(it, "status") {
                    "done" => ("✓", t.up()),
                    "error" => ("✗", t.down()),
                    _ => ("…", t.dim()),
                };
                let unseen = str_of(it, "status") == "done"
                    && it.get("seen").and_then(Value::as_bool) != Some(true);
                let top = commands(it).first().map_or("", |c| str_of(c, "key"));
                ListItem::new(Line::from(vec![
                    Span::styled(if unseen { "● " } else { "  " }, t.accent()),
                    Span::styled(format!("{glyph} "), style),
                    Span::styled(format!("{:<26} ", top), t.accent()),
                    Span::raw(str_of(it, "query").to_string()),
                    Span::styled(format!("  {}", str_of(it, "ts")), t.dim()),
                ]))
            })
            .collect()
    }

    fn command_rows(&self, item: &Value) -> Vec<ListItem<'static>> {
        let t = &self.theme;
        commands(item)
            .iter()
            .enumerate()
            .map(|(i, c)| {
                ListItem::new(Line::from(vec![
                    Span::styled(format!("{:>2}  ", i + 1), t.dim()),
                    Span::styled(format!("{:<28} ", str_of(c, "key")), t.accent()),
                    Span::styled(format!("{:<28} ", str_of(c, "name")), t.base()),
                    Span::styled(str_of(c, "why").to_string(), t.dim()),
                ]))
            })
            .collect()
    }

    fn pane(&self, title: String, focused: bool) -> Block<'static> {
        let t = &self.theme;
        let border = if focused { t.accent() } else { t.border() };
        Block::new()
            .borders(Borders::ALL)
            .border_style(border)
            .title(Span::styled(title, t.title()))
            .style(t.base())
    }
}

fn commands_len(item: Option<&Value>) -> usize {
    item.map_or(0, |i| commands(i).len())
}

impl Screen for GodelScreen {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        let (list_area, cmd_area, res_area, footer);
        if self.result.is_some() {
            let [a, b, c, d] = Layout::vertical([
                Constraint::Length(5),
                Constraint::Length(12),
                Constraint::Min(7),
                Constraint::Length(1),
            ])
            .areas(area);
            (list_area, cmd_area, res_area, footer) = (a, b, Some(c), d);
        } else {
            let [a, b, d] = Layout::vertical([
                Constraint::Percentage(35),
                Constraint::Min(5),
                Constraint::Length(1),
            ])
            .areas(area);
            (list_area, cmd_area, res_area, footer) = (a, b, None, d);
        }

        let q_focus = self.focus == Focus::Questions;
        let mut qs =
            ListState::default().with_selected((!self.items.is_empty()).then_some(self.item));
        frame.render_stateful_widget(
            List::new(self.question_rows())
                .block(self.pane(" godel · questions ".into(), q_focus))
                .highlight_style(if q_focus {
                    t.selected()
                } else {
                    t.base().fg(t.accent)
                }),
            list_area,
            &mut qs,
        );

        if self.items.is_empty() {
            frame.render_widget(
                Paragraph::new("No questions yet. In the note box (leader-vn) start with \">\", e.g. > aapl q4 performance 2023")
                    .style(t.dim())
                    .wrap(Wrap { trim: true })
                    .block(self.pane(" top 10 commands ".into(), false)),
                cmd_area,
            );
        } else if let Some(item) = self.current().cloned() {
            let title = format!(" top 10 commands · {} ", str_of(&item, "query"));
            let c_focus = self.focus == Focus::Commands;
            match str_of(&item, "status") {
                "done" => {
                    let mut cs = ListState::default().with_selected(Some(self.cmd));
                    frame.render_stateful_widget(
                        List::new(self.command_rows(&item))
                            .block(self.pane(title, c_focus))
                            .highlight_style(if c_focus { t.selected() } else { t.base() }),
                        cmd_area,
                        &mut cs,
                    );
                }
                "error" => frame.render_widget(
                    Paragraph::new(str_of(&item, "error").to_string())
                        .style(t.down())
                        .wrap(Wrap { trim: true })
                        .block(self.pane(title, false)),
                    cmd_area,
                ),
                _ => frame.render_widget(
                    Paragraph::new("cooking…")
                        .style(t.dim())
                        .block(self.pane(title, false)),
                    cmd_area,
                ),
            }
        }

        if let (Some(a), Some(r)) = (res_area, self.result.as_ref()) {
            self.draw_result(frame, a, r);
        }

        help::render_footer(frame, footer, KEYS, self.flash.as_deref(), &t);
        if self.help {
            help::render_overlay(frame, area, "godel", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        if self.help {
            self.help = false;
            return Action::None;
        }
        match key.code {
            KeyCode::Esc if self.focus == Focus::Result => self.focus = Focus::Commands,
            KeyCode::Char('h') | KeyCode::Left if self.focus == Focus::Result => {
                self.focus = Focus::Commands
            }
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Tab | KeyCode::BackTab => {
                self.focus = match (self.focus, self.result.is_some()) {
                    (Focus::Questions, _) => Focus::Commands,
                    (Focus::Commands, true) => Focus::Result,
                    (Focus::Commands, false) | (Focus::Result, _) => Focus::Questions,
                }
            }
            KeyCode::Enter => match self.focus {
                Focus::Questions => self.focus = Focus::Commands,
                _ => self.open_result(),
            },
            KeyCode::Char('j') | KeyCode::Down => self.step(1),
            KeyCode::Char('k') | KeyCode::Up => self.step(-1),
            KeyCode::Char('g') => self.jump(false),
            KeyCode::Char('G') => self.jump(true),
            KeyCode::Char('y') => {
                if let Some(k) = self.copy_current() {
                    return Action::Copy(k);
                }
            }
            KeyCode::Char('Y') if self.focus != Focus::Result => {
                if let Some(all) = self.copy_all() {
                    return Action::Copy(all);
                }
            }
            KeyCode::Char('d') if self.focus == Focus::Questions => self.delete_current(),
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        if self.checked.elapsed().as_millis() >= RELOAD_EVERY_MS {
            self.reload();
            self.mark_seen();
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;
    use serde_json::json;

    fn cmds() -> Value {
        Value::Array(
            (1..=10)
                .map(|i| json!({"key": format!("AAPL US EQ C{i}"), "name": "Financials", "why": "w", "cmd": "FA"}))
                .collect(),
        )
    }

    fn screen_with(items: Value, tag: &str) -> GodelScreen {
        let dir = std::env::temp_dir().join(format!("fl-godel-{tag}-{}", std::process::id()));
        let _ = fs::create_dir_all(&dir);
        let path = dir.join("items.json");
        fs::write(&path, items.to_string()).unwrap();
        let mut s = GodelScreen {
            theme: Theme::default(),
            path,
            items: Vec::new(),
            mtime: None,
            checked: Instant::now(),
            item: 0,
            cmd: 0,
            focus: Focus::Questions,
            result: None,
            flash: None,
            help: false,
        };
        s.reload();
        s.mark_seen();
        s
    }

    fn done(id: &str, q: &str) -> Value {
        json!({"id": id, "query": q, "ts": "10:00:00", "status": "done", "seen": false, "commands": cmds(), "extra": 1})
    }

    fn press(s: &mut GodelScreen, c: KeyCode) -> Action {
        s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
    }

    fn render(s: &mut GodelScreen) -> String {
        let (w, h) = (110, 30);
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| s.draw(f)).unwrap();
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
    fn shows_ten_commands_and_copies_selected_key() {
        let mut s = screen_with(json!([done("a", "aapl q4")]), "copy");
        let out = render(&mut s);
        assert!(out.contains("AAPL US EQ C1") && out.contains("AAPL US EQ C10"));
        assert_eq!(
            press(&mut s, KeyCode::Char('y')),
            Action::Copy("AAPL US EQ C1".into())
        );
        press(&mut s, KeyCode::Tab);
        press(&mut s, KeyCode::Char('j'));
        press(&mut s, KeyCode::Char('j'));
        assert_eq!(
            press(&mut s, KeyCode::Char('y')),
            Action::Copy("AAPL US EQ C3".into())
        );
    }

    #[test]
    fn enter_opens_result_below_with_cursor_trend_and_history() {
        let mk = |id: &str, q: &str| {
            let mut v = done(id, q);
            v["commands"] = json!([
                {"key": "AAPL US EQ FA 2023Q4", "name": "Financials", "why": "w", "cmd": "FA", "tickers": ["AAPL"]},
                {"key": "AAPL US EQ GR", "name": "Ratio Analysis", "why": "w", "cmd": "GR", "tickers": ["AAPL"]},
            ]);
            v
        };
        let mut s = screen_with(json!([mk("a", "aapl q4 2023"), mk("b", "aapl margins last year")]), "res");
        press(&mut s, KeyCode::Enter); // questions -> commands
        press(&mut s, KeyCode::Enter); // run command
        assert!(s.focus == Focus::Result);
        let out = render(&mut s);
        assert!(out.contains("result · AAPL US EQ FA 2023Q4"), "{out}");
        assert!(out.contains("Revenue") && out.contains("TREND") && out.contains("SEEN BEFORE"), "{out}");
        assert!(out.contains("aapl margins last year"), "{out}");
        press(&mut s, KeyCode::Char('j'));
        assert_eq!(s.result.as_ref().unwrap().sel, 1);
        assert!(matches!(press(&mut s, KeyCode::Char('y')), Action::Copy(t) if t.starts_with("Gross margin")));
        assert_eq!(press(&mut s, KeyCode::Esc), Action::None);
        assert!(s.focus == Focus::Commands);
        press(&mut s, KeyCode::Tab);
        press(&mut s, KeyCode::Tab);
        press(&mut s, KeyCode::Char('j')); // moving to another question closes the result
        assert!(s.result.is_none());
    }

    #[test]
    fn copy_all_joins_ten_lines() {
        let mut s = screen_with(json!([done("a", "q")]), "all");
        match press(&mut s, KeyCode::Char('Y')) {
            Action::Copy(t) => assert_eq!(t.lines().count(), 10),
            other => panic!("{other:?}"),
        }
    }

    #[test]
    fn viewing_marks_seen_on_disk_and_keeps_unknown_fields() {
        let s = screen_with(json!([done("a", "q")]), "seen");
        let on_disk: Vec<Value> =
            serde_json::from_str(&fs::read_to_string(&s.path).unwrap()).unwrap();
        assert_eq!(on_disk[0]["seen"], json!(true));
        assert_eq!(on_disk[0]["extra"], json!(1));
    }

    #[test]
    fn delete_removes_row_and_clamps_cursor() {
        let mut s = screen_with(json!([done("a", "one"), done("b", "two")]), "del");
        press(&mut s, KeyCode::Char('j'));
        press(&mut s, KeyCode::Char('d'));
        assert_eq!(s.items.len(), 1);
        assert_eq!(s.item, 0);
        press(&mut s, KeyCode::Char('d'));
        assert!(s.items.is_empty());
        assert!(render(&mut s).contains("No questions yet"));
    }

    #[test]
    fn cooking_and_error_rows_render() {
        let items = json!([
            {"id": "a", "query": "slow one", "ts": "1", "status": "cooking", "commands": []},
            {"id": "b", "query": "bad one", "ts": "2", "status": "error", "error": "429: slow down", "commands": []},
        ]);
        let mut s = screen_with(items, "states");
        assert!(render(&mut s).contains("cooking…"));
        press(&mut s, KeyCode::Char('j'));
        assert!(render(&mut s).contains("429: slow down"));
        assert_eq!(press(&mut s, KeyCode::Char('y')), Action::None);
    }
}
