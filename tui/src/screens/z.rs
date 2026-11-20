// Z: diagrams built in the chat. The left pane is a canvas showing the newest diagram in
// the Z folder (`data/z/*.json`, format in z_spec.rs); the right pane is Claude Code
// itself, running in a tmux session (one per mode, so switching modes keeps each
// conversation). Claude writes diagram files while it talks; the canvas hot-reloads them.
// The canvas writes `state.json` (what the user is looking at) for Claude to read.
//
// Keys mirror the Diagrams screen: hjkl orbit, +/- zoom, 0 reset, 1-9 sections, a-e
// zooms, o overview, F full picture, [ ] previous/next diagram. `C` gives Claude the keys;
// ctrl-] takes them back. `M` switches mode (chat, build, quiz).

use std::io;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};

use image::{DynamicImage, RgbaImage};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use ratatui_image::picker::{Picker, ProtocolType};
use ratatui_image::protocol::StatefulProtocol;
use ratatui_image::{Resize, StatefulImage};

use super::diagrams_window::ClaudeWindow;
use super::z_spec::{self, Camera, Diagram, Scene};
use crate::app::{Action, Ctx, Screen};
use crate::ui::theme::Theme;

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
const IMAGE_IDS: [u32; 2] = [u32::from_be_bytes([0, 0xF3, 0x2A, 0x01]), u32::from_be_bytes([0, 0xF3, 0x2A, 0x02])];

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
                 geometry). When a diagram carries the explanation, keep the chat reply short and \
                 point at sections and keys."
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
                 why, add a section that explains it, then go on or go deeper."
            }
        }
    }
}

/// Which picture the canvas shows.
#[derive(Clone, Copy, PartialEq, Debug)]
enum View {
    Overview,
    Zoom(char),
}

/// The picture on screen and what it was drawn from.
struct Shown {
    key: (u64, u32, u32),
    proto: StatefulProtocol,
}

pub struct Z {
    theme: Theme,
    dir: PathBuf,
    /// Diagram files, in name order, with the mtime each had when last listed.
    files: Vec<(PathBuf, SystemTime)>,
    cur: usize,
    /// The diagram on the canvas: the last version of the file that parsed.
    diagram: Option<Diagram>,
    /// Why the current file did not parse, when it did not.
    errors: Vec<String>,
    view: View,
    section: Option<usize>,
    camera: poly3d::View,
    /// Show the art instead of the scene, when a view has both.
    art_first: bool,
    full: bool,
    paused: bool,
    scroll: u16,
    start: Instant,
    last_watch: Instant,
    /// Newest mtime seen in the folder: a newer file is followed.
    newest: SystemTime,
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
            Ok(ClaudeWindow::with(ctx.theme.clone(), SOCKET, m.session(), claude_command(&dir, &prompt)))
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
        cur: 0,
        diagram: None,
        errors: Vec::new(),
        view: View::Overview,
        section: None,
        camera: poly3d::View::default(),
        art_first: false,
        full: false,
        paused: false,
        scroll: 0,
        start: Instant::now(),
        last_watch: Instant::now(),
        newest: SystemTime::UNIX_EPOCH,
        mode: Mode::Chat,
        windows,
        picker,
        shown: None,
        frames: 0,
        last_state: String::new(),
        flash: None,
    };
    z.watch(true);
    if let Some(a) = arg.as_deref().map(str::to_lowercase) {
        if let Some(m) = MODES.iter().find(|m| m.name() == a) {
            z.mode = *m;
        } else if let Some(i) = z.files.iter().position(|(p, _)| file_name(p).to_lowercase().contains(&a)) {
            z.select(i);
        }
    }
    Ok(z)
}

fn file_name(p: &Path) -> String {
    p.file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default()
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

    /// Re-lists the folder. Follows a file that is newer than any seen before (Claude just
    /// wrote it), and reloads the current file when it changed.
    fn watch(&mut self, first: bool) {
        let files = list(&self.dir);
        let cur_path = self.files.get(self.cur).map(|f| f.0.clone());
        let cur_changed = cur_path.as_ref().is_some_and(|p| {
            let old = self.files.iter().find(|f| &f.0 == p).map(|f| f.1);
            let new = files.iter().find(|f| &f.0 == p).map(|f| f.1);
            old != new
        });
        let newest = files.iter().max_by_key(|f| f.1).cloned();
        self.files = files;
        if let Some((p, m)) = newest {
            if m > self.newest {
                self.newest = m;
                if first || Some(&p) != cur_path.as_ref() {
                    let i = self.files.iter().position(|f| f.0 == p).unwrap_or(0);
                    self.select(i);
                    if !first {
                        self.flash(format!("new: {}", file_name(&p)));
                    }
                    return;
                }
            }
        }
        match cur_path.and_then(|p| self.files.iter().position(|f| f.0 == p)) {
            Some(i) => {
                self.cur = i;
                if cur_changed {
                    self.reload(true);
                }
            }
            None if !self.files.is_empty() => self.select(self.cur.min(self.files.len() - 1)),
            None => {
                self.diagram = None;
                self.errors.clear();
            }
        }
    }

    fn select(&mut self, i: usize) {
        self.cur = i;
        self.reload(false);
    }

    /// Loads the current file. `keep` keeps the camera and the open view (the same file
    /// was edited); otherwise the view starts at the diagram's own camera.
    fn reload(&mut self, keep: bool) {
        let Some((path, _)) = self.files.get(self.cur) else {
            return;
        };
        match z_spec::load(path) {
            Ok(d) => {
                self.errors.clear();
                if !keep {
                    self.view = View::Overview;
                    self.section = None;
                    self.scroll = 0;
                    self.art_first = false;
                    self.camera = camera_view(d.scene.as_ref().and_then(|s| s.camera).unwrap_or_default());
                } else {
                    if let View::Zoom(k) = self.view {
                        if !d.zooms.iter().any(|z| z.key.starts_with(k)) {
                            self.view = View::Overview;
                        }
                    }
                    if self.section.is_some_and(|s| s >= d.sections.len()) {
                        self.section = None;
                    }
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

    /// The picture, caption and text of what is open: (title, art, scene, caption, text).
    fn current(&self) -> Option<(String, &[String], Option<&Scene>, &str, &str)> {
        let d = self.diagram.as_ref()?;
        let zoom_key = match (self.view, self.section.and_then(|i| d.sections.get(i))) {
            (View::Zoom(k), _) => Some(k),
            (_, Some(s)) => s.zoom.as_deref().and_then(|z| z.chars().next()),
            _ => None,
        };
        let zoom = zoom_key.and_then(|k| d.zooms.iter().find(|z| z.key.starts_with(k)));
        let (title, art, scene, caption, mut text) = match zoom {
            Some(z) => (format!("{} › {}", d.title, z.title), &z.art[..], z.scene.as_ref(), z.caption.as_str(), z.text.as_str()),
            None => (d.title.clone(), &d.art[..], d.scene.as_ref(), d.caption.as_str(), d.text.as_str()),
        };
        if let Some(s) = self.section.and_then(|i| d.sections.get(i)) {
            text = s.text.as_str();
        }
        Some((title, art, scene, caption, text))
    }

    fn focus(&self) -> Vec<String> {
        let d = self.diagram.as_ref();
        self.section
            .and_then(|i| d?.sections.get(i))
            .map(|s| s.focus.clone())
            .unwrap_or_default()
    }

    fn animating(&self) -> bool {
        !self.paused
            && self
                .current()
                .is_some_and(|(_, art, scene, ..)| scene.is_some_and(|s| !s.flows.is_empty()) && !(self.art_first && !art.is_empty()))
    }

    fn open_section(&mut self, i: usize) {
        let Some(d) = self.diagram.as_ref() else { return };
        let Some(s) = d.sections.get(i) else {
            self.flash(format!("no section {}", i + 1));
            return;
        };
        if let Some(c) = s.camera {
            self.camera = camera_view(c);
        }
        if s.zoom.is_some() {
            self.view = View::Overview;
        }
        self.section = Some(i);
        self.scroll = 0;
        self.shown = None;
    }

    fn open_zoom(&mut self, k: char) {
        let Some(d) = self.diagram.as_ref() else { return };
        let Some(z) = d.zooms.iter().find(|z| z.key.starts_with(k)) else {
            self.flash(format!("no zoom {k}"));
            return;
        };
        let cam = z.scene.as_ref().and_then(|s| s.camera).unwrap_or_default();
        self.view = View::Zoom(k);
        self.section = None;
        self.scroll = 0;
        self.camera = camera_view(cam);
        self.shown = None;
    }

    fn overview(&mut self) {
        self.view = View::Overview;
        self.section = None;
        self.scroll = 0;
        self.camera = camera_view(self.diagram.as_ref().and_then(|d| d.scene.as_ref()?.camera).unwrap_or_default());
        self.shown = None;
    }

    /// Writes state.json when what the user sees changed, for Claude to read.
    fn write_state(&mut self) {
        let d = self.diagram.as_ref();
        let state = serde_json::json!({
            "mode": self.mode.name(),
            "file": self.files.get(self.cur).map(|f| f.0.display().to_string()),
            "title": d.map(|d| d.title.clone()),
            "view": match self.view { View::Overview => "overview".to_string(), View::Zoom(k) => k.to_string() },
            "section": self.section.map(|i| i + 1),
            "section_title": self.section.and_then(|i| d?.sections.get(i)).map(|s| s.title.clone()),
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
        let (mut w, mut h) = (area.width as u32 * font.width as u32, area.height as u32 * font.height as u32);
        let k = (MAX_PX.0 as f64 / w as f64).min(MAX_PX.1 as f64 / h as f64).min(1.0);
        w = ((w as f64 * k) as u32).max(8);
        h = ((h as f64 * k) as u32).max(8);
        let phase = self.start.elapsed().as_secs_f64() / FLOW_SECS;
        poly3d::set_user_marks(self.focus());
        let img = poly3d::render_spec(scene, &self.camera, phase, w as usize, h as usize, BG);
        poly3d::set_user_marks(Vec::new());
        Some(img)
    }

    fn picture_key(&self, area: Rect) -> u64 {
        use std::hash::{Hash, Hasher};
        let mut hs = std::collections::hash_map::DefaultHasher::new();
        self.cur.hash(&mut hs);
        format!("{:?}{:?}{:?}", self.view, self.section, self.files.get(self.cur).map(|f| f.1)).hash(&mut hs);
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
        let key = (self.picture_key(area), area.width as u32, area.height as u32);
        if self.shown.as_ref().is_none_or(|s| s.key != key) {
            let poly = z_spec::to_poly(scene);
            if let Some(img) = self.render(&poly, area) {
                let id = IMAGE_IDS[(self.frames % 2) as usize];
                self.frames += 1;
                if let Some(p) = self.picker.as_ref() {
                    self.shown = Some(Shown { key, proto: protocol(p, DynamicImage::ImageRgba8(img), id) });
                }
            }
        }
        if let Some(s) = self.shown.as_mut() {
            frame.render_stateful_widget(StatefulImage::default().resize(Resize::Scale(None)), area, &mut s.proto);
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
                        spans.push(Span::styled(std::mem::take(&mut buf), if frame_run { t.accent() } else { t.base() }));
                    }
                    frame_run = f;
                    buf.push(c);
                }
                if !buf.is_empty() {
                    spans.push(Span::styled(buf, if frame_run { t.accent() } else { t.base() }));
                }
                Line::from(spans)
            })
            .collect()
    }

    /// The tab row: overview, zooms, sections; the open one highlighted.
    fn tabs(&self) -> Line<'static> {
        let t = &self.theme;
        let Some(d) = self.diagram.as_ref() else {
            return Line::default();
        };
        let mut spans = Vec::new();
        let on = |b: bool| if b { t.selected() } else { t.dim() };
        spans.push(Span::styled(" o overview ", on(self.view == View::Overview && self.section.is_none())));
        for z in &d.zooms {
            let k = z.key.chars().next().unwrap_or('?');
            spans.push(Span::styled(format!(" {k} {} ", z.title), on(self.view == View::Zoom(k))));
        }
        if !d.sections.is_empty() {
            spans.push(Span::styled(" │", t.dim()));
        }
        for (i, s) in d.sections.iter().enumerate() {
            spans.push(Span::styled(format!(" {} {} ", i + 1, s.title), on(self.section == Some(i))));
        }
        Line::from(spans)
    }

    fn draw_canvas(&mut self, frame: &mut Frame, area: Rect) {
        let t = self.theme.clone();
        let n = self.files.len();
        let name = self.files.get(self.cur).map(|f| file_name(&f.0)).unwrap_or_default();
        let title = match self.current() {
            Some((title, ..)) => title,
            None => "no diagram yet".into(),
        };
        let hint = if self.window_ref().open && self.window_ref().focus {
            " ctrl-] canvas ".to_string()
        } else {
            " C claude  M mode  [ ] diagram  hjkl turn  1-9 a-e o  F full  q back ".to_string()
        };
        let flash = self.flash.as_ref().filter(|(_, at)| at.elapsed() < Duration::from_secs(3)).map(|(m, _)| m.clone());
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(if self.window_ref().focus && self.window_ref().open { t.dim() } else { t.accent() })
            .title(Span::styled(format!(" Z · {} · {title} ", self.mode.name()), t.title()))
            .title(Line::from(Span::styled(format!(" {name} {}/{n} ", if n == 0 { 0 } else { self.cur + 1 }), t.dim())).right_aligned())
            .title_bottom(Span::styled(flash.map(|f| format!(" {f} ")).unwrap_or(hint), t.dim()));
        let inner = block.inner(area);
        frame.render_widget(block, area);

        let Some((_, art, scene, caption, text)) = self.current() else {
            let mut lines = vec![
                Line::raw(""),
                Line::styled("  No diagrams yet.", t.title()),
                Line::raw(""),
                Line::styled("  Press C and ask Claude something; it draws here when a picture helps.", t.base()),
                Line::styled(format!("  Files go in {}", self.dir.display()), t.dim()),
            ];
            for e in &self.errors {
                lines.push(Line::styled(format!("  {e}"), t.down()));
            }
            frame.render_widget(Paragraph::new(lines).style(t.base()), inner);
            return;
        };
        let (art, scene, caption, text) = (art.to_vec(), scene.cloned(), caption.to_string(), text.to_string());

        let text_h = if self.full || text.trim().is_empty() && self.errors.is_empty() {
            0
        } else {
            (inner.height / 3).max(4)
        };
        let [tabs, pic, cap, body] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(u16::from(!caption.is_empty())),
            Constraint::Length(text_h),
        ])
        .areas(inner);
        frame.render_widget(Paragraph::new(self.tabs()).style(t.base()), tabs);

        let show_art = !art.is_empty() && (scene.is_none() || self.art_first);
        if show_art {
            let lines = self.art_lines(&art);
            let h = lines.len() as u16;
            let y = pic.y + pic.height.saturating_sub(h) / 2;
            let w = art.iter().map(|r| unicode_width::UnicodeWidthStr::width(r.as_str())).max().unwrap_or(0) as u16;
            let x = pic.x + pic.width.saturating_sub(w) / 2;
            let r = Rect::new(x, y, w.min(pic.width), h.min(pic.height));
            frame.render_widget(Paragraph::new(lines).style(t.base()), r);
        } else if let Some(s) = &scene {
            self.draw_picture(frame, pic, s);
        }
        if !caption.is_empty() {
            frame.render_widget(Paragraph::new(Line::styled(caption, t.dim())).centered(), cap);
        }
        if text_h > 0 {
            let mut lines: Vec<Line> = self.errors.iter().map(|e| Line::styled(format!("✗ {e}"), t.down())).collect();
            if !lines.is_empty() {
                lines.push(Line::raw(""));
            }
            if let Some(s) = self.section.and_then(|i| self.diagram.as_ref()?.sections.get(i)) {
                lines.push(Line::styled(format!("{} {}", self.section.unwrap_or(0) + 1, s.title), t.title()));
            }
            lines.extend(text.lines().map(|l| Line::styled(l.to_string(), t.base())));
            let body_block = Block::new().borders(Borders::TOP).border_style(t.dim());
            frame.render_widget(
                Paragraph::new(lines).block(body_block).wrap(Wrap { trim: false }).scroll((self.scroll, 0)).style(t.base()),
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
                if self.window_ref().open {
                    self.window().open = false;
                } else if self.full {
                    self.full = false;
                } else if self.view != View::Overview || self.section.is_some() {
                    self.overview();
                } else {
                    return Action::Quit;
                }
            }
            KeyCode::Char('C') | KeyCode::Char('i') | KeyCode::Enter => {
                self.full = false;
                self.window().show();
            }
            KeyCode::Char('M') => {
                let was_open = self.window_ref().open;
                let i = MODES.iter().position(|m| *m == self.mode).unwrap_or(0);
                self.window().open = false;
                self.mode = MODES[(i + 1) % MODES.len()];
                if was_open {
                    self.window().open = true;
                    self.window().focus = false;
                }
                self.flash(format!("mode: {}", self.mode.name()));
            }
            KeyCode::Char('[') if self.cur > 0 => self.select(self.cur - 1),
            KeyCode::Char(']') if self.cur + 1 < self.files.len() => self.select(self.cur + 1),
            KeyCode::Char('g') if !self.files.is_empty() => self.select(0),
            KeyCode::Char('G') if !self.files.is_empty() => self.select(self.files.len() - 1),
            KeyCode::Char('h') | KeyCode::Left => self.camera.orbit(-step, 0.0),
            KeyCode::Char('l') | KeyCode::Right => self.camera.orbit(step, 0.0),
            KeyCode::Char('k') | KeyCode::Up => self.camera.orbit(0.0, step),
            KeyCode::Char('j') | KeyCode::Down => self.camera.orbit(0.0, -step),
            KeyCode::Char('+') | KeyCode::Char('=') => self.camera.zoom_by(1.15),
            KeyCode::Char('-') | KeyCode::Char('_') => self.camera.zoom_by(1.0 / 1.15),
            KeyCode::Char('0') => {
                let cam = match self.view {
                    View::Zoom(k) => self.diagram.as_ref().and_then(|d| d.zooms.iter().find(|z| z.key.starts_with(k))?.scene.as_ref()?.camera),
                    View::Overview => self.diagram.as_ref().and_then(|d| d.scene.as_ref()?.camera),
                };
                self.camera = camera_view(cam.unwrap_or_default());
            }
            KeyCode::Char(c @ '1'..='9') => self.open_section(c as usize - '1' as usize),
            KeyCode::Char(c @ 'a'..='e') => self.open_zoom(c),
            KeyCode::Char('o') => self.overview(),
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

impl Screen for Z {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        frame.render_widget(Block::new().style(self.theme.base()), area);
        let claude = self.window_ref().open && !self.full;
        if claude {
            let [left, right] = Layout::horizontal([Constraint::Percentage(56), Constraint::Percentage(44)]).areas(area);
            self.draw_canvas(frame, left);
            let label = self.mode.name();
            let t = self.theme.clone();
            self.window().draw(frame, right, label, &t);
        } else {
            self.draw_canvas(frame, area);
        }
        self.write_state();
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
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
        if self.animating() { FRAME } else { Duration::from_millis(100) }
    }

    fn leader_ok(&self) -> bool {
        !(self.window_ref().open && self.window_ref().focus)
    }

    fn shows_tape(&self) -> bool {
        false
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
            cur: 0,
            diagram: None,
            errors: Vec::new(),
            view: View::Overview,
            section: None,
            camera: poly3d::View::default(),
            art_first: false,
            full: false,
            paused: false,
            scroll: 0,
            start: Instant::now(),
            last_watch: Instant::now(),
            newest: SystemTime::UNIX_EPOCH,
            mode: Mode::Chat,
            windows: MODES.iter().map(|m| ClaudeWindow::with(theme.clone(), SOCKET, m.session(), "true".into())).collect(),
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
        "text":"overview text","sections":[{"title":"Post","text":"post text","focus":["post"],"camera":{"yaw":90}}],
        "zooms":[{"key":"a","title":"Detail","art":["┌──┐","│ab│","└──┘"],"text":"zoom text"}]}"#;

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
        std::fs::write(dir.join("01-stack.json"), r#"{"title":"Stack","scene":{"parts":[{"shape":"cone"}]}}"#).unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Stack");
        assert!(z.errors[0].contains("shape"), "{:?}", z.errors);

        // a newer file is followed
        std::thread::sleep(Duration::from_millis(20));
        std::fs::write(dir.join("02-art.json"), r#"{"title":"Art","art":["┌┐","└┘"]}"#).unwrap();
        z.watch(false);
        assert_eq!(z.diagram.as_ref().unwrap().title, "Art");
        z.on_key(key('['));
        assert_eq!(z.cur, 0);
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn keys_open_sections_and_zooms_and_draw() {
        let dir = tmp("keys");
        std::fs::write(dir.join("01-stack.json"), SCENE).unwrap();
        let mut z = screen(&dir);
        let mut term = Terminal::new(TestBackend::new(100, 40)).unwrap();
        term.draw(|f| z.draw(f)).unwrap();
        let screen_text = |term: &Terminal<TestBackend>| {
            term.backend().buffer().content().iter().map(|c| c.symbol()).collect::<String>()
        };
        assert!(screen_text(&term).contains("overview text"));

        z.on_key(key('1'));
        assert_eq!(z.section, Some(0));
        assert!((z.camera.yaw - 90f64.to_radians()).abs() < 1e-9);
        assert_eq!(z.focus(), vec!["post".to_string()]);
        term.draw(|f| z.draw(f)).unwrap();
        assert!(screen_text(&term).contains("post text"));

        z.on_key(key('a'));
        assert_eq!(z.view, View::Zoom('a'));
        term.draw(|f| z.draw(f)).unwrap();
        let s = screen_text(&term);
        assert!(s.contains("zoom text") && s.contains("│ab│"), "{s}");

        z.on_key(key('q'));
        assert_eq!(z.view, View::Overview);
        assert_eq!(z.on_key(key('q')), Action::Quit);

        let state: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(dir.join("state.json")).unwrap()).unwrap();
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
