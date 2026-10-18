// MELT + PULL section 7: animated close-up in the zoom template. Four beats: the quartz crucible is consumed each
// pull and its supply can fail; one dislocation forces a remelt; oxygen and dopant uniformity at 300 mm; and the
// cyclical demand drop in SEMI's 2023 figures.

use crate::ui::anim::shapes::{Path, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, lerp, noise};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Melt surface with a moving ripple, as in the page overview.
fn melt_surface(c: &mut Canvas, cx: i32, mel: i32, t: &Time) {
    for x in cx - 10..=cx + 10 {
        let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
            '≈'
        } else {
            '~'
        };
        c.put(x, mel, ch);
    }
}

const BEATS: &[Beat] = &[
    Beat::new(
        "the quartz crucible is consumed every pull, and its Spruce Pine supply can stop",
        BEAT_MS,
    )
    .note(
        "The crucible is worn away by the melt on every pull, so each pull needs a new one. High-purity quartz comes mostly from Spruce Pine, NC. If that supply stops, the pullers have nothing to hold the melt.",
        "The crucible wall eroding from the top as the pull runs, and the supply pipe from Spruce Pine going cold at the ╳ cut.",
    )
    .detail(
        "Quartz is the single consumable that every pull depends on. A supply outage idles the pullers even when the rest of the line works.",
        &[
            "Crucibles are consumed every pull (page text)",
            "High-purity quartz mostly from Spruce Pine, NC (page text, see SAND)",
            "A Spruce Pine outage idles pullers (page text)",
        ],
    ),
    Beat::new(
        "one dislocation anywhere in the body means the crystal is remelted",
        BEAT_MS,
    )
    .note(
        "A dislocation that survives into the body is a fault in the whole crystal, so the pull is ruined. The body drops back into the melt and the charge is melted again.",
        "The ▓ body with a / dislocation running through it, then the body sinking into the ≈ melt.",
    )
    .detail(
        "Yield is lost to a single defect. A large hot zone and a long cycle make each ruined pull more expensive to lose.",
        &[
            "A dislocation anywhere in the body means remelting (page text)",
            "Big hot zones and long cycles make a ruined pull expensive (page text)",
            "Cycle times are not sourced in this section",
        ],
    ),
    Beat::new(
        "oxygen and dopant uniformity across a 300 mm wafer is the hard control problem",
        BEAT_MS,
    )
    .note(
        "Across the diameter of a 300 mm crystal, the oxygen and dopant level varies from point to point. The varying level is shown as · low, + mid and * high. Crucible rotation is one control on this, and it is patented.",
        "The disc of wafer cells, with the scatter tightening as the control is applied, and the ↺ ↻ rotation labels.",
    )
    .detail(
        "Uniformity is the control that a 300 mm puller must hold. Crucible rotation is one of the levers, and it is covered by patents.",
        &[
            "Oxygen and dopant uniformity at 300 mm is the hard control problem (page text)",
            "Patents cover crucible rotation (page text)",
            "Oxygen is set by crucible rotation and melt depth (page text)",
        ],
    ),
    Beat::new(
        "demand is cyclical: SEMI's 2023 figures show wafer revenue and 300 mm shipments down",
        BEAT_MS,
    )
    .note(
        "The bars show SEMI's 2023 changes. Wafer revenue fell, and polished 300 mm shipments fell further, with epi 300 mm down less. Total area shipped fell the most. Each bar grows from the axis as the figure is read.",
        "Four bars growing to the right from the axis, each with its percent change at the end.",
    )
    .detail(
        "Demand swings give the pullers less work and pressure the margin on each pull. A fall in shipments is a risk to the whole chain.",
        &[
            "SEMI: 2023 silicon wafer revenue fell 10.9% to $12.3B (page text)",
            "Polished 300 mm shipments fell 13%; epi 300 mm fell 5% (page text)",
            "Total area 12,602 million sq in, down 14.3% (page text)",
        ],
    ),
];

/// SEMI 2023 changes, in percent, from the page text. Drawn as bars with the figure at the end.
const DEMAND: &[(&str, f32, &str)] = &[
    ("wafer revenue", 10.9, "-10.9%"),
    ("polished 300 mm", 13.0, "-13%"),
    ("epi 300 mm", 5.0, "-5%"),
    ("total area", 14.3, "-14.3%"),
];

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
        let cx = w / 2;
        let mel = h - 8;
        let bot = h - 3;
        let (cl, cr) = (cx - 10, cx + 10);
        match t.beat {
            0 => {
                // the supply pipe from Spruce Pine feeds the crucible; the crucible wears away from the top
                let pipe = Path::new(&[(4, 4), (4, mel - 6), (cl - 1, mel - 6)]);
                pipe.draw(c);
                c.label(2, 2, "Spruce Pine, NC");
                if t.local < 0.5 {
                    flow(c, &pipe, t.ms, Particles::new(701, 300, 2200), |_| '·');
                } else {
                    c.put(cl - 4, mel - 6, '╳');
                    c.label(4, 8, "outage: pullers idle");
                }
                let eroded = (t.local * 4.0) as i32;
                c.vline(cl, mel - 4, bot - mel + 4, '│');
                c.vline(cr, mel - 4, bot - mel + 4, '│');
                for k in 0..eroded {
                    c.put(cl, mel - 4 + k, ' ');
                    c.put(cr, mel - 4 + k, ' ');
                }
                c.hline(cl, bot, cr - cl + 1, '─');
                c.put(cl, bot, '└');
                c.put(cr, bot, '┘');
                for y in mel..bot {
                    for x in cl + 1..cr {
                        c.put(x, y, '~');
                    }
                }
                melt_surface(c, cx, mel, t);
                c.label(cr + 2, mel - 2, "crucible consumed each pull");
            }
            1 => {
                // the body hangs above the melt; past the midpoint it sinks into the melt for a remelt
                let body_top = mel - 10;
                let sink = if t.local < 0.5 {
                    0
                } else {
                    (4.0 * ease_in_out((t.local - 0.5) * 2.0)).round() as i32
                };
                c.vline(cx, 1, body_top - 1, '│');
                for y in body_top..mel {
                    c.hline(cx - 4, y + sink, 9, '▓');
                }
                if sink == 0 {
                    for y in (body_top + 1..mel).step_by(2) {
                        c.put(cx - 1, y, '/');
                    }
                }
                c.vline(cl, mel - 4, bot - mel + 4, '│');
                c.vline(cr, mel - 4, bot - mel + 4, '│');
                c.hline(cl, bot, cr - cl + 1, '─');
                for y in mel..bot {
                    for x in cl + 1..cr {
                        c.put(x, y, '~');
                    }
                }
                melt_surface(c, cx, mel, t);
                if sink == 0 {
                    c.label(cr + 2, body_top + 2, "dislocation in body");
                } else {
                    c.label(cr + 2, mel - 3, "remelt");
                }
                c.label(4, 2, "big hot zone, long cycle:");
                c.label(4, 3, "a ruined pull costs more");
            }
            2 => {
                // a wafer cross-section: each cell's level is noise, scattered wide and then tightened by the control
                let (rx, ry) = (14, 6);
                let cy = h / 2;
                let amp = if t.local < 0.5 {
                    1.0
                } else {
                    lerp(1.0, 0.35, ease_in_out((t.local - 0.5) * 2.0))
                };
                for y in cy - ry..=cy + ry {
                    for x in cx - rx..=cx + rx {
                        let (dx, dy) = ((x - cx) as f32 / rx as f32, (y - cy) as f32 / ry as f32);
                        if dx * dx + dy * dy > 1.0 {
                            continue;
                        }
                        let v = (noise(707, (x * 131 + y * 17) as u64) - 0.5) * amp;
                        let ch = if v < -0.15 {
                            '·'
                        } else if v < 0.15 {
                            '+'
                        } else {
                            '*'
                        };
                        c.put(x, y, ch);
                    }
                }
                c.label(cx - rx, cy + ry + 2, "300 mm cross-section");
                c.label(cx + rx + 3, cy - 1, "↺ rotation");
                c.label(cx + rx + 3, cy + 1, "is patented");
                c.label(cx + rx + 3, cy + 3, "↻ control");
            }
            _ => {
                // SEMI 2023 changes as bars growing from the axis
                let grow = ease_in_out(t.local);
                c.label(4, 2, "SEMI 2023 change");
                for (i, (name, pct, value)) in DEMAND.iter().enumerate() {
                    let y = 6 + 4 * i as i32;
                    let len = (pct / 15.0 * 36.0 * grow).round() as i32;
                    c.label(4, y, name);
                    c.hline(26, y, len.max(1), '█');
                    c.label(26 + len + 2, y, value);
                }
                c.label(
                    4,
                    h - 3,
                    "wafer revenue $12.3B; total area 12,602 million sq in",
                );
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
        }
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(build(), Instant::now());
            p.fit(w, h);
            let last_start: u64 = Section.beats()[..Section.beats().len() - 1]
                .iter()
                .map(|b| b.ms)
                .sum();
            for ms in [0, BEAT_MS / 2, last_start, p.loop_ms() - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        let mut p = Player::new(build(), Instant::now());
        p.fit(120, 40);
        assert!(at(&mut p, 0, 0.2).contains("Spruce Pine"));
        assert!(at(&mut p, 0, 0.8).contains("outage"));
        assert!(at(&mut p, 1, 0.2).contains("dislocation"));
        assert!(at(&mut p, 1, 0.9).contains("remelt"));
        assert!(at(&mut p, 2, 0.5).contains("300 mm"));
        assert!(at(&mut p, 3, 0.9).contains("-14.3%"));
    }
}
