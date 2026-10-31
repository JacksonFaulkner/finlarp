// `fl claude_log`: tail of the Claude background log.
//
// This follows the newest .log in the current project's dir under
// ~/.cache/claude-logs/<project>/ (or the file given as the screen argument).
// The file is re-checked about once a second; new bytes are appended, truncation
// restarts the view.
//
//   Claude log  ~/.cache/claude-logs/finlarp/x.log  ·  following
//
// j/k scroll · ^d/^u page · g top · G follow the end · esc/q back.

use std::collections::VecDeque;
use std::fs::{self, File};
use std::io::{self, Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Wrap};

use crate::app::{Action, Ctx, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

/// Lines kept in memory; the oldest scroll off.
const MAX_LINES: usize = 5_000;
/// On first load, only the last this many bytes are read.
const INITIAL_BYTES: u64 = 256 * 1024;
const CHECK_EVERY: Duration = Duration::from_secs(1);

pub struct ClaudeLog {
    /// Path given as the screen argument; None means "newest log in `dir`".
    explicit: Option<PathBuf>,
    /// ~/.cache/claude-logs/<current project>
    dir: PathBuf,
    path: Option<PathBuf>,
    lines: VecDeque<String>,
    /// Unterminated last line of the file, drawn after `lines`.
    partial: String,
    /// Bytes of `path` consumed so far.
    offset: u64,
    /// The first chunk began mid-file, so its first (partial) line is dropped.
    skip_first: bool,
    error: Option<String>,
    follow: bool,
    /// Top visible line; only meaningful while not following.
    top: usize,
    /// Rows per screenful, from the last draw.
    page: usize,
    last_check: Instant,
    dirty: bool,
    theme: Theme,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<ClaudeLog> {
    let explicit = arg.filter(|a| !a.trim().is_empty()).map(PathBuf::from);
    let mut s = ClaudeLog::new(explicit, log_dir(), ctx.theme);
    s.set_path(s.resolve());
    s.refresh();
    Ok(s)
}

fn home() -> PathBuf {
    std::env::var_os("HOME").map(PathBuf::from).unwrap_or_default()
}

/// Directory of the Claude background logs, keyed by the current project name.
fn log_dir() -> PathBuf {
    let project = std::env::current_dir()
        .ok()
        .and_then(|d| d.file_name().map(|n| n.to_string_lossy().into_owned()))
        .unwrap_or_default();
    home().join(".cache").join("claude-logs").join(project)
}

/// Newest `*.log` directly inside `dir`.
fn newest_log(dir: &Path) -> Option<PathBuf> {
    fs::read_dir(dir)
        .ok()?
        .flatten()
        .filter(|e| e.path().extension().is_some_and(|x| x == "log"))
        .filter_map(|e| {
            let modified = e.metadata().ok()?.modified().ok()?;
            Some((modified, e.path()))
        })
        .max_by_key(|(modified, _)| *modified)
        .map(|(_, path)| path)
}

fn tilde(path: &Path) -> String {
    let p = path.to_string_lossy();
    match std::env::var("HOME") {
        Ok(home) if !home.is_empty() && p.starts_with(&home) => format!("~{}", &p[home.len()..]),
        _ => p.into_owned(),
    }
}

/// Drops ANSI escape sequences and control characters; expands tabs.
fn clean_line(raw: &str) -> String {
    let mut out = String::with_capacity(raw.len());
    let mut chars = raw.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '\x1b' => {
                if chars.peek() == Some(&'[') {
                    chars.next();
                    // CSI: parameter bytes, then a final byte in @..=~
                    for n in chars.by_ref() {
                        if ('@'..='~').contains(&n) {
                            break;
                        }
                    }
                } else {
                    chars.next();
                }
            }
            '\t' => out.push_str("    "),
            c if c.is_control() => {}
            c => out.push(c),
        }
    }
    out
}

impl ClaudeLog {
    fn new(explicit: Option<PathBuf>, dir: PathBuf, theme: Theme) -> Self {
        Self {
            explicit,
            dir,
            path: None,
            lines: VecDeque::new(),
            partial: String::new(),
            offset: 0,
            skip_first: false,
            error: None,
            follow: true,
            top: 0,
            page: 10,
            last_check: Instant::now(),
            dirty: true,
            theme,
        }
    }

    fn resolve(&self) -> Option<PathBuf> {
        match &self.explicit {
            Some(p) => p.is_file().then(|| p.clone()),
            None => newest_log(&self.dir),
        }
    }

    fn set_path(&mut self, path: Option<PathBuf>) {
        if self.path != path {
            self.path = path;
            self.reset();
        }
    }

    fn reset(&mut self) {
        self.lines.clear();
        self.partial.clear();
        self.offset = 0;
        self.skip_first = false;
        self.top = 0;
        self.dirty = true;
    }

    fn total(&self) -> usize {
        self.lines.len() + usize::from(!self.partial.is_empty())
    }

    fn max_top(&self) -> usize {
        self.total().saturating_sub(self.page)
    }

    fn current_top(&self) -> usize {
        if self.follow {
            self.max_top()
        } else {
            self.top.min(self.max_top())
        }
    }

    fn scroll_to(&mut self, top: usize) {
        let max = self.max_top();
        self.top = top.min(max);
        self.follow = self.top == max;
        self.dirty = true;
    }

    /// Reads whatever was appended since the last call. Returns Ok(false) when nothing changed.
    fn sync(&mut self) -> io::Result<bool> {
        let Some(path) = self.path.clone() else {
            return Ok(false);
        };
        let len = fs::metadata(&path)?.len();
        if len < self.offset {
            // truncated or rotated in place: start over
            self.reset();
        }
        if len == self.offset {
            return Ok(false);
        }
        if self.offset == 0 && len > INITIAL_BYTES {
            self.offset = len - INITIAL_BYTES;
            self.skip_first = true;
        }
        let mut file = File::open(&path)?;
        file.seek(SeekFrom::Start(self.offset))?;
        let mut buf = Vec::new();
        file.take(len - self.offset).read_to_end(&mut buf)?;
        self.offset += buf.len() as u64;
        if self.skip_first {
            match buf.iter().position(|&b| b == b'\n') {
                Some(i) => {
                    buf.drain(..=i);
                    self.skip_first = false;
                }
                None => buf.clear(),
            }
        }
        self.push_text(&String::from_utf8_lossy(&buf));
        self.dirty = true;
        Ok(true)
    }

    fn push_text(&mut self, chunk: &str) {
        let text = format!("{}{}", self.partial, chunk);
        let mut parts: Vec<&str> = text.split('\n').collect();
        let tail = parts.pop().unwrap_or("").to_string();
        for p in parts {
            self.lines.push_back(clean_line(p.trim_end_matches('\r')));
        }
        self.partial = clean_line(&tail);
        while self.lines.len() > MAX_LINES {
            self.lines.pop_front();
            self.top = self.top.saturating_sub(1);
        }
    }

    /// Sync and remember any error for the footer.
    fn refresh(&mut self) {
        match self.sync() {
            Ok(_) => self.error = None,
            Err(e) => self.error = Some(e.to_string()),
        }
    }

    fn missing_message(&self) -> String {
        match &self.explicit {
            Some(p) => format!("no log at {}", tilde(p)),
            None if !self.dir.is_dir() => format!("no logs yet: {}", tilde(&self.dir)),
            None => format!("no .log files in {}", tilde(&self.dir)),
        }
    }
}

impl Screen for ClaudeLog {
    fn draw(&mut self, frame: &mut Frame) {
        self.dirty = false;
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);
        self.page = body.height.max(1) as usize;
        let width = body.width as usize;

        let location = match &self.path {
            Some(p) => tilde(p),
            None => "no log".to_string(),
        };
        let mode = if self.follow { "following" } else { "paused · G to follow" };
        let head_line = Line::from(vec![
            Span::styled("Claude log", t.accent()),
            Span::styled(format!("  {location}  ·  {mode}"), t.dim()),
        ]);
        frame.render_widget(Paragraph::new(head_line), head);

        if self.path.is_none() {
            let msg = Paragraph::new(Span::styled(self.missing_message(), t.dim())).wrap(Wrap { trim: false });
            frame.render_widget(msg, body);
        } else if self.total() == 0 {
            frame.render_widget(Paragraph::new(Span::styled("(empty log)", t.dim())), body);
        } else {
            let top = self.current_top();
            let end = (top + self.page).min(self.total());
            let rows: Vec<Line> = (top..end)
                .map(|i| {
                    let s = if i < self.lines.len() {
                        self.lines[i].as_str()
                    } else {
                        self.partial.as_str()
                    };
                    Line::from(Span::styled(text::truncate(s, width), t.base()))
                })
                .collect();
            frame.render_widget(Paragraph::new(rows), body);
        }

        let mut foot_spans = vec![Span::styled(
            format!("{} lines  ·  j/k scroll · ^d/^u page · g top · G follow · esc back", self.total()),
            t.dim(),
        )];
        if let Some(e) = &self.error {
            foot_spans.insert(0, Span::styled(format!("read error: {e}  ·  "), t.accent()));
        }
        frame.render_widget(Paragraph::new(Line::from(foot_spans)), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        if key.code == KeyCode::Esc || (key.code == KeyCode::Char('q') && !ctrl) {
            return Action::Quit;
        }
        let half = (self.page / 2).max(1);
        let cur = self.current_top();
        match key.code {
            KeyCode::Char('j') | KeyCode::Down if !ctrl => self.scroll_to(cur + 1),
            KeyCode::Char('k') | KeyCode::Up if !ctrl => self.scroll_to(cur.saturating_sub(1)),
            KeyCode::Char('d') if ctrl => self.scroll_to(cur + half),
            KeyCode::PageDown => self.scroll_to(cur + half),
            KeyCode::Char('u') if ctrl => self.scroll_to(cur.saturating_sub(half)),
            KeyCode::PageUp => self.scroll_to(cur.saturating_sub(half)),
            KeyCode::Char('g') | KeyCode::Home if !ctrl => self.scroll_to(0),
            KeyCode::Char('G') | KeyCode::End => {
                self.follow = true;
                self.dirty = true;
            }
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        if self.last_check.elapsed() < CHECK_EVERY {
            return Action::None;
        }
        self.last_check = Instant::now();
        // Pick up a log that appeared, or move on when the current one is gone.
        if self.path.as_ref().is_none_or(|p| !p.is_file()) {
            let next = self.resolve();
            self.set_path(next);
        }
        self.refresh();
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.dirty
    }
}

#[cfg(test)]
mod tests {
    use std::io::Write;

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

    fn temp_file(name: &str, contents: &[u8]) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("claude_log_test_{}_{name}", std::process::id()));
        let _ = fs::create_dir_all(&dir);
        let path = dir.join("bg.log");
        fs::write(&path, contents).unwrap();
        path
    }

    fn screen_for(path: &Path) -> ClaudeLog {
        let mut s = ClaudeLog::new(Some(path.to_path_buf()), PathBuf::new(), Theme::from_args(None, None, None));
        s.set_path(s.resolve());
        s.refresh();
        s.page = 3;
        s
    }

    fn all(s: &ClaudeLog) -> Vec<String> {
        let mut v: Vec<String> = s.lines.iter().cloned().collect();
        if !s.partial.is_empty() {
            v.push(s.partial.clone());
        }
        v
    }

    #[test]
    fn clean_line_strips_ansi_and_controls() {
        assert_eq!(clean_line("\x1b[31mred\x1b[0m\tx\r"), "red    x");
        assert_eq!(clean_line("a\x07b"), "ab");
    }

    #[test]
    fn follows_appends_and_holds_partial_lines() {
        let path = temp_file("append", b"one\ntwo\n");
        let mut s = screen_for(&path);
        assert_eq!(all(&s), vec!["one", "two"]);

        let mut f = fs::OpenOptions::new().append(true).open(&path).unwrap();
        f.write_all(b"thr").unwrap();
        drop(f);
        assert!(s.sync().unwrap());
        assert_eq!(all(&s), vec!["one", "two", "thr"]);

        let mut f = fs::OpenOptions::new().append(true).open(&path).unwrap();
        f.write_all(b"ee\r\n").unwrap();
        drop(f);
        s.sync().unwrap();
        assert_eq!(all(&s), vec!["one", "two", "three"]);
        assert!(!s.sync().unwrap());
    }

    #[test]
    fn truncation_restarts_the_view() {
        let path = temp_file("truncate", b"old1\nold2\nold3\n");
        let mut s = screen_for(&path);
        fs::write(&path, b"new\n").unwrap();
        s.sync().unwrap();
        assert_eq!(all(&s), vec!["new"]);
    }

    #[test]
    fn first_load_reads_only_the_tail() {
        let mut body = String::new();
        for i in 0..(INITIAL_BYTES / 8 + 100) {
            body.push_str(&format!("{i:07}\n"));
        }
        let path = temp_file("tail", body.as_bytes());
        let s = screen_for(&path);
        let lines = all(&s);
        assert!(lines.len() < body.lines().count());
        assert_eq!(lines.last().map(String::as_str), body.lines().last());
        assert!(lines[0].len() == 7, "partial first line must be dropped: {:?}", lines[0]);
    }

    #[test]
    fn missing_file_gives_message_and_no_path() {
        let missing = std::env::temp_dir().join("claude_log_definitely_missing.log");
        let s = ClaudeLog::new(Some(missing.clone()), PathBuf::new(), Theme::from_args(None, None, None));
        assert!(s.resolve().is_none());
        assert!(s.missing_message().starts_with("no log at "));
    }

    #[test]
    fn navigation_pauses_and_g_capital_resumes() {
        let path = temp_file("nav", b"1\n2\n3\n4\n5\n");
        let mut s = screen_for(&path);
        assert!(s.follow);
        assert_eq!(s.current_top(), 2);
        s.on_key(key(KeyCode::Char('g')));
        assert!(!s.follow);
        assert_eq!(s.current_top(), 0);
        s.on_key(key(KeyCode::Char('j')));
        assert_eq!(s.current_top(), 1);
        s.on_key(key(KeyCode::Char('G')));
        assert!(s.follow);
        assert_eq!(s.current_top(), 2);
        assert_eq!(s.on_key(key(KeyCode::Char('q'))), Action::Quit);
        assert_eq!(s.on_key(key(KeyCode::Esc)), Action::Quit);
    }

    #[test]
    fn draws_tail_when_following() {
        let path = temp_file("draw", b"alpha\nbeta\ngamma\ndelta\n");
        let mut s = screen_for(&path);
        let mut term = Terminal::new(TestBackend::new(40, 5)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        let buf = format!("{:?}", term.backend().buffer());
        assert!(buf.contains("delta"));
        assert!(!buf.contains("alpha"));
    }
}
