// INGOT section 7: who makes the wafers, drawn as share bars.
//
//   Shares    the five makers' 2024 shares (Report Prime estimate), one bar each
//   Stack     the same five stacked against the whole large-wafer market, rest left as dots
//   Omdia     the 2020 Omdia shares for the three makers the article names, plus the group totals
//   Basis     the 2020 and 2024 five-firm totals side by side, and why the two sources differ
//
// Sources, read as HTML pages (no PDF figure was found for these shares):
//   Report Prime 2024 ranking table: https://www.reportprime.com/large-semiconductor-wafers-r3643/company
//     (its methodology note: 70% quantitative, 30% qualitative weighting)
//   Omdia 2020 shares, via KED Global: https://www.kedglobal.com/newsView/ked202203160007
// Every share is the number the sources print. The 68.5% five-firm total and the 31.5% rest are
// computed here from the five 2024 shares; neither is printed by a source.

use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

/// Cells per percentage point for single bars, and for the stacked bar (half a cell per point).
const SCALE: f32 = 2.0;
const STACK: f32 = 0.5;
/// Column where bars start, first bar row, and rows between bars.
const BAR_X: i32 = 16;
const ROW0: i32 = 4;
const ROW_H: i32 = 3;
/// Glyphs for the five makers in the stacked bar, and for the rest of the market.
const FILLS: [char; 5] = ['█', '▓', '▒', '░', '▪'];
const REST: char = '·';

/// Report Prime 2024 shares, percent, in ranking order.
const SHARE_2024: &[(&str, f32)] = &[
    ("Shin-Etsu", 19.9),
    ("SUMCO", 17.2),
    ("GlobalWafers", 12.9),
    ("Siltronic", 9.9),
    ("SK Siltron", 8.6),
];
/// Omdia 2020 shares, percent, for the three makers the article names one by one.
const SHARE_2020: &[(&str, f32)] = &[
    ("GlobalWafers", 16.7),
    ("Siltronic", 12.3),
    ("SK Siltron", 10.6),
];
/// Five-firm totals from the two sources, percent. The 2024 total is the sum of SHARE_2024.
const FIVE_2020: f32 = 94.0;
const FIVE_2024: f32 = 68.5;
/// Width of the whole market in stacked-bar cells.
const TOTAL_CELLS: i32 = 50;

fn rows(c: &Canvas) -> i32 {
    c.height().max(MIN_H as usize) as i32
}

/// Eased growth of bar `k` within a beat: each bar starts a little after the one above it.
fn grow(t: &Time, k: usize, span: f32) -> f32 {
    ease_in_out(((t.local - 0.12 * k as f32) / span).clamp(0.0, 1.0))
}

/// One labelled bar at row `y`, `f` of the way grown; the value shows once it is full.
fn bar_row(c: &mut Canvas, y: i32, name: &str, pct: f32, glyph: char, scale: f32, f: f32) {
    c.text(2, y, name);
    let len = (pct * scale * f).round() as i32;
    c.hline(BAR_X, y, len, glyph);
    if f >= 0.99 {
        c.label(BAR_X + len + 1, y, &format!("{pct:.1}%"));
    }
}

/// The five 2024 shares as one bar, drawn left to right; `f` is how much of the bar is shown.
fn stacked(c: &mut Canvas, y: i32, f: f32) {
    let vis = (TOTAL_CELLS as f32 * f).round() as i32;
    let mut cum = 0.0f32;
    for (i, (_, pct)) in SHARE_2024.iter().enumerate() {
        let a = (cum * STACK).round() as i32;
        cum += pct;
        let b = (cum * STACK).round() as i32;
        for x in a..b.min(vis) {
            c.put(BAR_X + x, y, FILLS[i]);
        }
    }
    let a = (cum * STACK).round() as i32;
    for x in a..TOTAL_CELLS.min(vis) {
        c.put(BAR_X + x, y, REST);
    }
}

pub struct Section;

const BEATS: &[Beat] = &[
    Beat::new(
        "five makers, Shin-Etsu 19.9% and SUMCO 17.2% first, in the 2024 estimate",
        BEAT_MS,
    )
    .note(
        "Each bar is one maker's share of large silicon wafers in 2024. Shin-Etsu leads, then SUMCO; the rest are lower.",
        "Five bars growing in ranking order, each one with its percentage at the end.",
    )
    .detail(
        "The ranking is the point here: Shin-Etsu and SUMCO are first, and that order holds across the sources on this page.",
        &[
            "Report Prime 2024 shares: Shin-Etsu 19.9%, SUMCO 17.2%, GlobalWafers 12.9%",
            "Report Prime 2024 shares: Siltronic 9.9%, SK Siltron 8.6%",
            "Report Prime is an estimate, a ranking table on a web page, not a filing",
        ],
    ),
    Beat::new(
        "stacked against the whole market, the five come to 68.5%; the rest is 31.5%",
        BEAT_MS,
    )
    .note(
        "The same five shares laid end to end make one bar for the whole market. The dotted end is every maker not on the list.",
        "A stacked bar filling left to right, each maker a different glyph, then the dotted rest.",
    )
    .detail(
        "The five listed here add up to 68.5% of the 2024 estimate. The 31.5% rest is what that leaves, and the page does not name it.",
        &[
            "68.5% is the sum of the five 2024 shares (computed here, not printed)",
            "31.5% is 100 minus 68.5 (computed here, not printed)",
            "The page's other sources put the five at 82-94% (page text)",
        ],
    ),
    Beat::new(
        "Omdia 2020: GlobalWafers 16.7%, Siltronic 12.3%, and five players hold 94%",
        BEAT_MS,
    )
    .note(
        "An older set of shares, from Omdia in 2020, names three makers one by one and gives two group totals.",
        "Three bars in a lighter fill, then the two group totals written underneath them.",
    )
    .detail(
        "These are 2020 numbers on a different basis from the 2024 estimate. They are the page's higher end for the five-firm total.",
        &[
            "Omdia 2020 via KED Global: GlobalWafers 16.7%, Siltronic 12.3%, SK Siltron 10.6%",
            "Shin-Etsu and SUMCO together: more than 55% (Omdia 2020)",
            "Five players: 94% of an $11.2B market, 2020 (KED Global)",
        ],
    ),
    Beat::new(
        "the 2020 and 2024 five-firm totals side by side: 94% against 68.5%",
        BEAT_MS,
    )
    .note(
        "Two totals on one scale: the 2020 five-firm share and the 2024 sum of the five. They come from different sources and bases.",
        "Two bars, the top one long and the lower one shorter, each labelled with its year.",
    )
    .detail(
        "The two totals are not a trend. One is a 2020 market count, the other a 2024 estimate built on a different weighting.",
        &[
            "2020 five-firm total 94% (Omdia via KED Global)",
            "2024 five-firm total 68.5% (sum of the Report Prime shares, computed here)",
            "Report Prime weights 70% quantitative and 30% qualitative factors (its page)",
        ],
    ),
];

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let h = rows(c);
        match t.beat {
            0 => {
                c.text(2, 1, "share of large wafers, 2024 (Report Prime)");
                for (k, (name, pct)) in SHARE_2024.iter().enumerate() {
                    let y = ROW0 + k as i32 * ROW_H;
                    bar_row(c, y, name, *pct, '█', SCALE, grow(t, k, 0.6));
                }
                c.text(2, h - 2, "estimate, low reliability: one aggregator, not a filing");
            }
            1 => {
                c.text(2, 1, "the whole large-wafer market, stacked by maker");
                let f = ease_in_out(t.local.clamp(0.0, 1.0));
                stacked(c, ROW0 + 1, f);
                for (i, (name, pct)) in SHARE_2024.iter().enumerate() {
                    let y = ROW0 + 4 + i as i32;
                    c.put(2, y, FILLS[i]);
                    c.text(4, y, &format!("{name} {pct:.1}%"));
                }
                c.put(2, ROW0 + 9, REST);
                c.text(4, ROW0 + 9, &format!("not on the list {:.1}%", 100.0 - FIVE_2024));
                if t.local > 0.6 {
                    c.text(2, ROW0 + 11, &format!("five listed together: {FIVE_2024:.1}%"));
                }
                c.text(2, h - 2, "bar = whole market; the dotted rest is the remainder");
            }
            2 => {
                c.text(2, 1, "Omdia 2020 shares, via KED Global");
                for (k, (name, pct)) in SHARE_2020.iter().enumerate() {
                    let y = ROW0 + k as i32 * ROW_H;
                    bar_row(c, y, name, *pct, '▒', SCALE, grow(t, k, 0.6));
                }
                c.text(2, 14, "Shin-Etsu + SUMCO together: more than 55%");
                c.text(2, 16, "five players: 94% of an $11.2B market");
                c.text(2, h - 2, "the article names only these three makers' shares");
            }
            _ => {
                c.text(2, 1, "five-firm totals, two sources");
                bar_row(c, ROW0, "2020 Omdia", FIVE_2020, '▒', STACK, grow(t, 0, 0.6));
                bar_row(c, ROW0 + ROW_H, "2024 est", FIVE_2024, '█', STACK, grow(t, 1, 0.6));
                c.text(2, 12, "2020: five firms in an $11.2B market (Omdia)");
                c.text(2, 14, "2024: a Report Prime ranking estimate, not a filing");
                c.text(2, 16, "its weights: 70% quantitative, 30% qualitative");
                c.text(2, h - 2, "compare the totals only with their year and basis");
            }
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Section)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn time(beat: usize, local: f32) -> Time {
        Time {
            ms: beat as u64 * BEAT_MS + (local * BEAT_MS as f32) as u64,
            beat,
            local,
            beat_start: beat as u64 * BEAT_MS,
        }
    }

    fn at(beat: usize, local: f32, w: usize, h: usize) -> String {
        let mut c = Canvas::new(w as u16, h as u16);
        Section.draw(&mut c, &time(beat, local));
        c.lines().join("\n")
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        let s = build();
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.caption.is_empty()
                    && !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty()
                    && b.facts.iter().all(|f| !f.is_empty()),
                "beat {i}"
            );
        }
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            for beat in 0..BEATS.len() {
                for local in [0.0, 0.5, 0.99] {
                    let mut c = Canvas::new(w, h);
                    Section.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn shares_add_up_as_stated() {
        let sum: f32 = SHARE_2024.iter().map(|(_, p)| p).sum();
        assert!((sum - FIVE_2024).abs() < 0.05);
        assert!((100.0 - FIVE_2024 - 31.5).abs() < 0.05);
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.9, 80, 26).contains("19.9%"));
        assert!(at(1, 0.9, 80, 26).contains("68.5%"));
        assert!(at(2, 0.9, 80, 26).contains("16.7%"));
        assert!(at(3, 0.9, 80, 26).contains("94.0%"));
    }
}
