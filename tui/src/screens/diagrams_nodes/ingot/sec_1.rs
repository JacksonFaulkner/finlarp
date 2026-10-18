// INGOT section 1: from as-pulled crystal to wafer-ready cylinder, close up.
//
//   Rod   the as-pulled rod, with a cone on each end, is cropped; a cut face is tested for
//         orientation; the outer diameter is ground to 300 mm; a V notch is ground along the
//         length; the ground, notched cylinder leaves the node for the wire saw
//
// Sources (the text was read; the patent drawings were not, so the rod is schematic):
//   US 8,376,809 (Sumco, cylindrical grinder for silicon ingot)
//     https://patents.google.com/patent/US8376809
//     Background: Czochralski pull, then traverse grinding of the outer circumference, then
//     slicing perpendicular to the axis. FIG. 18 is the related-art grinder, ingot clamped
//     horizontally, grinding unit moving along the axis.
//   US 11,551,922 (ingot periphery grinding and notch)
//     https://patents.google.com/patent/US11551922
//     Periphery ground to set the diameter. Groove along the axis, "an arc shape or an
//     approximate V shape", marks <110>. No notch depth or angle given in the text.
//   SV029 datasheet, 300 mm silicon wafer (Silicon Valley Microelectronics)
//     https://svmi.com/wp-content/uploads/2021/01/SV029.pdf
//     Diameter 300 +/- 0.20 mm; notch depth 1.0 (+0.25/-0.00) mm; notch angle 90 deg (+5/-1);
//     notch orientation <110> +/- 1 deg. (A second datasheet, SV031, lists +/- 0.10 mm for the
//     diameter; seen in a search snippet only, not read.)
//   INGOT page text (crop, test, grind, notch steps; cut-face tests).

use crate::ui::anim::shapes::fill_ellipse;
use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

// schematic rod: half-height of the body in rows, length of each cone in columns
const HB: i32 = 4;
const CL: i32 = 5;
const CONE_SLIDE: f32 = 8.0;

// the six stages, in page order (one per beat)
const STAGES: [&str; 6] = ["AS-PULLED", "CROP", "TEST", "GRIND OD", "NOTCH", "WIRE SAW"];

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Stage strip across the top: six boxes, the current stage marked below.
fn stage_row(c: &mut Canvas, w: i32, cur: usize) {
    let (bw, gap) = (11, 2);
    let x0 = (w - (6 * bw + 5 * gap)) / 2;
    for (i, name) in STAGES.iter().enumerate() {
        let x = x0 + i as i32 * (bw + gap);
        c.boxed(x, 1, bw, 3);
        let nx = x + 1 + (bw - 2 - name.len() as i32) / 2;
        c.text(nx, 2, name);
        if i == cur {
            c.put(x + bw / 2, 4, '▼');
        }
    }
}

/// Left cone: tapers from a point at the far end to the body at `x0`. `ox` slides it.
fn cone_left(c: &mut Canvas, cy: i32, x0: i32, ox: i32) {
    for i in 0..CL {
        let x = x0 - CL + i + ox;
        let h = HB * i / CL;
        for dy in -h..=h {
            let ch = if h > 0 && dy.abs() == h { '▒' } else { '▓' };
            c.put(x, cy + dy, ch);
        }
    }
}

/// Right cone: tapers from the body at `x1` to a point. `ox` slides it.
fn cone_right(c: &mut Canvas, cy: i32, x1: i32, ox: i32) {
    for i in 0..CL {
        let x = x1 + 1 + i + ox;
        let h = HB * (CL - 1 - i) / CL;
        for dy in -h..=h {
            let ch = if h > 0 && dy.abs() == h { '▒' } else { '▓' };
            c.put(x, cy + dy, ch);
        }
    }
}

/// Straight body from `x0` to `x1`. Columns where `rough` holds keep an oversize, uneven top
/// and bottom (marked with '~'); the rest are at the finished half-height.
fn body(c: &mut Canvas, cy: i32, x0: i32, x1: i32, rough: &dyn Fn(i32) -> bool) {
    for x in x0..=x1 {
        for dy in -HB..=HB {
            let ch = if dy.abs() == HB { '▒' } else { '▓' };
            c.put(x, cy + dy, ch);
        }
        if rough(x) {
            c.put(x, cy - HB - 1, '~');
            c.put(x, cy + HB + 1, '~');
        }
    }
}

/// Crop line: a dotted cut at column `x`, drawn only where nothing is already there.
fn crop_line(c: &mut Canvas, cy: i32, x: i32) {
    for y in cy - HB - 2..=cy + HB + 2 {
        c.put_if_blank(x, y, '┊');
    }
}

/// The V groove along the top edge, up to column `upto`.
fn groove(c: &mut Canvas, cy: i32, x0: i32, x1: i32, upto: f32) {
    for x in x0..=x1 {
        if ((x - x0) as f32) <= upto * (x1 - x0) as f32 {
            c.put(x, cy - HB, '∨');
        }
    }
}

pub struct Section;

const BEATS: &[Beat] = &[
    Beat::new("as-pulled: a rough rod with a cone at each end, not yet round", BEAT_MS)
        .note(
            "The crystal comes out of the puller as a rough rod. A cone sits at each end, and the body is oversize and not round.",
            "The seed cone on the left, the tail cone on the right, and an uneven edge along the body.",
        )
        .detail(
            "Every later step starts from this rough rod. Nothing is yet at the 300 mm size or has the orientation mark.",
            &[
                "Ingot grown by the Czochralski method, then ground and sliced (US 8376809 background)",
                "Grinding sets the ingot periphery to a predetermined diameter (US 11551922)",
            ],
        ),
    Beat::new("crop: the seed cone and the tail cone are cut off", BEAT_MS)
        .note(
            "The two cones are cut away at the crop lines, leaving the straight body of the single crystal.",
            "Crop lines appear at both ends, and each cone slides off the body.",
        )
        .detail(
            "The cones are the ends of the rod, not usable body. Where the cut goes is set per crystal by measurement.",
            &[
                "Crop positions follow the measured crystal (INGOT page details; not checked against a PDF)",
                "Cut faces are the samples taken for the next step (INGOT page details)",
            ],
        ),
    Beat::new("test: an X-ray on the cut face checks orientation before grinding", BEAT_MS)
        .note(
            "A sample from the cut face is checked by X-ray for crystal orientation, doping type and resistivity.",
            "The X-ray beam comes in from the left and lands on the flat cut face.",
        )
        .detail(
            "The orientation is checked here. A crystal that was seeded wrongly is caught before grinding and slicing.",
            &[
                "Test samples from the cut faces: orientation, type, resistivity (INGOT page details)",
                "Notch orientation tolerance <110> +/- 1 deg (SV029 datasheet)",
            ],
        ),
    Beat::new("grind OD: the wheel traverses the length until the rod is 300 mm", BEAT_MS)
        .note(
            "A grinding wheel passes along the length of the ingot and takes the rough outer surface down to the target diameter.",
            "The rough top edge shrinks as the wheel passes; the smooth part is what it has already ground.",
        )
        .detail(
            "The diameter is the first size the wafer spec depends on. Silicon removed here was already pulled and paid for.",
            &[
                "Wafer diameter 300 +/- 0.20 mm (SV029 datasheet)",
                "Traverse grinding of the outer circumference, wheel moving along the axis (US 8376809, FIG. 18 description)",
            ],
        ),
    Beat::new("notch: a 90 deg V groove runs the full length, marking <110>", BEAT_MS)
        .note(
            "A V-shaped groove is ground along the full length of the cylinder. It marks the crystal direction <110>.",
            "The V marks run along the top of the body; the end view on the right shows the notch at the top edge.",
        )
        .detail(
            "The notch is how the tools later find the crystal direction. Its size is a fixed spec, not chosen per ingot.",
            &[
                "Notch depth 1.0 mm (+0.25/-0.00), angle 90 deg (+5/-1) (SV029 datasheet)",
                "Groove is an arc or approximate V, cut by moving the grindstone along the axis (US 11551922)",
            ],
        ),
    Beat::new("done: a 300 mm notched cylinder goes on to the wire saw", BEAT_MS)
        .note(
            "The ground, notched cylinder leaves this node. The wire saw slices it perpendicular to its axis.",
            "The finished body, with its V marks, runs out to the right toward the saw.",
        )
        .detail(
            "The node ends at a ground, notched cylinder. Lap, etch and polish come after the saw.",
            &[
                "Slicing is perpendicular to the ingot axis (US 8376809 background)",
                "The saw output goes on to lap, etch and polish (INGOT page text)",
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
        let cy = h / 2 + 1;
        let (x0, x1) = (12, w - 24);
        stage_row(c, w, t.beat);
        c.text(2, h - 2, "schematic, not to scale");
        match t.beat {
            0 => {
                cone_left(c, cy, x0, 0);
                cone_right(c, cy, x1, 0);
                body(c, cy, x0, x1, &|_| true);
                c.label(x0 - CL - 1, cy + HB + 2, "seed cone");
                c.label(x1 + 1, cy + HB + 2, "tail cone");
                c.label(2, h - 4, "OD rough ~~~, not round, cones on both ends");
            }
            1 => {
                let k = (ease_in_out(t.local) * CONE_SLIDE).round() as i32;
                cone_left(c, cy, x0, -k);
                cone_right(c, cy, x1, k);
                body(c, cy, x0, x1, &|_| true);
                crop_line(c, cy, x0 - 1);
                crop_line(c, cy, x1 + 1);
                c.label(2, h - 4, "crop: cones off along the crop lines");
            }
            2 => {
                body(c, cy, x0, x1, &|_| true);
                crop_line(c, cy, x0 - 1);
                crop_line(c, cy, x1 + 1);
                c.text(1, cy, "X◉═══════▶");
                c.label(2, h - 4, "X-ray on the cut face: orientation, type, resistivity");
            }
            3 => {
                let xw = lerp(x1 as f32, x0 as f32, ease_in_out(t.local)).round() as i32;
                body(c, cy, x0, x1, &|x| x <= xw);
                c.text(xw - 2, cy - HB - 3, "╭───╮");
                c.text(xw - 2, cy - HB - 2, "╰─◎─╯");
                c.label(2, h - 4, "OD: rough ~~~ --> 300 mm +/- 0.20 mm");
            }
            4 => {
                let prog = ease_in_out(t.local);
                body(c, cy, x0, x1, &|_| false);
                groove(c, cy, x0, x1, prog);
                let cx = x1 + 14;
                fill_ellipse(c, cx, cy, (2 * HB) as f32, HB as f32, '▓');
                for x in cx - 1..=cx + 1 {
                    c.put(x, cy - HB, '∨');
                }
                c.put(cx, cy - HB - 1, '▼');
                c.label(cx - 2, cy - HB - 2, "notch");
                c.label(cx - 4, cy + HB + 2, "end view");
                c.label(2, h - 4, "V groove 90 deg, 1.0 mm deep (+0.25/-0.00), on <110>");
            }
            _ => {
                body(c, cy, x0, x1, &|_| false);
                groove(c, cy, x0, x1, 1.0);
                c.text(x1 + 2, cy, "──▶ wire saw");
                c.label(2, h - 4, "300 mm, notch <110> +/- 1 deg; this node ends here");
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
        Section.draw(&mut c, &time(beat, local));
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
            for beat in 0..BEATS.len() {
                for local in [0.0, 0.5, 0.99] {
                    let mut c = Canvas::new(w, h);
                    Section.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.5, 80, 26).contains("seed cone"));
        assert!(at(2, 0.5, 80, 26).contains("X◉"));
        assert!(at(3, 0.5, 80, 26).contains("300 mm"));
        assert!(at(4, 0.99, 80, 26).contains("<110>"));
        assert!(at(5, 0.5, 80, 26).contains("wire saw"));
    }
}
