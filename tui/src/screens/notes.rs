// `<leader>vm`: browser over every note you've asked. nvim fetches them from
// mind.duckdb (ui/notes.lua) and passes JSON in $FINLARP_NOTES_FILE.
// Rows are grouped by ticker (A-Z, untagged last), newest first within a group.
//
//   Notes ›  mrvl█
//   ✓ 10-12  MRVL   Custom silicon ramp ...      ●●○  ai-capex
//   ── YOUR NOTE ... ── ANSWER ... (scrollable card)
//
// Type filters (ticker, title, body, themes, entities) · ^n/^p move ·
// ^d/^u scroll card · ↵ reopen the Claude chat · ^f follow-up chips (1-9) ·
// ^o dossier · ^g godel · esc back.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph, Wrap};
use serde::{Deserialize, Deserializer};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

pub const NOTES_FILE_ENV: &str = "FINLARP_NOTES_FILE";

/// Lua encodes an empty list as `{}`; accept that (and null) as empty.
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
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub summary: String,
    #[serde(default)]
    pub depth: String,
    #[serde(default, deserialize_with = "lenient")]
    pub themes: Vec<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub key_points: Vec<String>,
    #[serde(default)]
    pub assumption: String,
    #[serde(default, deserialize_with = "lenient")]
    pub follow_ups: Vec<String>,
    #[serde(default, deserialize_with = "lenient")]
    pub learn: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Note {
    pub id: String,
    #[serde(default)]
    pub kind: String,
    #[serde(default)]
    pub body: String,
    #[serde(default)]
    pub context: String,
    #[serde(default)]
    pub ts: String,
    #[serde(default)]
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
                out.push("(waiting for answer)".into());
            }
        }
        out
    }
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
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Notes> {
    let notes: Vec<Note> = match std::env::var_os(NOTES_FILE_ENV) {
        Some(p) => serde_json::from_str(&std::fs::read_to_string(p)?).map_err(io::Error::other)?,
        None => Vec::new(),
    };
    Ok(Notes::new(notes, ctx.theme))
}

impl Notes {
    pub fn new(mut notes: Vec<Note>, theme: Theme) -> Self {
        // input is newest-first; stable sort keeps that within a ticker
        notes.sort_by_key(|n| n.ticker().unwrap_or_else(|| "~".into()));
        let mut s = Self {
            notes,
            query: String::new(),
            shown: Vec::new(),
            state: ListState::default(),
            scroll: 0,
            browse: false,
            follow_mode: false,
            flash: None,
            theme,
        };
        s.refilter();
        s
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
            KeyCode::Enter => match self.current() {
                Some(n) => Action::Nvim(NvimAction::NoteChat { id: n.id.clone() }),
                None => Action::None,
            },
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
        let q = n
            .structured
            .as_ref()
            .and_then(|a| a.follow_ups.get(k.wrapping_sub(1)));
        match q {
            Some(q) => Action::Nvim(NvimAction::NoteAsk {
                id: n.id.clone(),
                question: q.clone(),
            }),
            None => {
                self.flash = Some("no such follow-up".into());
                Action::None
            }
        }
    }
}

impl Screen for Notes {
    fn leader_ok(&self) -> bool {
        false
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
            let msg = if self.notes.is_empty() {
                "  no notes yet (<leader>vn)"
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
            KeyCode::Enter => match self.current() {
                Some(n) => Action::Nvim(NvimAction::NoteChat { id: n.id.clone() }),
                None => Action::None,
            },
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
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    const JSON: &str = r#"[
      {"id":"b","kind":"word","body":"why AVGO","ts":"2026-10-11T10:00:00","status":"pending",
       "entities":{},"themes":{},"anchor":"ticker:AVGO"},
      {"id":"a1","kind":"word","body":"what is capex","ts":"2026-10-12T09:00:00","status":"answered",
       "entities":["ticker:MRVL"],"themes":["ai-capex"],
       "structured":{"title":"Capex","summary":"s","depth":"causal","follow_ups":["why?","how much?"],
                     "key_points":{},"themes":["ai-capex"]}},
      {"id":"c","kind":"word","body":"untagged","ts":"2026-10-10T09:00:00","status":"failed",
       "entities":[],"themes":[],"error":"boom"}
    ]"#;

    fn notes() -> Notes {
        Notes::new(serde_json::from_str(JSON).expect("json"), Theme::default())
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
}
