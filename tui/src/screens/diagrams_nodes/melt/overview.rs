// MELT + PULL overview: a Czochralski puller cut open so the inside shows, played back from the
// Blender scene (tools/pbr3d/blender/melt_overview.py) in the picture-and-panel template. Load
// polysilicon and dopant into a quartz crucible, melt it under argon, dip a seed and pull a thin
// dash neck, flare the shoulder, grow the body, taper the tail and lift the crystal clear.
// Zooms (a-c) open the dash neck, the melt convection with its magnetic field, and the hot zone
// with its argon sweep (tools/pbr3d/blender/melt_zooms.py).
//
// Sources: COMSOL, thermal analysis of a Czochralski furnace (model); Wikipedia, Czochralski method; US 6,866,713
// (dash neck); US 7,179,330 (dash-free neck); US 9,988,736 (tail growth); Journal of Synthetic Crystals 52(4)
// (2023), 300 mm pull-rate study.

use super::super::blender::{Cell, Page, BEAT_MS};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("polysilicon chunks and a measured dose of dopant are loaded into a quartz crucible", BEAT_MS)
        .note(
            "The charge is the electronic-grade polysilicon from the POLYSILICON page, broken into chunks, plus dopant (boron or phosphorus) weighed to set the target resistivity. It is packed into a quartz crucible, which sits in a graphite susceptor, before the chamber is sealed.",
            "grey chunks dropping into the white quartz crucible, with a few blue dopant specks among them",
        )
        .detail(
            "The dopant mass sets the resistivity of the whole crystal. Any metal or carbon loaded here dissolves into the melt and cannot be removed later.",
            &[
                "Segregation: dopant prefers the liquid, so the melt gets richer and the tail ends up more heavily doped than the head",
                "Recharge: fresh undoped poly added during the pull refills the melt and dilutes the dopant, so one crucible makes a longer crystal",
                "Liquid feed (continuous Czochralski) keeps the melt steady but adds contamination and cooling risk, so solid recharge is usual",
            ],
        ),
    Beat::new("the charge melts at about 1414 C under flowing argon, then holds just above freezing", BEAT_MS)
        .note(
            "A graphite heater inside felt insulation brings the charge above the silicon melting point. Argon flows down through the chamber to carry away SiO and CO and keep oxygen low. The melt is then held steady so the seed meets it at the right temperature.",
            "the heater ring glowing orange, the chunks shrinking as the orange melt rises, and pale blue argon running down past the shield and out at the bottom",
        )
        .detail(
            "A stable, flat melt is needed before seeding. Rushing the seed causes temperature drift and a diameter that wanders.",
            &[
                "COMSOL model: melt near 1414 C, contact 1403-1407.5 C, argon 100 L/min at 2500 Pa",
                "Wikipedia quotes 1425 C for semiconductor-grade silicon, so the exact figure depends on the source",
                "The model's graphite heater is about 310 kW and needs about 400 minutes to reach a steady contact temperature",
            ],
        ),
    Beat::new("the seed touches the melt; a thin dash neck is pulled fast to purge dislocations", BEAT_MS)
        .note(
            "A small oriented seed crystal is lowered on its wire until it touches the melt. The contact shock creates dislocations, so a thin neck, 2-4 mm across, is pulled at high speed. The dislocations slide out through the neck surface before the body starts.",
            "the seed coming down to the orange surface, settling, then rising with a thin bright neck growing under it",
        )
        .detail(
            "Everything hangs from this neck, so it is the most failure-prone step. A neck break drops the whole crystal into hot silicon.",
            &[
                "Neck pulled up to about 6 mm/min (US 6,866,713)",
                "About 100-125 mm of neck is needed to purge dislocations (US 6,866,713)",
                "Dash-necked crystals are limited to about 100 kg (patent text)",
            ],
        ),
    Beat::new("shoulder: the melt is cooled slightly and the crystal flares out to 300 mm", BEAT_MS)
        .note(
            "The temperature is trimmed down and the pull slowed so the crystal widens along a cone to full diameter. A sudden jump from the thin neck would be a sharp corner that concentrates stress, so the cone is gradual. The heat shield above the melt shapes the temperature at the edge of the crystal.",
            "the cone widening on the melt surface under the grey heat shield",
        )
        .detail(
            "Too steep a flare can start new dislocations or twin the crystal. Dislocations that survived the neck can multiply as it widens.",
            &[
                "Target diameter is 300 mm for modern wafers",
                "The shoulder is later cropped off as scrap",
                "A failure here wastes the whole charge",
            ],
        ),
    Beat::new("body: grows at about 1.0-1.6 mm a minute while the crucible rises with the falling melt", BEAT_MS)
        .note(
            "The saleable body grows as the seed rises into the pull chamber. Crystal and crucible counter-rotate to stir the melt, so temperature and dopant stay even and the freezing front stays flat. The crucible is lifted as the melt gets shallower, so the interface stays at the same height.",
            "the body lengthening up into the pull chamber while the crucible creeps up and the melt gets shallower",
        )
        .detail(
            "The freezing front must stay flat. A faster pull pushes it convex or concave, locks in stress and defects, and shifts oxygen. Yield is set here.",
            &[
                "1.0 mm/min of 300 mm crystal is about 9.9 kg/h; 1.6 mm/min is about 15.8 kg/h (computed, density 2.33 g/cm3)",
                "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
                "Up to about 2 m long and several hundred kg (Wikipedia)",
            ],
        ),
    Beat::new("tail: tapers to an end cone, then the crystal is lifted clear of the melt to cool", BEAT_MS)
        .note(
            "At the end the diameter is tapered and the crystal is lifted off the melt in steps while it cools. An abrupt lift-off is a thermal shock that can send slip dislocations back up into the body; the taper makes the release gradual.",
            "the bottom of the crystal narrowing to a cone, then the whole crystal rising clear of the melt",
        )
        .detail(
            "The tail is the most contaminated zone, since segregation pushes dopants and metals into the last liquid to freeze. It is cropped off in the INGOT step.",
            &[
                "A tail-growth method suppresses slip dislocations (US 9,988,736)",
                "The finished rod is the INGOT node",
                "The charge left in the crucible and the tail are non-wafer silicon",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the dash neck",
        build: || -> Box<dyn Scene> { zoom::neck() },
    },
    Zoom {
        key: 'b',
        label: "melt convection and the magnetic field",
        build: || -> Box<dyn Scene> { zoom::conv() },
    },
    Zoom {
        key: 'c',
        label: "the hot zone and the argon sweep",
        build: || -> Box<dyn Scene> { zoom::hot() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/melt_overview.glb"),
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
        super::super::super::blender::explained(s.as_ref(), "MELT + PULL overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abc");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "MELT + PULL overview");
    }
}
