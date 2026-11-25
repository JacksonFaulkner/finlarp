// Where `{` and `}` stop on an intraday chart: the bars worth a look. Two kinds, merged into
// one sorted list (a bar that is both is one stop with both tags):
//
//   volume spike   volume >= SPIKE_X times the session's typical bar (the median of the bars
//                  that traded at all, so minutes with no volume reported don't drag it to 0)
//                  and the biggest within SPIKE_RADIUS bars, so one surge is one stop
//   swing high/low the highest high / lowest low within SWING_RADIUS bars on each side: the
//                  turns in the line. Bars near either end only need what exists on their side.

use crate::ui::hcandles::HBar;

const SPIKE_X: f64 = 2.5;
const SPIKE_RADIUS: usize = 2;
const SWING_RADIUS: usize = 3;

/// What makes a bar a stop.
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Stop {
    pub idx: usize,
    pub swing_high: bool,
    pub swing_low: bool,
    /// Volume as a multiple of the typical bar, when it is a spike.
    pub spike: Option<f64>,
}

impl Stop {
    /// Readout tag: "swing high · vol 3.1×".
    pub fn label(&self) -> String {
        let mut parts = Vec::new();
        if self.swing_high {
            parts.push("swing high".to_string());
        }
        if self.swing_low {
            parts.push("swing low".to_string());
        }
        if let Some(x) = self.spike {
            parts.push(format!("vol {x:.1}×"));
        }
        parts.join(" · ")
    }
}

fn window(i: usize, r: usize, n: usize) -> std::ops::Range<usize> {
    i.saturating_sub(r)..(i + r + 1).min(n)
}

/// Every stop in `bars`, oldest first.
pub fn stops(bars: &[HBar]) -> Vec<Stop> {
    let n = bars.len();
    let mut traded: Vec<u64> = bars.iter().map(|b| b.volume).filter(|&v| v > 0).collect();
    traded.sort_unstable();
    let typical = traded.get(traded.len() / 2).copied().unwrap_or(0) as f64;
    let mut out = Vec::new();
    for (i, b) in bars.iter().enumerate() {
        let w = window(i, SWING_RADIUS, n);
        // ties go to the first bar of a flat top, so a plateau is one stop
        let swing_high = n > 2
            && bars[w.clone()]
                .iter()
                .enumerate()
                .all(|(k, o)| o.high < b.high || (o.high == b.high && w.start + k >= i));
        let swing_low = n > 2
            && bars[w.clone()]
                .iter()
                .enumerate()
                .all(|(k, o)| o.low > b.low || (o.low == b.low && w.start + k >= i));
        let spike = (typical > 0.0 && b.volume as f64 >= SPIKE_X * typical)
            .then(|| {
                let w = window(i, SPIKE_RADIUS, n);
                bars[w.clone()]
                    .iter()
                    .enumerate()
                    .all(|(k, o)| o.volume < b.volume || (o.volume == b.volume && w.start + k >= i))
                    .then_some(b.volume as f64 / typical)
            })
            .flatten();
        if swing_high || swing_low || spike.is_some() {
            out.push(Stop {
                idx: i,
                swing_high,
                swing_low,
                spike,
            });
        }
    }
    out
}

/// The stop `times` stops after (forward) or before `from`, or the last one there is.
pub fn step(stops: &[Stop], from: usize, forward: bool, times: usize) -> Option<usize> {
    let ahead: Vec<usize> = if forward {
        stops.iter().map(|s| s.idx).filter(|&i| i > from).collect()
    } else {
        stops
            .iter()
            .rev()
            .map(|s| s.idx)
            .filter(|&i| i < from)
            .collect()
    };
    ahead
        .get(times.max(1) - 1)
        .or_else(|| ahead.last())
        .copied()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::hcandles::Session;

    fn bar(high: f64, low: f64, volume: u64) -> HBar {
        HBar {
            label: String::new(),
            open: (high + low) / 2.0,
            high,
            low,
            close: (high + low) / 2.0,
            volume,
            session: Session::Regular,
        }
    }

    /// Up to a top at 4, down to a bottom at 9, up again; one volume surge at 6.
    fn day() -> Vec<HBar> {
        let highs = [
            10.0, 11.0, 12.0, 13.0, 14.0, 13.0, 12.0, 11.0, 10.0, 9.0, 10.0, 11.0, 12.0, 13.0,
        ];
        highs
            .iter()
            .enumerate()
            .map(|(i, &h)| bar(h, h - 1.0, if i == 6 { 5000 } else { 1000 }))
            .collect()
    }

    #[test]
    fn finds_the_turns_and_the_surge() {
        let s = stops(&day());
        let at = |i: usize| s.iter().find(|x| x.idx == i).copied().unwrap_or_default();
        assert!(at(4).swing_high, "{s:?}");
        assert!(at(9).swing_low, "{s:?}");
        assert_eq!(at(6).spike, Some(5.0));
        assert_eq!(at(4).label(), "swing high");
        assert_eq!(at(6).label(), "vol 5.0×");
    }

    #[test]
    fn zero_volume_minutes_do_not_make_everything_a_spike() {
        let mut d = day();
        for b in d.iter_mut().skip(1).step_by(2) {
            b.volume = 0;
        }
        let s = stops(&d);
        let spikes: Vec<usize> = s
            .iter()
            .filter(|x| x.spike.is_some())
            .map(|x| x.idx)
            .collect();
        assert_eq!(spikes, [6]);
    }

    #[test]
    fn step_moves_by_stops_and_stops_at_the_last() {
        let s = stops(&day());
        let idx: Vec<usize> = s.iter().map(|x| x.idx).collect();
        let first = idx[0];
        assert_eq!(step(&s, first, true, 1), Some(idx[1]));
        assert_eq!(step(&s, first, true, 2), Some(idx[2]));
        assert_eq!(step(&s, idx[2], false, 1), Some(idx[1]));
        assert_eq!(
            step(&s, first, true, 99),
            idx.last().copied(),
            "a big count lands on the last"
        );
        assert_eq!(step(&s, first, false, 1), None, "nothing before the first");
    }
}
