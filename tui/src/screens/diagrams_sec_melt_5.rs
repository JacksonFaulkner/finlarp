// MELT + PULL section 5: animated close-up on the pull-rate figures from the literature, mm/min.
//
// Sources: US 6,866,713 (dash neck, 6.0 mm/min); 2023 300 mm pull-rate simulation (1.6 mm/min); US 5,578,284
// (neck example, 2.4 mm/min); US 7,179,330 (dash-free neck, 0.5 mm/min or less).

use crate::ui::anim::shapes::{Path, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

/// Left edge of the bars, and the rate that the full bar width stands for.
const X0: i32 = 24;
const SCALE_MAX: f32 = 6.0;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Full bar width in cells for the rate at `SCALE_MAX`; grows with the canvas.
fn bar_max(w: i32) -> i32 {
    (w - 40).clamp(20, 60)
}

struct Rate {
    name: &'static str,
    mm: f32,
    /// True for a ceiling ("<= 0.5"), not a measured value.
    bound: bool,
    source: &'static str,
}

const RATES: &[Rate] = &[
    Rate {
        name: "dash neck max",
        mm: 6.0,
        bound: false,
        source: "US 6,866,713",
    },
    Rate {
        name: "300 mm sim",
        mm: 1.6,
        bound: false,
        source: "2023 simulation",
    },
    Rate {
        name: "neck example",
        mm: 2.4,
        bound: false,
        source: "US 5,578,284",
    },
    Rate {
        name: "dash-free neck",
        mm: 0.5,
        bound: true,
        source: "US 7,179,330",
    },
];

const BEATS: &[Beat] = &[
    Beat::new(
        "the dash neck is pulled at up to 6.0 mm/min, the fastest figure in this section",
        BEAT_MS,
    )
    .note(
        "The thin dash neck is pulled up at its maximum rate. The bar is drawn to scale, with 6.0 mm/min as the full width.",
        "The top bar growing across the scale to its full width, with 6.0 beside it.",
    )
    .detail(
        "The speed is the point of the neck: a fast pull carries dislocations out through the surface before the body starts.",
        &[
            "Dash neck max 6.0 mm/min (US 6,866,713)",
            "The neck is pulled fast so dislocations exit the surface (section text)",
            "Dash-necked crystals are limited to about 100 kg (US 6,866,713)",
        ],
    ),
    Beat::new(
        "the 300 mm body in a 2023 simulation is pulled at 1.6 mm/min, far slower than the neck",
        BEAT_MS,
    )
    .note(
        "The body rate for a 300 mm crystal comes from a simulation. The bar is much shorter than the neck bar on the same scale.",
        "The second bar growing to 1.6, labelled as a simulation rather than a measured pull.",
    )
    .detail(
        "The body is grown slowly so the freezing interface stays flat and stable. Faster pulls push it convex or concave.",
        &[
            "300 mm simulated pull rate 1.6 mm/min (2023 simulation)",
            "The 2023 study was aimed at photovoltaic silicon (page text)",
            "Pull rates faster than 1.0-1.6 mm/min push the interface convex or concave (page text)",
        ],
    ),
    Beat::new(
        "the neck example at 2.4 mm/min and the dash-free neck at 0.5 mm/min or less fill out the range",
        BEAT_MS,
    )
    .note(
        "Two more bars grow in. The dash-free bar is marked with <= because 0.5 is a ceiling, not a measured value.",
        "The third bar at 2.4, and the fourth bar stopping short at <= 0.5.",
    )
    .detail(
        "The figures span more than a tenfold range, from 0.5 to 6.0 mm/min, so the neck method is a choice rather than one fixed rate.",
        &[
            "Neck example 2.4 mm/min (US 5,578,284)",
            "Dash-free neck at 0.5 mm/min or less (US 7,179,330)",
            "Figures come from patents and one simulation, not a survey (section text)",
        ],
    ),
    Beat::new(
        "the neck runs fast to purge dislocations; the body runs slow to keep the interface flat",
        BEAT_MS,
    )
    .note(
        "The two parts of the pull run at different speeds for different jobs. Fast particles stream along the neck track, slow ones along the body track.",
        "Quick ▪ moving along the neck track, and slow • moving along the body track below it.",
    )
    .detail(
        "Each speed matches its job: the neck trades speed for purging dislocations, and the body trades speed for a flat, stable interface.",
        &[
            "The neck runs fast to purge dislocations (section text)",
            "The body runs slow to keep the interface flat and stable (section text)",
            "Dash neck max 6.0 mm/min against 1.6 mm/min simulated for 300 mm (section text)",
        ],
    ),
];

pub struct Rates;

impl Scene for Rates {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, _) = dims(c);
        let bm = bar_max(w);
        c.text(2, 1, "mm/min");
        c.text(X0, 1, "0");
        c.text(X0 + bm - 2, 1, "6.0");
        for (i, r) in RATES.iter().enumerate() {
            let y = 3 + 3 * i as i32;
            // beat 0 grows the neck, beat 1 the 300 mm body, beat 2 the last two; beat 3 holds all four
            let started = match t.beat {
                0 => i == 0,
                1 => i <= 1,
                _ => true,
            };
            if !started {
                c.text(2, y, r.name);
                continue;
            }
            let growing = match t.beat {
                0 => i == 0,
                1 => i == 1,
                2 => i >= 2,
                _ => false,
            };
            let f = if growing { ease_in_out(t.local) } else { 1.0 };
            let mut len = (bm as f32 * r.mm / SCALE_MAX * f).round() as i32;
            if f > 0.0 && len == 0 {
                len = 1;
            }
            c.text(2, y, r.name);
            if len > 0 {
                c.hline(X0, y, len, '█');
            }
            if f >= 0.95 {
                let v = if r.bound {
                    format!("<= {:.1}", r.mm)
                } else {
                    format!("{:.1}", r.mm)
                };
                c.label(X0 + len + 2, y, &v);
                c.text(X0, y + 1, r.source);
            }
        }
        if t.beat == 3 {
            let (neck_y, body_y) = (17, 20);
            let neck = Path::new(&[(X0, neck_y), (X0 + bm, neck_y)]);
            let body = Path::new(&[(X0, body_y), (X0 + bm, body_y)]);
            c.hline(X0, neck_y, bm + 1, '┄');
            c.hline(X0, body_y, bm + 1, '┄');
            c.label(X0, neck_y - 1, "neck: fast, purges dislocations");
            c.label(X0, body_y - 1, "body: slow, interface stays flat");
            flow(c, &neck, t.ms, Particles::new(501, 180, 900), |_| '▪');
            flow(c, &body, t.ms, Particles::new(502, 600, 2600), |_| '•');
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Rates)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn player() -> Player {
        Player::new(Box::new(Rates), Instant::now())
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> Vec<String> {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
    }

    fn has(ls: &[String], s: &str) -> bool {
        ls.iter().any(|l| l.contains(s))
    }

    fn bars(ls: &[String]) -> usize {
        ls.iter().map(|r| r.matches('█').count()).sum()
    }

    #[test]
    fn four_beats_all_explained() {
        let s = Rates;
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
    fn bars_grow_to_scale() {
        let mut p = player();
        p.fit(120, 40);
        assert!(bars(&at(&mut p, 0, 0.2)) < bars(&at(&mut p, 0, 0.99)));
        assert!(has(&at(&mut p, 0, 0.99), "6.0"));
        assert!(has(&at(&mut p, 1, 0.99), "1.6"));
        assert!(has(&at(&mut p, 2, 0.99), "2.4"));
        assert!(has(&at(&mut p, 2, 0.99), "<= 0.5"));
        assert!(has(&at(&mut p, 3, 0.5), "neck: fast"));
        assert!(has(&at(&mut p, 3, 0.5), "body: slow"));
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = player();
            p.fit(w, h);
            let last = p.loop_ms() - 1;
            for ms in [0, BEAT_MS + BEAT_MS / 2, last] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }
}
