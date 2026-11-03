//! The ticker tape: a row at the bottom of every screen, with the AI-universe
//! names moving on heavy volume and a real price move. A background run of the
//! movers script (py/sources/ticker_tape.py) refreshes it every few minutes,
//! and the row scrolls from left to right while it waits. Outside the regular
//! session each name also shows its pre-market (PM) or after-hours (AH) move.

use std::sync::mpsc::{Receiver, TryRecvError};
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;

use crate::pyrun;
use crate::ui::text;
use crate::ui::theme::Theme;

const TAPE_SCRIPT: &str = "py/sources/ticker_tape.py";
const TAPE_EVERY: Duration = Duration::from_secs(300);
/// Columns the lane scrolls per second, left to right.
const TAPE_SPEED: f64 = 10.0;

/// One name on the tape: heavy volume and a real move, from the movers script.
#[derive(Clone, Debug, PartialEq)]
pub struct Mover {
    ticker: String,
    pct: f64,
    ratio: f64,
    /// The extended-hours move against the last regular close, labelled PM or
    /// AH. None in the regular session or when Yahoo has no fresh print.
    ext: Option<(String, f64)>,
}

#[derive(Clone, Debug, Default, PartialEq)]
enum TapeStatus {
    #[default]
    Loading,
    Ready,
    Failed(String),
}

/// The tape's state. `tick` runs the movers script in the background and
/// advances the scroll; `draw` paints the row.
pub struct Tape {
    enabled: bool,
    status: TapeStatus,
    movers: Vec<Mover>,
    /// Columns scrolled so far. The text moves right as this grows.
    shift: f64,
    at: Instant,
    /// When the last run finished, successful or not.
    fetched: Option<Instant>,
    rx: Option<Receiver<Result<String, String>>>,
}

impl Tape {
    pub fn new() -> Self {
        Self {
            enabled: true,
            status: TapeStatus::Loading,
            movers: Vec::new(),
            shift: 0.0,
            at: Instant::now(),
            fetched: None,
            rx: None,
        }
    }

    /// A tape that never runs and is never drawn: tests, and screens with no bottom row.
    pub fn off() -> Self {
        Self {
            enabled: false,
            ..Self::new()
        }
    }

    /// Whether the tape row is shown at all.
    pub fn enabled(&self) -> bool {
        self.enabled
    }

    /// Advances the scroll, collects a finished run, and starts a new one
    /// when the last is older than TAPE_EVERY.
    pub fn tick(&mut self, now: Instant) {
        if !self.enabled {
            return;
        }
        let dt = now.duration_since(self.at).as_secs_f64().min(0.5);
        self.at = now;
        self.shift += dt * TAPE_SPEED;
        if let Some(rx) = &self.rx {
            match rx.try_recv() {
                Ok(res) => {
                    self.rx = None;
                    self.fetched = Some(now);
                    self.apply(res);
                }
                Err(TryRecvError::Empty) => {}
                Err(TryRecvError::Disconnected) => {
                    self.rx = None;
                    self.fetched = Some(now);
                    self.status = TapeStatus::Failed("the movers run stopped".into());
                }
            }
        } else if self.fetched.is_none_or(|f| now.duration_since(f) >= TAPE_EVERY) {
            self.rx = Some(pyrun::spawn_script(TAPE_SCRIPT, &[]));
        }
    }

    fn apply(&mut self, res: Result<String, String>) {
        match res.and_then(|out| parse_movers(&out)) {
            Ok(movers) => {
                self.movers = movers;
                self.status = TapeStatus::Ready;
            }
            Err(e) => self.status = TapeStatus::Failed(e),
        }
    }

    /// Paints the row: the scrolling lane across the full width. Before the
    /// first read, or when the read failed or found nothing, it says so instead.
    pub fn draw(&self, frame: &mut Frame, lane: Rect, t: Theme) {
        let w = lane.width as usize;
        let note = match &self.status {
            TapeStatus::Loading => Some("reading movers from Yahoo…".to_string()),
            TapeStatus::Failed(e) => Some(format!(
                "movers unavailable: {}",
                e.lines().next().unwrap_or_default()
            )),
            TapeStatus::Ready if self.movers.is_empty() => {
                Some("quiet: no name on heavy volume with a 2% move".to_string())
            }
            TapeStatus::Ready => None,
        };
        match note {
            Some(msg) => frame.render_widget(
                Paragraph::new(Line::styled(text::truncate(&msg, w), t.dim())),
                lane,
            ),
            None => {
                let cells = tape_cells(&self.movers, t);
                frame.render_widget(
                    Paragraph::new(tape_window(&cells, self.shift as usize, w)),
                    lane,
                );
            }
        }
    }
}

/// The script's JSON -> movers.
fn parse_movers(out: &str) -> Result<Vec<Mover>, String> {
    let v: serde_json::Value =
        serde_json::from_str(out).map_err(|e| format!("bad movers output: {e}"))?;
    let movers = v["movers"]
        .as_array()
        .map(|rows| {
            rows.iter()
                .filter_map(|m| {
                    Some(Mover {
                        ticker: m["ticker"].as_str()?.to_string(),
                        pct: m["pct"].as_f64()?,
                        ratio: m["ratio"].as_f64()?,
                        ext: m["ext_label"]
                            .as_str()
                            .zip(m["ext_pct"].as_f64())
                            .map(|(l, p)| (l.to_string(), p)),
                    })
                })
                .collect()
        })
        .unwrap_or_default();
    Ok(movers)
}

/// One pass of the tape, cell by cell: each mover as ticker, signed move, and
/// volume against its 10-day average, then any pre-market or after-hours
/// move, separated by dots.
fn tape_cells(movers: &[Mover], t: Theme) -> Vec<(char, Style)> {
    let mut cells = Vec::new();
    let mut push = |s: &str, st: Style| cells.extend(s.chars().map(|c| (c, st)));
    for m in movers {
        let arrow = if m.pct >= 0.0 { "▲" } else { "▼" };
        push(&m.ticker, t.title());
        push(" ", t.dim());
        push(&format!("{arrow}{:+.1}%", m.pct), t.signed(m.pct));
        push(&format!(" {:.1}×", m.ratio), t.dim());
        if let Some((label, pct)) = &m.ext {
            let arrow = if *pct >= 0.0 { "▲" } else { "▼" };
            push(&format!("  {label} "), t.dim());
            push(&format!("{arrow}{pct:+.1}%"), t.signed(*pct));
        }
        push("  ·  ", t.dim());
    }
    cells
}

/// The lane's visible slice of the endless tape, `w` columns wide. The tape
/// repeats; `shift` columns in, the text has moved that far to the right.
fn tape_window(cells: &[(char, Style)], shift: usize, w: usize) -> Line<'static> {
    if cells.is_empty() || w == 0 {
        return Line::default();
    }
    let n = cells.len();
    let start = n - shift % n;
    let mut out: Vec<Span<'static>> = Vec::new();
    let mut buf = String::new();
    let mut cur: Option<Style> = None;
    for i in 0..w {
        let (c, st) = cells[(start + i) % n];
        if cur != Some(st) {
            if let Some(s) = cur {
                out.push(Span::styled(std::mem::take(&mut buf), s));
            }
            cur = Some(st);
        }
        buf.push(c);
    }
    if let Some(s) = cur {
        out.push(Span::styled(buf, s));
    }
    Line::from(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn plain(line: &Line) -> String {
        line.spans.iter().map(|s| s.content.as_ref()).collect()
    }

    #[test]
    fn movers_json_becomes_rows() {
        let out = r#"{"asof":"2026-11-02T15:16","checked":463,"movers":[
            {"ticker":"MRVL","price":170.35,"pct":-13.26,"ratio":2.14,"volume":1},
            {"ticker":"TEM","price":80.29,"pct":11.17,"ratio":2.47,"volume":1}]}"#;
        let movers = parse_movers(out).unwrap();
        assert_eq!(movers[0].ticker, "MRVL");
        assert_eq!(movers[1].pct, 11.17);
        assert_eq!(movers[0].ext, None);
        assert!(parse_movers("not json").is_err());
    }

    #[test]
    fn extended_hours_fields_are_read_when_present() {
        let out = r#"{"movers":[
            {"ticker":"AEHR","pct":-6.23,"ratio":1.9,"ext_label":"AH","ext_pct":13.99},
            {"ticker":"KVYO","pct":8.24,"ratio":2.5,"ext_label":null,"ext_pct":null}]}"#;
        let movers = parse_movers(out).unwrap();
        assert_eq!(movers[0].ext, Some(("AH".to_string(), 13.99)));
        assert_eq!(movers[1].ext, None);
    }

    #[test]
    fn tape_scrolls_left_to_right() {
        let cells: Vec<(char, Style)> = "abcd".chars().map(|c| (c, Style::default())).collect();
        assert_eq!(plain(&tape_window(&cells, 0, 4)), "abcd");
        // One column in, the text has moved right: the last cell comes first.
        assert_eq!(plain(&tape_window(&cells, 1, 4)), "dabc");
        // Wraps around the endless tape.
        assert_eq!(plain(&tape_window(&cells, 5, 4)), "dabc");
        assert_eq!(plain(&tape_window(&[], 3, 4)), "");
    }

    #[test]
    fn tape_text_carries_the_ticker_move_and_volume() {
        let t = Theme::default();
        let movers = [Mover { ticker: "TEM".into(), pct: 11.17, ratio: 2.47, ext: None }];
        let text: String = tape_cells(&movers, t).into_iter().map(|(c, _)| c).collect();
        assert!(text.starts_with("TEM ▲+11.2% 2.5×  ·  "), "{text}");
    }

    #[test]
    fn tape_text_adds_the_extended_hours_move() {
        let t = Theme::default();
        let movers = [
            Mover { ticker: "AEHR".into(), pct: -6.23, ratio: 1.9, ext: Some(("AH".into(), 3.1)) },
            Mover { ticker: "NVDA".into(), pct: 2.0, ratio: 1.6, ext: Some(("PM".into(), -1.04)) },
        ];
        let cells = tape_cells(&movers, t);
        let text: String = cells.iter().map(|(c, _)| *c).collect();
        assert_eq!(
            text,
            "AEHR ▼-6.2% 1.9×  AH ▲+3.1%  ·  NVDA ▲+2.0% 1.6×  PM ▼-1.0%  ·  "
        );
        // The extended move takes its own sign's colour, not the day's: the
        // first '+' is AEHR's after-hours gain on a down day.
        let plus = text.chars().position(|c| c == '+').unwrap();
        assert_eq!(cells[plus].1, t.signed(3.1));
        assert_ne!(cells[plus].1, t.signed(-6.23));
    }

    #[test]
    fn an_off_tape_never_starts_a_run() {
        let mut tape = Tape::off();
        tape.tick(Instant::now());
        assert!(tape.rx.is_none());
        assert!(!tape.enabled());
    }
}
