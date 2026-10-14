// Deterministic mock OHLCV bars until the chart reads bars_1d. Each bar is
// aggregated from a geometric-Brownian-motion tick path, so open == previous
// close, high/low bracket the ticks, and volume scales with |return|. The
// whole series is rescaled so the last close equals `end_price`.

use chrono::{Datelike, NaiveDate, Weekday};

use crate::model::Candle;

const TICKS_PER_BAR: usize = 30;

/// xorshift64*: tiny, seedable, no dependency.
struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    /// Uniform in (0, 1).
    fn unit(&mut self) -> f64 {
        ((self.next_u64() >> 11) as f64 + 0.5) / (1u64 << 53) as f64
    }

    /// Standard normal (Box-Muller).
    fn gauss(&mut self) -> f64 {
        let (u, v) = (self.unit(), self.unit());
        (-2.0 * u.ln()).sqrt() * (std::f64::consts::TAU * v).cos()
    }
}

/// FNV-1a, so a ticker always gets the same series.
pub fn seed_for(ticker: &str) -> u64 {
    ticker.bytes().fold(0xcbf2_9ce4_8422_2325, |h, b| {
        (h ^ b as u64).wrapping_mul(0x100_0000_01b3)
    }) | 1
}

/// `n` daily bars on consecutive weekdays ending on or before `end_date`.
/// `daily_vol` is the std-dev of the daily log return (0.045 ~ small-cap biotech).
pub fn candles(
    seed: u64,
    n: usize,
    end_price: f64,
    daily_vol: f64,
    end_date: NaiveDate,
) -> Vec<Candle> {
    if n == 0 {
        return Vec::new();
    }
    let mut rng = Rng(seed | 1);
    let step = daily_vol / (TICKS_PER_BAR as f64).sqrt();
    let mut price = 100.0_f64;
    let mut raw = Vec::with_capacity(n);
    for _ in 0..n {
        let open = price;
        let (mut high, mut low) = (open, open);
        for _ in 0..TICKS_PER_BAR {
            price *= (rng.gauss() * step).exp();
            high = high.max(price);
            low = low.min(price);
        }
        let ret = (price / open).ln().abs();
        let volume = (200_000.0 * (0.5 + rng.unit()) * (1.0 + ret / daily_vol * 2.0)) as u64;
        raw.push((open, high, low, price, volume));
    }
    let k = end_price / raw[n - 1].3;
    let dates = weekdays_ending(end_date, n);
    raw.into_iter()
        .zip(dates)
        .map(|((o, h, l, c, volume), d)| Candle {
            date: d.format("%Y-%m-%d").to_string(),
            open: o * k,
            high: h * k,
            low: l * k,
            close: c * k,
            volume,
        })
        .collect()
}

fn weekdays_ending(end: NaiveDate, n: usize) -> Vec<NaiveDate> {
    let mut out = Vec::with_capacity(n);
    let mut d = end;
    while out.len() < n {
        if !matches!(d.weekday(), Weekday::Sat | Weekday::Sun) {
            out.push(d);
        }
        d = d.pred_opt().unwrap_or(d);
    }
    out.reverse();
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn end() -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, 10, 14).unwrap()
    }

    #[test]
    fn deterministic_per_seed() {
        let a = candles(seed_for("SPRB"), 60, 39.26, 0.045, end());
        let b = candles(seed_for("SPRB"), 60, 39.26, 0.045, end());
        let c = candles(seed_for("MRVL"), 60, 39.26, 0.045, end());
        assert_eq!(a, b);
        assert_ne!(a, c);
    }

    #[test]
    fn bars_are_well_formed() {
        for c in candles(seed_for("SPRB"), 200, 39.26, 0.045, end()) {
            assert!(c.low <= c.open.min(c.close) + 1e-9, "{c:?}");
            assert!(c.high >= c.open.max(c.close) - 1e-9, "{c:?}");
            assert!(c.low > 0.0 && c.volume > 0);
        }
    }

    #[test]
    fn continuous_and_ends_at_target() {
        let v = candles(seed_for("SPRB"), 100, 39.26, 0.045, end());
        for w in v.windows(2) {
            assert!((w[1].open - w[0].close).abs() < 1e-9);
        }
        assert!((v[99].close - 39.26).abs() < 1e-9);
    }

    #[test]
    fn dates_are_weekdays_ending_on_end() {
        let v = candles(1, 10, 10.0, 0.03, end()); // Wed 2026-10-14
        assert_eq!(v[9].date, "2026-10-14");
        assert_eq!(v[5].date, "2026-10-08");
        assert!(v.iter().all(|c| {
            let d = NaiveDate::parse_from_str(&c.date, "%Y-%m-%d").unwrap();
            !matches!(d.weekday(), Weekday::Sat | Weekday::Sun)
        }));
    }

    #[test]
    fn empty_ok() {
        assert!(candles(1, 0, 10.0, 0.03, end()).is_empty());
    }
}
