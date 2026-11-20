// LITHO overview: one layer through the exposure scanner, played back from the Blender scene
// (tools/pbr3d/blender/litho_overview.py) in the picture-and-panel template. Align the wafer
// with the sensor, light the reticle, print the image 4x smaller through the lens, scan one field
// and step across the wafer, develop, then etch and renew the resist for the next layer.
// Zooms a-f open the reticle, the lens and NA, the resist, step and scan, overlay and EUV light
// (tools/pbr3d/blender/litho_zooms.py).
//
// Sources: ASML TWINSCAN EXE:5000 product page (NA 0.55, 8 nm); ASML "5 things you should know
// about High NA EUV lithography" (2024); ASML annual report 2024 and 20-F FY2025 (NXE:3800E 220
// wafers per hour, matched overlay 0.9 nm); US 6,839,125 (k1 floor ~0.25).

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("align: the sensor reads the marks on the wafer", BEAT_MS)
        .note(
            "A wafer coated with photoresist sits on the wafer stage. The alignment sensor reads the marks left by the layer below, so the stage knows exactly where that layer is.",
            "the green sensor beside the lens sends a beam down to the cross-shaped mark on the wafer",
        )
        .detail(
            "This layer must land on the one below to within a few nanometres, so every exposure starts by measuring the wafer.",
            &[
                "Matched-machine overlay down to 0.9 nm on the NXE:3800E (ASML annual report 2024)",
                "One reticle per layer; every layer of the array is printed this way",
            ],
        ),
    Beat::new("the source lights the reticle", BEAT_MS)
        .note(
            "The source sends light down through the reticle. The pattern is chrome on clear quartz: light passes the openings and stops on the chrome.",
            "the yellow light plate above the reticle glows, and light runs down through the gaps between the chrome bars",
        )
        .detail(
            "The wavelength sets how fine a line can be printed. DUV uses 193 nm light, EUV 13.5 nm.",
            &["DUV ArF: 193 nm", "EUV: 13.5 nm"],
        ),
    Beat::new("the lens prints the image 4x smaller on the resist", BEAT_MS)
        .note(
            "The projection lens collects the light from the reticle and focuses it on the wafer at a quarter of the size.",
            "the rays converge down the lens barrel to points on the wafer, and a yellow slit glows under the lens",
        )
        .detail(
            "Printing smaller than the mask keeps mask errors small too: a reticle defect shrinks with the image.",
            &[
                "Reduction: 4x on NXE EUV and DUV scanners",
                "High-NA fields are half size (ASML, 2024)",
            ],
        ),
    Beat::new("scan: the wafer and the reticle move opposite ways", BEAT_MS)
        .note(
            "The slit only covers a strip of the field. The wafer slides one field width under it while the reticle slides the other way, 4x as far, so the field is printed strip by strip.",
            "one field on the wafer turns pink as the wafer slides under the yellow slit, with the reticle sliding the other way",
        )
        .detail(
            "Scanning lets a small, well-corrected slit of the lens print a large field.",
            &["Reticle moves 4x as far as the wafer (the 4x reduction)"],
        ),
    Beat::new("step: the stage moves field to field across the wafer", BEAT_MS)
        .note(
            "After each field the stage steps to the next and scans again, so the same pattern repeats across the wafer.",
            "the wafer steps along the row of fields, and the exposed fields fill in pink one after another",
        )
        .detail(
            "Throughput is money: a scanner that prints more wafers per hour costs less per layer.",
            &[
                "NXE:3800E: 220 wafers per hour (ASML 20-F FY2025)",
                "NXE:3600D: 160 wafers per hour (ASML annual report 2024)",
            ],
        ),
    Beat::new("develop: the exposed resist dissolves and the pattern stands", BEAT_MS)
        .note(
            "The light changed the resist's chemistry, not its shape. Develop dissolves the exposed part (positive resist), so the film below shows through where the light fell.",
            "the pink fields turn cyan as the exposed resist washes away and the film shows through",
        )
        .detail(
            "The gaps are the pattern. The resist that stays protects the film while etch cuts the gaps into it.",
            &["Positive resist: the exposed part develops away (page text)"],
        ),
    Beat::new("the wafer goes to etch; fresh resist for the next layer", BEAT_MS)
        .note(
            "Etch copies the gaps into the film, the resist is stripped, a new film goes on and the wafer is coated again. Then it comes back for the next layer.",
            "the cyan open fields fade back to purple resist, ready for the next layer",
        )
        .detail(
            "A DRAM wafer goes round this loop once per patterned layer, so litho cost is paid many times over.",
            &["Each layer has its own reticle and its own alignment to the layer below (page text)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the reticle: chrome on quartz, copied to every die",
        build: || -> Box<dyn Scene> { zoom::reticle() },
    },
    Zoom {
        key: 'b',
        label: "the lens: numerical aperture and the finest line",
        build: || -> Box<dyn Scene> { zoom::lens() },
    },
    Zoom {
        key: 'c',
        label: "inside the resist: expose, develop, etch",
        build: || -> Box<dyn Scene> { zoom::resist() },
    },
    Zoom {
        key: 'd',
        label: "step and scan: field by field across the wafer",
        build: || -> Box<dyn Scene> { zoom::scan() },
    },
    Zoom {
        key: 'e',
        label: "overlay: lining up with the layer below",
        build: || -> Box<dyn Scene> { zoom::overlay() },
    },
    Zoom {
        key: 'f',
        label: "EUV light: tin, plasma and mirrors",
        build: || -> Box<dyn Scene> { zoom::euv() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/litho_overview.glb"),
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
        super::super::super::blender::explained(s.as_ref(), "LITHO overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcdef");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "LITHO overview");
    }
}
