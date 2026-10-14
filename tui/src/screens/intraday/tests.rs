use super::data::Bar1;
use super::stream::Event;
use super::*;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use std::sync::mpsc::Sender;

// 2026-10-14 09:30 EDT
const OPEN: i64 = 1_791_984_600;

fn bars(base: f64, n: i64) -> Vec<Bar1> {
    (0..n)
        .map(|i| {
            let c = base + (i as f64 * 0.7).sin() * 2.0 + i as f64 * 0.05;
            Bar1 {
                t: OPEN + i * 60,
                o: c - 0.3,
                h: c + 0.8,
                l: c - 0.9,
                c,
                v: 1000 + (i as u64 * 37) % 900,
            }
        })
        .collect()
}

fn screen() -> (Intraday, Sender<Event>) {
    let (stream, tx) = Stream::detached();
    let syms = ["MKSI", "WDC", "WULF", "APLD"].map(String::from).to_vec();
    (Intraday::new(Theme::default(), syms, stream), tx)
}

fn seed(tx: &Sender<Event>, sym: &str, base: f64, n: i64) {
    tx.send(Event::Seed {
        sym: sym.into(),
        prev_close: Some(base - 1.0),
        reg: Some((OPEN, OPEN + 390 * 60)),
        bars: bars(base, n),
    })
    .unwrap();
}

fn loaded() -> (Intraday, Sender<Event>) {
    let (mut s, tx) = screen();
    for (sym, base) in [
        ("MKSI", 240.0),
        ("WDC", 370.0),
        ("WULF", 12.0),
        ("APLD", 22.0),
    ] {
        seed(&tx, sym, base, 90);
    }
    s.tick();
    (s, tx)
}

fn render(s: &mut Intraday, w: u16, h: u16) -> String {
    let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
    t.draw(|f| s.draw(f)).unwrap();
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

fn press(s: &mut Intraday, c: KeyCode) -> Action {
    s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
}

#[test]
fn parses_and_pads_symbols() {
    assert_eq!(
        parse_symbols(Some("mksi, wdc")),
        ["MKSI", "WDC", "SPY", "QQQ"]
    );
    assert_eq!(
        parse_symbols(Some("SPY,SPY,A B C D")),
        ["SPY", "A", "B", "C"]
    );
    assert_eq!(parse_symbols(None), ["SPY", "QQQ", "NVDA", "AAPL"]);
}

#[test]
fn opening_subscribes_to_all_four_symbols() {
    let (s, _tx) = screen();
    assert_eq!(
        s.stream.sent,
        [r#"{"cmd":"set","symbols":["MKSI","WDC","WULF","APLD"]}"#]
    );
}

#[test]
fn renders_a_two_by_two_grid_with_all_tickers() {
    let (mut s, _tx) = loaded();
    let out = render(&mut s, 140, 40);
    for sym in ["MKSI", "WDC", "WULF", "APLD"] {
        assert!(out.contains(sym), "{sym} missing:\n{out}");
    }
    assert!(out.contains("5m"));
    assert!(out.contains("09:"), "ET time labels");
    assert!(
        out.chars()
            .any(|c| ('\u{1FB00}'..='\u{1FB3B}').contains(&c) || "▌▐█".contains(c))
    );
    // two tiles per row: the first row's border line holds two titles
    let top = out.lines().nth(1).unwrap();
    assert!(top.contains("MKSI") && top.contains("WDC"), "{top}");
}

#[test]
fn tiles_without_data_say_loading() {
    let (mut s, _tx) = screen();
    assert!(render(&mut s, 100, 30).contains("loading"));
}

#[test]
fn a_feed_error_is_shown_in_its_tile() {
    let (mut s, tx) = screen();
    tx.send(Event::Error {
        sym: "WDC".into(),
        msg: "seed failed: 404".into(),
    })
    .unwrap();
    s.tick();
    assert!(render(&mut s, 100, 30).contains("seed failed: 404"));
}

#[test]
fn live_bars_update_the_last_row() {
    let (mut s, tx) = loaded();
    let last = bars(370.0, 90)[89];
    tx.send(Event::Bar {
        sym: "WDC".into(),
        bar: Bar1 {
            c: last.c + 5.0,
            h: last.h + 5.0,
            ..last
        },
    })
    .unwrap();
    s.tick();
    let wdc = &s.tiles[1];
    let agg = s.bars(wdc);
    assert_eq!(agg.last().unwrap().close, last.c + 5.0);
    assert_eq!(agg.len(), 18, "90 one-minute bars at 5m");
    // a bar for an untracked symbol is ignored
    tx.send(Event::Bar {
        sym: "ZZZZ".into(),
        bar: last,
    })
    .unwrap();
    s.tick();
}

#[test]
fn status_events_drive_the_header() {
    let (mut s, tx) = screen();
    assert!(render(&mut s, 100, 30).contains("offline"));
    tx.send(Event::Status {
        live: true,
        msg: "streaming 4 symbols".into(),
    })
    .unwrap();
    s.tick();
    let out = render(&mut s, 100, 30);
    assert!(
        out.contains("● live") && out.contains("streaming 4 symbols"),
        "{out}"
    );
}

#[test]
fn focus_interval_extended_and_zoom_keys() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Tab);
    assert_eq!(s.focus, 1);
    press(&mut s, KeyCode::Char('4'));
    assert_eq!(s.focus, 3);
    press(&mut s, KeyCode::BackTab);
    assert_eq!(s.focus, 2);
    assert_eq!(STEPS[s.step], 5);
    press(&mut s, KeyCode::Char('i'));
    assert_eq!(STEPS[s.step], 15);
    press(&mut s, KeyCode::Char('i'));
    assert_eq!(STEPS[s.step], 1);
    assert!(!s.ext);
    press(&mut s, KeyCode::Char('e'));
    assert!(s.ext);
    press(&mut s, KeyCode::Enter);
    assert!(s.zoom);
    let out = render(&mut s, 120, 36);
    assert!(
        out.contains("WULF") && !out.contains("MKSI"),
        "zoom shows only the focused tile"
    );
    press(&mut s, KeyCode::Enter);
    assert!(s.zoom, "enter never toggles back out");
    // esc leaves zoom first, then quits
    assert_eq!(press(&mut s, KeyCode::Esc), Action::None);
    assert!(!s.zoom);
    assert_eq!(press(&mut s, KeyCode::Esc), Action::Quit);
    assert_eq!(press(&mut s, KeyCode::Char('q')), Action::Quit);
}

#[test]
fn hjkl_move_between_tiles_spatially_and_stop_at_edges() {
    let (mut s, _tx) = loaded();
    assert_eq!(s.focus, 0); // top-left
    press(&mut s, KeyCode::Char('h'));
    press(&mut s, KeyCode::Char('k'));
    assert_eq!(s.focus, 0, "no wrap past the top-left");
    press(&mut s, KeyCode::Char('l'));
    assert_eq!(s.focus, 1); // top-right
    press(&mut s, KeyCode::Char('l'));
    assert_eq!(s.focus, 1);
    press(&mut s, KeyCode::Char('j'));
    assert_eq!(s.focus, 3); // bottom-right
    press(&mut s, KeyCode::Char('h'));
    assert_eq!(s.focus, 2); // bottom-left
    press(&mut s, KeyCode::Char('k'));
    assert_eq!(s.focus, 0);
    press(&mut s, KeyCode::Char('j'));
    assert_eq!(s.focus, 2);
    // arrows: left/right switch tiles, up/down move the bar cursor
    press(&mut s, KeyCode::Right);
    assert_eq!(s.focus, 3);
    render(&mut s, 100, 24);
    press(&mut s, KeyCode::Up);
    assert!(s.tiles[3].cursor.is_some());
    assert_eq!(s.focus, 3);
}

#[test]
fn cursor_scrolls_through_history_and_g_returns_to_live() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Char('i')); // 15m: 90 bars -> 6 bars; use 1m for scrolling
    press(&mut s, KeyCode::Char('i'));
    assert_eq!(STEPS[s.step], 1);
    render(&mut s, 100, 24); // learn the window size
    let rows = s.tiles[0].rows;
    assert!(rows > 0 && rows < 90);
    for _ in 0..rows + 5 {
        press(&mut s, KeyCode::Char('K'));
    }
    let t = &s.tiles[0];
    assert_eq!(t.cursor, Some(90 - 1 - (rows + 5)));
    assert!(t.end_off > 0, "window scrolled to keep the cursor visible");
    let out = render(&mut s, 100, 24);
    assert!(out.contains('▸'), "cursor marker is on screen:\n{out}");
    press(&mut s, KeyCode::Char('G'));
    assert_eq!((s.tiles[0].cursor, s.tiles[0].end_off), (None, 0));
    // j past the newest bar re-follows live
    press(&mut s, KeyCode::Char('K'));
    press(&mut s, KeyCode::Char('J'));
    assert_eq!(s.tiles[0].cursor, None);
}

#[test]
fn setting_a_ticker_clears_the_tile_and_resubscribes() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Char('2')); // focus WDC
    press(&mut s, KeyCode::Char('s'));
    assert!(!s.leader_ok(), "space is a plain character while typing");
    for c in "nvda".chars() {
        press(&mut s, KeyCode::Char(c));
    }
    assert!(render(&mut s, 100, 30).contains("ticker for tile 2: nvda"));
    press(&mut s, KeyCode::Backspace);
    press(&mut s, KeyCode::Char('a'));
    press(&mut s, KeyCode::Enter);
    assert!(s.leader_ok());
    assert_eq!(s.tiles[1].sym, "NVDA");
    assert!(s.tiles[1].series.is_empty());
    assert_eq!(
        s.stream.sent.last().unwrap(),
        r#"{"cmd":"set","symbols":["MKSI","NVDA","WULF","APLD"]}"#
    );
    // esc cancels without changing anything
    press(&mut s, KeyCode::Char('s'));
    press(&mut s, KeyCode::Char('x'));
    press(&mut s, KeyCode::Esc);
    assert_eq!(s.tiles[1].sym, "NVDA");
    assert_eq!(s.stream.sent.len(), 2);
}

#[test]
fn resync_key_sends_a_command() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Char('r'));
    assert_eq!(s.stream.sent.last().unwrap(), r#"{"cmd":"resync"}"#);
}

#[test]
fn help_overlay_opens_and_any_key_closes_it() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Char('?'));
    assert!(render(&mut s, 100, 30).contains("full screen tile"));
    press(&mut s, KeyCode::Char('x'));
    assert!(!s.help);
}

#[test]
fn escape_returns_to_the_grid_with_focus_and_state_kept() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Char('l'));
    press(&mut s, KeyCode::Char('i')); // 15m
    press(&mut s, KeyCode::Enter);
    assert!(
        render(&mut s, 120, 36).matches('┌').count() == 1,
        "one full-screen tile"
    );
    assert_eq!(press(&mut s, KeyCode::Esc), Action::None);
    let grid = render(&mut s, 120, 36);
    assert_eq!(grid.matches('┌').count(), 4, "back to four tiles");
    assert_eq!((s.focus, STEPS[s.step]), (1, 15));
}

#[test]
fn tiny_terminals_do_not_panic() {
    let (mut s, _tx) = loaded();
    render(&mut s, 12, 4);
    render(&mut s, 3, 2);
    render(&mut s, 60, 12);
    press(&mut s, KeyCode::Char('z'));
    render(&mut s, 20, 6);
}

/// Real feed, real network: `cargo test live_smoke -- --ignored --nocapture`.
#[test]
#[ignore]
fn live_smoke() {
    let mut s = Intraday::new(
        Theme::default(),
        ["MKSI", "WDC", "WULF", "APLD"].map(String::from).to_vec(),
        Stream::spawn(),
    );
    for _ in 0..80 {
        std::thread::sleep(std::time::Duration::from_millis(100));
        s.tick();
    }
    println!("{}", render(&mut s, 160, 48));
}
