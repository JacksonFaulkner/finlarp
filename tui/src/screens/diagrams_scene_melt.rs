// MELT + PULL page, overview: the Czochralski puller in the realistic GPU render (pbr3d), in time
// order: load polysilicon and dopant into a quartz crucible, melt it under argon, dip a seed and
// pull a thin dash neck, flare the shoulder, grow the body, taper the tail and lift the crystal
// clear. Zooms (a-c) open the dash neck, the melt convection with its magnetic field, and the hot
// zone with its argon sweep, each a 3D close-up.
//
// Sources: COMSOL, thermal analysis of a Czochralski furnace (model); Wikipedia, Czochralski method; US 6,866,713
// (dash neck); US 7,179,330 (dash-free neck); Journal of Synthetic Crystals 52(4) (2023), 300 mm pull-rate study.

use image::RgbaImage;

use super::diagrams_px as px;
use super::diagrams_scene_melt_zoom as zoom;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};

const BEAT_MS: u64 = 5200;
pub const MIN_W: u16 = 100;
pub const MIN_H: u16 = 30;

/// The MELT + PULL overview picture: the realistic GPU render (pbr3d) at the clock's beat.
/// The orbit turns the camera around the furnace.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    pbr3d::render_melt(
        t.beat,
        t.local,
        (view.yaw - 0.5) as f32, // the far wall carries the nameplate
        (view.pitch - 0.04) as f32,
        view.zoom as f32,
        w,
        h,
        px::BG,
    )
}

const BEATS: &[Beat] = &[
    Beat::new(
        "polysilicon chunks and a measured dose of dopant are loaded into a quartz crucible",
        BEAT_MS,
    )
    .note(
        "The charge is the electronic-grade polysilicon from the POLYSILICON page, broken into chunks, plus dopant (boron or phosphorus) weighed to set the target resistivity. It is packed into a quartz crucible before the chamber is sealed.",
        "Chunks dropping in from the top and piling into the crucible, with a few · dopant specks mixed in.",
    )
    .detail(
        "The dopant mass sets the resistivity of the whole crystal. Any metal or carbon loaded here dissolves into the melt and cannot be removed later.",
        &[
            "Recharge: fresh undoped poly is added during the pull. It dilutes the dopant building up in the melt and refills it, so one crucible makes a longer crystal",
            "Liquid feed (continuous Czochralski) would keep the melt steady, but moving molten silicon adds contamination and cooling risk, so solid recharge is the usual choice",
            "Segregation: silicon freezes out but dopant stays in the liquid, so the melt gets richer and the tail is more heavily doped than the head",
            "A 300 mm pull consumes the charge as one batch",
        ],
    ),
    Beat::new(
        "the charge melts at about 1414 C under flowing argon, then holds just above freezing",
        BEAT_MS,
    )
    .note(
        "A graphite heater brings the charge above the silicon melting point. Argon flows through the chamber to carry away SiO and CO and keep oxygen low. The melt is held steady so the seed can touch it at the right temperature.",
        "Chunks shrinking as the melt level rises, the ≈ surface settling flat, and the heater glow around the crucible.",
    )
    .detail(
        "A stable, flat melt is needed before seeding. Rushing the seed causes temperature drift and a diameter that wanders.",
        &[
            "COMSOL model: melt near 1414 C, contact 1403-1407.5 C, argon 100 L/min at 2500 Pa",
            "Wikipedia quotes 1425 C for semiconductor-grade silicon, so the exact figure depends on the source",
            "The model needs about 400 minutes to reach a steady contact temperature",
            "Heating to 1414 C in argon needs a graphite heater (about 310 kW in the model); small power changes move the interface",
        ],
    ),
    Beat::new(
        "the seed touches the melt; a thin dash neck is pulled fast to purge dislocations",
        BEAT_MS,
    )
    .note(
        "A small oriented seed crystal is lowered until it touches the melt. The contact shock creates dislocations, so the operator pulls a thin neck, 2-4 mm across, at high speed. The dislocations slide out through the neck surface before the body starts.",
        "The seed descending, the neck thin and rising, and dislocation marks / leaving through its sides.",
    )
    .detail(
        "Everything hangs from this neck, so it is the most failure-prone step. A neck break drops the whole crystal into hot silicon.",
        &[
            "Neck pulled up to about 6 mm/min (US 6,866,713)",
            "About 100-125 mm of neck is needed to purge dislocations",
            "Dash-necked crystals are limited to about 100 kg (patent text)",
        ],
    ),
    Beat::new(
        "shoulder: the melt is cooled slightly and the crystal flares out to 300 mm",
        BEAT_MS,
    )
    .note(
        "The temperature is trimmed down and the pull slowed so the crystal widens along a cone to full diameter. A sudden jump from the thin neck would be a sharp corner that concentrates stress and can start new dislocations, so the cone is gradual. Growth releases latent heat at the interface, so the temperature loop, not just pull speed, now sets the diameter.",
        "The narrow neck opening into a cone that widens to full width.",
    )
    .detail(
        "Too steep a flare can start new dislocations or twin the crystal. Dislocations that survived the neck can multiply as it widens.",
        &[
            "Target diameter is 300 mm for modern wafers",
            "The shoulder is later cropped off as scrap",
            "A failure here wastes the whole charge",
        ],
    ),
    Beat::new(
        "body: grows at about 1.0-1.6 mm a minute while the crucible rises with the falling melt",
        BEAT_MS,
    )
    .note(
        "The saleable body grows as the seed rises. Crystal and crucible counter-rotate to stir the melt, so temperature and dopant stay even and the freezing front stays flat. The crucible is lifted as the melt level drops so the interface stays put. Heater power is trimmed to hold the diameter.",
        "The crystal lengthening upward, the crucible rising slightly, and the melt level staying put.",
    )
    .detail(
        "The freezing front must stay flat. A faster pull pushes it convex or concave, locks in stress and defects, and shifts oxygen. Yield is set here.",
        &[
            "1.0 mm/min of 300 mm crystal is about 9.9 kg/h; 1.6 mm/min is about 15.8 kg/h",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
            "Oxygen: slower crucible spin or a shallower melt cuts oxygen pulled off the quartz; faster argon and lower pressure carry SiO away. Both cost uniformity and output",
            "Oxygen is a tradeoff: zero is not the goal, and some oxygen helps trap defects during device making (general knowledge, not on the page)",
            "Up to about 2 m long and several hundred kg (Wikipedia)",
        ],
    ),
    Beat::new(
        "tail: tapers to an end cone, then the crystal is lifted clear of the melt to cool",
        BEAT_MS,
    )
    .note(
        "At the end the diameter is tapered and the crystal is lifted off the melt in steps while it cools. An abrupt lift-off is a thermal shock, the same stress that makes dislocations, and it can send slip dislocations back up into the body. The taper makes the release gradual.",
        "The top of the crystal narrowing into a cone, then the whole crystal rising clear of the surface.",
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
        build: || -> Box<dyn Scene> { Box::new(zoom::Neck) },
    },
    Zoom {
        key: 'b',
        label: "melt convection and the magnetic field",
        build: || -> Box<dyn Scene> { Box::new(zoom::Convection) },
    },
    Zoom {
        key: 'c',
        label: "the hot zone and the argon sweep",
        build: || -> Box<dyn Scene> { Box::new(zoom::HotZone) },
    },
];

pub struct Melt;

impl Scene for Melt {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }

    fn draw(&self, _c: &mut Canvas, _t: &Time) {}

    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
        Some(overview_frame(t, &poly3d::View::default(), w, h))
    }

    fn notes_in_picture(&self) -> bool {
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_picture_is_drawn_not_blank() {
        let view = poly3d::View::default();
        let t = Time {
            beat: 2,
            local: 0.5,
            ms: 1000,
            beat_start: 0,
        };
        let img = overview_frame(&t, &view, 480, 320);
        assert_eq!((img.width(), img.height()), (480, 320));
        let bg = px::BG;
        let drawn = img
            .pixels()
            .filter(|p| p.0[0] != bg[0] || p.0[1] != bg[1] || p.0[2] != bg[2])
            .count();
        assert!(
            drawn > 480 * 320 / 10,
            "only {drawn} pixels off the background"
        );
    }
}
