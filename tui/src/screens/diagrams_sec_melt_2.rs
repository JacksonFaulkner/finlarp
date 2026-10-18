// MELT + PULL section 2: the inside of a Czochralski puller, as a zoom-in close-up.
//
//   Chamber   water-cooled chamber under argon, the seed parked over the melt
//   Growth    seed lowered, then neck, shoulder and body grow as the shaft lifts; crystal and crucible turn oppositely
//   Interface the crucible lifts as the melt level drops, so the solid-melt interface stays at 1414 C
//   HotZone   graphite heater and felt, the heat shield, argon sweeping down and out the base with SiO
//
// Facts come from the section text: the COMSOL thermal model, and Wikipedia for the melt temperature.

use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, flicker, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

/// Seed bar row while parked above the melt.
const PARKED: i32 = 3;
/// Crystal stack heights in rows: dash neck, shoulder cone, and the body's maximum.
const NECK: i32 = 3;
const CONE: i32 = 3;
/// Half-width of the body in cells (9 cells across).
const HW: i32 = 4;
/// Half-widths of the crucible, graphite cup, heater, felt, heat shield and chamber.
const CRU_HW: i32 = 10;
const GRAPH_HW: i32 = 12;
const HEATER_HW: i32 = 14;
const FELT_HW: i32 = 16;
const SHIELD_HW: i32 = 6;
const CHAMBER_HW: i32 = 18;
/// How many rows the crucible lifts in beat 2 to hold the interface still.
const RISE: i32 = 2;

const ARGON: Particles = Particles::new(501, 300, 2600);
const OUTFLOW: Particles = Particles::new(502, 900, 2000);

const BEATS: &[Beat] = &[
    Beat::new(
        "a water-cooled chamber holds argon near 2500 Pa around the crucible and melt",
        BEAT_MS,
    )
    .note(
        "The puller is a sealed, water-cooled steel chamber filled with argon at about 2500 Pa (COMSOL model). The quartz crucible holds the melt inside a graphite cup, and the seed hangs parked above it.",
        "Argon ° and · drifting down the left wall of the chamber, the seed parked at the top, and the ≈ melt in the crucible.",
    )
    .detail(
        "The chamber sets the gas and pressure the melt sees. Argon is the carrier that takes SiO and CO away from the melt surface.",
        &[
            "PULL CHAMBER: water-cooled steel, argon at ~2500 Pa (COMSOL model)",
            "Argon in at the top, down past the crystal, out at the bottom (page text)",
            "Pull shaft rotates and lifts the oriented seed crystal (page text)",
        ],
    ),
    Beat::new(
        "the pull shaft lowers a seed, then the neck, shoulder and body form as it lifts",
        BEAT_MS,
    )
    .note(
        "The seed is lowered onto the melt, then the shaft lifts. The dash neck, the shoulder and the body form in turn, and the crystal and crucible turn in opposite senses.",
        "The shaft tip rising as the crystal grows upward in stages, with its ▓▒ stripes shifting as it turns.",
    )
    .detail(
        "The crystal is grown by lifting it out of the melt. Each stage depends on the one below it, so a failed neck ends the whole pull.",
        &[
            "Neck 2-4 mm; dislocations grow out of it (page text)",
            "Shoulder widens to 300 mm; body up to about 2 m (page text)",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
        ],
    ),
    Beat::new(
        "the crucible rises as the melt level drops, so the solid-melt interface stays at 1414 C",
        BEAT_MS,
    )
    .note(
        "As silicon freezes out, the melt level falls. The crucible is lifted on its shaft, which keeps the solid-melt interface at the same place.",
        "The melt surface row holding still while the crucible walls and floor move up two rows, with ≈ melt draining from the bottom.",
    )
    .detail(
        "A fixed interface keeps the freezing front flat, which keeps growth stable. The temperature at the interface sets where the crystal freezes.",
        &[
            "Solid-melt interface at 1414 C (page text, COMSOL model)",
            "Crucible lifted as the melt level drops so the interface stays put (page text)",
            "Quartz crucible holds the melt; graphite crucible surrounds it (page text)",
        ],
    ),
    Beat::new(
        "the heater and heat shield set the heat; argon carries SiO and CO out the base",
        BEAT_MS,
    )
    .note(
        "The graphite heater and its felt wrap the crucible, and a heat shield sits above the melt around the crystal. Argon sweeps down past the crystal and out the bottom, taking SiO and CO with it.",
        "The heater ▒ glowing, the ║ shield around the crystal, argon ° sweeping down the wall, and * SiO rising from the melt.",
    )
    .detail(
        "The hot zone sets the temperature the crystal sees, and the argon path decides what leaves the melt surface.",
        &[
            "Graphite heater around the crucible: 310 kW in the COMSOL model (page text)",
            "Graphite felt insulation outside the heater (page text)",
            "Heat shield above the melt around the crystal (page text)",
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
        let p = Puller::new(c);
        let g = growth(t, p.body_max);
        let rise = crucible_rise(t);
        draw_chamber(c, &p, t);
        draw_heater(c, &p, t);
        draw_crucible(c, &p, t, rise);
        if t.beat == 3 {
            draw_shield(c, &p, t);
        }
        let top = draw_crystal(c, &p, t, &g);
        draw_shaft(c, &p, t, &g, top);
        draw_labels(c, &p, t, &g);
    }
}

pub struct Section;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Rows and axis of the puller for one canvas size.
struct Puller {
    cx: i32,
    h: i32,
    /// Melt surface row.
    mel: i32,
    /// Crucible floor row, before any lift.
    bot: i32,
    /// Most body rows that still fit above the melt.
    body_max: i32,
}

impl Puller {
    fn new(c: &Canvas) -> Self {
        let (w, h) = dims(c);
        let mel = h - 12;
        Self {
            cx: w / 2,
            h,
            mel,
            bot: h - 6,
            body_max: (mel - 4 - NECK - CONE).clamp(3, 9),
        }
    }
}

/// How much of each crystal section exists at this moment.
#[derive(Clone, Copy)]
struct Growth {
    neck: i32,
    cone: i32,
    body: i32,
}

fn growth(t: &Time, body_max: i32) -> Growth {
    let e = |f: f32| ease_in_out(f.clamp(0.0, 1.0));
    let grow = |v: i32, f: f32| (v as f32 * f).round() as i32;
    match t.beat {
        0 => Growth {
            neck: 0,
            cone: 0,
            body: 0,
        },
        1 => Growth {
            neck: grow(NECK, e((t.local - 0.3) / 0.2)),
            cone: grow(CONE, e((t.local - 0.5) / 0.15)),
            body: grow(body_max, e((t.local - 0.65) / 0.35)),
        },
        _ => Growth {
            neck: NECK,
            cone: CONE,
            body: body_max,
        },
    }
}

/// Crucible lift in rows: rises during beat 2, then holds.
fn crucible_rise(t: &Time) -> i32 {
    match t.beat {
        2 => lerp(0.0, RISE as f32, ease_in_out(t.local)).round() as i32,
        3 => RISE,
        _ => 0,
    }
}

fn draw_chamber(c: &mut Canvas, p: &Puller, t: &Time) {
    titled_box(
        c,
        p.cx - CHAMBER_HW,
        0,
        2 * CHAMBER_HW + 1,
        p.h - 2,
        "PULL CHAMBER, water-cooled",
    );
    // argon enters at the top, sweeps down past the crystal, and leaves the base
    let sweep = Path::new(&[(p.cx - CHAMBER_HW + 1, 1), (p.cx - CHAMBER_HW + 1, p.h - 4)]);
    flow(c, &sweep, t.ms, ARGON, |q| {
        if q.rand(1) > 0.5 { '°' } else { '·' }
    });
}

fn draw_heater(c: &mut Canvas, p: &Puller, t: &Time) {
    // felt stays grey; the heater glows once the melt is hot
    let glow = if t.beat == 0 || flicker(t.ms, 200, 5, 3) == 0 {
        '░'
    } else {
        '▒'
    };
    for x in [p.cx - FELT_HW, p.cx + FELT_HW] {
        c.vline(x, p.mel - 6, p.bot - p.mel + 8, '░');
    }
    for x in [p.cx - HEATER_HW, p.cx + HEATER_HW] {
        c.vline(x, p.mel - 5, p.bot - p.mel + 6, glow);
    }
    c.hline(p.cx - HEATER_HW, p.bot + 1, 2 * HEATER_HW + 1, glow);
}

fn draw_crucible(c: &mut Canvas, p: &Puller, t: &Time, rise: i32) {
    let (cl, cr) = (p.cx - CRU_HW, p.cx + CRU_HW);
    let (gl, gr) = (p.cx - GRAPH_HW, p.cx + GRAPH_HW);
    let floor = p.bot - rise;
    let top = p.mel - 5 - rise;
    // graphite cup around the quartz crucible; both sit on the crucible shaft
    c.vline(gl, top - 1, floor + 2 - top, '┃');
    c.vline(gr, top - 1, floor + 2 - top, '┃');
    c.hline(gl, floor + 1, gr - gl + 1, '━');
    // quartz crucible walls and floor
    c.vline(cl, top, floor - top, '│');
    c.vline(cr, top, floor - top, '│');
    c.hline(cl, floor, cr - cl + 1, '─');
    c.put(cl, floor, '└');
    c.put(cr, floor, '┘');
    // melt fills the quartz crucible from the surface down to the floor
    for y in p.mel..floor {
        for x in cl + 1..cr {
            let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
                '≈'
            } else {
                '~'
            };
            c.put(x, y, ch);
        }
    }
}

fn draw_shield(c: &mut Canvas, p: &Puller, t: &Time) {
    for x in [p.cx - SHIELD_HW, p.cx + SHIELD_HW] {
        c.vline(x, p.mel - 10, 9, '║');
    }
    c.hline(p.cx - SHIELD_HW, p.mel - 10, 2 * SHIELD_HW + 1, '═');
    // SiO leaves the melt surface and rises past the shield, out of the chamber
    let sio = Path::new(&[(p.cx + 8, p.mel - 1), (p.cx + 8, 2)]);
    flow(c, &sio, t.ms, OUTFLOW, |q| {
        if q.rand(1) > 0.5 { '*' } else { '·' }
    });
}

/// One crystal row, hatched so the stripes shift while the crystal turns.
fn stripes(c: &mut Canvas, cx: i32, y: i32, hw: i32, t: &Time) {
    for x in cx - hw..=cx + hw {
        let ch = if (x + (t.ms / 300) as i32).rem_euclid(2) == 0 {
            '▓'
        } else {
            '▒'
        };
        c.put(x, y, ch);
    }
}

/// Draws the crystal up from the melt and returns its top row.
fn draw_crystal(c: &mut Canvas, p: &Puller, t: &Time, g: &Growth) -> i32 {
    let mut y = p.mel - 1;
    for _ in 0..g.neck {
        stripes(c, p.cx, y, 1, t);
        y -= 1;
    }
    for k in 0..g.cone {
        let hw = (HW as f32 * (k + 1) as f32 / CONE as f32).round() as i32;
        stripes(c, p.cx, y, hw, t);
        y -= 1;
    }
    for _ in 0..g.body {
        stripes(c, p.cx, y, HW, t);
        y -= 1;
    }
    y + 1
}

/// Pull shaft and seed: parked above the melt, lowered to the melt, then riding the crystal top.
fn draw_shaft(c: &mut Canvas, p: &Puller, t: &Time, g: &Growth, top: i32) {
    let bar = if g.neck > 0 {
        top - 1
    } else if t.beat == 1 {
        let e = ease_in_out((t.local / 0.3).clamp(0.0, 1.0));
        lerp(PARKED as f32, (p.mel - 2) as f32, e).round() as i32
    } else {
        PARKED
    };
    c.vline(p.cx, 1, bar - 1, '│');
    c.hline(p.cx - 2, bar, 5, '▀');
}

fn draw_labels(c: &mut Canvas, p: &Puller, t: &Time, g: &Growth) {
    let lx = p.cx + 20;
    match t.beat {
        0 => {
            c.label(lx, 4, "argon ~2500 Pa");
            c.label(lx, 6, "water-cooled steel");
            c.label(lx, p.mel - 1, "quartz crucible");
        }
        1 => {
            c.label(lx, 3, "shaft turns + lifts");
            if g.neck > 0 {
                c.label(lx, 5, "neck 2-4 mm");
            }
            if g.cone > 0 {
                c.label(lx, 7, "shoulder to 300 mm");
            }
            if g.body > 0 {
                c.label(lx, 9, "body up to ~2 m");
            }
            c.label(lx, p.mel - 3, "crystal ↻ 5 rpm");
            c.label(lx, p.bot - 1, "crucible ↺ 5 rpm");
        }
        2 => {
            c.label(lx, p.mel, "interface 1414 C");
            c.label(lx, p.mel + 2, "crucible lifts");
            c.label(lx, p.mel + 4, "melt level drops");
        }
        _ => {
            c.label(lx, p.mel - 10, "heat shield");
            c.label(lx, p.mel - 4, "graphite heater");
            c.label(lx, p.h - 5, "argon out the base");
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

    fn player() -> Player {
        Player::new(Box::new(Section), Instant::now())
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn four_beats_all_annotated() {
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
    fn draws_at_sizes_and_times_without_panicking() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = player();
            p.fit(w, h);
            let mid = BEAT_MS + BEAT_MS / 2;
            let last = BEAT_MS * (BEATS.len() as u64 - 1) + BEAT_MS / 2;
            for ms in [0, mid, last] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(211) {
                seen.insert(p.shot_at(ms).lines.join("\n"));
            }
            assert!(seen.len() > 15, "{w}x{h}: {}", seen.len());
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        let mut p = player();
        p.fit(120, 38);
        assert!(at(&mut p, 0, 0.5).contains("argon ~2500 Pa"));
        assert!(at(&mut p, 1, 0.99).contains("neck 2-4 mm"));
        assert!(at(&mut p, 1, 0.99).contains("body up to ~2 m"));
        assert!(at(&mut p, 2, 0.5).contains("interface 1414 C"));
        assert!(at(&mut p, 2, 0.5).contains("crucible lifts"));
        assert!(at(&mut p, 3, 0.5).contains("heat shield"));
        assert!(at(&mut p, 3, 0.5).contains("argon out the base"));
    }
}
