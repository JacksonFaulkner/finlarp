// SLICE + POLISH overview: the wafer line, seven stations in page order, one per beat. The wafer rides
// the track from station to station: ingot, slice, lap, etch, edge, polish, clean. Played back from
// tools/pbr3d/blender/slice_overview.py in the picture-and-panel template. Zooms (a-d) open the wire
// web, the lapping plates, the Preston polish and the thickness budget (slice_zooms.py).
//
// Sources: see the zoom and section pages and the page's own list ([1]-[8] in SLICE_POLISH.txt).

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("ingot: a ground 300 mm cylinder goes on the saw", BEAT_MS)
        .note(
            "The line starts with a ground 300 mm ingot, one silicon cylinder on its cradle. It has been pulled, ground and notched; every later station turns it into a polished wafer.",
            "a grey ingot standing on its cradle at the left, with the frame of the wire saw beyond it",
        )
        .detail(
            "The ingot is the feed for the whole line, and its diameter sets the wafer size.",
            &[
                "The ingot is ground to 300 mm and notched (page section 1)",
                "The saw cuts the ingot in the next step (page section 1)",
            ],
        ),
    Beat::new("slice: a diamond wire web cuts the ingot into wafers", BEAT_MS)
        .note(
            "The ingot is fed down through a multi-wire diamond saw. Each pass of the wire cuts one slot in every wafer at once, so the wafers come out one kerf apart.",
            "the ingot sinking through a stack of horizontal steel wires, then seven slices standing with a thin gap where each wire passed",
        )
        .detail(
            "The kerf is silicon turned into swarf, the first loss in the thickness budget.",
            &[
                "Kerf about 125 um for diamond wire today, with a path to about 85 um (page source [1])",
                "Diamond wire cuts about 2x faster than the older slurry technology (page section 4)",
            ],
        ),
    Beat::new("lap: plates take both faces at once and the wafer comes out flat", BEAT_MS)
        .note(
            "The wafer is carried to two lapping plates with loose abrasive slurry between them. Both faces are worked together, which sets flatness and parallelism and removes the saw damage.",
            "a grey wafer under a flat plate that lowers onto it, with thin orange damage rings on its faces",
        )
        .detail(
            "Lapping is the largest planned removal after the kerf, so it is a cost lever on the line.",
            &[
                "Double-side lapping removes 80 to 200 um in total (page section 4)",
                "One 200-300 mm patent example: 80 um in 40 min (page section 4)",
            ],
        ),
    Beat::new("etch: a wet bath strips the damage the saw and lap left", BEAT_MS)
        .note(
            "The wafer goes into a wet alkali or acid bath. The chemistry removes the cracked layer without adding mechanical stress, so the surface is clean silicon again.",
            "the wafer in a teal tank as the liquid rises, and the orange damage rings on its faces fading away",
        )
        .detail(
            "Every later step exists to remove damage, and etching removes it chemically.",
            &[
                "Etch removes about 15-25 um after lapping (page section 4)",
                "One 300 mm patent example: acid etch 10 um, gas-phase etch 2 um (page section 4)",
            ],
        ),
    Beat::new("edge: a resin wheel rounds the sharp rim", BEAT_MS)
        .note(
            "The rim is ground round so it does not chip in handling. The resin wheel turns against the edge while the wafer is held at this station.",
            "a brown resin wheel turning beside the wafer edge",
        )
        .detail(
            "A chipped edge makes particles and can start cracks that run across the wafer under heat in the fab.",
            &[
                "Edge profiling sits between etch and polish on the page (page section 1)",
                "No removal figure for this step was found in the sources (page section 1)",
            ],
        ),
    Beat::new("polish: a pad and slurry leave a mirror face", BEAT_MS)
        .note(
            "A pad turns over the wafer with slurry between them. The chemistry softens the top layer and the abrasive wipes it off, until the face is a mirror.",
            "a tan pad turning over the wafer, a bright sheen moving across the top, and the face turning to a mirror",
        )
        .detail(
            "The polished face is the flat reference for lithography, so this is the last removal step.",
            &[
                "Double-side polish removes 10-20 um; front-side polish 10-15 um in 5-15 min (page section 4)",
                "Polishing is chemical plus mechanical (page section 3)",
            ],
        ),
    Beat::new("clean: the wafer is cleaned, inspected and shipped", BEAT_MS)
        .note(
            "Chemical cleans take off the slurry residue and metal traces. The wafer is inspected against the customer's spec, then shipped.",
            "spray nozzles misting the mirror wafer, which is clean and bright",
        )
        .detail(
            "Customers qualify the wafer, and that qualification is slow to change.",
            &[
                "775 um +/- 25 um thick, TTV 5 um or less (vendor datasheet, see WAFER)",
                "Inspection measures thickness, flatness and particle counts (textbook)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the wire web and its kerf",
        build: || -> Box<dyn Scene> { zoom::web() },
    },
    Zoom {
        key: 'b',
        label: "lapping both faces at once",
        build: || -> Box<dyn Scene> { zoom::lap() },
    },
    Zoom {
        key: 'c',
        label: "Preston polish and pH",
        build: || -> Box<dyn Scene> { zoom::preston() },
    },
    Zoom {
        key: 'd',
        label: "the thickness budget",
        build: || -> Box<dyn Scene> { zoom::budget() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/slice_overview.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "SLICE + POLISH overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "SLICE + POLISH overview");
    }
}
