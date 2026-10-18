// MELT + PULL section 1: a rod of silicon pulled out of a melt, close up.
//
//   Rod   charge loaded and melted under argon, seed dipped and a neck pulled, the shoulder widens,
//         the body grows, then the tail tapers and the rod is lifted clear to cool

use crate::ui::anim::shapes::{Path, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

// rod profile, one row per unit of height
const NECK: i32 = 4;
const SHOULDER: i32 = 4;
const BODY_HW: i32 = 6;
const TAIL: i32 = 5;
const LIFT: i32 = 3;
const CHUNKS: i32 = 6;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Longest body that still leaves room above it for the shoulder, neck, seed and wire.
fn body_max(mel: i32) -> i32 {
    (mel - 8 - NECK - SHOULDER).max(2)
}

/// Melt glyph: alternating ripple that shifts with time.
fn melt_char(x: i32, y: i32, ms: u64) -> char {
    if (x + y + (ms / 400) as i32).rem_euclid(2) == 0 {
        '≈'
    } else {
        '~'
    }
}

/// Where poly chunk `k` lands in the crucible.
fn chunk_spot(cl: i32, bot: i32, k: i32) -> (i32, i32) {
    (cl + 3 + 4 * k, bot - 2 - (k % 2) * 2)
}

/// Half-width of the rod `d` rows above its lower end. The tail tapers the lowest rows to a point,
/// then the body, the shoulder narrowing up into the neck, and the neck (one cell wide).
fn half_width(d: i32, body: i32, shoulder: i32, tail: i32) -> i32 {
    if d < tail {
        return (BODY_HW * d + tail - 1) / tail;
    }
    if d < body {
        return BODY_HW;
    }
    let k = d - body;
    if k < shoulder {
        return (BODY_HW * (shoulder - k - 1) + shoulder - 1) / shoulder;
    }
    0
}

/// A crystal row: one cell for the neck, otherwise `hw` cells either side of the axis.
fn hrow(c: &mut Canvas, cx: i32, y: i32, hw: i32) {
    if hw == 0 {
        c.put(cx, y, '▓');
    } else {
        c.hline(cx - hw, y, 2 * hw + 1, '▓');
    }
}

/// The rod from its lower end at row `base` upward: body, then shoulder, then neck.
fn draw_rod(c: &mut Canvas, cx: i32, base: i32, body: i32, shoulder: i32, neck: i32, tail: i32) {
    for d in 0..body + shoulder + neck {
        hrow(c, cx, base - d, half_width(d, body, shoulder, tail));
    }
}

/// The seed on its pull wire; `y` is the seed's lower row, sitting directly on the rod.
fn draw_seed(c: &mut Canvas, cx: i32, y: i32) {
    c.vline(cx, 1, y - 2, '│');
    c.hline(cx - 2, y - 1, 5, '▀');
    c.hline(cx - 2, y, 5, '▓');
}

pub struct Rod;

const BEATS: &[Beat] = &[
    Beat::new(
        "poly chunks and dopant are loaded into the crucible",
        BEAT_MS,
    )
    .note(
        "The charge goes into the crucible: solid polysilicon chunks from POLYSILICON, with the dopant added alongside.",
        "Chunks ▪ dropping into the crucible, then · dopant dust settling above them.",
    )
    .detail(
        "The charge is where the rod starts. What goes in as poly and dopant is what the rod is made of.",
        &[
            "Charge is poly chunks from POLYSILICON plus dopant (section 1)",
            "LOAD is the first of six stages (section 1)",
            "The finished rod is the INGOT node (section 1)",
        ],
    ),
    Beat::new(
        "the charge melts into one liquid pool under argon, at about 1414 C",
        BEAT_MS,
    )
    .note(
        "Heat melts the chunks from the floor up into a single liquid pool. Argon fills the chamber above the melt.",
        "The liquid rising from the floor, the ▪ chunks melting away, and argon ° sweeping in across the top.",
    )
    .detail(
        "The melt is the source for the whole rod. Every later stage pulls from this one pool.",
        &[
            "MELT is about 1414 C, under argon (section 1)",
            "Poly and dopant go from solid chunks to one melt (section 1)",
            "MELT is the second stage, after LOAD (section 1)",
        ],
    ),
    Beat::new(
        "a seed is dipped into the melt and a thin neck is pulled, 2-4 mm across",
        BEAT_MS,
    )
    .note(
        "The seed comes down to touch the melt, then is pulled up to draw a thin neck out of the liquid.",
        "The seed lowering, * sparks at contact, then the neck growing up under the seed.",
    )
    .detail(
        "The neck is thin and comes before the shoulder, so the rod has a narrow start before it widens.",
        &[
            "SEED + NECK: a 2-4 mm neck (section 1)",
            "The neck is pulled before the shoulder (section 1)",
            "The seed is the top of the rod on the wire (section 1 diagram)",
        ],
    ),
    Beat::new(
        "the shoulder widens, then the body grows slowly to 300 mm",
        BEAT_MS,
    )
    .note(
        "Once the neck is set, the rod widens into a shoulder at its lower end, then the body grows at a steady, slow pace.",
        "The shoulder spreading out below the neck, then the body lengthening beneath it toward the melt.",
    )
    .detail(
        "The body is the part of the rod that carries the wafers. Growing it slowly keeps the diameter steady.",
        &[
            "SHOULDER: widen (section 1)",
            "BODY: 300 mm, slow (section 1)",
            "The body grows down from the shoulder to the melt (section 1 diagram)",
        ],
    ),
    Beat::new(
        "the tail tapers the end, and the rod is lifted clear of the melt to cool",
        BEAT_MS,
    )
    .note(
        "At the end the diameter is reduced into a tail. The rod is then lifted out of the melt so it can cool.",
        "The bottom of the rod narrowing to a point, and a gap opening between the rod and the melt.",
    )
    .detail(
        "The tail is the last stage. The cooled rod is the INGOT node that the rest of the chain works from.",
        &[
            "TAIL: taper, cool (section 1)",
            "TAIL is the sixth and last stage (section 1)",
            "The finished rod is the INGOT node (section 1)",
        ],
    ),
];

impl Scene for Rod {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cx = w / 2;
        let mel = h - 7;
        let bot = h - 2;
        let (cl, cr) = (cx - 16, cx + 16);
        let base = mel - 1;
        // crucible walls and floor, in every beat
        c.vline(cl, mel - 3, bot - mel + 3, '│');
        c.vline(cr, mel - 3, bot - mel + 3, '│');
        c.hline(cl, bot, cr - cl + 1, '─');
        c.put(cl, bot, '└');
        c.put(cr, bot, '┘');
        // melt: empty while loading, rises from the floor while melting, full after
        let liq = match t.beat {
            0 => bot,
            1 => lerp((bot - 1) as f32, mel as f32, ease_in_out(t.local)).round() as i32,
            _ => mel,
        };
        for y in liq..bot {
            for x in cl + 1..cr {
                c.put(x, y, melt_char(x, y, t.ms));
            }
        }
        match t.beat {
            0 => {
                // chunks drop in one after another, then dopant dust settles over them
                for k in 0..CHUNKS {
                    let (x, ty) = chunk_spot(cl, bot, k);
                    let f = ((t.local - 0.07 * k as f32) / 0.5).clamp(0.0, 1.0);
                    let y = lerp(1.0, ty as f32, ease_in_out(f)).round() as i32;
                    c.put(x, y, '▪');
                }
                if t.local > 0.6 {
                    for y in bot - 7..bot - 2 {
                        for x in cl + 1..cr {
                            if (x * 5 + y * 3).rem_euclid(7) == 0 {
                                c.put(x, y, '·');
                            }
                        }
                    }
                }
                c.label(cr + 3, bot - 5, "poly + dopant");
            }
            1 => {
                // chunks melt one by one, last one about 0.9 of the way through
                for k in 0..CHUNKS {
                    if t.local < 0.3 + 0.12 * k as f32 {
                        let (x, ty) = chunk_spot(cl, bot, k);
                        c.put(x, ty, '▪');
                    }
                }
                let argon = Path::new(&[(cl - 6, 2), (cr + 6, 2)]);
                flow(c, &argon, t.ms, Particles::new(501, 300, 1800), |_| '°');
                c.label(cl - 6, 1, "argon in");
                c.label(cr + 3, mel, "~1414 C");
            }
            2 => {
                // seed lowers to the melt, then the neck is pulled up from it
                let contact = t.local < 0.4;
                let neck = if contact {
                    0
                } else {
                    let pull = ((t.local - 0.4) / 0.6).clamp(0.0, 1.0);
                    (NECK as f32 * ease_in_out(pull)).round() as i32
                };
                let seed = if contact {
                    lerp(3.0, base as f32, ease_in_out(t.local / 0.4)).round() as i32
                } else {
                    base - neck
                };
                draw_rod(c, cx, base, 0, 0, neck, 0);
                draw_seed(c, cx, seed);
                if (0.3..0.45).contains(&t.local) {
                    c.put(cx - 3, base, '*');
                    c.put(cx + 3, base, '*');
                }
                if !contact {
                    c.label(cx + 5, base - NECK / 2, "2-4 mm neck");
                }
            }
            3 => {
                // shoulder forms first at the lower end, then the body grows beneath it
                let shoulder =
                    (SHOULDER as f32 * ease_in_out((t.local / 0.4).clamp(0.0, 1.0))).round() as i32;
                let body = (body_max(mel) as f32
                    * ease_in_out(((t.local - 0.4) / 0.6).clamp(0.0, 1.0)))
                .round() as i32;
                draw_rod(c, cx, base, body, shoulder, NECK, 0);
                draw_seed(c, cx, base - (body + shoulder + NECK));
                if shoulder > 0 {
                    c.label(cx + 8, base - body - 1, "shoulder");
                }
                if body > 0 {
                    c.label(cx + 8, base - body / 2, "body 300 mm");
                }
            }
            _ => {
                // tail tapers the bottom, then the rod is lifted off the melt
                let f = ease_in_out(t.local);
                let tail = (TAIL as f32 * f).round() as i32;
                let lift = (LIFT as f32 * f).round() as i32;
                let body = body_max(mel);
                let rod_base = base - lift;
                draw_rod(c, cx, rod_base, body, SHOULDER, NECK, tail);
                draw_seed(c, cx, rod_base - (body + SHOULDER + NECK));
                c.label(cx + 8, rod_base - 1, "tail: taper, cool");
                if t.local > 0.5 {
                    c.label(cx + 8, rod_base - body / 2, "INGOT");
                }
            }
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Rod)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn time(beat: usize, local: f32) -> Time {
        Time {
            ms: beat as u64 * BEAT_MS + (local * BEAT_MS as f32) as u64,
            beat,
            local,
            beat_start: beat as u64 * BEAT_MS,
        }
    }

    fn at(beat: usize, local: f32, w: usize, h: usize) -> String {
        let mut c = Canvas::new(w as u16, h as u16);
        Rod.draw(&mut c, &time(beat, local));
        c.lines().join("\n")
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        let s = build();
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.caption.is_empty()
                    && !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty()
                    && b.facts.iter().all(|f| !f.is_empty()),
                "beat {i}"
            );
        }
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            for beat in [0, BEATS.len() / 2, BEATS.len() - 1] {
                for local in [0.0, 0.5, 0.99] {
                    let mut c = Canvas::new(w, h);
                    Rod.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.9, 120, 40).contains('▪'));
        assert!(at(1, 0.5, 120, 40).contains("1414 C"));
        assert!(at(2, 0.9, 120, 40).contains("2-4 mm neck"));
        assert!(at(3, 0.99, 120, 40).contains("body 300 mm"));
        assert!(at(4, 0.9, 120, 40).contains("tail: taper, cool"));
    }
}
