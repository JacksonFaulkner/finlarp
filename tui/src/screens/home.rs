// `fl` / `fl .`: the front door. The screens sit on a keyboard: each key is
// the screen bound to it, and a shifted key's screen shows in the top line of
// the same key. A cursor moves over the board (hjkl or arrows): h and l move
// sideways instead of opening their screens, and Enter opens the screen under
// the cursor. Pressing any other key opens its screen. q/esc inside a screen
// comes back here.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Alignment, Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, Route, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

/// (title, screen, description, key). Screens that need a ticker open the
/// ticker picker when given none. A shifted key (`N`, `?`) is listed here as
/// itself and sits on the same board key as its base letter.
const ENTRIES: &[(&str, &str, &str, char)] = &[
    (
        "Portfolio",
        "portfolio",
        "positions, exposure, risk, activity",
        'p',
    ),
    ("History chart", "chart", "daily portfolio value", 'h'),
    ("CANSLIM", "canslim", "scorecard for one ticker", 'c'),
    (
        "Dossier",
        "dossier",
        "sourced research file for one ticker",
        'd',
    ),
    (
        "Filing search",
        "search",
        "full-text search over SEC filings",
        's',
    ),
    (
        "AI universe",
        "universe",
        "browse the sectors and regions",
        'u',
    ),
    (
        "Earnings report",
        "earnings",
        "latest earnings research report",
        'e',
    ),
    (
        "Diagrams",
        "diagrams",
        "chip fab, fiber optics, data center power",
        'x',
    ),
    ("Events", "events", "catalyst calendar", 'v'),
    ("Chat", "chat", "ask Claude; open the tickers it names", 'a'),
    ("Candles", "candles", "daily OHLC and volume for one ticker", 'b'),
    ("Intraday", "intraday", "2x2 live candle tapes", 'i'),
    ("Filings", "filings", "EDGAR 8-K and 6-K filing search", 'f'),
    ("Notes", "notes", "questions asked, answers as they arrive", 'n'),
    ("New note", "note", "type a note; answered in the background", 'N'),
    ("Godel", "godel", "ranked commands for a question", 'r'),
    ("Menu", "menu", "filterable list of standalone commands", 'M'),
    ("Sources", "sources", "data providers, keys and schedules", 'S'),
    ("Transactions", "transactions", "E*TRADE transaction history", 't'),
    ("Watchlists", "watchlists", "watchlist with daily change", 'w'),
    ("Onboard", "onboard", "add a ticker, pull its data, build its dossier", 'o'),
    ("Claude history", "claude_history", "browse Claude Code sessions", 'H'),
    ("Claude log", "claude_log", "tail of the Claude background log", 'l'),
    ("Video", "video", "play docs screen recordings in the terminal", 'V'),
    ("Keys", "keys", "command and key reference", '?'),
];

/// The board, unshifted, row by row: number row, then the three letter rows.
/// Keys with no screen stay blank. The space bar sits below, drawn apart.
const BOARD: [&str; 4] = ["1234567890", "qwertyuiop", "asdfghjkl;", "zxcvbnm,./"];
/// Row index of the space bar (one cell, one row below the letters).
const SPACE_ROW: usize = BOARD.len();
/// Each row's indent, in quarters of a key, as on a real keyboard.
const INDENT: [u16; 4] = [0, 2, 3, 5];
/// Space bar: indent and span, in quarters and keys.
const SPACE_INDENT: u16 = 6;
const SPACE_KEYS: u16 = 6;
/// A key is a bordered box: a shifted-legend line and two title lines.
const KEY_H: u16 = 5;
/// Narrowest key that still fits the whole board: 5 columns a key puts all
/// ten keys of the top row in about 58 columns. Narrower panes drop the far right.
const KEY_W_MIN: u16 = 5;
const KEY_W_MAX: u16 = 14;

/// The wordmark: Pits font, one row per line, every row padded to the same
/// width so the block centres as a whole.
const WORDMARK: &str = r"▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄      ▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄ 
██▀┼┼┼┼┼┼┼█ █┼┼┼▀██ ██▀┼┼┼┼┼┼┼▀██ ██▀┼┼█      ██▀┼┼┼┼┼┼┼▀██ █┼┼┼┼┼┼┼┼▀▀▄▀ ██▀┼┼┼┼┼┼▀▀▄
█▌┼┼┼▄▀▀▀▀▀ █┼┼┼┼▐█ █▌┼┼┼▄▀▄┼┼┼▐█ █▌┼┼┼█      █▌┼┼┼▄▀▄┼┼┼▐█ █┼┼┼┼▄▀▄┼┼┼░█ █▌┼┼┼▄▀▄┼┼┼█
█┼┼┼┼█▄▄▄▄  █┼┼┼┼┼█ █┼┼┼┼▓ ▓┼┼┼┼█ █┼┼┼┼█      █┼┼┼┼▀▄▀┼┼┼┼█ █┼┼┼┼▀▀▀┼┼▄▀▀ █┼┼┼┼▀▀▀┼┼┼█
▓┼┼┼┼█▀▀▀▀  ▓┼┼┼┼┼▓ ▓┼┼┼┼▒ ▒┼┼┼┼▓ ▓┼┼┼┼█      ▓┼┼┼┼┼┼┼┼┼┼┼▓ ▓┼┼┼┼▓▄┼┼┼▀▀▀ ▓┼┼┼┼┼┼┼┼┼▄▀
▒▌┼┼┼█      ▒▌┼┼┼┼▒ ▒▌┼┼┼░ ░┼┼┼▐▒ ▒▌┼┼┼▀▄▄▄▄▄ ▒▌┼┼┼▄▀▄┼┼┼▐▒ ▒┼┼┼┼▒ ▓┼┼┼▓▓ ▒▌┼┼┼▓▀▀▀▀▀ 
░█▄┼┼▒      ░█▄┼┼┼░ ░█▄┼┼░ ░┼┼▄█░ ░█▄┼┼┼┼┼┼┼▒ ░█▄┼┼▒ ▒┼┼▄█░ ░┼┼┼┼░ ▒┼┼▄█▒ ░█▄┼▐▒      
▀▀▀▀▀▀      ▀▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀ ▀▀▀▀▀▀      ";
const WORDMARK_H: u16 = 8;


/// The shifted character a key produces on this board.
fn shifted(c: char) -> char {
    match c {
        '1' => '!',
        '2' => '@',
        '3' => '#',
        '4' => '$',
        '5' => '%',
        '6' => '^',
        '7' => '&',
        '8' => '*',
        '9' => '(',
        '0' => ')',
        ',' => '<',
        '.' => '>',
        '/' => '?',
        ';' => ':',
        c => c.to_ascii_uppercase(),
    }
}

/// The ENTRIES index bound to this exact key, if any.
fn entry_for(c: char) -> Option<usize> {
    ENTRIES.iter().position(|e| e.3 == c)
}

/// What home does with a key that has no screen of its own.
fn reserved(c: char) -> Option<&'static str> {
    match c {
        'q' => Some("quit"),
        'h' => Some("left"),
        'j' => Some("down"),
        'k' => Some("up"),
        'l' => Some("right"),
        'g' => Some("top"),
        'G' => Some("end"),
        _ => None,
    }
}

/// Board position (row, column) of the key that produces `c`, base or shifted.
fn key_pos(c: char) -> Option<(usize, usize)> {
    BOARD.iter().enumerate().find_map(|(r, row)| {
        row.chars()
            .position(|b| b == c || shifted(b) == c)
            .map(|k| (r, k))
    })
}

/// Columns in a board row. The space bar row has one cell.
fn row_len(r: usize) -> usize {
    if r == SPACE_ROW {
        1
    } else {
        BOARD[r].len()
    }
}

/// Horizontal centre of a cell, in quarters of a key, so rows line up as drawn.
fn cell_x(r: usize, c: usize) -> i32 {
    if r == SPACE_ROW {
        i32::from(SPACE_INDENT)
    } else {
        i32::from(INDENT[r]) + 4 * c as i32
    }
}

/// The column in row `r` whose cell sits closest to horizontal position `x`.
fn nearest_col(r: usize, x: i32) -> usize {
    (0..row_len(r))
        .min_by_key(|&c| (cell_x(r, c) - x).abs())
        .unwrap_or(0)
}

/// A title in at most two lines of `w` columns. Anything longer is cut with an ellipsis.
fn title_lines(s: &str, w: usize) -> Vec<String> {
    let mut lines = text::wrap(s, w.max(1));
    if lines.len() > 2 {
        let rest = lines.split_off(1).join(" ");
        lines.truncate(1);
        lines.push(text::truncate(&rest, w));
    }
    lines
}

pub struct Home {
    /// Board cursor: (row, column). The space bar is row SPACE_ROW.
    cursor: (usize, usize),
    theme: Theme,
}

pub fn open(ctx: &Ctx) -> io::Result<Home> {
    Ok(Home {
        cursor: key_pos('p').unwrap_or((0, 0)),
        theme: ctx.theme,
    })
}

/// Home's palette, from the theme like every other screen: borders and idle
/// keys in the border grey, keys and labels in the accent, legends in dim,
/// the selected key on the cursor background.
fn edge(t: &Theme) -> Style {
    t.border()
}
fn lit(t: &Theme) -> Style {
    t.accent()
}
fn grey(t: &Theme) -> Style {
    t.dim()
}
fn idle(t: &Theme) -> Style {
    t.border()
}
fn picked(t: &Theme) -> Style {
    t.selected().add_modifier(Modifier::BOLD)
}

impl Home {
    /// The base character under the cursor, None on the space bar.
    fn cursor_char(&self) -> Option<char> {
        let (r, c) = self.cursor;
        if r == SPACE_ROW {
            None
        } else {
            BOARD[r].chars().nth(c)
        }
    }

    /// The entry under the cursor: the key's own screen, else its shifted one.
    fn entry_at(&self) -> Option<usize> {
        let base = self.cursor_char()?;
        entry_for(base).or_else(|| entry_for(shifted(base)))
    }

    fn across(&mut self, delta: isize) {
        let (r, c) = self.cursor;
        let last = row_len(r) as isize - 1;
        self.cursor = (r, (c as isize + delta).clamp(0, last) as usize);
    }

    fn down_up(&mut self, delta: isize) {
        let (r, c) = self.cursor;
        let x = cell_x(r, c);
        let nr = (r as isize + delta).clamp(0, SPACE_ROW as isize) as usize;
        self.cursor = (nr, nearest_col(nr, x));
    }

    fn open_at(&self, i: usize) -> Action {
        Action::Route(Route::Screen {
            screen: ENTRIES[i].1.into(),
            arg: None,
        })
    }

    fn draw_key(&self, frame: &mut Frame, r: Rect, base: char, selected: bool) {
        let t = self.theme;
        let top = shifted(base);
        let primary = entry_for(base);
        let secondary = entry_for(top);
        let face = if selected {
            picked(&t)
        } else if primary.is_some() {
            lit(&t)
        } else {
            idle(&t)
        };
        let legend = if selected { picked(&t) } else { grey(&t) };
        let block = Block::bordered()
            .border_style(if selected { lit(&t) } else { edge(&t) })
            .style(face)
            .title_top(Line::styled(
                format!(" {base} "),
                if selected { picked(&t) } else { t.base() },
            ));
        let inner = block.inner(r);
        let w = inner.width as usize;

        // The top line is the shifted key's legend: its screen, its reserved
        // action, or just its letter when nothing is bound to it yet.
        let shift_line = match (secondary, reserved(top)) {
            (Some(j), _) => format!("{top} {}", ENTRIES[j].0),
            (None, Some(label)) => format!("{top} {label}"),
            _ => top.to_string(),
        };
        let mut lines = vec![Line::styled(text::truncate(&shift_line, w), legend)];
        match (primary, reserved(base)) {
            (Some(i), _) => {
                for l in title_lines(ENTRIES[i].0, w) {
                    lines.push(Line::styled(l, face));
                }
            }
            (None, Some(label)) => lines.push(Line::styled(label.to_string(), legend)),
            _ => {}
        }

        frame.render_widget(block, r);
        frame.render_widget(
            Paragraph::new(lines)
                .alignment(Alignment::Center)
                .style(face),
            inner,
        );
    }
}

impl Screen for Home {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        // The logo and the keyboard are one group, centred in the screen.
        let board_h = (BOARD.len() as u16 + 1) * KEY_H;
        let [_, head, _, board, _] = Layout::vertical([
            Constraint::Min(0),
            Constraint::Length(WORDMARK_H),
            Constraint::Length(1),
            Constraint::Length(board_h),
            Constraint::Min(0),
        ])
        .areas(area);

        // The wordmark, centred as one block.
        let (lines, width) = wordmark(&t);
        let w = width.min(head.width);
        let logo = Rect {
            x: head.x + head.width.saturating_sub(width) / 2,
            width: w,
            ..head
        };
        frame.render_widget(Paragraph::new(lines), logo);

        // Key width from the board's width; the zxcv row is 11.25 keys wide.
        // The board is centred in the space below the header.
        let w = (board.width.saturating_sub(2) * 4 / 45).clamp(KEY_W_MIN, KEY_W_MAX);
        let board_w = w * 45 / 4;
        let origin = board.x + board.width.saturating_sub(board_w) / 2;
        for (r, row) in BOARD.iter().enumerate() {
            let x0 = origin + w * INDENT[r] / 4;
            let y = board.y + r as u16 * KEY_H;
            for (k, base) in row.chars().enumerate() {
                let key = Rect::new(x0 + k as u16 * w, y, w, KEY_H);
                if key.right() > board.right() || key.bottom() > board.bottom() {
                    continue;
                }
                self.draw_key(frame, key, base, self.cursor == (r, k));
            }
        }
        // Space bar, below the letters: the leader key (space, then a chord).
        let space = Rect::new(
            origin + w * SPACE_INDENT / 4,
            board.y + SPACE_ROW as u16 * KEY_H,
            w * SPACE_KEYS,
            KEY_H,
        );
        if space.right() <= board.right() && space.bottom() <= board.bottom() {
            let on = self.cursor.0 == SPACE_ROW;
            let style = if on { picked(&t) } else { Style::new() };
            let block = Block::bordered()
                .border_style(if on { lit(&t) } else { edge(&t) })
                .style(style)
                .title_top(Line::styled(" space ", edge(&t)));
            let inner = block.inner(space);
            frame.render_widget(block, space);
            frame.render_widget(
                Paragraph::new(vec![
                    Line::styled("leader", style),
                    Line::styled("ac chat", if on { style } else { grey(&t) }),
                ])
                .alignment(Alignment::Center),
                inner,
            );
        }

    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if key.modifiers.contains(KeyModifiers::CONTROL) {
            return match key.code {
                KeyCode::Char('n' | 'j') => {
                    self.down_up(1);
                    Action::None
                }
                KeyCode::Char('p' | 'k') => {
                    self.down_up(-1);
                    Action::None
                }
                _ => Action::None,
            };
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => Action::Quit,
            // h and l move the cursor; they do not open their screens.
            KeyCode::Char('h') | KeyCode::Left => {
                self.across(-1);
                Action::None
            }
            KeyCode::Char('l') | KeyCode::Right => {
                self.across(1);
                Action::None
            }
            KeyCode::Char('j') | KeyCode::Down => {
                self.down_up(1);
                Action::None
            }
            KeyCode::Char('k') | KeyCode::Up => {
                self.down_up(-1);
                Action::None
            }
            KeyCode::Char('g') | KeyCode::Home => {
                self.cursor = (0, 0);
                Action::None
            }
            KeyCode::Char('G') | KeyCode::End => {
                self.cursor = (SPACE_ROW, 0);
                Action::None
            }
            KeyCode::Enter => match self.entry_at() {
                Some(i) => self.open_at(i),
                None => Action::None,
            },
            KeyCode::Char(c) => match entry_for(c) {
                Some(i) => self.open_at(i),
                None => Action::None,
            },
            _ => Action::None,
        }
    }

    fn needs_redraw(&self) -> bool {
        false
    }
}

/// Colour for one wordmark character: the grid lines inside the letters in
/// white, the shading in light grey, the blocks in the theme accent.
fn wordmark_style(c: char, t: &Theme) -> Style {
    match c {
        '┼' => Style::new().fg(Color::White),
        '░' | '▒' | '▓' => Style::new().fg(Color::Gray),
        '▀' | '▄' | '█' | '▌' | '▐' => t.accent(),
        _ => t.base(),
    }
}

/// The logo's lines, coloured per character, and the width of the widest one.
fn wordmark(t: &Theme) -> (Vec<Line<'static>>, u16) {
    let lines: Vec<Line<'static>> = WORDMARK
        .lines()
        .map(|l| {
            Line::from(
                l.chars()
                    .map(|c| Span::styled(c.to_string(), wordmark_style(c, t)))
                    .collect::<Vec<_>>(),
            )
        })
        .collect();
    let width = lines.iter().map(Line::width).max().unwrap_or(0) as u16;
    (lines, width)
}

#[cfg(test)]
mod tests {
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn press(h: &mut Home, code: KeyCode) -> Action {
        h.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn opens(screen: &str) -> Action {
        Action::Route(Route::Screen {
            screen: screen.into(),
            arg: None,
        })
    }

    fn home() -> Home {
        open(&Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        })
        .expect("open")
    }

    #[test]
    fn cursor_starts_on_portfolio_and_enter_opens_it() {
        let mut h = home();
        assert_eq!(h.cursor, key_pos('p').unwrap());
        assert_eq!(press(&mut h, KeyCode::Enter), opens("portfolio"));
    }

    #[test]
    fn hotkeys_open_screens_except_h_and_l() {
        let mut h = home();
        assert_eq!(press(&mut h, KeyCode::Char('d')), opens("dossier"));
        assert_eq!(press(&mut h, KeyCode::Char('N')), opens("note"));
        assert_eq!(press(&mut h, KeyCode::Char('z')), Action::None);
        assert_eq!(press(&mut h, KeyCode::Char('q')), Action::Quit);
    }

    #[test]
    fn h_and_l_move_the_cursor_instead_of_opening() {
        let mut h = home();
        let start = h.cursor;
        // p is the last key of its row, so l stays put and h steps left to o.
        assert_eq!(press(&mut h, KeyCode::Char('l')), Action::None);
        assert_eq!(h.cursor, start);
        assert_eq!(press(&mut h, KeyCode::Char('h')), Action::None);
        assert_eq!(h.cursor, (1, 8));
        assert_eq!(press(&mut h, KeyCode::Char('l')), Action::None);
        assert_eq!(h.cursor, start);
    }

    #[test]
    fn enter_opens_the_screen_under_the_cursor_even_for_h_and_l() {
        let mut h = home();
        h.cursor = key_pos('h').unwrap();
        assert_eq!(press(&mut h, KeyCode::Enter), opens("chart"));
        h.cursor = key_pos('l').unwrap();
        assert_eq!(press(&mut h, KeyCode::Enter), opens("claude_log"));
    }

    #[test]
    fn j_and_k_move_by_physical_column() {
        let mut h = home();
        // p sits at x=38 quarters; the asdf row's nearest key there is ';'.
        press(&mut h, KeyCode::Char('j'));
        assert_eq!(h.cursor, (2, 9));
        press(&mut h, KeyCode::Char('k'));
        assert_eq!(h.cursor, (1, 9));
        // Down from the bottom letters reaches the space bar, then stops there.
        h.cursor = (3, 0);
        press(&mut h, KeyCode::Char('j'));
        assert_eq!(h.cursor, (SPACE_ROW, 0));
        press(&mut h, KeyCode::Char('j'));
        assert_eq!(h.cursor, (SPACE_ROW, 0));
    }

    #[test]
    fn g_and_capital_g_jump_to_the_ends() {
        let mut h = home();
        press(&mut h, KeyCode::Char('G'));
        assert_eq!(h.cursor, (SPACE_ROW, 0));
        press(&mut h, KeyCode::Char('g'));
        assert_eq!(h.cursor, (0, 0));
    }

    #[test]
    fn hotkeys_are_unique_and_screens_known() {
        for (i, a) in ENTRIES.iter().enumerate() {
            assert!(crate::SCREENS.contains(&a.1), "{} unknown", a.1);
            assert!(
                ENTRIES[i + 1..].iter().all(|b| b.3 != a.3),
                "dup key {}",
                a.3
            );
        }
    }

    #[test]
    fn every_entry_sits_on_the_board() {
        for e in ENTRIES {
            assert!(key_pos(e.3).is_some(), "{} is off the board", e.3);
        }
    }

    #[test]
    fn whole_top_row_shows_at_sixty_columns() {
        use ratatui::Terminal;
        use ratatui::backend::TestBackend;

        let mut h = home();
        let mut term = Terminal::new(TestBackend::new(60, 50)).unwrap();
        term.draw(|f| h.draw(f)).unwrap();
        let out = term.backend().to_string();
        // The last key of the top row (p) must not be cut off.
        assert!(out.contains("┌ p "), "{out}");
    }

    #[test]
    fn number_row_and_space_bar_are_on_the_board() {
        use ratatui::Terminal;
        use ratatui::backend::TestBackend;

        let mut h = home();
        let mut term = Terminal::new(TestBackend::new(120, 50)).unwrap();
        term.draw(|f| h.draw(f)).unwrap();
        let out = term.backend().to_string();
        assert!(out.contains("┌ 1 "), "number row missing: {out}");
        assert!(out.contains("┌ 0 "), "number row cut short: {out}");
        assert!(out.contains("space"), "space bar missing: {out}");
        assert!(out.contains("leader"), "space bar legend missing: {out}");
    }

    #[test]
    fn titles_fit_a_key_in_two_lines() {
        for e in ENTRIES {
            let lines = title_lines(e.0, 10);
            assert!(lines.len() <= 2, "{}: {lines:?}", e.0);
            assert!(lines.iter().all(|l| text::width(l) <= 10), "{}: {lines:?}", e.0);
        }
    }
}
