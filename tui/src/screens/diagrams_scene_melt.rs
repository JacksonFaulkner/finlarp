// MELT + PULL page, overview: the Czochralski puller as one animation, in time order: load polysilicon and
// dopant into a quartz crucible, melt it under argon, dip a seed and pull a thin dash neck, flare the shoulder,
// grow the body, taper the tail and lift the crystal clear. Zooms (a-c) open the dash neck, the melt convection
// with its magnetic field, and the hot zone with its argon sweep.
//
// Sources: COMSOL, thermal analysis of a Czochralski furnace (model); Wikipedia, Czochralski method; US 6,866,713
// (dash neck); US 7,179,330 (dash-free neck); Journal of Synthetic Crystals 52(4) (2023), 300 mm pull-rate study.

use super::diagrams_scene_melt_zoom as zoom;
use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, lerp, noise};

const BEAT_MS: u64 = 5200;
pub const MIN_W: u16 = 100;
pub const MIN_H: u16 = 30;

const LOAD: usize = 0;
const MELT: usize = 1;
const SEED: usize = 2;
const SHOULDER: usize = 3;
const BODY: usize = 4;
const TAIL: usize = 5;

/// Crystal stack heights in rows: dash neck, shoulder cone, end cone, and how far the tail lifts off the melt.
const NECK: i32 = 3;
const CONE: i32 = 3;
const TAIL_LEN: i32 = 2;
const LIFT: i32 = 3;
/// Half-width of the body in cells (9 cells across).
const HW: i32 = 4;
/// Half-width of the crucible and the chamber.
const CRU_HW: i32 = 10;
const GRAPH_HW: i32 = 11;
const HEATER_HW: i32 = 13;
const SHIELD_HW: i32 = 15;
const CHAMBER_HW: i32 = 16;

const BEATS: &[Beat] = &[
    Beat::new(
        "polysilicon chunks and a measured dose of dopant are loaded into a quartz crucible",
        BEAT_MS,
    )
    .note(
        "The charge is the electronic-grade polysilicon from the POLYSILICON page, broken into chunks, plus dopant (boron or phosphorus) weighed to set the target resistivity. It is packed into a quartz crucible before the chamber is sealed.",
        "Chunks dropping in from the top and piling into the crucible, with a few · dopant specks mixed in.",
    )
    .detail(
        "The dopant mass sets the resistivity of the whole crystal. Any metal or carbon loaded here dissolves into the melt and cannot be removed later.",
        &[
            "Recharge: fresh undoped poly is added during the pull. It dilutes the dopant building up in the melt and refills it, so one crucible makes a longer crystal",
            "Liquid feed (continuous Czochralski) would keep the melt steady, but moving molten silicon adds contamination and cooling risk, so solid recharge is the usual choice",
            "Segregation: silicon freezes out but dopant stays in the liquid, so the melt gets richer and the tail is more heavily doped than the head",
            "A 300 mm pull consumes the charge as one batch",
        ],
    ),
    Beat::new(
        "the charge melts at about 1414 C under flowing argon, then holds just above freezing",
        BEAT_MS,
    )
    .note(
        "A graphite heater brings the charge above the silicon melting point. Argon flows through the chamber to carry away SiO and CO and keep oxygen low. The melt is held steady so the seed can touch it at the right temperature.",
        "Chunks shrinking as the melt level rises, the ≈ surface settling flat, and the heater glow around the crucible.",
    )
    .detail(
        "A stable, flat melt is needed before seeding. Rushing the seed causes temperature drift and a diameter that wanders.",
        &[
            "COMSOL model: melt near 1414 C, contact 1403-1407.5 C, argon 100 L/min at 2500 Pa",
            "Wikipedia quotes 1425 C for semiconductor-grade silicon, so the exact figure depends on the source",
            "The model needs about 400 minutes to reach a steady contact temperature",
            "Heating to 1414 C in argon needs a graphite heater (about 310 kW in the model); small power changes move the interface",
        ],
    ),
    Beat::new(
        "the seed touches the melt; a thin dash neck is pulled fast to purge dislocations",
        BEAT_MS,
    )
    .note(
        "A small oriented seed crystal is lowered until it touches the melt. The contact shock creates dislocations, so the operator pulls a thin neck, 2-4 mm across, at high speed. The dislocations slide out through the neck surface before the body starts.",
        "The seed descending, the neck thin and rising, and dislocation marks / leaving through its sides.",
    )
    .detail(
        "Everything hangs from this neck, so it is the most failure-prone step. A neck break drops the whole crystal into hot silicon.",
        &[
            "Neck pulled up to about 6 mm/min (US 6,866,713)",
            "About 100-125 mm of neck is needed to purge dislocations",
            "Dash-necked crystals are limited to about 100 kg (patent text)",
        ],
    ),
    Beat::new(
        "shoulder: the melt is cooled slightly and the crystal flares out to 300 mm",
        BEAT_MS,
    )
    .note(
        "The temperature is trimmed down and the pull slowed so the crystal widens along a cone to full diameter. A sudden jump from the thin neck would be a sharp corner that concentrates stress and can start new dislocations, so the cone is gradual. Growth releases latent heat at the interface, so the temperature loop, not just pull speed, now sets the diameter.",
        "The narrow neck opening into a cone that widens to full width.",
    )
    .detail(
        "Too steep a flare can start new dislocations or twin the crystal. Dislocations that survived the neck can multiply as it widens.",
        &[
            "Target diameter is 300 mm for modern wafers",
            "The shoulder is later cropped off as scrap",
            "A failure here wastes the whole charge",
        ],
    ),
    Beat::new(
        "body: grows at about 1.0-1.6 mm a minute while the crucible rises with the falling melt",
        BEAT_MS,
    )
    .note(
        "The saleable body grows as the seed rises. Crystal and crucible counter-rotate to stir the melt, so temperature and dopant stay even and the freezing front stays flat. The crucible is lifted as the melt level drops so the interface stays put. Heater power is trimmed to hold the diameter.",
        "The crystal lengthening upward, the crucible rising slightly, and the melt level staying put.",
    )
    .detail(
        "The freezing front must stay flat. A faster pull pushes it convex or concave, locks in stress and defects, and shifts oxygen. Yield is set here.",
        &[
            "1.0 mm/min of 300 mm crystal is about 9.9 kg/h; 1.6 mm/min is about 15.8 kg/h",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
            "Oxygen: slower crucible spin or a shallower melt cuts oxygen pulled off the quartz; faster argon and lower pressure carry SiO away. Both cost uniformity and output",
            "Oxygen is a tradeoff: zero is not the goal, and some oxygen helps trap defects during device making (general knowledge, not on the page)",
            "Up to about 2 m long and several hundred kg (Wikipedia)",
        ],
    ),
    Beat::new(
        "tail: tapers to an end cone, then the crystal is lifted clear of the melt to cool",
        BEAT_MS,
    )
    .note(
        "At the end the diameter is tapered and the crystal is lifted off the melt in steps while it cools. An abrupt lift-off is a thermal shock, the same stress that makes dislocations, and it can send slip dislocations back up into the body. The taper makes the release gradual.",
        "The top of the crystal narrowing into a cone, then the whole crystal rising clear of the surface.",
    )
    .detail(
        "The tail is the most contaminated zone, since segregation pushes dopants and metals into the last liquid to freeze. It is cropped off in the INGOT step.",
        &[
            "A tail-growth method suppresses slip dislocations (US 9,988,736)",
            "The finished rod is the INGOT node",
            "The charge left in the crucible and the tail are non-wafer silicon",
        ],
    ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the dash neck",
        build: || -> Box<dyn Scene> { Box::new(zoom::Neck) },
    },
    Zoom {
        key: 'b',
        label: "melt convection and the magnetic field",
        build: || -> Box<dyn Scene> { Box::new(zoom::Convection) },
    },
    Zoom {
        key: 'c',
        label: "the hot zone and the argon sweep",
        build: || -> Box<dyn Scene> { Box::new(zoom::HotZone) },
    },
];

const CHARGE: Particles = Particles::new(201, 450, 1500);
const ARGON: Particles = Particles::new(202, 300, 2600);

/// Positions of the puller parts for one canvas size.
struct Puller {
    cx: i32,
    x0: i32,
    x1: i32,
    h: i32,
    /// Melt surface row.
    mel: i32,
    /// Crucible floor row.
    bot: i32,
    /// Most body rows that still fit above the melt with the tail and lift.
    body_max: i32,
}

impl Puller {
    fn new(w: usize, h: usize) -> Self {
        let (w, h) = (w.max(MIN_W as usize) as i32, h.max(MIN_H as usize) as i32);
        let cx = w * 2 / 5;
        let mel = h - 11;
        Self {
            cx,
            x0: cx - CHAMBER_HW,
            x1: cx + CHAMBER_HW,
            h,
            mel,
            bot: h - 8,
            body_max: (mel - 2 - NECK - CONE - TAIL_LEN - LIFT).clamp(3, 9),
        }
    }
}

/// How much of each crystal section exists at this moment.
struct Stack {
    neck: i32,
    cone: i32,
    body: i32,
    tail: i32,
    lift: i32,
}

fn stack(t: &Time, body_max: i32) -> Stack {
    let e = |f: f32| ease_in_out(f.clamp(0.0, 1.0));
    let grow = |v: i32, f: f32| (v as f32 * f).round() as i32;
    match t.beat {
        SEED => Stack {
            neck: grow(NECK, e((t.local - 0.3) / 0.7)),
            cone: 0,
            body: 0,
            tail: 0,
            lift: 0,
        },
        SHOULDER => Stack {
            neck: NECK,
            cone: grow(CONE, e(t.local)),
            body: 0,
            tail: 0,
            lift: 0,
        },
        BODY => Stack {
            neck: NECK,
            cone: CONE,
            body: grow(body_max, e(t.local)),
            tail: 0,
            lift: 0,
        },
        TAIL => Stack {
            neck: NECK,
            cone: CONE,
            body: body_max,
            tail: grow(TAIL_LEN, e(t.local / 0.6)),
            lift: grow(LIFT, e((t.local - 0.6) / 0.4)),
        },
        _ => Stack {
            neck: 0,
            cone: 0,
            body: 0,
            tail: 0,
            lift: 0,
        },
    }
}

impl Stack {
    fn height(&self) -> i32 {
        self.neck + self.cone + self.body + self.tail
    }
}

pub struct Melt;

impl Scene for Melt {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let p = Puller::new(c.width(), c.height());
        let s = stack(t, p.body_max);
        draw_chamber(c, &p, t);
        draw_charge(c, &p, t);
        draw_crystal(c, &p, t, &s);
        draw_labels(c, &p, t, &s);
        draw_dopant(c, &p, t);
    }
}

fn draw_chamber(c: &mut Canvas, p: &Puller, t: &Time) {
    titled_box(c, p.x0, 0, p.x1 - p.x0 + 1, p.h - 2, "PULL CHAMBER, argon");
    // argon sweeps down the wall, past the crystal, and out the base
    let sweep = Path::new(&[(p.x0 + 2, 1), (p.x0 + 2, p.h - 5)]);
    sweep.draw(c);
    flow(c, &sweep, t.ms, ARGON, |q| {
        if q.rand(1) > 0.5 { '°' } else { '·' }
    });
    // heat shield: the outer layer around the hot zone, from the reference cutaway
    for x in [p.cx - SHIELD_HW, p.cx + SHIELD_HW] {
        c.vline(x, p.mel - 7, p.bot - p.mel + 8, '┊');
    }
    // graphite heater beside the graphite cup, glowing once the melt is hot
    let glow = if t.beat >= MELT { '▒' } else { '░' };
    for x in [p.cx - HEATER_HW, p.cx + HEATER_HW] {
        c.vline(x, p.mel - 5, p.bot - p.mel + 7, glow);
    }
    // graphite crucible (susceptor) cupping the quartz crucible
    let (gl, gr) = (p.cx - GRAPH_HW, p.cx + GRAPH_HW);
    c.vline(gl, p.mel - 6, p.bot - p.mel + 8, '┃');
    c.vline(gr, p.mel - 6, p.bot - p.mel + 8, '┃');
    c.hline(gl, p.bot + 1, gr - gl + 1, '━');
    // quartz crucible: the melt sits in it
    let cl = p.cx - CRU_HW;
    let cr = p.cx + CRU_HW;
    c.vline(cl, p.mel - 6, p.bot - p.mel + 7, '│');
    c.vline(cr, p.mel - 6, p.bot - p.mel + 7, '│');
    c.hline(cl, p.bot, cr - cl + 1, '─');
    c.put(cl, p.bot, '└');
    c.put(cr, p.bot, '┘');
    // spill tray under the crucible, electrodes through the base plate
    c.hline(p.x0 + 2, p.bot + 3, p.x1 - p.x0 - 3, '▁');
    for x in [p.cx - HEATER_HW, p.cx + HEATER_HW] {
        c.vline(x, p.h - 4, 2, '║');
    }
    // spindle that turns and lifts the crucible
    c.vline(p.cx, p.bot + 2, p.h - 4 - p.bot - 2, '║');
    c.hline(p.x0 + 1, p.h - 4, p.x1 - p.x0 - 1, '═');
}

fn draw_charge(c: &mut Canvas, p: &Puller, t: &Time) {
    let (cl, cr) = (p.cx - CRU_HW + 1, p.cx + CRU_HW - 1);
    if t.beat == LOAD {
        let stream = Path::new(&[(p.cx, 4), (p.cx, p.mel - 5)]);
        flow(c, &stream, t.ms, CHARGE, |q| {
            if q.rand(1) > 0.3 { '▪' } else { '·' }
        });
    }
    // chunks shrink away as the melt rises
    let keep = match t.beat {
        LOAD => 1.0,
        MELT => 1.0 - ease_in_out(t.local),
        _ => 0.0,
    };
    for y in p.mel - 4..p.bot {
        for x in cl..=cr {
            if noise(7, (x * 131 + y) as u64) < keep {
                c.put(x, y, '▪');
            }
        }
    }
    // melt fills the crucible from the floor up to the surface
    let level = match t.beat {
        LOAD => p.bot,
        MELT => lerp((p.bot - 1) as f32, p.mel as f32, ease_in_out(t.local)).round() as i32,
        _ => p.mel,
    };
    for y in level..p.bot {
        for x in cl..=cr {
            let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
                '≈'
            } else {
                '~'
            };
            c.put_if_blank(x, y, ch);
        }
    }
}

fn draw_crystal(c: &mut Canvas, p: &Puller, t: &Time, s: &Stack) {
    let bottom = p.mel - 1 - s.lift;
    let mut y = bottom;
    for _ in 0..s.neck {
        c.put(p.cx, y, '▓');
        y -= 1;
    }
    for k in 0..s.cone {
        let hw = (HW as f32 * (k + 1) as f32 / s.cone as f32).round() as i32;
        hrow(c, p.cx, y, hw);
        y -= 1;
    }
    for _ in 0..s.body {
        hrow(c, p.cx, y, HW);
        y -= 1;
    }
    for k in 0..s.tail {
        let hw = (HW as f32 * (1.0 - (k + 1) as f32 / (s.tail + 1) as f32)).round() as i32;
        hrow(c, p.cx, y, hw);
        y -= 1;
    }
    // pull shaft and seed: parked above the melt, lowered to touch it, then following the crystal top
    let top = y + 1;
    let tip = match t.beat {
        LOAD | MELT => 5,
        SEED if s.neck == 0 => {
            lerp(5.0, (p.mel - 1) as f32, ease_in_out(t.local / 0.3)).round() as i32
        }
        _ => top,
    };
    c.vline(p.cx, 1, tip - 1, '│');
    c.hline(p.cx - 2, tip - 1, 5, '▀');
}

/// One crystal row: a single cell for the neck, otherwise `hw` cells either side of the axis.
fn hrow(c: &mut Canvas, cx: i32, y: i32, hw: i32) {
    if hw == 0 {
        c.put(cx, y, '▓');
    } else {
        c.hline(cx - hw, y, 2 * hw + 1, '▓');
    }
}

fn draw_labels(c: &mut Canvas, p: &Puller, t: &Time, s: &Stack) {
    let bottom = p.mel - 1 - s.lift;
    let lx = p.x1 + 2;
    c.text(lx, 3, "pull shaft: rotates + lifts");
    c.text(lx, 5, "argon 2500 Pa, swept down");
    c.text(lx, p.mel - 5, "crystal ↻  crucible ↺");
    c.text(lx, p.mel - 2, "melt ~1414 C");
    c.text(lx, p.mel - 7, "heat shield");
    c.text(lx, p.bot - 1, "quartz crucible");
    c.text(lx, p.bot + 1, "graphite crucible (cup)");
    c.text(lx, p.bot + 3, "spill tray, electrodes");
    c.text(lx, p.bot + 5, "graphite heater (310 kW model)");
    let cx = p.cx + 6;
    match t.beat {
        SEED => c.label(cx, bottom - 1, "neck 2-4 mm"),
        SHOULDER => c.label(cx, bottom - s.neck - 1, "shoulder"),
        BODY => c.label(cx, bottom - s.neck - s.cone - s.body / 2, "body 300 mm"),
        TAIL => c.label(cx, bottom - s.height() + 1, "tail"),
        _ => {}
    }
}

/// Dopant in the melt, relative to the loaded dose (1.0x). Silicon freezes out and the dopant stays
/// behind, so it climbs through the body; recharge (undoped poly) dilutes it; the tail is the heaviest.
fn dopant_level(t: &Time) -> f32 {
    match t.beat {
        BODY if t.local < 0.5 => lerp(1.0, 1.43, ease_in_out(t.local / 0.5)),
        BODY if t.local < 0.6 => lerp(1.43, 1.0, ease_in_out((t.local - 0.5) / 0.1)),
        BODY => lerp(1.0, 1.7, ease_in_out((t.local - 0.6) / 0.4)),
        TAIL => lerp(1.7, 2.5, ease_in_out(t.local)),
        _ => 1.0,
    }
}

/// The dopant gauge under the labels, with a note while recharge dilutes the melt.
fn draw_dopant(c: &mut Canvas, p: &Puller, t: &Time) {
    let conc = dopant_level(t);
    const CELLS: usize = 12;
    let fill = ((conc / 2.5).clamp(0.0, 1.0) * CELLS as f32).round() as usize;
    let bar = format!("{}{}", "█".repeat(fill), "░".repeat(CELLS - fill));
    let lx = p.x1 + 2;
    c.text(lx, 7, &format!("dopant in melt {bar} {conc:.1}x"));
    if t.beat == BODY && (0.5..0.6).contains(&t.local) {
        c.text(lx, 8, "recharge: undoped poly dilutes");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn player() -> Player {
        Player::new(Box::new(Melt), Instant::now())
    }

    fn at_beat(p: &mut Player, beat: usize, frac: f32) -> Vec<String> {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
    }

    fn has(ls: &[String], s: &str) -> bool {
        ls.iter().any(|l| l.contains(s))
    }

    #[test]
    fn six_beats_three_zooms_all_annotated() {
        let p = player();
        assert_eq!(p.loop_ms(), BEAT_MS * 6);
        assert_eq!(p.zooms().iter().map(|z| z.key).collect::<String>(), "abc");
        for (i, b) in BEATS.iter().enumerate() {
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
    fn crystal_grows_then_lifts_clear() {
        let mut p = player();
        p.fit(120, 36);
        let cells = |l: &[String]| l.iter().map(|r| r.matches('▓').count()).sum::<usize>();
        let neck = cells(&at_beat(&mut p, SEED, 0.99));
        let body = cells(&at_beat(&mut p, BODY, 0.99));
        assert!(body > neck + 20, "{neck} -> {body}");
        let lifted = at_beat(&mut p, TAIL, 0.99);
        assert!(has(&lifted, "tail"));
        // the tail adds a short taper (10 cells over two rows) on top of the full body
        assert!(
            cells(&lifted) <= cells(&at_beat(&mut p, BODY, 0.99)) + 10,
            "tail adds only its taper"
        );
    }

    #[test]
    fn every_stage_is_on_screen() {
        let mut p = player();
        p.fit(120, 36);
        assert!(has(&at_beat(&mut p, LOAD, 0.5), "quartz crucible"));
        assert!(has(&at_beat(&mut p, MELT, 0.9), "melt ~1414 C"));
        assert!(has(&at_beat(&mut p, SEED, 0.9), "neck 2-4 mm"));
        assert!(has(&at_beat(&mut p, SHOULDER, 0.9), "shoulder"));
        assert!(has(&at_beat(&mut p, BODY, 0.9), "body 300 mm"));
        assert!(has(&at_beat(&mut p, TAIL, 0.9), "tail"));
        assert!(has(&at_beat(&mut p, LOAD, 0.5), "crystal ↻  crucible ↺"));
        assert!(has(&at_beat(&mut p, LOAD, 0.5), "argon 2500 Pa"));
        assert!(has(&at_beat(&mut p, BODY, 0.9), "dopant in melt"));
        assert!(has(&at_beat(&mut p, BODY, 0.55), "recharge"));
        assert!(!has(&at_beat(&mut p, BODY, 0.9), "recharge"));
        for want in ["heat shield", "graphite crucible (cup)", "spill tray"] {
            assert!(has(&at_beat(&mut p, MELT, 0.5), want), "missing {want}");
        }
    }

    #[test]
    fn scales_without_panicking_and_moves() {
        for (w, h) in [(60, 10), (100, 30), (140, 40), (230, 70)] {
            let mut p = player();
            p.fit(w, h);
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(211) {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                seen.insert(s.lines.join("\n"));
            }
            assert!(seen.len() > 20, "{w}x{h}: {}", seen.len());
        }
    }
}
