// `<leader>vm`: browser over every note you've asked. nvim fetches them from
// mind.duckdb (ui/notes.lua) and passes JSON in $FINLARP_NOTES_FILE. Standalone
// (`fl notes`) it reads mind.duckdb itself through py/mind/cli.py index, and
// reloads every few seconds while an answer is still pending.
// Rows are grouped by ticker (A-Z, untagged last), newest first within a group.
//
//   Notes ›  mrvl█
//   ✓ 10-12  MRVL   Custom silicon ramp ...      ●●○  ai-capex
//   ── YOUR NOTE ... ── ANSWER ... (scrollable card)
//
// `fl notes last` shows only the newest answered note.
//
// Type filters (ticker, title, body, themes, entities) · ^n/^p move ·
// ^d/^u scroll card · ↵ reopen the Claude chat · ^f follow-up chips (1-9) ·
// ^o dossier · ^g godel · esc back.
//
// Standalone, ↵ reopens the chat in a new tmux window (`claude --resume`, run
// from the note's cwd) and a follow-up chip saves the follow-up as a new note.

use std::io;
use std::process::Command;
use std::sync::mpsc::{Receiver, TryRecvError};
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph, Wrap};
use serde::{Deserialize, Deserializer};

use super::note::{CLI, Save};
use crate::app::{ACTION_FILE_ENV, Action, Ctx, NvimAction, Screen};
use crate::pyrun;
use crate::ui::text;
use crate::ui::theme::Theme;

pub const NOTES_FILE_ENV: &str = "FINLARP_NOTES_FILE";

/// Standalone: how often pending answers are re-read from mind.duckdb...
const RELOAD_EVERY: Duration = Duration::from_secs(5);
/// ...and for how long after the screen opens or a save lands.
const RELOAD_FOR: Duration = Duration::from_secs(15 * 60);

/// Lua encodes an empty list as `{}`; accept that (and null) as empty.
/// Accepts `null` as the empty string: `#[serde(default)]` only covers a missing field.
fn nullable_str<'de, D: Deserializer<'de>>(d: D) -> Result<String, D::Error> {
    Ok(Option::<String>::deserialize(d)?.unwrap_or_default())
}

fn lenient<'de, D: Deserializer<'de>>(d: D) -> Result<Vec<String>, D::Error> {
    let v = serde_json::Value::deserialize(d)?;
    Ok(match v {
        serde_json::Value::Array(a) => a
            .into_iter()
            .filter_map(|x| x.as_str().map(str::to_string))
            .collect(),
        _ => Vec::new(),
    })
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Answer {
    #[serde(default, deserialize_with = "nullable_str")]
    pub title: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub summary: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub depth: String,
    #[serde(default, deserialize_with = "lenient")]
    pub themes: Vec<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub key_points: Vec<String>,
    #[serde(default, deserialize_with = "nullable_str")]
    pub assumption: String,
    #[serde(default, deserialize_with = "lenient")]
    pub follow_ups: Vec<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub learn: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Note {
    pub id: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub kind: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub body: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub context: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub ts: String,
    #[serde(default, deserialize_with = "nullable_str")]
    pub status: String,
    #[serde(default)]
    pub anchor: Option<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub entities: Vec<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub themes: Vec<String>,
    #[serde(default)]
    pub structured: Option<Answer>,
    #[serde(default)]
    pub error: Option<String>,
    /// Claude session that answered the note (`claude --resume` target).
    #[serde(default)]
    pub session_id: Option<String>,
    /// Working directory that session ran in; `--resume` only finds it from there.
    #[serde(default)]
    pub cwd: Option<String>,
}

impl Note {
    /// Anchor if it is a ticker, else the first linked ticker.
    fn ticker(&self) -> Option<String> {
        self.anchor
            .iter()
            .chain(self.entities.iter())
            .find_map(|e| e.strip_prefix("ticker:").map(str::to_string))
    }

    fn title(&self) -> String {
        match &self.structured {
            Some(a) if !a.title.is_empty() => a.title.clone(),
            _ => self.body.replace(['\n', '\t', '\r'], " "),
        }
    }

    fn depth_glyph(&self) -> &'static str {
        match self.structured.as_ref().map(|a| a.depth.as_str()) {
            Some("definitional") => "●○○",
            Some("causal") => "●●○",
            Some("counterfactual") => "●●●",
            _ => "   ",
        }
    }

    fn status_glyph(&self) -> &'static str {
        match self.status.as_str() {
            "answered" => "✓",
            "pending" => "…",
            "failed" => "✗",
            _ => "?",
        }
    }

    fn haystack(&self) -> String {
        format!(
            "{} {} {} {} {} {}",
            self.ticker().unwrap_or_default(),
            self.title(),
            self.body,
            self.themes.join(" "),
            self.entities.join(" "),
            self.context
        )
        .to_lowercase()
    }

    /// Plain-text card for the preview pane.
    fn card(&self) -> Vec<String> {
        fn rule(out: &mut Vec<String>, title: &str) {
            out.push(String::new());
            out.push(format!(
                "── {title} {}",
                "─".repeat(60usize.saturating_sub(title.chars().count()))
            ));
        }
        fn list(out: &mut Vec<String>, title: &str, items: &[String], numbered: bool) {
            if items.is_empty() {
                return;
            }
            rule(out, title);
            for (i, it) in items.iter().enumerate() {
                out.push(if numbered {
                    format!("{}. {it}", i + 1)
                } else {
                    format!("• {it}")
                });
            }
        }
        let mut out = vec![format!("YOUR NOTE  ({})", self.kind), String::new()];
        out.extend(self.body.lines().map(str::to_string));
        if !self.context.is_empty() {
            out.push(String::new());
            out.push(format!("on: {}", self.context.replace('\n', " ")));
        }
        let mut meta = vec![
            self.ts.chars().take(16).collect::<String>(),
            self.status.clone(),
        ];
        if let Some(a) = self.structured.as_ref().filter(|a| !a.depth.is_empty()) {
            meta.push(format!("depth {} {}", self.depth_glyph(), a.depth));
        }
        if !self.entities.is_empty() {
            meta.push(self.entities.join(" "));
        }
        out.push(String::new());
        out.push(meta.join("  ·  "));
        match (&self.structured, &self.error) {
            (Some(a), _) => {
                if !a.themes.is_empty() {
                    out.push(format!("themes: {}", a.themes.join(", ")));
                }
                rule(&mut out, &format!("ANSWER  {}", a.title));
                out.extend(a.summary.lines().map(str::to_string));
                list(&mut out, "EVIDENCE", &a.key_points, false);
                if !a.assumption.is_empty() {
                    rule(&mut out, "YOUR ASSUMPTION");
                    out.push(a.assumption.clone());
                }
                list(&mut out, "ASK NEXT  (^f)", &a.follow_ups, true);
                list(&mut out, "LEARN", &a.learn, false);
            }
            (None, Some(e)) => {
                rule(&mut out, "FAILED");
                out.push(e.clone());
            }
            (None, None) => {
                rule(&mut out, "ANSWER");
                out.push(if self.status == "pending" {
                    "answering…".into()
                } else {
                    "(no answer)".into()
                });
            }
        }
        out
    }
}

/// `fl notes last`: the newest answered note, or the newest note if none is answered yet.
fn pick_last(notes: Vec<Note>) -> Vec<Note> {
    let newest = |answered_only: bool| {
        notes
            .iter()
            .enumerate()
            .filter(|(_, n)| !answered_only || n.status == "answered")
            .max_by_key(|(_, n)| n.ts.replace('T', " "))
            .map(|(i, _)| i)
    };
    match newest(true).or_else(|| newest(false)) {
        Some(i) => notes.into_iter().nth(i).into_iter().collect(),
        None => Vec::new(),
    }
}

/// Argv for `tmux` that reopens the chat that answered `n`, or why it cannot.
/// Passed as argv (no shell), so the session id and cwd are never interpreted.
pub fn resume_args(n: &Note, in_tmux: bool) -> Result<Vec<String>, String> {
    if !in_tmux {
        return Err("needs tmux".into());
    }
    let sid = n
        .session_id
        .as_deref()
        .filter(|s| !s.is_empty())
        .ok_or_else(|| "note has no chat yet".to_string())?;
    if !sid.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
        return Err("session id looks wrong, not resuming".into());
    }
    let mut args = vec!["new-window".to_string()];
    if let Some(cwd) = n.cwd.as_deref().filter(|c| !c.is_empty()) {
        args.extend(["-c".to_string(), cwd.to_string()]);
    }
    args.extend(["claude".to_string(), "--resume".to_string(), sid.to_string()]);
    Ok(args)
}

pub struct Notes {
    notes: Vec<Note>,
    query: String,
    shown: Vec<usize>,
    state: ListState,
    scroll: u16,
    /// Esc from the search bar: keys act on the list/card (vim-style) instead
    /// of typing. `/` or `i` returns to the bar; Esc again closes.
    browse: bool,
    /// ^f pressed: digits choose a follow-up.
    follow_mode: bool,
    flash: Option<String>,
    theme: Theme,
    /// Running under nvim (FINLARP_ACTION_FILE set): actions go back to nvim.
    nvim: bool,
    /// `fl notes last`: only the newest answered note.
    last_only: bool,
    /// Notes come from mind.duckdb (standalone), not from nvim's snapshot file.
    live: bool,
    loading: bool,
    /// A `py/mind/cli.py index` run in flight.
    refresh: Option<Receiver<Result<String, String>>>,
    next_reload: Instant,
    reload_until: Instant,
    /// Follow-ups being saved (standalone ^f).
    saves: Vec<Save>,
    /// Set when the screen changed outside a key press, so the next frame draws.
    redraw: bool,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Notes> {
    let last = arg.as_deref().is_some_and(|a| a.trim().eq_ignore_ascii_case("last"));
    match std::env::var_os(NOTES_FILE_ENV) {
        Some(p) => {
            let notes: Vec<Note> =
                serde_json::from_str(&std::fs::read_to_string(p)?).map_err(io::Error::other)?;
            let mut s = Notes::empty(ctx.theme, last);
            s.set_notes(notes);
            Ok(s)
        }
        None => {
            let mut s = Notes::empty(ctx.theme, last);
            s.live = true;
            s.loading = true;
            s.refresh = Some(pyrun::spawn_script(CLI, &["index"]));
            s.reload_until = Instant::now() + RELOAD_FOR;
            Ok(s)
        }
    }
}

/// Newest answered note (or newest note) from a `mind index` result.
fn load_json(json: &str, last: bool) -> Result<Vec<Note>, String> {
    let notes: Vec<Note> = serde_json::from_str(json).map_err(|e| format!("notes: {e}"))?;
    Ok(if last { pick_last(notes) } else { notes })
}

impl Notes {
    fn empty(theme: Theme, last_only: bool) -> Self {
        Self {
            notes: Vec::new(),
            query: String::new(),
            shown: Vec::new(),
            state: ListState::default(),
            scroll: 0,
            browse: false,
            follow_mode: false,
            flash: None,
            theme,
            nvim: std::env::var_os(ACTION_FILE_ENV).is_some(),
            last_only,
            live: false,
            loading: false,
            refresh: None,
            next_reload: Instant::now(),
            reload_until: Instant::now(),
            saves: Vec::new(),
            redraw: false,
        }
    }

    /// Replaces the list, keeping the selected note and card scroll when it is still there.
    fn set_notes(&mut self, notes: Vec<Note>) {
        let selected = self.current().map(|n| n.id.clone());
        let scroll = self.scroll;
        let mut notes = if self.last_only {
            pick_last(notes)
        } else {
            notes
        };
        // input is newest-first; stable sort keeps that within a ticker
        notes.sort_by_key(|n| n.ticker().unwrap_or_else(|| "~".into()));
        self.notes = notes;
        self.refilter();
        if let Some(id) = selected
            && let Some(pos) = self.shown.iter().position(|&i| self.notes[i].id == id)
        {
            self.state.select(Some(pos));
            self.scroll = scroll;
        }
    }

    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        let terms: Vec<&str> = q.split_whitespace().collect();
        self.shown = self
            .notes
            .iter()
            .enumerate()
            .filter(|(_, n)| {
                let hay = n.haystack();
                terms.iter().all(|t| hay.contains(t))
            })
            .map(|(i, _)| i)
            .collect();
        self.state
            .select(if self.shown.is_empty() { None } else { Some(0) });
        self.scroll = 0;
    }

    fn step(&mut self, delta: isize) {
        let n = self.shown.len();
        if n > 0 {
            let cur = self.state.selected().unwrap_or(0) as isize;
            self.state
                .select(Some((cur + delta).rem_euclid(n as isize) as usize));
            self.scroll = 0;
        }
    }

    fn current(&self) -> Option<&Note> {
        self.state
            .selected()
            .and_then(|s| self.shown.get(s))
            .map(|&i| &self.notes[i])
    }

    fn start_follow(&mut self) {
        let has = self
            .current()
            .and_then(|n| n.structured.as_ref())
            .is_some_and(|a| !a.follow_ups.is_empty());
        if has {
            self.follow_mode = true;
        } else {
            self.flash = Some("no follow-ups for this note".into());
        }
    }

    fn open_dossier(&mut self) -> Action {
        match self.current().and_then(Note::ticker) {
            Some(tk) => Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some(tk),
            }),
            None => {
                self.flash = Some("note has no ticker".into());
                Action::None
            }
        }
    }

    /// ↵: reopen the Claude chat that answered the selected note.
    fn resume(&mut self) -> Action {
        let Some(n) = self.current() else {
            return Action::None;
        };
        if self.nvim {
            return Action::Nvim(NvimAction::NoteChat { id: n.id.clone() });
        }
        let in_tmux = std::env::var_os("TMUX").is_some();
        let msg = match resume_args(n, in_tmux) {
            Ok(args) => match Command::new("tmux").args(&args).output() {
                Ok(out) if out.status.success() => "opened the chat in a new tmux window".to_string(),
                Ok(out) => format!("tmux: {}", String::from_utf8_lossy(&out.stderr).trim()),
                Err(e) => format!("tmux: {e}"),
            },
            Err(e) => e,
        };
        self.flash = Some(msg);
        Action::None
    }

    /// Follow-up `question` as a new note anchored like note `id`.
    fn ask(&mut self, id: String, question: String) -> Action {
        if self.nvim {
            return Action::Nvim(NvimAction::NoteAsk { id, question });
        }
        let Some(n) = self.notes.iter().find(|n| n.id == id) else {
            return Action::None;
        };
        let anchor = n.anchor.clone().or_else(|| n.entities.first().cloned());
        match Save::start(&question, &n.context, anchor.as_deref()) {
            Some(save) => {
                self.saves.push(save);
                self.flash = Some("saving follow-up…".into());
            }
            None => self.flash = Some("empty follow-up".into()),
        }
        Action::None
    }

    /// Esc'd out of the search bar: vim-style keys over the list and card.
    fn on_browse_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let last = self.shown.len().saturating_sub(1);
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
            KeyCode::Char('/' | 'i') if !ctrl => {
                self.browse = false;
                Action::None
            }
            KeyCode::Char('j') | KeyCode::Down if !ctrl => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('k') | KeyCode::Up if !ctrl => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('g') | KeyCode::Home if !ctrl => {
                self.jump(0);
                Action::None
            }
            KeyCode::Char('G') | KeyCode::End => {
                self.jump(last);
                Action::None
            }
            KeyCode::Char('d') if ctrl => {
                self.scroll = self.scroll.saturating_add(8);
                Action::None
            }
            KeyCode::Char('u') if ctrl => {
                self.scroll = self.scroll.saturating_sub(8);
                Action::None
            }
            KeyCode::PageDown => {
                self.scroll = self.scroll.saturating_add(8);
                Action::None
            }
            KeyCode::PageUp => {
                self.scroll = self.scroll.saturating_sub(8);
                Action::None
            }
            KeyCode::Enter => self.resume(),
            KeyCode::Char('f') => {
                self.start_follow();
                Action::None
            }
            KeyCode::Char('o') => self.open_dossier(),
            KeyCode::Char('c') if ctrl => Action::Quit,
            _ => Action::None,
        }
    }

    fn jump(&mut self, i: usize) {
        if !self.shown.is_empty() {
            self.state.select(Some(i.min(self.shown.len() - 1)));
            self.scroll = 0;
        }
    }

    fn follow_up(&mut self, k: usize) -> Action {
        self.follow_mode = false;
        let Some(n) = self.current() else {
            return Action::None;
        };
        let picked = n
            .structured
            .as_ref()
            .and_then(|a| a.follow_ups.get(k.wrapping_sub(1)))
            .cloned();
        let id = n.id.clone();
        match picked {
            Some(q) => self.ask(id, q),
            None => {
                self.flash = Some("no such follow-up".into());
                Action::None
            }
        }
    }

    /// Applies a finished `mind index` run.
    fn load_done(&mut self, json: &str) {
        match load_json(json, self.last_only) {
            Ok(notes) => self.set_notes(notes),
            Err(e) => self.flash = Some(e),
        }
    }
}

impl Screen for Notes {
    fn leader_ok(&self) -> bool {
        false
    }

    fn needs_redraw(&self) -> bool {
        self.redraw || self.loading || self.refresh.is_some() || !self.saves.is_empty()
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }

    fn tick(&mut self) -> Action {
        // a finished `mind index` run (the first load, or a reload)
        let got = self.refresh.as_ref().map(|rx| rx.try_recv());
        match got {
            None | Some(Err(TryRecvError::Empty)) => {}
            Some(Err(TryRecvError::Disconnected)) => {
                self.refresh = None;
                self.loading = false;
            }
            Some(Ok(res)) => {
                self.refresh = None;
                self.loading = false;
                self.redraw = true;
                match res {
                    Ok(json) => self.load_done(&json),
                    Err(e) => self.flash = Some(format!("notes: {e}")),
                }
            }
        }

        // follow-ups that finished saving: their answers are pending now
        let mut done = Vec::new();
        self.saves.retain(|s| match s.poll() {
            None => true,
            Some(r) => {
                done.push(r);
                false
            }
        });
        for r in done {
            self.redraw = true;
            self.reload_until = Instant::now() + RELOAD_FOR;
            self.next_reload = Instant::now();
            self.flash = Some(match r {
                Ok(id) => format!("saved {id} · answering in the background"),
                Err(e) => e,
            });
        }

        // while any answer is pending, re-read the list every few seconds
        let now = Instant::now();
        if self.live
            && self.refresh.is_none()
            && now < self.reload_until
            && now >= self.next_reload
            && self.notes.iter().any(|n| n.status == "pending")
        {
            self.refresh = Some(pyrun::spawn_script(CLI, &["index"]));
            self.next_reload = now + RELOAD_EVERY;
        }
        Action::None
    }

    fn draw(&mut self, frame: &mut Frame) {
        self.redraw = false;
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [input, list, card, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Percentage(35),
            Constraint::Min(3),
            Constraint::Length(1),
        ])
        .areas(area);

        let prefix = " Notes › ";
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prefix, t.accent()),
                Span::styled(self.query.clone(), t.base()),
            ])),
            input,
        );
        if !self.browse {
            frame.set_cursor_position((
                input.x + (text::width(prefix) + text::width(&self.query)) as u16,
                input.y,
            ));
        }

        if self.shown.is_empty() {
            let msg = if self.loading {
                "  loading notes…"
            } else if self.notes.is_empty() {
                if self.nvim {
                    "  no notes yet (<leader>vn)"
                } else {
                    "  no notes yet (fl note)"
                }
            } else {
                "  no match"
            };
            frame.render_widget(Paragraph::new(msg).style(t.dim()), list);
        } else {
            let title_w = (list.width as usize).saturating_sub(34).max(10);
            let rows: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| {
                    let n = &self.notes[i];
                    let day: String = n.ts.chars().skip(5).take(5).collect();
                    ListItem::new(Line::from(vec![
                        Span::styled(format!("  {} {day}  ", n.status_glyph()), t.dim()),
                        Span::styled(
                            format!("{:<6} ", n.ticker().unwrap_or_default()),
                            t.accent(),
                        ),
                        Span::styled(
                            format!("{:<title_w$} ", text::truncate(&n.title(), title_w)),
                            t.base(),
                        ),
                        Span::styled(
                            format!("{}  {}", n.depth_glyph(), n.themes.join(" · ")),
                            t.dim(),
                        ),
                    ]))
                })
                .collect();
            frame.render_stateful_widget(
                List::new(rows)
                    .style(t.base())
                    .highlight_style(t.selected()),
                list,
                &mut self.state,
            );
        }

        if let Some(n) = self.current() {
            let lines: Vec<Line> = n
                .card()
                .into_iter()
                .map(|l| {
                    if l.starts_with("──") || l.starts_with("YOUR NOTE") {
                        Line::from(Span::styled(l, t.title()))
                    } else {
                        Line::from(l)
                    }
                })
                .collect();
            frame.render_widget(
                Paragraph::new(lines)
                    .style(t.base())
                    .block(
                        Block::new()
                            .borders(ratatui::widgets::Borders::TOP)
                            .border_style(t.border()),
                    )
                    .wrap(Wrap { trim: false })
                    .scroll((self.scroll, 0)),
                card,
            );
        }

        let foot_text = if self.follow_mode {
            " follow-up: press 1-9 to ask · esc cancel".to_string()
        } else if self.browse {
            self.flash.clone().unwrap_or_else(|| {
                " j/k move · ^d/^u scroll card · g/G top/bottom · ↵ chat · f follow-up · o dossier · / search · esc close"
                    .to_string()
            })
        } else {
            self.flash.clone().unwrap_or_else(|| {
                " ↑/↓ or alt-j/k move · ^d/^u scroll · ↵ chat · ^f follow-up · ^o dossier · ^g godel · esc browse"
                    .to_string()
            })
        };
        frame.render_widget(Paragraph::new(foot_text).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        if self.follow_mode {
            return match key.code {
                KeyCode::Char(c @ '1'..='9') => self.follow_up(c as usize - '0' as usize),
                _ => {
                    self.follow_mode = false;
                    Action::None
                }
            };
        }
        if self.browse {
            return self.on_browse_key(key);
        }
        let alt = key.modifiers.contains(KeyModifiers::ALT);
        match key.code {
            KeyCode::Esc => {
                self.browse = true;
                Action::None
            }
            KeyCode::Char('j') if alt => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('k') if alt => {
                self.step(-1);
                Action::None
            }
            KeyCode::Enter => self.resume(),
            KeyCode::Down | KeyCode::Tab => {
                self.step(1);
                Action::None
            }
            KeyCode::Up | KeyCode::BackTab => {
                self.step(-1);
                Action::None
            }
            KeyCode::PageDown => {
                self.scroll = self.scroll.saturating_add(8);
                Action::None
            }
            KeyCode::PageUp => {
                self.scroll = self.scroll.saturating_sub(8);
                Action::None
            }
            KeyCode::Char('n' | 'j') if ctrl => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('p' | 'k') if ctrl => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('d') if ctrl => {
                self.scroll = self.scroll.saturating_add(8);
                Action::None
            }
            KeyCode::Char('u') if ctrl => {
                self.scroll = self.scroll.saturating_sub(8);
                Action::None
            }
            KeyCode::Char('f') if ctrl => {
                self.start_follow();
                Action::None
            }
            KeyCode::Char('o') if ctrl => self.open_dossier(),
            KeyCode::Char('g') if ctrl => Action::Nvim(NvimAction::Screen {
                screen: "godel".into(),
                arg: None,
            }),
            KeyCode::Char('c') if ctrl => Action::Quit,
            KeyCode::Backspace => {
                self.query.pop();
                self.refilter();
                Action::None
            }
            KeyCode::Char(c) if !ctrl && !alt => {
                self.query.push(c);
                self.refilter();
                Action::None
            }
            _ => Action::None,
        }
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::buffer::Buffer;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    const JSON: &str = r#"[
      {"id":"b","kind":"word","body":"why AVGO","ts":"2026-10-11T10:00:00","status":"pending",
       "entities":{},"themes":{},"anchor":"ticker:AVGO"},
      {"id":"a1","kind":"word","body":"what is capex","ts":"2026-10-12T09:00:00","status":"answered",
       "entities":["ticker:MRVL"],"themes":["ai-capex"],"session_id":"6f1c2b3a-0000-4000-8000-000000000001",
       "cwd":"/work/finlarp",
       "structured":{"title":"Capex","summary":"s","depth":"causal","follow_ups":["why?","how much?"],
                     "key_points":{},"themes":["ai-capex"]}},
      {"id":"c","kind":"word","body":"untagged","ts":"2026-10-10T09:00:00","status":"failed",
       "entities":[],"themes":[],"error":"boom"}
    ]"#;

    fn notes() -> Notes {
        let mut n = Notes::empty(Theme::default(), false);
        n.set_notes(parsed());
        n.nvim = true; // the nvim actions (NoteChat, NoteAsk) are what these tests check
        n
    }

    fn parsed() -> Vec<Note> {
        serde_json::from_str(JSON).expect("json")
    }

    fn press(n: &mut Notes, code: KeyCode, mods: KeyModifiers) -> Action {
        n.on_key(KeyEvent {
            code,
            modifiers: mods,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn id_of(n: &Notes) -> &str {
        &n.current().expect("selected").id
    }

    fn screen_text(buf: &Buffer) -> String {
        buf.content().iter().map(|c| c.symbol()).collect()
    }

    #[test]
    fn parses_lua_empty_tables_and_groups_by_ticker() {
        let n = notes();
        // AVGO, MRVL, then untagged last
        let order: Vec<&str> = n.shown.iter().map(|&i| n.notes[i].id.as_str()).collect();
        assert_eq!(order, ["b", "a1", "c"]);
    }

    #[test]
    fn enter_reopens_chat_and_filter_narrows() {
        let mut n = notes();
        for c in "capex".chars() {
            press(&mut n, KeyCode::Char(c), KeyModifiers::NONE);
        }
        assert_eq!(id_of(&n), "a1");
        assert_eq!(
            press(&mut n, KeyCode::Enter, KeyModifiers::NONE),
            Action::Nvim(NvimAction::NoteChat { id: "a1".into() })
        );
    }

    #[test]
    fn follow_up_chips_pick_by_digit() {
        let mut n = notes();
        press(&mut n, KeyCode::Down, KeyModifiers::NONE); // a1
        press(&mut n, KeyCode::Char('f'), KeyModifiers::CONTROL);
        assert!(n.follow_mode);
        assert_eq!(
            press(&mut n, KeyCode::Char('2'), KeyModifiers::NONE),
            Action::Nvim(NvimAction::NoteAsk {
                id: "a1".into(),
                question: "how much?".into()
            })
        );
    }

    #[test]
    fn dossier_needs_a_ticker() {
        let mut n = notes();
        assert_eq!(
            press(&mut n, KeyCode::Char('o'), KeyModifiers::CONTROL),
            Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some("AVGO".into())
            })
        );
        press(&mut n, KeyCode::Down, KeyModifiers::NONE);
        press(&mut n, KeyCode::Down, KeyModifiers::NONE); // untagged
        assert_eq!(
            press(&mut n, KeyCode::Char('o'), KeyModifiers::CONTROL),
            Action::None
        );
    }

    #[test]
    fn esc_browses_then_closes_and_jk_navigate() {
        let mut n = notes();
        // typing j in the bar is text; alt-j moves
        press(&mut n, KeyCode::Char('j'), KeyModifiers::ALT);
        assert_eq!(id_of(&n), "a1");
        assert_eq!(n.query, "");
        // esc leaves the bar, keys now navigate instead of typing
        assert_eq!(
            press(&mut n, KeyCode::Esc, KeyModifiers::NONE),
            Action::None
        );
        assert!(n.browse);
        press(&mut n, KeyCode::Char('j'), KeyModifiers::NONE);
        assert_eq!(id_of(&n), "c");
        press(&mut n, KeyCode::Char('k'), KeyModifiers::NONE);
        press(&mut n, KeyCode::Char('g'), KeyModifiers::NONE);
        assert_eq!(id_of(&n), "b");
        press(&mut n, KeyCode::Char('G'), KeyModifiers::NONE);
        assert_eq!(id_of(&n), "c");
        assert_eq!(n.query, "");
        // `/` goes back to the bar; esc, esc closes
        press(&mut n, KeyCode::Char('/'), KeyModifiers::NONE);
        assert!(!n.browse);
        press(&mut n, KeyCode::Esc, KeyModifiers::NONE);
        assert_eq!(
            press(&mut n, KeyCode::Esc, KeyModifiers::NONE),
            Action::Quit
        );
    }

    #[test]
    fn card_renders_every_state() {
        for note in &notes().notes {
            assert!(note.card().len() > 3);
        }
    }

    #[test]
    fn last_picks_newest_answered_note() {
        let picked = pick_last(parsed());
        assert_eq!(picked.iter().map(|n| n.id.as_str()).collect::<Vec<_>>(), ["a1"]);
        // nothing answered yet: the newest note, whatever its status
        let mut pending: Vec<Note> = parsed();
        pending.retain(|n| n.id != "a1");
        let picked = pick_last(pending);
        assert_eq!(picked.iter().map(|n| n.id.as_str()).collect::<Vec<_>>(), ["b"]);
        assert!(pick_last(Vec::new()).is_empty());
    }

    #[test]
    fn last_mode_keeps_only_that_note() {
        let mut n = Notes::empty(Theme::default(), true);
        n.nvim = true;
        n.set_notes(parsed());
        assert_eq!(n.notes.len(), 1);
        assert_eq!(id_of(&n), "a1");
    }

    #[test]
    fn resume_argv_is_tmux_new_window_in_cwd() {
        let n = notes().notes.into_iter().find(|n| n.id == "a1").expect("a1");
        assert_eq!(
            resume_args(&n, true).expect("argv"),
            [
                "new-window",
                "-c",
                "/work/finlarp",
                "claude",
                "--resume",
                "6f1c2b3a-0000-4000-8000-000000000001"
            ]
        );
        assert_eq!(resume_args(&n, false), Err("needs tmux".to_string()));
        let no_chat = notes().notes.into_iter().find(|n| n.id == "b").expect("b");
        assert_eq!(
            resume_args(&no_chat, true),
            Err("note has no chat yet".to_string())
        );
    }

    #[test]
    fn resume_rejects_odd_session_ids() {
        let mut n = notes().notes.into_iter().find(|n| n.id == "a1").expect("a1");
        n.session_id = Some("x; rm -rf ~".into());
        assert!(resume_args(&n, true).is_err());
        n.session_id = Some("abc-123".into());
        n.cwd = None;
        assert_eq!(
            resume_args(&n, true).expect("argv"),
            ["new-window", "claude", "--resume", "abc-123"]
        );
    }

    #[test]
    fn renders_list_and_answer_card() {
        let mut n = notes();
        let mut term = Terminal::new(TestBackend::new(100, 30)).expect("terminal");
        term.draw(|f| n.draw(f)).expect("draw");
        let text = screen_text(term.backend().buffer());
        assert!(text.contains("Capex"), "{text}");
        assert!(text.contains("ANSWER"), "{text}");
    }
}

#[cfg(test)]
mod null_fields_tests {
    use super::Note;

    /// mind's index emits `null` for unset strings (context, error); that must parse, not fail the screen.
    #[test]
    fn null_string_fields_parse_as_empty() {
        let n: Note = serde_json::from_str(
            r#"{"id":"n1","body":"b","context":null,"status":null,"structured":null,"entities":null}"#,
        )
        .expect("null strings should deserialize");
        assert_eq!(n.context, "");
        assert_eq!(n.status, "");
        assert_eq!(n.body, "b");
        assert!(n.structured.is_none());
    }
}
