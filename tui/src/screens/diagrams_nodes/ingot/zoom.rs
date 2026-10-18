// Zoom-ins for the INGOT overview. Each opens one stage the overview animates.
//
//   Grind   a: the outer diameter is ground from an oversize, out-of-round crystal to a round cylinder
//   Notch   b: the V groove ground along the length, then its end-on shape, marking <110>
//   Test    c: X-ray on a cut face; the diffraction spots line up on the crystal plane
//   Saw     d: the wire web slices the ingot; each pass leaves a wafer and a kerf
//
// Sources (text read; no PDF drawing was read, so every drawing is schematic, not to scale):
//   US 8,376,809 (Sumco grinder): https://patents.google.com/patent/US8376809
//   US 11,551,922 (periphery grind and notch): https://patents.google.com/patent/US11551922
//   SV029 datasheet, 300 mm wafer: https://svmi.com/wp-content/uploads/2021/01/SV029.pdf
//   US 5,529,051 (<110> found by X-ray, flat or notch ground to it): https://patents.google.com/patent/US5529051
//   INGOT page text (crop, test, grind, notch and saw steps)

use crate::ui::anim::shapes::{Path, fill_disc, flow};
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

/// Time through the current beat, 0..1.
fn local(t: &Time) -> f32 {
    t.local.clamp(0.0, 1.0)
}

// ---- a: grind -------------------------------------------------------------

pub struct Grind;

const GRIND_BEATS: &[Beat] = &[
    Beat::new("as-pulled cross section: an oval, oversize", BEAT_MS)
        .note(
            "the rough crystal seen end-on: wider than it is tall, bigger than the target",
            "the outline is an oval and the edge is ragged",
        )
        .detail(
            "The as-pulled crystal is slightly oversize and not round, so it is ground to size (patent text, US 8,376,809).",
            &[
                "as-pulled: oversize, not round (INGOT page)",
                "target after grinding: 300 mm +/- 0.2 mm (SV029 datasheet)",
            ],
        ),
    Beat::new("the wheel takes the surface down to a round cylinder", BEAT_MS)
        .note(
            "the grind wheel runs along the length and removes the outer layer",
            "the oval shrinks toward a circle; the wheel marks sit on the top edge",
        )
        .detail(
            "Every micron ground off is silicon already pulled and paid for, so grinding time and loss both matter (INGOT page).",
            &[
                "grinding damage or chipping at the ends is the failure mode (INGOT page)",
                "wheel wear can give the cylinder a taper (INGOT page)",
            ],
        ),
    Beat::new("done: a round cylinder at the target diameter", BEAT_MS)
        .note(
            "the cross section is now a circle, and the diameter is held along the full length",
            "a circle with a steady ring of ground surface around it",
        )
        .detail(
            "The grind sets the diameter that every downstream tool assumes (FOUP and wafer handling, INGOT page).",
            &["diameter tolerance: +/- 0.2 mm (SV029 datasheet)"],
        ),
];

impl Scene for Grind {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        GRIND_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        panels(c, w, h, 1, "SIDE: along the axis", "END-ON: cross section");
        grind_side(c, w / 4, cy, t);
        grind_end(c, 3 * w / 4, cy, t);
        c.text(2, h - 2, "the wheel runs the length; the cross section goes round");
    }
}

/// Two panels split at the middle, each titled. `row` is where the titles sit.
fn panels(c: &mut Canvas, w: i32, h: i32, row: i32, left: &str, right: &str) {
    c.vline(w / 2, row, h - row - 3, '┊');
    c.text(w / 4 - left.chars().count() as i32 / 2, row, left);
    c.text(3 * w / 4 - right.chars().count() as i32 / 2, row, right);
}

/// Side view: the rod along its axis. The wheel removes the rough top edge as it passes.
fn grind_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    let (x0, x1) = (cx - 14, cx + 14);
    for y in cy - 3..=cy + 3 {
        c.hline(x0, y, x1 - x0 + 1, '▓');
    }
    // rough top edge before the wheel, clean after it
    let wheel = match t.beat {
        0 => None,
        1 => Some(lerp(x0 as f32, x1 as f32, ease_in_out(local(t))).round() as i32),
        _ => Some(x1 + 1),
    };
    for x in x0..=x1 {
        let rough = match wheel {
            None => true,
            Some(wx) => x > wx,
        };
        if rough {
            c.put(x, cy - 3, '~');
        }
    }
    if let (1, Some(wx)) = (t.beat, wheel) {
        c.put(wx, cy - 5, '▼');
        c.hline(x0, cy - 5, x1 - x0 + 1, '─');
    }
}

/// End-on view: the cross section, oval and oversize, then round at the target diameter.
fn grind_end(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    // beat 0: oval, beat 1: shrinking, beat 2: round
    let p = match t.beat {
        0 => 0.0,
        1 => ease_in_out(local(t)),
        _ => 1.0,
    };
    let rx = lerp(12.0, 10.0, p);
    let ry = lerp(6.0, 5.0, p);
    fill_disc(c, cx, cy, rx, ry, '▓');
}

// ---- b: notch -------------------------------------------------------------

pub struct Notch;

const NOTCH_BEATS: &[Beat] = &[
    Beat::new("the ground cylinder, before the notch", BEAT_MS)
        .note(
            "side view: the outer surface is smooth and the top edge is flat",
            "no groove yet; the orientation mark is still to be ground",
        )
        .detail(
            "Orientation is marked on the rim after grinding, so the mark is placed on a true cylinder (INGOT page).",
            &["notch orientation: <110> +/- 1 deg (SV029 datasheet)"],
        ),
    Beat::new("the wheel grinds a V groove along the full length", BEAT_MS)
        .note(
            "side view: the groove runs left to right along the top, one cut the full length",
            "a V-shaped notch appears on the rim and extends from one end to the other",
        )
        .detail(
            "The groove is ground along the whole length so every wafer sliced from the ingot carries the same mark (INGOT page; US 11,551,922).",
            &[
                "notch depth 1.0 mm (+0.25 / -0.00), 90 deg angle (SV029 datasheet)",
                "the patent describes the groove as an arc or an approximate V (US 11,551,922)",
            ],
        ),
    Beat::new("end view: the notch marks <110> for every tool", BEAT_MS)
        .note(
            "end-on: the cross section with its V notch on the rim",
            "the notch sits on top; tools use it to align each wafer",
        )
        .detail(
            "Notch orientation <110> is found by X-ray and marked on the rim (US 5,529,051); tools align wafers to it.",
            &["notch angle and depth: SV029 datasheet"],
        ),
];

impl Scene for Notch {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        NOTCH_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2;
        panels(c, w, h, 1, "SIDE: the groove", "END-ON: the notch");
        notch_side(c, w / 4, cy, t);
        notch_end(c, 3 * w / 4, cy, t.beat);
        c.text(2, h - 2, "the groove runs the full length; end-on it is the V on the rim");
    }
}

/// Side view: a bar, top edge flat until the groove runs along it, then the full V groove.
fn notch_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    let (x0, x1) = (cx - 14, cx + 14);
    let top = cy - 3;
    for y in top..=cy + 3 {
        c.hline(x0, y, x1 - x0 + 1, '▓');
    }
    match t.beat {
        0 => {}
        1 => {
            let gx = lerp(x0 as f32, x1 as f32, local(t)).round() as i32;
            for x in x0..gx {
                c.put(x, top, '▽');
            }
            c.put(gx, top, '▼');
        }
        _ => {
            for x in x0..=x1 {
                c.put(x, top, '▽');
            }
        }
    }
}

/// End-on view: a disc, with a V notch cut out of its top rim from beat 2 on.
fn notch_end(c: &mut Canvas, cx: i32, cy: i32, beat: usize) {
    let r = 5;
    fill_disc(c, cx, cy, 2.0 * r as f32, r as f32, '▓');
    if beat >= 2 {
        for dy in 0..=2 {
            for dx in -(2 - dy)..=(2 - dy) {
                c.put(cx + dx, cy - r + dy, ' ');
            }
        }
        c.put(cx, cy - r + 2, '▽');
    }
}

// ---- c: cut-face test -----------------------------------------------------

pub struct Test;

const TEST_BEATS: &[Beat] = &[
    Beat::new("X-ray aimed at a cut face", BEAT_MS)
        .note(
            "side: the beam leaves the source and runs into the face; detector: nothing yet",
            "dots run along the beam, left to right, into the crystal",
        )
        .detail(
            "After cropping, test samples are taken from the cut faces to check orientation (INGOT page; US 5,529,051).",
            &["test: orientation, doping type, resistivity (INGOT page)"],
        ),
    Beat::new("the diffraction spots come back", BEAT_MS)
        .note(
            "side: a reflected beam leaves the face; detector: spots appear in a pattern set by the crystal planes",
            "the spots flicker on as the detector reads them",
        )
        .detail(
            "Orientation is checked by X-ray diffraction against the intended Miller plane (INGOT page).",
            &["{100} for logic and CMOS, {111} for bipolar, power and MEMS (INGOT page)"],
        ),
    Beat::new("the spots line up: the plane is found and marked", BEAT_MS)
        .note(
            "side: the <110> direction is marked on the crystal edge; detector: the same mark on the pattern",
            "the marks line up on the face and on the detector",
        )
        .detail(
            "A mis-seeded crystal is caught here, the last cheap point to reject it (INGOT page).",
            &["notch tolerance <110> +/- 1 deg (SV029 datasheet)"],
        ),
];


/// Dotted line between two cells, one dot every other cell.
fn dotted(c: &mut Canvas, (x0, y0): (i32, i32), (x1, y1): (i32, i32)) {
    let n = (x1 - x0).abs().max((y1 - y0).abs());
    for i in (0..=n).step_by(2) {
        let f = i as f32 / n as f32;
        let x = lerp(x0 as f32, x1 as f32, f).round() as i32;
        let y = lerp(y0 as f32, y1 as f32, f).round() as i32;
        c.put(x, y, '·');
    }
}

/// Side view: the X-ray source, the beam running into the cut face, and the reflected beam.
fn test_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    // the crystal: its cut face is the left edge, toward the source
    for y in cy - 4..=cy + 4 {
        c.hline(cx - 2, y, 12, '▓');
    }
    c.text(cx - 18, cy, "X◉");
    // the incoming beam, animated along its path
    let beam = Path::new(&[(cx - 14, cy), (cx - 3, cy)]);
    flow(c, &beam, t.ms, Particles::new(31, 200, 900), |_| '▶');
    if t.beat >= 1 {
        dotted(c, (cx - 2, cy - 2), (cx + 26, cy - 2));
    }
    if t.beat == 2 {
        // <110> marked on the crystal's top edge
        c.put(cx + 4, cy - 5, '▲');
        c.text(cx + 2, cy - 6, "<110>");
    }
}

/// Detector: a box with the diffraction pattern. {100} gives four spots about the centre.
fn test_detector(c: &mut Canvas, x0: i32, y0: i32, w: i32, h: i32, t: &Time) {
    c.boxed(x0, y0, w, h);
    let (dcx, dcy) = (x0 + w / 2, y0 + h / 2);
    let spots = [(-7, 0), (7, 0), (0, -3), (0, 3)];
    for (i, (dx, dy)) in spots.iter().enumerate() {
        let on = match t.beat {
            0 => false,
            1 => flicker(t.ms, 350, 5 + i as u64, 2) == 0,
            _ => true,
        };
        if on {
            c.put(dcx + dx, dcy + dy, '•');
        }
    }
    if t.beat == 2 {
        c.put(dcx, y0, '▲');
        c.text(dcx - 2, y0 - 1, "<110>");
    }
}

impl Scene for Test {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        TEST_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        panels(c, w, h, 5, "SIDE: beam on the cut face", "DETECTOR: diffraction spots");
        test_side(c, w / 4, cy, t);
        test_detector(c, 3 * w / 4 - 12, cy - 7, 24, 11, t);
    }
}

// ---- d: wire saw ----------------------------------------------------------

pub struct Saw;

const SAW_BEATS: &[Beat] = &[
    Beat::new("the ingot is fed down into the wire web", BEAT_MS)
        .note(
            "the wire runs over guide rollers and forms a web of parallel passes",
            "the ingot block moves down into the web from above",
        )
        .detail(
            "The wire saw runs one diamond wire over guide rollers; the beam lowers the ingot at table speed (US 9,873,159).",
            &["wire pitch sets wafer thickness plus kerf (INGOT page)"],
        ),
    Beat::new("each pass of wire leaves one slice", BEAT_MS)
        .note(
            "the ingot is through the web; each wire pass has cut a slice",
            "slices stack up below the ingot as the cut advances",
        )
        .detail(
            "Pitch and kerf numbers for a 300 mm ingot were not found; a 150 mm test used pitch 0.33 mm and kerf allowance 0.13 mm (US 8,256,407).",
            &["sawing speed and kerf for 300 mm: no source found (INGOT page)"],
        ),
    Beat::new("the slices come off, each with a kerf of lost silicon", BEAT_MS)
        .note(
            "the wafers are apart; the gaps between them are the kerf",
            "bright slices separated by dark kerf lines",
        )
        .detail(
            "Wafers are then machined for flatness, edge-ground, chamfered, etched and polished (INGOT page).",
            &["slices go to lap, etch and polish next (INGOT page)"],
        ),
];

impl Scene for Saw {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SAW_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (x0, x1) = (w / 2 - 12, w / 2 + 12);
        // guide rollers and the wire web
        c.hline(x0 - 2, 3, x1 - x0 + 4, '═');
        let mut x = x0;
        while x <= x1 {
            c.vline(x, 4, h - 8, '│');
            x += 3;
        }
        match t.beat {
            0 => {
                // ingot block lowers into the web
                let top = lerp(4.0, 9.0, ease_in_out(local(t))).round() as i32;
                for y in top..top + 5 {
                    c.hline(x0 + 2, y, x1 - x0 - 4, '▓');
                }
            }
            _ => {
                // the ingot is through; slices stack up below it
                let slices = if t.beat == 1 {
                    (local(t) * 6.0).round() as i32
                } else {
                    6
                };
                let mut y = 9;
                for i in 0..slices {
                    c.hline(x0 + 2, y, x1 - x0 - 4, '▓');
                    y += 2;
                    if t.beat == 2 && i < 5 {
                        c.hline(x0 + 2, y - 1, x1 - x0 - 4, '░');
                    }
                }
            }
        }
        c.text(2, h - 2, "wire web: one wire, many passes, one slice per pass");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn beats_ok(s: &dyn Scene) {
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
    fn beats_are_captioned_and_explained() {
        beats_ok(&Grind);
        beats_ok(&Notch);
        beats_ok(&Test);
        beats_ok(&Saw);
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for build in [
            || -> Box<dyn Scene> { Box::new(Grind) },
            || -> Box<dyn Scene> { Box::new(Notch) },
            || -> Box<dyn Scene> { Box::new(Test) },
            || -> Box<dyn Scene> { Box::new(Saw) },
        ] {
            for (w, h) in [(80, 26), (120, 40), (200, 60)] {
                let mut p = Player::new(build(), Instant::now());
                p.fit(w, h);
                for k in 0..p.loop_ms() / 500 {
                    let s = p.shot_at(k * 500);
                    assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                }
            }
        }
    }
}
