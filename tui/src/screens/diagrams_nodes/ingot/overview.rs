// INGOT overview in the picture-and-panel template: the as-pulled rod moves through six stations,
// cropped, tested on its cut face, ground to 300 mm, notched and wire-sawn. Played back from the
// Blender scene (tools/pbr3d/blender/ingot_overview.py). Zooms (a-d) open the grind, the notch,
// the X-ray test and the wire saw (tools/pbr3d/blender/ingot_zooms.py).
//
// Sources: page text (INGOT.txt sections 1-9) and INGOT.details.txt; Wikipedia, Czochralski method
// and Wafer (electronics); SV029 datasheet (300 mm wafer: diameter, notch); US 8,376,809 (Sumco
// grinder); US 11,551,922 (periphery grind and notch); US 5,529,051 (<110> found by X-ray); US 12617032
// and US 12605863 (crop, grind, notch, saw steps, patent text); US 9,988,736 (tail growth).
// The rod drawings are schematic, not to scale.

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("as-pulled: a rough rod with a cone on each end, a little over 300 mm", BEAT_MS)
        .note(
            "The rod comes off the puller as a rough, slightly wavy cylinder: a seed cone and neck at one end, a tail cone at the other. It is ground to size later, so it is left a little over 300 mm and not round.",
            "a grey rod on two cradles, a pale rough skin wider than the body under it, and a dark cone at each end",
        )
        .detail(
            "The rod holds the value of one whole furnace run, so each later step tries to keep as much of it as possible.",
            &[
                "Up to about 2 m long and several hundred kg (Wikipedia, Czochralski method)",
                "The as-pulled rod is oversize and not round (INGOT page)",
                "A 450 mm crystal would have weighed about 1 tonne (INGOT details)",
            ],
        ),
    Beat::new("crop: blades cut the seed and tail cones off at the joints", BEAT_MS)
        .note(
            "Saw blades take the two cones off at the crop lines. The cones fall away as scrap, and the body is left with flat cut faces ready for testing.",
            "two thin steel blades at the joints of the rod, and the dark cones dropping away below it",
        )
        .detail(
            "Where the cut goes is set by measurement, not at a fixed distance. A conservative crop loses silicon; an aggressive one passes marginal wafers to customers.",
            &[
                "Cropping also removes zones with voids or contamination (patent text, US 12617032)",
                "The tail is the most contaminated end, since dopants and metals concentrate in the last melt (textbook)",
                "Crop length is part of the wafers-per-pull figure; no source here gives that number",
            ],
        ),
    Beat::new("test: X-ray on the cut face checks the orientation before grinding", BEAT_MS)
        .note(
            "A test sample is taken from the cut face and X-rays are aimed at it. The reflected beam makes spots, and when they line up the crystal plane is found. The orientation is confirmed before the rod is committed to grinding and slicing.",
            "a cyan X-ray beam hitting the flat end face, a reflected beam to a detector block, and four bright spots on the face",
        )
        .detail(
            "This is the last cheap point to reject a crystal. Rejecting after slicing wastes saw time and wire.",
            &[
                "Orientation is checked by X-ray diffraction against the intended Miller plane (INGOT details)",
                "The notch tolerance is <110> +/- 1 degree (vendor datasheet)",
                "{100} for logic and CMOS, {111} for bipolar, power and MEMS (Wikipedia infobox)",
            ],
        ),
    Beat::new("grind OD: a wheel grinds the rod round to 300 mm", BEAT_MS)
        .note(
            "A grind wheel runs along the rough rod and takes the oversize skin off, so the finished cylinder is round and at the target outer diameter.",
            "a dark wheel pressed onto the top of the rod, a row of orange sparks where it touches, and the pale skin going",
        )
        .detail(
            "Diameter control matters because wafer handling robots, FOUPs and every downstream tool assume the 300 mm standard. The removed material is silicon that was already pulled and paid for.",
            &[
                "Diameter 300 mm, tolerance +/- 0.2 mm (vendor datasheet, SV029)",
                "A grind wheel brings the ingot to target outer diameter and length (patent text, US 12617032)",
                "Grinding damage, chipping at the ends and wheel wear causing taper are the failure modes (INGOT details)",
            ],
        ),
    Beat::new("notch: a 90 degree V groove is ground the full length, marking <110>", BEAT_MS)
        .note(
            "A V groove is ground along the whole length of the cylinder. It marks the <110> direction, so every tool can align the wafer to the crystal.",
            "an orange V-shaped groove running along the top of the cylinder from one end to the other",
        )
        .detail(
            "Wafers of 200 mm and up carry one notch instead of flats, because a notch wastes less area. The notch marks <110> and does not show doping type.",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle, on <110> +/- 1 degree (vendor datasheet, SV029)",
                "Periphery grind and notch: an arc or approximate V groove marks <110> (US 11,551,922)",
                "450 mm wafers were to be notchless, with a laser mark (INGOT page)",
            ],
        ),
    Beat::new("wire saw: a diamond wire web slices the ingot into wafers", BEAT_MS)
        .note(
            "The ingot is bonded to a mounting beam and lowered into a web of diamond-abrasive wire, which cuts every wafer at once. The wire pitch sets the wafer thickness plus the kerf.",
            "the rod with a pale mounting beam on top, the wires running across it, and the cut wafers starting to part along the kerf",
        )
        .detail(
            "Saw loss is silicon that was already grown, so thinner wire is a direct yield gain. The page finds no kerf, speed or wafers-per-ingot number for 300 mm sawing.",
            &[
                "Wafer thickness 775 um, +/- 25 um in vendor sheets (INGOT page)",
                "Wire pitch sets wafer thickness plus kerf (INGOT page)",
                "No kerf number for 300 mm sawing was found (INGOT page)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the grind to 300 mm",
        build: || -> Box<dyn Scene> { zoom::grind() },
    },
    Zoom {
        key: 'b',
        label: "the V notch along the length",
        build: || -> Box<dyn Scene> { zoom::notch() },
    },
    Zoom {
        key: 'c',
        label: "X-ray on the cut face",
        build: || -> Box<dyn Scene> { zoom::test() },
    },
    Zoom {
        key: 'd',
        label: "the wire web slices the ingot",
        build: || -> Box<dyn Scene> { zoom::saw() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/ingot_overview.glb"),
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
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "INGOT overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "INGOT overview");
    }
}
