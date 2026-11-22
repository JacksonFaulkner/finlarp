// Z: diagrams built in the chat. The left pane is a canvas showing the ACTIVE diagram, one
// file in the Z folder (`data/z/*.json`, format in z_spec.rs). The active diagram changes
// only when the user opens one (f menu, [ ], g/G, b back); Claude writing a file never
// switches the view, it only flashes "new: ...". The right pane is Claude Code itself,
// running in a tmux session (one per mode, so switching modes keeps each conversation).
// The canvas writes `state.json` (what the user is looking at) for Claude to read.
//
// One picture per diagram: no sections or zooms, and no number or letter keys. Explanations
// are labels on the parts. Keys: hjkl orbit, +/- zoom, 0 reset, F full picture, v art,
// p pause flows, [ ] previous/next diagram, f diagram menu, b back to the diagram you came
// from. The chat sits under the picture and is always on screen (F hides it); `C` gives
// Claude the keys, ctrl-/ takes them back. `M` switches mode.

use std::io;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};

use image::{DynamicImage, RgbaImage};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    Block, Borders, Clear, List, ListItem, ListState, Paragraph, StatefulWidget, Widget, Wrap,
};
use ratatui_image::picker::{Picker, ProtocolType};
use ratatui_image::protocol::StatefulProtocol;
use ratatui_image::{Resize, StatefulImage};

use super::diagrams_window::ClaudeWindow;
use super::z_spec::{self, Camera, Diagram, Scene};
use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{Help, Key, key};
use crate::ui::layout::popup;
use crate::ui::theme::Theme;

/// How many earlier diagrams `b` can walk back through.
const HISTORY: usize = 50;
/// Claude writes a diagram's file name here when the user asked for it to be shown; the
/// canvas opens that file and removes the marker. Dot files are not diagrams.
const OPEN_MARK: &str = ".open";

const SOCKET: &str = "fl-z";
const RULES: &str = include_str!("z_rules.md");
/// The picture's background, as the Diagrams screen's 3D views.
const BG: [u8; 3] = [0x28, 0x2a, 0x36];
/// Largest render, in pixels: the terminal scales it up. Keeps a held orbit key smooth.
const MAX_PX: (u32, u32) = (1600, 1000);
/// One trip of the flow dashes.
const FLOW_SECS: f64 = 2.5;
const FRAME: Duration = Duration::from_millis(80);
const WATCH: Duration = Duration::from_millis(300);
/// Kitty image ids used in turn, so the old frame stays up while the new one uploads.
const IMAGE_IDS: [u32; 2] = [
    u32::from_be_bytes([0, 0xF3, 0x2A, 0x01]),
    u32::from_be_bytes([0, 0xF3, 0x2A, 0x02]),
];

#[derive(Clone, Copy, PartialEq, Debug)]
enum Mode {
    Chat,
    Build,
    Quiz,
}

const MODES: [Mode; 3] = [Mode::Chat, Mode::Build, Mode::Quiz];

impl Mode {
    fn name(self) -> &'static str {
        match self {
            Mode::Chat => "chat",
            Mode::Build => "build",
            Mode::Quiz => "quiz",
        }
    }
    fn session(self) -> &'static str {
        match self {
            Mode::Chat => "finlarp-z-chat",
            Mode::Build => "finlarp-z-build",
            Mode::Quiz => "finlarp-z-quiz",
        }
    }
    fn brief(self) -> &'static str {
        match self {
            Mode::Chat => {
                "Normal conversation. Answer in the chat; draw a diagram only when a picture explains \
                 the idea better than words (a mechanism, a structure, something that flows, a \
                 geometry). Put the explanation on the picture as part labels and in the diagram's \
                 text, and keep the chat reply short."
            }
            Mode::Build => {
                "The user is designing a diagram with you. Every turn changes the canvas: edit the \
                 current file (see state.json) rather than starting a new one, unless they ask for a \
                 new diagram. When a design choice is open, offer it with AskUserQuestion."
            }
            Mode::Quiz => {
                "Teach by asking. Draw the diagram, then quiz the user with AskUserQuestion, one \
                 question at a time, using the picture (\"which part carries the current?\", \"what \
                 happens if this layer is thinner?\"). After each answer say whether it was right and \
                 why, label the part it is about on the picture, then go on or go deeper."
            }
        }
    }
}

/// The picture on screen and what it was drawn from.
struct Shown {
    key: (u64, u32, u32),
    proto: StatefulProtocol,
}

/// One diagram file in the Z folder, as last listed.
#[derive(Clone)]
struct Entry {
    path: PathBuf,
    mtime: SystemTime,
    /// The diagram's title, or the file name when it does not parse.
    title: String,
    ok: bool,
}

pub struct Z {
    theme: Theme,
    dir: PathBuf,
    /// Diagram files, in name order.
    files: Vec<Entry>,
    /// The diagram on the canvas. The only place that says which one is open; it is always
    /// a path in `files` or None (empty folder).
    active: Option<PathBuf>,
    /// Diagrams left behind by `open`, most recent last; `b` pops one back.
    history: Vec<PathBuf>,
    /// The diagram menu (f) when open: the row under the cursor.
    menu: Option<usize>,
    /// The active diagram: the last version of the file that parsed.
    diagram: Option<Diagram>,
    /// Why the current file did not parse, when it did not.
    errors: Vec<String>,
    camera: poly3d::View,
    /// Show the art instead of the scene, when a diagram has both.
    art_first: bool,
    full: bool,
    paused: bool,
    scroll: u16,
    start: Instant,
    last_watch: Instant,
    mode: Mode,
    windows: Vec<ClaudeWindow>,
    picker: Option<Picker>,
    shown: Option<Shown>,
    frames: u32,
    last_state: String,
    flash: Option<(String, Instant)>,
}

pub fn z_dir() -> PathBuf {
    crate::data_dir().join("z")
}

/// The system prompt for `mode`, written next to the diagrams so tmux can `cat` it.
fn prompt_file(dir: &Path, mode: Mode) -> io::Result<PathBuf> {
    let path = dir.join(format!(".prompt-{}.md", mode.name()));
    let text = format!(
        "{RULES}\n\n## Z folder\n\n{}\n\n## Mode: {}\n\n{}\n",
        dir.display(),
        mode.name(),
        mode.brief()
    );
    std::fs::write(&path, text)?;
    Ok(path)
}

fn claude_command(dir: &Path, prompt: &Path) -> String {
    let d = dir.display();
    format!(
        "claude --append-system-prompt \"$(cat '{}')\" --allowedTools 'Write(/{d}/**)' 'Edit(/{d}/**)' 'Read(/{d}/**)' 'Bash(fl z check:*)' 'Bash(fl z render:*)' 'Read(//tmp/**)'",
        prompt.display()
    )
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Z> {
    let dir = z_dir();
    std::fs::create_dir_all(&dir)?;
    let windows = MODES
        .iter()
        .map(|&m| {
            let prompt = prompt_file(&dir, m)?;
            Ok(ClaudeWindow::with(
                ctx.theme.clone(),
                SOCKET,
                m.session(),
                claude_command(&dir, &prompt),
            ))
        })
        .collect::<io::Result<Vec<_>>>()?;
    // Must run before the event loop reads stdin: the terminal answers the query on stdin.
    #[cfg(not(test))]
    let picker = Some(super::diagrams::query_picker());
    #[cfg(test)]
    let picker = Some(Picker::halfblocks());
    let mut z = Z {
        theme: ctx.theme.clone(),
        dir,
        files: Vec::new(),
        active: None,
        history: Vec::new(),
        menu: None,
        diagram: None,
        errors: Vec::new(),
        camera: poly3d::View::default(),
        art_first: false,
        full: false,
        paused: false,
        scroll: 0,
        start: Instant::now(),
        last_watch: Instant::now(),
        mode: Mode::Chat,
        windows,
        picker,
        shown: None,
        frames: 0,
        last_state: String::new(),
        flash: None,
    };
    for w in &mut z.windows {
        w.open = true;
    }
    z.watch(true);
    if let Some(a) = arg.as_deref().map(str::to_lowercase) {
        if let Some(m) = MODES.iter().find(|m| m.name() == a) {
            z.mode = *m;
        } else if let Some(p) = z
            .files
            .iter()
            .find(|f| file_name(&f.path).to_lowercase().contains(&a))
            .map(|f| f.path.clone())
        {
            z.show(p);
        }
    }
    Ok(z)
}

fn file_name(p: &Path) -> String {
    p.file_name()
        .map(|s| s.to_string_lossy().into_owned())
        .unwrap_or_default()
}

/// The title a file shows in the menu, and whether it parses.
fn title_of(path: &Path) -> (String, bool) {
    match z_spec::load(path) {
        Ok(d) => (d.title, true),
        Err(_) => ("does not parse; open it to see why".into(), false),
    }
}

fn list(dir: &Path) -> Vec<(PathBuf, SystemTime)> {
    let Ok(rd) = std::fs::read_dir(dir) else {
        return Vec::new();
    };
    let mut out: Vec<(PathBuf, SystemTime)> = rd
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| {
            let n = file_name(p);
            p.extension().is_some_and(|x| x == "json") && !n.starts_with('.') && n != "state.json"
        })
        .filter_map(|p| {
            let m = std::fs::metadata(&p).and_then(|m| m.modified()).ok()?;
            Some((p, m))
        })
        .collect();
    out.sort_by(|a, b| a.0.cmp(&b.0));
    out
}

fn camera_view(c: Camera) -> poly3d::View {
    poly3d::View {
        yaw: c.yaw.to_radians(),
        pitch: c.pitch.to_radians().clamp(-0.3, 1.3),
        zoom: c.zoom.clamp(0.3, 6.0),
        pan: [0.0, 0.0],
    }
}

/// Box, line and arrow glyphs: drawn in the accent colour.
fn is_frame_glyph(c: char) -> bool {
    matches!(c as u32, 0x2190..=0x21FF | 0x2500..=0x259F | 0x25A0..=0x25FF | 0x2794..=0x27BF)
}

impl Z {
    fn window(&mut self) -> &mut ClaudeWindow {
        let i = MODES.iter().position(|m| *m == self.mode).unwrap_or(0);
        &mut self.windows[i]
    }
    fn window_ref(&self) -> &ClaudeWindow {
        let i = MODES.iter().position(|m| *m == self.mode).unwrap_or(0);
        &self.windows[i]
    }

    fn flash(&mut self, msg: impl Into<String>) {
        self.flash = Some((msg.into(), Instant::now()));
    }

    /// Index of the active diagram in the folder listing.
    fn cur(&self) -> Option<usize> {
        let p = self.active.as_deref()?;
        self.files.iter().position(|f| f.path == p)
    }

    fn newest_path(&self) -> Option<PathBuf> {
        self.files
            .iter()
            .max_by_key(|f| f.mtime)
            .map(|f| f.path.clone())
    }

    /// Re-lists the folder. The active diagram stays active: it reloads when its file was
    /// edited, and only moves when its file is gone. New files are announced, not opened.
    fn watch(&mut self, first: bool) {
        let old = std::mem::take(&mut self.files);
        let files: Vec<Entry> = list(&self.dir)
            .into_iter()
            .map(|(path, mtime)| match old.iter().find(|e| e.path == path) {
                Some(e) if e.mtime == mtime => e.clone(),
                _ => {
                    let (title, ok) = title_of(&path);
                    Entry {
                        path,
                        mtime,
                        title,
                        ok,
                    }
                }
            })
            .collect();
        let fresh: Vec<String> = files
            .iter()
            .filter(|f| !old.iter().any(|o| o.path == f.path))
            .map(|f| file_name(&f.path))
            .collect();
        let mtime_in = |l: &[Entry], p: &Path| l.iter().find(|e| e.path == p).map(|e| e.mtime);
        let edited = self
            .active
            .as_deref()
            .is_some_and(|p| mtime_in(&old, p) != mtime_in(&files, p));
        self.files = files;

        let gone = self
            .active
            .as_deref()
            .is_none_or(|p| !self.files.iter().any(|f| f.path == p));
        if gone {
            // First start opens the newest file; a vanished active file falls back to it too.
            let had = self.active.is_some();
            self.active = self.newest_path();
            self.reload(false);
            if had && !first {
                self.flash("open diagram was removed; showing the newest");
            }
        } else if edited {
            self.reload(true);
        }
        let asked = self.take_open_request();
        if let Some(p) = &asked {
            self.flash(format!("opened {}", file_name(p)));
        }
        if !first {
            for name in fresh
                .into_iter()
                .filter(|n| asked.as_deref().is_none_or(|p| file_name(p) != *n))
            {
                self.flash(format!("new: {name}  (f to open)"));
            }
        }
        if let Some(p) = asked {
            self.open(p);
        }
    }

    /// The file Claude asked to show, from `.open`. The marker is removed once the file is
    /// found, so a request for a file not written yet waits for it.
    fn take_open_request(&self) -> Option<PathBuf> {
        let mark = self.dir.join(OPEN_MARK);
        let name = std::fs::read_to_string(&mark).ok()?;
        let name = name.trim();
        let p = self
            .files
            .iter()
            .find(|f| file_name(&f.path) == name)?
            .path
            .clone();
        let _ = std::fs::remove_file(&mark);
        Some(p)
    }

    /// Opens `path` and remembers the diagram it replaces, so `b` can return to it.
    fn open(&mut self, path: PathBuf) {
        if self.active.as_ref() == Some(&path) {
            return;
        }
        if let Some(prev) = self.active.take() {
            self.history.push(prev);
            if self.history.len() > HISTORY {
                self.history.remove(0);
            }
        }
        self.show(path);
    }

    /// Makes `path` the active diagram without touching the history.
    fn show(&mut self, path: PathBuf) {
        self.active = Some(path);
        self.reload(false);
    }

    /// `b`: back to the diagram open before this one. Skips files that are gone.
    fn back(&mut self) {
        while let Some(p) = self.history.pop() {
            if self.files.iter().any(|f| f.path == p) {
                self.show(p);
                return;
            }
        }
        self.flash("no earlier diagram");
    }

    /// Opens the diagram at listing position `i`, if there is one.
    fn open_at(&mut self, i: usize) {
        if let Some(f) = self.files.get(i) {
            let p = f.path.clone();
            self.open(p);
        }
    }

    /// `[` and `]`: the diagram `delta` places along the folder listing.
    fn step(&mut self, delta: isize) {
        let Some(i) = self.cur() else { return };
        if let Ok(j) = usize::try_from(i as isize + delta) {
            self.open_at(j);
        }
    }

    /// Keys while the f menu is open: move, Enter opens, Esc/f/q close.
    fn menu_key(&mut self, key: KeyEvent) -> Action {
        let Some(sel) = self.menu else {
            return Action::None;
        };
        let last = self.files.len().saturating_sub(1);
        match key.code {
            KeyCode::Esc | KeyCode::Char('f') | KeyCode::Char('q') => self.menu = None,
            KeyCode::Up | KeyCode::Char('k') => self.menu = Some(sel.saturating_sub(1)),
            KeyCode::Down | KeyCode::Char('j') => self.menu = Some((sel + 1).min(last)),
            KeyCode::Char('g') => self.menu = Some(0),
            KeyCode::Char('G') => self.menu = Some(last),
            KeyCode::Enter => {
                self.menu = None;
                self.open_at(sel);
            }
            _ => {}
        }
        Action::None
    }

    /// The f menu: every diagram in the folder, one line each. The active one is marked; a
    /// file that does not parse is shown with its file name and a cross.
    fn draw_menu(&self, frame: &mut Frame, area: Rect) {
        let Some(sel) = self.menu else { return };
        let t = &self.theme;
        let r = popup(area, 72, self.files.len() as u16 + 4);
        Clear.render(r, frame.buffer_mut());
        let block = Block::bordered()
            .title(" diagrams · enter open · esc close ")
            .border_style(t.accent())
            .style(t.base());
        let inner = block.inner(r);
        frame.render_widget(block, r);
        if self.files.is_empty() {
            frame.render_widget(
                Paragraph::new(Line::styled("  no diagrams in the folder", t.dim())),
                inner,
            );
            return;
        }
        let active = self.cur();
        let items: Vec<ListItem> = self
            .files
            .iter()
            .enumerate()
            .map(|(i, f)| {
                let mark = if active == Some(i) { "● " } else { "  " };
                let title = if f.ok {
                    f.title.clone()
                } else {
                    format!("✗ {}", f.title)
                };
                let style = if f.ok { t.title() } else { t.down() };
                ListItem::new(Line::from(vec![
                    Span::styled(mark, t.accent()),
                    Span::styled(format!("{:<22}", file_name(&f.path)), t.dim()),
                    Span::styled(title, style),
                ]))
            })
            .collect();
        let list = List::new(items)
            .highlight_style(t.selected().add_modifier(Modifier::BOLD))
            .highlight_symbol("▌ ");
        let mut state = ListState::default().with_selected(Some(sel.min(self.files.len() - 1)));
        StatefulWidget::render(list, inner, frame.buffer_mut(), &mut state);
    }

    /// Loads the active file. `keep` keeps the camera and the open view (the same file
    /// was edited); otherwise the view starts at the diagram's own camera.
    fn reload(&mut self, keep: bool) {
        let Some(path) = self.active.clone() else {
            self.diagram = None;
            self.errors.clear();
            self.shown = None;
            return;
        };
        match z_spec::load(&path) {
            Ok(d) => {
                self.errors.clear();
                if !keep {
                    self.scroll = 0;
                    self.art_first = false;
                    self.camera =
                        camera_view(d.scene.as_ref().and_then(|s| s.camera).unwrap_or_default());
                }
                self.diagram = Some(d);
            }
            Err(e) => {
                if !keep {
                    self.diagram = None;
                }
                self.errors = e;
            }
        }
        self.shown = None;
    }

    /// The picture, caption and text of the active diagram: (title, art, scene, caption, text).
    fn current(&self) -> Option<(String, &[String], Option<&Scene>, &str, &str)> {
        let d = self.diagram.as_ref()?;
        Some((
            d.title.clone(),
            &d.art[..],
            d.scene.as_ref(),
            d.caption.as_str(),
            d.text.as_str(),
        ))
    }

    fn animating(&self) -> bool {
        !self.paused
            && self.current().is_some_and(|(_, art, scene, ..)| {
                scene.is_some_and(|s| !s.flows.is_empty()) && !(self.art_first && !art.is_empty())
            })
    }

    /// Puts the camera back to the diagram's own starting view.
    fn reset_camera(&mut self) {
        self.camera = camera_view(
            self.diagram
                .as_ref()
                .and_then(|d| d.scene.as_ref()?.camera)
                .unwrap_or_default(),
        );
        self.shown = None;
    }

    /// Writes state.json when what the user sees changed, for Claude to read.
    fn write_state(&mut self) {
        let d = self.diagram.as_ref();
        let state = serde_json::json!({
            "mode": self.mode.name(),
            "file": self.active.as_ref().map(|p| p.display().to_string()),
            "previous": self.history.last().map(|p| p.display().to_string()),
            "title": d.map(|d| d.title.clone()),
            "camera": { "yaw": self.camera.yaw.to_degrees().round(), "pitch": self.camera.pitch.to_degrees().round(), "zoom": (self.camera.zoom * 100.0).round() / 100.0 },
            "errors": self.errors,
        });
        let text = serde_json::to_string_pretty(&state).unwrap_or_default();
        if text != self.last_state {
            let _ = std::fs::write(self.dir.join("state.json"), &text);
            self.last_state = text;
        }
    }

    fn render(&mut self, scene: &poly3d::SpecScene, area: Rect) -> Option<RgbaImage> {
        let picker = self.picker.as_ref()?;
        let font = picker.font_size();
        let (mut w, mut h) = (
            area.width as u32 * font.width as u32,
            area.height as u32 * font.height as u32,
        );
        let k = (MAX_PX.0 as f64 / w as f64)
            .min(MAX_PX.1 as f64 / h as f64)
            .min(1.0);
        w = ((w as f64 * k) as u32).max(8);
        h = ((h as f64 * k) as u32).max(8);
        let phase = self.start.elapsed().as_secs_f64() / FLOW_SECS;
        let img = poly3d::render_spec(scene, &self.camera, phase, w as usize, h as usize, BG);
        poly3d::set_user_marks(Vec::new());
        Some(img)
    }

    fn picture_key(&self, area: Rect) -> u64 {
        use std::hash::{Hash, Hasher};
        let mut hs = std::collections::hash_map::DefaultHasher::new();
        self.active.hash(&mut hs);
        self.cur().map(|i| self.files[i].mtime).hash(&mut hs);
        for v in [self.camera.yaw, self.camera.pitch, self.camera.zoom] {
            ((v * 1000.0).round() as i64).hash(&mut hs);
        }
        if self.animating() {
            (self.start.elapsed().as_millis() / FRAME.as_millis()).hash(&mut hs);
        }
        (area.width, area.height).hash(&mut hs);
        hs.finish()
    }

    fn draw_picture(&mut self, frame: &mut Frame, area: Rect, scene: &Scene) {
        if area.width < 4 || area.height < 2 {
            return;
        }
        let key = (
            self.picture_key(area),
            area.width as u32,
            area.height as u32,
        );
        if self.shown.as_ref().is_none_or(|s| s.key != key) {
            let poly = z_spec::to_poly(scene);
            if let Some(img) = self.render(&poly, area) {
                let id = IMAGE_IDS[(self.frames % 2) as usize];
                self.frames += 1;
                if let Some(p) = self.picker.as_ref() {
                    self.shown = Some(Shown {
                        key,
                        proto: protocol(p, DynamicImage::ImageRgba8(img), id),
                    });
                }
            }
        }
        if let Some(s) = self.shown.as_mut() {
            frame.render_stateful_widget(
                StatefulImage::default().resize(Resize::Scale(None)),
                area,
                &mut s.proto,
            );
        }
    }

    fn art_lines(&self, art: &[String]) -> Vec<Line<'static>> {
        let t = &self.theme;
        art.iter()
            .map(|row| {
                let mut spans: Vec<Span<'static>> = Vec::new();
                let mut buf = String::new();
                let mut frame_run = false;
                for c in row.chars() {
                    let f = is_frame_glyph(c);
                    if f != frame_run && !buf.is_empty() {
                        spans.push(Span::styled(
                            std::mem::take(&mut buf),
                            if frame_run { t.accent() } else { t.base() },
                        ));
                    }
                    frame_run = f;
                    buf.push(c);
                }
                if !buf.is_empty() {
                    spans.push(Span::styled(
                        buf,
                        if frame_run { t.accent() } else { t.base() },
                    ));
                }
                Line::from(spans)
            })
            .collect()
    }

    fn draw_canvas(&mut self, frame: &mut Frame, area: Rect) {
        let t = self.theme.clone();
        let n = self.files.len();
        let at = self.cur();
        let name = self.active.as_deref().map(file_name).unwrap_or_default();
        let title = match self.current() {
            Some((title, ..)) => title,
            None => "no diagram yet".into(),
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(if self.window_ref().focus && self.window_ref().open {
                t.dim()
            } else {
                t.accent()
            })
            .title(Span::styled(
                format!(" Z · {} · {title} ", self.mode.name()),
                t.title(),
            ))
            .title(
                Line::from(Span::styled(
                    format!(" {name} {}/{n} ", at.map_or(0, |i| i + 1)),
                    t.dim(),
                ))
                .right_aligned(),
            );
        let inner = block.inner(area);
        frame.render_widget(block, area);

        let Some((_, art, scene, caption, _text)) = self.current() else {
            let mut lines = vec![
                Line::raw(""),
                Line::styled("  No diagrams yet.", t.title()),
                Line::raw(""),
                Line::styled(
                    "  Press C and ask Claude something; it draws here when a picture helps.",
                    t.base(),
                ),
                Line::styled(format!("  Files go in {}", self.dir.display()), t.dim()),
            ];
            for e in &self.errors {
                lines.push(Line::styled(format!("  {e}"), t.down()));
            }
            frame.render_widget(Paragraph::new(lines).style(t.base()), inner);
            return;
        };
        let (art, scene, caption) = (art.to_vec(), scene.cloned(), caption.to_string());

        // Only parse errors go under the picture; the diagram's text is not shown.
        let text_h = if self.full || self.errors.is_empty() {
            0
        } else {
            (inner.height / 4).max(3)
        };
        let [pic, cap, body] = Layout::vertical([
            Constraint::Min(3),
            Constraint::Length(u16::from(!caption.is_empty())),
            Constraint::Length(text_h),
        ])
        .areas(inner);

        let show_art = !art.is_empty() && (scene.is_none() || self.art_first);
        if show_art {
            let lines = self.art_lines(&art);
            let h = lines.len() as u16;
            let y = pic.y + pic.height.saturating_sub(h) / 2;
            let w = art
                .iter()
                .map(|r| unicode_width::UnicodeWidthStr::width(r.as_str()))
                .max()
                .unwrap_or(0) as u16;
            let x = pic.x + pic.width.saturating_sub(w) / 2;
            let r = Rect::new(x, y, w.min(pic.width), h.min(pic.height));
            frame.render_widget(Paragraph::new(lines).style(t.base()), r);
        } else if let Some(s) = &scene {
            self.draw_picture(frame, pic, s);
        }
        if !caption.is_empty() {
            frame.render_widget(
                Paragraph::new(Line::styled(caption, t.dim())).centered(),
                cap,
            );
        }
        if text_h > 0 {
            let lines: Vec<Line> = self
                .errors
                .iter()
                .map(|e| Line::styled(format!("✗ {e}"), t.down()))
                .collect();
            let body_block = Block::new().borders(Borders::TOP).border_style(t.dim());
            frame.render_widget(
                Paragraph::new(lines)
                    .block(body_block)
                    .wrap(Wrap { trim: false })
                    .scroll((self.scroll, 0))
                    .style(t.base()),
                body,
            );
        }
    }

    fn browse_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let step = 0.12;
        match key.code {
            KeyCode::Char('d') if ctrl => self.scroll = self.scroll.saturating_add(8),
            KeyCode::Char('u') if ctrl => self.scroll = self.scroll.saturating_sub(8),
            KeyCode::Esc | KeyCode::Char('q') => {
                if self.full {
                    self.full = false;
                } else {
                    return Action::Quit;
                }
            }
            KeyCode::Char('C') | KeyCode::Char('i') | KeyCode::Enter => {
                self.full = false;
                self.window().show();
            }
            KeyCode::Char('M') => {
                let i = MODES.iter().position(|m| *m == self.mode).unwrap_or(0);
                self.mode = MODES[(i + 1) % MODES.len()];
                // the new mode's chat is on screen too, with the keys on the canvas
                self.window().open = true;
                self.window().focus = false;
                self.flash(format!("mode: {}", self.mode.name()));
            }
            KeyCode::Char('[') => self.step(-1),
            KeyCode::Char(']') => self.step(1),
            KeyCode::Char('g') => self.open_at(0),
            KeyCode::Char('G') => self.open_at(self.files.len().saturating_sub(1)),
            KeyCode::Char('b') | KeyCode::Backspace => self.back(),
            KeyCode::Char('f') => self.menu = Some(self.cur().unwrap_or(0)),
            KeyCode::Char('h') | KeyCode::Left => self.camera.orbit(-step, 0.0),
            KeyCode::Char('l') | KeyCode::Right => self.camera.orbit(step, 0.0),
            KeyCode::Char('k') | KeyCode::Up => self.camera.orbit(0.0, step),
            KeyCode::Char('j') | KeyCode::Down => self.camera.orbit(0.0, -step),
            KeyCode::Char('+') | KeyCode::Char('=') => self.camera.zoom_by(1.15),
            KeyCode::Char('-') | KeyCode::Char('_') => self.camera.zoom_by(1.0 / 1.15),
            KeyCode::Char('0') => self.reset_camera(),
            KeyCode::Char('F') => self.full = !self.full,
            KeyCode::Char('p') => self.paused = !self.paused,
            KeyCode::Char('v') => {
                self.art_first = !self.art_first;
                self.shown = None;
            }
            KeyCode::Char('J') => self.scroll = self.scroll.saturating_add(1),
            KeyCode::Char('K') => self.scroll = self.scroll.saturating_sub(1),
            KeyCode::Char('r') => self.reload(true),
            _ => {}
        }
        Action::None
    }
}

/// Kitty frames under a fixed id pair (see IMAGE_IDS); anything else as the picker likes.
fn protocol(picker: &Picker, img: DynamicImage, id: u32) -> StatefulProtocol {
    use ratatui_image::picker::Capability;
    use ratatui_image::protocol::StatefulProtocolType;
    use ratatui_image::protocol::kitty::StatefulKitty;
    if picker.protocol_type() != ProtocolType::Kitty {
        return picker.new_resize_protocol(img);
    }
    let caps = picker.capabilities();
    StatefulProtocol::new(
        img,
        picker.font_size(),
        None,
        StatefulProtocolType::Kitty(StatefulKitty::new(
            id,
            picker.tmux_detected(),
            caps.is_empty() || caps.contains(&Capability::KittyCompression),
            caps.contains(&Capability::KittySharedMemory),
        )),
    )
}

const KEYS: &[Key] = &[
    key("C/i/↵", "ask Claude"),
    key("M", "mode"),
    key("f", "diagrams menu"),
    key("b/⌫", "back"),
    key("[/]", "previous / next diagram"),
    key("h/j/k/l", "turn"),
    key("+/=", "zoom in"),
    key("-/_", "zoom out"),
    key("0", "reset the camera"),
    key("v", "art"),
    key("F", "full screen"),
    key("p", "pause / resume"),
    key("J/K", "scroll"),
    key("^d/^u", "scroll 8 lines"),
    key("g/G", "first / last diagram"),
    key("r", "reload"),
    key("ctrl-/", "canvas (from the chat)"),
    key("q/esc", "quit"),
];

impl Screen for Z {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        frame.render_widget(Block::new().style(self.theme.base()), area);
        // The hero picture on top, Claude under it, always on screen; F gives the picture all of it.
        if !self.full {
            let [top, chat] =
                Layout::vertical([Constraint::Min(10), Constraint::Percentage(30)]).areas(area);
            self.draw_canvas(frame, top);
            let label = self.mode.name();
            let t = self.theme.clone();
            self.window().draw(frame, chat, label, &t, Borders::ALL);
        } else {
            self.draw_canvas(frame, area);
        }
        self.draw_menu(frame, area);
        self.write_state();
    }

    fn help(&self) -> Help {
        Help::new("z", KEYS)
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.menu.is_some() {
            return self.menu_key(key);
        }
        let w = self.window_ref();
        if w.open && w.focus {
            self.window().key(key);
            return Action::None;
        }
        self.browse_key(key)
    }

    fn tick(&mut self) -> Action {
        if self.last_watch.elapsed() >= WATCH {
            self.last_watch = Instant::now();
            self.watch(false);
        }
        Action::None
    }

    fn poll_interval(&self) -> Duration {
        if self.animating() {
            FRAME
        } else {
            Duration::from_millis(100)
        }
    }

    fn leader_ok(&self) -> bool {
        !(self.window_ref().open && self.window_ref().focus) && self.menu.is_none()
    }

    fn shows_tape(&self) -> bool {
        false
    }

    fn takes_text(&self) -> bool {
        // typing goes to the Claude window while it has focus
        self.window_ref().open && self.window_ref().focus
    }

    fn flash_text(&self) -> Option<&str> {
        self.flash
            .as_ref()
            .filter(|(_, at)| at.elapsed() < Duration::from_secs(3))
            .map(|(m, _)| m.as_str())
    }

    fn set_flash(&mut self, msg: String) {
        self.flash(msg);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn screen(dir: &Path) -> Z {
        let theme = Theme::default();
        let mut z = Z {
            theme: theme.clone(),
            dir: dir.to_path_buf(),
            files: Vec::new(),
            active: None,
            history: Vec::new(),
            menu: None,
            diagram: None,
            errors: Vec::new(),
            camera: poly3d::View::default(),
            art_first: false,
            full: false,
            paused: false,
            scroll: 0,
            start: Instant::now(),
            last_watch: Instant::now(),
            mode: Mode::Chat,
            windows: MODES
                .iter()
                .map(|m| ClaudeWindow::with(theme.clone(), SOCKET, m.session(), "true".into()))
                .collect(),
            picker: Some(Picker::halfblocks()),
            shown: None,
            frames: 0,
            last_state: String::new(),
            flash: None,
        };
        z.watch(true);
        z
    }

    fn tmp(tag: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("fl-z-test-{tag}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    fn key(c: char) -> KeyEvent {
        KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)
    }

    const SCENE: &str = r#"{"title":"Stack","caption":"cap","scene":{"parts":[
        {"shape":"box","name":"base","at":[0,0,0],"size":[4,1,4]},
        {"shape":"cylinder","name":"post","from":[0,0.5,0],"to":[0,3,0],"r":0.3,"color":"copper"}],
        "flows":[{"name":"current","path":[[0,0,0],[0,3,0]]}]},
        "text":"overview text"}"#;

    #[test]
    fn follows_new_files_and_shows_errors_without_losing_the_picture() {
        let dir = tmp("follow");
        let mut z = screen(&dir);
        assert!(z.diagram.is_none());
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");

        // a broken edit keeps the last good diagram on screen, with the errors
        std::thread::sleep(Duration::from_millis(20));
        std::fs::write(
            dir.join("01-stack.json"),
            r#"{"title":"Stack","scene":{"parts":[{"shape":"cone"}]}}"#,
        )
        .unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        assert!(z.errors[0].contains("shape"), "{:?}", z.errors);

        // the edit is fixed; the canvas picks it up
        std::thread::sleep(Duration::from_millis(20));
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        z.watch(false);
        assert!(z.errors.is_empty());

        // a new file is announced but does not take the canvas
        std::thread::sleep(Duration::from_millis(20));
        std::fs::write(
            dir.join("02-art.json"),
            r#"{"title":"Art","art":["┌┐","└┘"]}"#,
        )
        .unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        assert!(z.flash.as_ref().unwrap().0.contains("02-art.json"));

        // the user moves on with ]; b returns; with no history left, b says so
        z.on_key(key('['));
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        z.on_key(key(']'));
        assert_eq!(z.diagram.as_ref().unwrap().title, "Art");
        z.on_key(key('b'));
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        z.on_key(key('b'));
        assert!(z.flash.as_ref().unwrap().0.contains("no earlier"));
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn a_change_request_opens_the_new_file_and_plain_new_files_do_not() {
        let dir = tmp("open");
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        let mut z = screen(&dir);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");

        // a new file alone stays closed: the user opens it from the menu
        std::thread::sleep(Duration::from_millis(20));
        std::fs::write(
            dir.join("02-art.json"),
            r#"{"title":"Art","art":["┌┐","└┘"]}"#,
        )
        .unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");

        // Claude asked for it: .open names it, the canvas opens it and uses up the request
        std::fs::write(dir.join(OPEN_MARK), "02-art.json\n").unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Art");
        assert!(!dir.join(OPEN_MARK).exists());
        z.on_key(key('b'));
        assert_eq!(
            z.diagram.as_ref().unwrap().title,
            "Stack",
            "b returns to the diagram before"
        );

        // a request for a file not written yet waits for it
        std::fs::write(dir.join(OPEN_MARK), "03-later.json").unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        assert!(dir.join(OPEN_MARK).exists());
        std::fs::write(dir.join("03-later.json"), r#"{"title":"Later","text":"t"}"#).unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Later");
        assert!(!dir.join(OPEN_MARK).exists());
        let _ = std::fs::remove_dir_all(&dir);
    }

    fn code(c: KeyCode) -> KeyEvent {
        KeyEvent::new(c, KeyModifiers::NONE)
    }

    #[test]
    fn f_menu_lists_every_diagram_and_enter_opens_one() {
        let dir = tmp("menu");
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        std::fs::write(
            dir.join("02-art.json"),
            r#"{"title":"Art","art":["┌┐","└┘"]}"#,
        )
        .unwrap();
        std::fs::write(dir.join("03-broken.json"), "{ nope").unwrap();
        let mut z = screen(&dir);
        z.show(dir.join("01-stack.json"));

        // f opens the menu on the active row; arrows move and clamp; enter opens and closes
        z.on_key(key('f'));
        assert_eq!(z.menu, Some(0));
        for _ in 0..3 {
            z.on_key(code(KeyCode::Down));
        }
        assert_eq!(z.menu, Some(2), "clamps at the last row");
        z.on_key(code(KeyCode::Enter));
        assert_eq!(z.menu, None);
        assert!(z.active.as_ref().unwrap().ends_with("03-broken.json"));
        assert!(!z.errors.is_empty(), "a broken file opens with its errors");

        // b goes back to the diagram the menu replaced
        z.on_key(key('b'));
        assert!(z.active.as_ref().unwrap().ends_with("01-stack.json"));
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");

        // the menu draws every file, marks the active one, and the state file says which it is
        let mut term = Terminal::new(TestBackend::new(100, 40)).unwrap();
        z.on_key(key('f'));
        term.draw(|f| z.draw(f)).unwrap();
        let s: String = term
            .backend()
            .buffer()
            .content()
            .iter()
            .map(|c| c.symbol())
            .collect();
        assert!(
            s.contains("01-stack.json")
                && s.contains("02-art.json")
                && s.contains("03-broken.json"),
            "{s}"
        );
        assert!(s.contains("● "), "{s}");
        let state: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(dir.join("state.json")).unwrap())
                .unwrap();
        assert!(state["file"].as_str().unwrap().ends_with("01-stack.json"));
        assert!(
            state["previous"].is_null(),
            "back popped the only entry: {state}"
        );
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn draws_one_picture_with_its_caption_and_no_key_labels() {
        let dir = tmp("keys");
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        let mut z = screen(&dir);
        let mut term = Terminal::new(TestBackend::new(100, 40)).unwrap();
        term.draw(|f| z.draw(f)).unwrap();
        let s: String = term
            .backend()
            .buffer()
            .content()
            .iter()
            .map(|c| c.symbol())
            .collect();
        assert!(s.contains("cap") && !s.contains("overview text"), "{s}");
        // no section or zoom keys do anything any more: nothing to open, nothing to print
        for c in ['1', 'a', 'o'] {
            z.on_key(key(c));
        }
        assert!(z.active.is_some());
        assert_eq!(z.on_key(key('q')), Action::Quit);

        let state: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(dir.join("state.json")).unwrap())
                .unwrap();
        assert_eq!(state["title"], "Stack");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn mode_switch_keeps_one_window_per_mode() {
        let dir = tmp("mode");
        let mut z = screen(&dir);
        z.on_key(key('M'));
        assert_eq!(z.mode, Mode::Build);
        z.on_key(key('M'));
        z.on_key(key('M'));
        assert_eq!(z.mode, Mode::Chat);
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn prompt_names_the_folder_and_mode() {
        let dir = tmp("prompt");
        let p = prompt_file(&dir, Mode::Quiz).unwrap();
        let text = std::fs::read_to_string(p).unwrap();
        assert!(text.contains(&dir.display().to_string()) && text.contains("Mode: quiz"));
        let cmd = claude_command(&dir, &dir.join(".prompt-quiz.md"));
        assert!(cmd.contains("fl z check") && cmd.contains("--append-system-prompt"));
        let _ = std::fs::remove_dir_all(&dir);
    }
}
