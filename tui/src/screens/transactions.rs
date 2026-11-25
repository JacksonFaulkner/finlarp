// Standalone transaction history: the E*TRADE records cached in
// `transactions_cache` (py/core/db.py) in the finlarp DuckDB, newest first,
// with a filter and a jump to the ticker's dossier.
//
//   Transactions  /mrv█
//   date                 sym     type           qty       price      amount  description
//   2026-10-30 14:42:04  MRVL    Sold           -10       $194.06   +1940.60  MARVELL TECHNOLOGY ...
//   237 rows · finlarp.duckdb · cache as of 2026-10-31 19:55
//   / filter · j/k move · g/G ends · ^d/^u page · ↵ dossier · esc back
//
// Duplicate records (same transaction_id, which the cache can hold) show once.

use std::collections::HashSet;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::mpsc::Receiver;

use chrono::{DateTime, Local, Utc};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Paragraph, Row, Table, TableState, Wrap};

use crate::app::{Action, Ctx, Route, Screen};
use crate::ui::help::{Help, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

/// One cached E*TRADE record. Transfers and interest carry no symbol.
#[derive(Debug, Clone, PartialEq)]
pub struct Txn {
    pub id: String,
    /// Fill time (epoch millis in the cache), shown in local time.
    pub at: Option<DateTime<Local>>,
    pub kind: String,
    pub symbol: String,
    pub qty: Option<f64>,
    pub price: Option<f64>,
    /// Cash effect: buys negative, sells and income positive.
    pub amount: Option<f64>,
    pub description: String,
}

/// Everything the screen shows, read once at open.
#[derive(Debug, Default)]
pub struct Loaded {
    /// Deduplicated, newest first.
    pub rows: Vec<Txn>,
    /// Newest `fetched_at` across accounts: when the cache was last refreshed.
    pub fetched_at: Option<DateTime<Local>>,
    /// Why there are no rows (cache missing or unreadable).
    pub error: Option<String>,
}

pub struct Transactions {
    rows: Vec<Txn>,
    /// Indices into `rows` that pass the filter, in display order.
    shown: Vec<usize>,
    state: TableState,
    query: String,
    /// True while typing into the `/` filter.
    editing: bool,
    error: Option<String>,
    source: String,
    fetched_at: Option<DateTime<Local>>,
    /// Table body rows visible at the last draw, for ctrl-d / ctrl-u.
    page: usize,
    flash: Option<String>,
    theme: Theme,
    /// The DuckDB the cache lives in (reread after a refresh).
    db_path: PathBuf,
    /// A pull from E*TRADE (or a login step) running in the background.
    job: Option<(Job, Receiver<Result<String, String>>)>,
    /// E*TRADE wants a fresh login: the request token pair, and the code typed so far.
    login: Option<Login>,
    dirty: bool,
}

/// What the background job is.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Job {
    Pull,
    Finish,
}

/// A login in progress: E*TRADE's page is open in the browser, the user types the code.
#[derive(Clone, Debug, PartialEq)]
struct Login {
    url: String,
    token: String,
    secret: String,
    code: String,
}

/// The cache is pulled again on open when it is older than this.
const STALE_MINS: i64 = 60;
const ETRADE: &str = "py/sources/etrade.py";

/// What a pull printed: a login E*TRADE wants, an error, or fine.
#[derive(Debug, PartialEq)]
enum Pulled {
    Ok,
    Login { url: String, token: String, secret: String },
    Err(String),
}

fn parse_pull(out: Result<String, String>) -> Pulled {
    let out = match out {
        Ok(o) => o,
        Err(e) => return Pulled::Err(e.lines().last().unwrap_or("failed").to_string()),
    };
    let v: serde_json::Value = out
        .lines()
        .rev()
        .find_map(|l| serde_json::from_str(l).ok())
        .unwrap_or_default();
    if v["auth_required"] == true {
        let g = |k: &str| v[k].as_str().unwrap_or("").to_string();
        return Pulled::Login {
            url: g("authorize_url"),
            token: g("request_token"),
            secret: g("request_token_secret"),
        };
    }
    Pulled::Ok
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Transactions> {
    let source = ctx
        .db_path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| "finlarp.duckdb".into());
    let mut s = Transactions::new(load(&ctx.db_path), source, ctx.theme);
    s.db_path = ctx.db_path.clone();
    let stale = s
        .fetched_at
        .is_none_or(|t| (Local::now() - t).num_minutes() > STALE_MINS);
    if stale && !cfg!(test) {
        s.pull();
    }
    Ok(s)
}

impl Transactions {
    fn new(loaded: Loaded, source: String, theme: Theme) -> Self {
        let mut s = Self {
            rows: loaded.rows,
            shown: Vec::new(),
            state: TableState::default(),
            query: String::new(),
            editing: false,
            error: loaded.error,
            source,
            fetched_at: loaded.fetched_at,
            page: 10,
            flash: None,
            theme,
            db_path: PathBuf::new(),
            job: None,
            login: None,
            dirty: true,
        };
        s.refilter();
        s
    }

    /// R: pulls the history from E*TRADE now (past the cache), in the background.
    fn pull(&mut self) {
        if self.job.is_some() {
            return;
        }
        self.flash = Some("pulling from E*TRADE…".into());
        self.job = Some((Job::Pull, crate::pyrun::spawn_script(ETRADE, &["transactions_fresh"])));
    }

    /// Enter in the login box: hands E*TRADE the code, then pulls again.
    fn finish_login(&mut self) {
        let Some(l) = self.login.take() else { return };
        let code = l.code.trim().to_string();
        if code.is_empty() {
            self.login = Some(l);
            return;
        }
        self.flash = Some("logging in…".into());
        self.job = Some((
            Job::Finish,
            crate::pyrun::spawn_script(ETRADE, &["auth_finish", &l.token, &l.secret, &code]),
        ));
    }

    /// A finished job: reload the cache, start the login, or say what went wrong.
    fn job_done(&mut self, job: Job, out: Result<String, String>) -> Action {
        self.dirty = true;
        match (job, parse_pull(out)) {
            (Job::Pull, Pulled::Ok) => {
                let keep = self.query.clone();
                let l = load(&self.db_path);
                self.rows = l.rows;
                self.error = l.error;
                self.fetched_at = l.fetched_at;
                self.query = keep;
                self.refilter();
                self.flash = Some(format!("{} rows from E*TRADE", self.rows.len()));
            }
            (Job::Pull, Pulled::Login { url, token, secret }) => {
                self.flash = Some("E*TRADE login: approve in the browser, type the code".into());
                self.login = Some(Login {
                    url: url.clone(),
                    token,
                    secret,
                    code: String::new(),
                });
                return Action::OpenBrowser(url);
            }
            (Job::Finish, Pulled::Ok) => {
                self.job = None;
                self.pull();
            }
            (_, Pulled::Login { .. }) => self.flash = Some("login failed; R to try again".into()),
            (_, Pulled::Err(e)) => self.flash = Some(format!("E*TRADE: {e}")),
        }
        Action::None
    }

    /// Keys while the login code box is open.
    fn on_login_key(&mut self, key: KeyEvent) -> Action {
        let Some(l) = self.login.as_mut() else {
            return Action::None;
        };
        match key.code {
            KeyCode::Esc => {
                self.login = None;
                self.flash = Some("login cancelled".into());
            }
            KeyCode::Enter => self.finish_login(),
            KeyCode::Backspace => {
                l.code.pop();
            }
            KeyCode::Char('o') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                return Action::OpenBrowser(l.url.clone());
            }
            KeyCode::Char(c) if !c.is_whitespace() => l.code.push(c),
            _ => {}
        }
        Action::None
    }

    /// Rows matching every whitespace-separated term of the query
    /// (case-insensitive, over symbol, type and description).
    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        let terms: Vec<&str> = q.split_whitespace().collect();
        self.shown = self
            .rows
            .iter()
            .enumerate()
            .filter(|(_, t)| {
                let hay = format!("{} {} {}", t.symbol, t.kind, t.description).to_lowercase();
                terms.iter().all(|term| hay.contains(term))
            })
            .map(|(i, _)| i)
            .collect();
        self.select(if self.shown.is_empty() { None } else { Some(0) });
    }

    fn select(&mut self, i: Option<usize>) {
        self.state.select(i);
    }

    fn move_by(&mut self, delta: isize) {
        let n = self.shown.len();
        if n == 0 {
            return;
        }
        let cur = self.state.selected().unwrap_or(0) as isize;
        self.select(Some((cur + delta).clamp(0, n as isize - 1) as usize));
    }

    fn selected(&self) -> Option<&Txn> {
        self.state
            .selected()
            .and_then(|s| self.shown.get(s))
            .map(|&i| &self.rows[i])
    }

    fn open_dossier(&mut self) -> Action {
        let symbol = self.selected().map(|t| t.symbol.clone());
        match symbol {
            None => Action::None,
            Some(s) if s.is_empty() => {
                self.flash = Some("no ticker on this row".into());
                Action::None
            }
            Some(s) => Action::Route(Route::Screen {
                screen: "dossier".into(),
                arg: Some(s),
            }),
        }
    }

    fn on_filter_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Enter => self.editing = false,
            KeyCode::Esc => {
                self.editing = false;
                self.query.clear();
                self.refilter();
            }
            KeyCode::Backspace => {
                self.query.pop();
                self.refilter();
            }
            KeyCode::Char('u') if ctrl => {
                self.query.clear();
                self.refilter();
            }
            KeyCode::Char(c) if !ctrl => {
                self.query.push(c);
                self.refilter();
            }
            _ => {}
        }
        Action::None
    }

    fn empty_message(&self) -> Option<String> {
        if self.rows.is_empty() {
            Some(match &self.error {
                Some(e) => {
                    format!("no transactions cached\n\n{e}\n\nRefresh the cache to fill it.")
                }
                None => "no transactions cached yet. Refresh the cache to fill it.".into(),
            })
        } else if self.shown.is_empty() {
            Some(format!(
                "no transactions match \"{}\"  (esc clears)",
                self.query
            ))
        } else {
            None
        }
    }

    fn table(&self, t: Theme) -> Table<'static> {
        let header = Row::new(vec![
            cell("date", t.dim(), false),
            cell("sym", t.dim(), false),
            cell("type", t.dim(), false),
            cell("qty", t.dim(), true),
            cell("price", t.dim(), true),
            cell("amount", t.dim(), true),
            cell("description", t.dim(), false),
        ]);
        let rows: Vec<Row> = self
            .shown
            .iter()
            .map(|&i| {
                let r = &self.rows[i];
                let amount_style = r.amount.map_or(t.base(), |v| t.signed(v));
                Row::new(vec![
                    cell(fmt_date(r.at), t.base(), false),
                    cell(r.symbol.clone(), t.title(), false),
                    cell(r.kind.clone(), t.base(), false),
                    cell(fmt_qty(r.qty), t.base(), true),
                    cell(fmt_price(r.price), t.base(), true),
                    cell(fmt_amount(r.amount), amount_style, true),
                    cell(r.description.clone(), t.dim(), false),
                ])
            })
            .collect();
        Table::new(
            rows,
            [
                Constraint::Length(19),
                Constraint::Length(7),
                Constraint::Length(15),
                Constraint::Length(10),
                Constraint::Length(10),
                Constraint::Length(12),
                Constraint::Fill(1),
            ],
        )
        .header(header)
        .column_spacing(2)
        .style(t.base())
        .row_highlight_style(t.selected())
    }
}

const KEYS: &[Key] = &[
    key("/", "filter (type, ↵ keep, esc clear)"),
    key("j/k", "move"),
    key("g/G", "first / last row"),
    key("^d/^u", "page down / up"),
    key("↵", "dossier"),
    key("R", "pull from E*TRADE now (logs in when the token is stale)"),
    key("^o", "login box: reopen E*TRADE's page"),
    key("esc", "back"),
    key("q", "close"),
    key("^n/^p", "move down / up"),
];

impl Screen for Transactions {
    fn leader_ok(&self) -> bool {
        !self.editing && self.login.is_none()
    }

    fn tick(&mut self) -> Action {
        let Some((job, rx)) = &self.job else {
            return Action::None;
        };
        let job = *job;
        match rx.try_recv() {
            Ok(out) => {
                self.job = None;
                self.job_done(job, out)
            }
            Err(std::sync::mpsc::TryRecvError::Empty) => Action::None,
            Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                self.job = None;
                Action::None
            }
        }
    }

    fn draw(&mut self, frame: &mut Frame) {
        self.dirty = false;
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [top, body, status] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let prefix = " Transactions  /";
        let mut spans = vec![Span::styled(" Transactions", t.title())];
        if self.editing || !self.query.is_empty() {
            spans.push(Span::styled("  /", t.accent()));
            spans.push(Span::styled(self.query.clone(), t.base()));
        }
        frame.render_widget(Paragraph::new(Line::from(spans)), top);
        if self.editing {
            let x = top.x + (text::width(prefix) + text::width(&self.query)) as u16;
            frame.set_cursor_position((x.min(top.right().saturating_sub(1)), top.y));
        }

        match self.empty_message() {
            Some(msg) => {
                frame.render_widget(
                    Paragraph::new(msg)
                        .style(t.dim())
                        .wrap(Wrap { trim: false }),
                    body,
                );
            }
            None => {
                self.page = body.height.saturating_sub(1).max(1) as usize;
                let table = self.table(t);
                frame.render_stateful_widget(table, body, &mut self.state);
            }
        }

        if let Some(l) = &self.login {
            let w = 64.min(area.width.saturating_sub(4));
            let r = ratatui::layout::Rect {
                x: area.x + (area.width.saturating_sub(w)) / 2,
                y: area.y + area.height / 3,
                width: w,
                height: 5,
            };
            frame.render_widget(ratatui::widgets::Clear, r);
            let lines = vec![
                Line::styled("approve fl on E*TRADE's page, then type the code", t.dim()),
                Line::from(vec![
                    Span::styled("code ", t.accent()),
                    Span::styled(format!("{}█", l.code), t.base()),
                ]),
                Line::styled("enter submit · ^o reopen page · esc cancel", t.dim()),
            ];
            frame.render_widget(
                Paragraph::new(lines).block(
                    Block::bordered()
                        .title(" E*TRADE login ")
                        .border_style(t.accent()),
                ),
                r,
            );
        }

        let status_line = match &self.flash {
            Some(f) => f.clone(),
            None => {
                let count = if self.query.is_empty() {
                    format!("{} rows", self.rows.len())
                } else {
                    format!("{} of {} rows", self.shown.len(), self.rows.len())
                };
                let when = self
                    .fetched_at
                    .map(|d| d.format("%Y-%m-%d %H:%M").to_string())
                    .unwrap_or_else(|| "never".into());
                format!(" {count} · {} · cache as of {when}", self.source)
            }
        };
        frame.render_widget(
            Paragraph::new(text::truncate(&status_line, status.width as usize)).style(t.dim()),
            status,
        );
    }

    fn takes_text(&self) -> bool {
        self.editing || self.login.is_some()
    }

    fn help(&self) -> Help {
        Help::new("transactions", KEYS)
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        self.dirty = true;
        if self.login.is_some() {
            return self.on_login_key(key);
        }
        if self.editing {
            return self.on_filter_key(key);
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let half = (self.page / 2).max(1) as isize;
        let page = self.page.max(1) as isize;
        match key.code {
            KeyCode::Esc => {
                if self.query.is_empty() {
                    Action::Quit
                } else {
                    self.query.clear();
                    self.refilter();
                    Action::None
                }
            }
            KeyCode::Char('q') if !ctrl => Action::Quit,
            KeyCode::Char('R') => {
                self.pull();
                Action::None
            }
            KeyCode::Char('/') if !ctrl => {
                self.editing = true;
                Action::None
            }
            KeyCode::Enter => self.open_dossier(),
            KeyCode::Char('j') | KeyCode::Down if !ctrl => {
                self.move_by(1);
                Action::None
            }
            KeyCode::Char('n') if ctrl => {
                self.move_by(1);
                Action::None
            }
            KeyCode::Char('k') | KeyCode::Up if !ctrl => {
                self.move_by(-1);
                Action::None
            }
            KeyCode::Char('p') if ctrl => {
                self.move_by(-1);
                Action::None
            }
            KeyCode::Char('d') if ctrl => {
                self.move_by(half);
                Action::None
            }
            KeyCode::Char('u') if ctrl => {
                self.move_by(-half);
                Action::None
            }
            KeyCode::PageDown => {
                self.move_by(page);
                Action::None
            }
            KeyCode::PageUp => {
                self.move_by(-page);
                Action::None
            }
            KeyCode::Char('g') if !ctrl => {
                if !self.shown.is_empty() {
                    self.select(Some(0));
                }
                Action::None
            }
            KeyCode::Char('G') if !ctrl => {
                if let Some(last) = self.shown.len().checked_sub(1) {
                    self.select(Some(last));
                }
                Action::None
            }
            _ => Action::None,
        }
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
        self.dirty = true;
    }

    fn needs_redraw(&self) -> bool {
        self.dirty || self.job.is_some()
    }

    fn claude_context(&self) -> Option<String> {
        self.selected().map(|t| {
            format!(
                "transaction {} {} {} {} @ {} on {}",
                t.symbol,
                t.kind,
                fmt_qty(t.qty),
                fmt_amount(t.amount),
                fmt_price(t.price),
                fmt_date(t.at),
            )
        })
    }
}

fn cell(s: impl Into<String>, style: Style, right: bool) -> Cell<'static> {
    let line = Line::from(Span::styled(s.into(), style));
    Cell::from(if right { line.right_aligned() } else { line })
}

/// Local time to the second.
fn fmt_date(at: Option<DateTime<Local>>) -> String {
    at.map(|d| d.format("%Y-%m-%d %H:%M:%S").to_string())
        .unwrap_or_else(|| "?".into())
}

/// Four significant digits, trailing zeros dropped (C's `%.4g` for shares).
fn fmt_qty(q: Option<f64>) -> String {
    let Some(v) = q else {
        return String::new();
    };
    if v == 0.0 {
        return "0".into();
    }
    let mag = v.abs().log10().floor() as i32;
    let decimals = (3 - mag).max(0) as usize;
    let s = format!("{:.*}", decimals, v);
    if s.contains('.') {
        s.trim_end_matches('0').trim_end_matches('.').to_string()
    } else {
        s
    }
}

fn fmt_price(p: Option<f64>) -> String {
    p.map(|v| format!("${v:.2}")).unwrap_or_default()
}

fn fmt_amount(a: Option<f64>) -> String {
    a.map(|v| format!("{v:+.2}")).unwrap_or_default()
}

/// One cached record per transaction_id, keeping the first. Rows without an id stay.
fn dedupe(rows: &mut Vec<Txn>) {
    let mut seen = HashSet::new();
    rows.retain(|t| t.id.is_empty() || seen.insert(t.id.clone()));
}

/// `transactions_cache` rows: `[{"transaction_id", "date": epoch_ms, "type",
/// "symbol", "description", "quantity", "price", "amount"}, ...]`.
pub fn parse_txns(json: &str) -> Vec<Txn> {
    let Ok(serde_json::Value::Array(items)) = serde_json::from_str::<serde_json::Value>(json)
    else {
        return Vec::new();
    };
    items
        .iter()
        .map(|t| {
            let s = |k: &str| {
                t.get(k)
                    .and_then(|v| v.as_str())
                    .unwrap_or_default()
                    .to_string()
            };
            let f = |k: &str| t.get(k).and_then(|v| v.as_f64());
            Txn {
                id: s("transaction_id"),
                at: f("date")
                    .and_then(|ms| DateTime::<Utc>::from_timestamp_millis(ms as i64))
                    .map(|d| d.with_timezone(&Local)),
                kind: s("type"),
                symbol: s("symbol"),
                qty: f("quantity"),
                price: f("price"),
                amount: f("amount"),
                description: s("description"),
            }
        })
        .collect()
}

/// Reads the cache at `db_path`. Never panics: a missing file or table
/// comes back as `Loaded::error` with empty rows.
pub fn load(db_path: &Path) -> Loaded {
    match crate::db::open_read_only(db_path) {
        Ok(conn) => load_from(&conn),
        Err(e) => Loaded {
            error: Some(e),
            ..Loaded::default()
        },
    }
}

fn read_cache(conn: &duckdb::Connection) -> Result<Vec<(String, Option<f64>)>, duckdb::Error> {
    let mut stmt = conn.prepare("SELECT transactions_json, fetched_at FROM transactions_cache")?;
    let rows = stmt.query_map([], |r| {
        Ok((r.get::<_, String>(0)?, r.get::<_, Option<f64>>(1)?))
    })?;
    rows.collect()
}

fn load_from(conn: &duckdb::Connection) -> Loaded {
    let cache = match read_cache(conn) {
        Ok(c) => c,
        Err(e) => {
            let msg = e.to_string();
            let error = if msg.contains("does not exist") {
                "transactions_cache table not found".to_string()
            } else {
                msg
            };
            return Loaded {
                error: Some(error),
                ..Loaded::default()
            };
        }
    };
    let fetched_at = cache
        .iter()
        .filter_map(|(_, f)| *f)
        .reduce(f64::max)
        .and_then(|secs| DateTime::<Utc>::from_timestamp(secs as i64, 0))
        .map(|d| d.with_timezone(&Local));
    let mut rows: Vec<Txn> = cache
        .iter()
        .flat_map(|(json, _)| parse_txns(json))
        .collect();
    dedupe(&mut rows);
    // Newest first; undated rows (none in practice) sink to the bottom.
    rows.sort_by(|a, b| b.at.cmp(&a.at));
    Loaded {
        rows,
        fetched_at,
        error: None,
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    use super::*;

    const CACHE_JSON: &str = r#"[
        {"account": "1", "transaction_id": "3", "date": 1793388284000, "type": "Sold",
         "description": "MARVELL TECHNOLOGY", "symbol": "MRVL", "quantity": -10, "price": 194.0644, "amount": 1940.6},
        {"account": "1", "transaction_id": "1", "date": 1793343600000, "type": "Interest Income",
         "description": "BANK PERIOD", "symbol": "MSBNK", "quantity": -0.22, "price": 0, "amount": 0.22},
        {"account": "1", "transaction_id": "2", "date": 1793300000000, "type": "Bought",
         "description": "NVIDIA CORP", "symbol": "NVDA", "quantity": 5, "price": 100.5, "amount": -502.5},
        {"account": "1", "transaction_id": "2", "date": 1793300000000, "type": "Bought",
         "description": "NVIDIA CORP", "symbol": "NVDA", "quantity": 5, "price": 100.5, "amount": -502.5},
        {"account": "1", "transaction_id": "4", "date": 1793200000000, "type": "Online Transfer",
         "description": "ACH DEPOSIT", "quantity": 0, "amount": 1000}
    ]"#;

    fn key(code: KeyCode) -> KeyEvent {
        KeyEvent::new(code, KeyModifiers::NONE)
    }

    fn ctrl(c: char) -> KeyEvent {
        KeyEvent::new(KeyCode::Char(c), KeyModifiers::CONTROL)
    }

    fn press(s: &mut Transactions, k: KeyEvent) -> Action {
        s.on_key(k)
    }

    fn typed(s: &mut Transactions, text: &str) {
        press(s, key(KeyCode::Char('/')));
        for c in text.chars() {
            press(s, key(KeyCode::Char(c)));
        }
    }

    fn screen_with(json: &str) -> Transactions {
        let conn = duckdb::Connection::open_in_memory().unwrap();
        conn.execute_batch(&format!(
            "CREATE TABLE transactions_cache (account VARCHAR PRIMARY KEY, transactions_json VARCHAR, fetched_at DOUBLE);
             INSERT INTO transactions_cache VALUES ('1', '{}', 1793400000.0);",
            json.replace('\'', "''")
        ))
        .unwrap();
        Transactions::new(load_from(&conn), "finlarp.duckdb".into(), Theme::default())
    }

    fn sample() -> Transactions {
        screen_with(CACHE_JSON)
    }

    fn symbols(s: &Transactions) -> Vec<String> {
        s.shown.iter().map(|&i| s.rows[i].symbol.clone()).collect()
    }

    fn render(s: &mut Transactions, w: u16, h: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        let buf = term.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| buf[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn pull_output_asks_for_login_or_reloads() {
        let login = r#"{"auth_required": true, "authorize_url": "https://us.etrade.com/e/t/etws/authorize?key=k&token=t", "request_token": "t", "request_token_secret": "s"}"#;
        assert_eq!(
            parse_pull(Ok(login.into())),
            Pulled::Login {
                url: "https://us.etrade.com/e/t/etws/authorize?key=k&token=t".into(),
                token: "t".into(),
                secret: "s".into()
            }
        );
        assert_eq!(parse_pull(Ok("{\"ok\": true}".into())), Pulled::Ok);
        assert!(matches!(parse_pull(Err("x\nboom".into())), Pulled::Err(e) if e == "boom"));
        let mut s = sample();
        let a = s.job_done(Job::Pull, Ok(login.into()));
        assert!(matches!(a, Action::OpenBrowser(_)));
        assert!(s.takes_text());
        for c in "AB12".chars() {
            press(&mut s, key(KeyCode::Char(c)));
        }
        assert_eq!(s.login.as_ref().unwrap().code, "AB12");
        press(&mut s, key(KeyCode::Esc));
        assert!(s.login.is_none());
    }

    #[test]
    fn loads_newest_first_and_dedupes_by_id() {
        let s = sample();
        assert_eq!(s.rows.len(), 4); // duplicate transaction_id 2 collapsed
        assert_eq!(s.rows[0].symbol, "MRVL");
        assert_eq!(s.rows[3].symbol, ""); // the transfer, oldest
        assert!(s.error.is_none());
        assert!(s.fetched_at.is_some());
    }

    #[test]
    fn filter_matches_symbol_type_and_description() {
        let mut s = sample();
        typed(&mut s, "nvda");
        assert_eq!(symbols(&s), vec!["NVDA"]);
        press(&mut s, key(KeyCode::Esc)); // clears and leaves edit mode
        assert_eq!(s.shown.len(), 4);
        typed(&mut s, "sold marvell");
        assert_eq!(symbols(&s), vec!["MRVL"]);
        press(&mut s, key(KeyCode::Enter)); // applies: keeps the filter, leaves edit mode
        assert!(!s.editing);
        assert_eq!(s.query, "sold marvell");
        typed(&mut s, "zzz");
        assert!(s.shown.is_empty());
        assert!(s.empty_message().unwrap().contains("no transactions match"));
    }

    #[test]
    fn enter_opens_dossier_for_the_selected_ticker() {
        let mut s = sample();
        assert_eq!(
            press(&mut s, key(KeyCode::Enter)),
            Action::Route(Route::Screen {
                screen: "dossier".into(),
                arg: Some("MRVL".into()),
            })
        );
        press(&mut s, key(KeyCode::Char('G')));
        assert_eq!(press(&mut s, key(KeyCode::Enter)), Action::None);
        assert_eq!(s.flash.as_deref(), Some("no ticker on this row"));
    }

    #[test]
    fn navigation_clamps_and_jumps() {
        let mut s = sample();
        press(&mut s, key(KeyCode::Char('k')));
        assert_eq!(s.state.selected(), Some(0));
        press(&mut s, key(KeyCode::Char('j')));
        press(&mut s, key(KeyCode::Char('j')));
        assert_eq!(s.state.selected(), Some(2));
        press(&mut s, key(KeyCode::Char('G')));
        assert_eq!(s.state.selected(), Some(3));
        press(&mut s, key(KeyCode::Char('j')));
        assert_eq!(s.state.selected(), Some(3));
        press(&mut s, key(KeyCode::Char('g')));
        assert_eq!(s.state.selected(), Some(0));
        press(&mut s, ctrl('d'));
        assert_eq!(s.state.selected(), Some(3)); // page of 10 covers all rows: half-page clamps
    }

    #[test]
    fn esc_clears_filter_before_leaving_and_q_leaves() {
        let mut s = sample();
        typed(&mut s, "nvda");
        press(&mut s, key(KeyCode::Enter));
        assert_eq!(press(&mut s, key(KeyCode::Esc)), Action::None);
        assert!(s.query.is_empty());
        assert_eq!(press(&mut s, key(KeyCode::Esc)), Action::Quit);
        assert_eq!(press(&mut sample(), key(KeyCode::Char('q'))), Action::Quit);
    }

    #[test]
    fn q_types_into_filter_and_space_is_not_a_leader() {
        let mut s = sample();
        typed(&mut s, "q");
        assert_eq!(s.query, "q");
        assert!(!s.leader_ok());
        press(&mut s, key(KeyCode::Enter));
        assert!(s.leader_ok());
    }

    #[test]
    fn empty_cache_shows_message() {
        let mut s = screen_with("[]");
        assert!(s.rows.is_empty());
        assert!(
            s.empty_message()
                .unwrap()
                .contains("no transactions cached")
        );
        assert!(render(&mut s, 80, 10).contains("no transactions cached"));
    }

    #[test]
    fn missing_table_is_an_error_not_a_panic() {
        let conn = duckdb::Connection::open_in_memory().unwrap();
        let loaded = load_from(&conn);
        assert!(loaded.rows.is_empty());
        assert_eq!(
            loaded.error.as_deref(),
            Some("transactions_cache table not found")
        );
    }

    #[test]
    fn missing_file_is_an_error_not_a_panic() {
        let loaded = load(Path::new("/nonexistent/finlarp-test.duckdb"));
        assert!(loaded.rows.is_empty());
        assert!(loaded.error.is_some());
    }

    #[test]
    fn renders_rows_and_status() {
        let mut s = sample();
        let out = render(&mut s, 120, 12);
        assert!(out.contains("MRVL"));
        assert!(out.contains("Sold"));
        assert!(out.contains("$194.06"));
        assert!(out.contains("+1940.60"));
        assert!(out.contains("4 rows"));
        assert!(out.contains("finlarp.duckdb"));
        assert!(out.contains("cache as of"));
    }

    #[test]
    fn formats_quantities_prices_and_amounts() {
        assert_eq!(fmt_qty(Some(-10.0)), "-10");
        assert_eq!(fmt_qty(Some(0.123456)), "0.1235");
        assert_eq!(fmt_qty(Some(1234.5)), "1234");
        assert_eq!(fmt_qty(None), "");
        assert_eq!(fmt_price(Some(194.0644)), "$194.06");
        assert_eq!(fmt_amount(Some(1940.6)), "+1940.60");
        assert_eq!(fmt_amount(Some(-502.5)), "-502.50");
        assert_eq!(fmt_date(None), "?");
    }
}
