// Asking Claude about the diagram that is open, with no chat window: `<space>aw` opens a
// one-line box under the picture, enter sends it, and the answer arrives on the
// diagram itself.
//
// Each question spawns headless `claude -p --output-format stream-json` (resuming one
// session per fl run), with a context block in front: the tab, the node, what is on
// screen, the page's write-up. Claude answers by calling the `diagram` MCP tools
// (diagrams_ipc: `fl diagram-mcp` forwards them to this screen's socket), which the
// screen checks and runs: move to a zoom or a beat, pin notes to parts, ring parts,
// ask the user a question and wait for the key.
//
// This file holds what the tools act on that is not the diagram itself (the notes,
// the rings, the caption, an open quiz), the steps a tool call parses into, and the
// bar under the picture. Words Claude writes outside tool calls show as the caption.

use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{Receiver, channel};
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent};
use ratatui::layout::Rect;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph};
use serde_json::Value;
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::ui::text;
use crate::ui::theme::Theme;

const SYSTEM_PROMPT: &str = r#"You are answering inside the Diagrams screen of finlarp, a terminal UI. The user is looking at an animated diagram of one node (for example LITHO on the Memory tab). There is no chat window: your answer is shown on the diagram itself, by calling the diagram tools. Every message starts with a [diagram] block saying which tab, node and view are open, what the picture shows, and what you can navigate to.

How to answer:
- Go to where the answer is visible: the zoom-in, section or beat that shows the thing asked about (goto, beat, open_node).
- Explain with notes pinned to the parts they are about. A note has a title of one to three words and under 140 characters of text. At most four notes up at once. Ring a part with `point` when you only need to say "look here".
- Pin with exact part names. The [diagram] block lists the names on the picture now; for any other view call `parts` first. A note whose `on` matches nothing is rejected with the valid names: fix it and retry.
- Anything with steps is a walk-through. Send it as ONE `sequence` call: note, wait 3000-5000 ms, remove_note or the next beat, the next note. Several short steps, never one crowded picture. Finish with the notes that sum it up left on screen.
- Start by clearing what no longer applies (the [diagram] block lists the notes that are up).
- When the user asks to be quizzed or tested, or says "quiz me": use `ask` (multiple choice) and `ask_part` (pick the part on the picture; hide the names first with `labels`). Have them predict before you play a beat, then play it and say whether they were right. Two to four questions, then show the labels again.
- Views without a picture (the menu, a section's text) show no notes: go to the overview or a zoom-in.
- Words you write outside tool calls appear as one caption line under the picture. End with one short plain sentence that sums up the answer; write nothing else. No markdown. Never mention the tools or the [diagram] block.
- When the user asks you to change the diagram itself (its words, labels, numbers, notes, or the picture), edit the source with Edit or Write, the same as any Claude Code session. The write-ups are in tui/src/screens/diagrams_pages/*.txt and diagrams_desc.rs; the scenes and nodes are the diagrams_*.rs files under tui/src/screens and the rigs under tools/poly3d/src. Then run `cargo build --release` in tui/ (Bash is allowed for cargo) and fix any error. Changes show after the next start of fl. The caption says in one plain sentence what changed.
- Do not edit anything for a question. Edit only what the user asked to change."#;

/// What the headless Claude may use: the diagram and finlarp tools, reading, and (for
/// editing a diagram) Edit, Write and cargo. Anything else is refused, not prompted.
const ALLOWED_TOOLS: &str =
    "mcp__diagram__*,mcp__finlarp__*,Read,Grep,Glob,Edit,Write,Bash(cargo:*)";

/// One box Claude has put on the picture.
#[derive(Clone, Debug, PartialEq)]
pub struct Note {
    pub id: String,
    pub title: String,
    pub text: String,
    pub on: Option<String>,
}

/// Where a `goto` leads inside the open node.
#[derive(Clone, Debug, PartialEq)]
pub enum Target {
    Zoom(char),
    /// 1-based, as the menu numbers them.
    Section(usize),
    Overview,
    Menu,
}

/// One thing a tool call does to the picture. A `sequence` is a list of these.
#[derive(Clone, Debug, PartialEq)]
pub enum Step {
    Open(String),
    Goto(Target),
    /// 1-based beat to hold on.
    Beat(usize),
    Play,
    Pause,
    Camera {
        yaw: f64,
        pitch: f64,
        zoom: f64,
        reset: bool,
    },
    Note(Note),
    Unnote(String),
    Clear,
    Point(Vec<String>),
    Caption(String),
    Labels(bool),
    Wait(u64),
}

/// Longest wait one step can ask for.
pub const MAX_WAIT_MS: u64 = 10_000;
/// Most notes on the picture at once.
pub const MAX_NOTES: usize = 4;

/// Reads a tool call (or a sequence step) into a `Step`, or says what is wrong with it.
pub fn parse_step(tool: &str, a: &Value) -> Result<Step, String> {
    let s = |k: &str| {
        a[k].as_str()
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .map(str::to_string)
    };
    let need = |k: &str| s(k).ok_or_else(|| format!("{tool}: \"{k}\" is required"));
    match tool {
        "open_node" => Ok(Step::Open(need("node")?)),
        "goto" => {
            let mut found = Vec::new();
            if let Some(z) = s("zoom") {
                let mut cs = z.chars();
                match (cs.next(), cs.next()) {
                    (Some(c), None) => found.push(Target::Zoom(c.to_ascii_lowercase())),
                    _ => return Err(format!("goto: zoom is one letter, got {z:?}")),
                }
            }
            if !a["section"].is_null() {
                match a["section"].as_u64().filter(|n| *n >= 1) {
                    Some(n) => found.push(Target::Section(n as usize)),
                    None => return Err("goto: section is a number from 1".into()),
                }
            }
            if a["overview"] == true {
                found.push(Target::Overview);
            }
            if a["menu"] == true {
                found.push(Target::Menu);
            }
            match found.len() {
                1 => Ok(Step::Goto(found.remove(0))),
                0 => Err("goto: give one of zoom, section, overview: true, menu: true".into()),
                _ => Err("goto: give only one of zoom, section, overview, menu".into()),
            }
        }
        "beat" => a["n"]
            .as_u64()
            .filter(|n| *n >= 1)
            .map(|n| Step::Beat(n as usize))
            .ok_or_else(|| "beat: n is a number from 1".into()),
        "play" => Ok(Step::Play),
        "pause" => Ok(Step::Pause),
        "camera" => {
            let step = Step::Camera {
                yaw: a["yaw"].as_f64().unwrap_or(0.0).clamp(-360.0, 360.0),
                pitch: a["pitch"].as_f64().unwrap_or(0.0).clamp(-90.0, 90.0),
                zoom: a["zoom"].as_f64().unwrap_or(1.0).clamp(0.3, 4.0),
                reset: a["reset"] == true,
            };
            if step
                == (Step::Camera {
                    yaw: 0.0,
                    pitch: 0.0,
                    zoom: 1.0,
                    reset: false,
                })
            {
                return Err("camera: give yaw, pitch, zoom or reset: true".into());
            }
            Ok(step)
        }
        "note" => {
            let text = need("text")?;
            if text.chars().count() > 200 {
                return Err("note: text is over 200 characters; split it into steps".into());
            }
            Ok(Step::Note(Note {
                id: need("id")?,
                title: s("title").unwrap_or_default(),
                text,
                on: s("on"),
            }))
        }
        "remove_note" => Ok(Step::Unnote(need("id")?)),
        "clear" => Ok(Step::Clear),
        "point" => match a["parts"].as_array() {
            Some(list) => Ok(Step::Point(
                list.iter()
                    .filter_map(|p| p.as_str())
                    .map(|p| p.trim().to_string())
                    .filter(|p| !p.is_empty())
                    .collect(),
            )),
            None => Err("point: parts is a list of part names".into()),
        },
        "caption" => Ok(Step::Caption(
            a["text"].as_str().unwrap_or("").trim().to_string(),
        )),
        "labels" => a["show"]
            .as_bool()
            .map(Step::Labels)
            .ok_or_else(|| "labels: show is true or false".into()),
        "wait" => a["ms"]
            .as_u64()
            .filter(|ms| *ms > 0)
            .map(|ms| Step::Wait(ms.min(MAX_WAIT_MS)))
            .ok_or_else(|| "wait: ms is a number of milliseconds".into()),
        other => Err(format!("{other} is not a step")),
    }
}

/// A question the user is answering under the picture.
#[derive(Clone, Debug, PartialEq)]
pub enum Quiz {
    /// Pick a letter.
    Choice {
        question: String,
        choices: Vec<String>,
    },
    /// Move the ring to a part and press enter.
    Part {
        question: String,
        names: Vec<String>,
        cur: usize,
    },
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

pub struct Chat {
    input: Input,
    /// The ask box is open and takes the keys.
    pub focus: bool,
    session: Option<String>,
    rx: Option<Receiver<Ev>>,
    child: Option<Child>,
    /// The caption under the picture: Claude's words, a `caption` call, or an error.
    say: String,
    failed: bool,
    /// What Claude is doing while no words have come yet ("thinking", a tool's name).
    status: String,
    /// The assistant message that is streaming in.
    raw: String,
    notes: Vec<Note>,
    /// Parts ringed on the picture.
    marks: Vec<String>,
    /// The question the user is being asked, if any.
    pub quiz: Option<Quiz>,
    /// A line above everything else in the bar (the demo's "3/24 · question").
    pub banner: String,
    /// A line the screen is collecting input on (the demo's rating), with what is typed.
    pub prompt: Option<(String, String)>,
    /// A `j` just typed: `k` right after it closes the box (jk, as in the Claude popup).
    last_j: Option<Instant>,
    /// Something changed since the last draw.
    dirty: bool,
    /// The node whose write-up the session has already been sent.
    pub sent_page: Option<String>,
}

/// How soon `k` must follow `j` to count as `jk`.
const JK: Duration = Duration::from_millis(250);

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
    pub fn new() -> Self {
        Self {
            input: Input::default(),
            focus: false,
            session: None,
            rx: None,
            child: None,
            say: String::new(),
            failed: false,
            status: String::new(),
            raw: String::new(),
            notes: Vec::new(),
            marks: Vec::new(),
            quiz: None,
            banner: String::new(),
            prompt: None,
            last_j: None,
            dirty: false,
            sent_page: None,
        }
    }

    pub fn busy(&self) -> bool {
        self.rx.is_some()
    }

    /// The bar needs drawing again without a key having been pressed.
    pub fn wants_redraw(&self) -> bool {
        self.busy() || self.dirty
    }

    pub fn notes(&self) -> &[Note] {
        &self.notes
    }

    pub fn marks(&self) -> &[String] {
        &self.marks
    }

    pub fn caption(&self) -> &str {
        &self.say
    }

    /// The caption is an error: the last question got no answer.
    pub fn failed(&self) -> bool {
        self.failed
    }

    /// Adds a note, or replaces the one with its id.
    pub fn set_note(&mut self, note: Note) {
        match self.notes.iter_mut().find(|n| n.id == note.id) {
            Some(n) => *n = note,
            None => self.notes.push(note),
        }
    }

    /// Takes one note off; false if none had that id.
    pub fn remove_note(&mut self, id: &str) -> bool {
        let before = self.notes.len();
        self.notes.retain(|n| n.id != id);
        self.notes.len() != before
    }

    pub fn set_marks(&mut self, parts: Vec<String>) {
        self.marks = parts;
    }

    pub fn set_caption(&mut self, text: String) {
        self.say = text;
        self.failed = false;
        self.dirty = true;
    }

    /// Takes every note, ring and the caption off; true if anything was up.
    pub fn clear_notes(&mut self) -> bool {
        let had = !self.notes.is_empty() || !self.say.is_empty() || !self.marks.is_empty();
        self.notes.clear();
        self.marks.clear();
        self.say.clear();
        self.failed = false;
        had
    }

    /// A key while the ask box has the focus. Returns the question to send, if enter sent one.
    pub fn key(&mut self, key: KeyEvent) -> Option<String> {
        let now = Instant::now();
        let jk = key.code == KeyCode::Char('k')
            && self.last_j.is_some_and(|at| now.duration_since(at) < JK)
            && self.input.value().ends_with('j');
        self.last_j = (key.code == KeyCode::Char('j')).then_some(now);
        if jk {
            let kept: String = {
                let v = self.input.value();
                v[..v.len() - 1].to_string()
            };
            self.input = Input::new(kept);
            self.focus = false;
            return None;
        }
        match key.code {
            KeyCode::Esc => self.focus = false,
            KeyCode::Enter => {
                let q = self.input.value().trim().to_string();
                if q.is_empty() {
                    return None;
                }
                self.input.reset();
                // the box closes: the answer comes on the picture
                self.focus = false;
                return Some(q);
            }
            _ => {
                self.input.handle_event(&Event::Key(key));
            }
        }
        None
    }

    /// Asks `question`, with `context` (the [diagram] block) in front of it for Claude.
    /// `sock` is the screen's socket, which the diagram tools reach it on.
    pub fn send(&mut self, question: &str, context: &str, sock: &Path) {
        // a new question drops an answer still on its way
        self.cancel();
        self.say.clear();
        self.failed = false;
        self.status = "thinking".to_string();
        self.raw.clear();
        let prompt = format!("{context}\n\n{question}");
        let exe = std::env::current_exe()
            .map(|p| p.to_string_lossy().into_owned())
            .unwrap_or_else(|_| "fl".to_string());
        let mcp = serde_json::json!({
            "mcpServers": {
                "diagram": {
                    "command": exe,
                    "args": ["diagram-mcp"],
                    "env": { super::diagrams_ipc::SOCK_ENV: sock.to_string_lossy() },
                }
            }
        })
        .to_string();
        let mut cmd = Command::new("claude");
        cmd.args([
            "-p",
            &prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--mcp-config",
            &mcp,
            "--allowedTools",
            ALLOWED_TOOLS,
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
                self.fail(format!("can't run claude: {e}"));
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

    /// Stops an answer that is still coming.
    pub fn cancel(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
        self.rx = None;
        self.status.clear();
    }

    pub fn fail(&mut self, msg: String) {
        self.say = msg;
        self.failed = true;
        self.status.clear();
        self.dirty = true;
    }

    /// Takes in what has streamed since the last call.
    pub fn tick(&mut self) {
        let mut evs = Vec::new();
        if let Some(rx) = &self.rx {
            while let Ok(ev) = rx.try_recv() {
                evs.push(ev);
            }
        }
        for ev in evs {
            self.dirty = true;
            self.apply(ev);
        }
    }

    fn apply(&mut self, ev: Ev) {
        match ev {
            Ev::Session(s) => self.session = Some(s),
            Ev::Message => self.raw.clear(),
            Ev::Text(t) => {
                self.raw.push_str(&t);
                let shown = self.raw.split_whitespace().collect::<Vec<_>>().join(" ");
                if !shown.is_empty() {
                    self.say = shown;
                    self.failed = false;
                }
            }
            Ev::Tool(n) => {
                self.status = n.rsplit("__").next().unwrap_or(&n).replace('_', " ");
            }
            Ev::Failed(m) => self.fail(m),
            Ev::Done => {
                if let Some(mut c) = self.child.take() {
                    let _ = c.wait();
                }
                self.rx = None;
                self.status.clear();
            }
        }
    }

    /// The bar's rows, top to bottom, wrapped to `w`.
    fn rows(&self, w: usize, t: &Theme) -> Vec<Line<'static>> {
        let w = w.max(10);
        let mut lines: Vec<Line> = Vec::new();
        if !self.banner.is_empty() {
            for l in text::wrap(&self.banner, w).into_iter().take(2) {
                lines.push(Line::styled(l, t.accent()));
            }
        }
        if !self.say.is_empty() {
            let style = if self.failed { t.down() } else { t.base() };
            let wrapped = text::wrap(&self.say, w);
            // the end of a long caption is the newest part: keep that
            let skip = wrapped.len().saturating_sub(4);
            lines.extend(
                wrapped
                    .into_iter()
                    .skip(skip)
                    .map(|l| Line::styled(l, style)),
            );
        } else if self.busy() && self.quiz.is_none() {
            lines.push(Line::styled(format!("\u{2026} {}", self.status), t.dim()));
        }
        match &self.quiz {
            Some(Quiz::Choice { question, choices }) => {
                for l in text::wrap(question, w) {
                    lines.push(Line::styled(l, t.title()));
                }
                for (i, c) in choices.iter().enumerate() {
                    let key = (b'a' + i as u8) as char;
                    lines.push(Line::from(vec![
                        Span::styled(format!(" [{key}] "), t.accent()),
                        Span::styled(c.clone(), t.base()),
                    ]));
                }
            }
            Some(Quiz::Part {
                question,
                names,
                cur,
            }) => {
                for l in text::wrap(question, w) {
                    lines.push(Line::styled(l, t.title()));
                }
                lines.push(Line::styled(
                    format!(
                        " the ring is on part {} of {}: h/l moves it, enter picks",
                        cur + 1,
                        names.len()
                    ),
                    t.dim(),
                ));
            }
            None => {}
        }
        if let Some((ask, typed)) = &self.prompt {
            lines.push(Line::from(vec![
                Span::styled(format!("{ask} "), t.accent()),
                Span::styled(format!("{typed}\u{2581}"), t.base()),
            ]));
        }
        lines
    }

    /// Rows the bar under the picture needs at `width`: none when there is nothing to
    /// ask, say or wait for.
    pub fn bar_height(&self, width: u16, t: &Theme) -> u16 {
        let w = width.saturating_sub(4) as usize;
        let rows = self.rows(w, t).len() + usize::from(self.focus);
        if rows == 0 { 0 } else { rows as u16 + 2 }
    }

    /// The bar under the picture: the caption (or what Claude is doing), a quiz, and
    /// the ask box while it is open.
    pub fn draw(&mut self, frame: &mut Frame, r: Rect, t: &Theme) {
        self.dirty = false;
        if r.height < 3 || r.width < 12 {
            return;
        }
        frame.render_widget(Clear, r);
        let asking = self.focus || self.quiz.is_some() || self.prompt.is_some();
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(if asking { t.accent() } else { t.border() })
            .title(Span::styled(" claude ", t.title()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(block, r);
        let w = inner.width as usize;
        let mut lines = self.rows(w, t);
        // when the bar is short of rows, the newest (lowest) ones stay
        let room = (inner.height as usize).saturating_sub(usize::from(self.focus));
        if lines.len() > room {
            lines.drain(..lines.len() - room);
        }
        let mut cursor = None;
        if self.focus {
            // a long question shows its end, where the typing is
            let typed = self.input.value();
            let room = w.saturating_sub(3);
            let from = typed
                .char_indices()
                .rev()
                .nth(room.saturating_sub(1))
                .map_or(0, |(i, _)| i);
            let shown = &typed[from..];
            cursor = Some((
                inner.x + (2 + text::width(shown)).min(w.saturating_sub(1)) as u16,
                inner.y + lines.len() as u16,
            ));
            lines.push(Line::from(vec![
                Span::styled("\u{203A} ", t.accent()),
                Span::styled(shown.to_string(), t.base()),
            ]));
        }
        frame.render_widget(Paragraph::new(lines).style(t.base()), inner);
        // drawn after the text so it lands on top of it
        if let Some((x, y)) = cursor {
            super::diagrams_window::block_cursor(frame, x, y);
        }
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
    use ratatui::crossterm::event::KeyModifiers;
    use serde_json::json;

    #[test]
    fn the_chat_may_edit_diagrams() {
        for tool in ["Edit", "Write", "Bash(cargo:*)", "mcp__diagram__*"] {
            assert!(
                ALLOWED_TOOLS.split(',').any(|t| t == tool),
                "{tool} missing"
            );
        }
    }

    #[test]
    fn tool_calls_parse_into_steps() {
        assert_eq!(
            parse_step("goto", &json!({"zoom": "B"})),
            Ok(Step::Goto(Target::Zoom('b')))
        );
        assert_eq!(
            parse_step("goto", &json!({"section": 4})),
            Ok(Step::Goto(Target::Section(4)))
        );
        assert_eq!(
            parse_step("goto", &json!({"overview": true})),
            Ok(Step::Goto(Target::Overview))
        );
        assert_eq!(parse_step("beat", &json!({"n": 3})), Ok(Step::Beat(3)));
        assert_eq!(
            parse_step("wait", &json!({"ms": 999999})),
            Ok(Step::Wait(MAX_WAIT_MS))
        );
        assert_eq!(
            parse_step("point", &json!({"parts": ["lens", " "]})),
            Ok(Step::Point(vec!["lens".into()]))
        );
        assert_eq!(
            parse_step(
                "note",
                &json!({"id": "a", "on": "lens", "text": "one", "title": "NA"})
            ),
            Ok(Step::Note(Note {
                id: "a".into(),
                title: "NA".into(),
                text: "one".into(),
                on: Some("lens".into()),
            }))
        );
    }

    #[test]
    fn bad_calls_say_what_is_wrong() {
        for (tool, args, want) in [
            ("goto", json!({}), "give one of"),
            ("goto", json!({"zoom": "b", "section": 2}), "only one"),
            ("goto", json!({"zoom": "bb"}), "one letter"),
            ("beat", json!({"n": 0}), "from 1"),
            ("note", json!({"id": "a"}), "\"text\" is required"),
            ("note", json!({"text": "x"}), "\"id\" is required"),
            ("camera", json!({}), "give yaw"),
            ("labels", json!({}), "true or false"),
            ("fly", json!({}), "not a step"),
        ] {
            let err = parse_step(tool, &args).unwrap_err();
            assert!(err.contains(want), "{tool} {args}: {err}");
        }
    }

    #[test]
    fn notes_are_added_replaced_and_removed_by_id() {
        let mut c = Chat::new();
        let note = |id: &str, text: &str| Note {
            id: id.into(),
            title: String::new(),
            text: text.into(),
            on: None,
        };
        c.set_note(note("a", "one"));
        c.set_note(note("b", "two"));
        c.set_note(note("a", "three"));
        assert_eq!(c.notes().len(), 2);
        assert_eq!(c.notes()[0].text, "three");
        assert!(c.remove_note("b") && !c.remove_note("zz"));
        c.set_marks(vec!["lens".into()]);
        assert!(c.clear_notes());
        assert!(c.notes().is_empty() && c.marks().is_empty());
        assert!(!c.clear_notes());
    }

    #[test]
    fn the_caption_is_the_message_that_is_streaming() {
        let mut c = Chat::new();
        c.apply(Ev::Message);
        c.apply(Ev::Text("Going to".into()));
        c.apply(Ev::Text(" the lens.".into()));
        assert_eq!(c.caption(), "Going to the lens.");
        c.apply(Ev::Tool("mcp__diagram__read_section".into()));
        assert_eq!(c.status, "read section");
        // an empty message after a tool call leaves the caption up
        c.apply(Ev::Message);
        assert_eq!(c.caption(), "Going to the lens.");
        c.apply(Ev::Text("NA sets the finest line.".into()));
        assert_eq!(c.caption(), "NA sets the finest line.");
    }

    #[test]
    fn enter_hands_back_the_question_and_jk_leaves_the_input() {
        let t = Theme::default();
        let mut c = Chat::new();
        c.focus = true;
        let press = |c: &mut Chat, code| c.key(KeyEvent::new(code, KeyModifiers::NONE));
        for ch in "why".chars() {
            assert_eq!(press(&mut c, KeyCode::Char(ch)), None);
        }
        assert_eq!(press(&mut c, KeyCode::Enter), Some("why".to_string()));
        assert_eq!(c.input.value(), "");
        assert!(!c.focus, "sending closes the box");
        assert_eq!(c.bar_height(100, &t), 0, "nothing to show: no bar");
        c.focus = true;
        assert_eq!(c.bar_height(100, &t), 3);
        press(&mut c, KeyCode::Char('a'));
        press(&mut c, KeyCode::Char('j'));
        press(&mut c, KeyCode::Char('k'));
        assert!(!c.focus);
        assert_eq!(c.input.value(), "a");
        // a quiz and a rating prompt take rows of their own
        c.quiz = Some(Quiz::Choice {
            question: "which?".into(),
            choices: vec!["one".into(), "two".into()],
        });
        assert_eq!(c.bar_height(100, &t), 5);
        c.prompt = Some(("rate 1-100:".into(), "8".into()));
        assert_eq!(c.bar_height(100, &t), 6);
    }

    #[test]
    fn parses_stream_events() {
        let evs = parse_line(
            r#"{"type":"stream_event","event":{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"hi"}}}"#,
        );
        assert!(matches!(evs.as_slice(), [Ev::Text(t)] if t == "hi"));
        let evs = parse_line(r#"{"type":"system","subtype":"init","session_id":"abc"}"#);
        assert!(matches!(evs.as_slice(), [Ev::Session(s)] if s == "abc"));
    }
}
