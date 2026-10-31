// `fl claude_history`: browser over Claude Code sessions on this machine
// (~/.claude/projects/<encoded-cwd>/<session>.jsonl), newest first.
//
//   Claude history  12 of 300
//   / finlarp█
//   2026-11-01 17:38  finlarp     okay we were working on claude code chat...
//
// Sessions are listed from file mtimes at open; each transcript's cwd and
// first prompt are read lazily, a batch per tick, and only from the first
// few lines. `/` filters (substring over cwd and first prompt) · j/k move ·
// ^d/^u page · g/G ends · enter resumes in a new tmux window · esc/q back.

use std::cmp::Reverse;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::SystemTime;

use chrono::{DateTime, Local};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph};
use serde_json::Value;

use crate::app::{Action, Ctx, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

/// Most recent transcripts listed; older ones are never opened.
const MAX_SESSIONS: usize = 300;
/// Sessions whose header is read per tick, so the list paints at once.
const PARSE_BATCH: usize = 25;
/// Lines read per transcript while looking for cwd and the first prompt.
const MAX_LINES: usize = 200;
/// Stored prompt length in chars; the list only shows one line of it.
const MAX_PROMPT: usize = 300;
const PROJECT_COL: usize = 22;
const DATE_FMT: &str = "%Y-%m-%d %H:%M";

#[derive(Debug, Clone)]
struct Session {
    id: String,
    path: PathBuf,
    /// Encoded project dir name (e.g. `-Users-me-code-x`), shown when cwd is unknown.
    project_dir: String,
    modified: SystemTime,
    cwd: String,
    prompt: String,
    /// Header (cwd + first prompt) has been read.
    parsed: bool,
}

impl Session {
    fn load(&mut self) {
        self.parsed = true;
        let Ok(file) = File::open(&self.path) else {
            return;
        };
        let (cwd, prompt) = parse_header(BufReader::new(file).lines().map_while(Result::ok).take(MAX_LINES));
        self.cwd = cwd;
        self.prompt = prompt;
    }

    fn matches(&self, q_lower: &str) -> bool {
        if q_lower.is_empty() {
            return true;
        }
        self.parsed
            && (self.cwd.to_lowercase().contains(q_lower) || self.prompt.to_lowercase().contains(q_lower))
    }

    fn project_label(&self) -> String {
        if self.cwd.is_empty() {
            return self.project_dir.clone();
        }
        Path::new(&self.cwd)
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_else(|| self.cwd.clone())
    }
}

/// First `cwd` and first real user prompt in a transcript's lines.
fn parse_header(lines: impl Iterator<Item = String>) -> (String, String) {
    let mut cwd = String::new();
    let mut prompt = String::new();
    for line in lines {
        if cwd.is_empty() || prompt.is_empty() {
            let Ok(v) = serde_json::from_str::<Value>(&line) else {
                continue;
            };
            if cwd.is_empty()
                && let Some(c) = v.get("cwd").and_then(Value::as_str)
            {
                cwd = c.to_string();
            }
            if prompt.is_empty()
                && let Some(p) = user_prompt(&v)
            {
                prompt = p;
            }
        }
        if !cwd.is_empty() && !prompt.is_empty() {
            break;
        }
    }
    (cwd, prompt)
}

/// Text of a typed user message; None for tool results, meta lines, and
/// slash-command / local-command wrappers.
fn user_prompt(v: &Value) -> Option<String> {
    if v.get("type").and_then(Value::as_str) != Some("user") {
        return None;
    }
    if v.get("isMeta").and_then(Value::as_bool) == Some(true) {
        return None;
    }
    let raw = match v.pointer("/message/content")? {
        Value::String(s) => s.clone(),
        Value::Array(blocks) => blocks
            .iter()
            .filter(|b| b.get("type").and_then(Value::as_str) == Some("text"))
            .find_map(|b| b.get("text").and_then(Value::as_str))?
            .to_string(),
        _ => return None,
    };
    let clean = raw.split_whitespace().collect::<Vec<_>>().join(" ");
    if clean.is_empty() || clean.starts_with('<') || clean.starts_with("Caveat:") {
        return None;
    }
    Some(clean.chars().take(MAX_PROMPT).collect())
}

/// Top-level `<projects>/<dir>/<id>.jsonl` files, newest first, capped.
/// Subagent transcripts live one level deeper and are skipped.
fn list_sessions(root: &Path) -> Vec<Session> {
    let Ok(projects) = std::fs::read_dir(root) else {
        return Vec::new();
    };
    let mut found = Vec::new();
    for proj in projects.flatten() {
        let dir = proj.path();
        if !dir.is_dir() {
            continue;
        }
        let project_dir = proj.file_name().to_string_lossy().into_owned();
        let Ok(files) = std::fs::read_dir(&dir) else {
            continue;
        };
        for f in files.flatten() {
            let path = f.path();
            if path.extension().is_none_or(|e| e != "jsonl") {
                continue;
            }
            let Some(id) = path.file_stem().map(|s| s.to_string_lossy().into_owned()) else {
                continue;
            };
            let Ok(modified) = f.metadata().and_then(|m| m.modified()) else {
                continue;
            };
            found.push(Session {
                id,
                path,
                project_dir: project_dir.clone(),
                modified,
                cwd: String::new(),
                prompt: String::new(),
                parsed: false,
            });
        }
    }
    found.sort_by_key(|s| Reverse(s.modified));
    found.truncate(MAX_SESSIONS);
    found
}

fn projects_dir() -> PathBuf {
    std::env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_default()
        .join(".claude")
        .join("projects")
}

/// Session ids are UUIDs; anything else never reaches the tmux command line.
fn valid_session_id(id: &str) -> bool {
    !id.is_empty() && id.chars().all(|c| c.is_ascii_alphanumeric() || c == '-')
}

/// Arguments for `tmux` that open a new window running `claude --resume`.
fn tmux_args(session: &Session) -> Vec<String> {
    let mut args = vec!["new-window".to_string()];
    if !session.cwd.is_empty() {
        args.push("-c".into());
        args.push(session.cwd.clone());
    }
    args.push(format!("claude --resume {}", session.id));
    args
}

fn tilde(path: &str) -> String {
    match std::env::var("HOME") {
        Ok(home) if !home.is_empty() && path.starts_with(&home) => format!("~{}", &path[home.len()..]),
        _ => path.to_string(),
    }
}

pub struct ClaudeHistory {
    sessions: Vec<Session>,
    /// `sessions[..parsed]` have had their headers read.
    parsed: usize,
    /// Indices into `sessions` that pass the filter, in display order.
    shown: Vec<usize>,
    query: String,
    filtering: bool,
    state: ListState,
    /// Rows per screenful and list width, from the last draw.
    page: usize,
    width: u16,
    root_exists: bool,
    flash: Option<String>,
    dirty: bool,
    theme: Theme,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<ClaudeHistory> {
    let root = projects_dir();
    let mut s = ClaudeHistory::new(list_sessions(&root), ctx.theme);
    s.root_exists = root.is_dir();
    Ok(s)
}

impl ClaudeHistory {
    fn new(sessions: Vec<Session>, theme: Theme) -> Self {
        let mut s = Self {
            sessions,
            parsed: 0,
            shown: Vec::new(),
            query: String::new(),
            filtering: false,
            state: ListState::default(),
            page: 10,
            width: 80,
            root_exists: true,
            flash: None,
            dirty: true,
            theme,
        };
        s.refilter();
        s
    }

    fn selected_session(&self) -> Option<usize> {
        self.state.selected().and_then(|p| self.shown.get(p)).copied()
    }

    /// Recompute `shown`, keeping the cursor on the same session when it still matches.
    fn refilter(&mut self) {
        let keep = self.selected_session();
        let q = self.query.to_lowercase();
        self.shown = (0..self.sessions.len())
            .filter(|&i| self.sessions[i].matches(&q))
            .collect();
        let pos = keep
            .and_then(|si| self.shown.iter().position(|&x| x == si))
            .unwrap_or(0);
        self.state.select((!self.shown.is_empty()).then_some(pos));
    }

    fn step(&mut self, delta: isize) {
        let n = self.shown.len();
        if n == 0 {
            return;
        }
        let cur = self.state.selected().unwrap_or(0) as isize;
        self.state.select(Some((cur + delta).clamp(0, n as isize - 1) as usize));
    }

    fn jump(&mut self, pos: usize) {
        let n = self.shown.len();
        if n > 0 {
            self.state.select(Some(pos.min(n - 1)));
        }
    }

    fn resume(&mut self) {
        let Some(i) = self.selected_session() else {
            return;
        };
        if std::env::var_os("TMUX").is_none() {
            self.flash = Some("needs tmux".into());
            return;
        }
        let session = &self.sessions[i];
        if !valid_session_id(&session.id) {
            self.flash = Some("bad session id".into());
            return;
        }
        self.flash = Some(match Command::new("tmux").args(tmux_args(session)).output() {
            Ok(out) if out.status.success() => "resumed in a new tmux window".into(),
            Ok(out) => format!("tmux: {}", String::from_utf8_lossy(&out.stderr).trim()),
            Err(e) => format!("tmux: {e}"),
        });
    }

    fn on_filter_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => {
                self.filtering = false;
                self.query.clear();
                self.refilter();
            }
            KeyCode::Enter => self.filtering = false,
            KeyCode::Backspace => {
                self.query.pop();
                self.refilter();
            }
            KeyCode::Char('u') if ctrl => {
                self.query.clear();
                self.refilter();
            }
            KeyCode::Char(c) if !key.modifiers.intersects(KeyModifiers::CONTROL | KeyModifiers::ALT) => {
                self.query.push(c);
                self.refilter();
            }
            KeyCode::Down => self.step(1),
            KeyCode::Up => self.step(-1),
            _ => {}
        }
        Action::None
    }

    fn row(&self, s: &Session) -> Line<'static> {
        let t = self.theme;
        let date = DateTime::<Local>::from(s.modified).format(DATE_FMT).to_string();
        let prompt = if !s.parsed {
            "…".to_string()
        } else if s.prompt.is_empty() {
            "(no prompt)".to_string()
        } else {
            s.prompt.clone()
        };
        let prompt_w = (self.width as usize).saturating_sub(date.len() + 2 + PROJECT_COL + 2);
        Line::from(vec![
            Span::styled(format!("{date}  "), t.dim()),
            Span::styled(text::fit(&s.project_label(), PROJECT_COL, false), t.accent()),
            Span::styled(format!("  {}", text::fit(&prompt, prompt_w, false)), t.base()),
        ])
    }

}

impl Screen for ClaudeHistory {
    fn draw(&mut self, frame: &mut Frame) {
        self.dirty = false;
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [title, filter, list_area, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);
        self.page = list_area.height.max(1) as usize;
        self.width = list_area.width;

        let total = self.sessions.len();
        let mut head = vec![Span::styled("Claude history", t.accent().add_modifier(Modifier::BOLD))];
        head.push(Span::styled(format!("  {} of {total}", self.shown.len()), t.dim()));
        if self.parsed < total {
            head.push(Span::styled(format!("  reading {}/{total}", self.parsed), t.dim()));
        }
        if !self.root_exists {
            head.push(Span::styled("  no ~/.claude/projects", t.dim()));
        }
        frame.render_widget(Paragraph::new(Line::from(head)), title);

        let filter_line = if self.filtering {
            Line::from(vec![
                Span::styled("/ ", t.accent()),
                Span::styled(format!("{}█", self.query), t.base()),
            ])
        } else if !self.query.is_empty() {
            Line::from(Span::styled(format!("/ {}", self.query), t.dim()))
        } else {
            Line::from(Span::styled("/ to filter", t.dim()))
        };
        frame.render_widget(Paragraph::new(filter_line), filter);

        if self.shown.is_empty() {
            let msg = if self.sessions.is_empty() {
                "no Claude sessions found"
            } else {
                "no matches"
            };
            frame.render_widget(Paragraph::new(Span::styled(msg, t.dim())), list_area);
        } else {
            let items: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| ListItem::new(self.row(&self.sessions[i])))
                .collect();
            let list = List::new(items).highlight_style(t.selected());
            frame.render_stateful_widget(list, list_area, &mut self.state);
        }

        let hint = "/ filter · j/k move · ^d/^u page · ↵ resume in tmux · esc back";
        let left = match (&self.flash, self.selected_session()) {
            (Some(f), _) => Span::styled(f.clone(), t.accent()),
            (None, Some(i)) => {
                let s = &self.sessions[i];
                let cwd = if s.cwd.is_empty() { s.project_dir.clone() } else { tilde(&s.cwd) };
                Span::styled(cwd, t.dim())
            }
            (None, None) => Span::styled("", t.dim()),
        };
        let line = Line::from(vec![left, Span::styled(format!("  ·  {hint}"), t.dim())]);
        frame.render_widget(Paragraph::new(line), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        if self.filtering {
            return self.on_filter_key(key);
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let half = (self.page / 2).max(1) as isize;
        let last = self.shown.len().saturating_sub(1);
        if key.code == KeyCode::Esc || (key.code == KeyCode::Char('q') && !ctrl) {
            return Action::Quit;
        }
        match key.code {
            KeyCode::Char('/') if !ctrl => self.filtering = true,
            KeyCode::Char('j') | KeyCode::Down if !ctrl => self.step(1),
            KeyCode::Char('k') | KeyCode::Up if !ctrl => self.step(-1),
            KeyCode::Char('d') if ctrl => self.step(half),
            KeyCode::Char('u') if ctrl => self.step(-half),
            KeyCode::Char('g') | KeyCode::Home if !ctrl => self.jump(0),
            KeyCode::Char('G') | KeyCode::End => self.jump(last),
            KeyCode::Enter => self.resume(),
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        if self.parsed < self.sessions.len() {
            let end = (self.parsed + PARSE_BATCH).min(self.sessions.len());
            for s in &mut self.sessions[self.parsed..end] {
                s.load();
            }
            self.parsed = end;
            if !self.query.is_empty() {
                self.refilter();
            }
            self.dirty = true;
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.dirty
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
        self.dirty = true;
    }

    fn leader_ok(&self) -> bool {
        !self.filtering
    }
}

#[cfg(test)]
mod tests {
    use std::fs;

    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn key(code: KeyCode) -> KeyEvent {
        KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        }
    }

    fn sess(id: &str, cwd: &str, prompt: &str) -> Session {
        Session {
            id: id.into(),
            path: PathBuf::from(format!("/nonexistent/{id}.jsonl")),
            project_dir: "-enc".into(),
            modified: SystemTime::UNIX_EPOCH,
            cwd: cwd.into(),
            prompt: prompt.into(),
            parsed: true,
        }
    }

    fn screen(sessions: Vec<Session>) -> ClaudeHistory {
        ClaudeHistory::new(sessions, Theme::from_args(None, None, None))
    }

    #[test]
    fn header_takes_first_cwd_and_first_typed_prompt() {
        let lines = [
            r#"{"type":"attachment","attachment":{"type":"hook_success"}}"#,
            r#"{"type":"user","isMeta":true,"cwd":"/a/meta","message":{"role":"user","content":"caveat"}}"#,
            r#"{"type":"user","cwd":"/a/proj","message":{"role":"user","content":[{"type":"tool_result","content":"x"}]}}"#,
            r#"{"type":"user","cwd":"/a/proj","message":{"role":"user","content":"  fix   the\nbug "}}"#,
            r#"{"type":"user","cwd":"/a/other","message":{"role":"user","content":"second"}}"#,
        ];
        let (cwd, prompt) = parse_header(lines.iter().map(|s| s.to_string()));
        assert_eq!(cwd, "/a/meta");
        assert_eq!(prompt, "fix the bug");
    }

    #[test]
    fn header_skips_command_wrappers_and_garbage() {
        let lines = [
            "not json",
            r#"{"type":"user","message":{"content":"<command-name>/clear</command-name>"}}"#,
            r#"{"type":"user","message":{"content":[{"type":"text","text":"real one"}]}}"#,
        ];
        let (cwd, prompt) = parse_header(lines.iter().map(|s| s.to_string()));
        assert_eq!(cwd, "");
        assert_eq!(prompt, "real one");
    }

    #[test]
    fn list_takes_top_level_jsonl_newest_first() {
        let root = std::env::temp_dir().join(format!("claude_history_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        let proj = root.join("-enc-proj");
        fs::create_dir_all(proj.join("sub")).unwrap();
        let old = proj.join("old.jsonl");
        let new = proj.join("new.jsonl");
        fs::write(&old, "").unwrap();
        fs::write(&new, "").unwrap();
        fs::write(proj.join("sub").join("nested.jsonl"), "").unwrap();
        fs::write(proj.join("notes.txt"), "").unwrap();
        let t0 = SystemTime::UNIX_EPOCH + std::time::Duration::from_secs(1_000);
        fs::File::options().write(true).open(&old).unwrap().set_modified(t0).unwrap();
        fs::File::options()
            .write(true)
            .open(&new)
            .unwrap()
            .set_modified(t0 + std::time::Duration::from_secs(10))
            .unwrap();

        let sessions = list_sessions(&root);
        let ids: Vec<&str> = sessions.iter().map(|s| s.id.as_str()).collect();
        assert_eq!(ids, vec!["new", "old"]);
        assert_eq!(sessions[0].project_dir, "-enc-proj");
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn filter_matches_cwd_and_prompt_case_insensitively() {
        let s = sess("a", "/x/FinLarp", "plot the chart");
        assert!(s.matches(""));
        assert!(s.matches("finlarp"));
        assert!(s.matches("chart"));
        assert!(!s.matches("godel"));
        let mut unparsed = sess("b", "", "");
        unparsed.parsed = false;
        assert!(unparsed.matches(""));
        assert!(!unparsed.matches("x"));
    }

    #[test]
    fn filter_keys_narrow_and_keep_cursor_on_same_session() {
        let mut s = screen(vec![
            sess("1", "/p/alpha", "one"),
            sess("2", "/p/beta", "two"),
            sess("3", "/p/alpha", "three"),
        ]);
        s.on_key(key(KeyCode::Char('j')));
        assert_eq!(s.selected_session(), Some(1));
        s.on_key(key(KeyCode::Char('/')));
        assert!(!s.leader_ok());
        for c in "alpha".chars() {
            s.on_key(key(KeyCode::Char(c)));
        }
        assert_eq!(s.shown, vec![0, 2]);
        assert_eq!(s.selected_session(), Some(0));
        s.on_key(key(KeyCode::Esc));
        assert_eq!(s.shown.len(), 3);
        assert!(s.leader_ok());
    }

    #[test]
    fn esc_q_quit_and_gg_jump() {
        let mut s = screen(vec![sess("1", "/a", "x"), sess("2", "/b", "y"), sess("3", "/c", "z")]);
        assert_eq!(s.on_key(key(KeyCode::Char('G'))), Action::None);
        assert_eq!(s.selected_session(), Some(2));
        s.on_key(key(KeyCode::Char('g')));
        assert_eq!(s.selected_session(), Some(0));
        assert_eq!(s.on_key(key(KeyCode::Esc)), Action::Quit);
        assert_eq!(s.on_key(key(KeyCode::Char('q'))), Action::Quit);
    }

    #[test]
    fn resume_args_use_cwd_and_quoted_safe_id() {
        let s = sess("0123-abcd", "/code/finlarp", "x");
        assert_eq!(
            tmux_args(&s),
            vec!["new-window", "-c", "/code/finlarp", "claude --resume 0123-abcd"]
        );
        assert!(valid_session_id("0123-abcd"));
        assert!(!valid_session_id("a;rm -rf"));
        assert!(!valid_session_id(""));
    }

    #[test]
    fn enter_without_tmux_flashes_needs_tmux() {
        if std::env::var_os("TMUX").is_some() {
            return; // only meaningful outside tmux
        }
        let mut s = screen(vec![sess("1", "/a", "x")]);
        s.on_key(key(KeyCode::Enter));
        assert_eq!(s.flash.as_deref(), Some("needs tmux"));
    }

    #[test]
    fn draws_rows_and_placeholder() {
        let mut s = screen(vec![sess("1", "/code/finlarp", "hello there")]);
        let mut term = Terminal::new(TestBackend::new(70, 6)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        let buf = format!("{:?}", term.backend().buffer());
        assert!(buf.contains("finlarp"));
        assert!(buf.contains("hello there"));
    }
}
