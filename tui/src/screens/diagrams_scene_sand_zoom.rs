// Zoom-ins for the SAND overview: each is its own full-size scene, laid out
// from the canvas it is given.
//
//   Cavity1     one electrode tip: arc, gas cavity, SiC shell, Si dripping out
//   CrustStoke  crust growing around the cavity, then a stoking car breaks it
//   Tapping     lance, metal stream into the ladle, hood over the spout
//   BagHouse    off-gas through bag filters, pulse-jet cleaning, silica bin

use super::diagrams_scene_kit::{Cavity, paint};
use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, flicker, lerp, noise};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Electrode column with its tip, and a flickering arc down to `floor`.
fn electrode(c: &mut Canvas, cx: i32, tip: i32, floor: i32, t: &Time) {
    for y in 0..tip {
        c.put(cx - 1, y, '║');
        c.put(cx + 1, y, '║');
        c.put(cx, y, '▒');
    }
    c.text(cx - 1, tip, "╚═╝");
    for y in tip + 1..floor {
        let g = match flicker(t.ms + y as u64 * 37, 110, 5, 4) {
            0 => '┃',
            1 => '╎',
            2 => '╽',
            _ => '│',
        };
        c.put(cx, y, g);
    }
    for k in 0..6u64 {
        let n = noise(40 + k, t.ms / 90);
        let m = noise(60 + k, t.ms / 90);
        let x = cx + ((n * 2.0 - 1.0) * 5.0) as i32;
        let y = tip + 1 + (m * (floor - tip).max(1) as f32) as i32;
        c.put_if_blank(x, y, '*');
    }
}

// ---- a: the gas cavity ----------------------------------------------------

pub struct Cavity1;

const CAV_BEATS: &[Beat] = &[
    Beat::new(
        "a continuous arc keeps a gas cavity open under the electrode, above 1800 C",
        BEAT_MS,
    )
    .note(
        "The carbon electrode carries tens of kiloamps into the burden. The arc at its tip heats the charge until a pocket of gas, mostly SiO and CO, stays open around it. A hard, porous SiC shell lines the pocket.",
        "The arc ┃ flickering from the tip to the molten floor, sparks *, and gas ° moving around inside the cavity.",
    ),
    Beat::new(
        "SiO2 + C ─▶ SiO + CO: quartz at the cavity wall is reduced and SiO gas fills the cavity",
        BEAT_MS,
    )
    .note(
        "Quartz that reaches the hot wall melts and reacts with carbon. The products are gases: SiO and CO. This reaction is strongly endothermic, which is why the furnace needs so much power.",
        "° bubbles forming at the shell wall and moving in toward the center, with · sparkles where the charge breaks down.",
    ),
    Beat::new(
        "SiC + SiO ─▶ 2Si + CO: liquid silicon forms and collects on the cavity floor",
        BEAT_MS,
    )
    .note(
        "SiO gas meets SiC in the shell and the reaction yields liquid silicon, the product, plus CO. The silicon runs down the shell and pools on the floor of the cavity.",
        "● drops forming on the lower shell, sliding down, and the ≈ molten floor of the cavity thickening.",
    ),
    Beat::new(
        "Si drips to the pool; SiO that escapes upward is recaptured: SiO + 2C ─▶ SiC + CO",
        BEAT_MS,
    )
    .note(
        "Liquid silicon drains through the bed into the pool below. Some SiO escapes up through the shell. In the cooler charge above it meets carbon and turns into SiC, which feeds the shell again.",
        "● drops falling out the bottom into the ▓ pool, and ° gas leaving the top of the shell and thinning out as it rises.",
    ),
];

impl Scene for Cavity1 {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        CAV_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cv = Cavity {
            cx: w * 40 / 100,
            cy: h * 48 / 100,
            rx: (w as f32 * 0.17).max(11.0),
            ry: (h as f32 * 0.18).max(4.0),
        };
        let pool_top = (h - 5).max(cv.cy + cv.ry as i32 + 3).min(h - 3);
        paint(c, &[cv], 0.0, (1, w - 1, 0, pool_top), (t.ms / 1500) as i64);
        // molten floor of the cavity
        let floor = cv.cy + (cv.ry * 0.5) as i32;
        let thick = match t.beat {
            0 | 1 => 0,
            2 => (2.0 * ease_in_out(t.local)) as i32 + 1,
            _ => 3,
        };
        for y in floor..=cv.cy + cv.ry as i32 {
            for x in cv.cx - cv.rx as i32..=cv.cx + cv.rx as i32 {
                if cv.layer(x, y, 0.0) == Some(super::diagrams_scene_kit::Layer::Cavity)
                    && y >= cv.cy + cv.ry as i32 - thick
                {
                    c.put(x, y, '≈');
                }
            }
        }
        electrode(c, cv.cx, cv.cy - cv.ry as i32 + 1, floor, t);
        // the pool
        for y in pool_top..h - 1 {
            c.hline(1, y, w - 2, '▓');
        }
        draw_cavity_action(c, &cv, pool_top, t);
        // labels
        let lx = (cv.cx + cv.rx as i32 + 6).min(w - 34);
        c.label(lx, 1, "◀ carbon electrode, consumed");
        c.label(
            lx,
            cv.cy - cv.ry as i32 - 2,
            "◀ charge: o quartz • coke ‡ chips",
        );
        c.label(lx, cv.cy - 1, "◀ gas cavity: SiO + CO");
        c.label(lx, cv.cy + 1, "◀ ░ SiC shell, hard and porous");
        c.label(lx, floor + 1, "◀ ≈ molten Si on the floor");
        c.label(lx, pool_top + 1, "◀ liquid Si pool");
    }
}

fn draw_cavity_action(c: &mut Canvas, cv: &Cavity, pool_top: i32, t: &Time) {
    let (rx, ry) = (cv.rx, cv.ry);
    let boundary = |theta: f32| {
        (
            cv.cx as f32 + (rx + 1.2) * theta.cos(),
            cv.cy as f32 + (ry + 0.6) * theta.sin(),
        )
    };
    match t.beat {
        0 => {
            for k in 0..14u64 {
                let a = noise(k, t.ms / 180);
                let b = noise(k + 99, t.ms / 180);
                let x = cv.cx + ((a * 2.0 - 1.0) * (rx - 2.0)) as i32;
                let y = cv.cy + ((b * 2.0 - 1.0) * (ry - 1.0)) as i32;
                c.put_if_blank(x, y, '°');
            }
        }
        1 => {
            Particles::new(51, 90, 1800).each(t.ms, |p| {
                let (bx, by) = boundary(p.rand(1) * std::f32::consts::TAU);
                let (x, y) = (
                    lerp(bx, cv.cx as f32, p.age * 0.8),
                    lerp(by, cv.cy as f32 - ry * 0.3, p.age * 0.8),
                );
                c.put_if_blank(x.round() as i32, y.round() as i32, '°');
            });
            for k in 0..10u64 {
                let (x, y) = boundary(noise(k, t.ms / 260) * std::f32::consts::TAU);
                c.put(x.round() as i32, y.round() as i32, '·');
            }
        }
        2 => {
            Particles::new(52, 160, 1700).each(t.ms, |p| {
                let theta = lerp(0.2, 2.9, p.rand(1));
                let (bx, by) = boundary(theta);
                let y = by + p.age * (ry * 0.5);
                c.put(bx.round() as i32, y.round() as i32, '●');
            });
        }
        _ => {
            Particles::new(53, 260, 2400).each(t.ms, |p| {
                let y = cv.cy
                    + ry as i32
                    + 1
                    + (p.age * (pool_top - cv.cy - ry as i32 - 1).max(1) as f32) as i32;
                let x = cv.cx + (p.rand(1) * 6.0) as i32 - 3;
                if y < pool_top {
                    c.put(x, y, '●');
                }
            });
            Particles::new(54, 140, 2600).each(t.ms, |p| {
                let x = cv.cx + ((p.rand(1) - 0.5) * 2.0 * (rx - 2.0)) as i32;
                let y = cv.cy as f32 - ry - 1.0 - p.age * (cv.cy as f32 - ry - 2.0);
                c.put_if_blank(x + (p.age * 4.0 * (p.rand(2) - 0.5)) as i32, y as i32, '°');
            });
        }
    }
}

// ---- b: crust and stoking ---------------------------------------------------

pub struct CrustStoke;

const CRUST_BEATS: &[Beat] = &[
    Beat::new(
        "normal running: charge sinks into the cavity zone as fast as it is consumed",
        BEAT_MS,
    )
    .note(
        "In the ideal furnace raw material falls slowly through the shaft and is used up as fast as it is fed in. The cavity is steady and the SiC shell thin.",
        "The charge sliding down past the thin ▒ crust, steady ° gas, and a small cavity.",
    ),
    Beat::new(
        "SiO condenses on the cooler outside: 2SiO ─▶ SiO2 + Si builds crust",
        BEAT_MS,
    )
    .note(
        "Near the top of the furnace temperatures are low enough that SiO gas condenses to a sticky SiO2 + Si mix (reaction 3). That sets hard and becomes crust.",
        "· particles rising and sticking to the outer edge, the ▒ crust ring creeping outward.",
    ),
    Beat::new(
        "the crust thickens and rises, swelling the cavity and blocking charge from the hot zone",
        BEAT_MS,
    )
    .note(
        "As the crust gets thicker the gas cavity grows with it. Solid and liquid material can no longer reach the hot lower region, so less silicon is made and the furnace is losing output.",
        "The charge pattern freezing in place, the cavity visibly wider, and ▒ crust now far thicker than the ░ shell.",
    ),
    Beat::new(
        "stoking: a stoking car on the lid pushes a bar down into the crust",
        BEAT_MS,
    )
    .note(
        "About once an hour the operators send a stoking car along the lid. It pushes a long bar down through the charge onto the crust and starts breaking it.",
        "The car ▐███▌ sliding in at the top, and the bar ┃ descending until it touches the crust.",
    ),
    Beat::new(
        "the crust breaks up and charge falls into the hot zone again",
        BEAT_MS,
    )
    .note(
        "With the crust broken, charge can fall back into the cavity zone. The cavity shrinks and silicon production recovers, until the crust builds up again.",
        "Sparks * at the break, the ▒ ring shrinking, the cavity narrowing, and the charge sliding down again.",
    ),
];

fn crust_at(t: &Time) -> f32 {
    match t.beat {
        0 => 0.25,
        1 => lerp(0.25, 1.1, ease_in_out(t.local)),
        2 => lerp(1.1, 2.0, ease_in_out(t.local)),
        3 => 2.0,
        _ => lerp(
            2.0,
            0.25,
            ease_in_out((t.local * 1.4 - 0.2).clamp(0.0, 1.0)),
        ),
    }
}

impl Scene for CrustStoke {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        CRUST_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cv = Cavity {
            cx: w * 34 / 100,
            cy: h * 56 / 100,
            rx: (w as f32 * 0.11).max(7.0),
            ry: (h as f32 * 0.12).max(3.0),
        };
        let ct = crust_at(t);
        let frozen = 2 * BEAT_MS;
        let ms = match t.beat {
            0 | 1 => t.ms,
            2 | 3 => frozen,
            _ => frozen + (t.ms - 4 * BEAT_MS),
        };
        let pool_top = h - 4;
        paint(c, &[cv], ct, (1, w - 1, 2, pool_top), (ms / 1300) as i64);
        for y in pool_top..h - 1 {
            c.hline(1, y, w - 2, '▓');
        }
        let floor = cv.cy + (cv.ry * 0.5) as i32;
        electrode(c, cv.cx, cv.cy - cv.ry as i32 + 1, floor, t);
        // gas inside the (swelling) cavity
        let (rx, ry) = cv.radii(ct);
        for k in 0..8u64 {
            let x = cv.cx + ((noise(k, t.ms / 200) * 2.0 - 1.0) * (rx - 1.0)) as i32;
            let y = cv.cy + ((noise(k + 7, t.ms / 200) * 2.0 - 1.0) * (ry - 0.5)) as i32;
            c.put_if_blank(x, y, '°');
        }
        // condensing SiO settling onto the crust
        if t.beat == 1 || t.beat == 2 {
            Particles::new(61, 110, 2000).each(t.ms, |p| {
                let theta = lerp(3.5, 6.0, p.rand(1));
                let (rx2, ry2) = (rx + 2.0 + 2.5 * ct, ry + 1.2 + 1.4 * ct);
                let tx = cv.cx as f32 + rx2 * theta.cos();
                let ty = cv.cy as f32 + ry2 * theta.sin();
                let y = lerp(ty - 5.0, ty, p.age);
                c.put_if_blank(tx.round() as i32, y.round() as i32, '·');
            });
        }
        // stoking car and bar
        if t.beat >= 3 {
            let bar_x = cv.cx - (rx as i32) - 3;
            let slide = if t.beat == 3 {
                ease_in_out((t.local / 0.35).min(1.0))
            } else {
                1.0
            };
            let x = lerp(3.0, bar_x as f32, slide) as i32;
            c.text(x - 2, 0, "▐███▌");
            c.text(x - 2, 1, " o o ");
            let (_, ry_c) = cv.radii(2.0);
            let target = cv.cy - ry_c as i32 - 3;
            let depth = match t.beat {
                3 => ease_in_out(((t.local - 0.35) / 0.65).clamp(0.0, 1.0)),
                _ => (1.0 - (t.local - 0.7).max(0.0) / 0.3).clamp(0.0, 1.0),
            };
            let bottom = 2 + ((target - 2) as f32 * depth) as i32;
            if depth > 0.0 {
                c.vline(x, 2, bottom - 1, '┃');
            }
            if t.beat == 4 && t.local < 0.7 {
                for (dx, dy) in [(-2, 0), (2, 0), (0, 1), (-1, -1), (1, -1), (3, 1)] {
                    if noise(9, t.ms / 90 + (dx + 5) as u64) > 0.35 {
                        c.put(x + dx, bottom + dy, '*');
                    }
                }
            }
        }
        let lx = (cv.cx + cv.rx as i32 + 14).min(w - 34);
        c.label(lx, 3, "legend");
        c.label(lx, 4, "░ SiC shell");
        c.label(lx, 5, "▒ crust: SiO2 + Si + SiC");
        c.label(lx, 6, "° gas cavity (SiO + CO)");
        c.label(lx, 7, "o • ‡ loose charge");
        c.label(lx, 8, "▓ liquid Si");
    }
}

// ---- c: tapping --------------------------------------------------------------

pub struct Tapping;

const TAP_BEATS: &[Beat] = &[
    Beat::new(
        "the pool is full and the tap hole is plugged with clay",
        BEAT_MS,
    )
    .note(
        "Silicon collects at the bottom of the furnace over hours. The tap hole sits low in the wall and is kept shut with a clay plug until the pool is deep enough.",
        "The ▓ pool at its highest and the ▪ plug sealing the hole in the right wall.",
    ),
    Beat::new(
        "an oxygen lance burns through the plug",
        BEAT_MS,
    )
    .note(
        "Operators open the hole with an oxygen lance, which burns through the clay in seconds. The lance is a steel pipe; the oxygen makes the flame at its tip.",
        "The lance ═══▷ sliding in from the right and the flame * at its tip eating the plug ▪.",
    ),
    Beat::new(
        "metal runs down the spout into the ladle; fume rises off the stream",
        BEAT_MS,
    )
    .note(
        "Liquid silicon runs out through the hole and down a spout into the ladle. The pool falls as the ladle fills. Hot metal in air makes SiO and CO fume, which burns to microsilica.",
        "The ▓ stream pouring into the ladle, the pool level dropping, and · : fume rising off the metal.",
    ),
    Beat::new(
        "a hood over the spout pulls the fume into the filter line",
        BEAT_MS,
    )
    .note(
        "A hood, sometimes called a doghouse, sits over the taphole and spout. Fan suction pulls the fume up a duct to the bag filter. How well it captures depends on the shape of the hood and duct.",
        "The fume · now curving up into the hood and away along the duct instead of drifting into the room.",
    ),
    Beat::new(
        "a mud gun packs clay back into the hole to close it",
        BEAT_MS,
    )
    .note(
        "When the ladle is full a mud gun presses fresh clay into the hole. The furnace builds a new pool until the next tap. Only 80-90% of the silicon charged is recovered this way.",
        "The gun ▐▇▇═ pushing ▪ clay into the wall as the stream stops.",
    ),
];

impl Scene for Tapping {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        TAP_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let wall = w * 52 / 100;
        let top = 3;
        let bottom = h * 58 / 100;
        let hole_y = bottom - 3;
        // furnace cutaway: wall, charge on top, pool underneath
        c.hline(2, top, wall - 1, '─');
        c.vline(2, top + 1, bottom - top, '│');
        c.vline(wall, top + 1, bottom - top, '│');
        c.put(2, top, '┌');
        c.put(wall, top, '┐');
        c.hline(2, bottom, wall - 1, '─');
        c.put(2, bottom, '└');
        c.put(wall, bottom, '┘');
        let level = match t.beat {
            0 | 1 => 0.85,
            2 => lerp(0.85, 0.5, ease_in_out(t.local)),
            3 => lerp(0.5, 0.25, ease_in_out(t.local)),
            _ => lerp(0.25, 0.3, t.local),
        };
        let rows = bottom - top - 1;
        let pool = ((rows as f32) * level * 0.7).round() as i32;
        let pool_top = bottom - pool;
        let charge_end = pool_top;
        paint(
            c,
            &[],
            0.0,
            (3, wall, top + 1, charge_end),
            (t.ms / 1500) as i64,
        );
        for y in pool_top..bottom {
            c.hline(3, y, wall - 3, '▓');
        }
        c.text(5, pool_top.max(top + 2), "liquid Si");
        // tap hole
        let plug_open = matches!(t.beat, 2 | 3);
        let burning = t.beat == 1 && t.local > 0.35;
        let glyph = if plug_open {
            ' '
        } else if burning {
            '*'
        } else {
            '▪'
        };
        for dy in 0..2 {
            c.put(wall, hole_y + dy, glyph);
        }
        if t.beat == 4 {
            let push = ((t.local / 0.6).min(1.0) * 3.0) as i32;
            for dx in 0..push {
                c.put(wall - dx, hole_y, '▪');
                c.put(wall - dx, hole_y + 1, '▪');
            }
        }
        // spout, ladle and the stream
        let spout_x = wall + 10;
        let spout = Path::new(&[(wall + 1, hole_y + 1), (spout_x, hole_y + 1)]);
        spout.draw(c);
        let ladle_y = bottom + 4;
        let ladle_x = spout_x - 6;
        titled_box(c, ladle_x, ladle_y, 14, h - ladle_y - 1, "ladle");
        let lh = (h - ladle_y - 3).max(1);
        let lfill = match t.beat {
            0 | 1 => 0,
            2 => (lh as f32 * 0.5 * ease_in_out(t.local)).round() as i32,
            3 => (lh as f32 * (0.5 + 0.5 * t.local)).round() as i32,
            _ => lh,
        };
        for r in 0..lfill {
            c.hline(ladle_x + 1, h - 3 - r, 12, '▓');
        }
        if matches!(t.beat, 2 | 3) {
            Particles::new(71, 70, 600).each(t.ms, |p| {
                let y = hole_y + 2 + (p.age * (ladle_y - hole_y - 2) as f32) as i32;
                c.put(spout_x, y, '▓');
            });
            // fume off the stream
            let stream_fume = Particles::new(72, 150, 2200);
            if t.beat == 2 {
                stream_fume.each(t.ms, |p| {
                    let x = spout_x + ((p.rand(1) - 0.3) * 8.0 * p.age) as i32;
                    let y = hole_y as f32 - p.age * (hole_y as f32 - 1.0) * 0.8;
                    c.put_if_blank(x, y as i32, if p.rand(2) > 0.5 { '·' } else { ':' });
                });
            }
        }
        // hood and duct (drawn from beat 3)
        if t.beat == 3 {
            let hood_y = hole_y - 5;
            c.text(spout_x - 5, hood_y, "╱‾‾‾‾‾‾‾‾‾╲");
            c.label(spout_x + 2, hood_y - 1, "hood");
            let duct = Path::new(&[(spout_x, hood_y - 1), (spout_x, 1), (w - 2, 1)]);
            duct.draw(c);
            flow(c, &duct, t.ms, Particles::new(73, 140, 2600), |p| {
                if p.rand(1) > 0.5 { '·' } else { ':' }
            });
            c.text(w - 14, 2, "to filter ▶");
            Particles::new(74, 150, 1200).each(t.ms, |p| {
                let x = spout_x + ((p.rand(1) - 0.5) * 7.0 * (1.0 - p.age)) as i32;
                let y = hole_y as f32 - p.age * (hole_y - hood_y) as f32;
                c.put_if_blank(x, y as i32, '·');
            });
        }
        // lance (beat 1) and mud gun (beat 4)
        if t.beat == 1 {
            let ease = ease_in_out((t.local / 0.5).min(1.0));
            let tip = lerp((w - 4) as f32, (wall + 2) as f32, ease) as i32;
            c.hline(tip + 1, hole_y, (w - 3 - tip).max(0), '═');
            c.put(tip, hole_y, '▷');
            if t.local > 0.3 {
                c.put(tip - 1, hole_y, '*');
            }
        }
        if t.beat == 4 {
            let tip = wall + 3 - ((t.local / 0.6).min(1.0) * 2.0) as i32;
            c.text(tip, hole_y + 1, "▐▇▇══════");
        }
        c.text(wall + 2, hole_y - 2, "tap hole");
    }
}

// ---- d: the bag filter ---------------------------------------------------------

pub struct BagHouse;

const BAG_BEATS: &[Beat] = &[
    Beat::new(
        "off-gas laden with silica fume enters the baghouse",
        BEAT_MS,
    )
    .note(
        "SiO that escapes the burden burns in air to SiO2 particles about 150 nm across. They ride out of the lid in the hot gas with CO, and the duct carries the mixture to a bag filter.",
        "· fume and ° gas arriving along the duct from the left and spreading through the dirty side.",
    ),
    Beat::new(
        "gas passes through the bags; the fume stays behind as a cake on the cloth",
        BEAT_MS,
    )
    .note(
        "The cloth bags let gas through and stop the particles. A cake of fine silica builds up on the outside of each bag, which makes the filtering even finer but slows the flow.",
        "° passing through the bags and up out of the top, while · stops at the cloth and the ▒ cake thickens on each bag.",
    ),
    Beat::new(
        "a pulse of compressed air from the top shakes the cake off the bags",
        BEAT_MS,
    )
    .note(
        "When the cake is thick, a short blast of compressed air is fired down the inside of each bag in turn. The bag flexes and the cake drops off, so the filter can keep running.",
        "The ↓ jets at the top of each bag and ▒ cake falling off into the hopper below.",
    ),
    Beat::new(
        "the fume is collected as microsilica; clean gas goes up the stack",
        BEAT_MS,
    )
    .note(
        "The dust funnels into a bin. Microsilica is a valuable byproduct, used in concrete. Some producers also briquette it with carbon and feed it back to the furnace. The cleaned gas leaves through the stack.",
        "The silica bin ▒ rising and a thin stream of clean ° out of the stack at the top right.",
    ),
];

impl Scene for BagHouse {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BAG_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let bx = w * 22 / 100;
        let bw = w * 52 / 100;
        let (top, bot) = (4, h - 10);
        titled_box(c, bx, top, bw, bot - top + 1, "baghouse");
        // inlet duct from the left
        let in_y = bot - 3;
        let inlet = Path::new(&[(1, in_y), (bx, in_y)]);
        inlet.draw(c);
        c.text(1, in_y - 1, "from furnace lid");
        let n = ((bw - 8) / 8).clamp(3, 6);
        let gap = (bw - 6) / n;
        let bag_top = top + 4;
        let bag_bot = bot - 4;
        let cake_max = ((bag_bot - bag_top) as f32 * 0.75) as i32;
        let cake = match t.beat {
            0 => 0,
            1 => (cake_max as f32 * ease_in_out(t.local)) as i32,
            2 => {
                (cake_max as f32 * (1.0 - ease_in_out((t.local * 1.6 - 0.3).clamp(0.0, 1.0))))
                    as i32
            }
            _ => 0,
        };
        let mut xs = Vec::new();
        for i in 0..n {
            let x = bx + 4 + gap / 2 + i * gap;
            xs.push(x);
            c.vline(x, bag_top, bag_bot - bag_top, '║');
            for k in 0..cake {
                c.put(x - 1, bag_bot - 1 - k, '▒');
                c.put(x + 1, bag_bot - 1 - k, '▒');
            }
            if t.beat == 2 && (0.05..0.45).contains(&t.local) {
                c.put(x, bag_top - 1, '↓');
                c.put(x, bag_top, '↓');
            }
        }
        // dirty gas: fume stops at the first bag, gas goes through and up
        let dirty = Particles::new(81, 110, 2400);
        let reach = *xs.first().unwrap_or(&(bx + 6)) - 2;
        if t.beat <= 1 {
            dirty.each(t.ms, |p| {
                let x = lerp(1.0, reach as f32, (p.age * 1.4).min(1.0)) as i32;
                let y =
                    in_y - (p.rand(1) * 5.0) as i32 + ((p.age * 1.4 - 1.0).max(0.0) * 3.0) as i32;
                if p.rand(2) > 0.5 || x < bx {
                    c.put_if_blank(x, y, '·');
                } else {
                    c.put_if_blank(x, y, '°');
                }
            });
            Particles::new(82, 150, 2600).each(t.ms, |p| {
                let x = bx + 5 + (p.rand(1) * (bw - 10) as f32) as i32;
                let y = lerp((bag_bot - 1) as f32, (top + 1) as f32, p.age);
                if t.beat == 1 {
                    c.put_if_blank(x, y as i32, '°');
                }
            });
        }
        // dust falling off the bags into the hopper
        if t.beat == 2 {
            Particles::new(83, 70, 1400).each(t.ms, |p| {
                let x = xs[(p.id as usize) % xs.len()] + (p.rand(1) * 3.0) as i32 - 1;
                let y = bag_bot - 2 + (p.age * (bot - bag_bot + 3) as f32) as i32;
                c.put_if_blank(x, y, '▒');
            });
        }
        // hopper funnel and silica bin
        let fy = bot + 1;
        let hx = bx + bw / 2;
        c.text(hx - 4, fy, "\\______/");
        Path::new(&[(hx, fy + 1), (hx, fy + 2)]).draw(c);
        titled_box(c, hx - 6, fy + 3, 13, 5.min(h - fy - 3), "silica");
        let level = match t.beat {
            0 => 1,
            1 => 1,
            2 => 1 + (2.0 * t.local) as i32,
            _ => 3,
        };
        for r in 0..level.min(3) {
            c.hline(hx - 5, fy + 6 - r, 11, '▒');
        }
        // stack on the clean side
        let sx = bx + bw - 6;
        c.vline(sx, 0, top, '║');
        c.text(sx + 2, 1, "stack");
        let stack = Path::new(&[(sx, top), (sx, 0)]);
        flow(c, &stack, t.ms, Particles::new(84, 380, 1400), |_| '°');
        c.text(bx + 3, top + 1, "clean side: gas leaves upward");
        c.text(bx + 3, bot - 1, "dirty side");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn scenes() -> Vec<(&'static str, Box<dyn Scene>)> {
        vec![
            ("cavity", Box::new(Cavity1)),
            ("crust", Box::new(CrustStoke)),
            ("tapping", Box::new(Tapping)),
            ("baghouse", Box::new(BagHouse)),
        ]
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        for (name, s) in scenes() {
            assert!(s.beats().len() >= 4, "{name}");
            for (i, b) in s.beats().iter().enumerate() {
                assert!(!b.caption.is_empty(), "{name} beat {i} caption");
                assert!(
                    !b.what.is_empty() && !b.look.is_empty(),
                    "{name} beat {i} note"
                );
            }
        }
    }

    #[test]
    fn zooms_scale_without_panicking_and_move() {
        for (name, _) in scenes() {
            for (w, h) in [(50, 10), (80, 26), (130, 40), (240, 80)] {
                let mut p = Player::new(
                    scenes().into_iter().find(|(n, _)| *n == name).unwrap().1,
                    Instant::now(),
                );
                p.fit(w, h);
                let mut seen = std::collections::HashSet::new();
                for ms in (0..p.loop_ms()).step_by(173) {
                    let s = p.shot_at(ms);
                    assert_eq!(s.lines.len(), p.height());
                    assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                    seen.insert(s.lines.join("\n"));
                }
                assert!(seen.len() > 20, "{name} {w}x{h}: {} distinct", seen.len());
            }
        }
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn each_zoom_shows_its_story() {
        let mk = |s: Box<dyn Scene>| {
            let mut p = Player::new(s, Instant::now());
            p.fit(120, 38);
            p
        };
        let mut p = mk(Box::new(Cavity1));
        assert!(at(&mut p, 0, 0.5).contains("╚═╝"));
        assert!(at(&mut p, 2, 0.9).contains('≈'));
        let mut p = mk(Box::new(CrustStoke));
        let n = |s: &str| s.matches('▒').count();
        assert!(n(&at(&mut p, 3, 0.1)) > n(&at(&mut p, 0, 0.5)) + 20);
        assert!(at(&mut p, 3, 0.5).contains("▐███▌"));
        let mut p = mk(Box::new(Tapping));
        assert!(at(&mut p, 1, 0.9).contains('▷'));
        assert!(at(&mut p, 3, 0.5).contains("hood"));
        assert!(at(&mut p, 4, 0.9).contains("▐▇▇"));
        let mut p = mk(Box::new(BagHouse));
        assert!(at(&mut p, 1, 0.9).contains('▒'));
        assert!(at(&mut p, 2, 0.2).contains('↓'));
        assert!(at(&mut p, 0, 0.5).contains("baghouse"));
    }
}
