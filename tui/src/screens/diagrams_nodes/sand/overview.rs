// SAND page overview: the submerged-arc furnace (cut in half so the inside shows) and its plant,
// played back from the Blender scene (tools/pbr3d/blender/sand_overview.py) through pbr3d. The
// picture is the 3D scene on the left, with tags pinned to the parts the beat is about, and the
// beat's text in a panel on the right (pbr3d::caption). Zoom-ins (a-d) open the cavity, crust and
// stoking, tapping, and the bag filter.

use std::sync::OnceLock;

use super::{zoom, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new(
        "hoppers feed quartzite (SiO2) and carbon (coke, wood chips) onto the burden",
        BEAT_MS,
    )
    .note(
        "Quartzite is the silicon source. Coke and wood chips are the reductant, and the chips keep the pile open for gas. They drop in continuously, so the whole burden slowly sinks.",
        "lumps falling down the two chutes onto the charge, which sinks a little as they land",
    )
    .detail(
        "Everything downstream depends on a loose, evenly mixed burden. Chips and coke open gaps so hot gas can climb through, and lumps rather than dust keep those gaps from clogging.",
        &[
            "Textbook overall reaction: SiO2 + 2C gives Si + 2CO, which absorbs a lot of heat",
            "Power: 11-13 MWh per tonne of silicon, the furnace's biggest cost",
            "The charge sinks continuously as it is consumed and refilled from the top",
        ],
    ),
    Beat::new(
        "at each electrode tip an arc holds a gas cavity above 1800 C: SiO2 + C ─▶ SiO + CO, then SiC + SiO ─▶ 2Si + CO",
        BEAT_MS,
    )
    .note(
        "This is where silicon is made. The arc keeps a cavity of SiO and CO gas open under each electrode. SiC + SiO gives 2Si + CO (reaction 1), and the liquid silicon drains to the pool. Gas that climbs into the cooler shaft is recaptured as SiC or condensed back to SiO2 + Si, so it stays in the furnace.",
        "a glowing cavity under each electrode, the silicon pool below it, and the rising gas paler above",
    )
    .detail(
        "The cavity is the engine of the furnace. It has to stay open and hot enough for the two key reactions, which is why electrode position and power are controlled so carefully. Recapturing SiO keeps the yield up: SiO that escapes is silicon lost.",
        &[
            "Reaction 1: SiO + SiC gives 2 Si + CO, which makes the tappable silicon",
            "Reaction 2: SiO2 + Si gives 2 SiO, which makes the SiO gas",
            "Reaction 3: 2 SiO gives SiO2 + Si (condensation); reaction 4: SiO + 2C gives SiC + CO (recapture)",
            "Arc zone above 1800 C; silicon melts at 1414 C; hearth 2200-2400 K (Elkem and Oxford ESGI report)",
        ],
    ),
    Beat::new(
        "SiO condenses on the cool charge and a crust builds around each cavity; a stoking car breaks it up",
        BEAT_MS,
    )
    .note(
        "Over hours a hard crust (SiO2, SiC, Si) grows around each cavity. It thickens, rises, and swells the cavity, and charge can no longer fall into the hot zone, so reactions stall. About hourly, operators push a bar down through the crust from a stoking car on the lid, so the charge drops again.",
        "a dark crust swelling round each cavity, then the stoking bar driving down into it",
    )
    .detail(
        "Crust costs output and, if it gets too thick, can force the furnace to be emptied. Stoking is a trade-off between lost output and disturbing the furnace. The aim is to restore the downward flow of charge without disturbing the cavities that are actually making silicon.",
        &[
            "Crust is mainly SiO2 with silicon and SiC mixed in (ESGI report)",
            "It forms where SiO condenses at low temperature: 2 SiO gives SiO2 + Si",
            "Typically about once an hour; the crust is broken up by hand, not removed (Sloman and Elkem)",
            "After months or years the crust or hearth layer may need the furnace emptied, with a productivity penalty",
        ],
    ),
    Beat::new(
        "pool full: the tap hole is lanced, Si runs to the ladle, and a hood pulls fume off the spout",
        BEAT_MS,
    )
    .note(
        "Liquid silicon leaves from the base through the tap hole. Fume is worst during tapping, so a hood over the spout pulls it into the filter line.",
        "the pool level falls as silicon runs down the launder into the ladle",
    )
    .detail(
        "A full pool leaves the cavities nowhere to drip, so the furnace is tapped on a regular schedule. Tapping is also the dirtiest moment for fume.",
        &[
            "Hood over the taphole and spout, called a doghouse, pulls fume into the duct (USPTO 11874064)",
            "Fume is 40-80% of fugitive emissions from tapping, refining and casting at one Norwegian plant (Elkem Salten study)",
            "Only 80-90% of the silicon charged is recovered as product",
        ],
    ),
    Beat::new(
        "hot gas leaves the lid; bag filters catch silica fume and clean gas goes up the stack",
        BEAT_MS,
    )
    .note(
        "SiO that escapes the burden burns in air to ~150 nm SiO2 fume. The off-gas duct carries it to bag filters. The fume is caught and sold as microsilica; only clean gas goes up the stack.",
        "hot gas and fume rising off the lid, along the duct and into the bag house",
    )
    .detail(
        "Catching the fume is both a legal need and a revenue stream. Microsilica is sold, and letting it escape means losing silicon and polluting.",
        &[
            "Fume particles are about 150 nm of SiO2",
            "In one DC furnace 19.5% of the charged silicon was lost as fume",
            "Briquetted microsilica plus carbon made up 0-50% of the charge in a 200 kVA test furnace (2024 preprint)",
        ],
    ),
    Beat::new(
        "ladle metal is refined, cast, crushed and sized into the product",
        BEAT_MS,
    )
    .note(
        "Tapped silicon is refined in the ladle, cast into a solid, crushed and screened to the grain size the customer wants. Only 80-90% of the charged silicon ends up as product.",
        "the ladle empties and the silicon lumps fill the product bin",
    )
    .detail(
        "Customers buy by grade and grain size, so purity and sizing decide the price per tonne.",
        &[
            "Ladle refining with air and oxygen mainly removes Ca and Al into slag (Springer review)",
            "The product is cast, crushed and screened",
            "80-90% of the charged silicon ends up as product",
        ],
    ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "gas cavity at the electrode tip",
        build: zoom::cavity,
    },
    Zoom {
        key: 'b',
        label: "crust growth and stoking",
        build: zoom::crust,
    },
    Zoom {
        key: 'c',
        label: "tapping the metal",
        build: zoom::tap,
    },
    Zoom {
        key: 'd',
        label: "off-gas and the bag filter",
        build: zoom::bag,
    },
];

/// The SAND overview, drawn from the Blender scene (tools/pbr3d/blender/sand_overview.py).
static SAND_SCENE: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &SAND_SCENE,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/sand_overview.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn beats_are_captioned_and_explained() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::tests::explained(s.as_ref(), "overview");
    }

    #[test]
    fn zooms_are_keyed_a_to_d() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
    }

    #[test]
    fn blender_sand_draws_every_beat() {
        super::super::tests::draws_every_beat(build().as_ref(), "overview");
    }

    #[test]
    fn zoom_pictures_draw_every_beat() {
        for z in ZOOMS {
            let s = (z.build)();
            super::super::tests::explained(s.as_ref(), z.label);
            super::super::tests::draws_every_beat(s.as_ref(), z.label);
        }
    }
}
