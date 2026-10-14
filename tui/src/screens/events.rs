// Catalyst calendar (`fl events`): the calendar component (ui/calendar.rs)
// over dated AI-stock catalysts from fixtures/catalysts.json. Dates marked
// `est` in the file are unconfirmed (estimated from past cadence) and render
// with a leading `~`.
//
// Enter on a day opens its day view (the event list); Enter on an event that
// has a page in fixtures/catalyst_pages.json opens it (screens/catalyst_page).
//
// Tweet layer (`T`): every tweet that names a universe ticker, from
// py/derive/tweet_calendar.py. Month and week cells show one line per day
// (count, busiest tickers, net stance); the day view lists the tweets one per
// row (ET time, @author, tickers with their labelled stance, text) and Enter
// opens the post. `f` (or `/`) filters the layer by ticker, e.g. `MU NVDA`;
// `F` clears the filter. Catalysts always stay on.
//
// Argument: a view (`month` | `week` | `day`), a start date (`YYYY-MM-DD`),
// `tweets` to open with the layer on, and `t:MU,NVDA` to open filtered, e.g.
// `fl events day 2026-10-09 t:MU`.

use std::collections::BTreeMap;
use std::io;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{Event as TermEvent, KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};
use serde::Deserialize;
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use super::catalyst_page::{self, Outcome, Page};
use crate::app::{Action, Ctx, Screen};
use crate::pyrun;
use crate::ui::calendar::{self, Calendar, Event, Tone, View};
use crate::ui::help::{self, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

const FOOTER: &[Key] = &[
    key("?", "help"),
    key("m/w/d", "view"),
    key("W", "weekends"),
    key("h/l", "day"),
    key("j/k", "week"),
    key("[ ]", "period"),
    key("t", "today"),
    key("T", "tweets"),
    key("f", "ticker filter"),
    key("enter", "day / open"),
    key("q", "quit"),
];

/// Keys the events screen adds to the calendar's own (for the `?` overlay).
const EXTRA_KEYS: &[Key] = &[
    key("T", "show / hide the tweet layer"),
    key(
        "f /",
        "filter tweets by ticker (space separated; empty clears)",
    ),
    key("F", "clear the ticker filter"),
    key(
        "enter",
        "month/week: day view; day view: open the catalyst page or the tweet",
    ),
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
            link: None,
        })
        .collect()
}

// ---- tweet layer ----------------------------------------------------------------

#[derive(Deserialize)]
struct Payload {
    tweets: Vec<RawTweet>,
}

/// One row of tweet_calendar.json (short keys keep the file small; see py/derive/tweet_calendar.py).
#[derive(Deserialize)]
struct RawTweet {
    d: String,
    t: String,
    h: String,
    u: String,
    x: String,
    l: u64,
    v: u64,
    r: u8,
    k: Vec<(String, Option<i32>)>,
}

#[derive(Debug, Clone)]
pub struct Tweet {
    date: NaiveDate,
    time: String,
    handle: String,
    url: String,
    text: String,
    likes: u64,
    views: u64,
    reply: bool,
    /// Universe tickers it names, with the labelled stance (-2..2) when there is one.
    tickers: Vec<(String, Option<i32>)>,
}

fn parse_tweets(json: &str) -> Result<Vec<Tweet>, String> {
    let p: Payload = serde_json::from_str(json).map_err(|e| format!("tweet_calendar.json: {e}"))?;
    Ok(p.tweets
        .into_iter()
        .filter_map(|r| {
            Some(Tweet {
                date: NaiveDate::parse_from_str(&r.d, "%Y-%m-%d").ok()?,
                time: r.t,
                handle: r.h,
                url: r.u,
                text: r.x,
                likes: r.l,
                views: r.v,
                reply: r.r != 0,
                tickers: r.k,
            })
        })
        .collect())
}

fn load_tweets() -> Result<Vec<Tweet>, String> {
    parse_tweets(&pyrun::run_script("py/derive/tweet_calendar.py", &[])?)
}

/// Tickers typed in the filter prompt or the `t:` argument: split on spaces and commas, `$` dropped, upper-cased.
fn parse_filter(s: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for w in s.split(|c: char| c.is_whitespace() || c == ',') {
        let w = w.trim_start_matches('$').to_uppercase();
        if !w.is_empty() && !out.contains(&w) {
            out.push(w);
        }
    }
    out
}

/// `MU+1`, `NVDA-2`, or just the symbol when the tweet is unlabelled or neutral for it.
fn ticker_tag(t: &str, stance: Option<i32>) -> String {
    match stance {
        Some(s) if s != 0 => format!("{t}{s:+}"),
        _ => t.to_string(),
    }
}

/// Mean labelled stance over the tickers that count (the filtered ones, else all), None when nothing is labelled.
fn net_stance(tw: &Tweet, filter: &[String]) -> Option<f64> {
    let s: Vec<i32> = tw
        .tickers
        .iter()
        .filter(|(t, _)| filter.is_empty() || filter.contains(t))
        .filter_map(|(_, s)| *s)
        .collect();
    (!s.is_empty()).then(|| f64::from(s.iter().sum::<i32>()) / s.len() as f64)
}

fn stance_tone(net: Option<f64>, cut: f64) -> Tone {
    match net {
        Some(n) if n > cut => Tone::Up,
        Some(n) if n < -cut => Tone::Down,
        _ => Tone::Plain,
    }
}

fn matches(tw: &Tweet, filter: &[String]) -> bool {
    filter.is_empty() || tw.tickers.iter().any(|(t, _)| filter.contains(t))
}

/// Calendar events for the tweet layer: one per tweet in the day view, one summary per day otherwise.
fn tweet_events(tweets: &[Tweet], filter: &[String], per_tweet: bool) -> Vec<Event> {
    let shown = tweets.iter().filter(|tw| matches(tw, filter));
    if per_tweet {
        return shown
            .map(|tw| {
                let mut tickers: Vec<&(String, Option<i32>)> = tw.tickers.iter().collect();
                // the filtered tickers first, so the one you asked about is always visible
                tickers.sort_by_key(|(t, _)| !filter.contains(t));
                let more = tickers.len().saturating_sub(4);
                let tags: Vec<String> = tickers
                    .iter()
                    .take(4)
                    .map(|(t, s)| ticker_tag(t, *s))
                    .collect();
                let reply = if tw.reply { "↩ " } else { "" };
                Event {
                    date: tw.date,
                    time: Some(tw.time.clone()),
                    label: format!(
                        "@{} {}{}{}",
                        tw.handle,
                        tags.join(" "),
                        if more > 0 {
                            format!(" +{more}")
                        } else {
                            String::new()
                        },
                        format_args!("  {reply}{}", tw.text)
                    ),
                    detail: Some(format!(
                        "{}  ·  {} likes · {} views · {}",
                        tw.text,
                        tw.likes,
                        tw.views,
                        text::short_url(&tw.url)
                    )),
                    tone: stance_tone(net_stance(tw, filter), 0.0),
                    link: (!tw.url.is_empty()).then(|| tw.url.clone()),
                }
            })
            .collect();
    }
    let mut days: BTreeMap<NaiveDate, Vec<&Tweet>> = BTreeMap::new();
    for tw in shown {
        days.entry(tw.date).or_default().push(tw);
    }
    days.into_iter()
        .map(|(date, tws)| {
            let nets: Vec<f64> = tws.iter().filter_map(|tw| net_stance(tw, filter)).collect();
            let net = (!nets.is_empty()).then(|| nets.iter().sum::<f64>() / nets.len() as f64);
            let tail = if filter.is_empty() {
                let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
                for tw in &tws {
                    for (t, _) in &tw.tickers {
                        *counts.entry(t.as_str()).or_default() += 1;
                    }
                }
                let mut top: Vec<(&str, usize)> = counts.into_iter().collect();
                top.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
                top.iter()
                    .take(3)
                    .map(|(t, n)| format!("{t}×{n}"))
                    .collect::<Vec<_>>()
                    .join(" ")
            } else {
                net.map(|n| format!("{n:+.1}")).unwrap_or_default()
            };
            Event {
                date,
                time: None,
                label: format!("{} tweets {tail}", tws.len())
                    .trim_end()
                    .to_string(),
                detail: None,
                tone: stance_tone(net, 0.25),
                link: None,
            }
        })
        .collect()
}

// ---- the screen -------------------------------------------------------------------

pub struct Events {
    cal: Calendar,
    theme: Theme,
    help: bool,
    pages: Vec<Page>,
    /// The open catalyst page, if any.
    page: Option<catalyst_page::View>,
    /// The fixed catalysts; the tweet layer is added on top of these.
    catalysts: Vec<Event>,
    /// Loaded on first use (`T`, `f`, or the `tweets` / `t:` argument).
    tweets: Option<Vec<Tweet>>,
    loader: fn() -> Result<Vec<Tweet>, String>,
    show_tweets: bool,
    filter: Vec<String>,
    /// The ticker prompt while it is open.
    prompt: Option<Input>,
    /// What the calendar was last built for: (view, layer on, filter).
    built: (View, bool, Vec<String>),
    flash: Option<String>,
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
    let mut cal = Calendar::new(today, events.clone(), ctx.theme);
    let (mut want_tweets, mut filter) = (false, Vec::new());
    for word in arg.unwrap_or_default().split_whitespace() {
        if word == "tweets" {
            want_tweets = true;
            continue;
        }
        if let Some(list) = word
            .strip_prefix("t:")
            .or_else(|| word.strip_prefix("ticker:"))
        {
            want_tweets = true;
            filter = parse_filter(list);
            continue;
        }
        cal = match word {
            "month" => cal.with_view(View::Month),
            "week" => cal.with_view(View::Week),
            "day" => cal.with_view(View::Day),
            w => match NaiveDate::parse_from_str(w, "%Y-%m-%d") {
                Ok(d) => cal.with_cursor(d),
                Err(_) => {
                    return Err(io::Error::other(format!(
                        "events: expected month|week|day, YYYY-MM-DD, tweets or t:TICKER, got {w:?}"
                    )));
                }
            },
        };
    }
    let mut s = Events {
        built: (cal.view(), false, Vec::new()),
        cal,
        theme: ctx.theme,
        help: false,
        pages: catalyst_page::load(),
        page: None,
        catalysts: events,
        tweets: None,
        loader: load_tweets,
        show_tweets: false,
        filter,
        prompt: None,
        flash: None,
    };
    if want_tweets {
        s.show_tweets = s.ensure_tweets();
        s.rebuild();
    }
    Ok(s)
}

impl Events {
    fn ensure_tweets(&mut self) -> bool {
        if self.tweets.is_none() {
            match (self.loader)() {
                Ok(t) => self.tweets = Some(t),
                Err(e) => {
                    self.flash = Some(format!(
                        "tweets unavailable: {}",
                        e.lines().next().unwrap_or("")
                    ));
                    return false;
                }
            }
        }
        true
    }

    fn status(&self) -> String {
        if !self.show_tweets {
            return String::new();
        }
        let who = if self.filter.is_empty() {
            "all tickers".to_string()
        } else {
            self.filter
                .iter()
                .map(|t| format!("${t}"))
                .collect::<Vec<_>>()
                .join(" ")
        };
        format!("tweets · {who}")
    }

    /// Rebuild the calendar's events for the current view, layer and filter.
    fn rebuild(&mut self) {
        let view = self.cal.view();
        let mut events = self.catalysts.clone();
        if self.show_tweets
            && let Some(tw) = &self.tweets
        {
            events.extend(tweet_events(tw, &self.filter, view == View::Day));
        }
        self.cal.set_events(events);
        self.cal.set_status(self.status());
        self.built = (view, self.show_tweets, self.filter.clone());
    }

    /// Rebuild if a key changed the view, the layer or the filter.
    fn sync(&mut self) {
        if self.built != (self.cal.view(), self.show_tweets, self.filter.clone()) {
            self.rebuild();
        }
    }

    fn toggle_tweets(&mut self) {
        self.show_tweets = !self.show_tweets && self.ensure_tweets();
        self.sync();
    }

    fn apply_filter(&mut self, typed: &str) {
        self.filter = parse_filter(typed);
        if !self.filter.is_empty() {
            self.show_tweets = self.ensure_tweets();
        }
        self.sync();
    }

    /// Enter: month/week -> day view of the cursor day; day view -> the
    /// selected tweet's post, or the catalyst's page if it has one.
    fn enter(&mut self) -> Action {
        if self.cal.view() != View::Day {
            self.cal.set_view(View::Day);
            self.sync();
            return Action::None;
        }
        let Some(e) = self.cal.selected_event() else {
            return Action::None;
        };
        if let Some(url) = &e.link {
            return Action::OpenBrowser(url.clone());
        }
        if let Some(i) = catalyst_page::find(&self.pages, e.date, &e.label) {
            self.page = Some(catalyst_page::View::new(i));
        }
        Action::None
    }

    fn on_prompt_key(&mut self, key: KeyEvent) {
        let Some(input) = &mut self.prompt else {
            return;
        };
        match key.code {
            KeyCode::Enter => {
                let typed = input.value().to_string();
                self.prompt = None;
                self.apply_filter(&typed);
            }
            KeyCode::Esc => self.prompt = None,
            _ => {
                input.handle_event(&TermEvent::Key(key));
            }
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
        if let Some(input) = &self.prompt {
            let prefix = " ticker (space separated, empty clears) › ";
            frame.render_widget(
                Paragraph::new(Line::from(vec![
                    Span::styled(prefix, t.accent()),
                    Span::styled(input.value().to_string(), t.base()),
                ]))
                .style(t.base()),
                foot,
            );
            frame.set_cursor_position((
                foot.x + (text::width(prefix) + input.visual_cursor()) as u16,
                foot.y,
            ));
        } else {
            help::render_footer(frame, foot, FOOTER, self.flash.as_deref(), &t);
        }
        if self.help {
            let keys = [calendar::KEYS, EXTRA_KEYS].concat();
            help::render_overlay(frame, area, "events keys", &keys, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.prompt.is_some() {
            self.on_prompt_key(key);
            return Action::None;
        }
        self.flash = None;
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
            KeyCode::Enter => self.enter(),
            KeyCode::Char('q') | KeyCode::Esc => Action::Quit,
            KeyCode::Char('?') => {
                self.help = true;
                Action::None
            }
            KeyCode::Char('T') => {
                self.toggle_tweets();
                Action::None
            }
            KeyCode::Char('f') | KeyCode::Char('/') => {
                self.prompt = Some(Input::new(self.filter.join(" ")));
                Action::None
            }
            KeyCode::Char('F') => {
                self.apply_filter("");
                Action::None
            }
            _ => {
                self.cal.on_key(key);
                self.sync();
                Action::None
            }
        }
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }

    /// Space must stay a plain character while a ticker is being typed.
    fn leader_ok(&self) -> bool {
        self.prompt.is_none()
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

    // ---- tweet layer ----

    fn tw(d: u32, time: &str, handle: &str, tickers: &[(&str, Option<i32>)], text: &str) -> Tweet {
        Tweet {
            date: NaiveDate::from_ymd_opt(2026, 10, d).unwrap(),
            time: time.into(),
            handle: handle.into(),
            url: format!("https://x.com/{handle}/status/1"),
            text: text.into(),
            likes: 7,
            views: 1200,
            reply: false,
            tickers: tickers.iter().map(|(t, s)| (t.to_string(), *s)).collect(),
        }
    }

    fn fixture() -> Vec<Tweet> {
        vec![
            tw(
                9,
                "09:45",
                "alice",
                &[("MU", Some(1)), ("NVDA", None)],
                "MU looks great",
            ),
            tw(9, "10:30", "bob", &[("MU", Some(-1))], "short MU"),
            tw(9, "11:00", "carol", &[("AMD", Some(1))], "AMD is cheap"),
            tw(10, "12:00", "dave", &[("MU", Some(2))], "MU to the moon"),
        ]
    }

    fn with_tweets() -> Events {
        let mut s = open_with(&ctx(), Some("2026-10-09"), today(), Vec::new()).unwrap();
        s.loader = || Ok(fixture());
        s
    }

    fn code(s: &mut Events, c: KeyCode) -> Action {
        s.on_key(KeyEvent {
            code: c,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn type_str(s: &mut Events, text: &str) {
        for c in text.chars() {
            press(s, c);
        }
    }

    fn labels(s: &Events, d: u32) -> Vec<String> {
        s.cal
            .events_on(NaiveDate::from_ymd_opt(2026, 10, d).unwrap())
            .iter()
            .map(|e| e.label.clone())
            .collect()
    }

    #[test]
    fn layer_is_off_until_toggled_and_summarises_each_day() {
        let mut s = with_tweets();
        assert!(labels(&s, 9).is_empty());
        press(&mut s, 'T');
        assert!(s.show_tweets);
        assert_eq!(labels(&s, 9), ["3 tweets MU×2 AMD×1 NVDA×1"]);
        assert_eq!(labels(&s, 10), ["1 tweets MU×1"]);
        press(&mut s, 'T');
        assert!(labels(&s, 9).is_empty());
    }

    #[test]
    fn day_view_lists_each_tweet_in_time_order_with_stance_tags() {
        let mut s = with_tweets();
        press(&mut s, 'T');
        press(&mut s, 'd');
        let rows = labels(&s, 9);
        assert_eq!(rows.len(), 3);
        assert!(rows[0].starts_with("@alice MU+1 NVDA"), "{}", rows[0]);
        assert!(rows[1].starts_with("@bob MU-1"), "{}", rows[1]);
        assert!(rows[2].contains("AMD+1"));
    }

    #[test]
    fn ticker_filter_narrows_month_and_day_views() {
        let mut s = with_tweets();
        press(&mut s, 'f');
        assert!(s.prompt.is_some() && !s.leader_ok());
        type_str(&mut s, "$mu");
        code(&mut s, KeyCode::Enter);
        assert!(s.prompt.is_none() && s.leader_ok());
        assert_eq!(s.filter, ["MU"]);
        assert!(s.show_tweets, "filtering turns the layer on");
        assert_eq!(labels(&s, 9), ["2 tweets +0.0"]); // alice +1, bob -1
        press(&mut s, 'd');
        let rows = labels(&s, 9);
        assert_eq!(rows.len(), 2);
        assert!(rows.iter().all(|r| r.contains("MU")));
        // two tickers, comma or space separated
        press(&mut s, 'f');
        for _ in 0..2 {
            code(&mut s, KeyCode::Backspace);
        }
        type_str(&mut s, "AMD,NVDA");
        code(&mut s, KeyCode::Enter);
        assert_eq!(s.filter, ["AMD", "NVDA"]);
        assert_eq!(labels(&s, 9).len(), 2);
        // F clears
        press(&mut s, 'F');
        assert!(s.filter.is_empty());
        assert_eq!(labels(&s, 9).len(), 3);
    }

    #[test]
    fn prompt_escape_cancels_and_empty_enter_clears() {
        let mut s = with_tweets();
        press(&mut s, 'f');
        type_str(&mut s, "AMD");
        code(&mut s, KeyCode::Esc);
        assert!(s.prompt.is_none() && s.filter.is_empty() && !s.show_tweets);
        press(&mut s, 'f');
        type_str(&mut s, "AMD");
        code(&mut s, KeyCode::Enter);
        assert_eq!(s.filter, ["AMD"]);
        press(&mut s, 'f');
        for _ in 0..3 {
            code(&mut s, KeyCode::Backspace);
        }
        code(&mut s, KeyCode::Enter);
        assert!(s.filter.is_empty());
    }

    #[test]
    fn enter_on_a_tweet_opens_its_post() {
        let mut s = with_tweets();
        press(&mut s, 'T');
        press(&mut s, 'd');
        press(&mut s, 'j'); // @bob
        assert_eq!(
            code(&mut s, KeyCode::Enter),
            Action::OpenBrowser("https://x.com/bob/status/1".into())
        );
    }

    #[test]
    fn arguments_open_with_the_layer_and_filter() {
        let mut s = open_with(&ctx(), Some("day 2026-10-09 t:mu,amd"), today(), Vec::new())
            .unwrap_or_else(|_| unreachable!());
        // the real loader would call python; swap in the fixture and rebuild as `open` would after loading
        s.loader = || Ok(fixture());
        s.tweets = None;
        s.show_tweets = s.ensure_tweets();
        s.rebuild();
        assert_eq!(s.filter, ["MU", "AMD"]);
        assert_eq!(s.cal.view(), View::Day);
        assert_eq!(labels(&s, 9).len(), 3);
    }

    #[test]
    fn a_failing_loader_leaves_the_layer_off_with_a_message() {
        let mut s = with_tweets();
        s.loader = || Err("py/derive/tweet_calendar.py failed:\nboom".into());
        press(&mut s, 'T');
        assert!(!s.show_tweets);
        assert_eq!(
            s.flash.as_deref(),
            Some("tweets unavailable: py/derive/tweet_calendar.py failed:")
        );
    }

    #[test]
    fn filter_parsing() {
        assert_eq!(parse_filter(" $mu, NVDA  mu "), ["MU", "NVDA"]);
        assert!(parse_filter("  ,  ").is_empty());
    }

    fn render(s: &mut Events, w: u16, h: u16) -> String {
        use ratatui::Terminal;
        use ratatui::backend::TestBackend;
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        let b = term.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn renders_the_status_the_day_list_and_the_prompt() {
        let mut s = with_tweets();
        press(&mut s, 'T');
        press(&mut s, 'd');
        let screen = render(&mut s, 120, 24);
        assert!(screen.contains("tweets · all tickers"), "{screen}");
        assert!(screen.contains("@alice MU+1 NVDA"), "{screen}");
        assert!(
            screen.contains("tweets"),
            "footer lists the T key:\n{screen}"
        );
        press(&mut s, 'f');
        let screen = render(&mut s, 120, 24);
        assert!(
            screen.contains("ticker (space separated, empty clears) ›"),
            "{screen}"
        );
    }
}
