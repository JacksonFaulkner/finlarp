// `<space>wq` in any screen: rebuild `fl` from the checkout, then restart into
// the screen you were on, so you know you are running the newest code.
//
// Progress comes from cargo itself. `--message-format=json-render-diagnostics`
// puts one JSON object per finished unit on stdout (`compiler-artifact`, with
// `fresh: true` when nothing changed) and a final `build-finished`; stderr
// carries the human status lines ("Compiling foo v1.2", "Blocking waiting for
// file lock") and rendered errors. Starts minus finishes is what is compiling
// right now. The unit count and duration of the last build are saved next to
// the binary, so the bar has a real total and an ETA from the second run on.
//
// On success the screen returns `Route::Restart`; main execs the new binary
// with the original flags and the screen beneath this one. On failure it
// stays up with the errors; q/esc goes back. Esc during a build kills cargo.

use std::collections::VecDeque;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Gauge, Paragraph, Wrap};
use throbber_widgets_tui::ThrobberState;

use crate::app::{Action, Ctx, Route, Screen};
use crate::ui::help::{Key, key, render_footer};
use crate::ui::theme::Theme;
use crate::ui::throbber;

/// The crate this binary was built from (tui/), baked in at compile time.
pub const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

/// What the restart execs: exactly the file cargo just wrote.
pub fn built_binary() -> PathBuf {
    Path::new(MANIFEST_DIR).join("target/release/fl")
}

/// Last build's unit count and seconds, for the bar total and the ETA.
fn stats_path() -> PathBuf {
    Path::new(MANIFEST_DIR).join("target/release/.fl-rebuild")
}

/// How long the "built, restarting" line stays up before the exec.
const LINGER: Duration = Duration::from_millis(700);
/// Lines of cargo output kept for the log pane.
const LOG_CAP: usize = 400;

const KEYS: &[Key] = &[key("esc", "cancel / back"), key("j/k", "scroll log")];

/// One parsed line from cargo, sent from the reader threads.
#[derive(Debug, PartialEq)]
enum Msg {
    /// stderr `Compiling foo v1.2 (...)`: a unit started.
    Started(String),
    /// stdout `compiler-artifact`: a unit finished (`fresh` = was up to date).
    Finished { name: String, fresh: bool },
    /// stdout `build-finished`.
    Done(bool),
    /// Any other stderr line (errors, warnings, lock waits).
    Log(String),
}

/// Parses one stdout JSON line from cargo.
fn parse_stdout(line: &str) -> Option<Msg> {
    let v: serde_json::Value = serde_json::from_str(line).ok()?;
    match v.get("reason")?.as_str()? {
        "compiler-artifact" => Some(Msg::Finished {
            name: v.pointer("/target/name")?.as_str()?.to_string(),
            fresh: v.get("fresh").and_then(|f| f.as_bool()).unwrap_or(false),
        }),
        "build-finished" => Some(Msg::Done(v.get("success")?.as_bool()?)),
        _ => None,
    }
}

/// Parses one stderr line: `Compiling` status lines become `Started`.
fn parse_stderr(line: &str) -> Msg {
    let t = line.trim_start();
    match t.strip_prefix("Compiling ") {
        Some(rest) => Msg::Started(rest.split_whitespace().next().unwrap_or(rest).to_string()),
        None => Msg::Log(line.to_string()),
    }
}

#[derive(Debug, PartialEq)]
enum State {
    Building,
    /// Built at this instant; restart once LINGER has passed.
    Built(Instant),
    Failed,
    Cancelled,
}

pub struct Rebuild {
    theme: Theme,
    child: Option<Child>,
    rx: Receiver<Msg>,
    state: State,
    started: Instant,
    elapsed: Duration,
    /// Units finished so far, and how many of them were fresh.
    done: usize,
    fresh: usize,
    /// Units started but not finished, oldest first.
    active: Vec<String>,
    /// From the last build: (units, seconds).
    prev: Option<(usize, f64)>,
    log: VecDeque<String>,
    /// Lines scrolled up from the bottom of the log.
    scroll: usize,
    spin: ThrobberState,
    flash: Option<String>,
}

fn find_cargo() -> PathBuf {
    // tmux popups and nvim jobs do not always have ~/.cargo/bin on PATH.
    if let Some(home) = std::env::var_os("HOME") {
        let p = PathBuf::from(home).join(".cargo/bin/cargo");
        if p.is_file() {
            return p;
        }
    }
    PathBuf::from("cargo")
}

fn read_stats() -> Option<(usize, f64)> {
    let s = std::fs::read_to_string(stats_path()).ok()?;
    let (u, t) = s.trim().split_once(' ')?;
    Some((u.parse().ok()?, t.parse().ok()?))
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Rebuild> {
    let mut child = Command::new(find_cargo())
        .args([
            "build",
            "--release",
            "--message-format=json-render-diagnostics",
        ])
        .arg("--manifest-path")
        .arg(Path::new(MANIFEST_DIR).join("Cargo.toml"))
        .env("CARGO_TERM_COLOR", "never")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| io::Error::other(format!("rebuild: could not start cargo: {e}")))?;
    let (tx, rx) = mpsc::channel();
    let out = child.stdout.take().expect("piped stdout");
    let err = child.stderr.take().expect("piped stderr");
    let tx2 = tx.clone();
    thread::spawn(move || {
        for line in BufReader::new(out).lines().map_while(Result::ok) {
            if let Some(m) = parse_stdout(&line)
                && tx.send(m).is_err()
            {
                break;
            }
        }
    });
    thread::spawn(move || {
        for line in BufReader::new(err).lines().map_while(Result::ok) {
            if tx2.send(parse_stderr(&line)).is_err() {
                break;
            }
        }
    });
    Ok(Rebuild::new(ctx.theme, Some(child), rx, read_stats()))
}

impl Rebuild {
    fn new(
        theme: Theme,
        child: Option<Child>,
        rx: Receiver<Msg>,
        prev: Option<(usize, f64)>,
    ) -> Self {
        Self {
            theme,
            child,
            rx,
            state: State::Building,
            started: Instant::now(),
            elapsed: Duration::ZERO,
            done: 0,
            fresh: 0,
            active: Vec::new(),
            prev,
            log: VecDeque::new(),
            scroll: 0,
            spin: ThrobberState::default(),
            flash: None,
        }
    }

    fn push_log(&mut self, line: String) {
        if self.log.len() == LOG_CAP {
            self.log.pop_front();
        }
        self.log.push_back(line);
    }

    fn apply(&mut self, msg: Msg) {
        match msg {
            Msg::Started(name) => {
                self.push_log(format!("   Compiling {name}"));
                self.active.push(name);
            }
            Msg::Finished { name, fresh } => {
                self.done += 1;
                if fresh {
                    self.fresh += 1;
                }
                // Crate names use `-`, target names use `_`.
                let norm = |s: &str| s.replace('-', "_");
                if let Some(i) = self.active.iter().position(|a| norm(a) == norm(&name)) {
                    self.active.remove(i);
                }
            }
            Msg::Done(ok) => {
                self.elapsed = self.started.elapsed();
                self.active.clear();
                if ok {
                    let _ = std::fs::write(
                        stats_path(),
                        format!("{} {:.1}", self.done, self.elapsed.as_secs_f64()),
                    );
                    self.state = State::Built(Instant::now());
                } else {
                    self.state = State::Failed;
                }
            }
            Msg::Log(line) => self.push_log(line),
        }
    }

    /// Done fraction, if the last build gave a total.
    fn ratio(&self) -> Option<f64> {
        let (units, _) = self.prev?;
        (units > 0).then(|| (self.done as f64 / units as f64).min(1.0))
    }

    fn status_line(&self) -> Line<'_> {
        let t = &self.theme;
        let secs = match self.state {
            State::Building => self.started.elapsed(),
            _ => self.elapsed,
        }
        .as_secs_f64();
        match &self.state {
            State::Building => {
                let mut label = format!("building fl  {secs:.0}s");
                if let Some((_, prev)) = self.prev {
                    label.push_str(&format!("  (last {prev:.0}s)"));
                }
                let mut line = throbber::line(&self.spin, "", t.accent());
                line.spans.push(Span::styled(label, t.base()));
                line
            }
            State::Built(_) => {
                let what = if self.done == self.fresh {
                    "already up to date".to_string()
                } else {
                    format!("rebuilt {} of {} units", self.done - self.fresh, self.done)
                };
                Line::from(vec![
                    Span::styled("✓ ", t.up()),
                    Span::styled(format!("{what} in {secs:.1}s, restarting…"), t.base()),
                ])
            }
            State::Failed => Line::from(vec![
                Span::styled("✗ ", t.down()),
                Span::styled(
                    format!("build failed after {secs:.1}s; still running the old fl"),
                    t.base(),
                ),
            ]),
            State::Cancelled => Line::from(Span::styled("cancelled", t.dim())),
        }
    }
}

impl Drop for Rebuild {
    fn drop(&mut self) {
        if let Some(c) = self.child.as_mut() {
            if matches!(c.try_wait(), Ok(None)) {
                let _ = c.kill();
            }
            let _ = c.wait();
        }
    }
}

impl Screen for Rebuild {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let block = Block::bordered()
            .title(Span::styled(" rebuild fl ", t.title()))
            .border_style(t.border())
            .style(t.base());
        let inner = block.inner(frame.area());
        frame.render_widget(block, frame.area());
        let [status, bar, now, log, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .spacing(0)
        .areas(inner);

        frame.render_widget(Paragraph::new(self.status_line()), status);

        let count = match self.prev {
            Some((units, _)) => format!("{}/{} units", self.done, units.max(self.done)),
            None => format!("{} units (no total yet: first rebuild)", self.done),
        };
        let ratio = match self.state {
            State::Built(_) => 1.0,
            _ => self.ratio().unwrap_or(0.0),
        };
        let color = match self.state {
            State::Failed => t.down,
            State::Built(_) => t.up,
            _ => t.accent,
        };
        frame.render_widget(
            Gauge::default()
                .ratio(ratio)
                .label(Span::styled(count, t.base()))
                .gauge_style(Style::new().fg(color))
                .use_unicode(true),
            bar,
        );

        let now_text = if self.active.is_empty() {
            String::new()
        } else {
            format!("compiling: {}", self.active.join(", "))
        };
        frame.render_widget(Paragraph::new(Span::styled(now_text, t.accent())), now);

        let h = log.height as usize;
        let end = self.log.len().saturating_sub(self.scroll);
        let start = end.saturating_sub(h);
        let lines: Vec<Line> = self
            .log
            .range(start..end)
            .map(|l| {
                let style = if l.starts_with("error") {
                    t.down()
                } else if l.starts_with("warning") {
                    t.accent()
                } else {
                    t.dim()
                };
                Line::styled(l.clone(), style)
            })
            .collect();
        frame.render_widget(Paragraph::new(lines).wrap(Wrap { trim: false }), log);

        render_footer(frame, foot, KEYS, self.flash.as_deref(), &t);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => {
                if self.state == State::Building {
                    if let Some(c) = self.child.as_mut() {
                        let _ = c.kill();
                    }
                    self.state = State::Cancelled;
                }
                Action::Quit
            }
            KeyCode::Char('k') | KeyCode::Up => {
                self.scroll = (self.scroll + 1).min(self.log.len().saturating_sub(1));
                Action::None
            }
            KeyCode::Char('j') | KeyCode::Down => {
                self.scroll = self.scroll.saturating_sub(1);
                Action::None
            }
            _ => Action::None,
        }
    }

    fn tick(&mut self) -> Action {
        while let Ok(m) = self.rx.try_recv() {
            self.apply(m);
        }
        if self.state == State::Building {
            self.spin.calc_next();
            // cargo died without a build-finished line (killed, crashed).
            if let Some(Ok(Some(status))) = self.child.as_mut().map(|c| c.try_wait()) {
                // Drain what the readers still hold before deciding.
                thread::sleep(Duration::from_millis(20));
                while let Ok(m) = self.rx.try_recv() {
                    self.apply(m);
                }
                if self.state == State::Building {
                    self.elapsed = self.started.elapsed();
                    self.push_log(format!("cargo exited: {status}"));
                    self.state = State::Failed;
                }
            }
        }
        match self.state {
            State::Built(at) if at.elapsed() >= LINGER => Action::Route(Route::Restart),
            _ => Action::None,
        }
    }

    fn poll_interval(&self) -> Duration {
        Duration::from_millis(80)
    }

    fn leader_ok(&self) -> bool {
        false
    }

    fn shows_tape(&self) -> bool {
        false
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn screen(prev: Option<(usize, f64)>) -> (Rebuild, mpsc::Sender<Msg>) {
        let (tx, rx) = mpsc::channel();
        (
            Rebuild::new(Theme::from_args(None, None, None), None, rx, prev),
            tx,
        )
    }

    #[test]
    fn parses_cargo_json_and_status_lines() {
        let art = r#"{"reason":"compiler-artifact","target":{"name":"serde_json"},"fresh":true}"#;
        assert_eq!(
            parse_stdout(art),
            Some(Msg::Finished {
                name: "serde_json".into(),
                fresh: true
            })
        );
        assert_eq!(
            parse_stdout(r#"{"reason":"build-finished","success":false}"#),
            Some(Msg::Done(false))
        );
        assert_eq!(parse_stdout(r#"{"reason":"build-script-executed"}"#), None);
        assert_eq!(parse_stdout("not json"), None);
        assert_eq!(
            parse_stderr("   Compiling serde-json v1.0.1"),
            Msg::Started("serde-json".into())
        );
        assert_eq!(
            parse_stderr("error[E0308]: x"),
            Msg::Log("error[E0308]: x".into())
        );
    }

    #[test]
    fn tracks_active_units_and_restarts_after_success() {
        let (mut s, tx) = screen(Some((4, 10.0)));
        tx.send(Msg::Started("serde-json".into())).unwrap();
        tx.send(Msg::Started("finlarp".into())).unwrap();
        tx.send(Msg::Finished {
            name: "serde_json".into(),
            fresh: false,
        })
        .unwrap();
        s.tick();
        assert_eq!(s.active, vec!["finlarp".to_string()]);
        assert_eq!(s.ratio(), Some(0.25));
        s.state = State::Built(Instant::now() - LINGER);
        assert_eq!(s.tick(), Action::Route(Route::Restart));
    }

    #[test]
    fn failure_stays_up() {
        let (mut s, tx) = screen(None);
        tx.send(Msg::Log("error: boom".into())).unwrap();
        tx.send(Msg::Done(false)).unwrap();
        assert_eq!(s.tick(), Action::None);
        assert_eq!(s.state, State::Failed);
    }
}
