// SLICE + POLISH page overview: the 300 mm ingot goes through seven stations in page order: the
// ingot comes in, a wire web slices it, then lap, etch, edge, polish and clean. The wafer rides a
// track from station to station. Zoom-ins (a-d) open the wire web, the lapping plates, the Preston
// polish and the thickness budget.
//
//   Wafer    schematic side view; thickness and surface change with each stage
//   Stations the boxes across the top; the wafer rides the track below them
//
// Sources: see zoom.rs and the page's own list ([1]-[8] in SLICE_POLISH.txt). Drawings are schematic.

use super::zoom;
use crate::ui::anim::shapes::{Path, fill_disc, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, flicker, lerp};

const MIN_W: u16 = 100;
const MIN_H: u16 = 30;
const BEAT_MS: u64 = 5200;

// stations: boxes SW columns wide, PITCH apart, from column X0; the wafer rides the track below
const SW: i32 = 11;
const PITCH: i32 = 13;
const X0: i32 = 4;
const BOX_TOP: i32 = 2;
const BOX_BOT: i32 = 13;
const WAFER_Y: i32 = 16;
const TRACK: i32 = 18;

const STATIONS: [&str; 7] = ["INGOT", "SLICE", "LAP", "ETCH", "EDGE", "POLISH", "CLEAN"];

const BEATS: &[Beat] = &[
    Beat::new("ingot: a ground 300 mm cylinder", BEAT_MS)
        .note(
            "the ground ingot, side view, ready for the saw",
            "a thick block, edges clean",
        )
        .detail(
            "The ingot node ends at a ground, notched cylinder; this node starts there (page section 1).",
            &["slicing turns the cylinder into wafers (page section 1)"],
        ),
    Beat::new("slice: a diamond wire web cuts the ingot", BEAT_MS)
        .note(
            "the ingot is fed down through the wire web; each pass cuts one slot",
            "vertical wire lines cross the block",
        )
        .detail(
            "Multi-wire diamond saw: every wire is a steel core with diamond grit; each pass cuts one slot in all wafers at once (page section 2).",
            &["kerf about 125 um today (page source [1])"],
        ),
    Beat::new("lap: two plates and slurry take both faces at once", BEAT_MS)
        .note(
            "the wafer sits between two plates; slurry flickers in the gaps",
            "the plates close in on a thin slab, faces flat and parallel",
        )
        .detail(
            "Lapping uses loose abrasive slurry between two plates; it sets flatness and parallelism (page section 3).",
            &["double-side lapping removes 80 to 200 um in total (page section 4)"],
        ),
    Beat::new("etch: the damaged layer is stripped away", BEAT_MS)
        .note(
            "the outer rows of the wafer fade as the wet etch removes them",
            "shaded rows on both faces fade to clean silicon",
        )
        .detail(
            "Alkali or acid etch removes the damaged layer lapping leaves behind; about 15-25 um after lapping (page sections 3-4).",
            &["the etch step is wet chemistry (page section 3)"],
        ),
    Beat::new("edge: the rim is profiled round", BEAT_MS)
        .note(
            "the sharp rim is ground and chamfered to a round profile",
            "the square ends of the wafer become rounded",
        )
        .detail(
            "The edge is ground round so it does not chip; the order of the steps is on the page (page section 1).",
            &["edge profiling sits between etch and polish on the page"],
        ),
    Beat::new("polish: pads and slurry leave a mirror face", BEAT_MS)
        .note(
            "a pad sits over the wafer; a sheen moves across the polished face",
            "a light band passes over the wafer's top face",
        )
        .detail(
            "Double-side polish removes 10-20 um; front-side polish 10-15 um, 5-15 min (page section 4).",
            &["polishing is chemical plus mechanical (page section 3)"],
        ),
    Beat::new("clean: inspect, then ship", BEAT_MS)
        .note(
            "the cleaned wafer is inspected and checked against the thickness spec",
            "a check mark sits above the finished wafer",
        )
        .detail(
            "End result: 775 um +/- 25 um thick, TTV 5 um or less (vendor datasheet; see WAFER on the page).",
            &["the step ends with inspection and shipping (page section 1)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the wire web and its kerf",
        build: || -> Box<dyn Scene> { Box::new(zoom::WebSaw) },
    },
    Zoom {
        key: 'b',
        label: "lapping both faces at once",
        build: || -> Box<dyn Scene> { Box::new(zoom::Lap) },
    },
    Zoom {
        key: 'c',
        label: "Preston polish and pH",
        build: || -> Box<dyn Scene> { Box::new(zoom::Preston) },
    },
    Zoom {
        key: 'd',
        label: "the thickness budget",
        build: || -> Box<dyn Scene> { Box::new(zoom::Budget) },
    },
];

fn station_x(i: usize) -> i32 {
    X0 + i as i32 * PITCH
}

fn station_mid(i: usize) -> i32 {
    station_x(i) + SW / 2
}

pub struct Polish;

/// One station box with its equipment drawn inside. Station i is the step for beat i.
fn station(c: &mut Canvas, i: usize, t: &Time) {
    let x = station_x(i);
    titled_box(c, x, BOX_TOP, SW, BOX_BOT - BOX_TOP + 1, STATIONS[i]);
    let cx = x + SW / 2;
    match i {
        0 => {
            // the ground ingot, waiting to go on the saw
            for y in 6..=8 {
                c.hline(x + 2, y, SW - 4, '▓');
            }
        }
        1 => {
            // three rollers carry the wire web; the top run moves; slices drop to the tray
            for (rx, ry) in [(x + 3, 6), (x + 7, 6), (x + 5, 10)] {
                fill_disc(c, rx, ry, 1.5, 1.0, '▒');
            }
            let run = Path::new(&[(x + 2, 4), (x + 8, 4)]);
            flow(c, &run, t.ms, Particles::new(71, 220, 800), |_| '▸');
            if t.beat == 1 {
                let drop = Path::new(&[(cx, 11), (cx, 19)]);
                flow(c, &drop, t.ms, Particles::new(72, 420, 1000), |_| '▪');
            }
        }
        2 => {
            // two plates with slurry between them; the plates close during the beat
            let gap = if t.beat == 2 {
                lerp(3.0, 1.0, ease_in_out(t.local.clamp(0.0, 1.0))).round() as i32
            } else {
                3
            };
            c.hline(x + 1, 6 - gap, SW - 2, '═');
            c.hline(x + 1, 9 + gap, SW - 2, '═');
            for k in 0..4 {
                if flicker(t.ms, 300, 81 + k, 2) == 0 {
                    c.put(x + 2 + 2 * k as i32, 7, '·');
                }
            }
        }
        3 => {
            // the bath: liquid at the top, bubbles rising from the wafer
            c.boxed(x + 1, 6, SW - 2, 6);
            let liquid = if (t.ms / 400).is_multiple_of(2) { '≈' } else { '~' };
            c.hline(x + 2, 7, SW - 4, liquid);
            let bubbles = Path::new(&[(cx, 11), (cx, 8)]);
            flow(c, &bubbles, t.ms, Particles::new(73, 300, 900), |_| '°');
        }
        4 => {
            // the edge grinder: a wheel with its spokes turning, rounding the rim
            fill_disc(c, cx, 7, 3.0, 1.5, '▒');
            let spoke = ['|', '/', '—', '\\'][((t.ms / 150) % 4) as usize];
            c.put(cx, 7, spoke);
            c.text(x + 1, 11, "round rim");
        }
        5 => {
            // the polishing pad, with pressure arrows and grains moving under it
            c.hline(x + 1, 5, SW - 2, '░');
            c.put(cx, 4, '▼');
            let grains = Path::new(&[(x + 2, 7), (x + 8, 7)]);
            flow(c, &grains, t.ms, Particles::new(74, 180, 1200), |_| '·');
        }
        _ => {
            // the clean: spray nozzles on the wafer, then a check mark
            let spray = Path::new(&[(cx, 4), (cx, 8)]);
            flow(c, &spray, t.ms, Particles::new(75, 260, 700), |_| '·');
            c.put(cx, 10, '✓');
        }
    }
}

/// The wafer on the track. Thick through the saw and lap, thin from etch on; it rides from the
/// previous station to this one during the first quarter of each beat.
fn wafer(c: &mut Canvas, t: &Time) {
    let moved = ease_in_out((t.local / 0.25).clamp(0.0, 1.0));
    let cx = if t.beat == 0 {
        station_mid(0)
    } else {
        lerp(station_mid(t.beat - 1) as f32, station_mid(t.beat) as f32, moved).round() as i32
    };
    let (x0, x1) = (cx - 5, cx + 5);
    let rows = if t.beat <= 1 { 3 } else { 2 };
    let top = WAFER_Y - rows / 2;
    for y in top..top + rows {
        c.hline(x0, y, x1 - x0 + 1, '▓');
    }
    match t.beat {
        // etch: the outer rows of the wafer fade as the damage is stripped
        3 => {
            let fade = (t.local.clamp(0.0, 1.0) * 3.0) as i32;
            let shade = match fade {
                0 => '▒',
                1 => '·',
                _ => ' ',
            };
            c.hline(x0, top - 1, x1 - x0 + 1, shade);
        }
        // edge: the square ends become round
        4 => {
            c.put(x0 - 1, WAFER_Y, '(');
            c.put(x1 + 1, WAFER_Y, ')');
        }
        // polish: a sheen moves across the top face
        5 => {
            let sx = lerp(x0 as f32, x1 as f32, t.local.clamp(0.0, 1.0)).round() as i32;
            c.put(sx, top, '░');
        }
        _ => {}
    }
    if t.beat == 6 {
        c.put(cx, WAFER_Y - 3, '✓');
    }
}

impl Scene for Polish {
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
        // the track the wafer rides on, and a marker over the station that is active now
        c.hline(2, TRACK, w - 4, '═');
        c.put(station_mid(t.beat), BOX_BOT + 1, '▼');
        wafer(c, t);
        // swarf bin under the saw; a ship box under the clean
        titled_box(c, station_x(1), 20, SW, 3, "swarf");
        titled_box(c, station_x(6), 20, SW, 3, "ship");
        c.text(X0, 25, "▓ wafer   ▒ wheel or saw   ═ track   ▼ station now   ▪ slices   ° bubbles");
        c.text(X0, 27, "next: WAFER (inspect and ship)");
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
}


pub fn build() -> Box<dyn Scene> {
    Box::new(Polish)
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
