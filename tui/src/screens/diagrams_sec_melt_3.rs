// MELT + PULL section 3, "The physics and chemistry": animated close-up in the zoom template.
// Growth at the freezing point, mass flow from the pull rate, oxygen from the quartz crucible, and dopant segregation.
//
// Sources: COMSOL, thermal analysis of a Czochralski furnace (model); Wikipedia, Czochralski method; textbook values
// (density 2.33 g/cm3, SiO2 + Si to 2SiO) are marked as such in the page text.

use crate::ui::anim::shapes::{Path, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, lerp, noise};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

/// Half-width of the quartz crucible in cells.
const CRU_HW: i32 = 12;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Melt from the surface row down to the crucible floor, with a moving ripple.
fn melt(c: &mut Canvas, cx: i32, mel: i32, bot: i32, t: &Time) {
    for y in mel..bot {
        for x in cx - CRU_HW + 1..cx + CRU_HW {
            let ch = if (x + (t.ms / 400) as i32).rem_euclid(2) == 0 {
                '≈'
            } else {
                '~'
            };
            c.put(x, y, ch);
        }
    }
}

/// Quartz crucible walls and floor.
fn crucible(c: &mut Canvas, cx: i32, mel: i32, bot: i32, wall: char) {
    let (cl, cr) = (cx - CRU_HW, cx + CRU_HW);
    c.vline(cl, mel - 3, bot - mel + 3, wall);
    c.vline(cr, mel - 3, bot - mel + 3, wall);
    c.hline(cl, bot, cr - cl + 1, '─');
    c.put(cl, bot, '└');
    c.put(cr, bot, '┘');
}

/// One crystal row: a single cell for the neck, otherwise `hw` cells either side of the axis.
fn hrow(c: &mut Canvas, cx: i32, y: i32, hw: i32) {
    if hw == 0 {
        c.put(cx, y, '▓');
    } else {
        c.hline(cx - hw, y, 2 * hw + 1, '▓');
    }
}

// ---- 0: growth at the freezing point -----------------------------------------------

/// The seed lowers onto the melt, then atoms add to its base row by row in the seed's orientation.
fn growth(c: &mut Canvas, cx: i32, mel: i32, t: &Time) {
    let touch = 0.5;
    let rows = if t.local < touch {
        0
    } else {
        (6.0 * ease_in_out((t.local - touch) / (1.0 - touch))).round() as i32
    };
    let tip = if t.local < touch {
        lerp(2.0, (mel - 1) as f32, ease_in_out(t.local / touch)).round() as i32
    } else {
        mel - 1 - rows
    };
    c.vline(cx, 1, tip - 1, '│');
    c.hline(cx - 2, tip, 5, '▀');
    for k in 0..rows {
        hrow(c, cx, mel - 1 - k, 2);
    }
    if rows > 0 {
        // atoms attach at the freezing front, one on each side of the growing top row
        let front = mel - rows;
        let ch = if (t.ms / 250).is_multiple_of(2) {
            '▪'
        } else {
            '·'
        };
        c.put(cx - 3, front, ch);
        c.put(cx + 3, front, ch);
        c.label(cx + 6, front, "freezing front");
    }
    c.label(cx + CRU_HW + 2, mel, "melt ~1414 C");
}

// ---- 1: mass flow from the pull rate ----------------------------------------------

/// A 300 mm body rises one slice per minute. The slice mass is area x density x pull rate.
fn mass(c: &mut Canvas, cx: i32, mel: i32, t: &Time) {
    let rows = 4 + (5.0 * ease_in_out(t.local)).round() as i32;
    let top = mel - rows;
    for y in top..mel {
        hrow(c, cx, y, 4);
    }
    // the slice frozen in one minute: a band at the front, thicker when the pull is faster
    let fast = t.local >= 0.5;
    let band = if fast { 2 } else { 1 };
    for y in top..top + band {
        c.hline(cx - 5, y, 11, '═');
    }
    c.text(3, 2, "mass/h = v x A x density");
    c.text(3, 3, "density 2.33 g/cm3 (textbook)");
    c.label(cx + 7, top - 1, "A = 300 mm body");
    c.label(
        cx + 7,
        top + 2,
        if fast {
            "v = 1.6 mm/min"
        } else {
            "v = 1.0 mm/min"
        },
    );
    c.label(
        cx + 7,
        top + 4,
        if fast { "~15.8 kg/h" } else { "~9.9 kg/h" },
    );
}

// ---- 2: oxygen from the quartz crucible -------------------------------------------

/// The quartz wall dissolves into SiO. Most of it rises and leaves; some oxygen freezes into the crystal.
fn oxygen(c: &mut Canvas, cx: i32, mel: i32, bot: i32, t: &Time) {
    let rows = 7;
    let top = mel - rows;
    for y in top..mel {
        hrow(c, cx, y, 2);
    }
    if t.local > 0.6 {
        for y in top..mel {
            for x in cx - 2..=cx + 2 {
                if noise(9, (x * 131 + y) as u64) < 0.25 {
                    c.put(x, y, '·');
                }
            }
        }
        c.label(cx + 6, top - 1, "~1e18 O/cm3 frozen in");
    }
    let sio = Path::new(&[(cx - CRU_HW + 2, bot - 1), (cx - CRU_HW + 2, mel)]);
    flow(c, &sio, t.ms, Particles::new(601, 500, 1800), |_| '*');
    c.label(cx + CRU_HW + 2, mel - 2, "SiO2 + Si ──▶ 2SiO");
}

// ---- 3: dopant segregation --------------------------------------------------------

/// The crystal grows up out of a melt that keeps the dopant, so higher rows carry more of it.
fn segregation(c: &mut Canvas, cx: i32, mel: i32, t: &Time) {
    let rows = ((9.0 * ease_in_out(t.local)).round() as i32).max(1);
    for k in 0..rows {
        let ch = if k < 3 {
            '░'
        } else if k < 6 {
            '▒'
        } else {
            '▓'
        };
        for x in cx - 3..=cx + 3 {
            c.put(x, mel - 1 - k, ch);
        }
    }
    // dopant in the melt: more specks as the liquid gets richer
    let richer = 0.1 + 0.5 * t.local;
    for y in mel..mel + 3 {
        for x in cx - CRU_HW + 1..cx + CRU_HW {
            if noise(11, (x * 131 + y) as u64) < richer {
                c.put(x, y, '·');
            }
        }
    }
    c.text(3, 2, "solute prefers the liquid");
    c.text(3, 3, "melt gets richer as it freezes");
    c.label(cx + 6, mel - 1, "head: lighter");
    c.label(cx + 6, mel - 8, "tail: more doped");
}

// ---- scene ------------------------------------------------------------------------

const BEATS: &[Beat] = &[
    Beat::new(
        "growth: the seed touches the melt at its freezing point, and atoms attach in its orientation",
        BEAT_MS,
    )
    .note(
        "The seed is lowered until it touches the melt at the freezing point. Atoms attach at the solid-liquid front, in the same orientation as the seed, so pulling up extends one crystal.",
        "The seed coming down, then ▪ atoms at the front adding ▓ rows one at a time beneath it.",
    )
    .detail(
        "Matching the seed's orientation is what makes one single crystal instead of many grains.",
        &[
            "Melting point 1414 C in the COMSOL model",
            "1425 C on Wikipedia for semiconductor grade; sources differ by a few degrees",
            "Atoms attach in the seed's orientation (page text)",
        ],
    ),
    Beat::new(
        "mass flow: pull rate x cross-section x density is the silicon frozen per hour",
        BEAT_MS,
    )
    .note(
        "A 300 mm body frozen at a steady pull rate adds one slice per minute. The slice's volume is the cross-section times the pull rate, and its mass follows from the density.",
        "The body rising slice by slice, with a ═ band at the front; the rate label changes from 1.0 to 1.6 mm/min.",
    )
    .detail(
        "The pull rate sets how fast the crystal, and so the yield, comes out. The same arithmetic shows why faster pulls are worth the risk.",
        &[
            "300 mm body, 1.0 mm/min gives about 9.9 kg/h (computed on page)",
            "1.6 mm/min gives about 15.8 kg/h (computed on page)",
            "Density 2.33 g/cm3 is textbook",
        ],
    ),
    Beat::new(
        "oxygen: the quartz crucible dissolves into SiO, and some oxygen freezes into the crystal",
        BEAT_MS,
    )
    .note(
        "The melt dissolves the quartz wall, making SiO. Most of it evaporates, but some oxygen freezes into the crystal. Crucible rotation, melt depth, pull speed and magnetic fields tune how much.",
        "The crucible wall thinning to ░, * SiO rising from the wall, and · oxygen specks appearing in the crystal.",
    )
    .detail(
        "Oxygen is the main impurity the rotation and magnetic field are used to control. Too much makes the wafer brittle.",
        &[
            "SiO2 + Si to 2SiO; most SiO evaporates (textbook, unsourced)",
            "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
            "Rotation, melt depth, pull speed and magnetic fields tune oxygen (page text)",
        ],
    ),
    Beat::new(
        "segregation: the solute prefers the liquid, so the melt gets richer and the tail more doped",
        BEAT_MS,
    )
    .note(
        "Dopant such as boron or phosphorus prefers the liquid over the solid. As the crystal freezes out, the dopant stays behind, so the melt gets richer and each new slice carries more.",
        "The crystal shading from ░ at the head to ▓ at the tail, with · specks thickening in the melt below.",
    )
    .detail(
        "Segregation is why the tail of a crystal is the most doped and the most contaminated part.",
        &[
            "Boron or phosphorus is added to the melt (page text)",
            "The tail is more doped than the head (textbook, unsourced)",
            "The tail is cropped off in the INGOT step (page text)",
        ],
    ),
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
        let bot = h - 4;
        // the crucible wall dissolves once the oxygen beat starts
        let wall = if t.beat == 3 && t.local > 0.25 {
            '░'
        } else {
            '│'
        };
        melt(c, cx, mel, bot, t);
        crucible(c, cx, mel, bot, wall);
        match t.beat {
            0 => growth(c, cx, mel, t),
            1 => mass(c, cx, mel, t),
            2 => oxygen(c, cx, mel, bot, t),
            _ => segregation(c, cx, mel, t),
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
    fn every_beat_is_captioned_and_explained() {
        assert!(BEATS.len() >= 3);
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
    fn draws_at_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = player();
            p.fit(w, h);
            let end = p.loop_ms();
            for ms in [0, BEAT_MS / 2, 3 * BEAT_MS + BEAT_MS / 2, end - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        let mut p = player();
        p.fit(120, 38);
        let frames: Vec<String> = (0..BEATS.len()).map(|b| at(&mut p, b, 0.5)).collect();
        for i in 0..frames.len() {
            for j in i + 1..frames.len() {
                assert_ne!(frames[i], frames[j], "beats {i} and {j} look the same");
            }
        }
        assert!(at(&mut p, 0, 0.9).contains("freezing front"));
        assert!(at(&mut p, 1, 0.75).contains("1.6 mm/min"));
        assert!(at(&mut p, 2, 0.9).contains("2SiO"));
        assert!(at(&mut p, 3, 0.9).contains("tail: more doped"));
    }
}
