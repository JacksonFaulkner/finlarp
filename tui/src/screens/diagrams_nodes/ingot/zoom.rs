// INGOT zoom-ins a-d in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/ingot_zooms.py: a grind, b notch, c test (the X-ray cut-face check) and
// d saw. Four beats each.
//
// Sources: US 8,376,809 (Sumco cylindrical grinder, traverse grind): https://patents.google.com/patent/US8376809
//   US 11,551,922 (periphery grind and notch, arc or approximate V groove): https://patents.google.com/patent/US11551922
//   SV029 datasheet, 300 mm wafer (diameter, notch depth, angle, <110> tolerance):
//     https://svmi.com/wp-content/uploads/2021/01/SV029.pdf
//   US 5,529,051 (<110> found by X-ray, flat or notch ground to it): https://patents.google.com/patent/US5529051
//   US 8,256,407, US 9,873,159 (wire saw) and US 12,183,616 (notch on wafers over 200 mm): used for the
//   saw captions only; the 150 mm test-cut pitch and kerf in those patents are not used here.
//   INGOT page text (crop, test, grind, notch and saw steps). The drawings are schematic.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

pub const GRIND_BEATS: &[Beat] = &[
    Beat::new("as-pulled: the rod has a rough skin a little over size, and is not yet round", BEAT_MS)
        .note(
            "The rod as it comes from the crop is wider than its finished size and not quite round. The skin on the outside is what the grinder has to take off.",
            "a grey rod with a rough, slightly uneven outer skin, and a rougher ring on its end face",
        )
        .detail(
            "The finished body must sit within the 300 mm tolerance, so everything outside it is removed.",
            &[
                "The as-pulled rod is oversize and not round (INGOT page)",
                "Up to about 2 m long and several hundred kg (Wikipedia, Czochralski method)",
                "Diameter 300 mm, +/- 0.2 mm (vendor datasheet, SV029)",
            ],
        ),
    Beat::new("the wheel takes the skin off: a traverse grind along the length", BEAT_MS)
        .note(
            "A grinding wheel is brought onto the top of the rod and traverses its length. It takes the rough skin off as it passes, and sparks fly where the wheel meets the surface.",
            "a large dark wheel above the rod, a row of bright sparks where it touches, and the rough skin being removed",
        )
        .detail(
            "Material removed is silicon that was already pulled, so the grind is a yield cost as well as a shape step.",
            &[
                "US 8,376,809: a grinder for silicon ingot, the outer circumference ground by traverse (patent text)",
                "A grind wheel brings the ingot to target outer diameter and length (patent text, US 12617032)",
                "Failure modes: grinding damage or chipping at the ends, and wheel wear causing taper (INGOT details)",
            ],
        ),
    Beat::new("round body at 300 mm: the rough skin is gone", BEAT_MS)
        .note(
            "With the skin ground away the body is a smooth, round cylinder at its target outer diameter. Its surface is what the wafers will be cut from.",
            "a plain grey cylinder with a smooth surface, and the wheel no longer touching it",
        )
        .detail(
            "Diameter control matters because wafer handling robots, FOUPs and every downstream tool assume the 300 mm standard.",
            &[
                "Diameter 300 mm, +/- 0.2 mm (vendor datasheet, SV029)",
                "The page's 300 mm wafer: 775 um thick, about 125 g (Wikipedia, Wafer (electronics))",
                "Wafer handling robots and FOUPs assume the 300 mm standard (INGOT details)",
            ],
        ),
    Beat::new("end face: the outline is round at the finished diameter", BEAT_MS)
        .note(
            "Looking along the axis, the end of the body is a round disc at the finished diameter. The grinder sets the edge of that disc, not the shape of the cut.",
            "a grey disc at the end of the cylinder, round, with the body behind it",
        )
        .detail(
            "The grind tolerance is the one the wafer spec needs. SEMI M1 governs polished wafers; its tables were not fetched for this page.",
            &[
                "Diameter 300 mm, +/- 0.2 mm (vendor datasheet, SV029)",
                "SEMI M1 governs polished single-crystal wafers (INGOT page; tables not fetched)",
                "Grinding removes the surface layer that grew against the hot zone (INGOT details)",
            ],
        ),
];

pub const NOTCH_BEATS: &[Beat] = &[
    Beat::new("the ground cylinder before the notch: a plain round body", BEAT_MS)
        .note(
            "The body is round and ground to size. Nothing yet marks the crystal direction on it, so the notch is the next step.",
            "a plain grey cylinder with no groove on its top",
        )
        .detail(
            "The notch is the reference every tool uses to line up the wafer, so it has to be ground to the right direction.",
            &[
                "Diameter 300 mm, +/- 0.2 mm (vendor datasheet, SV029)",
                "Notch on the wafer rim marks <110> (INGOT page)",
                "Wafers of 200 mm and up use a notch, not flats (INGOT page)",
            ],
        ),
    Beat::new("the V groove grows along the length, from one end to the other", BEAT_MS)
        .note(
            "A V groove is ground along the top of the cylinder, growing from one end to the other. It runs the whole length, so it marks the crystal direction everywhere along the body.",
            "an orange-gold groove growing along the top of the cylinder from left to right",
        )
        .detail(
            "A notch that is too sharp can seed a crack at the wafer edge, so the angle and depth are set by the datasheet (textbook).",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle, on <110> +/- 1 degree (vendor datasheet, SV029)",
                "Periphery grind and notch: an arc or approximate V groove marks <110> (US 11,551,922)",
                "The notch runs along the full length of the ground body (INGOT page)",
            ],
        ),
    Beat::new("end view: the groove is a V in the top edge, 90 degrees, 1.0 mm deep", BEAT_MS)
        .note(
            "Looking along the axis, the end face is a circle with the V groove cut into its top edge. The groove is the same all the way along the body, so the end view shows its shape.",
            "the end face: a grey circle with a gold V notch cut into its top rim",
        )
        .detail(
            "Misalignment of the notch shows up later as pattern placement errors and as chipping at dicing (textbook).",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle (vendor datasheet, SV029)",
                "The notch tolerance is <110> +/- 1 degree (vendor datasheet, SV029)",
                "450 mm wafers were to be notchless, with a laser mark (INGOT page)",
            ],
        ),
    Beat::new("the notch on a wafer rim marks <110>, to within 1 degree", BEAT_MS)
        .note(
            "A wafer is shown with its V notch on the rim and an arrow from the centre to the notch. The notch lines up with the <110> direction, to within 1 degree.",
            "a grey wafer disc with its V notch on the rim, and a gold arrow from the centre out to the notch",
        )
        .detail(
            "The notch does not show doping type. Silicon cleaves along {110}-family directions, so the notch lines dies up with the cleavage planes (textbook).",
            &[
                "<110> +/- 1 degree (vendor datasheet, SV029)",
                "US 5,529,051: the (110) direction is found by X-ray and marked; the flat or notch is ground to it, to about 1 degree (patent text)",
                "The notch marks <110> and does not show doping type (INGOT page)",
            ],
        ),
];

pub const TEST_BEATS: &[Beat] = &[
    Beat::new("the cut face, from the crop: a flat end is ready to test", BEAT_MS)
        .note(
            "After the crop the end of the body is a flat face. A test sample is taken from this face to check the orientation before the rod is ground and sliced.",
            "a grey cylinder with a flat cut end, and the X-ray source and detector blocks beside it",
        )
        .detail(
            "Orientation is set by the seed in MELT + PULL, so a mis-seeded crystal is discovered at this test.",
            &[
                "Test samples are taken from the cut faces after cropping (INGOT details)",
                "{100} for logic and CMOS, {111} for bipolar, power and MEMS (Wikipedia infobox)",
                "Orientation is checked by X-ray diffraction against the intended Miller plane (INGOT details)",
            ],
        ),
    Beat::new("X-ray beam onto the face: the beam is reflected into the detector", BEAT_MS)
        .note(
            "The X-ray beam is aimed at the cut face. The reflected beam leaves the face at an angle set by the crystal planes, and a detector picks it up.",
            "a cyan beam going in from the upper right, bouncing off the end face and out to the lower detector block",
        )
        .detail(
            "The reflected beam angle is what gives the orientation, so the detector position is fixed for each plane tested.",
            &[
                "Orientation checked by X-ray diffraction against the intended Miller plane (INGOT details)",
                "Notch tolerance <110> +/- 1 degree (vendor datasheet, SV029)",
                "Test samples come from the cut faces, before grinding (INGOT page)",
            ],
        ),
    Beat::new("spots scattered: the plane is not yet found", BEAT_MS)
        .note(
            "The diffraction spots appear on the face, but they are scattered. The plane is not yet identified, so the orientation is not yet confirmed.",
            "four bright spots scattered around the centre of the face",
        )
        .detail(
            "A spot pattern that does not line up means the crystal is not on the intended plane, which is the case for a mis-seeded crystal.",
            &[
                "A mis-seeded crystal is discovered at this test (INGOT details)",
                "Customers audit these specs during qualification, which takes years (INGOT details)",
                "Resistivity check step: no source found (INGOT page)",
            ],
        ),
    Beat::new("spots line up: the plane is found and marked", BEAT_MS)
        .note(
            "The spots move into a symmetric cross on the face. The plane is found, and it is marked so the grinder and notch tool can use it.",
            "four spots in a cross around the centre of the face, one on each side",
        )
        .detail(
            "This is the last cheap point to reject a crystal. Rejecting after slicing wastes saw time and wire.",
            &[
                "The notch tolerance is <110> +/- 1 degree (vendor datasheet, SV029)",
                "{100} for logic and CMOS; {111} for bipolar, power and MEMS (Wikipedia infobox)",
                "Rejecting after slicing wastes saw time and wire (INGOT details)",
            ],
        ),
];

pub const SAW_BEATS: &[Beat] = &[
    Beat::new("the wire web: a row of fine wires strung between two rollers", BEAT_MS)
        .note(
            "A single long wire is wound around grooved guide rollers to make a web. The gaps between the wires are where the cuts will be made.",
            "a row of thin wires strung between two rollers, with the mounting beam and rod above",
        )
        .detail(
            "Diamond abrasive on the wire does the cutting, so every wafer is cut at once.",
            &[
                "A single wire is wound around grooved guide rollers to form a web (INGOT page)",
                "Diamond abrasive on the wire does the cutting (INGOT page)",
                "US 9,873,159: a diamond-coated wire saw, the wire web from guide rollers (patent text)",
            ],
        ),
    Beat::new("the ingot is fed down: it is bonded to a mounting beam and lowered", BEAT_MS)
        .note(
            "The ingot is bonded to a mounting beam, which holds it while the wire passes. It is lowered down through the web at a steady pace.",
            "the grey rod with a pale mounting beam on top, dropping towards the wire web",
        )
        .detail(
            "The mounting beam is the reference for the saw, so the wafers stay attached to it while the wire exits.",
            &[
                "The ingot is bonded to a mounting beam (INGOT page)",
                "US 9,873,159: beam lowered at table speed (patent text)",
                "Wafer thickness plus kerf sets the wafer count per ingot (textbook)",
            ],
        ),
    Beat::new("each wire leaves a wafer: the wire cuts through the ingot", BEAT_MS)
        .note(
            "As the ingot passes the wires, each cut makes a wafer. The wires cut through the whole diameter, so each pass leaves a slice of the body.",
            "the rod with thin slices forming along its length, and the wires visible between them",
        )
        .detail(
            "Wire pitch sets the wafer thickness plus the kerf. This page found no kerf number for 300 mm sawing.",
            &[
                "Wire pitch sets wafer thickness plus kerf (INGOT page)",
                "No kerf, speed or wafers-per-ingot number for 300 mm sawing was found (INGOT page)",
                "Wafer thickness 775 um, +/- 25 um in vendor sheets (INGOT page)",
            ],
        ),
    Beat::new("kerf between wafers: the silicon lost to the wire is the gap", BEAT_MS)
        .note(
            "The wafers part from one another. The kerf is the silicon the wire removes; it is the gap between each pair of wafers.",
            "a row of thin wafers spaced apart along the rod, with a gap between each pair",
        )
        .detail(
            "Wafers per ingot is the ingot length divided by the thickness plus kerf (textbook). Thinner wire is a direct yield gain.",
            &[
                "Solar wafers: diamond wire about 125 um kerf, against about 150 um for slurry (TaiyangNews/ITRPV; solar, not 300 mm)",
                "No kerf number for 300 mm sawing was found (INGOT page)",
                "Diamond wire roughly 2x faster than slurry for solar (TaiyangNews/ITRPV; solar, not 300 mm)",
            ],
        ),
];

static GRIND: Cell = std::sync::OnceLock::new();
static NOTCH: Cell = std::sync::OnceLock::new();
static TEST: Cell = std::sync::OnceLock::new();
static SAW: Cell = std::sync::OnceLock::new();

pub fn grind() -> Box<dyn Scene> {
    page(
        &GRIND,
        include_bytes!("../../../../../tools/pbr3d/assets/ingot_grind.glb"),
        GRIND_BEATS,
    )
}

pub fn notch() -> Box<dyn Scene> {
    page(
        &NOTCH,
        include_bytes!("../../../../../tools/pbr3d/assets/ingot_notch.glb"),
        NOTCH_BEATS,
    )
}

pub fn test() -> Box<dyn Scene> {
    page(
        &TEST,
        include_bytes!("../../../../../tools/pbr3d/assets/ingot_test.glb"),
        TEST_BEATS,
    )
}

pub fn saw() -> Box<dyn Scene> {
    page(
        &SAW,
        include_bytes!("../../../../../tools/pbr3d/assets/ingot_saw.glb"),
        SAW_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("grind", grind as fn() -> Box<dyn Scene>),
            ("notch", notch),
            ("test", test),
            ("saw", saw),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
