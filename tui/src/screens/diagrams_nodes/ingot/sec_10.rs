// INGOT section 10 (Sources): the page's eight-item source list [1]-[8] as a checklist.
//
// Each numbered source is a card, in the page's list order. A group's cards light up in turn
// (blinking while named, then checked off), and the bar at the bottom counts the checks.
// The sources are the page's own list; the figures were not re-read from them in this pass.
//
// Sources (the page's list, INGOT.txt):
//   [1] https://en.wikipedia.org/wiki/Wafer_(electronics)
//   [2] https://en.wikipedia.org/wiki/Czochralski_method
//   [3] https://www.universitywafer.com/300mm-silicon-wafers.html
//   [4] https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12617032
//       https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12605863
//   [5] https://www.reportprime.com/large-semiconductor-wafers-r3643/company
//   [6] https://kedglobal.com/newsView/ked202203160007
//   [7] https://marklapedus.substack.com/p/silicon-wafer-market-upturn-higher
//   [8] https://store-us.semi.org/products/m00100-semi-m1-specification-for-polished-single-crystal-silicon-wafers

use crate::ui::anim::{Beat, Canvas, Scene, Time, flicker};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Grid geometry: first card row, rows of cards, card height in rows.
const GRID_Y: i32 = 3;
const ROW_H: i32 = 5;
const CARD_H: i32 = 4;
/// Share of each beat spent checking; the rest is a pause on the finished group.
const CHECK_START: f32 = 0.1;
const CHECK_SPAN: f32 = 0.8;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// One numbered entry of the Sources list, as shown on its card.
struct Source {
    title: &'static str,
    line: &'static str,
}

/// Cards in the page's list order, two per row, so each group is a contiguous run.
const SOURCES: &[Source] = &[
    Source {
        title: "[1] Wikipedia",
        line: "Wafer (electronics) table",
    },
    Source {
        title: "[2] Wikipedia",
        line: "Czochralski method",
    },
    Source {
        title: "[3] University Wafer",
        line: "300 mm sheet",
    },
    Source {
        title: "[4] USPTO patents",
        line: "crop, grind, notch, saw",
    },
    Source {
        title: "[5] Reportprime",
        line: "large wafer shares",
    },
    Source {
        title: "[6] Omdia 2020",
        line: "via KED Global",
    },
    Source {
        title: "[7] SEMI 2023 data",
        line: "LTA pricing, substack",
    },
    Source {
        title: "[8] SEMI M1",
        line: "polished wafer spec",
    },
];

/// Beat groups: label, then the [start, end) run of SOURCES it covers.
const GROUPS: &[(&str, usize, usize)] = &[
    ("general reference", 0, 2),
    ("dimensions and process", 2, 4),
    ("market data", 4, 7),
    ("SEMI specification", 7, 8),
];

const BEATS: &[Beat] = &[
    Beat::new(
        "general reference: the wafer standards table and the Czochralski entry, both Wikipedia",
        BEAT_MS,
    )
    .note(
        "Cards [1] and [2] are the reference entries: the Wikipedia wafer standards table and the Wikipedia page on the Czochralski method.",
        "Cards [1] and [2] light up in turn, each one checked off once named.",
    )
    .detail(
        "The thickness ladder and the mass and die tables on the page are read from the standards table in [1].",
        &[
            "[1] en.wikipedia.org/wiki/Wafer_(electronics)",
            "[2] en.wikipedia.org/wiki/Czochralski_method",
        ],
    ),
    Beat::new(
        "dimensions and process: the 300 mm sheet and the USPTO patent steps",
        BEAT_MS,
    )
    .note(
        "Cards [3] and [4] cover the physical side: a vendor sheet for 300 mm diameter and notch, and the USPTO patent texts for the crop, grind, notch and saw steps.",
        "Cards [3] and [4] light up in turn, each one checked off once named.",
    )
    .detail(
        "The diameter and notch come from [3]; the process steps come from the two patent texts named in [4].",
        &[
            "[3] universitywafer.com/300mm-silicon-wafers.html",
            "[4] US patents 12617032 and 12605863 (print/downloadPdf)",
        ],
    ),
    Beat::new(
        "market data: wafer shares, Omdia 2020 shares, and SEMI 2023 pricing",
        BEAT_MS,
    )
    .note(
        "Cards [5], [6] and [7] are the market sources: Report Prime's share estimate, Omdia's 2020 shares via KED Global, and SEMI 2023 data with Shin-Etsu's long-term agreement pricing.",
        "Cards [5], [6] and [7] light up in turn, and the bar at the bottom reaches seven of eight.",
    )
    .detail(
        "These are market figures from different years, so they should not be read as one period. Report Prime is marked low-reliability on the page.",
        &[
            "[5] reportprime.com/large-semiconductor-wafers-r3643/company",
            "[6] kedglobal.com/newsView/ked202203160007",
            "[7] marklapedus.substack.com/p/silicon-wafer-market-upturn-higher",
        ],
    ),
    Beat::new(
        "SEMI specification: the M1 listing for polished single-crystal silicon wafers",
        BEAT_MS,
    )
    .note(
        "Card [8] is the SEMI M1 specification for polished single-crystal silicon wafers. It is the last source, and once it is checked off every source on the page has been named.",
        "Card [8] lights up, then the bar fills to all eight.",
    )
    .detail(
        "The page cites M1 as a SEMI listing for polished wafers. The listing was not opened in this pass, so the spec's contents are not stated here.",
        &["[8] store-us.semi.org/products/m00100-semi-m1-specification-for-polished-single-crystal-silicon-wafers"],
    ),
];

#[derive(Clone, Copy, PartialEq)]
enum State {
    Idle,
    Active,
    Checked,
}

/// Where card `i` stands at this moment of the current beat.
fn state_of(i: usize, t: &Time) -> State {
    let (start, end) = match GROUPS.get(t.beat) {
        Some(&(_, s, e)) => (s, e),
        None => return State::Checked,
    };
    if i < start {
        return State::Checked;
    }
    if i >= end || t.local < CHECK_START {
        return State::Idle;
    }
    // the group's cards are named one after another across the check span
    let p = ((t.local - CHECK_START) / CHECK_SPAN).clamp(0.0, 1.0);
    let step = p * (end - start) as f32;
    let k = (i - start) as f32;
    if step < k {
        State::Idle
    } else if step < k + 1.0 {
        State::Active
    } else {
        State::Checked
    }
}

fn fit(s: &str, n: i32) -> String {
    s.chars().take(n.max(0) as usize).collect()
}

/// One card. Idle is a light border, active a double border with a marker, checked a heavy border and a tick.
fn card(c: &mut Canvas, x: i32, y: i32, w: i32, src: &Source, state: State, t: &Time) {
    let (tl, tr, bl, br, hz, vt) = match state {
        State::Idle => ('┌', '┐', '└', '┘', '─', '│'),
        State::Active => ('╔', '╗', '╚', '╝', '═', '║'),
        State::Checked => ('┏', '┓', '┗', '┛', '━', '┃'),
    };
    c.hline(x + 1, y, w - 2, hz);
    c.hline(x + 1, y + CARD_H - 1, w - 2, hz);
    c.vline(x, y + 1, CARD_H - 2, vt);
    c.vline(x + w - 1, y + 1, CARD_H - 2, vt);
    c.put(x, y, tl);
    c.put(x + w - 1, y, tr);
    c.put(x, y + CARD_H - 1, bl);
    c.put(x + w - 1, y + CARD_H - 1, br);
    c.text(x + 2, y + 1, &fit(src.title, w - 4));
    c.text(x + 2, y + 2, &fit(src.line, w - 4));
    match state {
        State::Active => {
            if flicker(t.ms, 300, 4, 2) != 0 {
                c.put(x - 2, y + 1, '▸');
            }
        }
        State::Checked => c.put(x + w - 3, y, '✓'),
        State::Idle => {}
    }
}

pub struct Section;

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cw = ((w - 8) / 2).clamp(24, 44);
        let cols = [2, w - 2 - cw];
        let mut checked = 0;
        for (i, src) in SOURCES.iter().enumerate() {
            let state = state_of(i, t);
            if state == State::Checked {
                checked += 1;
            }
            let x = cols[i % 2];
            let y = GRID_Y + (i as i32 / 2) * ROW_H;
            card(c, x, y, cw, src, state, t);
        }
        let group = GROUPS.get(t.beat).map_or("all sources", |g| g.0);
        c.text(2, 1, &format!("checking: {group}"));
        // progress bar: one step per checked source
        let total = SOURCES.len() as i32;
        let bar = 40;
        let filled = checked * bar / total;
        c.text(2, h - 2, &format!("checked {checked} of {total}"));
        c.hline(22, h - 2, filled, '█');
        c.hline(22 + filled, h - 2, bar - filled, '░');
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Section)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn beats_are_captioned_and_grouped() {
        let s = build();
        assert!(s.beats().len() >= 3);
        assert_eq!(s.beats().len(), GROUPS.len());
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
        // groups cover every source once, in order
        let mut next = 0;
        for &(_, start, end) in GROUPS {
            assert_eq!(start, next);
            assert!(end > start);
            next = end;
        }
        assert_eq!(next, SOURCES.len());
    }

    #[test]
    fn draws_at_sizes_and_times_without_panicking() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(build(), Instant::now());
            p.fit(w, h);
            for ms in [0, BEAT_MS / 2, 3 * BEAT_MS + BEAT_MS - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }

    #[test]
    fn cards_light_up_and_check_off() {
        let mut p = Player::new(build(), Instant::now());
        p.fit(120, 38);
        assert!(at(&mut p, 0, 0.5).contains("checking: general reference"));
        assert!(at(&mut p, 0, 0.5).contains("[1] Wikipedia"));
        assert!(at(&mut p, 1, 0.5).contains("[4] USPTO patents"));
        assert!(at(&mut p, 2, 0.9).contains("[7] SEMI 2023 data"));
        // the last beat ends with every source checked off
        let last = at(&mut p, 3, 0.99);
        assert_eq!(last.matches('✓').count(), SOURCES.len());
        assert!(last.contains("checked 8 of 8"));
        // the first beat has checked nothing yet
        assert_eq!(at(&mut p, 0, 0.05).matches('✓').count(), 0);
    }
}
