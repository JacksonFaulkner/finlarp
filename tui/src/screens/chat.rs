// Chat with Claude Code, inside `fl`. Each turn spawns headless
// `claude -p --output-format stream-json --resume <session>` and streams the
// reply into a plain transcript; the finlarp MCP tools run through it exactly
// as in the nvim terminal. What the terminal pane can't do: tickers in the
// reply are selectable, `d` opens the dossier and `c` the CANSLIM card, and
// q/esc there comes back here.
//
//   you › what is moving in memory?
//   MU and SNDK lead ...
//   ⚙ mcp__finlarp__sql
//   tickers: [MU] SNDK WDC         (tab cycles, d dossier, c canslim)
//   › _
//
// Insert: type, ↵ send, esc stop/normal.  Normal: j/k/^d/^u/g/G scroll,
// i or ↵ type, tab/shift-tab ticker, d dossier, c canslim, q back.

use std::collections::HashSet;
use std::io::{self, BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{Receiver, channel};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::db;
use crate::ui::text;
use crate::ui::theme::Theme;

const SYSTEM_PROMPT: &str = "You are answering inside the finlarp terminal UI. \
Refer to stocks by plain uppercase ticker (NVDA, MU) so the UI can link them. \
Prefer the finlarp tools for data and say which source each number came from.";

#[derive(Clone, Copy, PartialEq)]
enum Role {
    User,
    Claude,
    Tool,
    Error,
}

enum Ev {
    Session(String),
    /// A new assistant message began (after a tool call or a fresh turn).
    Message,
    Text(String),
    Tool(String),
    Failed(String),
    Done,
}

#[derive(Clone, Copy, PartialEq)]
enum Mode {
    Insert,
    Normal,
}

pub struct Chat {
    theme: Theme,
    log: Vec<(Role, String)>,
    input: Input,
    mode: Mode,
    session: Option<String>,
    rx: Option<Receiver<Ev>>,
    child: Option<Child>,
    /// Lines scrolled up from the bottom; 0 follows new output.
    scroll: usize,
    known: HashSet<String>,
    tickers: Vec<String>,
    sel: usize,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Chat> {
    let known = load_known(ctx);
    let mut c = Chat {
        theme: ctx.theme,
        log: Vec::new(),
        input: Input::new(arg.unwrap_or_default()),
        mode: Mode::Insert,
        session: None,
        rx: None,
        child: None,
        scroll: 0,
        known,
        tickers: Vec::new(),
        sel: 0,
    };
    if c.log.is_empty() && c.input.value().is_empty() {
        c.log.push((
            Role::Tool,
            "Claude Code, headless. Ask about a ticker; tickers in the reply open with d.".into(),
        ));
    }
    Ok(c)
}

/// Tickers worth linking: the universe plus anything ever traded.
fn load_known(ctx: &Ctx) -> HashSet<String> {
    let mut set = HashSet::new();
    if let Ok(conn) = db::open_read_only(&ctx.db_path) {
        if let Ok(mut st) = conn.prepare("SELECT ticker FROM ai_universe") {
            if let Ok(rows) = st.query_map([], |r| r.get::<_, String>(0)) {
                set.extend(rows.flatten());
            }
        }
    }
    if let Ok(syms) = super::portfolio::traded_symbols(&ctx.db_path) {
        set.extend(syms);
    }
    set
}

/// Uppercase words (optionally `$`-prefixed) that are known tickers, in order
/// of first appearance.
fn find_tickers(s: &str, known: &HashSet<String>) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for w in s.split(|c: char| !(c.is_ascii_alphanumeric() || c == '.' || c == '$')) {
        let w = w.trim_start_matches('$').trim_end_matches('.');
        if (1..=6).contains(&w.len())
            && w.chars().all(|c| c.is_ascii_uppercase() || c == '.')
            && known.contains(w)
            && !out.iter().any(|t| t == w)
        {
            out.push(w.to_string());
        }
    }
    out
}

/// Maps one stream-json line to the events the UI cares about.
fn parse_line(line: &str) -> Vec<Ev> {
    let Ok(v) = serde_json::from_str::<serde_json::Value>(line) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    match v["type"].as_str() {
        Some("system") if v["subtype"] == "init" => {
            if let Some(s) = v["session_id"].as_str() {
                out.push(Ev::Session(s.to_string()));
            }
        }
        Some("stream_event") => {
            let e = &v["event"];
            match e["type"].as_str() {
                Some("message_start") => out.push(Ev::Message),
                Some("content_block_start") if e["content_block"]["type"] == "tool_use" => {
                    if let Some(n) = e["content_block"]["name"].as_str() {
                        out.push(Ev::Tool(n.to_string()));
                    }
                }
                Some("content_block_delta") if e["delta"]["type"] == "text_delta" => {
                    if let Some(t) = e["delta"]["text"].as_str() {
                        out.push(Ev::Text(t.to_string()));
                    }
                }
                _ => {}
            }
        }
        Some("result") => {
            if v["is_error"] == true {
                out.push(Ev::Failed(
                    v["result"].as_str().unwrap_or("claude failed").to_string(),
                ));
            }
        }
        _ => {}
    }
    out
}

impl Chat {
    fn busy(&self) -> bool {
        self.rx.is_some()
    }

    fn send(&mut self) {
        let prompt = self.input.value().trim().to_string();
        if prompt.is_empty() || self.busy() {
            return;
        }
        self.input.reset();
        self.log.push((Role::User, prompt.clone()));
        self.scroll = 0;

        let mut cmd = Command::new("claude");
        cmd.args([
            "-p",
            &prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--allowedTools",
            "mcp__finlarp__*",
            "--append-system-prompt",
            SYSTEM_PROMPT,
        ]);
        if let Some(s) = &self.session {
            cmd.args(["--resume", s]);
        }
        cmd.stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => {
                self.log
                    .push((Role::Error, format!("can't run claude: {e}")));
                return;
            }
        };
        let Some(stdout) = child.stdout.take() else {
            return;
        };
        let (tx, rx) = channel();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines().map_while(Result::ok) {
                for ev in parse_line(&line) {
                    if tx.send(ev).is_err() {
                        return;
                    }
                }
            }
            let _ = tx.send(Ev::Done);
        });
        self.child = Some(child);
        self.rx = Some(rx);
    }

    fn cancel(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
        self.rx = None;
        self.log.push((Role::Tool, "stopped".into()));
    }

    fn apply(&mut self, ev: Ev) {
        match ev {
            Ev::Session(s) => self.session = Some(s),
            Ev::Message => {
                if self.log.last().is_none_or(|(r, _)| *r != Role::Claude) {
                    self.log.push((Role::Claude, String::new()));
                } else if let Some((_, t)) = self.log.last_mut() {
                    if !t.is_empty() {
                        t.push_str("\n\n");
                    }
                }
            }
            Ev::Text(t) => {
                if self.log.last().is_none_or(|(r, _)| *r != Role::Claude) {
                    self.log.push((Role::Claude, String::new()));
                }
                if let Some((_, s)) = self.log.last_mut() {
                    s.push_str(&t);
                }
            }
            Ev::Tool(n) => self.log.push((Role::Tool, format!("⚙ {n}"))),
            Ev::Failed(m) => self.log.push((Role::Error, m)),
            Ev::Done => {
                if let Some(mut c) = self.child.take() {
                    let _ = c.wait();
                }
                self.rx = None;
                self.refresh_tickers();
            }
        }
    }

    /// Tickers from the latest assistant message.
    fn refresh_tickers(&mut self) {
        let last = self
            .log
            .iter()
            .rev()
            .find(|(r, _)| *r == Role::Claude)
            .map(|(_, t)| t.as_str())
            .unwrap_or("");
        self.tickers = find_tickers(last, &self.known);
        self.sel = 0;
    }

    fn open_selected(&self, screen: &str) -> Action {
        match self.tickers.get(self.sel) {
            Some(t) => Action::Nvim(NvimAction::Screen {
                screen: screen.into(),
                arg: Some(t.clone()),
            }),
            None => Action::None,
        }
    }

    fn lines(&self, width: usize) -> Vec<Line<'static>> {
        let t = self.theme;
        let mut out = Vec::new();
        for (role, body) in &self.log {
            let (style, prefix) = match role {
                Role::User => (t.accent(), "you › "),
                Role::Claude => (t.base(), ""),
                Role::Tool => (t.dim(), ""),
                Role::Error => (t.down(), "error: "),
            };
            for (i, l) in text::wrap(&format!("{prefix}{body}"), width.max(10))
                .into_iter()
                .enumerate()
            {
                // only the first line of a user turn carries the accent prefix
                let st = if *role == Role::User && i > 0 {
                    t.base()
                } else {
                    style
                };
                out.push(Line::styled(l, st));
            }
            if *role != Role::Tool {
                out.push(Line::raw(""));
            }
        }
        out
    }
}

impl Screen for Chat {
    fn leader_ok(&self) -> bool {
        self.mode == Mode::Normal
    }

    fn tick(&mut self) -> Action {
        let mut evs = Vec::new();
        if let Some(rx) = &self.rx {
            while let Ok(ev) = rx.try_recv() {
                evs.push(ev);
            }
        }
        for ev in evs {
            self.apply(ev);
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.busy()
    }

    fn claude_context(&self) -> Option<String> {
        self.tickers
            .get(self.sel)
            .map(|t| format!("ticker {t} (finlarp chat)"))
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [body, tick_row, input_row] = Layout::vertical([
            Constraint::Min(1),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let lines = self.lines(body.width.saturating_sub(2) as usize);
        let h = body.height as usize;
        let max_scroll = lines.len().saturating_sub(h);
        self.scroll = self.scroll.min(max_scroll);
        let start = lines.len().saturating_sub(h + self.scroll);
        let shown: Vec<Line> = lines.into_iter().skip(start).take(h).collect();
        frame.render_widget(Paragraph::new(shown), body);

        let mut spans = vec![Span::styled(" tickers: ", t.dim())];
        if self.tickers.is_empty() {
            spans.push(Span::styled("none yet", t.dim()));
        }
        for (i, tk) in self.tickers.iter().enumerate() {
            if i == self.sel {
                spans.push(Span::styled(format!("[{tk}]"), t.selected()));
            } else {
                spans.push(Span::styled(format!(" {tk} "), t.base()));
            }
        }
        let hint = match (self.busy(), self.mode) {
            (true, _) => "  esc stop",
            (_, Mode::Insert) => "  ↵ send · esc normal",
            (_, Mode::Normal) => "  tab pick · d dossier · c canslim · i type · q back",
        };
        spans.push(Span::styled(hint, t.dim()));
        frame.render_widget(Paragraph::new(Line::from(spans)), tick_row);

        let prefix = if self.busy() { " … " } else { " › " };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prefix, t.accent()),
                Span::styled(self.input.value().to_string(), t.base()),
            ])),
            input_row,
        );
        if self.mode == Mode::Insert {
            frame.set_cursor_position((
                input_row.x + (text::width(prefix) + self.input.visual_cursor()) as u16,
                input_row.y,
            ));
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if key.code == KeyCode::Esc && self.busy() {
            self.cancel();
            return Action::None;
        }
        match self.mode {
            Mode::Insert => match key.code {
                KeyCode::Enter => self.send(),
                KeyCode::Esc => self.mode = Mode::Normal,
                _ => {
                    self.input.handle_event(&Event::Key(key));
                }
            },
            Mode::Normal => {
                let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
                    KeyCode::Char('i') | KeyCode::Enter => self.mode = Mode::Insert,
                    KeyCode::Char('j') | KeyCode::Down => {
                        self.scroll = self.scroll.saturating_sub(1)
                    }
                    KeyCode::Char('k') | KeyCode::Up => self.scroll += 1,
                    KeyCode::Char('d') if ctrl => self.scroll = self.scroll.saturating_sub(10),
                    KeyCode::Char('u') if ctrl => self.scroll += 10,
                    KeyCode::Char('g') => self.scroll = usize::MAX / 2,
                    KeyCode::Char('G') => self.scroll = 0,
                    KeyCode::Tab | KeyCode::Char(']') if !self.tickers.is_empty() => {
                        self.sel = (self.sel + 1) % self.tickers.len()
                    }
                    KeyCode::BackTab | KeyCode::Char('[') if !self.tickers.is_empty() => {
                        self.sel = (self.sel + self.tickers.len() - 1) % self.tickers.len()
                    }
                    KeyCode::Char('d') => return self.open_selected("dossier"),
                    KeyCode::Char('c') => return self.open_selected("canslim"),
                    _ => {}
                }
            }
        }
        Action::None
    }
}

impl Drop for Chat {
    fn drop(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn known() -> HashSet<String> {
        ["NVDA", "MU", "BRK.B"]
            .iter()
            .map(|s| s.to_string())
            .collect()
    }

    #[test]
    fn finds_known_tickers_once_in_order() {
        let got = find_tickers(
            "MU beat; $NVDA too. NVDA again, THE and ABC no, BRK.B yes",
            &known(),
        );
        assert_eq!(got, vec!["MU", "NVDA", "BRK.B"]);
    }

    #[test]
    fn parses_stream_events() {
        let t = r#"{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"hi"}}}"#;
        assert!(matches!(parse_line(t).as_slice(), [Ev::Text(s)] if s == "hi"));
        let tool = r#"{"type":"stream_event","event":{"type":"content_block_start","content_block":{"type":"tool_use","name":"mcp__finlarp__sql"}}}"#;
        assert!(matches!(parse_line(tool).as_slice(), [Ev::Tool(s)] if s == "mcp__finlarp__sql"));
        let init = r#"{"type":"system","subtype":"init","session_id":"abc"}"#;
        assert!(matches!(parse_line(init).as_slice(), [Ev::Session(s)] if s == "abc"));
        assert!(parse_line("not json").is_empty());
    }
}
