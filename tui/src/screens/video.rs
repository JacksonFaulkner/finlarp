// `fl video [name]`: plays the screen recordings in docs/screens/*.gif inside the terminal.
//
//   fl video                    browse the clips, playing the first
//   fl video diagrams_power     open on the clip whose name starts with "diagrams_power"
//
// Frames are drawn through the terminal's graphics protocol (kitty, iTerm2, sixel) when it has
// one, and as half-block characters otherwise. Set FL_SCREENS_DIR to play clips from another dir.

use std::fs::{self, File};
use std::io::{self, BufReader};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use image::codecs::gif::GifDecoder;
use image::{AnimationDecoder, DynamicImage};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::Line;
use ratatui::widgets::{Block, Paragraph};
use ratatui_image::picker::Picker;
use ratatui_image::protocol::StatefulProtocol;
use ratatui_image::{Resize, StatefulImage};

use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{Key, key, render_footer};
use crate::ui::theme::Theme;

const KEYS: &[Key] = &[
    key("space", "play / pause"),
    key("h/l", "previous / next frame"),
    key("j/k", "next / previous clip"),
    key("q", "back"),
];

/// Redraw and tick interval while a clip plays (~30 fps polling; frames advance on their own delay).
const POLL: Duration = Duration::from_millis(30);

/// Where the recordings live: FL_SCREENS_DIR, else the repo's docs/screens.
fn screens_dir() -> PathBuf {
    std::env::var_os("FL_SCREENS_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../docs/screens")))
}

/// Every GIF in `dir`, sorted by name.
fn list_clips(dir: &Path) -> io::Result<Vec<PathBuf>> {
    let mut clips: Vec<PathBuf> = fs::read_dir(dir)?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|x| x == "gif"))
        .collect();
    clips.sort();
    Ok(clips)
}

/// A decoded clip: each frame's pixels and how long it stays up.
struct Decoded {
    frames: Vec<DynamicImage>,
    delays: Vec<Duration>,
}

fn decode(path: &Path) -> io::Result<Decoded> {
    let decoder = GifDecoder::new(BufReader::new(File::open(path)?)).map_err(io::Error::other)?;
    let raw = decoder
        .into_frames()
        .collect_frames()
        .map_err(io::Error::other)?;
    let delays = raw.iter().map(|f| Duration::from(f.delay())).collect();
    let frames = raw
        .into_iter()
        .map(|f| DynamicImage::ImageRgba8(f.into_buffer()))
        .collect();
    Ok(Decoded { frames, delays })
}

pub struct Video {
    theme: Theme,
    picker: Picker,
    clips: Vec<PathBuf>,
    /// Index into `clips` of the clip on screen.
    sel: usize,
    /// The decoded clip on screen; decoded again when the selection changes.
    clip: Option<Decoded>,
    /// Current frame, and how long it has been up.
    frame: usize,
    held: Duration,
    last: Instant,
    paused: bool,
    /// The graphics-protocol encoding of `frame`, rebuilt when the frame changes.
    proto: Option<(usize, StatefulProtocol)>,
    error: Option<String>,
}

/// Opens the viewer on the clip whose name starts with `arg` (default: the first clip).
pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Video> {
    let dir = screens_dir();
    let clips = list_clips(&dir)?;
    let sel = arg
        .as_deref()
        .map(str::to_lowercase)
        .and_then(|a| {
            clips.iter().position(|p| {
                p.file_stem()
                    .is_some_and(|s| s.to_string_lossy().to_lowercase().starts_with(&a))
            })
        })
        .unwrap_or(0);
    // Must run before the event loop reads stdin: the terminal answers the query on stdin.
    let picker = Picker::from_query_stdio().unwrap_or_else(|_| Picker::halfblocks());
    let mut video = Video {
        theme: ctx.theme,
        picker,
        clips,
        sel,
        clip: None,
        frame: 0,
        held: Duration::ZERO,
        last: Instant::now(),
        paused: false,
        proto: None,
        error: None,
    };
    video.load();
    Ok(video)
}

impl Video {
    fn load(&mut self) {
        self.frame = 0;
        self.held = Duration::ZERO;
        self.proto = None;
        self.clip = None;
        let Some(path) = self.clips.get(self.sel) else {
            self.error = Some(format!("no .gif clips in {}", screens_dir().display()));
            return;
        };
        match decode(path) {
            Ok(d) if !d.frames.is_empty() => {
                self.clip = Some(d);
                self.error = None;
            }
            Ok(_) => self.error = Some(format!("{} has no frames", path.display())),
            Err(e) => self.error = Some(format!("{}: {e}", path.display())),
        }
    }

    fn step_clip(&mut self, delta: isize) {
        let n = self.clips.len() as isize;
        if n == 0 {
            return;
        }
        self.sel = (self.sel as isize + delta).rem_euclid(n) as usize;
        self.load();
    }

    fn step_frame(&mut self, delta: isize) {
        let Some(clip) = &self.clip else { return };
        let n = clip.frames.len() as isize;
        self.frame = (self.frame as isize + delta).rem_euclid(n) as usize;
        self.held = Duration::ZERO;
    }

    fn name(&self) -> String {
        self.clips
            .get(self.sel)
            .and_then(|p| p.file_stem())
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_default()
    }

    /// Encodes the current frame for the terminal, once per frame change.
    fn ensure_proto(&mut self) {
        let Some(clip) = &self.clip else { return };
        if self.proto.as_ref().is_some_and(|(i, _)| *i == self.frame) {
            return;
        }
        let img = clip.frames[self.frame].clone();
        let proto = self.picker.new_resize_protocol(img);
        self.proto = Some((self.frame, proto));
    }
}

impl Screen for Video {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, image, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(1),
        ])
        .areas(area);

        let status = match &self.clip {
            Some(clip) => format!(
                "{}  frame {}/{}  {}",
                self.name(),
                self.frame + 1,
                clip.frames.len(),
                if self.paused { "paused" } else { "playing" }
            ),
            None => self.name(),
        };
        frame.render_widget(Paragraph::new(Line::styled(status, t.title())), head);

        match &self.error {
            Some(msg) => {
                frame.render_widget(Paragraph::new(Line::styled(msg.clone(), t.dim())), image)
            }
            None => {
                self.ensure_proto();
                if let Some((_, proto)) = self.proto.as_mut() {
                    frame.render_stateful_widget(
                        StatefulImage::default().resize(Resize::Fit(None)),
                        image,
                        proto,
                    );
                }
            }
        }
        render_footer(frame, footer, KEYS, None, &t);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char(' ') | KeyCode::Char('p') => self.paused = !self.paused,
            KeyCode::Char('h') | KeyCode::Left => {
                self.paused = true;
                self.step_frame(-1);
            }
            KeyCode::Char('l') | KeyCode::Right => {
                self.paused = true;
                self.step_frame(1);
            }
            KeyCode::Char('j') | KeyCode::Down => self.step_clip(1),
            KeyCode::Char('k') | KeyCode::Up => self.step_clip(-1),
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        let now = Instant::now();
        let elapsed = now - self.last;
        self.last = now;
        if self.paused {
            return Action::None;
        }
        let Some(clip) = &self.clip else {
            return Action::None;
        };
        self.held += elapsed;
        // a frame with no delay still shows for a moment, so the clip never spins
        let shown = clip.delays[self.frame].max(Duration::from_millis(20));
        if self.held >= shown {
            self.held -= shown;
            self.frame = (self.frame + 1) % clip.frames.len();
        }
        Action::None
    }

    fn poll_interval(&self) -> Duration {
        POLL
    }

    fn leader_ok(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    fn viewer(arg: &str) -> Video {
        let clips = list_clips(&screens_dir()).unwrap();
        let sel = clips
            .iter()
            .position(|p| {
                p.file_stem()
                    .is_some_and(|s| s.to_string_lossy().starts_with(arg))
            })
            .unwrap_or(0);
        let mut v = Video {
            theme: Theme::from_args(None, None, None),
            picker: Picker::halfblocks(),
            clips,
            sel,
            clip: None,
            frame: 0,
            held: Duration::ZERO,
            last: Instant::now(),
            paused: false,
            proto: None,
            error: None,
        };
        v.load();
        v
    }

    fn press(v: &mut Video, code: KeyCode) -> Action {
        v.on_key(KeyEvent::new(code, KeyModifiers::NONE))
    }

    #[test]
    fn decodes_the_recordings_and_draws() {
        let mut v = viewer("diagrams_power");
        assert!(v.error.is_none(), "{:?}", v.error);
        assert!(v.clip.as_ref().is_some_and(|c| c.frames.len() > 1));
        let mut term = Terminal::new(TestBackend::new(120, 40)).unwrap();
        term.draw(|f| v.draw(f)).unwrap();
        assert!(v.proto.is_some());
    }

    #[test]
    fn frames_advance_and_pause_holds() {
        let mut v = viewer("diagrams_power");
        v.last = Instant::now() - Duration::from_secs(10);
        v.tick();
        assert_eq!(v.frame, 1 % v.clip.as_ref().unwrap().frames.len());
        press(&mut v, KeyCode::Char(' '));
        let at = v.frame;
        v.last = Instant::now() - Duration::from_secs(10);
        v.tick();
        assert_eq!(v.frame, at);
    }

    #[test]
    fn keys_step_frames_and_clips() {
        let mut v = viewer("diagrams_power");
        let n = v.clip.as_ref().unwrap().frames.len();
        press(&mut v, KeyCode::Char('h'));
        assert_eq!(v.frame, n - 1);
        assert!(v.paused);
        let before = v.sel;
        press(&mut v, KeyCode::Char('j'));
        assert_eq!(v.sel, (before + 1) % v.clips.len());
        assert!(matches!(press(&mut v, KeyCode::Char('q')), Action::Quit));
    }
}
