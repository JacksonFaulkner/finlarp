// WAFER overview: a polished 300 mm disc through its optional layer, inspection, the FOUP and the
// fab, drawn in Blender (tools/pbr3d/blender/wafer_overview.py) in the picture-and-panel template.
// Zoom-ins a-d open the flatness sites, the epi layer, SOI by Smart Cut and the spec sheet
// (tools/pbr3d/blender/wafer_zooms.py).
//
// Sources: SEMI 2025 wafer shipments and revenue [1]; vendor 300 mm datasheets SV029 and SV031 [2];
// SEMI M1 and M43 [3]; SFQR patent US 12,635,427 [4]; Semiconductor Engineering shares 2021 [5];
// GEP top-five concentration 2018 [6]; SOI implant depth US 8,497,187 [7]; 300 mm market blog, low
// confidence [8]; China wafer landscape 2026 [9].

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("polished: a blank 300 mm disc with a mirror top face", BEAT_MS)
        .note(
            "The starting point is a prime wafer: single-crystal silicon, sliced, lapped, etched and polished to a mirror on the top face. Almost every chipmaker buys it rather than growing it.",
            "a flat grey disc with a bright mirror top, a small dark notch on the rim, and tags for the wafer and its thickness",
        )
        .detail(
            "The fab treats this polished top as the flat reference for every later layer. Its thickness is set on the vendor datasheet.",
            &[
                "775 +/- 25 um thick, TTV 5 um or less, edge exclusion 3.0 mm (SV029 datasheet, [2])",
                "200 mm and 300 mm dominate wafer volume; 150 mm and below are legacy (textbook)",
            ],
        ),
    Beat::new("epi or SOI: an optional layer grows on the top face", BEAT_MS)
        .note(
            "Epi is a thin single-crystal layer grown by CVD on the polished wafer, by the wafer maker. SOI, a bonded device layer over a buried oxide, is the other upgrade and is shown in the zooms.",
            "a tan layer grows up across the top face of the grey disc, until it covers the whole top",
        )
        .detail(
            "Epi and SOI are the optional upgrades that separate commodity wafers from AI-grade ones. Each rung up the ladder has fewer qualified suppliers and a higher price (textbook).",
            &[
                "Epi 1 to 10 um, about 3 to 6 um typical (patents, not a standard)",
                "SOI layer about 2 um max at roughly 200 keV implant (US 8,497,187, [7])",
            ],
        ),
    Beat::new("inspect: a scan bar checks flatness and particles", BEAT_MS)
        .note(
            "Inspection decides whether a wafer is shippable. Flatness is checked as TTV, SFQR and nanotopography, and surface particles are counted by laser scanning (textbook). A cyan scan bar crosses the disc from one side to the other.",
            "a bright cyan bar sweeps across the tan-topped disc, edge to edge, with a tag for TTV, SFQR and particles",
        )
        .detail(
            "A wafer that passes for one fab can fail another. Buyers set the limits per node and per customer.",
            &[
                "TTV under 1 um and site flatness under 0.1 um at 10 nm nodes and beyond (vendor guidance, not a standard)",
                "SEMI M1 numeric SFQR limits are not public; buyers set them per node (page section 3)",
            ],
        ),
    Beat::new("pack: the wafer slides into a FOUP carrier for shipping", BEAT_MS)
        .note(
            "Finished wafers ship to the fab in sealed carriers. For 300 mm the standard is the FOUP (front opening unified pod), which replaced SMIF pods in the mid-1990s. Here the disc slides into a glass-walled carrier.",
            "the disc slides off to the right into a clear carrier with glass walls on a steel base, with a tag for 25 wafers at 10 mm pitch",
        )
        .detail(
            "Purge options exist because moisture and airborne molecular contamination in the carrier can corrupt a wafer between steps.",
            &[
                "A standard FOUP holds 25 wafers at a 10 mm slot pitch (secondary sources)",
                "Entegris A300: 25-slot and 13-slot versions for bonded and thin wafers (datasheet)",
            ],
        ),
    Beat::new("fab: litho, etch, deposit and CMP all start from this flat face", BEAT_MS)
        .note(
            "The wafer comes out on a chuck. Everything downstream starts from its flat top face: deposition, lithography, etch and polish each build on it. Defects or warp that arrive with the wafer travel through hundreds of steps.",
            "the disc sits on a chuck in front of four grey tool blocks in a row, with a tag naming litho, etch, deposit and CMP",
        )
        .detail(
            "Incoming wafer quality shows up as yield (textbook). Company commentary points to tightness at the leading edge.",
            &[
                "GlobalWafers, Aug 4 2026 call: existing 300 mm capacity, excluding new lines, is fully utilized",
                "UBS, Sept 18 2026: 12-inch utilization 84% in 2026 rising to 99% in 2028 (broker view)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "flatness sites",
        build: || -> Box<dyn Scene> { zoom::sites() },
    },
    Zoom {
        key: 'b',
        label: "the epi layer",
        build: || -> Box<dyn Scene> { zoom::epi() },
    },
    Zoom {
        key: 'c',
        label: "SOI by Smart Cut",
        build: || -> Box<dyn Scene> { zoom::soi() },
    },
    Zoom {
        key: 'd',
        label: "the spec sheet",
        build: || -> Box<dyn Scene> { zoom::spec() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/wafer_overview.glb"),
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
        assert_eq!(s.beats().len(), 5);
        super::super::super::blender::explained(s.as_ref(), "WAFER overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
        for z in s.zooms() {
            assert_eq!((z.build)().beats().len(), 4, "zoom {}", z.key);
        }
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "WAFER overview");
    }
}
