// MELT + PULL zooms a-c, drawn in 3D by pbr3d in the same shaded style as the overview:
// a the dash neck, b the melt convection with its magnetic field, c the hot zone with its argon
// sweep. Each zoom is four beats, each beat its own 3D close-up (tools/pbr3d/src/shot_zoom.rs).

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time};
use pbr3d::Shot;

const MIN_W: u16 = 100;
const MIN_H: u16 = 30;
const BEAT_MS: u64 = 5200;

const NECK_BEATS: &[Beat] = &[
    Beat::new(
        "the seed touches the melt; the contact shock throws dislocations into the crystal",
        BEAT_MS,
    )
    .note(
        "The oriented seed is lowered onto the melt. At contact the temperature gradient is severe, and the thermal shock creates dislocations that can run through the whole crystal.",
        "The seed coming down, a burst of * at the contact point, and dark / lines forming just below it.",
    )
    .detail(
        "Without a neck, those dislocations would propagate into the body and ruin it. The neck is how they are removed.",
        &[
            "Seed set to a {100} or {111} orientation (page text)",
            "Thermal shock on contact generates dislocations (page text)",
            "Dash neck pulled fast so dislocations exit the surface",
        ],
    ),
    Beat::new(
        "dash neck: 2-4 mm across, pulled up to about 6 mm a minute, dislocations slide out",
        BEAT_MS,
    )
    .note(
        "The operator pulls a thin neck quickly. Dislocations are inclined and glide outward, so they reach the neck surface and leave the crystal. Roughly 100-125 mm of neck is needed.",
        "The neck rising, dislocations / moving diagonally to the wall, and their exit shown as · outside the neck.",
    )
    .detail(
        "The neck only has to be thin and long enough to purge dislocations. A longer neck costs time, a shorter one lets defects through.",
        &[
            "Neck pulled up to about 6 mm/min (US 6,866,713)",
            "About 100-125 mm of neck purges dislocations (US 6,866,713)",
            "Another neck method pulls 1.0-3.0 mm/min, e.g. 2.4 mm/min over 200 mm (US 5,578,284)",
        ],
    ),
    Beat::new(
        "the neck carries the whole crystal: a dash neck is limited to about 100 kg",
        BEAT_MS,
    )
    .note(
        "Everything hangs from the neck. Its thin cross-section can fracture under the weight, dropping the body into the crucible. A 300 mm crystal of several hundred kilograms is far past what a dash neck can hold.",
        "The body hanging from the neck with a ╳ crack in it, and ↓ the weight pulling down on it.",
    )
    .detail(
        "A neck break is the most expensive single failure: the whole crystal drops into hot silicon.",
        &[
            "Dash-necked crystals are limited to about 100 kg (patent text, US 6,866,713)",
            "A 300 mm crystal is several hundred kg (Wikipedia)",
            "Dash-free necks at 0.5 mm/min or less are an alternative (US 7,179,330)",
        ],
    ),
    Beat::new(
        "a dislocation that stays in the neck runs into the body and forces a remelt",
        BEAT_MS,
    )
    .note(
        "If a dislocation survives the neck it propagates up into the body. The crystal is then pulled back into the melt and the whole pull starts again.",
        "The / line continuing up into the body, then the body dropping back into the ≈ melt.",
    )
    .detail(
        "This is why the neck is inspected before the shoulder is grown. Any dislocation found there is a reason to stop early.",
        &[
            "A retained dislocation propagates into the body and forces a remelt (page text)",
            "Neck breaks and remelts are the most expensive failures in the process",
            "A slower neck, 1.0-3.0 mm/min, is used in some methods (US 5,578,284)",
        ],
    ),
];

const CONV_BEATS: &[Beat] = &[
    Beat::new(
        "the melt convects: the hot crucible wall drives buoyancy flow, and rotation adds more",
        BEAT_MS,
    )
    .note(
        "Heat enters at the hot crucible wall and rises, while cooler melt sinks near the crystal. Crystal and crucible rotation add forced convection on top of that.",
        "Packets circling the melt in a loop: ° rising along the wall and drifting back to the center.",
    )
    .detail(
        "Convection makes the temperature and oxygen uneven across the growth front. That unevenness is what limits 300 mm growth.",
        &[
            "A 2023 modelling study found convection causes uneven temperature, growth rate and oxygen at the interface",
            "Buoyancy flow from the hot wall; rotation adds forced flow (page text)",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
        ],
    ),
    Beat::new(
        "a horizontal magnetic field brakes the flow, since molten silicon conducts electricity",
        BEAT_MS,
    )
    .note(
        "A horizontal magnetic field (HMCZ) is applied across the melt. Its force opposes the moving liquid, so the convection slows and settles. Manufacturers adopted these fields in the early 2000s as melt volumes grew.",
        "The ═ field lines across the melt, and the loop of ° slowing to a few packets.",
    )
    .detail(
        "Damping the flow is what lets the interface stay stable at 300 mm, so oxygen and dopant come out uniform.",
        &[
            "Horizontal (HMCZ) and cusp fields damp the melt (patent background)",
            "Cusp-field studies show the zero-Gauss plane changes convection and oxygen transport",
            "Molten silicon is a good conductor, so the field acts directly on it",
        ],
    ),
    Beat::new(
        "the solid-liquid interface flattens: a flat front gives uniform oxygen and dopant",
        BEAT_MS,
    )
    .note(
        "The crystal bottom bulges into the melt when the flow is strong. As the flow damps, the interface relaxes to a flat front across the diameter.",
        "The ▓ crystal base changing from a bulge to a flat line at the melt surface.",
    )
    .detail(
        "A calmer, flatter interface means uniform oxygen and dopant across the wafer, which means more in-spec wafers per crystal.",
        &[
            "The axial gradient in the COMSOL model drops from 500 to 100 C per metre (model)",
            "Flat interface gives uniform oxygen and dopant (page text)",
            "Pull rates faster than 1.0-1.6 mm/min push the interface convex or concave (page text)",
        ],
    ),
    Beat::new(
        "SiO from the quartz: the crucible wall dissolves and oxygen freezes into the crystal",
        BEAT_MS,
    )
    .note(
        "The melt dissolves the inner surface of the quartz crucible, forming SiO. Most of it evaporates, but some freezes in as interstitial oxygen. Crucible rotation, melt depth, pull speed and magnetic fields tune the level.",
        "The crucible wall thinning to ░, and * SiO bubbles rising from the wall toward the surface.",
    )
    .detail(
        "Oxygen is the main impurity that the field and rotation are used to control. Too much makes the wafer brittle; too little changes device behavior.",
        &[
            "SiO2 + Si gives 2SiO; most SiO evaporates (page text, textbook)",
            "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
            "Crucible rotation and melt depth tune the oxygen (page text)",
        ],
    ),
];

const HOT_BEATS: &[Beat] = &[
    Beat::new(
        "a graphite heater surrounds the crucible, wrapped in felt insulation",
        BEAT_MS,
    )
    .note(
        "The resistive graphite heater is around the crucible, and graphite felt insulates it from the water-cooled chamber. Hot-zone parts are consumables that are changed periodically.",
        "The heater ▒ glowing, the felt ░ outside it, and the melt sitting in the middle.",
    )
    .detail(
        "The hot zone is the main know-how of a wafer maker and is typically proprietary. Its parts wear and are replaced.",
        &[
            "The COMSOL model uses a 310 kW graphite heater",
            "Heater, felt, susceptor and heat shield are consumables (textbook, page text)",
            "Graphite reacts with SiO to make CO, so argon carries it out",
        ],
    ),
    Beat::new(
        "heat leaves through the crystal: the axial gradient runs from about 500 to 100 C per metre",
        BEAT_MS,
    )
    .note(
        "Heat from the melt flows up the crystal and out to the cooler chamber, so the crystal has a temperature gradient. Near the melt it is hot and close to 1414 C; higher up it is much cooler.",
        "The crystal shaded from ▓ near the melt, through ▒, to ░ at the top, with the temperature labels.",
    )
    .detail(
        "The gradient sets the stress and defect density in the crystal. A steep gradient at the interface drives defects, so the shape of the hot zone matters.",
        &[
            "The COMSOL model gradient falls from 500 to 100 C per metre (model)",
            "Model reaches steady contact temperature after about 400 minutes (model)",
            "Melt near 1414 C (COMSOL); 1425 C on Wikipedia for semiconductor grade",
        ],
    ),
    Beat::new(
        "a heat shield above the melt limits radiant heat reaching the crystal",
        BEAT_MS,
    )
    .note(
        "A heat shield is placed around the crystal above the melt. It controls how much heat the growing crystal sees from the melt, shaping the axial gradient and the cooling rate.",
        "The shield || around the crystal, and the crystal beneath it staying in its gradient band.",
    )
    .detail(
        "The shield sets how fast the crystal cools, which trades growth speed against defects and stress.",
        &[
            "A thick heat shield above the melt is used in some pullers (US 8,524,000 description)",
            "Insulation above the reflector controls axial heat flow (US 8,524,000)",
            "Pull rate changes the power needed; 1.6 mm/min used 4.97% less power (2023 study)",
        ],
    ),
    Beat::new(
        "argon enters at the top, sweeps past the crystal, and leaves the base with SiO and CO",
        BEAT_MS,
    )
    .note(
        "Argon is the carrier gas. It flows down past the crystal and out the bottom, taking SiO and CO away so they do not condense on cold parts and fall back into the melt.",
        "° argon sweeping down the chamber wall past the crystal, with * SiO and · CO riding out the bottom.",
    )
    .detail(
        "Low pressure speeds up SiO evaporation, which lowers the oxygen picked up by the melt.",
        &[
            "Argon at 100 L/min and 2500 Pa in the COMSOL model (model, not a vendor spec)",
            "Argon carries SiO and CO out the bottom (page text)",
            "Graphite and SiO form CO (page text)",
        ],
    ),
];

macro_rules! zoom_scene_impl {
    ($name:ident, $beats:ident, $shot:expr) => {
        pub struct $name;

        impl Scene for $name {
            fn size(&self) -> (u16, u16) {
                (MIN_W, MIN_H)
            }
            fn beats(&self) -> &[Beat] {
                $beats
            }
            fn draw(&self, _c: &mut Canvas, _t: &Time) {}
            fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
                Some(pbr3d::render_shot(
                    $shot,
                    t.beat,
                    t.local,
                    0.0,
                    0.0,
                    1.0,
                    w,
                    h,
                    px::BG,
                ))
            }
        }
    };
}

zoom_scene_impl!(Neck, NECK_BEATS, Shot::Neck);
zoom_scene_impl!(Convection, CONV_BEATS, Shot::Convection);
zoom_scene_impl!(HotZone, HOT_BEATS, Shot::HotZone);

/// The 3D close-up for zoom or section key `key` ('a'-'c' zooms, '1'-'9' sections).
pub fn shot_for(key: char) -> Option<Shot> {
    match key {
        'a' => Some(Shot::Neck),
        'b' => Some(Shot::Convection),
        'c' => Some(Shot::HotZone),
        '1'..='9' => Some(Shot::Sec(key as u8 - b'0')),
        _ => None,
    }
}
