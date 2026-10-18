// Zoom-ins for the MELT + PULL overview.
//
//   Neck        seed contact, dash neck with dislocations sliding out, the weight it carries, a dislocation that stays
//   Convection  melt flow driven by the hot wall, damped by a magnetic field, the interface shape, SiO from the quartz
//   HotZone     heater and felt, the axial temperature gradient, the heat shield, argon sweeping out the base

use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, flicker, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Melt surface with a moving ripple and a few rows of liquid below it.
fn surface(c: &mut Canvas, cx: i32, mel: i32, t: &Time) {
    for x in cx - 16..=cx + 16 {
        let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
            '≈'
        } else {
            '~'
        };
        c.put(x, mel, ch);
    }
    c.hline(cx - 16, mel + 1, 33, '~');
}

/// A crystal row: one cell for the neck, otherwise `hw` cells either side of the axis.
fn hrow(c: &mut Canvas, cx: i32, y: i32, hw: i32) {
    if hw == 0 {
        c.put(cx, y, '▓');
    } else {
        c.hline(cx - hw, y, 2 * hw + 1, '▓');
    }
}

// ---- a: the dash neck -----------------------------------------------------------

pub struct Neck;

const NECK_BEATS: &[Beat] = &[
    Beat::new(
        "the seed touches the melt; the contact shock throws dislocations into the crystal",
        BEAT_MS,
    )
    .note(
        "The oriented seed is lowered onto the melt. At contact the temperature gradient is severe, and the thermal shock creates dislocations that can run through the whole crystal.",
        "The seed coming down, a burst of * at the contact point, and dark / lines forming just below it.",
    )
    .detail(
        "Without a neck, those dislocations would propagate into the body and ruin it. The neck is how they are removed.",
        &[
            "Seed set to a {100} or {111} orientation (page text)",
            "Thermal shock on contact generates dislocations (page text)",
            "Dash neck pulled fast so dislocations exit the surface",
        ],
    ),
    Beat::new(
        "dash neck: 2-4 mm across, pulled up to about 6 mm a minute, dislocations slide out",
        BEAT_MS,
    )
    .note(
        "The operator pulls a thin neck quickly. Dislocations are inclined and glide outward, so they reach the neck surface and leave the crystal. Roughly 100-125 mm of neck is needed.",
        "The neck rising, dislocations / moving diagonally to the wall, and their exit shown as · outside the neck.",
    )
    .detail(
        "The neck only has to be thin and long enough to purge dislocations. A longer neck costs time, a shorter one lets defects through.",
        &[
            "Neck pulled up to about 6 mm/min (US 6,866,713)",
            "About 100-125 mm of neck purges dislocations (US 6,866,713)",
            "Another neck method pulls 1.0-3.0 mm/min, e.g. 2.4 mm/min over 200 mm (US 5,578,284)",
        ],
    ),
    Beat::new(
        "the neck carries the whole crystal: a dash neck is limited to about 100 kg",
        BEAT_MS,
    )
    .note(
        "Everything hangs from the neck. Its thin cross-section can fracture under the weight, dropping the body into the crucible. A 300 mm crystal of several hundred kilograms is far past what a dash neck can hold.",
        "The body hanging from the neck with a ╳ crack in it, and ↓ the weight pulling down on it.",
    )
    .detail(
        "A neck break is the most expensive single failure: the whole crystal drops into hot silicon.",
        &[
            "Dash-necked crystals are limited to about 100 kg (patent text, US 6,866,713)",
            "A 300 mm crystal is several hundred kg (Wikipedia)",
            "Dash-free necks at 0.5 mm/min or less are an alternative (US 7,179,330)",
        ],
    ),
    Beat::new(
        "a dislocation that stays in the neck runs into the body and forces a remelt",
        BEAT_MS,
    )
    .note(
        "If a dislocation survives the neck it propagates up into the body. The crystal is then pulled back into the melt and the whole pull starts again.",
        "The / line continuing up into the body, then the body dropping back into the ≈ melt.",
    )
    .detail(
        "This is why the neck is inspected before the shoulder is grown. Any dislocation found there is a reason to stop early.",
        &[
            "A retained dislocation propagates into the body and forces a remelt (page text)",
            "Neck breaks and remelts are the most expensive failures in the process",
            "A slower neck, 1.0-3.0 mm/min, is used in some methods (US 5,578,284)",
        ],
    ),
];

impl Scene for Neck {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        NECK_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cx = w / 2;
        let mel = h - 6;
        c.vline(cx - 16, mel, h - mel, '│');
        c.vline(cx + 16, mel, h - mel, '│');
        surface(c, cx, mel, t);
        let neck_len = 10;
        match t.beat {
            0 => {
                let tip = lerp(2.0, (mel - 2) as f32, ease_in_out(t.local)).round() as i32;
                c.vline(cx, 1, tip - 1, '│');
                c.hline(cx - 2, tip, 5, '▀');
                if t.local > 0.9 {
                    for dx in [-2, 2] {
                        c.put(cx + dx, mel - 1, '*');
                    }
                    for k in 0..3 {
                        c.put(cx - 1 + k, mel - 2 - k, '/');
                    }
                }
            }
            1 => {
                let len = (neck_len as f32 * ease_in_out(t.local)).round() as i32;
                let top = mel - 1 - len;
                c.vline(cx, 1, top - 1, '│');
                for y in top..mel {
                    c.hline(cx - 1, y, 3, '▓');
                }
                for k in 0..3 {
                    let f = (t.local * 1.3 + k as f32 * 0.33) % 1.0;
                    let y = mel - 2 - (f * 8.0) as i32;
                    if f < 0.6 {
                        c.put(cx, y, '/');
                    } else {
                        let side = if k % 2 == 0 { -2 } else { 2 };
                        c.put(cx + side, y, '·');
                    }
                }
            }
            2 => {
                let top = mel - 1 - neck_len;
                c.vline(cx, 1, top - 1, '│');
                for y in top..mel {
                    c.hline(cx - 1, y, 3, '▓');
                }
                for y in top - 5..top {
                    hrow(c, cx, y, 4);
                }
                let crack = if flicker(t.ms, 300, 9, 2) != 0 {
                    '╳'
                } else {
                    '┼'
                };
                c.put(cx, mel - 5, crack);
                c.put(cx, top - 6, '↓');
                c.label(cx + 6, top - 3, "~several hundred kg");
            }
            _ => {
                let top = mel - 1 - neck_len;
                c.vline(cx, 1, top - 1, '│');
                for y in top..mel {
                    c.hline(cx - 1, y, 3, '▓');
                }
                let drop = if t.local < 0.5 {
                    0
                } else {
                    (9.0 * ease_in_out((t.local - 0.5) * 2.0)).round() as i32
                };
                for y in top - 5..top {
                    hrow(c, cx, y + drop, 4);
                }
                if drop == 0 {
                    for y in top - 5..top {
                        c.put(cx - 1, y, '/');
                    }
                    c.label(cx + 6, top - 3, "dislocation stays");
                } else {
                    c.label(cx + 6, mel - 3, "remelt");
                }
            }
        }
    }
}

// ---- b: melt convection and the magnetic field -----------------------------------

pub struct Convection;

const CONV_BEATS: &[Beat] = &[
    Beat::new(
        "the melt convects: the hot crucible wall drives buoyancy flow, and rotation adds more",
        BEAT_MS,
    )
    .note(
        "Heat enters at the hot crucible wall and rises, while cooler melt sinks near the crystal. Crystal and crucible rotation add forced convection on top of that.",
        "Packets circling the melt in a loop: ° rising along the wall and drifting back to the center.",
    )
    .detail(
        "Convection makes the temperature and oxygen uneven across the growth front. That unevenness is what limits 300 mm growth.",
        &[
            "A 2023 modelling study found convection causes uneven temperature, growth rate and oxygen at the interface",
            "Buoyancy flow from the hot wall; rotation adds forced flow (page text)",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
        ],
    ),
    Beat::new(
        "a horizontal magnetic field brakes the flow, since molten silicon conducts electricity",
        BEAT_MS,
    )
    .note(
        "A horizontal magnetic field (HMCZ) is applied across the melt. Its force opposes the moving liquid, so the convection slows and settles. Manufacturers adopted these fields in the early 2000s as melt volumes grew.",
        "The ═ field lines across the melt, and the loop of ° slowing to a few packets.",
    )
    .detail(
        "Damping the flow is what lets the interface stay stable at 300 mm, so oxygen and dopant come out uniform.",
        &[
            "Horizontal (HMCZ) and cusp fields damp the melt (patent background)",
            "Cusp-field studies show the zero-Gauss plane changes convection and oxygen transport",
            "Molten silicon is a good conductor, so the field acts directly on it",
        ],
    ),
    Beat::new(
        "the solid-liquid interface flattens: a flat front gives uniform oxygen and dopant",
        BEAT_MS,
    )
    .note(
        "The crystal bottom bulges into the melt when the flow is strong. As the flow damps, the interface relaxes to a flat front across the diameter.",
        "The ▓ crystal base changing from a bulge to a flat line at the melt surface.",
    )
    .detail(
        "A calmer, flatter interface means uniform oxygen and dopant across the wafer, which means more in-spec wafers per crystal.",
        &[
            "The axial gradient in the COMSOL model drops from 500 to 100 C per metre (model)",
            "Flat interface gives uniform oxygen and dopant (page text)",
            "Pull rates faster than 1.0-1.6 mm/min push the interface convex or concave (page text)",
        ],
    ),
    Beat::new(
        "SiO from the quartz: the crucible wall dissolves and oxygen freezes into the crystal",
        BEAT_MS,
    )
    .note(
        "The melt dissolves the inner surface of the quartz crucible, forming SiO. Most of it evaporates, but some freezes in as interstitial oxygen. Crucible rotation, melt depth, pull speed and magnetic fields tune the level.",
        "The crucible wall thinning to ░, and * SiO bubbles rising from the wall toward the surface.",
    )
    .detail(
        "Oxygen is the main impurity that the field and rotation are used to control. Too much makes the wafer brittle; too little changes device behavior.",
        &[
            "SiO2 + Si gives 2SiO; most SiO evaporates (page text, textbook)",
            "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
            "Crucible rotation and melt depth tune the oxygen (page text)",
        ],
    ),
];

impl Scene for Convection {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        CONV_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cx = w / 2;
        let mel = h - 12;
        let bot = h - 3;
        let (cl, cr) = (cx - 16, cx + 16);
        // crucible walls: solid, then dissolving once the quartz starts to go
        let wall = if t.beat == 3 { '░' } else { '│' };
        c.vline(cl, mel - 4, bot - mel + 4, wall);
        c.vline(cr, mel - 4, bot - mel + 4, wall);
        c.hline(cl, bot, cr - cl + 1, '─');
        c.put(cl, bot, '└');
        c.put(cr, bot, '┘');
        for y in mel..bot {
            for x in cl + 1..cr {
                let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
                    '≈'
                } else {
                    '~'
                };
                c.put(x, y, ch);
            }
        }
        if t.beat == 1 {
            for row in [mel + 1, mel + 3] {
                c.hline(cl + 1, row, cr - cl - 1, '═');
            }
            c.label(cr + 2, mel + 2, "B field (HMCZ)");
        }
        // interface: bulges into the melt while the flow is strong, then goes flat
        let bulge = match t.beat {
            0 => 2.0,
            1 => lerp(2.0, 1.0, ease_in_out(t.local)),
            2 => lerp(1.0, 0.0, ease_in_out(t.local)),
            _ => 0.0,
        };
        for x in cx - 4..=cx + 4 {
            let dx = (x - cx) as f32 / 4.0;
            let off = (bulge * (1.0 - dx * dx)).round() as i32;
            for y in mel - 4..=mel - 1 + off {
                c.put(x, y, '▓');
            }
        }
        if t.beat == 0 {
            // crucible spins one way, crystal the other: forced flow stirs the melt
            c.label(cr + 2, mel + 4, "crucible ↺  crystal ↻");
        }
        let ring = Path::new(&[
            (cl + 2, mel + 2),
            (cr - 2, mel + 2),
            (cr - 2, bot - 1),
            (cl + 2, bot - 1),
            (cl + 2, mel + 2),
        ]);
        ring.draw(c);
        match t.beat {
            0 => flow(c, &ring, t.ms, Particles::new(301, 260, 2600), |q| {
                if q.rand(1) > 0.5 { '°' } else { '·' }
            }),
            1 => flow(c, &ring, t.ms, Particles::new(302, 700, 2600), |q| {
                if q.rand(1) > 0.5 { '°' } else { '·' }
            }),
            2 => c.label(cr + 2, mel - 1, "flat interface"),
            3 => {
                // argon at 2500 Pa: sparse, so little gas pushes back on the SiO leaving the surface
                for y in mel - 3..mel {
                    for x in cl + 1..cr {
                        if (x * 7 + y * 3).rem_euclid(5) == 0 {
                            c.put_if_blank(x, y, '·');
                        }
                    }
                }
                let rise = Path::new(&[(cl + 1, bot - 1), (cl + 1, mel)]);
                flow(c, &rise, t.ms, Particles::new(303, 400, 1800), |_| '*');
                c.label(cr + 2, mel + 1, "SiO ↑");
                c.label(cr + 2, mel - 2, "2500 Pa: little gas to push back");
            }
            _ => {}
        }
    }
}

// ---- c: the hot zone and the argon sweep -------------------------------------------

pub struct HotZone;

const HOT_BEATS: &[Beat] = &[
    Beat::new(
        "a graphite heater surrounds the crucible, wrapped in felt insulation",
        BEAT_MS,
    )
    .note(
        "The resistive graphite heater is around the crucible, and graphite felt insulates it from the water-cooled chamber. Hot-zone parts are consumables that are changed periodically.",
        "The heater ▒ glowing, the felt ░ outside it, and the melt sitting in the middle.",
    )
    .detail(
        "The hot zone is the main know-how of a wafer maker and is typically proprietary. Its parts wear and are replaced.",
        &[
            "The COMSOL model uses a 310 kW graphite heater",
            "Heater, felt, susceptor and heat shield are consumables (textbook, page text)",
            "Graphite reacts with SiO to make CO, so argon carries it out",
        ],
    ),
    Beat::new(
        "heat leaves through the crystal: the axial gradient runs from about 500 to 100 C per metre",
        BEAT_MS,
    )
    .note(
        "Heat from the melt flows up the crystal and out to the cooler chamber, so the crystal has a temperature gradient. Near the melt it is hot and close to 1414 C; higher up it is much cooler.",
        "The crystal shaded from ▓ near the melt, through ▒, to ░ at the top, with the temperature labels.",
    )
    .detail(
        "The gradient sets the stress and defect density in the crystal. A steep gradient at the interface drives defects, so the shape of the hot zone matters.",
        &[
            "The COMSOL model gradient falls from 500 to 100 C per metre (model)",
            "Model reaches steady contact temperature after about 400 minutes (model)",
            "Melt near 1414 C (COMSOL); 1425 C on Wikipedia for semiconductor grade",
        ],
    ),
    Beat::new(
        "a heat shield above the melt limits radiant heat reaching the crystal",
        BEAT_MS,
    )
    .note(
        "A heat shield is placed around the crystal above the melt. It controls how much heat the growing crystal sees from the melt, shaping the axial gradient and the cooling rate.",
        "The shield || around the crystal, and the crystal beneath it staying in its gradient band.",
    )
    .detail(
        "The shield sets how fast the crystal cools, which trades growth speed against defects and stress.",
        &[
            "A thick heat shield above the melt is used in some pullers (US 8,524,000 description)",
            "Insulation above the reflector controls axial heat flow (US 8,524,000)",
            "Pull rate changes the power needed; 1.6 mm/min used 4.97% less power (2023 study)",
        ],
    ),
    Beat::new(
        "argon enters at the top, sweeps past the crystal, and leaves the base with SiO and CO",
        BEAT_MS,
    )
    .note(
        "Argon is the carrier gas. It flows down past the crystal and out the bottom, taking SiO and CO away so they do not condense on cold parts and fall back into the melt.",
        "° argon sweeping down the chamber wall past the crystal, with * SiO and · CO riding out the bottom.",
    )
    .detail(
        "Low pressure speeds up SiO evaporation, which lowers the oxygen picked up by the melt.",
        &[
            "Argon at 100 L/min and 2500 Pa in the COMSOL model (model, not a vendor spec)",
            "Argon carries SiO and CO out the bottom (page text)",
            "Graphite and SiO form CO (page text)",
        ],
    ),
];

impl Scene for HotZone {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        HOT_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cx = w / 2;
        let mel = h - 12;
        let bot = h - 6;
        let (cl, cr) = (cx - 10, cx + 10);
        // chamber, felt, heater, crucible
        titled_box(c, cx - 18, 0, 37, h - 2, "chamber, water-cooled");
        let glow = if flicker(t.ms, 200, 5, 3) != 0 {
            '▒'
        } else {
            '░'
        };
        let heat = if t.beat == 0 { '░' } else { glow };
        if t.beat == 0 {
            c.label(cx + 20, mel - 5, "heater ▒  felt ░");
        }
        for x in [cx - 15, cx + 15] {
            c.vline(x, mel - 6, bot - mel + 6, '░');
        }
        for x in [cx - 13, cx + 13] {
            c.vline(x, mel - 5, bot - mel + 5, heat);
        }
        c.hline(cx - 13, bot + 1, 27, heat);
        c.vline(cl, mel - 4, bot - mel + 4, '│');
        c.vline(cr, mel - 4, bot - mel + 4, '│');
        c.hline(cl, bot, cr - cl + 1, '─');
        surface(c, cx, mel, t);
        // crystal: a gradient from hot at the melt to cool at the top, with a heat shield in beat 2
        let g = 8;
        for y in mel - g..mel {
            let d = (mel - 1 - y) as f32 / g as f32;
            let ch = if t.beat == 0 || d < 0.33 {
                '▓'
            } else if d < 0.66 {
                '▒'
            } else {
                '░'
            };
            for x in cx - 4..=cx + 4 {
                c.put(x, y, ch);
            }
        }
        if t.beat == 1 {
            c.label(cx + 6, mel - 1, "1414 C");
            c.label(cx + 6, mel - g, "cooler");
        }
        if t.beat == 2 {
            c.vline(cx - 6, mel - 10, 9, '║');
            c.vline(cx + 6, mel - 10, 9, '║');
            c.hline(cx - 6, mel - 10, 13, '═');
            c.label(cx + 8, mel - 10, "heat shield");
        }
        if t.beat == 3 {
            let path = Path::new(&[(cx + 9, 1), (cx + 9, bot - 1)]);
            path.draw(c);
            flow(c, &path, t.ms, Particles::new(401, 240, 2400), |q| {
                if q.rand(1) > 0.6 { '°' } else { '·' }
            });
            let sio = Path::new(&[(cx + 9, mel - 1), (cx + 9, 1)]);
            flow(c, &sio, t.ms, Particles::new(402, 900, 2000), |q| {
                if q.rand(1) > 0.5 { '*' } else { '·' }
            });
            c.label(cx + 11, bot + 2, "argon out the base");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn scenes() -> Vec<(&'static str, fn() -> Box<dyn Scene>)> {
        vec![
            ("neck", || Box::new(Neck)),
            ("convection", || Box::new(Convection)),
            ("hotzone", || Box::new(HotZone)),
        ]
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        for (name, mk) in scenes() {
            let s = mk();
            assert_eq!(s.beats().len(), 4, "{name}");
            for (i, b) in s.beats().iter().enumerate() {
                assert!(
                    !b.what.is_empty()
                        && !b.look.is_empty()
                        && !b.why.is_empty()
                        && !b.facts.is_empty(),
                    "{name} {i}"
                );
            }
        }
    }

    #[test]
    fn zooms_scale_and_move() {
        for (name, mk) in scenes() {
            for (w, h) in [(50, 10), (80, 26), (130, 40), (240, 80)] {
                let mut p = Player::new(mk(), Instant::now());
                p.fit(w, h);
                let mut seen = std::collections::HashSet::new();
                for ms in (0..p.loop_ms()).step_by(173) {
                    let s = p.shot_at(ms);
                    assert_eq!(s.lines.len(), p.height());
                    assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                    seen.insert(s.lines.join("\n"));
                }
                assert!(seen.len() > 15, "{name} {w}x{h}: {}", seen.len());
            }
        }
    }

    #[test]
    fn each_zoom_shows_its_story() {
        let mk = |s: Box<dyn Scene>| {
            let mut p = Player::new(s, Instant::now());
            p.fit(120, 38);
            p
        };
        let mut p = mk(Box::new(Neck));
        assert!(at(&mut p, 0, 0.95).contains('*'));
        assert!(
            at(&mut p, 2, 0.5).contains('▓') && at(&mut p, 2, 0.5).contains("several hundred kg")
        );
        assert!(at(&mut p, 3, 0.9).contains("remelt"));
        assert!(at(&mut p, 3, 0.2).contains("dislocation stays"));
        let mut p = mk(Box::new(Convection));
        assert!(at(&mut p, 1, 0.5).contains("B field"));
        assert!(at(&mut p, 0, 0.5).contains("crucible ↺"));
        assert!(at(&mut p, 3, 0.5).contains("2500 Pa"));
        assert!(at(&mut p, 3, 0.5).contains("SiO"));
        assert!(at(&mut p, 2, 0.5).contains("flat interface"));
        let mut p = mk(Box::new(HotZone));
        assert!(at(&mut p, 0, 0.5).contains("felt ░"));
        assert!(at(&mut p, 1, 0.5).contains("1414 C"));
        assert!(at(&mut p, 2, 0.5).contains("heat shield"));
        assert!(at(&mut p, 3, 0.5).contains("argon out the base"));
    }
}
