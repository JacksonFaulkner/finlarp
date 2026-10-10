// Screen runtime shared by every TUI in this binary.
//
// A screen implements `Screen` (draw + key handling) and returns `Action`s;
// `run` owns the terminal (ratatui::run: init + restore, and the panic hook
// ratatui::init installs restores raw mode / the alternate screen before the
// panic message prints) and the event loop. Anything that must happen in nvim
// (open a document in the docview, open a search chunk, jump to another
// screen's picker) is an `NvimAction`: it is written as one JSON line to
// $FINLARP_ACTION_FILE and the process exits; ui/tui.lua
// reads the file after the popup closes and dispatches it. Browser opens and
// clipboard copies happen in-process and the screen stays up.
//
// Outside nvim (`fl`) there is no action file: documents open in the browser
// and screen/picker requests come back to main's router as `Exit::handoff`.
//
// Drawing is two-phase: the loop only calls `Screen::draw` when something
// could have changed (a key, a resize, a non-None action, a flash) or when
// the screen asks via `needs_redraw` (default: always, so tick-driven
// screens keep working unchanged; key-driven screens override it to skip
// idle redraws).

use std::io;
use std::path::PathBuf;
use std::time::Duration;

use ratatui::backend::Backend;
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use ratatui::{Frame, Terminal};
use serde::Serialize;

use crate::ui::theme::Theme;

/// Env var naming the file an `NvimAction` is written to.
pub const ACTION_FILE_ENV: &str = "FINLARP_ACTION_FILE";

/// How long the loop waits for input before calling `tick` again.
const POLL: Duration = Duration::from_millis(100);

/// Everything a screen needs from its environment.
pub struct Ctx {
    pub db_path: PathBuf,
    pub theme: Theme,
}

/// Work to hand back to nvim (or, outside nvim, to main's screen router).
/// Serialized as {"action": "...", ...}.
#[derive(Debug, Clone, Serialize, PartialEq)]
#[serde(tag = "action", rename_all = "lowercase")]
pub enum NvimAction {
    /// Open `url` in the nvim document viewer (ui/docview.lua), jumping to `quote`.
    Docview { url: String, quote: Option<String> },
    /// Open a search chunk by id (ui/search.lua open_chunk).
    Chunk { id: String },
    /// Open another screen: "canslim" | "dossier" | "search", with its argument.
    Screen { screen: String, arg: Option<String> },
    /// Reopen the symbol picker for `screen`.
    Picker { screen: String },
    /// `<space>ac` / `<space>as`: toggle the Claude Code window, or with
    /// `text` add it to Claude's context (ui/tui.lua writes it to a file and
    /// runs ClaudeCodeAdd).
    Claude { text: Option<String> },
}

#[derive(Debug, Clone, PartialEq)]
pub enum Action {
    None,
    Quit,
    /// Open a URL with the OS handler; screen stays open.
    OpenBrowser(String),
    /// Copy text to the clipboard; screen stays open.
    Copy(String),
    /// Hand work to nvim and exit.
    Nvim(NvimAction),
}

pub trait Screen {
    fn draw(&mut self, frame: &mut Frame);
    fn on_key(&mut self, key: KeyEvent) -> Action;
    /// Called every loop iteration (~poll interval) for debounced / async
    /// work, e.g. search re-querying after typing stops.
    fn tick(&mut self) -> Action {
        Action::None
    }
    /// Transient one-line status shown by screens that render a footer
    /// ("copied", "opened in browser"). Set by `run` after in-process actions.
    fn set_flash(&mut self, _msg: String) {}
    /// Whether to redraw on an idle poll (no key, no resize, tick returned
    /// None). Default true = redraw every ~100ms, which is what tick-driven
    /// screens need. Screens whose state only changes on keys return false
    /// (or true only while something time-based, like a flash, is showing).
    fn needs_redraw(&self) -> bool {
        true
    }
    /// How long the loop waits for input before the next `tick`; screens
    /// running an animation return a frame-sized interval while it plays.
    fn poll_interval(&self) -> Duration {
        POLL
    }
    /// Whether `<space>` may start the leader chord. Screens that type text
    /// (search, pickers, the command palette) return false so space stays a
    /// plain character there.
    fn leader_ok(&self) -> bool {
        true
    }
    /// Text for `<space>as`: the selected value with its source, or None if
    /// nothing is selected.
    fn claude_context(&self) -> Option<String> {
        None
    }
}

/// Progress through the nvim-style `<space>a{c,s}` leader chord.
#[derive(Clone, Copy, PartialEq)]
enum Chord {
    Idle,
    Space,
    SpaceA,
}

fn is_plain(key: &KeyEvent, c: char) -> bool {
    key.code == KeyCode::Char(c)
        && !key
            .modifiers
            .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
}

/// Feeds one key through the leader chord, then to the screen. Matches the
/// nvim bindings: `<space>ac` toggles Claude, `<space>as` adds context. A
/// space not followed by `a` is replayed to the screen, so it still works
/// (one key late).
fn route_key(screen: &mut dyn Screen, chord: &mut Chord, key: KeyEvent) -> Action {
    match *chord {
        Chord::Idle => {
            if is_plain(&key, ' ') && screen.leader_ok() {
                *chord = Chord::Space;
                Action::None
            } else {
                screen.on_key(key)
            }
        }
        Chord::Space => {
            *chord = Chord::Idle;
            if is_plain(&key, 'a') {
                *chord = Chord::SpaceA;
                return Action::None;
            }
            let space = KeyEvent::new(KeyCode::Char(' '), KeyModifiers::NONE);
            match screen.on_key(space) {
                Action::None => screen.on_key(key),
                a => a,
            }
        }
        Chord::SpaceA => {
            *chord = Chord::Idle;
            if is_plain(&key, 'c') {
                Action::Nvim(NvimAction::Claude { text: None })
            } else if is_plain(&key, 's') {
                match screen.claude_context() {
                    Some(text) => Action::Nvim(NvimAction::Claude { text: Some(text) }),
                    None => {
                        screen.set_flash("nothing selected to add".into());
                        Action::None
                    }
                }
            } else {
                Action::None
            }
        }
    }
}

/// Where the loop gets terminal events from; crossterm in production, a
/// scripted queue in tests.
pub(crate) trait Events {
    /// Next event, or None if `timeout` passed without one.
    fn next(&mut self, timeout: Duration) -> io::Result<Option<Event>>;
}

struct CrosstermEvents;

impl Events for CrosstermEvents {
    fn next(&mut self, timeout: Duration) -> io::Result<Option<Event>> {
        if event::poll(timeout)? {
            event::read().map(Some)
        } else {
            Ok(None)
        }
    }
}

fn write_nvim_action(a: &NvimAction) -> io::Result<()> {
    let Ok(path) = std::env::var(ACTION_FILE_ENV) else {
        return Ok(()); // launched outside nvim: nothing to hand back to
    };
    let line = serde_json::to_string(a).map_err(io::Error::other)?;
    std::fs::write(path, line + "\n")
}

/// How a screen ended: the process exit code, plus a screen/picker request
/// the caller (main's router) should open next when running outside nvim.
#[derive(Debug, PartialEq)]
pub struct Exit {
    pub code: i32,
    pub handoff: Option<NvimAction>,
}

impl Exit {
    fn code(code: i32) -> Self {
        Self {
            code,
            handoff: None,
        }
    }
}

/// Runs a screen to completion.
pub fn run(screen: &mut dyn Screen) -> io::Result<Exit> {
    ratatui::run(|terminal| event_loop(terminal, screen, &mut CrosstermEvents))
}

pub(crate) fn event_loop<B: Backend>(
    terminal: &mut Terminal<B>,
    screen: &mut dyn Screen,
    events: &mut dyn Events,
) -> io::Result<Exit> {
    let mut dirty = true;
    let mut chord = Chord::Idle;
    loop {
        if dirty || screen.needs_redraw() {
            terminal
                .draw(|f| screen.draw(f))
                .map_err(|e| io::Error::other(e.to_string()))?;
            dirty = false;
        }
        let mut action = screen.tick();
        if action == Action::None {
            match events.next(screen.poll_interval())? {
                Some(Event::Key(key)) if key.kind == KeyEventKind::Press => {
                    dirty = true;
                    action = if key.code == KeyCode::Char('c')
                        && key.modifiers.contains(KeyModifiers::CONTROL)
                    {
                        Action::Quit
                    } else {
                        route_key(screen, &mut chord, key)
                    };
                }
                // Terminal::draw autoresizes; the flag just forces the redraw
                // now rather than on the next key.
                Some(Event::Resize(..)) => dirty = true,
                // Release/repeat, focus, mouse, paste: nothing binds them.
                Some(_) | None => {}
            }
        } else {
            dirty = true;
        }
        match action {
            Action::None => {}
            Action::Quit => return Ok(Exit::code(0)),
            Action::OpenBrowser(url) => {
                let msg = match open::that_detached(&url) {
                    Ok(()) => "opened in browser".to_string(),
                    Err(e) => format!("open failed: {e}"),
                };
                screen.set_flash(msg);
            }
            Action::Copy(text) => {
                let msg = match arboard::Clipboard::new().and_then(|mut c| c.set_text(text)) {
                    Ok(()) => "copied".to_string(),
                    Err(e) => format!("copy failed: {e}"),
                };
                screen.set_flash(msg);
            }
            Action::Nvim(a) => {
                if std::env::var_os(ACTION_FILE_ENV).is_some() {
                    write_nvim_action(&a)?;
                    return Ok(Exit::code(0));
                }
                // Standalone (`fl`): nothing to hand back to. Documents open in
                // the browser; screen/picker requests go to main's router.
                match a {
                    NvimAction::Docview { url, .. } => {
                        let msg = match open::that_detached(&url) {
                            Ok(()) => "opened in browser".to_string(),
                            Err(e) => format!("open failed: {e}"),
                        };
                        screen.set_flash(msg);
                    }
                    NvimAction::Chunk { .. } => {
                        screen.set_flash("opening a chunk needs the nvim plugin".into());
                    }
                    NvimAction::Claude { .. } => {
                        screen.set_flash("Claude needs the nvim plugin".into());
                    }
                    a @ (NvimAction::Screen { .. } | NvimAction::Picker { .. }) => {
                        return Ok(Exit {
                            code: 0,
                            handoff: Some(a),
                        });
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use std::collections::VecDeque;

    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventState, KeyModifiers};
    use serde_json::json;

    use super::*;

    fn to_json(a: &NvimAction) -> serde_json::Value {
        serde_json::to_value(a).expect("serialize")
    }

    #[test]
    fn nvim_action_json_shape() {
        // ui/tui.lua dispatches on exactly these keys.
        let d = NvimAction::Docview {
            url: "https://x/y".into(),
            quote: Some("net revenue".into()),
        };
        assert_eq!(
            to_json(&d),
            json!({"action": "docview", "url": "https://x/y", "quote": "net revenue"})
        );
        let d = NvimAction::Docview {
            url: "u".into(),
            quote: None,
        };
        assert_eq!(
            to_json(&d),
            json!({"action": "docview", "url": "u", "quote": null})
        );
        assert_eq!(
            to_json(&NvimAction::Chunk { id: "42".into() }),
            json!({"action": "chunk", "id": "42"})
        );
        let s = NvimAction::Screen {
            screen: "dossier".into(),
            arg: Some("MRVL".into()),
        };
        assert_eq!(
            to_json(&s),
            json!({"action": "screen", "screen": "dossier", "arg": "MRVL"})
        );
        let p = NvimAction::Picker {
            screen: "canslim".into(),
        };
        assert_eq!(
            to_json(&p),
            json!({"action": "picker", "screen": "canslim"})
        );
        assert_eq!(
            to_json(&NvimAction::Claude { text: None }),
            json!({"action": "claude", "text": null})
        );
        assert_eq!(
            to_json(&NvimAction::Claude {
                text: Some("x".into())
            }),
            json!({"action": "claude", "text": "x"})
        );
        // One line, so the Lua side can read the file whole and decode it.
        assert!(!serde_json::to_string(&s).expect("serialize").contains('\n'));
    }

    /// Replays a fixed event list; errors when it runs dry so a test that
    /// forgets to quit fails instead of hanging.
    struct Script(VecDeque<Option<Event>>);

    impl Events for Script {
        fn next(&mut self, _timeout: Duration) -> io::Result<Option<Event>> {
            self.0
                .pop_front()
                .ok_or_else(|| io::Error::other("script exhausted"))
        }
    }

    fn key(c: char) -> Option<Event> {
        Some(Event::Key(KeyEvent::new(
            KeyCode::Char(c),
            KeyModifiers::NONE,
        )))
    }

    #[derive(Default)]
    struct Probe {
        draws: usize,
        idle_redraw: bool,
    }

    impl Screen for Probe {
        fn draw(&mut self, frame: &mut Frame) {
            self.draws += 1;
            frame.render_widget(format!("draws {}", self.draws), frame.area());
        }
        fn on_key(&mut self, key: KeyEvent) -> Action {
            match key.code {
                KeyCode::Char('q') => Action::Quit,
                _ => Action::None,
            }
        }
        fn needs_redraw(&self) -> bool {
            self.idle_redraw
        }
    }

    fn run_script(screen: &mut Probe, evs: Vec<Option<Event>>) -> io::Result<i32> {
        let mut term = Terminal::new(TestBackend::new(20, 3)).expect("terminal");
        event_loop(&mut term, screen, &mut Script(evs.into())).map(|e| e.code)
    }

    #[test]
    fn leader_chord_toggles_and_adds_context() {
        struct Ctx1;
        impl Screen for Ctx1 {
            fn draw(&mut self, _: &mut Frame) {}
            fn on_key(&mut self, _: KeyEvent) -> Action {
                Action::Quit
            }
            fn claude_context(&self) -> Option<String> {
                Some("ctx".into())
            }
        }
        let mut s = Ctx1;
        let mut c = Chord::Idle;
        let k = |ch| KeyEvent::new(KeyCode::Char(ch), KeyModifiers::NONE);
        assert_eq!(route_key(&mut s, &mut c, k(' ')), Action::None);
        assert_eq!(route_key(&mut s, &mut c, k('a')), Action::None);
        assert_eq!(
            route_key(&mut s, &mut c, k('s')),
            Action::Nvim(NvimAction::Claude {
                text: Some("ctx".into())
            })
        );
        for ch in [' ', 'a'] {
            route_key(&mut s, &mut c, k(ch));
        }
        assert_eq!(
            route_key(&mut s, &mut c, k('c')),
            Action::Nvim(NvimAction::Claude { text: None })
        );
        // space then a non-chord key replays both to the screen
        route_key(&mut s, &mut c, k(' '));
        assert_eq!(route_key(&mut s, &mut c, k('x')), Action::Quit);
        assert!(c == Chord::Idle);
    }

    #[test]
    fn idle_polls_skip_redraw_when_screen_opts_out() {
        let mut p = Probe::default();
        let code =
            run_script(&mut p, vec![None, None, None, key('j'), None, key('q')]).expect("run");
        assert_eq!(code, 0);
        // initial draw + one after `j`; the four idle polls draw nothing.
        assert_eq!(p.draws, 2);
    }

    #[test]
    fn default_redraws_every_poll_and_resize_forces_one() {
        let mut p = Probe {
            idle_redraw: true,
            ..Default::default()
        };
        run_script(&mut p, vec![None, None, key('q')]).expect("run");
        assert_eq!(p.draws, 3);

        let mut p = Probe::default();
        run_script(&mut p, vec![Some(Event::Resize(30, 5)), key('q')]).expect("run");
        assert_eq!(p.draws, 2);
    }

    #[test]
    fn ctrl_c_quits() {
        let mut p = Probe::default();
        let ctrl_c = Some(Event::Key(KeyEvent::new(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL,
        )));
        assert_eq!(run_script(&mut p, vec![ctrl_c]).expect("run"), 0);
    }

    #[test]
    fn key_release_is_ignored() {
        let mut p = Probe::default();
        let release = Some(Event::Key(KeyEvent {
            code: KeyCode::Char('q'),
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Release,
            state: KeyEventState::NONE,
        }));
        assert!(run_script(&mut p, vec![release]).is_err()); // did not quit; ran dry
    }
}
