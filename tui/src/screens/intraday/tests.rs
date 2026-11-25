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
    press(&mut s, KeyCode::Tab);
    press(&mut s, KeyCode::Tab);
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
    s.apply_pending_cursor(); // keys queue cursor steps; a draw applies them
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
    s.apply_pending_cursor();
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
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, None);
}

#[test]
fn setting_a_ticker_clears_the_tile_and_resubscribes() {
    let (mut s, _tx) = loaded();
    press(&mut s, KeyCode::Tab); // focus WDC
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
fn help_menu_lists_the_keys() {
    let (s, _tx) = loaded();
    assert!(
        s.help()
            .keys
            .iter()
            .any(|k| k.desc.contains("full screen tile"))
    );
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

/// Forces a graphics protocol on the screen, the way `open` would after a terminal query.
fn with_graphics(s: &mut Intraday) {
    let mut picker =
        ratatui_image::picker::Picker::from_fontsize(ratatui_image::FontSize::new(10, 20));
    picker.set_protocol_type(ratatui_image::picker::ProtocolType::Kitty);
    s.picker = Some(picker);
    s.pictures = true;
}

#[test]
fn tiles_draw_as_pictures_when_the_terminal_has_graphics() {
    let (mut s, _tx) = loaded();
    with_graphics(&mut s);
    let out = render(&mut s, 160, 45);
    assert!(out.contains("MKSI") && out.contains("APLD"));
    assert!(
        s.tiles.iter().all(|t| t.pic.is_some()),
        "every tile sent a picture"
    );
    // a tick with no new bars keeps the last picture (same content, same key)
    let before: Vec<u64> = s
        .tiles
        .iter()
        .map(|t| t.pic.as_ref().unwrap().key)
        .collect();
    render(&mut s, 160, 45);
    let after: Vec<u64> = s
        .tiles
        .iter()
        .map(|t| t.pic.as_ref().unwrap().key)
        .collect();
    assert_eq!(before, after);
}

#[test]
fn gg_goes_to_the_first_bar_and_g_alone_does_nothing() {
    let (mut s, _tx) = loaded();
    render(&mut s, 120, 40);
    press(&mut s, KeyCode::Char('g'));
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, None, "one g waits for the second");
    assert!(
        !s.pictures || s.picker.is_some(),
        "g no longer toggles pictures"
    );
    press(&mut s, KeyCode::Char('g'));
    assert_eq!(s.tiles[0].cursor, Some(0), "gg: the first bar");
    let out = render(&mut s, 120, 40);
    assert!(out.contains("MKSI"), "{out}");
    // G is back to the latest bar, following live
    press(&mut s, KeyCode::Char('G'));
    assert_eq!(s.tiles[0].cursor, None);
    // g then something else is not gg
    press(&mut s, KeyCode::Char('g'));
    press(&mut s, KeyCode::Char('e'));
    press(&mut s, KeyCode::Char('g'));
    assert_eq!(s.tiles[0].cursor, None);
}

/// Cost of one cursor move with pictures on: `cargo test --release move_cost -- --ignored --nocapture`.
#[test]
#[ignore]
fn move_cost() {
    let (mut s, _tx) = loaded();
    with_graphics(&mut s);
    // Ghostty-ish cells at 200x60: tiles near 1000x560 px
    render(&mut s, 200, 60);
    let n = 30;
    let t0 = std::time::Instant::now();
    let mut bytes = 0usize;
    for _ in 0..n {
        press(&mut s, KeyCode::Char('K'));
        let mut t = Terminal::new(TestBackend::new(200, 60)).unwrap();
        t.draw(|f| s.draw(f)).unwrap();
        bytes += t
            .backend()
            .buffer()
            .content
            .iter()
            .map(|c| c.symbol().len())
            .sum::<usize>();
    }
    println!(
        "per move: {:?}, {} KB written",
        t0.elapsed() / n,
        bytes / n as usize / 1024
    );
}

#[test]
fn h_and_l_move_the_cursor_along_the_picture() {
    let (mut s, _tx) = loaded();
    render(&mut s, 160, 45);
    press(&mut s, KeyCode::Char('H'));
    press(&mut s, KeyCode::Char('H'));
    s.apply_pending_cursor();
    let len = s.bars(&s.tiles[0]).len();
    assert_eq!(s.tiles[0].cursor, Some(len - 3));
    press(&mut s, KeyCode::Char('L'));
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, Some(len - 2));
    // back at the newest bar the cursor follows latest again
    press(&mut s, KeyCode::Char('L'));
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, None);
}

#[test]
fn cursor_moves_never_resend_the_picture() {
    let (mut s, _tx) = loaded();
    with_graphics(&mut s);
    render(&mut s, 160, 45);
    let sent = s.tiles[0].pic.as_ref().unwrap().sent;
    for _ in 0..5 {
        press(&mut s, KeyCode::Char('H'));
        let out = render(&mut s, 160, 45);
        assert!(out.contains('▲'), "cursor marker under the picture");
    }
    assert_eq!(s.tiles[0].pic.as_ref().unwrap().sent, sent);
}

/// Deterministic 1-minute random walk over one regular session (390 bars).
fn walk(base: f64, seed: u64) -> Vec<Bar1> {
    let mut x = seed;
    let mut rnd = move || {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        (x % 1_000_000) as f64 / 1_000_000.0
    };
    let mut c = base;
    (0..390)
        .map(|i| {
            let o = c;
            c = (c + (rnd() - 0.5) * 0.6).max(1.0);
            Bar1 {
                t: OPEN + i * 60,
                o,
                h: o.max(c) + rnd() * 0.3,
                l: o.min(c) - rnd() * 0.3,
                c,
                v: 500 + (rnd() * 4000.0) as u64,
            }
        })
        .collect()
}

/// A `Vec<u8>` the test keeps a handle to, so it can count what the terminal was sent.
struct SharedVec(std::rc::Rc<std::cell::RefCell<Vec<u8>>>);

impl std::io::Write for SharedVec {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        self.0.borrow_mut().extend_from_slice(buf);
        Ok(buf.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

/// Combo benchmark, no terminal needed: `cargo test --release bench_combo -- --ignored --nocapture`.
/// Four tiles, pictures on, a 200x60 terminal whose output bytes are counted per draw.
#[test]
#[ignore]
fn bench_combo() {
    let (mut s, tx) = screen();
    for (i, (sym, base)) in [
        ("MKSI", 240.0),
        ("WDC", 370.0),
        ("WULF", 12.0),
        ("APLD", 22.0),
    ]
    .into_iter()
    .enumerate()
    {
        tx.send(Event::Seed {
            sym: sym.into(),
            prev_close: Some(base - 1.0),
            reg: Some((OPEN, OPEN + 390 * 60)),
            bars: walk(base, 7 + i as u64),
        })
        .unwrap();
    }
    s.tick();
    let mut picker =
        ratatui_image::picker::Picker::from_fontsize(ratatui_image::FontSize::new(8, 16));
    picker.set_protocol_type(ratatui_image::picker::ProtocolType::Kitty);
    s.picker = Some(picker);
    s.pictures = true;
    s.step = 0; // 1-minute bars: 390 of them, so the sweep crosses window edges

    // Output goes to a Vec the bench can read (CrosstermBackend's writer accessor is unstable).
    let sink = std::rc::Rc::new(std::cell::RefCell::new(Vec::<u8>::new()));
    let mut term = Terminal::with_options(
        ratatui::backend::CrosstermBackend::new(SharedVec(sink.clone())),
        ratatui::TerminalOptions {
            viewport: ratatui::Viewport::Fixed(ratatui::layout::Rect::new(0, 0, 200, 60)),
        },
    )
    .unwrap();
    let written = |_: &Terminal<ratatui::backend::CrosstermBackend<SharedVec>>| sink.borrow().len();
    term.draw(|f| s.draw(f)).unwrap(); // first frame: sends the four pictures, not measured

    // Idle: 200 polls with no input or feed events.
    let mut idle = 0;
    for _ in 0..200 {
        s.tick();
        if s.needs_redraw() {
            idle += 1;
        }
    }

    // Sweep: H across the window edges, one key and one draw at a time.
    let (mut times, mut sweep_bytes, mut big) = (Vec::new(), 0usize, 0usize);
    for _ in 0..400 {
        let before = written(&term);
        let t0 = std::time::Instant::now();
        press(&mut s, KeyCode::Char('H'));
        term.draw(|f| s.draw(f)).unwrap();
        times.push(t0.elapsed().as_micros());
        let d = written(&term) - before;
        sweep_bytes += d;
        big += usize::from(d > 10_000);
    }
    times.sort_unstable();
    let pct = |p: f64| times[((times.len() as f64 * p) as usize).min(times.len() - 1)];

    // Hold: L back to the newest bar.
    let before = written(&term);
    for _ in 0..400 {
        press(&mut s, KeyCode::Char('L'));
        term.draw(|f| s.draw(f)).unwrap();
    }
    let hold_bytes = written(&term) - before;

    println!(
        "RESULT idle_redraws_per_200_polls={idle} sweep_median_us={} sweep_p95_us={} sweep_total_bytes={sweep_bytes} sweep_big_sends(>10KB)={big} hold_total_bytes={hold_bytes}",
        pct(0.5),
        pct(0.95),
    );
}

#[test]
fn visual_selects_bars_and_i_zooms_onto_them() {
    let (mut s, _tx) = loaded();
    render(&mut s, 120, 40);
    let len = s.bars(&s.tiles[0]).len();
    press(&mut s, KeyCode::Char('V'));
    assert_eq!(
        s.tiles[0].anchor,
        Some(len - 1),
        "V anchors on the cursor (the latest bar)"
    );
    for _ in 0..5 {
        press(&mut s, KeyCode::Char('H'));
    }
    let out = render(&mut s, 120, 40);
    assert!(
        out.contains("-- VISUAL --") && out.contains("6 bars"),
        "{out}"
    );
    let step = s.step;
    press(&mut s, KeyCode::Char('i'));
    assert_eq!(
        s.step, step,
        "in visual mode i zooms, it does not change the interval"
    );
    assert_eq!(s.tiles[0].span, Some((len - 6, len)));
    assert_eq!(s.tiles[0].anchor, None, "zooming leaves visual mode");
    let out = render(&mut s, 120, 40);
    assert!(out.contains("zoom "), "{out}");
    // the cursor can't leave the zoomed bars
    for _ in 0..20 {
        press(&mut s, KeyCode::Char('H'));
    }
    render(&mut s, 120, 40);
    assert_eq!(s.tiles[0].cursor, Some(len - 6));
    // esc zooms back out, then i is the interval again
    press(&mut s, KeyCode::Esc);
    assert_eq!(s.tiles[0].span, None);
    press(&mut s, KeyCode::Char('i'));
    assert_ne!(s.step, step);
}

#[test]
fn changing_the_interval_drops_a_selection() {
    let (mut s, _tx) = loaded();
    render(&mut s, 120, 40);
    press(&mut s, KeyCode::Char('V'));
    press(&mut s, KeyCode::Char('e'));
    assert_eq!(s.tiles[0].anchor, None);
}

/// Where the time goes when `i` changes the interval with pictures on, stage by stage:
/// `cargo test --release interval_cost -- --ignored --nocapture`.
#[test]
#[ignore]
fn interval_cost() {
    use ratatui::widgets::StatefulWidget;
    use ratatui_image::protocol::kitty::StatefulKitty;
    use ratatui_image::protocol::{StatefulProtocol, StatefulProtocolType};
    use ratatui_image::{FontSize, Resize, StatefulImage};
    use std::time::{Duration, Instant};

    // 390 one-minute bars per tile: a full regular session
    let (mut s, tx) = screen();
    for (sym, base) in [
        ("MKSI", 240.0),
        ("WDC", 370.0),
        ("WULF", 12.0),
        ("APLD", 22.0),
    ] {
        seed(&tx, sym, base, 390);
    }
    s.tick();
    let (cols, rows) = (200u16, 62u16);
    for (font, label) in [
        ((10u16, 20u16), "1x cells 10x20"),
        ((20, 40), "retina cells 20x40"),
    ] {
        for zoomed in [false, true] {
            // tile chart area in cells, as draw lays it out
            let (cw, ch) = if zoomed {
                (cols - 2, rows - 5)
            } else {
                (cols / 2 - 2, (rows - 1) / 2 - 4)
            };
            let n_tiles = if zoomed { 1 } else { 4 };
            let px = (
                u32::from(cw) * u32::from(font.0),
                u32::from(ch) * u32::from(font.1),
            );
            println!(
                "\n== {label}, {} ({} tile{}, {}x{} px each)",
                if zoomed { "full screen" } else { "2x2 grid" },
                n_tiles,
                if n_tiles == 1 { "" } else { "s" },
                px.0,
                px.1
            );
            for (mode, compress, shm) in [
                ("base64 raw", false, false),
                ("zlib+base64", true, false),
                ("shared memory", false, true),
            ] {
                let (mut agg, mut raster, mut clone, mut encode) = (
                    Duration::ZERO,
                    Duration::ZERO,
                    Duration::ZERO,
                    Duration::ZERO,
                );
                let mut bytes = 0usize;
                s.step = (s.step + 1) % STEPS.len(); // what `i` does: a new interval, every cache cold
                for idx in 0..n_tiles {
                    let t0 = Instant::now();
                    let bars = s.bars(&s.tiles[idx]);
                    agg += t0.elapsed();
                    let pal = Palette::from_theme(&s.theme);
                    let pic = picture::Pic {
                        bars: &bars,
                        vwap: s.tiles[idx].series.vwap(),
                        prev_close: s.tiles[idx].series.prev_close,
                        sel: None,
                        range: None,
                    };
                    let mut img = image::RgbaImage::new(px.0, px.1);
                    let t0 = Instant::now();
                    picture::render_into(&mut img, &pic, &pal);
                    raster += t0.elapsed();
                    let t0 = Instant::now();
                    let dynimg = image::DynamicImage::ImageRgba8(img.clone());
                    clone += t0.elapsed();
                    let mut proto = StatefulProtocol::new(
                        dynimg,
                        FontSize::new(font.0, font.1),
                        None,
                        StatefulProtocolType::Kitty(StatefulKitty::new(
                            tile_image_id(idx, 0),
                            false,
                            compress,
                            shm,
                        )),
                    );
                    let area = Rect::new(0, 0, cw, ch);
                    let mut buf = ratatui::buffer::Buffer::empty(area);
                    let t0 = Instant::now();
                    StatefulImage::default()
                        .resize(Resize::Fit(None))
                        .render(area, &mut buf, &mut proto);
                    encode += t0.elapsed();
                    bytes += buf.content.iter().map(|c| c.symbol().len()).sum::<usize>();
                }
                let total = agg + raster + clone + encode;
                println!(
                    "  {mode:<14} total {:>7.1?}  | aggregate {:>7.1?}  raster {:>7.1?}  copy {:>7.1?}  encode {:>7.1?}  | {:>6} KB to the terminal",
                    total,
                    agg,
                    raster,
                    clone,
                    encode,
                    bytes / 1024
                );
            }
        }
    }
    // The real draw path end to end (test picker: no compression, no shm caps => raw base64)
    with_graphics(&mut s);
    render(&mut s, cols, rows);
    let t0 = Instant::now();
    let mut t = Terminal::new(TestBackend::new(cols, rows)).unwrap();
    press(&mut s, KeyCode::Char('i'));
    t.draw(|f| s.draw(f)).unwrap();
    println!(
        "\nfull Intraday::draw after `i` (2x2, 10x20 cells, raw base64): {:?}",
        t0.elapsed()
    );
}

#[test]
fn the_visual_band_follows_the_cursor_without_waiting_for_the_live_refresh() {
    let (mut s, _tx) = loaded();
    with_graphics(&mut s);
    render(&mut s, 160, 45);
    press(&mut s, KeyCode::Char('V'));
    render(&mut s, 160, 45);
    for _ in 0..3 {
        let before = s.tiles[0].pic.as_ref().unwrap().key;
        press(&mut s, KeyCode::Char('H'));
        render(&mut s, 160, 45);
        let slot = s.tiles[0].pic.as_ref().unwrap();
        assert_ne!(
            slot.key, before,
            "the picture with the wider band went out this frame"
        );
        assert!(!s.deferred, "nothing left waiting for LIVE_REFRESH");
    }
}

#[test]
fn a_tile_alternates_between_its_two_image_ids() {
    // the old picture keeps its id (and stays on screen) while the new one arrives
    let ids: Vec<u32> = (0..4)
        .flat_map(|i| [tile_image_id(i, 0), tile_image_id(i, 1)])
        .collect();
    let mut unique = ids.clone();
    unique.sort();
    unique.dedup();
    assert_eq!(
        unique.len(),
        ids.len(),
        "no two tiles or generations share an id"
    );
    let (mut s, _tx) = loaded();
    with_graphics(&mut s);
    render(&mut s, 160, 45);
    let first = s.tiles[0].which;
    press(&mut s, KeyCode::Char('i'));
    render(&mut s, 160, 45);
    assert_ne!(s.tiles[0].which, first, "a resend switches to the other id");
}

#[test]
fn counts_repeat_motions_like_vim() {
    let (mut s, _tx) = loaded();
    s.step = STEPS.iter().position(|&m| m == 1).unwrap(); // 1m: all 90 bars
    render(&mut s, 120, 40);
    let len = s.bars(&s.tiles[0]).len();
    for c in "50H".chars() {
        press(&mut s, KeyCode::Char(c));
    }
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, Some(len - 51), "50H: fifty candles left");
    for c in "12L".chars() {
        press(&mut s, KeyCode::Char(c));
    }
    s.apply_pending_cursor();
    assert_eq!(s.tiles[0].cursor, Some(len - 39));
    // the count shows while it's typed, and esc drops it
    press(&mut s, KeyCode::Char('7'));
    assert!(
        render(&mut s, 120, 40)
            .lines()
            .next()
            .unwrap()
            .contains("7")
    );
    press(&mut s, KeyCode::Esc);
    assert_eq!(s.count, None);
    assert!(!s.zoom || s.zoom, "esc only cleared the count");
    // 10G and 10gg: bar ten
    for c in "10G".chars() {
        press(&mut s, KeyCode::Char(c));
    }
    assert_eq!(s.tiles[0].cursor, Some(9));
    s.follow_latest();
    for c in "10gg".chars() {
        press(&mut s, KeyCode::Char(c));
    }
    assert_eq!(s.tiles[0].cursor, Some(9));
    // a leading 0 is not a count; digits no longer focus tiles
    press(&mut s, KeyCode::Char('3'));
    press(&mut s, KeyCode::Tab);
    assert_eq!(s.focus, 1, "the count is used up by the next key");
    assert_eq!(s.count, None);
}

#[test]
fn braces_jump_between_stops_and_tag_them() {
    let (mut s, _tx) = loaded();
    s.step = STEPS.iter().position(|&m| m == 1).unwrap();
    render(&mut s, 120, 40);
    let bars = s.bars(&s.tiles[0]);
    let all: Vec<usize> = stops::stops(&bars).iter().map(|x| x.idx).collect();
    assert!(all.len() > 3, "the sine-wave fixture has turns: {all:?}");
    press(&mut s, KeyCode::Char('g'));
    press(&mut s, KeyCode::Char('g'));
    press(&mut s, KeyCode::Char('}'));
    let first_after_0 = *all.iter().find(|&&i| i > 0).unwrap();
    assert_eq!(s.tiles[0].cursor, Some(first_after_0));
    let line = s.readout(&bars, Some(first_after_0), None);
    let text: String = line.spans.iter().map(|sp| sp.content.as_ref()).collect();
    assert!(
        text.contains("swing") || text.contains("vol"),
        "the readout says why it stopped: {text}"
    );
    press(&mut s, KeyCode::Char('2'));
    press(&mut s, KeyCode::Char('}'));
    let k = all.iter().position(|&i| i == first_after_0).unwrap();
    assert_eq!(s.tiles[0].cursor, Some(all[k + 2]), "2}} skips one stop");
    press(&mut s, KeyCode::Char('{'));
    assert_eq!(s.tiles[0].cursor, Some(all[k + 1]));
}

#[test]
fn space_w_splits_eats_and_closes_tiles() {
    let (mut s, _tx) = loaded();
    let k = |c: char| KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE);
    assert!(s.leader_window(k('l')));
    assert_eq!(s.tiles.len(), 5);
    assert_eq!(s.focus, 4);
    // straight back to normal keys, the new tile on the copied ticker
    assert!(s.prompt.is_none());
    assert_eq!(s.tiles[4].sym, s.tiles[0].sym);
    let out = render(&mut s, 120, 30);
    assert!(out.contains(&s.tiles[1].sym));
    // eat: the new tile grows down over the bottom row's middle
    s.on_key(k('m'));
    s.on_key(k('j'));
    assert!(render(&mut s, 120, 30).contains("eat"));
    s.on_key(KeyEvent::new(KeyCode::Enter, KeyModifiers::NONE));
    assert!(s.eat.is_none());
    assert_eq!(s.tiles.len(), s.grid.cells.len());
    // close it again
    let before = s.tiles.len();
    assert!(s.leader_window(k('c')));
    assert_eq!(s.tiles.len(), before - 1);
    render(&mut s, 120, 30);
}

#[test]
fn edits_save_the_layout_and_f_loads_one() {
    let p = std::env::temp_dir().join(format!("fl-layouts-{}.json", std::process::id()));
    let _ = std::fs::remove_file(&p);
    // SAFETY: only this test sets this variable
    unsafe { std::env::set_var(super::layouts::FILE_ENV, &p) };
    let (mut s, _tx) = loaded();
    let k = |c: char| KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE);
    s.leader_window(k('j'));
    let mine = s.layout_id.expect("an edit saves a layout");
    let saved = super::layouts::load();
    let l = saved.iter().find(|l| l.id == mine).unwrap();
    assert_eq!(l.cells.len(), 5);
    // a fresh screen opens the menu and loads it
    let (mut t, _tx2) = loaded();
    t.on_key(k('f'));
    assert!(render(&mut t, 120, 30).contains("layouts"));
    let at = t.menu.as_ref().unwrap().0.iter().position(|l| l.id == mine).unwrap();
    for _ in 0..at {
        t.on_key(k('j'));
    }
    t.on_key(KeyEvent::new(KeyCode::Enter, KeyModifiers::NONE));
    assert!(t.menu.is_none());
    assert_eq!(t.tiles.len(), 5);
    assert_eq!(t.grid, s.grid);
    super::layouts::delete(mine);
    let _ = std::fs::remove_file(p);
}
