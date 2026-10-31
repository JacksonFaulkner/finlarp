// Standalone onboarding (nvim `va`). Adds new tickers to the universe, runs
// every puller for just those tickers, rebuilds their dossiers, then shows
// the per-step report and which dossier sections each ticker still lacks
// (py/jobs/onboard.py).
//
//   Onboard ›  AAPL SKHY█
//   ↵ run · esc back
//
// The job runs on a background thread so the screen stays live: progress
// comes from the job's `… <step>` lines on stderr, and esc cancels a run in
// flight. A ticker that is not in the universe asks for its sub-sector first,
// as the nvim flow does.

use std::collections::BTreeMap;
use std::io::{self, BufRead, BufReader, Read};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::sync::{Arc, Mutex, MutexGuard, PoisonError};
use std::thread;
use std::time::Instant;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph};

use crate::app::{Action, Ctx, Screen};
use crate::pyrun;
use crate::screens::watchlists::valid_symbol;
use crate::ui::text;
use crate::ui::theme::Theme;

const SCRIPT: &str = "py/jobs/onboard.py";

#[derive(Debug, Clone, Default, PartialEq)]
struct Step {
    name: String,
    /// "ok" | "failed" | "skipped"
    status: String,
    secs: f64,
    detail: String,
}

#[derive(Debug, Clone, Default, PartialEq)]
struct Report {
    tickers: Vec<String>,
    steps: Vec<Step>,
    /// Ticker -> dossier sections that are not ok ("section:status"); empty = all populated.
    health: BTreeMap<String, Vec<String>>,
    total_secs: f64,
}

/// What the job is for: the onboarding run, or the sub-sector list.
#[derive(Debug, Clone, Copy, PartialEq)]
enum Kind {
    Onboard,
    SubSectors,
}

/// Progress shared between the job's reader threads and the screen.
#[derive(Debug, Default)]
struct Shared {
    /// Step names from the `… <step>` lines, in order.
    steps: Vec<String>,
    /// Other stderr lines (warnings, tracebacks), kept for failure messages.
    err: Vec<String>,
}

struct Job {
    rx: Receiver<Result<String, String>>,
    child: Arc<Mutex<Option<Child>>>,
    shared: Arc<Mutex<Shared>>,
    kind: Kind,
    started: Instant,
}

impl Job {
    /// Kills the process if it is still running; the thread then reports and exits.
    fn kill(&self) {
        if let Some(c) = lock(&self.child).as_mut() {
            let _ = c.kill();
        }
    }
}

impl Drop for Job {
    fn drop(&mut self) {
        self.kill();
    }
}

enum Phase {
    Input,
    Running,
    SubPick { subs: Vec<String>, state: ListState },
    Done,
}

pub struct Onboard {
    theme: Theme,
    phase: Phase,
    input: String,
    /// Tickers of the run on screen (or about to run).
    tickers: Vec<String>,
    /// Sub-sector passed with `--sub` after the prompt, if any.
    sub: Option<String>,
    job: Option<Job>,
    report: Option<Report>,
    /// The job's raw stdout, shown when no report lines could be read from it.
    raw: String,
    /// Set when the run itself failed (non-zero exit, unreadable output).
    error: Option<String>,
    /// One-line message on the input screen (bad ticker, cancelled, ...).
    flash: Option<String>,
    scroll: u16,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Onboard> {
    Ok(Onboard {
        theme: ctx.theme,
        phase: Phase::Input,
        input: arg.unwrap_or_default().trim().to_string(),
        tickers: Vec::new(),
        sub: None,
        job: None,
        report: None,
        raw: String::new(),
        error: None,
        flash: None,
        scroll: 0,
    })
}

fn lock<T>(m: &Mutex<T>) -> MutexGuard<'_, T> {
    m.lock().unwrap_or_else(PoisonError::into_inner)
}

/// Tickers from the prompt: space or comma separated, uppercased (as the nvim flow does).
fn parse_tickers(text: &str) -> Result<Vec<String>, String> {
    let mut out: Vec<String> = Vec::new();
    for tok in text
        .split(|c: char| c.is_whitespace() || c == ',')
        .filter(|t| !t.is_empty())
    {
        let t = tok.to_uppercase();
        if !valid_symbol(&t) {
            return Err(format!("not a ticker: {tok}"));
        }
        if !out.contains(&t) {
            out.push(t);
        }
    }
    Ok(out)
}

/// Reads the human report `print_report` writes to stdout (no --json, so the
/// stderr progress lines stream live). Lines it does not recognise are skipped.
fn parse_report(out: &str) -> Report {
    let mut r = Report::default();
    for line in out.lines() {
        let t = line.trim_start();
        if let Some(mark) = t.chars().next().filter(|c| matches!(*c, '✓' | '✗' | '-')) {
            // "  ✓ name        1.2s  detail"
            let body = t[mark.len_utf8()..].trim_start();
            let (name, rest) = body.split_once(char::is_whitespace).unwrap_or((body, ""));
            let rest = rest.trim_start();
            let (secs, detail) = rest.split_once(char::is_whitespace).unwrap_or((rest, ""));
            r.steps.push(Step {
                name: name.to_string(),
                status: match mark {
                    '✓' => "ok",
                    '✗' => "failed",
                    _ => "skipped",
                }
                .to_string(),
                secs: secs.trim_end_matches('s').parse().unwrap_or(0.0),
                detail: detail.trim().to_string(),
            });
        } else if let Some(rest) = t.strip_prefix("onboard ") {
            // "onboard AAPL SKHY  (84.2s)"
            let (tickers, secs) = rest.split_once('(').unwrap_or((rest, ""));
            r.tickers = tickers.split_whitespace().map(str::to_string).collect();
            r.total_secs = secs.trim_end_matches(')').trim_end_matches('s').parse().unwrap_or(0.0);
        } else if line.starts_with("  ") {
            // "  AAPL: all dossier sections populated" / "  SKHY: financials:empty, ..."
            if let Some((ticker, bad)) = t.split_once(": ") {
                if !ticker.contains(' ') {
                    let bad = if bad == "all dossier sections populated" {
                        Vec::new()
                    } else {
                        bad.split(", ").map(str::to_string).collect()
                    };
                    r.health.insert(ticker.to_string(), bad);
                }
            }
        }
    }
    r
}

fn parse_subs(out: &str) -> Result<Vec<String>, String> {
    serde_json::from_str(out.trim()).map_err(|e| format!("could not read sub-sectors: {e}"))
}

/// The universe step stopped on a ticker that is not in the universe yet.
fn needs_sub(r: &Report) -> bool {
    r.steps
        .iter()
        .any(|s| s.name == "universe" && s.status == "failed" && s.detail.contains("pass --sub"))
}

/// Runs `SCRIPT` with `args`, reading stdout whole and stderr line by line into `shared`.
fn run_child(
    slot: &Mutex<Option<Child>>,
    shared: &Mutex<Shared>,
    args: &[String],
) -> Result<String, String> {
    let plugin = pyrun::plugin_dir();
    let mut child = Command::new(pyrun::python(&plugin))
        .arg(plugin.join(SCRIPT))
        .args(args)
        .current_dir(&plugin)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("{SCRIPT}: {e}"))?;
    let mut stdout = child.stdout.take();
    let stderr = child.stderr.take();
    *lock(slot) = Some(child);

    // Stderr is read live on a scoped thread (progress lines), stdout whole.
    let out = thread::scope(|s| {
        s.spawn(move || {
            if let Some(e) = stderr {
                for line in BufReader::new(e).lines().map_while(Result::ok) {
                    let mut sh = lock(shared);
                    match line.strip_prefix("… ") {
                        Some(name) => sh.steps.push(name.to_string()),
                        None => sh.err.push(line),
                    }
                }
            }
        });
        let mut out = Vec::new();
        if let Some(o) = stdout.as_mut() {
            let _ = o.read_to_end(&mut out);
        }
        String::from_utf8_lossy(&out).into_owned()
    });

    let Some(mut child) = lock(slot).take() else {
        return Err("cancelled".into());
    };
    let status = child.wait().map_err(|e| e.to_string())?;
    if status.success() {
        Ok(out)
    } else {
        let sh = lock(shared);
        let tail: Vec<&str> = sh.err.iter().rev().take(6).map(String::as_str).collect();
        let tail: Vec<&str> = tail.into_iter().rev().collect();
        Err(if tail.is_empty() {
            format!("{SCRIPT} exited {}", status.code().unwrap_or(-1))
        } else {
            tail.join("\n")
        })
    }
}

fn spawn_job(kind: Kind, args: Vec<String>) -> Job {
    let (tx, rx) = mpsc::channel();
    let child = Arc::new(Mutex::new(None::<Child>));
    let shared = Arc::new(Mutex::new(Shared::default()));
    let (slot, sh) = (child.clone(), shared.clone());
    thread::spawn(move || {
        let _ = tx.send(run_child(&slot, &sh, &args));
    });
    Job {
        rx,
        child,
        shared,
        kind,
        started: Instant::now(),
    }
}

fn report_lines(r: &Report, raw: &str, t: Theme) -> Vec<Line<'static>> {
    let mut out = Vec::new();
    let head = if r.tickers.is_empty() {
        "onboard".to_string()
    } else {
        format!("onboard {}", r.tickers.join(" "))
    };
    out.push(Line::styled(format!("{head}  ({:.1}s)", r.total_secs), t.title()));
    if r.steps.is_empty() {
        // Nothing recognisable: show what the job printed.
        out.push(Line::styled("no step report; raw output:", t.dim()));
        out.extend(raw.lines().map(|l| Line::styled(l.to_string(), t.base())));
        return out;
    }
    out.push(Line::raw(""));
    for s in &r.steps {
        let (mark, style) = match s.status.as_str() {
            "ok" => ("✓", t.base()),
            "failed" => ("✗", t.down()),
            _ => ("-", t.dim()),
        };
        out.push(Line::styled(
            format!("  {mark} {:<12} {:>7.1}s  {}", s.name, s.secs, s.detail),
            style,
        ));
    }
    let mut slow: Vec<&Step> = r.steps.iter().filter(|s| s.status == "ok").collect();
    slow.sort_by(|a, b| b.secs.total_cmp(&a.secs));
    if !slow.is_empty() {
        let top: Vec<String> = slow
            .iter()
            .take(3)
            .map(|s| format!("{} {:.0}s", s.name, s.secs))
            .collect();
        out.push(Line::styled(format!("  slowest: {}", top.join(", ")), t.dim()));
    }
    if !r.health.is_empty() {
        out.push(Line::raw(""));
        out.push(Line::styled("dossier health", t.accent()));
        for (ticker, bad) in &r.health {
            if bad.is_empty() {
                out.push(Line::styled(
                    format!("  {ticker}: all dossier sections populated"),
                    t.up(),
                ));
            } else {
                out.push(Line::styled(
                    format!("  {ticker}: {}", bad.join(", ")),
                    t.down(),
                ));
            }
        }
    }
    out
}

impl Onboard {
    fn submit(&mut self) {
        match parse_tickers(&self.input) {
            Ok(tickers) if tickers.is_empty() => {}
            Ok(tickers) => {
                self.tickers = tickers;
                self.sub = None;
                self.start(None);
            }
            Err(e) => self.flash = Some(e),
        }
    }

    fn start(&mut self, sub: Option<String>) {
        let mut args: Vec<String> = self.tickers.clone();
        if let Some(s) = &sub {
            args.push("--sub".into());
            args.push(s.clone());
        }
        self.sub = sub;
        self.report = None;
        self.raw.clear();
        self.error = None;
        self.flash = None;
        self.scroll = 0;
        self.job = Some(spawn_job(Kind::Onboard, args));
        self.phase = Phase::Running;
    }

    fn cancel(&mut self) {
        self.job = None; // Drop kills the process
    }

    fn finish(&mut self, kind: Kind, result: Result<String, String>) {
        match (kind, result) {
            (Kind::SubSectors, Ok(out)) => match parse_subs(&out) {
                Ok(subs) if !subs.is_empty() => {
                    let mut state = ListState::default();
                    state.select(Some(0));
                    self.phase = Phase::SubPick { subs, state };
                }
                Ok(_) => {
                    self.error = Some("no sub-sectors in the taxonomy".into());
                    self.phase = Phase::Done;
                }
                Err(e) => {
                    self.error = Some(e);
                    self.phase = Phase::Done;
                }
            },
            (Kind::SubSectors, Err(e)) => {
                self.error = Some(e);
                self.phase = Phase::Done;
            }
            (Kind::Onboard, Ok(out)) => {
                let report = parse_report(&out);
                if self.sub.is_none() && needs_sub(&report) {
                    // Same as nvim: ask for the sub-sector, then run again.
                    self.job = Some(spawn_job(Kind::SubSectors, vec!["--list-subs".into()]));
                    self.phase = Phase::Running;
                    return;
                }
                self.report = Some(report);
                self.raw = out;
                self.phase = Phase::Done;
            }
            (Kind::Onboard, Err(e)) => {
                self.error = Some(e);
                self.phase = Phase::Done;
            }
        }
    }

    /// Picks up the job's result once it lands; the loop calls this every poll.
    fn poll_job(&mut self) {
        let Some(job) = self.job.as_ref() else {
            return;
        };
        let result = match job.rx.try_recv() {
            Ok(r) => r,
            Err(TryRecvError::Empty) => return,
            Err(TryRecvError::Disconnected) => Err("job thread ended unexpectedly".into()),
        };
        let kind = job.kind;
        self.job = None;
        self.finish(kind, result);
    }

    fn steps_so_far(&self) -> Vec<String> {
        self.job
            .as_ref()
            .map(|j| lock(&j.shared).steps.clone())
            .unwrap_or_default()
    }

    fn header_tickers(&self) -> String {
        if self.tickers.is_empty() {
            self.input.clone()
        } else {
            self.tickers.join(" ")
        }
    }

    fn draw_running(&self, frame: &mut Frame, body: ratatui::layout::Rect) {
        let t = self.theme;
        let Some(job) = self.job.as_ref() else {
            return;
        };
        let secs = job.started.elapsed().as_secs();
        let mut lines = Vec::new();
        match job.kind {
            Kind::SubSectors => lines.push(Line::styled("loading sub-sectors…", t.base())),
            Kind::Onboard => {
                lines.push(Line::styled(
                    format!("onboarding {} · {secs}s running", self.tickers.join(" ")),
                    t.title(),
                ));
                lines.push(Line::raw(""));
                let steps = self.steps_so_far();
                if steps.is_empty() {
                    lines.push(Line::styled("  starting…", t.dim()));
                }
                let last = steps.len().saturating_sub(1);
                for (i, name) in steps.iter().enumerate() {
                    let line = if i == last {
                        Line::styled(format!("  … {name}"), t.accent())
                    } else {
                        Line::styled(format!("  ✓ {name}"), t.dim())
                    };
                    lines.push(line);
                }
            }
        }
        frame.render_widget(Paragraph::new(lines).style(t.base()), body);
    }

    fn draw_subpick(&mut self, frame: &mut Frame, body: ratatui::layout::Rect) {
        let t = self.theme;
        let header = format!("sub-sector for {}:", self.tickers.join(" "));
        let [head, list] =
            Layout::vertical([Constraint::Length(2), Constraint::Min(1)]).areas(body);
        frame.render_widget(Paragraph::new(Line::styled(header, t.accent())), head);
        if let Phase::SubPick { subs, state } = &mut self.phase {
            let items: Vec<ListItem> = subs
                .iter()
                .map(|s| ListItem::new(Line::styled(format!("  {s}"), t.base())))
                .collect();
            frame.render_stateful_widget(
                List::new(items)
                    .style(t.base())
                    .highlight_style(t.selected()),
                list,
                state,
            );
        }
    }

    fn draw_done(&mut self, frame: &mut Frame, body: ratatui::layout::Rect) {
        let t = self.theme;
        let mut lines: Vec<Line> = Vec::new();
        if let Some(e) = &self.error {
            lines.extend(e.lines().map(|l| Line::styled(l.to_string(), t.down())));
        }
        if let Some(r) = &self.report {
            lines.extend(report_lines(r, &self.raw, t));
        }
        let max = (lines.len() as u16).saturating_sub(body.height);
        self.scroll = self.scroll.min(max);
        frame.render_widget(
            Paragraph::new(lines).style(t.base()).scroll((self.scroll, 0)),
            body,
        );
    }
}

impl Screen for Onboard {
    fn leader_ok(&self) -> bool {
        matches!(self.phase, Phase::Done)
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let prompt = " Onboard › ";
        let header_text = match self.phase {
            Phase::Input => self.input.clone(),
            _ => self.header_tickers(),
        };
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(vec![
                    Span::styled(prompt, t.accent()),
                    Span::styled(header_text, t.base()),
                ]),
                Line::raw(""),
            ]),
            head,
        );
        if matches!(self.phase, Phase::Input) {
            frame.set_cursor_position((
                head.x + (text::width(prompt) + text::width(&self.input)) as u16,
                head.y,
            ));
        }

        let inner = body.inner(ratatui::layout::Margin::new(1, 0));
        match self.phase {
            Phase::Input => {
                let mut lines = Vec::new();
                if let Some(f) = &self.flash {
                    lines.push(Line::styled(f.clone(), t.down()));
                }
                lines.push(Line::styled(
                    "  Tickers in the universe run every puller and rebuild their dossiers.",
                    t.dim(),
                ));
                lines.push(Line::styled(
                    "  A new ticker is added first and asks for its sub-sector.",
                    t.dim(),
                ));
                lines.push(Line::styled("  Space or comma separated. Expect minutes.", t.dim()));
                frame.render_widget(Paragraph::new(lines), inner);
            }
            Phase::Running => self.draw_running(frame, inner),
            Phase::SubPick { .. } => self.draw_subpick(frame, inner),
            Phase::Done => self.draw_done(frame, inner),
        }

        let keys = match self.phase {
            Phase::Input => " ↵ run · esc back",
            Phase::Running => " esc cancel",
            Phase::SubPick { .. } => " j/k move · ↵ onboard · esc back",
            Phase::Done => " j/k scroll · esc back",
        };
        frame.render_widget(Paragraph::new(keys).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match &mut self.phase {
            Phase::Input => match key.code {
                KeyCode::Esc => Action::Quit,
                KeyCode::Enter => {
                    self.submit();
                    Action::None
                }
                KeyCode::Backspace => {
                    self.input.pop();
                    Action::None
                }
                KeyCode::Char(c) if !ctrl => {
                    self.input.push(c);
                    Action::None
                }
                _ => Action::None,
            },
            Phase::Running => match key.code {
                KeyCode::Esc | KeyCode::Char('q') => {
                    self.cancel();
                    Action::Quit
                }
                _ => Action::None,
            },
            Phase::SubPick { subs, state } => match key.code {
                KeyCode::Esc => {
                    self.phase = Phase::Input;
                    self.flash = Some("cancelled; the ticker was not onboarded".into());
                    Action::None
                }
                KeyCode::Down | KeyCode::Char('j') => {
                    let n = subs.len();
                    let cur = state.selected().unwrap_or(0);
                    state.select(Some((cur + 1) % n));
                    Action::None
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    let n = subs.len();
                    let cur = state.selected().unwrap_or(0);
                    state.select(Some((cur + n - 1) % n));
                    Action::None
                }
                KeyCode::Enter => {
                    let chosen = state.selected().and_then(|i| subs.get(i)).cloned();
                    if let Some(sub) = chosen {
                        self.start(Some(sub));
                    }
                    Action::None
                }
                _ => Action::None,
            },
            Phase::Done => match key.code {
                KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
                KeyCode::Down | KeyCode::Char('j') => {
                    self.scroll = self.scroll.saturating_add(1);
                    Action::None
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    self.scroll = self.scroll.saturating_sub(1);
                    Action::None
                }
                KeyCode::PageDown => {
                    self.scroll = self.scroll.saturating_add(10);
                    Action::None
                }
                KeyCode::PageUp => {
                    self.scroll = self.scroll.saturating_sub(10);
                    Action::None
                }
                _ => Action::None,
            },
        }
    }

    fn tick(&mut self) -> Action {
        self.poll_job();
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};
    use ratatui::Terminal;

    use super::*;

    const SAMPLE: &str = "\
… universe
… profile
… financials

onboard AAPL SKHY  (84.2s)
  ✓ universe        0.4s  already in universe
  ✓ profile         2.1s  2 fetched, missing []
  ✗ financials     11.0s  ValueError: no CIK
  - filing_text     0.0s
  ✓ dossier        20.5s  AAPL 14 sections; SKHY 12 sections [financials:empty]
  AAPL: all dossier sections populated
  SKHY: financials:empty, segments:missing
";

    fn key(code: KeyCode) -> KeyEvent {
        KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        }
    }

    fn screen(arg: Option<&str>) -> Onboard {
        open(
            &Ctx {
                db_path: "unused".into(),
                theme: Theme::default(),
            },
            arg.map(str::to_string),
        )
        .unwrap()
    }

    fn rendered(s: &mut Onboard, cols: u16, rows: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(cols, rows)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        let buf = term.backend().buffer().clone();
        (0..rows)
            .map(|y| (0..cols).map(|x| buf[(x, y)].symbol()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn tickers_split_on_space_and_comma_and_uppercase() {
        assert_eq!(
            parse_tickers("aapl, skhy  aapl\tbrk.b"),
            Ok(vec!["AAPL".into(), "SKHY".into(), "BRK.B".into()])
        );
        assert_eq!(parse_tickers("  ,  "), Ok(vec![]));
        assert_eq!(parse_tickers("--json"), Err("not a ticker: --json".into()));
    }

    #[test]
    fn parses_step_and_health_report() {
        let r = parse_report(SAMPLE);
        assert_eq!(r.tickers, vec!["AAPL", "SKHY"]);
        assert_eq!(r.total_secs, 84.2);
        assert_eq!(r.steps.len(), 5);
        assert_eq!(r.steps[2].name, "financials");
        assert_eq!(r.steps[2].status, "failed");
        assert_eq!(r.steps[2].secs, 11.0);
        assert_eq!(r.steps[2].detail, "ValueError: no CIK");
        assert_eq!(r.steps[3].status, "skipped");
        assert_eq!(r.health["AAPL"], Vec::<String>::new());
        assert_eq!(r.health["SKHY"], vec!["financials:empty", "segments:missing"]);
        assert!(!needs_sub(&r));
    }

    #[test]
    fn unknown_ticker_needs_sub_sector() {
        let out = "onboard NEWCO  (0.1s)\n  ✗ universe        0.1s  ValueError: NEWCO not in the universe: pass --sub <sub_sector>\n";
        assert!(needs_sub(&parse_report(out)));
    }

    #[test]
    fn subs_list_parses_and_rejects_junk() {
        assert_eq!(
            parse_subs("[\"cybersecurity\", \"memory\"]\n"),
            Ok(vec!["cybersecurity".into(), "memory".into()])
        );
        assert!(parse_subs("not json").is_err());
    }

    #[test]
    fn prefilled_arg_is_the_prompt_and_is_editable() {
        // Never call submit() in tests: that starts the real onboarding job.
        let mut s = screen(Some("aapl skhy"));
        assert_eq!(s.input, "aapl skhy");
        assert_eq!(parse_tickers(&s.input), Ok(vec!["AAPL".into(), "SKHY".into()]));
        s.on_key(key(KeyCode::Char('x')));
        assert_eq!(s.input, "aapl skhyx");
        s.on_key(key(KeyCode::Backspace));
        assert_eq!(s.input, "aapl skhy");
        assert_eq!(s.on_key(key(KeyCode::Esc)), Action::Quit);
    }

    #[test]
    fn bad_ticker_stays_on_input_with_message() {
        let mut s = screen(Some("--json"));
        s.submit();
        assert!(matches!(s.phase, Phase::Input));
        assert_eq!(s.flash.as_deref(), Some("not a ticker: --json"));
    }

    #[test]
    fn done_view_shows_steps_and_health() {
        let mut s = screen(None);
        s.tickers = vec!["AAPL".into(), "SKHY".into()];
        s.report = Some(parse_report(SAMPLE));
        s.raw = SAMPLE.into();
        s.phase = Phase::Done;
        let out = rendered(&mut s, 90, 24);
        assert!(out.contains("financials"), "{out}");
        assert!(out.contains("SKHY: financials:empty, segments:missing"), "{out}");
        assert!(out.contains("AAPL: all dossier sections populated"), "{out}");
        assert!(out.contains("slowest"), "{out}");
    }

    #[test]
    fn unreadable_report_falls_back_to_raw_output() {
        let r = parse_report("hello\nworld\n");
        let lines = report_lines(&r, "hello\nworld\n", Theme::default());
        let text: String = lines.iter().map(|l| l.to_string()).collect::<Vec<_>>().join("\n");
        assert!(text.contains("raw output"), "{text}");
        assert!(text.contains("world"), "{text}");
    }

    #[test]
    fn running_view_shows_live_steps() {
        let mut s = screen(None);
        s.tickers = vec!["AAPL".into()];
        s.phase = Phase::Running;
        let shared = Arc::new(Mutex::new(Shared {
            steps: vec!["universe".into(), "profile".into()],
            err: Vec::new(),
        }));
        let (_tx, rx) = mpsc::channel();
        s.job = Some(Job {
            rx,
            child: Arc::new(Mutex::new(None)),
            shared,
            kind: Kind::Onboard,
            started: Instant::now(),
        });
        let out = rendered(&mut s, 70, 12);
        assert!(out.contains("onboarding AAPL"), "{out}");
        assert!(out.contains("✓ universe"), "{out}");
        assert!(out.contains("… profile"), "{out}");
        s.job = None; // no child process in tests
    }

    #[test]
    fn sub_picker_moves_and_escape_returns_to_input() {
        let mut s = screen(None);
        s.tickers = vec!["NEWCO".into()];
        let mut state = ListState::default();
        state.select(Some(0));
        s.phase = Phase::SubPick {
            subs: vec!["cybersecurity".into(), "memory".into()],
            state,
        };
        s.on_key(key(KeyCode::Down));
        match &s.phase {
            Phase::SubPick { state, .. } => assert_eq!(state.selected(), Some(1)),
            _ => panic!("not in sub picker"),
        }
        s.on_key(key(KeyCode::Esc));
        assert!(matches!(s.phase, Phase::Input));
    }
}
