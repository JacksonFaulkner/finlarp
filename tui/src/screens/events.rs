// Catalyst calendar (`fl events`): the calendar component (ui/calendar.rs)
// over dated events. The catalyst source isn't wired up yet, so the calendar
// opens empty.
//
// Argument: a view (`month` | `week` | `day`) and/or a start date
// (`YYYY-MM-DD`), e.g. `fl events week 2026-10-06`.

use std::io;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::widgets::Block;

use crate::app::{Action, Ctx, Screen};
use crate::ui::calendar::{self, Calendar, Event, View};
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
    key("q", "quit"),
];

pub struct Events {
    cal: Calendar,
    theme: Theme,
    help: bool,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Events> {
    let today = chrono::Local::now().date_naive();
    open_with(ctx, arg.as_deref(), today, Vec::new())
}

fn open_with(ctx: &Ctx, arg: Option<&str>, today: NaiveDate, events: Vec<Event>) -> io::Result<Events> {
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
    })
}

impl Screen for Events {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [body, foot] = Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).areas(area);
        self.cal.draw(frame, body);
        help::render_footer(frame, foot, FOOTER, None, &t);
        if self.help {
            help::render_overlay(frame, area, "events keys", calendar::KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        match key.code {
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
        assert_eq!(s.cal.cursor(), NaiveDate::from_ymd_opt(2026, 10, 6).unwrap());
        let s = open_with(&ctx(), None, today(), Vec::new()).unwrap();
        assert_eq!((s.cal.view(), s.cal.cursor()), (View::Month, today()));
        assert!(open_with(&ctx(), Some("nope"), today(), Vec::new()).is_err());
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
