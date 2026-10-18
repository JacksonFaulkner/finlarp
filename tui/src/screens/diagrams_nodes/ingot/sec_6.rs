// INGOT section 6: mass per wafer and dies per wafer for 100, 200, 300 and 450 mm, as bars.
//
//   Mass   grams per wafer grow with diameter: 10, 53, 125, 342
//   Dies   ideal dies per wafer grow the same way: 56, 269, 640, 1490
//   450    proposed for 2018 and stopped in 2016; drawn hatched as a cancelled size
//
// Numbers are the page's table (section 6, "same table" as section 5). They are taken from the
// page text, not re-read from the source in this pass. The 100 mm2 die size behind the die counts
// is from INGOT.details.txt, not from the table.
// Sources: https://en.wikipedia.org/wiki/Wafer_(electronics)

use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, flicker};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Columns for the largest bar in each block, and the column the bars start at.
const BAR_MAX: i32 = 40;
const BAR_X: i32 = 12;
/// Header row of the mass block and of the dies block; size rows follow each header.
const MASS_Y: i32 = 3;
const DIES_Y: i32 = 9;
/// Share of a beat spent growing the bars it animates; the rest holds the finished bars.
const GROW: f32 = 0.6;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// One wafer diameter from the page table.
struct Size {
    name: &'static str,
    grams: i32,
    dies: i32,
    /// Proposed, then stopped: drawn with a hatched bar.
    cancelled: bool,
}

const SIZES: &[Size] = &[
    Size {
        name: "100 mm",
        grams: 10,
        dies: 56,
        cancelled: false,
    },
    Size {
        name: "200 mm",
        grams: 53,
        dies: 269,
        cancelled: false,
    },
    Size {
        name: "300 mm",
        grams: 125,
        dies: 640,
        cancelled: false,
    },
    Size {
        name: "450 mm",
        grams: 342,
        dies: 1490,
        cancelled: true,
    },
];

const BEATS: &[Beat] = &[
    Beat::new(
        "mass per wafer: 10 g at 100 mm, rising to 342 g at 450 mm",
        BEAT_MS,
    )
    .note(
        "The top block is grams per wafer for each diameter. Each bar grows from the left to its value, so the step from 200 mm to 300 mm reads as the jump it is.",
        "The mass bars grow in turn; the dies block is still empty.",
    )
    .detail(
        "Wafer mass rises with area, so each step up in diameter adds a lot of silicon to every wafer.",
        &[
            "100 mm: 10 g, 200 mm: 53 g, 300 mm: 125 g, 450 mm: 342 g (page table)",
            "Table source: Wikipedia wafer standards, the same table as section 5",
        ],
    ),
    Beat::new(
        "dies per wafer: 56 at 100 mm, rising to 1490 at 450 mm",
        BEAT_MS,
    )
    .note(
        "The lower block is ideal dies per wafer. Read it against the mass bars: the die count climbs with diameter in the same order.",
        "The mass bars hold; the dies bars grow in turn beneath them.",
    )
    .detail(
        "The die count is an ideal count, from the wafer area and an assumed die size, not a yield figure.",
        &[
            "100 mm: 56, 200 mm: 269, 300 mm: 640, 450 mm: 1490 dies (page table)",
            "Die size behind the count: 100 mm2, from INGOT.details.txt (not in the table)",
        ],
    ),
    Beat::new(
        "the 300 mm wafer: 125 g and 640 dies, the size the industry settled on",
        BEAT_MS,
    )
    .note(
        "Both blocks are full. The 300 mm row is marked as the standard: 125 g and 640 dies, the size the page treats as the working one.",
        "The 300 mm row carries a marker; every other row holds its bar.",
    )
    .detail(
        "The standard is the size the page's supply and market figures refer to, so this row is the working reference.",
        &[
            "300 mm: 125 g and 640 dies per wafer (page table)",
            "The 300 mm standard has lasted 25+ years (INGOT.details.txt)",
        ],
    ),
    Beat::new(
        "450 mm: 342 g and 1490 dies, but the size was cancelled",
        BEAT_MS,
    )
    .note(
        "The 450 mm row is hatched. It was proposed for 2018 and stopped in 2016 because tool makers declined the retooling cost, so the bar is a number on a table, not a wafer that is made.",
        "The 450 mm bars turn to hatching and the cancelled note appears under the blocks.",
    )
    .detail(
        "A bigger wafer needs new tools for every step, and the chip makers and tool makers would not pay for that change.",
        &[
            "450 mm: 342 g, 1490 dies per wafer (page table)",
            "Proposed for 2018, stopped in 2016: tool makers declined the retooling cost (page text)",
        ],
    ),
];

/// Fraction of a block's bar grown by time `local` in a beat.
fn grow(local: f32) -> f32 {
    ease_in_out((local / GROW).clamp(0.0, 1.0))
}

/// Bar length in columns for `value` out of the block's largest value, at `frac` grown.
fn bar_len(value: i32, max: i32, frac: f32) -> i32 {
    if frac <= 0.0 || value <= 0 {
        return 0;
    }
    ((value as f32 / max.max(1) as f32) * BAR_MAX as f32 * frac).round().max(1.0) as i32
}

/// One block: a title, then a row per diameter. `mass` picks grams or dies.
fn block(c: &mut Canvas, y0: i32, title: &str, mass: bool, frac: f32, beat: usize) {
    let max = SIZES
        .iter()
        .map(|s| if mass { s.grams } else { s.dies })
        .max()
        .unwrap_or(1);
    c.text(2, y0, title);
    for (i, s) in SIZES.iter().enumerate() {
        let y = y0 + 1 + i as i32;
        let v = if mass { s.grams } else { s.dies };
        let ch = if s.cancelled { '░' } else { '█' };
        c.text(2, y, s.name);
        let n = bar_len(v, max, frac);
        c.hline(BAR_X, y, n, ch);
        let unit = if mass {
            format!("{} g", v)
        } else {
            format!("{} die", v)
        };
        let tag = match (s.name, beat, s.cancelled) {
            ("300 mm", 2.., _) => "  standard",
            (_, 3.., true) => "  cancelled",
            _ => "",
        };
        c.text(BAR_X + n + 1, y, &format!("{unit}{tag}"));
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
        let (_w, h) = dims(c);
        // which block is growing this beat: mass first, then dies, then both held
        let (mass_f, dies_f) = match t.beat {
            0 => (grow(t.local), 0.0),
            1 => (1.0, grow(t.local)),
            _ => (1.0, 1.0),
        };
        c.text(2, 1, "per wafer, by diameter (page table, section 6)");
        block(c, MASS_Y, "mass per wafer, grams", true, mass_f, t.beat);
        block(c, DIES_Y, "ideal dies per wafer", false, dies_f, t.beat);
        // a marker on the standard row once it is singled out
        if t.beat >= 2 {
            let y = DIES_Y + 1 + 2;
            if flicker(t.ms, 300, 4, 2) != 0 {
                c.put(BAR_X - 2, MASS_Y + 1 + 2, '▸');
                c.put(BAR_X - 2, y, '▸');
            }
        }
        c.text(
            2,
            h - 3,
            "450 mm: proposed for 2018, stopped in 2016; tool makers declined the retooling cost",
        );
        c.text(2, h - 2, "bars scaled to the largest value in each block");
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
    fn beats_are_captioned_and_explained() {
        let s = build();
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
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
    fn values_and_tags_show_at_the_right_beats() {
        let mut p = Player::new(build(), Instant::now());
        p.fit(80, 26);
        let end = at(&mut p, 3, 0.99);
        assert!(end.contains("342 g"));
        assert!(end.contains("1490 die"));
        assert!(end.contains("cancelled"));
        assert!(at(&mut p, 2, 0.5).contains("standard"));
        assert!(!at(&mut p, 1, 0.5).contains("standard"));
    }
}
