// Figgie rules engine (Jane Street's card game, figgie.com/how-to-play).
// No terminal and no clock in here: the screen calls `advance` with elapsed
// seconds, and the bots are driven from the same loop.
//
// Rules as published:
// - 4 or 5 players, each starting with $350. Every round each player antes an
//   equal share of a $200 pot ($50 each with 4 players, $40 with 5).
// - 40 cards in four suits of 12, 10, 10 and 8. Which suit gets which count is
//   random and hidden until the round ends.
// - The goal suit is the other suit of the 12-card suit's colour: 10 or 8 cards.
// - Cards are dealt evenly: 10 each with 4 players, 8 each with 5.
// - Four minutes of continuous trading. Bids and offers are for one card, in
//   $1 steps. Any trade cancels every open quote in every suit.
// - Settlement: each goal card pays $10 from the pot. The rest of the pot goes
//   to the player with the most goal cards; ties split it.
//
// Where the page is silent (my choices):
// - A bid needs the cash to cover it. An offer needs no card in hand: short
//   selling is allowed, so a holding can go negative and settles as a debt.
// - A bid at or above someone else's offer trades at that offer, and an offer
//   at or below someone else's bid trades at that bid. Quotes never rest across.
// - Bank carries over between rounds.
// - A remainder that does not split evenly goes to the lowest seat.

use std::time::{SystemTime, UNIX_EPOCH};

pub const START_CASH: i64 = 350;
pub const POT: i64 = 200;
pub const GOAL_PAY: i64 = 10;
pub const ROUND_SECS: f64 = 240.0;
/// Midpoint of the bonus the leader can get ($100 with a 10-card goal suit, $120 with 8).
const BONUS_GUESS: f64 = 110.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Suit {
    Hearts,
    Diamonds,
    Clubs,
    Spades,
}

pub const SUITS: [Suit; 4] = [Suit::Hearts, Suit::Diamonds, Suit::Clubs, Suit::Spades];

impl Suit {
    pub fn idx(self) -> usize {
        self as usize
    }

    pub fn glyph(self) -> char {
        match self {
            Suit::Hearts => '♥',
            Suit::Diamonds => '♦',
            Suit::Clubs => '♣',
            Suit::Spades => '♠',
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            Suit::Hearts => "hearts",
            Suit::Diamonds => "diamonds",
            Suit::Clubs => "clubs",
            Suit::Spades => "spades",
        }
    }

    pub fn red(self) -> bool {
        matches!(self, Suit::Hearts | Suit::Diamonds)
    }

    /// The other suit of this colour.
    pub fn partner(self) -> Suit {
        match self {
            Suit::Hearts => Suit::Diamonds,
            Suit::Diamonds => Suit::Hearts,
            Suit::Clubs => Suit::Spades,
            Suit::Spades => Suit::Clubs,
        }
    }
}

/// Which side of the book a typed price goes to.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    Bid,
    Offer,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Player {
    pub name: String,
    pub human: bool,
    pub bank: i64,
    /// Cards held now, per suit. Negative means short.
    pub holds: [i64; 4],
    /// Cards dealt this round: the sample a bot reasons from.
    pub dealt: [i64; 4],
    /// Bot's quote edge in dollars: how far from its fair value it will trade.
    pub edge: i64,
}

/// One executed trade: a card of `suit` moved from `seller` to `buyer` at `price`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Trade {
    pub buyer: usize,
    pub seller: usize,
    pub suit: Suit,
    pub price: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Settlement {
    pub goal: Suit,
    pub counts: [i64; 4],
    /// Signed goal cards per player.
    pub goal_cards: Vec<i64>,
    /// $10 per goal card, per player (negative means the player pays in).
    pub goal_pay: Vec<i64>,
    /// Share of the pot remainder, per player (only the leaders get any).
    pub bonus: Vec<i64>,
}

pub struct Game {
    pub players: Vec<Player>,
    pub round: u32,
    /// Seconds left in the round.
    pub left: f64,
    /// Cards per suit this round. Hidden from the player until settlement.
    pub counts: [i64; 4],
    pub goal: Suit,
    /// Standing bid per player per suit.
    pub bids: Vec<[Option<i64>; 4]>,
    /// Standing offer per player per suit.
    pub offers: Vec<[Option<i64>; 4]>,
    pub last: [Option<i64>; 4],
    /// Every trade so far, oldest first.
    pub trades: Vec<Trade>,
    pub settled: Option<Settlement>,
    bot_next: Vec<f64>,
    rng: Rng,
}

impl Game {
    /// `bots` is 3 or 4, so the table is 4 or 5 players as the rules deal.
    pub fn new(bots: usize, seed: u64) -> Self {
        let n = bots + 1;
        assert!(n == 4 || n == 5, "figgie deals 4 or 5 players");
        let mut rng = Rng(seed | 1);
        let mut players = vec![Player {
            name: "You".into(),
            human: true,
            bank: START_CASH,
            holds: [0; 4],
            dealt: [0; 4],
            edge: 0,
        }];
        for b in 1..=bots {
            let edge = 1 + rng.below(3) as i64;
            players.push(Player {
                name: format!("Bot {b}"),
                human: false,
                bank: START_CASH,
                holds: [0; 4],
                dealt: [0; 4],
                edge,
            });
        }
        let mut game = Game {
            players,
            round: 0,
            left: ROUND_SECS,
            counts: [0; 4],
            goal: Suit::Hearts,
            bids: vec![[None; 4]; n],
            offers: vec![[None; 4]; n],
            last: [None; 4],
            trades: Vec::new(),
            settled: None,
            bot_next: vec![0.0; n],
            rng,
        };
        game.start_round();
        game
    }

    pub fn seed_from_clock() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0x9e37_79b9)
    }

    pub fn start_round(&mut self) {
        self.round += 1;
        let n = self.players.len();
        let ante = POT / n as i64;

        let mut counts = [12i64, 10, 10, 8];
        self.rng.shuffle(&mut counts);
        self.counts = counts;
        let twelve = counts.iter().position(|&c| c == 12).unwrap_or(0);
        self.goal = SUITS[twelve].partner();

        let mut deck: Vec<usize> = Vec::with_capacity(40);
        for (s, &c) in counts.iter().enumerate() {
            deck.extend(std::iter::repeat_n(s, c as usize));
        }
        self.rng.shuffle(&mut deck);
        let per = deck.len() / n;

        for p in &mut self.players {
            p.holds = [0; 4];
            p.dealt = [0; 4];
            p.bank -= ante;
        }
        for (i, chunk) in deck.chunks(per).enumerate().take(n) {
            for &s in chunk {
                self.players[i].holds[s] += 1;
                self.players[i].dealt[s] += 1;
            }
        }

        self.cancel_all();
        self.last = [None; 4];
        self.left = ROUND_SECS;
        self.settled = None;
        for p in 1..n {
            self.bot_next[p] = ROUND_SECS - (0.5 + 2.0 * self.rng.unit());
        }
    }

    /// Starts the next round. Only once the current one has settled.
    pub fn next_round(&mut self) -> Result<(), String> {
        if self.settled.is_none() {
            return Err("round still on".into());
        }
        self.start_round();
        Ok(())
    }

    /// Advances the clock by `dt` seconds. Bots act when their turn comes; the
    /// round settles when the clock runs out.
    pub fn advance(&mut self, dt: f64) {
        if self.settled.is_some() {
            return;
        }
        self.left -= dt;
        for p in 1..self.players.len() {
            if self.left <= self.bot_next[p] {
                self.bot_act(p);
                self.bot_next[p] = self.left - (1.5 + 2.5 * self.rng.unit());
            }
        }
        if self.left <= 0.0 {
            self.settle();
        }
    }

    /// Lowest offer in `s`, from anyone but `excl`. Ties go to the lower seat.
    pub fn best_offer(&self, s: Suit, excl: Option<usize>) -> Option<(i64, usize)> {
        self.offers
            .iter()
            .enumerate()
            .filter(|(p, _)| Some(*p) != excl)
            .filter_map(|(p, q)| q[s.idx()].map(|px| (px, p)))
            .min_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)))
    }

    /// Highest bid in `s` that the bidder can still pay, from anyone but `excl`.
    /// Ties go to the lower seat.
    pub fn best_bid(&self, s: Suit, excl: Option<usize>) -> Option<(i64, usize)> {
        self.bids
            .iter()
            .enumerate()
            .filter(|(p, _)| Some(*p) != excl)
            .filter_map(|(p, q)| {
                q[s.idx()]
                    .filter(|&px| px <= self.players[p].bank)
                    .map(|px| (px, p))
            })
            .max_by(|a, b| a.0.cmp(&b.0).then(b.1.cmp(&a.1)))
    }

    /// Bid for one card of `s` at `px`. Crosses at once if someone offers at or below it.
    pub fn bid(&mut self, p: usize, s: Suit, px: i64) -> Result<(), String> {
        self.live()?;
        if px < 1 {
            return Err("bids start at $1".into());
        }
        if px > self.players[p].bank {
            return Err(format!(
                "${px} is more than your ${} cash",
                self.players[p].bank
            ));
        }
        match self.best_offer(s, Some(p)) {
            Some((ask, seller)) if ask <= px => self.trade(p, seller, s, ask),
            _ => {
                self.bids[p][s.idx()] = Some(px);
                Ok(())
            }
        }
    }

    /// Offer one card of `s` at `px`. Crosses at once if someone bids at or above it.
    pub fn offer(&mut self, p: usize, s: Suit, px: i64) -> Result<(), String> {
        self.live()?;
        if px < 1 {
            return Err("offers start at $1".into());
        }
        match self.best_bid(s, Some(p)) {
            Some((bid, buyer)) if bid >= px => self.trade(buyer, p, s, bid),
            _ => {
                self.offers[p][s.idx()] = Some(px);
                Ok(())
            }
        }
    }

    /// Buy one card of `s` at the best offer.
    pub fn lift(&mut self, p: usize, s: Suit) -> Result<(), String> {
        self.live()?;
        match self.best_offer(s, Some(p)) {
            Some((ask, seller)) => self.trade(p, seller, s, ask),
            None => Err(format!("no offer in {}", s.name())),
        }
    }

    /// Sell one card of `s` at the best bid.
    pub fn hit(&mut self, p: usize, s: Suit) -> Result<(), String> {
        self.live()?;
        match self.best_bid(s, Some(p)) {
            Some((bid, buyer)) => self.trade(buyer, p, s, bid),
            None => Err(format!("no bid in {}", s.name())),
        }
    }

    /// Takes back this player's quotes in `s`.
    pub fn cancel(&mut self, p: usize, s: Suit) {
        self.bids[p][s.idx()] = None;
        self.offers[p][s.idx()] = None;
    }

    fn live(&self) -> Result<(), String> {
        if self.settled.is_some() {
            Err("round over: n deals the next one".into())
        } else {
            Ok(())
        }
    }

    fn trade(&mut self, buyer: usize, seller: usize, s: Suit, px: i64) -> Result<(), String> {
        if buyer == seller {
            return Err("that's your own quote".into());
        }
        if self.players[buyer].bank < px {
            return Err(format!("can't pay ${px}"));
        }
        self.players[buyer].bank -= px;
        self.players[buyer].holds[s.idx()] += 1;
        self.players[seller].bank += px;
        self.players[seller].holds[s.idx()] -= 1;
        self.last[s.idx()] = Some(px);
        self.trades.push(Trade {
            buyer,
            seller,
            suit: s,
            price: px,
        });
        self.cancel_all();
        Ok(())
    }

    fn cancel_all(&mut self) {
        for q in self.bids.iter_mut().chain(self.offers.iter_mut()) {
            *q = [None; 4];
        }
    }

    fn settle(&mut self) {
        let n = self.players.len();
        let g = self.goal.idx();
        let goal_cards: Vec<i64> = self.players.iter().map(|p| p.holds[g]).collect();
        // Signed holdings sum to the goal suit's card count, 8 or 10.
        let total: i64 = goal_cards.iter().sum();
        let remainder = POT - GOAL_PAY * total;
        let top = goal_cards.iter().copied().max().unwrap_or(0);
        let leaders: Vec<usize> = (0..n).filter(|&i| goal_cards[i] == top).collect();
        let k = leaders.len() as i64;

        let mut bonus = vec![0i64; n];
        for (j, &i) in leaders.iter().enumerate() {
            bonus[i] = remainder / k + i64::from((j as i64) < remainder % k);
        }
        let goal_pay: Vec<i64> = goal_cards.iter().map(|c| GOAL_PAY * c).collect();
        for i in 0..n {
            self.players[i].bank += goal_pay[i] + bonus[i];
        }

        self.cancel_all();
        self.left = 0.0;
        self.settled = Some(Settlement {
            goal: self.goal,
            counts: self.counts,
            goal_cards,
            goal_pay,
            bonus,
        });
    }

    /// Bot turn: pick a suit and lift or hit if the market is cheap or rich
    /// against its fair value. If it trades, that cancels every quote, so the
    /// bot re-quotes everything; otherwise it refreshes its quotes in all suits.
    fn bot_act(&mut self, p: usize) {
        let s = SUITS[self.rng.below(4)];
        if self.bot_trade(p, s) {
            return;
        }
        for s in SUITS {
            self.bot_quote(p, s);
        }
    }

    /// Lifts the best offer or hits the best bid in `s` if it is worth the
    /// bot's edge. True if a trade happened.
    fn bot_trade(&mut self, p: usize, s: Suit) -> bool {
        let fair = self.fair_value(p, s);
        let edge = self.players[p].edge as f64;
        if let Some((ask, seller)) = self.best_offer(s, Some(p))
            && fair - ask as f64 >= edge
            && ask <= self.players[p].bank
        {
            return self.trade(p, seller, s, ask).is_ok();
        }
        if let Some((bid, buyer)) = self.best_bid(s, Some(p))
            && bid as f64 - fair >= edge
        {
            return self.trade(buyer, p, s, bid).is_ok();
        }
        false
    }

    /// Posts a bid and an offer in `s` around fair value, never crossing
    /// someone else's quote.
    fn bot_quote(&mut self, p: usize, s: Suit) {
        let fair = self.fair_value(p, s);
        let edge = self.players[p].edge as f64;
        let bank = self.players[p].bank;
        let bid_px = (fair - edge).floor() as i64;
        let under_ask = self.best_offer(s, Some(p)).is_none_or(|(a, _)| bid_px < a);
        self.bids[p][s.idx()] = (bid_px >= 1 && bid_px <= bank && under_ask).then_some(bid_px);

        let offer_px = (fair + edge).ceil() as i64;
        let over_bid = self.best_bid(s, Some(p)).is_none_or(|(b, _)| offer_px > b);
        self.offers[p][s.idx()] = (offer_px >= 1 && over_bid).then_some(offer_px);
    }

    /// Expected value of one more card of `s` for player `p`, from what they
    /// were dealt: P(s is goal) × (goal pay + expected bonus share).
    fn fair_value(&self, p: usize, s: Suit) -> f64 {
        let (pg, ec) = self.posterior(p);
        let n = self.players.len() as f64;
        let me = &self.players[p];
        let own = me.holds[s.idx()].max(0) as f64;
        let others = (ec[s.idx()] - me.dealt[s.idx()] as f64).max(0.0) / (n - 1.0);
        let share = (own + 1.0) / (own + 1.0 + others);
        pg[s.idx()] * (GOAL_PAY as f64 + BONUS_GUESS * share)
    }

    /// Bayes over the 12 possible suit-count arrangements, given the cards
    /// player `p` was dealt. Returns P(goal = suit) and E[cards in suit].
    fn posterior(&self, p: usize) -> ([f64; 4], [f64; 4]) {
        let dealt = self.players[p].dealt;
        let mut pg = [0.0; 4];
        let mut ec = [0.0; 4];
        let mut total = 0.0;
        for arr in arrangements() {
            let w: f64 = (0..4).map(|s| choose(arr[s], dealt[s])).product();
            if w == 0.0 {
                continue;
            }
            let twelve = arr.iter().position(|&c| c == 12).unwrap_or(0);
            pg[SUITS[twelve].partner().idx()] += w;
            for s in 0..4 {
                ec[s] += w * arr[s] as f64;
            }
            total += w;
        }
        if total > 0.0 {
            for x in pg.iter_mut().chain(ec.iter_mut()) {
                *x /= total;
            }
        }
        (pg, ec)
    }
}

/// All distinct ways to lay 12, 10, 10, 8 over the four suits.
fn arrangements() -> Vec<[i64; 4]> {
    let mut out = Vec::with_capacity(12);
    for big in 0..4 {
        for eight in 0..4 {
            if eight == big {
                continue;
            }
            let mut c = [10i64; 4];
            c[big] = 12;
            c[eight] = 8;
            out.push(c);
        }
    }
    out
}

/// Binomial coefficient as f64; 0 when k is out of range.
fn choose(n: i64, k: i64) -> f64 {
    if k < 0 || k > n {
        return 0.0;
    }
    (0..k).fold(1.0, |acc, i| acc * (n - i) as f64 / (i + 1) as f64)
}

/// xorshift64. Good enough for shuffles and bot jitter.
#[derive(Debug, Clone)]
struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }

    fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }

    fn unit(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }

    fn shuffle<T>(&mut self, v: &mut [T]) {
        for i in (1..v.len()).rev() {
            let j = self.below(i + 1);
            v.swap(i, j);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn total_bank(g: &Game) -> i64 {
        g.players.iter().map(|p| p.bank).sum()
    }

    #[test]
    fn arrangements_are_the_twelve_deals() {
        let a = arrangements();
        assert_eq!(a.len(), 12);
        for c in &a {
            assert_eq!(c.iter().sum::<i64>(), 40);
            assert_eq!(c.iter().filter(|&&x| x == 12).count(), 1);
            assert_eq!(c.iter().filter(|&&x| x == 8).count(), 1);
        }
    }

    #[test]
    fn deal_and_goal_follow_the_rules() {
        for seed in 1..50 {
            for bots in [3, 4] {
                let g = Game::new(bots, seed);
                let n = bots + 1;
                assert_eq!(g.counts.iter().sum::<i64>(), 40);
                let twelve = g.counts.iter().position(|&c| c == 12).unwrap();
                assert_eq!(g.goal, SUITS[twelve].partner());
                assert!(g.counts[g.goal.idx()] == 8 || g.counts[g.goal.idx()] == 10);
                for s in 0..4 {
                    let dealt: i64 = g.players.iter().map(|p| p.dealt[s]).sum();
                    assert_eq!(dealt, g.counts[s]);
                }
                for p in &g.players {
                    assert_eq!(p.dealt.iter().sum::<i64>(), 40 / n as i64);
                    assert_eq!(p.bank, START_CASH - POT / n as i64);
                }
                assert_eq!(total_bank(&g), n as i64 * START_CASH - POT);
            }
        }
    }

    #[test]
    fn posterior_is_a_distribution_and_points_at_the_goal() {
        let g = Game::new(3, 7);
        for p in 0..g.players.len() {
            let (pg, ec) = g.posterior(p);
            assert!((pg.iter().sum::<f64>() - 1.0).abs() < 1e-9);
            assert!(ec.iter().all(|&e| e > 0.0));
        }
    }

    #[test]
    fn crossing_bid_trades_at_the_resting_offer() {
        let mut g = Game::new(3, 3);
        g.bids = vec![[None; 4]; 4];
        g.offers = vec![[None; 4]; 4];
        g.offers[2][Suit::Clubs.idx()] = Some(10);
        g.bids[3][Suit::Clubs.idx()] = Some(9);
        let (you_before, seller_before) = (g.players[0].bank, g.players[2].bank);
        let holds_before = g.players[0].holds[Suit::Clubs.idx()];
        g.bid(0, Suit::Clubs, 12).unwrap();
        assert_eq!(g.players[0].bank, you_before - 10);
        assert_eq!(g.players[2].bank, seller_before + 10);
        assert_eq!(g.players[0].holds[Suit::Clubs.idx()], holds_before + 1);
        assert!(g.bids.iter().all(|q| q.iter().all(|x| x.is_none())));
        assert!(g.offers.iter().all(|q| q.iter().all(|x| x.is_none())));
    }

    #[test]
    fn bid_above_cash_is_refused() {
        let mut g = Game::new(3, 5);
        let cash = g.players[0].bank;
        assert!(g.bid(0, Suit::Hearts, cash + 1).is_err());
        assert!(g.bids[0][Suit::Hearts.idx()].is_none());
    }

    #[test]
    fn full_round_conserves_cash_and_cards() {
        for seed in 1..40 {
            for bots in [3, 4] {
                let mut g = Game::new(bots, seed);
                let n = bots + 1;
                let mut steps = 0;
                while g.settled.is_none() {
                    g.advance(0.05);
                    steps += 1;
                    assert!(steps < 10_000, "round never settled");
                    for s in 0..4 {
                        let held: i64 = g.players.iter().map(|p| p.holds[s]).sum();
                        assert_eq!(held, g.counts[s], "cards must be conserved");
                    }
                }
                // The pot is paid out in full: total cash returns to n × $350.
                assert_eq!(total_bank(&g), n as i64 * START_CASH);
                let st = g.settled.clone().unwrap();
                let pot_out: i64 = st.goal_pay.iter().sum::<i64>() + st.bonus.iter().sum::<i64>();
                assert_eq!(pot_out, POT);
                assert_eq!(st.goal_cards.iter().sum::<i64>(), g.counts[g.goal.idx()]);
            }
        }
    }

    #[test]
    fn bots_trade_during_a_round() {
        let mut g = Game::new(4, 11);
        let mut t = 0.0;
        while t < ROUND_SECS / 2.0 {
            g.advance(0.1);
            t += 0.1;
        }
        assert!(!g.trades.is_empty(), "no trades in half a round");
    }

    #[test]
    fn next_round_waits_for_settlement() {
        let mut g = Game::new(3, 2);
        assert!(g.next_round().is_err());
        g.advance(ROUND_SECS + 1.0);
        assert!(g.settled.is_some());
        g.next_round().unwrap();
        assert_eq!(g.round, 2);
        assert!(g.settled.is_none());
    }
}
