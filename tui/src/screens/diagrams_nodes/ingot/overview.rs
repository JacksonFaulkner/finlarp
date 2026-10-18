// INGOT page overview: the as-pulled rod moves through the six stages in page order: cropped,
// tested, ground to diameter, notched, then sawn. Zoom-ins (a-d) open the grind, the notch,
// the cut-face test and the wire saw.
//
//   Rod      schematic, not to scale; the cones are cut off, the body is ground and notched
//   Stages   the strip across the top; the current stage is marked below it
//
// Sources: see zoom.rs and the section files. The rod is schematic; the stage order is the page's.

use super::zoom;
use crate::ui::anim::shapes::{Path, fill_disc, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, flicker, lerp};

const MIN_W: u16 = 100;
const MIN_H: u16 = 30;
const BEAT_MS: u64 = 5200;

// stations: boxes SW columns wide, PITCH apart, from column X0; the ingot rides the track below
const SW: i32 = 13;
const PITCH: i32 = 15;
const X0: i32 = 6;
const BOX_TOP: i32 = 2;
const BOX_BOT: i32 = 13;
const ROD_Y: i32 = 16;
const TRACK: i32 = 18;

const STATIONS: [&str; 6] = ["PULLER", "CROP", "TEST", "GRIND OD", "NOTCH", "WIRE SAW"];


const BEATS: &[Beat] = &[
    Beat::new("as-pulled: a rough rod with a cone on each end", BEAT_MS)
        .note(
            "the rod as it comes off the puller, seed cone on the left, tail cone on the right",
            "rough edges; the cones taper to a point",
        )
        .detail(
            "The crystal is up to about 2 m long and several hundred kg, and it holds the value of one furnace run (INGOT page; Wikipedia).",
            &["the as-pulled rod is oversize and not round (INGOT page)"],
        ),
    Beat::new("crop: the seed and tail cones are cut off", BEAT_MS)
        .note(
            "crop lines mark where the saw will cut the cones away",
            "the cones are marked with crop lines at each end of the body",
        )
        .detail(
            "Crop position is set by measurement: the tail end is richest in dopant and metal, so cuts move with each crystal (INGOT page).",
            &["a longer crop gives cleaner wafers but fewer of them (INGOT page)"],
        ),
    Beat::new("test: the cut faces are checked for orientation", BEAT_MS)
        .note(
            "the cones are gone; the cut faces are where the test samples come from",
            "X-ray marks sit on both cut faces",
        )
        .detail(
            "Test samples from the cut faces confirm orientation, doping type and resistivity (INGOT page).",
            &["orientation is checked by X-ray diffraction (INGOT page)"],
        ),
    Beat::new("grind OD: the body is ground round to 300 mm", BEAT_MS)
        .note(
            "the rough edges are ground away and the body becomes a clean cylinder",
            "the rough edge fades to a clean edge as the wheel passes",
        )
        .detail(
            "The grind sets the outer diameter to 300 mm +/- 0.2 mm (SV029 datasheet).",
            &["grinding is traverse OD grinding along the axis (US 8,376,809)"],
        ),
    Beat::new("notch: a V groove is ground along the length", BEAT_MS)
        .note(
            "the notch is ground on the rim along the full length of the body",
            "a V mark appears on the top rim",
        )
        .detail(
            "Notch: 90 deg, depth 1.0 mm (+0.25/-0.00), on <110> +/- 1 deg (SV029 datasheet).",
            &["notch marks orientation; it does not show doping type (INGOT page)"],
        ),
    Beat::new("wire saw: the cylinder is sawn into wafers", BEAT_MS)
        .note(
            "the ground, notched cylinder goes to the wire saw; its wire passes cut across the body",
            "wire lines cross the body; the body is the finished ingot leaving this node",
        )
        .detail(
            "Wire pitch sets wafer thickness plus kerf; pitch and kerf for 300 mm were not found (INGOT page).",
            &["the saw output goes on to lap, etch and polish (INGOT page)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the grind to 300 mm",
        build: || -> Box<dyn Scene> { Box::new(zoom::Grind) },
    },
    Zoom {
        key: 'b',
        label: "the V notch on the rim",
        build: || -> Box<dyn Scene> { Box::new(zoom::Notch) },
    },
    Zoom {
        key: 'c',
        label: "X-ray on the cut face",
        build: || -> Box<dyn Scene> { Box::new(zoom::Test) },
    },
    Zoom {
        key: 'd',
        label: "the wire web slices the ingot",
        build: || -> Box<dyn Scene> { Box::new(zoom::Saw) },
    },
];

fn station_x(i: usize) -> i32 {
    X0 + i as i32 * PITCH
}

fn station_mid(i: usize) -> i32 {
    station_x(i) + SW / 2
}

pub struct Ingot;

/// One station box with its equipment drawn inside.
fn station(c: &mut Canvas, i: usize, t: &Time) {
    let x = station_x(i);
    titled_box(c, x, BOX_TOP, SW, BOX_BOT - BOX_TOP + 1, STATIONS[i]);
    let cx = x + SW / 2;
    match i {
        0 => puller(c, x, t),
        1 => {
            // the cutting wheel turns; the cut-off cones drop into the scrap bin
            wheel(c, cx, 7, 4.0, 2.0, t);
            if t.beat == 1 {
                let drop = Path::new(&[(cx, 9), (cx, 19)]);
                flow(c, &drop, t.ms, Particles::new(61, 420, 1100), |_| 'O');
            }
        }
        2 => {
            // X-ray beam into the cut face; spots come back in the last beats
            c.text(x + 1, 5, "X◉");
            c.hline(x + 3, 5, 3, '═');
            c.hline(x + 7, 4, 2, '▓');
            c.hline(x + 7, 5, 2, '▓');
            c.hline(x + 7, 6, 2, '▓');
            if t.beat >= 1 {
                for (k, row) in [3, 5, 7].iter().enumerate() {
                    let on = t.beat == 2 || flicker(t.ms, 350, 5 + k as u64, 2) == 0;
                    if on {
                        c.put(x + 11, *row, '•');
                    }
                }
            }
        }
        3 => {
            // the grind wheel, with its spokes turning
            wheel(c, cx, 7, 4.0, 2.0, t);
            if t.beat == 3 {
                let sparks = Path::new(&[(cx + 4, 7), (cx + 8, 11)]);
                flow(c, &sparks, t.ms, Particles::new(62, 260, 700), |_| '·');
            }
        }
        4 => {
            // a small wheel cuts the V on the rim
            wheel(c, cx, 7, 3.0, 1.5, t);
            c.text(x + 2, 11, "V groove");
        }
        _ => {
            // three rollers carry the wire web; the top run moves, the slices fall to the tray
            for (rx, ry) in [(x + 3, 6), (x + 9, 6), (x + 6, 10)] {
                fill_disc(c, rx, ry, 2.0, 1.0, '▒');
            }
            c.hline(x + 3, 4, 7, '─');
            let run = Path::new(&[(x + 3, 4), (x + 9, 4)]);
            flow(c, &run, t.ms, Particles::new(63, 220, 800), |_| '▸');
            if t.beat == 5 {
                let slices = Path::new(&[(cx, 11), (cx, 19)]);
                flow(c, &slices, t.ms, Particles::new(64, 380, 1000), |_| '▪');
            }
        }
    }
}

/// A disc with a spoke that turns in time.
fn wheel(c: &mut Canvas, cx: i32, cy: i32, rx: f32, ry: f32, t: &Time) {
    fill_disc(c, cx, cy, rx, ry, '▒');
    let spoke = ['|', '/', '—', '\\'][((t.ms / 150) % 4) as usize];
    c.put(cx, cy, spoke);
}

/// Czochralski puller: the crucible with its melt, and the crystal being pulled from it in beat 0.
fn puller(c: &mut Canvas, x: i32, t: &Time) {
    let cx = x + SW / 2;
    c.boxed(x + 3, 9, 7, 4);
    let melt = if (t.ms / 400).is_multiple_of(2) { '≈' } else { '~' };
    c.hline(x + 4, 11, 5, melt);
    if t.beat == 0 {
        // the crystal grows up out of the melt as it is pulled
        let top = lerp(8.0, 4.0, ease_in_out(t.local.clamp(0.0, 1.0))).round() as i32;
        for y in top..=8 {
            c.hline(cx - 1, y, 3, '▓');
        }
        c.vline(cx, BOX_TOP + 1, (top - BOX_TOP - 1).max(0), '│');
    }
}

/// The ingot on the track. Hidden in beat 0 (it is still in the puller); from beat 1 it rides
/// from the previous station to this one during the first quarter of each beat.
fn rod(c: &mut Canvas, t: &Time) {
    if t.beat == 0 {
        return;
    }
    let moved = ease_in_out((t.local / 0.25).clamp(0.0, 1.0));
    let cx = lerp(station_mid(t.beat - 1) as f32, station_mid(t.beat) as f32, moved).round() as i32;
    let (x0, x1) = (cx - 5, cx + 5);
    for y in ROD_Y - 1..=ROD_Y + 1 {
        c.hline(x0, y, x1 - x0 + 1, '▓');
    }
    c.put(x0 - 1, ROD_Y, '(');
    c.put(x1 + 1, ROD_Y, ')');
    if t.beat == 4 {
        c.put(cx, ROD_Y - 2, '▽');
    }
    if t.beat == 5 {
        // the wire web passes down through the rod, one cut per pass
        let mut x = x0 + 1;
        while x < x1 {
            c.vline(x, ROD_Y - 1, 3, '│');
            x += 3;
        }
    }
}

impl Scene for Ingot {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let w = c.width().max(MIN_W as usize) as i32;
        for i in 0..STATIONS.len() {
            station(c, i, t);
        }
        // the track the ingot rides on, and a marker over the station that is active now
        c.hline(2, TRACK, w - 4, '═');
        c.put(station_mid(t.beat), BOX_BOT + 1, '▼');
        rod(c, t);
        // scrap bin under the crop station, slice tray under the saw
        titled_box(c, station_x(1), 20, SW, 3, "scrap");
        titled_box(c, station_x(5), 20, SW, 3, "slices");
        c.text(X0, 25, "▓ ingot   ▒ wheel or saw   ═ track   ▼ station now   O scrap   ▪ slices");
        c.text(X0, 27, "next: SLICE + POLISH (the slices go to lap, etch and polish)");
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
}


pub fn build() -> Box<dyn Scene> {
    Box::new(Ingot)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    #[test]
    fn beats_are_captioned_and_explained() {
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
    fn zooms_are_keyed_a_to_d() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
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
