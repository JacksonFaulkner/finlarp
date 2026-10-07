// Search screen tests: a fake client (channels we hold both ends of) fed
// with fixture.json, a reply captured from `search.py --serve` for
// "t:MRVL guidance" (k=3, texts trimmed) plus a `get 181329 --context 1`.

use std::sync::mpsc::{self, Receiver, Sender};
use std::time::{Duration, Instant};

use ratatui::Terminal;
use ratatui::backend::TestBackend;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::style::Modifier;

use super::*;

const FIXTURE: &str = include_str!("fixture.json");
const INDEX_URL: &str = "https://www.sec.gov/Archives/edgar/data/1835632/000183563226000011/0001835632-26-000011-index.htm";

struct Harness {
    s: Search,
    req: Receiver<Request>,
    reply: Sender<Reply>,
}

fn fixture(part: &str, id: u64) -> Reply {
    let v: serde_json::Value = serde_json::from_str(FIXTURE).unwrap_or_default();
    let mut r: Reply = serde_json::from_value(v[part].clone()).unwrap_or_default();
    r.id = Some(id);
    r
}

fn harness() -> Harness {
    let (tx, req) = mpsc::channel();
    let (reply, rx) = mpsc::channel();
    let s = Search::new(
        "t:MRVL guidance".into(),
        Theme::default(),
        Client { tx, rx },
        History::in_memory(&[]),
    );
    Harness { s, req, reply }
}

/// Harness with the initial query answered.
fn loaded() -> Harness {
    let mut h = harness();
    let first = h.req.try_recv();
    assert!(matches!(first, Ok(Request::Query { id: 1, ref q, .. }) if q == "t:MRVL guidance"));
    let _ = h.reply.send(fixture("query", 1));
    h.s.tick();
    h
}

fn press(s: &mut Search, code: KeyCode, m: KeyModifiers) -> Action {
    s.on_key(KeyEvent::new(code, m))
}

fn draw(s: &mut Search, w: u16, h: u16) -> Terminal<TestBackend> {
    let mut t = match Terminal::new(TestBackend::new(w, h)) {
        Ok(t) => t,
        Err(e) => panic!("terminal: {e}"),
    };
    if let Err(e) = t.draw(|f| s.draw(f)) {
        panic!("draw: {e}");
    }
    t
}

fn screen_text(t: &Terminal<TestBackend>) -> String {
    let b = t.backend().buffer();
    (0..b.area.height)
        .map(|y| {
            (0..b.area.width)
                .map(|x| b[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn renders_results_facets_preview_and_source() {
    let mut h = loaded();
    let t = draw(&mut h.s, 160, 30);
    let text = screen_text(&t);
    assert!(text.contains("search › t:MRVL guidance"), "{text}");
    assert!(text.contains("MRVL   10K 2026-03-11 mda"), "{text}");
    assert!(text.contains("ERN"), "{text}");
    assert!(text.contains("TICKER") && text.contains("● MRVL"), "{text}");
    assert!(text.contains("3 of 22"), "{text}");
    // source bar shows the selected hit's filing
    assert!(text.contains("0001835632-26-000011"), "{text}");
    // a query term in the results is highlighted
    let b = t.backend().buffer();
    let hl = (0..b.area.height).any(|y| {
        (0..b.area.width)
            .any(|x| b[(x, y)].symbol() == "g" && b[(x, y)].modifier.contains(Modifier::UNDERLINED))
    });
    assert!(hl, "no highlighted term");
}

#[test]
fn narrow_layout_stacks_preview_and_drops_facets() {
    let mut h = loaded();
    let text = screen_text(&draw(&mut h.s, 80, 30));
    assert!(!text.contains("TICKER"));
    assert!(text.contains("preview"), "{text}");
}

#[test]
fn keys_emit_nvim_and_in_process_actions() {
    let mut h = loaded();
    let a = press(&mut h.s, KeyCode::Enter, KeyModifiers::NONE);
    assert_eq!(
        a,
        Action::Nvim(NvimAction::Chunk {
            id: "149731".into()
        })
    );
    let a = press(&mut h.s, KeyCode::Char('v'), KeyModifiers::ALT);
    let Action::Nvim(NvimAction::Docview { url, quote }) = a else {
        panic!("{a:?}")
    };
    assert_eq!(url, INDEX_URL);
    assert_eq!(
        quote.as_deref(),
        Some("On January 5, 2026, the OECD released a comprehensive package")
    );
    assert_eq!(
        press(&mut h.s, KeyCode::Char('o'), KeyModifiers::CONTROL),
        Action::OpenBrowser(INDEX_URL.into())
    );
    // y types into the input while it has focus, copies from the results
    press(&mut h.s, KeyCode::Char('y'), KeyModifiers::NONE);
    assert_eq!(h.s.input.value(), "t:MRVL guidancey");
    press(&mut h.s, KeyCode::Backspace, KeyModifiers::NONE);
    press(&mut h.s, KeyCode::Tab, KeyModifiers::NONE);
    press(&mut h.s, KeyCode::Tab, KeyModifiers::NONE);
    assert_eq!(h.s.focus, Pane::Results);
    assert_eq!(
        press(&mut h.s, KeyCode::Char('y'), KeyModifiers::NONE),
        Action::Copy(INDEX_URL.into())
    );
    press(&mut h.s, KeyCode::Char('j'), KeyModifiers::CONTROL);
    press(&mut h.s, KeyCode::Char('j'), KeyModifiers::NONE);
    assert_eq!(h.s.selected().map(|x| x.id), Some(181329));
    assert_eq!(
        press(&mut h.s, KeyCode::Esc, KeyModifiers::NONE),
        Action::Quit
    );
}

#[test]
fn debounces_and_drops_stale_replies() {
    let mut h = loaded();
    h.s.debounce = Duration::from_secs(3600);
    press(&mut h.s, KeyCode::Char('s'), KeyModifiers::NONE);
    h.s.tick();
    assert!(
        h.req.try_recv().is_err(),
        "sent before the debounce expired"
    );
    h.s.debounce = Duration::ZERO;
    h.s.tick();
    let Ok(Request::Query { id, q, .. }) = h.req.try_recv() else {
        panic!("no query sent")
    };
    assert_eq!(q, "t:MRVL guidances");
    // a late reply to the first query must not replace anything
    let mut stale = fixture("query", 1);
    stale.results.truncate(1);
    let _ = h.reply.send(stale);
    h.s.tick();
    assert!(h.s.loading);
    let mut fresh = fixture("query", id);
    fresh.results.truncate(2);
    let _ = h.reply.send(fresh);
    h.s.tick();
    assert!(!h.s.loading);
    assert_eq!(h.s.results.len(), 2);
    // an unchanged query is not re-sent
    h.s.edited();
    h.s.tick();
    assert!(!matches!(h.req.try_recv(), Ok(Request::Query { .. })));
}

#[test]
fn facet_toggle_rewrites_query_and_sends() {
    let mut h = loaded();
    press(&mut h.s, KeyCode::Tab, KeyModifiers::NONE);
    assert_eq!(h.s.focus, Pane::Facets);
    // walk to the first "type" item (below the ticker items)
    let target =
        h.s.facets
            .iter()
            .position(|f| matches!(f, FacetRow::Item { dim: Dim::Type, .. }));
    while h.s.facet_state.selected() != target {
        press(&mut h.s, KeyCode::Char('j'), KeyModifiers::NONE);
    }
    press(&mut h.s, KeyCode::Char(' '), KeyModifiers::NONE);
    assert_eq!(h.s.input.value(), "type:filing t:MRVL guidance");
    h.s.debounce = Duration::from_millis(150);
    h.s.tick();
    assert!(
        matches!(h.req.try_recv(), Ok(Request::Query { q, .. }) if q == "type:filing t:MRVL guidance")
    );
    // toggling the active ticker facet removes it
    h.s.facet_state.select(Some(1));
    press(&mut h.s, KeyCode::Enter, KeyModifiers::NONE);
    assert_eq!(h.s.input.value(), "type:filing guidance");
}

#[test]
fn preview_fetches_context_and_jumps_to_match() {
    let mut h = loaded();
    h.s.move_result(2);
    h.s.selected_at = Instant::now().checked_sub(Duration::from_secs(1));
    h.s.tick();
    let Ok(Request::Get { id, get, context }) = h.req.try_recv() else {
        panic!("no get sent")
    };
    assert_eq!((get, context), (181329, 1));
    let _ = h.reply.send(fixture("get", id));
    h.s.tick();
    let text = screen_text(&draw(&mut h.s, 160, 30));
    assert!(text.contains("◀ match"), "{text}");
    assert!(text.contains("3 chunks"), "{text}");
    assert!(
        h.s.preview_scroll > 0,
        "preview should scroll to the matched chunk"
    );
    // cached: re-selecting does not re-fetch
    h.s.selection_changed();
    h.s.selected_at = Instant::now().checked_sub(Duration::from_secs(1));
    h.s.tick();
    assert!(h.req.try_recv().is_err());
}

#[test]
fn history_on_up_down_in_input() {
    let (tx, _req) = mpsc::channel();
    let (_reply, rx) = mpsc::channel();
    let mut s = Search::new(
        "draft".into(),
        Theme::default(),
        Client { tx, rx },
        History::in_memory(&["t:NVDA hbm"]),
    );
    press(&mut s, KeyCode::Up, KeyModifiers::NONE);
    assert_eq!(s.input.value(), "t:NVDA hbm");
    press(&mut s, KeyCode::Down, KeyModifiers::NONE);
    assert_eq!(s.input.value(), "draft");
    // ctrl-w / ctrl-u line editing via tui-input
    press(&mut s, KeyCode::Char('w'), KeyModifiers::CONTROL);
    assert_eq!(s.input.value(), "");
}

#[test]
fn server_failure_shows_error() {
    let mut h = harness();
    let _ = h.reply.send(Reply {
        error: Some("search.py exited".into()),
        ..Reply::default()
    });
    h.s.tick();
    let text = screen_text(&draw(&mut h.s, 120, 20));
    assert!(text.contains("search.py exited"), "{text}");
}
