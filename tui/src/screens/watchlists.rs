// Standalone watchlist (nvim `<leader>vww`). The writable list is
// data/watchlist.txt: one ticker per line, `#` starts a comment. That is the
// file py/jobs/refresh.py and py/derive/dossier_tabs/mine.py read, so adding
// or removing here is what they see. Each row shows the latest daily close
// and its change from bars_1d.
//
//   Watchlist ›  data/watchlist.txt · 3 symbols
//   > NVDA        213.66   -0.79%   2026-10-28
//     MU            ...
//   ^n/^p move · ↵ dossier · a add · x remove · r reload · esc back

use std::collections::HashMap;
use std::io;
use std::path::{Path, PathBuf};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

/// The writable watchlist, relative to the repo root.
const FILE: &str = "data/watchlist.txt";

#[derive(Debug, Clone, PartialEq)]
struct Quote {
    /// Session date of the last close, YYYY-MM-DD (New York time).
    date: String,
    last: f64,
    prev: Option<f64>,
}

#[derive(Debug, Clone, PartialEq)]
struct Row {
    symbol: String,
    quote: Option<Quote>,
}

pub struct Watchlists {
    path: PathBuf,
    db_path: PathBuf,
    theme: Theme,
    rows: Vec<Row>,
    state: ListState,
    /// Some(typed text) while the add prompt is open.
    adding: Option<String>,
    flash: Option<String>,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Watchlists> {
    let mut w = Watchlists {
        path: crate::pyrun::plugin_dir().join(FILE),
        db_path: ctx.db_path.clone(),
        theme: ctx.theme,
        rows: Vec::new(),
        state: ListState::default(),
        adding: None,
        flash: None,
    };
    w.reload();
    Ok(w)
}

/// The ticker on one watchlist line: text before `#`, trimmed, uppercased
/// (the same rule as refresh.py's watchlist()).
fn line_symbol(line: &str) -> String {
    line.split('#').next().unwrap_or("").trim().to_uppercase()
}

/// Distinct tickers in file order.
fn parse(text: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for sym in text.lines().map(line_symbol) {
        if !sym.is_empty() && !out.contains(&sym) {
            out.push(sym);
        }
    }
    out
}

/// Letters, digits, `.` and `-`, starting with a letter or digit (BRK.B, BF-B).
pub fn valid_symbol(s: &str) -> bool {
    s.len() <= 12
        && s.chars().next().is_some_and(|c| c.is_ascii_alphanumeric())
        && s.chars().all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-')
}

/// `text` with `sym` appended on its own line; unchanged if already listed.
fn with_symbol(text: &str, sym: &str) -> String {
    if parse(text).iter().any(|s| s == sym) {
        return text.to_string();
    }
    let mut out = text.to_string();
    if !out.is_empty() && !out.ends_with('\n') {
        out.push('\n');
    }
    out.push_str(sym);
    out.push('\n');
    out
}

/// `text` without the lines for `sym`; comments and other lines are kept.
fn without_symbol(text: &str, sym: &str) -> String {
    let mut out = String::new();
    for line in text.lines() {
        if line_symbol(line) == sym {
            continue;
        }
        out.push_str(line);
        out.push('\n');
    }
    out
}

fn change_pct(q: &Quote) -> Option<f64> {
    q.prev
        .filter(|p| *p != 0.0)
        .map(|p| (q.last - p) / p * 100.0)
}

fn read_file(path: &Path) -> Result<String, String> {
    match std::fs::read_to_string(path) {
        Ok(s) => Ok(s),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(String::new()),
        Err(e) => Err(format!("{}: {e}", path.display())),
    }
}

/// Writes via a temp file and rename, so a reader never sees a half-written list.
fn write_file(path: &Path, text: &str) -> Result<(), String> {
    let err = |e: io::Error| format!("{}: {e}", path.display());
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir).map_err(err)?;
    }
    let tmp = path.with_extension("txt.tmp");
    std::fs::write(&tmp, text).map_err(err)?;
    std::fs::rename(&tmp, path).map_err(err)
}

/// Latest close and the close before it, per symbol, from bars_1d.
fn latest_quotes(
    conn: &duckdb::Connection,
    syms: &[String],
) -> Result<HashMap<String, Quote>, String> {
    if syms.is_empty() {
        return Ok(HashMap::new());
    }
    let marks = vec!["?"; syms.len()].join(",");
    let sql = format!(
        "WITH r AS (
           SELECT symbol, close,
                  CAST(ts_event AT TIME ZONE 'America/New_York' AS DATE) AS d,
                  row_number() OVER (PARTITION BY symbol ORDER BY ts_event DESC) AS rn
           FROM bars_1d
           WHERE symbol IN ({marks}) AND close IS NOT NULL)
         SELECT symbol,
                max(CASE WHEN rn = 1 THEN CAST(d AS VARCHAR) END),
                max(CASE WHEN rn = 1 THEN close END),
                max(CASE WHEN rn = 2 THEN close END)
         FROM r WHERE rn <= 2
         GROUP BY symbol"
    );
    // No bars table yet = no prices; the rows still list.
    let Ok(mut stmt) = conn.prepare(&sql) else {
        return Ok(HashMap::new());
    };
    let rows = stmt
        .query_map(duckdb::params_from_iter(syms.iter().cloned()), |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, Option<String>>(1)?,
                r.get::<_, Option<f64>>(2)?,
                r.get::<_, Option<f64>>(3)?,
            ))
        })
        .map_err(|e| e.to_string())?;
    let mut out = HashMap::new();
    for row in rows {
        let (sym, date, last, prev) = row.map_err(|e| e.to_string())?;
        if let (Some(date), Some(last)) = (date, last) {
            out.insert(sym, Quote { date, last, prev });
        }
    }
    Ok(out)
}

fn load_quotes(db_path: &Path, syms: &[String]) -> Result<HashMap<String, Quote>, String> {
    if syms.is_empty() {
        return Ok(HashMap::new());
    }
    let conn = crate::db::open_read_only(db_path)?;
    latest_quotes(&conn, syms)
}

impl Watchlists {
    /// Re-reads the file and the prices; keeps the cursor where it was.
    fn reload(&mut self) {
        let keep = self.state.selected();
        let syms = match read_file(&self.path) {
            Ok(t) => parse(&t),
            Err(e) => {
                self.flash = Some(e);
                Vec::new()
            }
        };
        let quotes = match load_quotes(&self.db_path, &syms) {
            Ok(q) => q,
            Err(e) => {
                self.flash = Some(format!("no prices: {e}"));
                HashMap::new()
            }
        };
        self.rows = syms
            .into_iter()
            .map(|symbol| {
                let quote = quotes.get(&symbol).cloned();
                Row { symbol, quote }
            })
            .collect();
        self.select(keep);
    }

    /// Selects `i`, clamped to the rows (none when the list is empty).
    fn select(&mut self, i: Option<usize>) {
        self.state.select(match (i, self.rows.len()) {
            (_, 0) => None,
            (Some(i), n) => Some(i.min(n - 1)),
            (None, _) => Some(0),
        });
    }

    fn selected(&self) -> Option<&Row> {
        self.state.selected().and_then(|i| self.rows.get(i))
    }

    fn step(&mut self, delta: isize) {
        let n = self.rows.len();
        if n == 0 {
            return;
        }
        let cur = self.state.selected().unwrap_or(0) as isize;
        self.state
            .select(Some((cur + delta).rem_euclid(n as isize) as usize));
    }

    fn add(&mut self, typed: &str) {
        let sym = typed.trim().to_uppercase();
        if sym.is_empty() {
            return;
        }
        if !valid_symbol(&sym) {
            self.flash = Some(format!("not a ticker: {sym}"));
            return;
        }
        if let Some(i) = self.rows.iter().position(|r| r.symbol == sym) {
            self.select(Some(i));
            self.flash = Some(format!("{sym} is already on the watchlist"));
            return;
        }
        let written = read_file(&self.path)
            .and_then(|t| write_file(&self.path, &with_symbol(&t, &sym)));
        match written {
            Ok(()) => {
                self.reload();
                if let Some(i) = self.rows.iter().position(|r| r.symbol == sym) {
                    self.select(Some(i));
                }
                self.flash = Some(format!("added {sym}"));
            }
            Err(e) => self.flash = Some(e),
        }
    }

    fn remove_selected(&mut self) {
        let Some(sym) = self.selected().map(|r| r.symbol.clone()) else {
            return;
        };
        let written = read_file(&self.path)
            .and_then(|t| write_file(&self.path, &without_symbol(&t, &sym)));
        match written {
            Ok(()) => {
                self.reload();
                self.flash = Some(format!("removed {sym}"));
            }
            Err(e) => self.flash = Some(e),
        }
    }

    fn open_selected(&self) -> Action {
        match self.selected() {
            Some(r) => Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some(r.symbol.clone()),
            }),
            None => Action::None,
        }
    }

    fn row_line(&self, r: &Row) -> Line<'static> {
        let t = self.theme;
        let (price, chg, date, style) = match &r.quote {
            Some(q) => {
                let chg = change_pct(q);
                (
                    format!("{:.2}", q.last),
                    chg.map_or("-".to_string(), |p| format!("{p:+.2}%")),
                    q.date.clone(),
                    chg.map_or(t.dim(), |p| t.signed(p)),
                )
            }
            None => ("-".into(), "-".into(), String::new(), t.dim()),
        };
        Line::from(vec![
            Span::styled(format!("  {:<8}", r.symbol), t.title()),
            Span::styled(format!("{price:>10}"), t.base()),
            Span::styled(format!("  {chg:>9}"), style),
            Span::styled(format!("  {date}"), t.dim()),
        ])
    }

    fn on_add_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => self.adding = None,
            KeyCode::Enter => {
                let typed = self.adding.take().unwrap_or_default();
                self.add(&typed);
            }
            KeyCode::Backspace => {
                if let Some(buf) = self.adding.as_mut() {
                    buf.pop();
                }
            }
            KeyCode::Char(c) if !ctrl && !c.is_whitespace() => {
                if let Some(buf) = self.adding.as_mut() {
                    buf.push(c.to_ascii_uppercase());
                }
            }
            _ => {}
        }
        Action::None
    }
}

impl Screen for Watchlists {
    fn leader_ok(&self) -> bool {
        self.adding.is_none()
    }

    fn needs_redraw(&self) -> bool {
        false
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let n = self.rows.len();
        let title = format!(
            " Watchlist › {FILE} · {n} symbol{}",
            if n == 1 { "" } else { "s" }
        );
        let line2: Line = match &self.adding {
            Some(buf) => {
                frame.set_cursor_position((
                    head.x + (text::width(" add ticker › ") + text::width(buf)) as u16,
                    head.y + 1,
                ));
                Line::from(vec![
                    Span::styled(" add ticker › ", t.accent()),
                    Span::styled(buf.clone(), t.base()),
                ])
            }
            None => Line::styled(self.flash.clone().unwrap_or_default(), t.dim()),
        };
        frame.render_widget(
            Paragraph::new(vec![Line::styled(title, t.accent()), line2]),
            head,
        );

        if self.rows.is_empty() {
            frame.render_widget(
                Paragraph::new(format!(
                    "  No tickers yet. Press a to add one.\n  Stored in {FILE}, which refresh and the dossier read."
                ))
                .style(t.dim()),
                body,
            );
        } else {
            let items: Vec<ListItem> = self
                .rows
                .iter()
                .map(|r| ListItem::new(self.row_line(r)))
                .collect();
            frame.render_stateful_widget(
                List::new(items)
                    .style(t.base())
                    .highlight_style(t.selected()),
                body,
                &mut self.state,
            );
        }

        let keys = if self.adding.is_some() {
            " ↵ add · esc cancel"
        } else {
            " ↵ dossier · a add · x remove · r reload · esc back"
        };
        frame.render_widget(Paragraph::new(keys).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.adding.is_some() {
            return self.on_add_key(key);
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
            KeyCode::Enter => self.open_selected(),
            KeyCode::Down | KeyCode::Char('j') => {
                self.step(1);
                Action::None
            }
            KeyCode::Up | KeyCode::Char('k') => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('n') if ctrl => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('p') if ctrl => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('a') => {
                self.flash = None;
                self.adding = Some(String::new());
                Action::None
            }
            KeyCode::Char('x') | KeyCode::Delete => {
                self.remove_selected();
                Action::None
            }
            KeyCode::Char('r') => {
                self.reload();
                self.flash = Some("reloaded".into());
                Action::None
            }
            _ => Action::None,
        }
    }
}

#[cfg(test)]
mod tests {
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};
    use ratatui::Terminal;

    use super::*;

    fn key(code: KeyCode) -> KeyEvent {
        KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        }
    }

    fn screen_with(path: PathBuf, db_path: PathBuf) -> Watchlists {
        let mut w = Watchlists {
            path,
            db_path,
            theme: Theme::default(),
            rows: Vec::new(),
            state: ListState::default(),
            adding: None,
            flash: None,
        };
        w.reload();
        w
    }

    fn temp_dir(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("fl-watchlist-{name}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    fn rendered(w: &mut Watchlists, cols: u16, rows: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(cols, rows)).unwrap();
        term.draw(|f| w.draw(f)).unwrap();
        let buf = term.backend().buffer().clone();
        (0..rows)
            .map(|y| (0..cols).map(|x| buf[(x, y)].symbol()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn parses_comments_blanks_and_duplicates() {
        let text = "mrvl  # core\n\n# section\nNVDA\nMRVL\n  brk.b # odd\n";
        assert_eq!(parse(text), vec!["MRVL", "NVDA", "BRK.B"]);
    }

    #[test]
    fn valid_symbols() {
        assert!(valid_symbol("NVDA"));
        assert!(valid_symbol("BRK.B"));
        assert!(valid_symbol("BF-B"));
        assert!(!valid_symbol("--JSON"));
        assert!(!valid_symbol("A B"));
        assert!(!valid_symbol(""));
        assert!(!valid_symbol("ABCDEFGHIJKLMN"));
    }

    #[test]
    fn with_symbol_appends_once() {
        assert_eq!(with_symbol("", "NVDA"), "NVDA\n");
        assert_eq!(with_symbol("MRVL  # core", "NVDA"), "MRVL  # core\nNVDA\n");
        assert_eq!(with_symbol("NVDA\n", "NVDA"), "NVDA\n");
    }

    #[test]
    fn without_symbol_keeps_other_lines() {
        let text = "# keep me\nMRVL  # core\nNVDA\nmrvl\n";
        assert_eq!(without_symbol(text, "MRVL"), "# keep me\nNVDA\n");
        assert_eq!(without_symbol("NVDA\n", "ZZZ"), "NVDA\n");
    }

    #[test]
    fn change_is_relative_to_previous_close() {
        let q = Quote { date: "2026-10-28".into(), last: 213.66, prev: Some(215.38) };
        let c = change_pct(&q).unwrap();
        assert!((c + 0.7989).abs() < 1e-3, "{c}");
        let none = Quote { date: String::new(), last: 1.0, prev: None };
        assert_eq!(change_pct(&none), None);
    }

    #[test]
    fn latest_quotes_reads_last_two_closes_in_new_york_dates() {
        let conn = duckdb::Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE bars_1d (ts_event TIMESTAMPTZ, close DOUBLE, symbol VARCHAR);
             INSERT INTO bars_1d VALUES
               ('2026-10-27T20:00:00-04:00', 215.38, 'NVDA'),
               ('2026-10-28T20:00:00-04:00', 213.66, 'NVDA'),
               ('2026-10-26T20:00:00-04:00', 1.0, 'NVDA'),
               ('2026-10-28T20:00:00-04:00', 5.0, 'MU');",
        )
        .unwrap();
        let got = latest_quotes(&conn, &["NVDA".into(), "ZZZ".into()]).unwrap();
        assert_eq!(got.len(), 1);
        let q = &got["NVDA"];
        assert_eq!(q.date, "2026-10-28");
        assert_eq!(q.last, 213.66);
        assert_eq!(q.prev, Some(215.38));
    }

    #[test]
    fn no_bars_table_means_no_prices_not_an_error() {
        let conn = duckdb::Connection::open_in_memory().unwrap();
        assert!(latest_quotes(&conn, &["NVDA".into()]).unwrap().is_empty());
    }

    #[test]
    fn add_and_remove_round_trip_the_file() {
        let dir = temp_dir("roundtrip");
        let path = dir.join("data").join("watchlist.txt");
        let mut w = screen_with(path.clone(), dir.join("missing.duckdb"));
        assert!(w.rows.is_empty());

        w.on_key(key(KeyCode::Char('a')));
        for c in "nvda".chars() {
            w.on_key(key(KeyCode::Char(c)));
        }
        w.on_key(key(KeyCode::Enter));
        assert_eq!(std::fs::read_to_string(&path).unwrap(), "NVDA\n");
        assert_eq!(w.rows.len(), 1);
        assert_eq!(w.selected().unwrap().symbol, "NVDA");

        w.on_key(key(KeyCode::Char('x')));
        assert_eq!(std::fs::read_to_string(&path).unwrap(), "");
        assert!(w.rows.is_empty());
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn enter_opens_dossier_for_selected_row() {
        let dir = temp_dir("enter");
        let path = dir.join("watchlist.txt");
        std::fs::write(&path, "MRVL\nNVDA\n").unwrap();
        let mut w = screen_with(path, dir.join("missing.duckdb"));
        w.on_key(key(KeyCode::Char('j')));
        assert_eq!(
            w.on_key(key(KeyCode::Enter)),
            Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some("NVDA".into()),
            })
        );
        assert_eq!(w.on_key(key(KeyCode::Esc)), Action::Quit);
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn leader_is_off_while_typing_a_symbol() {
        let dir = temp_dir("leader");
        let mut w = screen_with(dir.join("w.txt"), dir.join("missing.duckdb"));
        assert!(w.leader_ok());
        w.on_key(key(KeyCode::Char('a')));
        assert!(!w.leader_ok());
        w.on_key(key(KeyCode::Esc));
        assert!(w.leader_ok());
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn renders_rows_with_price_and_change() {
        let mut w = Watchlists {
            path: PathBuf::from("unused"),
            db_path: PathBuf::from("unused"),
            theme: Theme::default(),
            rows: vec![
                Row {
                    symbol: "NVDA".into(),
                    quote: Some(Quote {
                        date: "2026-10-28".into(),
                        last: 213.66,
                        prev: Some(215.38),
                    }),
                },
                Row { symbol: "MU".into(), quote: None },
            ],
            state: ListState::default(),
            adding: None,
            flash: None,
        };
        w.select(Some(0));
        let out = rendered(&mut w, 60, 8);
        assert!(out.contains("Watchlist"), "{out}");
        assert!(out.contains("NVDA"), "{out}");
        assert!(out.contains("213.66"), "{out}");
        assert!(out.contains("-0.80%"), "{out}");
        assert!(out.contains("2026-10-28"), "{out}");
        assert!(out.contains("MU"), "{out}");
    }
}
