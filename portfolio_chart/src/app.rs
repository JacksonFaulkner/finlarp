// Screen runtime shared by every TUI in this binary.
//
// A screen implements `Screen` (draw + key handling) and returns `Action`s;
// `run` owns the terminal (ratatui::run: init + restore, and the panic hook
// ratatui::init installs restores raw mode / the alternate screen before the
// panic message prints) and the event loop. Anything that must happen in nvim
// (open a document in the docview, open a search chunk, jump to another
// screen's picker) is an `NvimAction`: it is written as one JSON line to
// $SECURITY_SPREAD_ACTION_FILE and the process exits; ui/portfolio_chart.lua
// reads the file after the popup closes and dispatches it. Browser opens and
// clipboard copies happen in-process and the screen stays up.
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

/// Exit code the Lua wrapper treats as "reopen the symbol picker" (legacy
/// CANSLIM `s` key); prefer `NvimAction::Picker` in new code.
pub const EXIT_BACK_TO_PICKER: i32 = 90;

/// Env var naming the file an `NvimAction` is written to.
pub const ACTION_FILE_ENV: &str = "SECURITY_SPREAD_ACTION_FILE";

/// How long the loop waits for input before calling `tick` again.
const POLL: Duration = Duration::from_millis(100);

/// Everything a screen needs from its environment.
pub struct Ctx {
    pub db_path: PathBuf,
    pub theme: Theme,
}

/// Work to hand back to nvim. Serialized as {"action": "...", ...}.
#[derive(Debug, Clone, Serialize, PartialEq)]
#[serde(tag = "action", rename_all = "lowercase")]
pub enum NvimAction {
    /// Open `url` in the nvim document viewer (ui/docview.lua), jumping to `quote`.
    Docview { url: String, quote: Option<String> },
    /// Open a search chunk by id (ui/search.lua open_chunk).
    Chunk { id: String },
    /// Open another screen: "canslim" | "dossier" | "search", with its argument.
    Screen { screen: String, arg: Option<String> },
    /// Reopen the fzf symbol picker for `screen`.
    Picker { screen: String },
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
    /// Exit with a specific process code.
    Exit(i32),
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

/// Runs a screen to completion. Returns the process exit code.
pub fn run(screen: &mut dyn Screen) -> io::Result<i32> {
    ratatui::run(|terminal| event_loop(terminal, screen, &mut CrosstermEvents))
}

pub(crate) fn event_loop<B: Backend>(
    terminal: &mut Terminal<B>,
    screen: &mut dyn Screen,
    events: &mut dyn Events,
) -> io::Result<i32> {
    let mut dirty = true;
    loop {
        if dirty || screen.needs_redraw() {
            terminal
                .draw(|f| screen.draw(f))
                .map_err(|e| io::Error::other(e.to_string()))?;
            dirty = false;
        }
        let mut action = screen.tick();
        if action == Action::None {
            match events.next(POLL)? {
                Some(Event::Key(key)) if key.kind == KeyEventKind::Press => {
                    dirty = true;
                    action = if key.code == KeyCode::Char('c')
                        && key.modifiers.contains(KeyModifiers::CONTROL)
                    {
                        Action::Quit
                    } else {
                        screen.on_key(key)
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
            Action::Quit => return Ok(0),
            Action::Exit(code) => return Ok(code),
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
                write_nvim_action(&a)?;
                return Ok(0);
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
        // ui/portfolio_chart.lua dispatches on exactly these keys.
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
                KeyCode::Char('x') => Action::Exit(EXIT_BACK_TO_PICKER),
                _ => Action::None,
            }
        }
        fn needs_redraw(&self) -> bool {
            self.idle_redraw
        }
    }

    fn run_script(screen: &mut Probe, evs: Vec<Option<Event>>) -> io::Result<i32> {
        let mut term = Terminal::new(TestBackend::new(20, 3)).expect("terminal");
        event_loop(&mut term, screen, &mut Script(evs.into()))
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
    fn ctrl_c_quits_and_exit_codes_pass_through() {
        let mut p = Probe::default();
        let ctrl_c = Some(Event::Key(KeyEvent::new(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL,
        )));
        assert_eq!(run_script(&mut p, vec![ctrl_c]).expect("run"), 0);
        let mut p = Probe::default();
        assert_eq!(
            run_script(&mut p, vec![key('x')]).expect("run"),
            EXIT_BACK_TO_PICKER
        );
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
