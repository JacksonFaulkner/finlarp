// INGOT section 5: the wafer size ladder, thickness in um per diameter.
//
// Sources: Wikipedia, "Wafer (electronics)", standards table:
//   https://en.wikipedia.org/wiki/Wafer_(electronics)
// Read via WebFetch (HTML, not a PDF): 100 mm 1976 525 um; 150 mm 1983 675 um; 200 mm 1992 725 um;
// 300 mm 1999 775 um; 450 mm proposed, 925 um. The page warns the thicknesses relate to when each
// size was introduced and are not necessarily correct now. Bar lengths are scaled to 925 um.
// No standards PDF (SEMI) was read for thickness; SEMI M1 is listed on the page but not fetched.
//
//   Ladder  one bar per size, grown in turn from 100 mm to 450 mm, each with its thickness
//   Pick    the 300 mm row is the size in use, highlighted with its tolerance note from the page
//   Never   the 450 mm row is proposed, not built, drawn as the top of the ladder

use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, flicker, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Share of beat 0 spent growing the bars; the rest holds the full ladder.
const GROW_SPAN: f32 = 0.85;
/// Bar scale: the longest bar (925 um) is this many cells.
const BAR_MAX: i32 = 40;
const BAR_X: i32 = 20;
const TOP_Y: i32 = 4;
const ROW_H: i32 = 2;

/// One rung of the ladder, as the page table gives it.
struct Rung {
    label: &'static str,
    um: i32,
}

const LADDER: &[Rung] = &[
    Rung {
        label: "100 mm (1976)",
        um: 525,
    },
    Rung {
        label: "150 mm (1983)",
        um: 675,
    },
    Rung {
        label: "200 mm (1992)",
        um: 725,
    },
    Rung {
        label: "300 mm (1999)",
        um: 775,
    },
    Rung {
        label: "450 mm (never)",
        um: 925,
    },
];

/// Longest rung, used to scale every bar.
const UM_MAX: i32 = 925;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Bar length in cells for a thickness, rounded to the nearest cell.
fn bar_len(um: i32) -> i32 {
    (um * BAR_MAX + UM_MAX / 2) / UM_MAX
}

/// Share of the ladder drawn for rung `i` at this moment of beat 0; rungs grow one after another.
fn grow(i: usize, t: &Time) -> f32 {
    if t.beat != 0 {
        return 1.0;
    }
    let p = (t.local / GROW_SPAN).clamp(0.0, 1.0);
    let k = i as f32 / LADDER.len() as f32;
    let step = 1.0 / LADDER.len() as f32;
    ease_in_out(((p - k) / step).clamp(0.0, 1.0))
}

pub struct Section;

const BEATS: &[Beat] = &[
    Beat::new(
        "the ladder: thickness grows with diameter, from 525 um at 100 mm to 775 um at 300 mm",
        BEAT_MS,
    )
    .note(
        "Each wafer size gets a bar scaled to its thickness. Going up the sizes, the wafer gets thicker: 525 um at 100 mm, 775 um at 300 mm.",
        "Bars grow in turn from the top rung down, each one ending on its thickness in um.",
    )
    .detail(
        "Thickness goes up with diameter, so a larger wafer needs a thicker blank to stay rigid through processing.",
        &[
            "100 mm (1976) 525 um, 150 mm (1983) 675 um (page table)",
            "200 mm (1992) 725 um, 300 mm (1999) 775 um (page table)",
            "Source: Wikipedia, Wafer (electronics), standards table",
        ],
    ),
    Beat::new(
        "300 mm at 775 um is the size in use, the one this page is about",
        BEAT_MS,
    )
    .note(
        "The 300 mm row is highlighted: 775 um, introduced in 1999. The table gives this as the typical thickness for the size.",
        "The 300 mm bar and its label blink while the other rungs hold steady.",
    )
    .detail(
        "The 775 um figure is the one section 4 quotes for the 300 mm wafer. The Wikipedia table warns the values relate to when each size was introduced.",
        &[
            "300 mm: 775 um, introduced 1999 (Wikipedia standards table)",
            "Section 4 gives 775 um +/- 25 um (vendor sheets); a drawing shows +/- 20 um",
            "Table caveat: values are for the introduction year, not necessarily current",
        ],
    ),
    Beat::new(
        "450 mm is the top rung at 925 um, proposed and never built",
        BEAT_MS,
    )
    .note(
        "The 450 mm row is the longest bar: 925 um. The table lists it as proposed, with no year of introduction.",
        "The 450 mm bar blinks, and the other rungs drop back to a steady fill.",
    )
    .detail(
        "The top rung is a proposal, not a size in production. The table lists its thickness but no year.",
        &[
            "450 mm: 925 um, proposed (Wikipedia standards table)",
            "No introduction year is given for 450 mm in the table",
            "Section 6 gives the 450 mm mass and die count from the same table",
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
        let (_w, _h) = dims(c);
        c.text(2, 1, "wafer thickness by diameter (um), Wikipedia standards table");
        // which rung is highlighted this beat: 300 mm in beat 1, 450 mm in beat 2
        let hot: Option<usize> = match t.beat {
            1 => Some(3),
            2 => Some(4),
            _ => None,
        };
        for (i, r) in LADDER.iter().enumerate() {
            let y = TOP_Y + ROW_H * i as i32;
            let full = bar_len(r.um);
            let len = lerp(0.0, full as f32, grow(i, t)).round() as i32;
            let blink = hot == Some(i) && flicker(t.ms, 350, 5, 2) == 0;
            let label_ch = if blink { '▸' } else { ' ' };
            c.put(1, y, label_ch);
            c.text(2, y, r.label);
            c.hline(BAR_X, y, len, if hot == Some(i) { '▓' } else { '█' });
            if grow(i, t) >= 1.0 {
                c.text(BAR_X + full + 2, y, &format!("{} um", r.um));
            }
        }
        // legend under the ladder
        c.text(2, TOP_Y + ROW_H * LADDER.len() as i32 + 1, "bar length: longest bar = 40 cells");
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
    fn beats_are_captioned_and_sized() {
        let s = build();
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.caption.is_empty()
                    && !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
    }

    #[test]
    fn bars_match_the_page_scale() {
        // bar lengths reproduce the page's ladder: 23, 29, 31, 34, 40 cells
        let lens: Vec<i32> = LADDER.iter().map(|r| bar_len(r.um)).collect();
        assert_eq!(lens, vec![23, 29, 31, 34, 40]);
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
    fn ladder_grows_then_holds() {
        let mut p = Player::new(build(), Instant::now());
        p.fit(80, 26);
        // the full ladder shows its thickness labels once grown
        let end = at(&mut p, 0, 0.99);
        assert!(end.contains("775 um") && end.contains("925 um"));
        // early in beat 0 the top rung is not yet labelled
        assert!(!at(&mut p, 0, 0.05).contains("925 um"));
    }
}
