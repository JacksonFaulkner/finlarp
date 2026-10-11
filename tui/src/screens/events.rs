// Catalyst calendar (`fl events`): the calendar component (ui/calendar.rs)
// over dated AI-stock catalysts from fixtures/catalysts.json. Dates marked
// `est` in the file are unconfirmed (estimated from past cadence) and render
// with a leading `~`.
//
// Enter on a day opens its day view (the event list); Enter on an event that
// has a page in fixtures/catalyst_pages.json opens it (screens/catalyst_page).
//
// Argument: a view (`month` | `week` | `day`) and/or a start date
// (`YYYY-MM-DD`), e.g. `fl events week 2026-10-06`.

use std::io;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::widgets::Block;
use serde::Deserialize;

use super::catalyst_page::{self, Outcome, Page};
use crate::app::{Action, Ctx, Screen};
use crate::ui::calendar::{self, Calendar, Event, Tone, View};
use crate::ui::help::{self, Key, key};
use crate::ui::theme::Theme;

const FOOTER: &[Key] = &[
    key("?", "help"),
    key("m/w/d", "view"),
    key("W", "weekends"),
    key("h/l", "day"),
    key("j/k", "week"),
    key("[ ]", "period"),
    key("t", "today"),
    key("enter", "day / page"),
    key("q", "quit"),
];

#[derive(Deserialize)]
struct Catalyst {
    date: String,
    time: Option<String>,
    label: String,
    detail: Option<String>,
    tone: String,
    est: bool,
}

fn catalysts() -> Vec<Event> {
    let raw: Vec<Catalyst> =
        serde_json::from_str(include_str!("fixtures/catalysts.json")).expect("catalysts.json");
    raw.into_iter()
        .map(|c| Event {
            date: NaiveDate::parse_from_str(&c.date, "%Y-%m-%d").expect("catalyst date"),
            time: c.time,
            label: if c.est {
                format!("~{}", c.label)
            } else {
                c.label
            },
            detail: c.detail,
            tone: match c.tone.as_str() {
                "bull" => Tone::Up,
                "bear" => Tone::Down,
                "risk" => Tone::Accent,
                _ => Tone::Plain,
            },
        })
        .collect()
}

pub struct Events {
    cal: Calendar,
    theme: Theme,
    help: bool,
    pages: Vec<Page>,
    /// The open catalyst page, if any.
    page: Option<catalyst_page::View>,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Events> {
    let today = chrono::Local::now().date_naive();
    open_with(ctx, arg.as_deref(), today, catalysts())
}

fn open_with(
    ctx: &Ctx,
    arg: Option<&str>,
    today: NaiveDate,
    events: Vec<Event>,
) -> io::Result<Events> {
    let mut cal = Calendar::new(today, events, ctx.theme);
    for word in arg.unwrap_or_default().split_whitespace() {
        cal = match word {
            "month" => cal.with_view(View::Month),
            "week" => cal.with_view(View::Week),
            "day" => cal.with_view(View::Day),
            w => match NaiveDate::parse_from_str(w, "%Y-%m-%d") {
                Ok(d) => cal.with_cursor(d),
                Err(_) => {
                    return Err(io::Error::other(format!(
                        "events: expected month|week|day or YYYY-MM-DD, got {w:?}"
                    )));
                }
            },
        };
    }
    Ok(Events {
        cal,
        theme: ctx.theme,
        help: false,
        pages: catalyst_page::load(),
        page: None,
    })
}

impl Events {
    /// Enter: month/week -> day view of the cursor day; day view -> the
    /// selected event's page, if it has one.
    fn enter(&mut self) {
        if self.cal.view() != View::Day {
            self.cal.set_view(View::Day);
            return;
        }
        let Some(e) = self.cal.selected_event() else {
            return;
        };
        if let Some(i) = catalyst_page::find(&self.pages, e.date, &e.label) {
            self.page = Some(catalyst_page::View::new(i));
        }
    }
}

impl Screen for Events {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [body, foot] =
            Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).areas(area);
        if let Some(page) = &mut self.page {
            page.draw(&self.pages, frame, body, &t);
            help::render_footer(frame, foot, catalyst_page::KEYS, None, &t);
            return;
        }
        self.cal.draw(frame, body);
        help::render_footer(frame, foot, FOOTER, None, &t);
        if self.help {
            help::render_overlay(frame, area, "events keys", calendar::KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if let Some(page) = &mut self.page {
            if page.on_key(&self.pages, key) == Outcome::Close {
                self.page = None;
            }
            return Action::None;
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        match key.code {
            KeyCode::Enter => {
                self.enter();
                Action::None
            }
            KeyCode::Char('q') | KeyCode::Esc => Action::Quit,
            KeyCode::Char('?') => {
                self.help = true;
                Action::None
            }
            _ => {
                self.cal.on_key(key);
                Action::None
            }
        }
    }

    fn needs_redraw(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState, KeyModifiers};

    use super::*;

    fn ctx() -> Ctx {
        Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        }
    }

    fn today() -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, 10, 10).unwrap()
    }

    fn press(s: &mut Events, c: char) -> Action {
        s.on_key(KeyEvent {
            code: KeyCode::Char(c),
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    #[test]
    fn args_pick_view_and_date() {
        let s = open_with(&ctx(), Some("week 2026-10-06"), today(), Vec::new()).unwrap();
        assert_eq!(s.cal.view(), View::Week);
        assert_eq!(
            s.cal.cursor(),
            NaiveDate::from_ymd_opt(2026, 10, 6).unwrap()
        );
        let s = open_with(&ctx(), None, today(), Vec::new()).unwrap();
        assert_eq!((s.cal.view(), s.cal.cursor()), (View::Month, today()));
        assert!(open_with(&ctx(), Some("nope"), today(), Vec::new()).is_err());
    }

    #[test]
    fn catalysts_load_and_enter_walks_day_then_page() {
        let ev = catalysts();
        assert!(ev.len() >= 45);
        assert!(ev.iter().any(|e| e.label.starts_with('~')));
        let mut s = open_with(&ctx(), Some("2026-11-03"), today(), ev).unwrap();
        let enter = |s: &mut Events| {
            s.on_key(KeyEvent {
                code: KeyCode::Enter,
                modifiers: KeyModifiers::NONE,
                kind: KeyEventKind::Press,
                state: KeyEventState::NONE,
            })
        };
        // month view: Enter drops into the day view, no page yet
        enter(&mut s);
        assert_eq!(s.cal.view(), View::Day);
        assert!(s.page.is_none());
        // day view lists AMD, ANET, PLTR, ...: select the first event with a page
        let n = s.cal.events_on(s.cal.cursor()).len();
        assert!(n >= 3);
        let mut opened = false;
        for _ in 0..n {
            enter(&mut s);
            if s.page.is_some() {
                opened = true;
                break;
            }
            press(&mut s, 'j');
        }
        assert!(opened);
        // q closes the page, not the screen
        assert_eq!(press(&mut s, 'q'), Action::None);
        assert!(s.page.is_none());
        assert_eq!(press(&mut s, 'q'), Action::Quit);
    }

    #[test]
    fn keys_route_to_calendar_help_and_quit() {
        let mut s = open_with(&ctx(), None, today(), Vec::new()).unwrap();
        assert_eq!(press(&mut s, 'w'), Action::None);
        assert_eq!(s.cal.view(), View::Week);
        press(&mut s, '?');
        assert!(s.help);
        press(&mut s, 'q'); // closes help, doesn't quit
        assert!(!s.help);
        assert_eq!(press(&mut s, 'q'), Action::Quit);
    }
}
