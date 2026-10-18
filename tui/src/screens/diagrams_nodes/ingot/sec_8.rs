// INGOT section 8 (Market structure and risks): who can make the wafer, how the cycle hits it,
// and where the supply chain is fragile.
//
// Sources (figures checked against the pages below unless marked page text):
//   [6] SEMI SMG year-end 2023 release, as quoted in Mark LaPedus's post:
//       marklapedus.substack.com/p/silicon-wafer-market-upturn-higher
//       (wafer revenue -10.9% to $12.3B; area shipments 12,602 million sq in, -14.3%;
//        300 mm polished -13%, epi -5%)
//   [7] Shin-Etsu's LTA comment, quoted in the same post (LTA prices rise on capex and raw
//       material costs).
//   Five-firm share (82-94%), the fixed vs step-up LTA rule, and the Spruce Pine link are
//   page text (INGOT.txt section 8) and were not re-checked here.
//
// Bars are schematic: their lengths are the stated percent changes, not measured data.

use crate::ui::anim::motion::{ease_in_out, lerp};
use crate::ui::anim::{Beat, Canvas, Scene, Time};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Bar width for a full 100% (2022 level, or 100% of the wafer market).
const BAR: i32 = 70;
const BAR_X: i32 = 4;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Fraction 0..1 of a span of the beat, eased.
fn span(t: &Time, from: f32, to: f32) -> f32 {
    ease_in_out(((t.local - from) / (to - from)).clamp(0.0, 1.0))
}

const BEATS: &[Beat] = &[
    Beat::new(
        "five firms make nearly all wafers: 82-94% of the market depending on source and year",
        BEAT_MS,
    )
    .note(
        "One bar is the whole wafer market. The solid part runs to the 82% mark and the band to 94%: the five-firm share across sources and years.",
        "The bar fills, then the five firm boxes light up under it. The marks stay where the page puts them.",
    )
    .detail(
        "Concentration is the main market fact. Qualification takes chipmakers years, so new entrants rarely win share.",
        &[
            "Five firms make nearly all wafers: 82-94% (page text, sections 7 and 8)",
            "Omdia 2020: five players 94% of $11.2B (page text, Omdia via KED Global)",
            "Shin-Etsu + SUMCO above 55% (page text)",
        ],
    ),
    Beat::new(
        "the 2023 down-cycle: wafer revenue -10.9% and shipments -14.3% in one year",
        BEAT_MS,
    )
    .note(
        "Each bar starts at the 2022 level (the faint dots) and shrinks to the stated 2023 change. The 300 mm rows are the polished and epi splits.",
        "Bars shrink over the beat. Bar length is schematic, drawn from the percent change, not from a dollar scale.",
    )
    .detail(
        "SEMI reported the 2023 fall, which the page calls a swing. The 300 mm polished rate fell faster than epi.",
        &[
            "[6] Wafer revenue -10.9% to $12.3B in 2023 (SEMI, via LaPedus post)",
            "[6] Area shipments 12,602 million sq in in 2023, -14.3% (SEMI)",
            "[6] 300 mm polished -13%, epi -5% in 2023 (SEMI chairman quote)",
        ],
    ),
    Beat::new(
        "the chain is fragile: quartz and polysilicon feed the wafer makers, and LTAs set the price",
        BEAT_MS,
    )
    .note(
        "A dot runs the chain from quartz to the chipmaker. Under the last link, the long-term agreement (LTA) is the price rule that moves with capex and raw material costs.",
        "The dot moves once per beat. The geography row lists where each firm is based.",
    )
    .detail(
        "Shin-Etsu said LTA prices rise because they include capex and raw material cost increases. Fixed-LTA customers see no 2024 rise, step-up LTAs may (page text).",
        &[
            "[7] Shin-Etsu: LTA prices expected to rise on capex and raw material costs",
            "Page text: crucible quartz (Spruce Pine) and electronic-grade polysilicon are chokepoints",
            "Page text: Japan (Shin-Etsu, SUMCO), Taiwan, Germany, Korea",
        ],
    ),
];

/// Five-firm bar: solid to 82%, banded to 94%, rest of the market left blank.
fn share_bar(c: &mut Canvas, y: i32, g: f32) {
    let fill = (BAR as f32 * 0.94 * g) as i32;
    let solid = ((BAR as f32 * 0.82) as i32).min(fill);
    c.hline(BAR_X, y, solid, '█');
    c.hline(BAR_X + solid, y, fill - solid, '▓');
    c.hline(BAR_X + fill, y, BAR - fill, '░');
    let m82 = BAR_X + (BAR as f32 * 0.82) as i32;
    let m94 = BAR_X + (BAR as f32 * 0.94) as i32;
    c.put(m82, y - 1, '┃');
    c.put(m94, y - 1, '┃');
    c.text(m82 - 2, y - 2, "82%");
    c.text(m94 - 2, y - 2, "94%");
}

/// One row of the cycle chart: a faint 2022 level and a bar that shrinks to the 2023 change.
fn fall_row(c: &mut Canvas, y: i32, drop: f32, g: f32, label: &str) {
    let full = BAR;
    let len = lerp(full as f32, full as f32 * (1.0 - drop), g) as i32;
    c.hline(BAR_X, y, full, '·');
    c.hline(BAR_X, y, len, '█');
    c.text(BAR_X, y + 1, label);
}

/// Chain box: name on the top row, sub-line below, inside a light border.
fn link(c: &mut Canvas, x: i32, y: i32, w: i32, name: &str, sub: &str) {
    c.boxed(x, y, w, 4);
    c.text(x + 2, y + 1, name);
    c.text(x + 2, y + 2, sub);
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
        c.text(2, 1, "market structure and risks");
        match t.beat {
            0 => {
                let g = span(t, 0.0, 0.5);
                c.text(
                    BAR_X,
                    3,
                    "share of all silicon wafers (page text: 82-94% by source and year)",
                );
                share_bar(c, 6, g);
                // five firm boxes, one per firm, lit once the bar has filled
                let names = [
                    "Shin-Etsu",
                    "SUMCO",
                    "GlobalWafers",
                    "Siltronic",
                    "SK Siltron",
                ];
                let lit = g >= 1.0;
                for (i, n) in names.iter().enumerate() {
                    let x = 2 + i as i32 * 15;
                    c.boxed(x, 9, 14, 3);
                    if lit {
                        c.text(x + 1, 10, &n[..n.len().min(12)]);
                    }
                }
                c.text(BAR_X, 13, "new entrant:");
                c.text(
                    BAR_X + 13,
                    13,
                    "qualification takes years, so share is slow to move",
                );
                c.text(
                    BAR_X,
                    15,
                    "other firms make the rest of the market (the blank band)",
                );
            }
            1 => {
                c.text(
                    BAR_X,
                    3,
                    "2023 change vs 2022 (dots = 2022 level, schematic bars)",
                );
                let g = span(t, 0.1, 0.6);
                fall_row(c, 5, 0.109, g, "wafer revenue -10.9%  to $12.3B  [6]");
                fall_row(
                    c,
                    8,
                    0.143,
                    g,
                    "area shipments -14.3%  to 12,602 million sq in  [6]",
                );
                fall_row(c, 11, 0.13, g, "300 mm polished -13%  [6]");
                fall_row(c, 14, 0.05, g, "300 mm epi -5%  [6]");
                c.text(
                    BAR_X,
                    17,
                    "SEMI named the drop: weaker end demand and an inventory correction.",
                );
                c.text(BAR_X, 18, "It ended three years of growth.");
            }
            _ => {
                let n = 4;
                let gap = 4;
                let lw = (w - 4 - gap * (n - 1)) / n;
                let names = [
                    ("quartz", "Spruce Pine"),
                    ("polysilicon", "electronic"),
                    ("wafer maker", "5 firms"),
                    ("chipmaker", "fab"),
                ];
                let mut xs = [0; 4];
                for (i, (name, sub)) in names.iter().enumerate() {
                    let x = 2 + i as i32 * (lw + gap);
                    xs[i] = x;
                    link(c, x, 5, lw, name, sub);
                }
                for i in 0..n as usize - 1 {
                    let x0 = xs[i] + lw;
                    c.hline(x0, 6, gap - 1, '-');
                    c.put(x0 + gap - 1, 6, '>');
                }
                // one dot travels the chain once per beat
                let f = span(t, 0.05, 0.95);
                let px = lerp(xs[0] as f32 + 2.0, xs[3] as f32 + 2.0, f) as i32;
                c.put(px, 6, '●');
                c.text(2, 10, "LTA = long-term agreement, the price contract between wafer maker and chipmaker.");
                c.text(
                    2,
                    11,
                    "Shin-Etsu: LTA prices rise on capex and raw material costs [7].",
                );
                c.text(
                    2,
                    13,
                    "Japan: Shin-Etsu, SUMCO   Taiwan: GlobalWafers   Germany: Siltronic",
                );
                c.text(2, 14, "Korea: SK Siltron");
                c.text(
                    2,
                    16,
                    "risks: quartz supply, polysilicon supply, LTA pricing, slow qualification",
                );
            }
        }
        // footer: which beat of the section is showing
        c.text(2, h - 2, &format!("beat {} of {}", t.beat + 1, BEATS.len()));
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

    #[test]
    fn beats_are_captioned() {
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
    fn draws_at_sizes_and_times_without_panicking() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(build(), Instant::now());
            p.fit(w, h);
            for ms in [0, BEAT_MS / 2, 2 * BEAT_MS + BEAT_MS - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }
}
