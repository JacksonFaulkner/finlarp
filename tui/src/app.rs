// Screen runtime shared by every TUI in this binary.
//
// A screen implements `Screen` (draw + key handling) and returns `Action`s;
// `run` owns the terminal (ratatui::run: init + restore, and the panic hook
// ratatui::init installs restores raw mode / the alternate screen before the
// panic message prints) and the event loop. Browser opens and clipboard copies
// happen in-process and the screen stays up. Opening another screen or picker
// is a `Route`: the screen exits with it as `Exit::handoff`, and main's router
// (`run_session`) pushes the new screen on a stack and returns here on q/esc.
// The Claude popup is also a `Route`, handled in the loop by claude_popup.
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

use crate::ui::theme::Theme;

/// How long the loop waits for input before calling `tick` again.
const POLL: Duration = Duration::from_millis(100);

/// Everything a screen needs from its environment.
pub struct Ctx {
    pub db_path: PathBuf,
    pub theme: Theme,
}

/// Work the router handles: open another screen, reopen a picker, or open
/// the Claude popup.
#[derive(Debug, Clone, PartialEq)]
pub enum Route {
    /// Open another screen: "canslim" | "dossier" | "search", with its argument.
    Screen { screen: String, arg: Option<String> },
    /// Reopen the symbol picker for `screen`.
    Picker { screen: String },
    /// `<space>ac` / `<space>as`: show the Claude popup, or with `text`
    /// type it into Claude's prompt first.
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
    /// Screen, picker, or Claude request; see `Route`.
    Route(Route),
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

/// Progress through the `<space>a{c,s}` leader chord.
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

/// Feeds one key through the leader chord, then to the screen. `<space>ac`
/// opens Claude, `<space>as` adds the selected context to it. A
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
                Action::Route(Route::Claude { text: None })
            } else if is_plain(&key, 's') {
                match screen.claude_context() {
                    Some(text) => Action::Route(Route::Claude { text: Some(text) }),
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

/// How a screen ended: the process exit code, plus a screen/picker request
/// the caller (main's router) should open next.
#[derive(Debug, PartialEq)]
pub struct Exit {
    pub code: i32,
    pub handoff: Option<Route>,
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
            // Screen/picker requests always go to main's session stack, so q/esc
            // in the child returns here.
            Action::Route(r @ (Route::Screen { .. } | Route::Picker { .. })) => {
                return Ok(Exit {
                    code: 0,
                    handoff: Some(r),
                });
            }
            Action::Route(Route::Claude { text }) => {
                if let Err(e) = crate::claude_popup::open(text.as_deref()) {
                    screen.set_flash(format!("claude: {e}"));
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

    use super::*;

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
            Action::Route(Route::Claude {
                text: Some("ctx".into())
            })
        );
        for ch in [' ', 'a'] {
            route_key(&mut s, &mut c, k(ch));
        }
        assert_eq!(
            route_key(&mut s, &mut c, k('c')),
            Action::Route(Route::Claude { text: None })
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
