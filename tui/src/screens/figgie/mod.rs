// Figgie (home key `F`): Jane Street's trading card game against 3 or 4 bots.
// Four suits, one goal suit worth $10 a card plus the pot remainder, four
// minutes of open outcry. The rules and the bots live in game.rs.
//
//   figgie › round 1 · 3:42 left · pot $200 · goal hidden
//   ┌ you ───────────────────────────────────────┐ ┌ trade history ─────┐
//   │ You  $310   ♠ 4  ♣ 2  ♦ 0  ♥ 2   quotes 1  │ │ buyer    suit seller   │
//   └────────────────────────────────────────────┘ │ Bot 1      ♥  Bot 2 $24 │
//   ▸ 1 ▲              ♠ spades   last 3      2 ▼ │ Bot 2      ♦  You   $19 │
//   [sell]  [bid $12▏]                  [offer –] [buy]                    │
//     …                                                                    │
//   ┌ players ────────────────────────────────────┐                        │
//   │ Bot 1   $273   quotes 0                      │                        │
//   └─────────────────────────────────────────────┘                        │
//   bid ♠ spades $12▏  enter sends · esc cancels
//   ←→ suit · b bid · a offer · s sell · f buy · x cancel · n next round · q leave
//
// Opponents' hands stay hidden: only your own holdings show until settlement.

mod game;

use std::io;
use std::time::Instant;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Alignment, Constraint, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Paragraph, Row, Table};

use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{Key, key, render_footer};
use crate::ui::theme::Theme;
use game::{Game, POT, SUITS, Side, Suit};

const KEYS: &[Key] = &[
    key("←→", "suit"),
    key("b", "bid"),
    key("a", "offer"),
    key("s", "sell"),
    key("f", "buy"),
    key("x", "cancel"),
    key("n", "next round"),
    key("q", "leave"),
];

/// Below this width the trade history column is dropped.
const HISTORY_MIN_WIDTH: u16 = 90;
const HISTORY_W: u16 = 38;

pub struct Figgie {
    game: Game,
    theme: Theme,
    /// Selected suit (index into SUITS).
    suit: usize,
    /// Price being typed: which side, and the digits so far.
    entry: Option<Side>,
    digits: String,
    flash: Option<String>,
    last_tick: Instant,
}

/// `fl figgie [3|4]`: bots at the table, 3 by default.
pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Figgie> {
    let bots = arg
        .as_deref()
        .and_then(|a| a.trim().parse::<usize>().ok())
        .filter(|b| (3..=4).contains(b))
        .unwrap_or(3);
    Ok(Figgie {
        game: Game::new(bots, Game::seed_from_clock()),
        theme: ctx.theme,
        suit: 0,
        entry: None,
        digits: String::new(),
        flash: None,
        last_tick: Instant::now(),
    })
}

fn money(v: i64) -> String {
    format!("${v}")
}

fn num_style(t: &Theme) -> Style {
    t.base().fg(t.num)
}

fn suit_style(t: &Theme, s: Suit) -> Style {
    if s.red() { t.down() } else { t.base() }
}

fn panel<'a>(t: &Theme, title: &'a str) -> Block<'a> {
    Block::bordered()
        .border_style(t.border())
        .title(Span::styled(title, t.title()))
}

impl Figgie {
    fn submit(&mut self) {
        let Some(side) = self.entry else { return };
        let Ok(px) = self.digits.parse::<i64>() else {
            self.flash = Some("type a price first".into());
            return;
        };
        let s = SUITS[self.suit];
        let res = match side {
            Side::Bid => self.game.bid(0, s, px),
            Side::Offer => self.game.offer(0, s, px),
        };
        self.entry = None;
        self.digits.clear();
        if let Err(e) = res {
            self.flash = Some(e);
        }
    }

    fn act(&mut self, res: Result<(), String>) {
        if let Err(e) = res {
            self.flash = Some(e);
        }
    }

    fn quote_count(&self, p: usize) -> usize {
        self.game.bids[p]
            .iter()
            .chain(self.game.offers[p].iter())
            .flatten()
            .count()
    }

    fn header_line(&self) -> Line<'static> {
        let t = self.theme;
        let g = &self.game;
        let mins = (g.left.max(0.0) / 60.0).floor() as i64;
        let secs = (g.left.max(0.0) % 60.0).floor() as i64;
        let state = match &g.settled {
            Some(st) => format!(
                "round over · goal {} {} ({} cards)",
                st.goal.glyph(),
                st.goal.name(),
                st.counts[st.goal.idx()]
            ),
            None => format!("{mins}:{secs:02} left · goal hidden"),
        };
        Line::from(vec![
            Span::styled("figgie", t.title()),
            Span::styled(
                format!(" › round {} · {} · pot ${POT}", g.round, state),
                t.dim(),
            ),
        ])
    }

    /// Your own hand: cash, holdings per suit, open quotes. Opponents' hands are not shown.
    fn draw_hand(&self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        let g = &self.game;
        let me = &g.players[0];
        let mut spans = vec![
            Span::styled("You", t.title()),
            Span::styled(format!("  {}", money(me.bank)), num_style(&t)),
        ];
        for s in SUITS {
            let held = me.holds[s.idx()];
            let style = if held < 0 {
                t.down()
            } else {
                suit_style(&t, s)
            };
            spans.push(Span::styled(format!("   {} {held}", s.glyph()), style));
        }
        spans.push(Span::styled(
            format!("   quotes {}", self.quote_count(0)),
            t.dim(),
        ));
        frame.render_widget(
            Paragraph::new(Line::from(spans)).block(panel(&t, " you ")),
            area,
        );
    }

    /// Four suit rows: best bid and offer on the top line, sell / bid / offer / buy below.
    fn draw_market(&self, frame: &mut Frame, area: Rect) {
        let rows = Layout::vertical([Constraint::Length(3); 4]).split(area);
        for (i, &s) in SUITS.iter().enumerate() {
            self.draw_suit(frame, rows[i], i, s);
        }
    }

    fn draw_suit(&self, frame: &mut Frame, area: Rect, i: usize, s: Suit) {
        let t = self.theme;
        let g = &self.game;
        let sel = i == self.suit;
        let [top, buttons, _gap] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let bid = g.best_bid(s, None);
        let ask = g.best_offer(s, None);
        let marker = if sel { "▸ " } else { "  " };
        let [l, c, r] = Layout::horizontal([
            Constraint::Length(16),
            Constraint::Min(0),
            Constraint::Length(16),
        ])
        .areas(top);
        let left = bid.map_or("–".into(), |(p, _)| money(p));
        let right = ask.map_or("–".into(), |(p, _)| money(p));
        frame.render_widget(
            Paragraph::new(Span::styled(format!("{marker}{left} ▲"), num_style(&t))),
            l,
        );
        let last = g.last[s.idx()].map_or("–".into(), money);
        let mut name_style = suit_style(&t, s);
        if sel {
            name_style = name_style.add_modifier(Modifier::BOLD);
        }
        frame.render_widget(
            Paragraph::new(Span::styled(
                format!("{} {}   last {last}", s.glyph(), s.name()),
                name_style,
            ))
            .alignment(Alignment::Center),
            c,
        );
        frame.render_widget(
            Paragraph::new(Span::styled(format!("▼ {right}  "), num_style(&t)))
                .alignment(Alignment::Right),
            r,
        );

        // Buttons: sell and buy light up when there is a price to hit.
        let [sell, _, bid_box, _, offer_box, _, buy] = Layout::horizontal([
            Constraint::Length(8),
            Constraint::Length(2),
            Constraint::Length(18),
            Constraint::Min(0),
            Constraint::Length(18),
            Constraint::Length(2),
            Constraint::Length(8),
        ])
        .areas(buttons);
        let live = |on: bool| if on { t.accent() } else { t.dim() };
        frame.render_widget(
            Paragraph::new(Span::styled("[sell]", live(bid.is_some()))),
            sell,
        );
        frame.render_widget(
            Paragraph::new(Span::styled("[buy]", live(ask.is_some()))),
            buy,
        );

        let own_bid = g.bids[0][s.idx()];
        let own_offer = g.offers[0][s.idx()];
        let typing = |side: Side| sel && self.entry == Some(side);
        let bid_text = if typing(Side::Bid) {
            Span::styled(format!("bid ${}▏", self.digits), t.accent())
        } else {
            match own_bid {
                Some(p) => Span::styled(format!("bid {} yours", money(p)), t.dim()),
                None => Span::styled("bid ——", t.dim()),
            }
        };
        let offer_text = if typing(Side::Offer) {
            Span::styled(format!("offer ${}▏", self.digits), t.accent())
        } else {
            match own_offer {
                Some(p) => Span::styled(format!("offer {} yours", money(p)), t.dim()),
                None => Span::styled("offer ——", t.dim()),
            }
        };
        frame.render_widget(Paragraph::new(bid_text), bid_box);
        frame.render_widget(
            Paragraph::new(offer_text).alignment(Alignment::Right),
            offer_box,
        );
    }

    /// Opponents: cash and open quotes. At settlement, their goal cards and payouts.
    fn draw_players(&self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        let g = &self.game;
        let header = Row::new(["player", "bank", "quotes", "goal", "pay", "bonus"]).style(t.dim());
        let rows: Vec<Row> = (1..g.players.len())
            .map(|i| {
                let p = &g.players[i];
                let (goal, pay, bonus) = match &g.settled {
                    Some(st) => (
                        Cell::from(Span::styled(format!("{:+}", st.goal_cards[i]), t.base())),
                        Cell::from(Span::styled(money(st.goal_pay[i]), num_style(&t))),
                        Cell::from(Span::styled(money(st.bonus[i]), num_style(&t))),
                    ),
                    None => (
                        Cell::from(Span::styled("–", t.dim())),
                        Cell::from(Span::styled("–", t.dim())),
                        Cell::from(Span::styled("–", t.dim())),
                    ),
                };
                Row::new(vec![
                    Cell::from(Span::styled(p.name.clone(), t.base())),
                    Cell::from(Span::styled(money(p.bank), num_style(&t))),
                    Cell::from(Span::styled(self.quote_count(i).to_string(), t.dim())),
                    goal,
                    pay,
                    bonus,
                ])
            })
            .collect();
        let widths = [
            Constraint::Length(10),
            Constraint::Length(8),
            Constraint::Length(8),
            Constraint::Length(6),
            Constraint::Length(8),
            Constraint::Min(7),
        ];
        frame.render_widget(
            Table::new(rows, widths)
                .header(header)
                .block(panel(&t, " players ")),
            area,
        );
    }

    /// Newest trades at the bottom, as many as fit.
    fn draw_history(&self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        let g = &self.game;
        let inner = area.height.saturating_sub(3) as usize;
        let start = g.trades.len().saturating_sub(inner);
        let rows: Vec<Row> = g.trades[start..]
            .iter()
            .map(|tr| {
                Row::new(vec![
                    Cell::from(Span::styled(g.players[tr.buyer].name.clone(), t.base())),
                    Cell::from(Span::styled(
                        tr.suit.glyph().to_string(),
                        suit_style(&t, tr.suit),
                    )),
                    Cell::from(Span::styled(g.players[tr.seller].name.clone(), t.base())),
                    Cell::from(Span::styled(money(tr.price), num_style(&t))),
                ])
            })
            .collect();
        let widths = [
            Constraint::Length(9),
            Constraint::Length(5),
            Constraint::Length(9),
            Constraint::Min(4),
        ];
        let header = Row::new(["buyer", "suit", "seller", "price"]).style(t.dim());
        frame.render_widget(
            Table::new(rows, widths)
                .header(header)
                .block(panel(&t, " trade history ")),
            area,
        );
    }

    fn entry_line(&self) -> Line<'static> {
        let t = self.theme;
        let s = SUITS[self.suit];
        match self.entry {
            Some(side) => {
                let word = match side {
                    Side::Bid => "bid",
                    Side::Offer => "offer",
                };
                Line::from(vec![
                    Span::styled(format!("{word} {} {} ", s.glyph(), s.name()), t.accent()),
                    Span::styled(format!("${}▏", self.digits), t.base()),
                    Span::styled("  enter sends · esc cancels", t.dim()),
                ])
            }
            None => Line::from(vec![
                Span::styled(format!("{} {}", s.glyph(), s.name()), suit_style(&t, s)),
                Span::styled("  one card per order, $1 steps", t.dim()),
            ]),
        }
    }
}

impl Screen for Figgie {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);

        let [header, body, entry, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(0),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(self.header_line()), header);

        let others = self.game.players.len() as u16 - 1;
        let (left, history) = if body.width >= HISTORY_MIN_WIDTH {
            let [l, r] =
                Layout::horizontal([Constraint::Min(0), Constraint::Length(HISTORY_W)]).areas(body);
            (l, Some(r))
        } else {
            (body, None)
        };
        let [hand, market, players, _rest] = Layout::vertical([
            Constraint::Length(3),
            Constraint::Length(12),
            Constraint::Length(others + 3),
            Constraint::Min(0),
        ])
        .areas(left);
        self.draw_hand(frame, hand);
        self.draw_market(frame, market);
        self.draw_players(frame, players);
        if let Some(h) = history {
            self.draw_history(frame, h);
        }

        frame.render_widget(Paragraph::new(self.entry_line()), entry);
        render_footer(frame, footer, KEYS, self.flash.as_deref(), &t);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        match key.code {
            KeyCode::Esc if self.entry.is_some() => {
                self.entry = None;
                self.digits.clear();
            }
            KeyCode::Esc | KeyCode::Char('q') if self.entry.is_none() => return Action::Quit,
            KeyCode::Enter => self.submit(),
            KeyCode::Backspace => {
                self.digits.pop();
            }
            KeyCode::Char(c) if self.entry.is_some() => {
                if c.is_ascii_digit() && self.digits.len() < 4 {
                    self.digits.push(c);
                }
            }
            KeyCode::Char('b') => {
                self.entry = Some(Side::Bid);
                self.digits.clear();
            }
            KeyCode::Char('a') => {
                self.entry = Some(Side::Offer);
                self.digits.clear();
            }
            KeyCode::Left | KeyCode::Up | KeyCode::Char('h' | 'k') => {
                self.suit = (self.suit + 3) % 4;
            }
            KeyCode::Right | KeyCode::Down | KeyCode::Char('l' | 'j') => {
                self.suit = (self.suit + 1) % 4;
            }
            KeyCode::Char('f') => {
                let s = SUITS[self.suit];
                let res = self.game.lift(0, s);
                self.act(res);
            }
            KeyCode::Char('s') => {
                let s = SUITS[self.suit];
                let res = self.game.hit(0, s);
                self.act(res);
            }
            KeyCode::Char('x') => {
                let s = SUITS[self.suit];
                self.game.cancel(0, s);
            }
            KeyCode::Char('n') => {
                let res = self.game.next_round();
                self.act(res);
            }
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        let now = Instant::now();
        let dt = now.duration_since(self.last_tick).as_secs_f64().min(0.5);
        self.last_tick = now;
        self.game.advance(dt);
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }

    fn shows_tape(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState, KeyModifiers};

    fn press(f: &mut Figgie, code: KeyCode) {
        f.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        });
    }

    fn screen(bots: usize) -> Figgie {
        Figgie {
            game: Game::new(bots, 42),
            theme: Theme::default(),
            suit: 0,
            entry: None,
            digits: String::new(),
            flash: None,
            last_tick: Instant::now(),
        }
    }

    fn render(f: &mut Figgie, w: u16, h: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|frame| f.draw(frame)).unwrap();
        term.backend()
            .buffer()
            .content()
            .iter()
            .map(|c| c.symbol())
            .collect()
    }

    #[test]
    fn typing_a_bid_sends_it_to_the_game() {
        let mut f = screen(3);
        press(&mut f, KeyCode::Char('b'));
        press(&mut f, KeyCode::Char('1'));
        press(&mut f, KeyCode::Char('2'));
        assert_eq!(f.digits, "12");
        press(&mut f, KeyCode::Enter);
        assert!(f.entry.is_none());
        assert!(f.digits.is_empty());
        // Either it rests as a bid or it crossed an offer; it must not be refused.
        assert!(f.flash.is_none(), "unexpected refusal: {:?}", f.flash);
    }

    #[test]
    fn q_leaves_but_not_while_typing() {
        let mut f = screen(3);
        press(&mut f, KeyCode::Char('a'));
        assert!(matches!(
            f.on_key(KeyEvent::new(KeyCode::Char('q'), KeyModifiers::NONE)),
            Action::None
        ));
        press(&mut f, KeyCode::Esc);
        assert!(matches!(
            f.on_key(KeyEvent::new(KeyCode::Char('q'), KeyModifiers::NONE)),
            Action::Quit
        ));
    }

    #[test]
    fn draws_the_table_without_showing_opponent_hands() {
        for bots in [3, 4] {
            let mut f = screen(bots);
            f.game.advance(30.0);
            let text = render(&mut f, 110, 36);
            assert!(text.contains("players"));
            assert!(text.contains("trade history"));
            assert!(text.contains("[sell]"));
            assert!(text.contains("Bot 1"));
            // Opponent holdings never render: the players panel has no suit columns.
            assert!(!text.contains("♠ +"), "opponent hand leaked");
        }
    }

    #[test]
    fn narrow_terminal_drops_the_history_column() {
        let mut f = screen(3);
        let text = render(&mut f, 70, 30);
        assert!(!text.contains("trade history"));
        assert!(text.contains("[sell]"));
    }

    #[test]
    fn settled_round_shows_the_goal() {
        let mut f = screen(3);
        f.game.advance(241.0);
        let text = render(&mut f, 110, 36);
        assert!(text.contains("round over"));
        assert!(text.contains(f.game.goal.name()));
    }
}
