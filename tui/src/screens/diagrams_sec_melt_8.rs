// MELT + PULL section 8: the listed names, as a zoom-in on the section text.
//
//   Names    the four wafer makers and their tickers, one box each
//   Parent   SK Siltron has no ticker here; it is held by SK Inc (034730.KS)
//   Pullers  the puller makers are a separate list: PVA TePla, Ferrotec
//   Sourcing tickers and puller makers are general knowledge, not a fetched source

use crate::ui::anim::shapes::titled_box;
use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, flicker, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

// ---- 8: the listed names ---------------------------------------------------------

pub struct Section;

const SECTION_BEATS: &[Beat] = &[
    Beat::new(
        "four listed wafer makers, each with its own exchange ticker",
        BEAT_MS,
    )
    .note(
        "The section lists four wafer makers with their tickers. The boxes appear in list order, so each name is read as it lands.",
        "Four boxes filling in, two per row, each with its ticker inside.",
    )
    .detail(
        "These tickers are the entry points for looking up the listed wafer makers. The section gives tickers only.",
        &[
            "Shin-Etsu Chemical 4063.T, SUMCO 3436.T (page text)",
            "GlobalWafers 6488.TWO, Siltronic SSG.DE, also WAF.DE (page text)",
            "No share, revenue or size figure appears in section 8 (page text)",
        ],
    ),
    Beat::new(
        "SK Siltron is not listed on its own: it is held by SK Inc",
        BEAT_MS,
    )
    .note(
        "SK Siltron appears inside the SK Inc box, which carries the listing (034730.KS). It is shown as a holding, not a separate ticker.",
        "A small SK Siltron box sliding into the SK Inc box, with the ticker on the parent.",
    )
    .detail(
        "The parent ticker is the one to look up for SK Siltron. Reading the section without this would suggest a missing listing.",
        &[
            "SK Siltron is held by SK Inc (034730.KS) (page text)",
            "The section gives no separate ticker for SK Siltron (page text)",
        ],
    ),
    Beat::new(
        "the puller makers are a separate list: PVA TePla and Ferrotec",
        BEAT_MS,
    )
    .note(
        "Pullers are the machines that grow the crystal. The section names two puller makers, and the crystal rises on its cable as they are read.",
        "A cable from the top of the frame, a crystal rising out of the melt, and two labels at its side.",
    )
    .detail(
        "Puller makers are kept apart from wafer makers in the section. A wafer maker and the puller it buys are different companies.",
        &[
            "Puller makers e.g. PVA TePla (TPL.DE) (page text)",
            "Ferrotec 6890.T is also named as a puller maker (page text)",
            "Puller makers are not in the wafer-maker list above (page text)",
        ],
    ),
    Beat::new(
        "the tickers and puller makers are general knowledge, not a fetched source",
        BEAT_MS,
    )
    .note(
        "The section closes by marking its own sourcing. All names are collected in one box, and a stamp flickers on to say they were not fetched.",
        "The six names in a box, and a flickering stamp that reads not from a fetched source.",
    )
    .detail(
        "The stamp is the only sourcing caveat for this section. Treat the tickers as a starting list to check, not as verified data.",
        &[
            "Tickers and puller makers are general knowledge (page text)",
            "Not from a fetched source (page text)",
            "The section's Sources heading is empty (page text)",
        ],
    ),
];

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SECTION_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cx = w / 2;
        match t.beat {
            0 => {
                // each name lands in turn, two per row
                let boxes = [
                    (cx - 32, 2, "Shin-Etsu Chemical", "4063.T"),
                    (cx + 2, 2, "SUMCO", "3436.T"),
                    (cx - 32, 9, "GlobalWafers", "6488.TWO"),
                    (cx + 2, 9, "Siltronic", "SSG.DE (WAF.DE)"),
                ];
                for (k, (x, y, name, ticker)) in boxes.iter().enumerate() {
                    if t.local < k as f32 * 0.2 {
                        continue;
                    }
                    titled_box(c, *x, *y, 30, 5, name);
                    c.label(x + 2, y + 2, ticker);
                }
                c.label(cx - 32, 16, "section 8 gives tickers only");
            }
            1 => {
                // the parent box is always there; SK Siltron slides in from the right
                titled_box(c, cx - 20, 2, 40, 12, "SK Inc");
                c.label(cx - 18, 4, "034730.KS");
                let slide = ease_in_out(t.local);
                let x = lerp((cx + 30) as f32, (cx - 14) as f32, slide).round() as i32;
                if slide > 0.05 {
                    titled_box(c, x, 6, 28, 5, "SK Siltron");
                    c.label(x + 2, 8, "held by SK Inc");
                }
                c.label(cx - 18, 16, "no separate ticker");
            }
            2 => {
                // puller frame, crystal rising out of the melt on its cable
                let base = h - 4;
                let top = 2;
                c.hline(cx - 8, top, 17, '─');
                c.vline(cx, top + 1, 2, '│');
                c.hline(cx - 12, base, 25, '≈');
                let f = ease_in_out(t.local);
                let tip = lerp((base - 1) as f32, (base - 12) as f32, f).round() as i32;
                c.vline(cx, top + 3, tip - top - 3, '│');
                for y in tip..base {
                    c.hline(cx - 2, y, 5, '▓');
                }
                if t.local > 0.4 {
                    c.label(cx + 10, 4, "PVA TePla  TPL.DE");
                }
                if t.local > 0.7 {
                    c.label(cx + 10, 6, "Ferrotec  6890.T");
                }
                c.label(
                    cx - 40,
                    base + 1,
                    "puller makers, separate from the wafer list",
                );
            }
            _ => {
                titled_box(c, cx - 30, 2, 60, 15, "sourcing");
                let names = [
                    "Shin-Etsu Chemical 4063.T",
                    "SUMCO 3436.T",
                    "GlobalWafers 6488.TWO",
                    "Siltronic SSG.DE (WAF.DE)",
                    "PVA TePla TPL.DE",
                    "Ferrotec 6890.T",
                ];
                for (k, name) in names.iter().enumerate() {
                    c.label(cx - 26, 4 + k as i32, name);
                }
                if flicker(t.ms, 400, 7, 2) != 0 || t.local > 0.6 {
                    c.label(cx - 26, 13, "general knowledge: not from a fetched source");
                }
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
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        let s = Section;
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
            assert!(b.facts.iter().all(|f| !f.is_empty()), "beat {i} facts");
        }
    }

    #[test]
    fn section_draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(Box::new(Section), Instant::now());
            p.fit(w, h);
            for ms in [0, BEAT_MS / 2, 3 * BEAT_MS + BEAT_MS / 2] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
            }
        }
    }

    #[test]
    fn section_shows_its_story() {
        let mut p = Player::new(Box::new(Section), Instant::now());
        p.fit(120, 38);
        assert!(at(&mut p, 0, 0.95).contains("4063.T"));
        assert!(at(&mut p, 1, 0.95).contains("034730.KS"));
        assert!(at(&mut p, 1, 0.95).contains("SK Siltron"));
        assert!(at(&mut p, 2, 0.95).contains("TPL.DE"));
        assert!(at(&mut p, 3, 0.95).contains("not from a fetched source"));
    }
}
