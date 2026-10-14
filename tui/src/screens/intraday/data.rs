// Per-symbol intraday state: the day's 1-minute bars, aggregated on demand to
// 5m / 15m, plus VWAP and the ET clock labels. Pure data, no I/O: the feed
// (stream.rs) pushes events in, the screen reads aggregated bars out.

use std::collections::BTreeMap;

use crate::ui::hcandles::HBar;

/// One 1-minute bar; `t` is the minute start, epoch seconds.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Bar1 {
    pub t: i64,
    pub o: f64,
    pub h: f64,
    pub l: f64,
    pub c: f64,
    pub v: u64,
}

/// Chart intervals, in minutes.
pub const STEPS: [i64; 3] = [1, 5, 15];

/// 09:30 ET as seconds after midnight, used to recover the UTC offset from
/// the regular-session open Yahoo reports (no tz database needed).
const OPEN_SECS: i64 = 9 * 3600 + 1800;

#[derive(Debug, Default)]
pub struct Series {
    bars: BTreeMap<i64, Bar1>,
    pub prev_close: Option<f64>,
    /// Regular session [open, close), epoch seconds.
    pub reg: Option<(i64, i64)>,
}

impl Series {
    #[cfg(test)]
    pub fn is_empty(&self) -> bool {
        self.bars.is_empty()
    }

    pub fn clear(&mut self) {
        *self = Self::default();
    }

    /// Replace bars with a fresh day from REST. The forming minute may already
    /// hold newer ticks than REST knows about, so it is merged, not replaced.
    pub fn seed(&mut self, prev_close: Option<f64>, reg: Option<(i64, i64)>, bars: &[Bar1]) {
        self.prev_close = prev_close.or(self.prev_close);
        self.reg = reg.or(self.reg);
        for b in bars {
            self.apply(*b);
        }
    }

    /// Insert or update one minute. The latest event wins on close; the range
    /// only widens and volume only grows, so a lagging row can't shrink a live bar.
    pub fn apply(&mut self, b: Bar1) {
        self.bars
            .entry(b.t)
            .and_modify(|old| {
                old.h = old.h.max(b.h);
                old.l = old.l.min(b.l);
                old.v = old.v.max(b.v);
                old.c = b.c;
            })
            .or_insert(b);
    }

    pub fn last_close(&self) -> Option<f64> {
        self.bars.values().next_back().map(|b| b.c)
    }

    /// Seconds to add to epoch to get ET wall-clock, from the session open.
    fn et_offset(&self) -> i64 {
        match self.reg {
            Some((open, _)) => {
                let mut off = (OPEN_SECS - open).rem_euclid(86_400);
                if off > 43_200 {
                    off -= 86_400;
                }
                off
            }
            None => -4 * 3600,
        }
    }

    fn label(&self, t: i64) -> String {
        let s = (t + self.et_offset()).rem_euclid(86_400);
        format!("{:02}:{:02}", s / 3600, s % 3600 / 60)
    }

    fn in_session(&self, t: i64) -> bool {
        self.reg.is_none_or(|(o, c)| (o..c).contains(&t))
    }

    /// Bars at `step` minutes. Without `ext`, only the regular session.
    pub fn aggregate(&self, step: i64, ext: bool) -> Vec<HBar> {
        let width = step * 60;
        let mut out: Vec<(i64, Bar1)> = Vec::new();
        for b in self.bars.values() {
            if !ext && !self.in_session(b.t) {
                continue;
            }
            let bucket = b.t - b.t.rem_euclid(width);
            match out.last_mut() {
                Some((t, a)) if *t == bucket => {
                    a.h = a.h.max(b.h);
                    a.l = a.l.min(b.l);
                    a.c = b.c;
                    a.v += b.v;
                }
                _ => out.push((bucket, Bar1 { t: bucket, ..*b })),
            }
        }
        out.into_iter()
            .map(|(t, b)| HBar {
                label: self.label(t),
                open: b.o,
                high: b.h,
                low: b.l,
                close: b.c,
                volume: b.v,
                ext: !self.in_session(t),
            })
            .collect()
    }

    /// Session VWAP from 1-minute typical price; before the open, over
    /// whatever has traded so far.
    pub fn vwap(&self) -> Option<f64> {
        let regular = self
            .bars
            .values()
            .filter(|b| self.in_session(b.t) && self.reg.is_some());
        let (pv, v) = self.sum_pv(regular);
        if v > 0.0 {
            return Some(pv / v);
        }
        let (pv, v) = self.sum_pv(self.bars.values());
        (v > 0.0).then(|| pv / v)
    }

    fn sum_pv<'a>(&self, bars: impl Iterator<Item = &'a Bar1>) -> (f64, f64) {
        bars.fold((0.0, 0.0), |(pv, v), b| {
            let w = b.v as f64;
            (pv + (b.h + b.l + b.c) / 3.0 * w, v + w)
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // 2026-10-14 09:30 EDT = 13:30 UTC
    const OPEN: i64 = 1_791_984_600;

    fn b(min: i64, o: f64, h: f64, l: f64, c: f64, v: u64) -> Bar1 {
        Bar1 {
            t: OPEN + min * 60,
            o,
            h,
            l,
            c,
            v,
        }
    }

    fn series() -> Series {
        let mut s = Series::default();
        s.reg = Some((OPEN, OPEN + 390 * 60));
        for (i, c) in [10.0, 11.0, 12.0, 11.5, 13.0, 12.5].iter().enumerate() {
            s.apply(b(i as i64, *c - 0.5, *c + 1.0, *c - 1.0, *c, 100));
        }
        s
    }

    #[test]
    fn labels_use_et_derived_from_the_session_open() {
        let s = series();
        assert_eq!(s.label(OPEN), "09:30");
        assert_eq!(s.label(OPEN + 61 * 60), "10:31");
        // standard time (EST): the open is 14:30 UTC and still reads 09:30
        let mut w = Series::default();
        w.reg = Some((1_800_000_000 - 1_800_000_000 % 86_400 + 14 * 3600 + 1800, 0));
        assert_eq!(w.label(w.reg.unwrap().0), "09:30");
    }

    #[test]
    fn aggregates_to_five_minutes() {
        let s = series();
        let one = s.aggregate(1, false);
        assert_eq!(one.len(), 6);
        let five = s.aggregate(5, false);
        assert_eq!(five.len(), 2);
        let first = &five[0];
        assert_eq!(first.label, "09:30");
        assert_eq!(first.open, 9.5); // first bar's open
        assert_eq!(first.close, 13.0); // fifth bar's close
        assert_eq!(first.high, 14.0);
        assert_eq!(first.low, 9.0);
        assert_eq!(first.volume, 500);
        assert_eq!(five[1].volume, 100);
    }

    #[test]
    fn extended_hours_are_filtered_and_flagged() {
        let mut s = series();
        s.apply(b(-30, 9.0, 9.5, 8.5, 9.2, 50)); // 09:00 pre-market
        assert_eq!(s.aggregate(1, false).len(), 6);
        let all = s.aggregate(1, true);
        assert_eq!(all.len(), 7);
        assert!(all[0].ext && !all[1].ext);
    }

    #[test]
    fn apply_keeps_the_wider_range_and_larger_volume() {
        let mut s = series();
        s.apply(b(5, 12.0, 12.2, 12.1, 12.1, 40)); // stale REST row for the last minute
        let last = s.aggregate(1, false).pop().unwrap();
        assert_eq!(last.high, 13.5);
        assert_eq!(last.low, 11.5);
        assert_eq!(last.volume, 100);
    }

    #[test]
    fn vwap_weights_by_volume() {
        let mut s = Series::default();
        s.reg = Some((OPEN, OPEN + 390 * 60));
        s.apply(b(0, 10.0, 10.0, 10.0, 10.0, 100));
        s.apply(b(1, 20.0, 20.0, 20.0, 20.0, 300));
        assert_eq!(s.vwap(), Some(17.5));
        assert_eq!(Series::default().vwap(), None);
    }
}
