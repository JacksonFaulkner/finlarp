// MELT + PULL section 4, "By the numbers", as a close-up in the zoom template: the model's melt temperature and
// gradient, the furnace settings, the body size, and the 1.6 mm/min pull study. Every value comes from the section text.
//
// Sources: COMSOL, thermal model of a Czochralski furnace (model); Wikipedia, Czochralski method; 2023 study aimed
// at photovoltaic silicon (Journal of Synthetic Crystals 52(4)).

use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Melt surface with a moving ripple, `hw` cells either side of the axis.
fn melt(c: &mut Canvas, cx: i32, mel: i32, hw: i32, t: &Time) {
    for x in cx - hw..=cx + hw {
        let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
            '≈'
        } else {
            '~'
        };
        c.put(x, mel, ch);
    }
}

/// The crystal rod from `top` down to the melt at `mel`. Graded shading runs from ▓ at the melt to ░ at the top.
fn rod(c: &mut Canvas, cx: i32, top: i32, mel: i32, hw: i32, graded: bool) {
    let len = (mel - top).max(1);
    for y in top..mel {
        let d = (mel - 1 - y) as f32 / len as f32;
        let ch = if !graded || d < 0.33 {
            '▓'
        } else if d < 0.66 {
            '▒'
        } else {
            '░'
        };
        c.hline(cx - hw, y, 2 * hw + 1, ch);
    }
}

pub struct Section;

const BEATS: &[Beat] = &[
    Beat::new(
        "the melt sits near 1414 C; the model's gradient along the rod runs 500 down to 100 C per metre",
        BEAT_MS,
    )
    .note(
        "The simulation puts the melt near 1414 C and the contact between 1403 and 1407.5 C. Along the rod the axial gradient falls from 500 to 100 C per metre. These are model outputs, not measurements.",
        "The rod shaded from ▓ at the melt to ░ at the top, with three labels appearing in turn.",
    )
    .detail(
        "The gradient is the model's input for stress and defect density, so these numbers are what the hot zone is designed around.",
        &[
            "Melt ~1414 C (COMSOL); contact 1403-1407.5 C in the model",
            "Axial gradient 500 down to 100 C per metre (model)",
            "Model reaches steady contact temperature after ~400 minutes",
        ],
    ),
    Beat::new(
        "furnace settings: argon at 100 L/min and 2500 Pa, a 310 kW heater, and counter-rotation",
        BEAT_MS,
    )
    .note(
        "The model's operating point: argon flow and furnace pressure, heater power, and crucible and crystal rotation. The page marks all of these as model values, not vendor specs.",
        "Three rows on the right filling in turn. The bars only reveal the rows; they are not a scale.",
    )
    .detail(
        "These are the knobs the model sets. Argon carries SiO and CO out of the chamber, and rotation drives the melt flow.",
        &[
            "Argon 100 L/min at 2500 Pa in the COMSOL model (model, not a vendor spec)",
            "Graphite heater at 310 kW (model)",
            "Crucible 5 rpm, crystal -5 rpm (model)",
        ],
    ),
    Beat::new(
        "a 300 mm wafer needs a 300 mm-plus body; the body can reach 2 m and several hundred kg",
        BEAT_MS,
    )
    .note(
        "The body has to be wider than the wafer and long enough to make a full ingot. The page lists 450 mm as a planned step that was stopped. Length and mass grow with the body.",
        "The rod growing to full height, a dotted 450 mm outline appearing beside it, and the 2 m label at the top.",
    )
    .detail(
        "Diameter and length set the mass, and the neck has to hold that mass. This is why the neck limit matters at this size.",
        &[
            "300 mm wafers need a 300 mm+ body (page text)",
            "450 mm was planned for 2018 and stopped in 2016 (page text)",
            "Why it stopped (general industry knowledge, not on the page): 2.25x the wafer area needs new tools at almost every step, and the market did not need the extra capacity",
            "Up to 2 m long and several hundred kg (Wikipedia)",
        ],
    ),
    Beat::new(
        "a 1.6 mm/min simulated pull shifts the interface 33 mm; the model settles after about 400 minutes",
        BEAT_MS,
    )
    .note(
        "The 2023 study simulated a 300 mm pull at 1.6 mm/min. That moves the interface 33 mm and changes growth time and power. The model needs about 400 minutes to reach a steady contact temperature.",
        "The timeline marker running to 400 minutes, and the readout rows appearing in turn.",
    )
    .detail(
        "Pull speed trades growth time against power and interface position. The study was aimed at photovoltaic silicon, so these are not microelectronics figures.",
        &[
            "1.6 mm/min simulated: interface shifts 33 mm (2023 study)",
            "Growth time -46.4%, power -4.97% at that rate (2023 study)",
            "Steady contact temperature after ~400 minutes (model)",
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
        let (w, h) = dims(c);
        let cx = w / 3;
        let mel = h - 6;
        let top = 2;
        let hw = 4;
        let x0 = cx + hw + 6;
        match t.beat {
            0 => {
                rod(c, cx, top, mel, hw, true);
                melt(c, cx, mel, hw + 2, t);
                if t.local > 0.2 {
                    c.label(x0, mel - 1, "melt ~1414 C (COMSOL)");
                }
                if t.local > 0.5 {
                    c.label(x0, mel - 4, "contact 1403-1407.5 C (model)");
                }
                if t.local > 0.8 {
                    c.label(x0, top + 1, "gradient 500 down to 100 C/m (model)");
                }
            }
            1 => {
                rod(c, cx, top, mel, hw, false);
                melt(c, cx, mel, hw + 2, t);
                let rows = [
                    ("argon, furnace", "100 L/min, 2500 Pa (model)"),
                    ("heater", "310 kW graphite (model)"),
                    ("rotation", "crucible 5 rpm, crystal -5 rpm (model)"),
                ];
                for (k, (name, value)) in rows.iter().enumerate() {
                    let y = top + 2 + 4 * k as i32;
                    let start = 0.1 + 0.25 * k as f32;
                    let f = ease_in_out(((t.local - start) / 0.3).clamp(0.0, 1.0));
                    c.text(x0, y, name);
                    c.text(x0, y + 1, value);
                    let n = (f * 24.0).round() as i32;
                    c.hline(x0, y + 2, n, '█');
                }
                c.label(x0, top + 16, "bars reveal rows, not a scale");
            }
            2 => {
                let grow = ease_in_out(t.local);
                let len = lerp(2.0, (mel - 3) as f32, grow).round() as i32;
                let top_r = mel - len;
                rod(c, cx, top_r, mel, hw, false);
                melt(c, cx, mel, hw + 2, t);
                if t.local > 0.3 {
                    c.label(x0, mel - 1, "300 mm wafer: body 300 mm+");
                }
                if t.local > 0.5 {
                    // 450 mm is 1.5x the 300 mm body, so the outline sits at 6 cells either side, not 4.
                    for y in top_r..mel {
                        if y % 2 == 0 {
                            c.put(cx - hw - 2, y, '·');
                            c.put(cx + hw + 2, y, '·');
                        }
                    }
                    c.label(x0, mel - 4, "450 mm: planned 2018, stopped 2016");
                }
                if t.local > 0.7 {
                    c.label(x0, top, "up to 2 m, several hundred kg");
                }
            }
            _ => {
                rod(c, cx, top, mel, hw, false);
                melt(c, cx, mel, hw + 2, t);
                // timeline: 0 to 400 minutes, marker running along it
                let p = ease_in_out(t.local);
                let span = 30;
                c.text(x0, top + 2, "minutes to steady state");
                c.hline(x0, top + 3, span + 1, '─');
                c.put(x0 + span, top + 3, '|');
                c.put(x0 + (p * span as f32).round() as i32, top + 3, '▲');
                c.text(x0, top + 4, "0");
                c.text(x0 + span - 3, top + 4, "400");
                if t.local > 0.9 {
                    c.label(x0, top + 5, "steady after ~400 min");
                }
                if t.local > 0.3 {
                    c.text(x0, top + 8, "1.6 mm/min simulated, 300 mm");
                }
                if t.local > 0.5 {
                    c.text(x0, top + 10, "interface shifts 33 mm");
                }
                if t.local > 0.7 {
                    c.text(x0, top + 12, "growth time -46.4%, power -4.97%");
                    c.text(x0, top + 14, "(2023 study, photovoltaic silicon)");
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
    fn draws_at_sizes_and_times_without_panicking() {
        let beats = Section.beats().len();
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(Box::new(Section), Instant::now());
            p.fit(w, h);
            for beat in 0..beats {
                for frac in [0.0, 0.5, 0.99] {
                    let s =
                        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64);
                    assert_eq!(s.lines.len(), p.height());
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_numbers() {
        let mut p = Player::new(Box::new(Section), Instant::now());
        p.fit(120, 38);
        assert!(at(&mut p, 0, 0.9).contains("1414 C"));
        assert!(at(&mut p, 1, 0.9).contains("2500 Pa"));
        assert!(at(&mut p, 2, 0.9).contains("450 mm"));
        assert!(at(&mut p, 3, 0.95).contains("400"));
    }
}
