// MELT + PULL zoom-ins a-c in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/melt_zooms.py: a the dash neck, b melt convection and the magnetic field,
// c the hot zone and the argon sweep. Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

pub const NECK_BEATS: &[Beat] = &[
    Beat::new("the seed touches the melt; the contact shock throws dislocations into the crystal", BEAT_MS)
        .note(
            "The oriented seed is lowered onto the melt. At contact the temperature step is severe, and the thermal shock creates dislocations that could run through the whole crystal.",
            "the seed coming down to the orange surface, a spray of sparks at contact, and red lines appearing in the bottom of the seed",
        )
        .detail(
            "Without a neck, those dislocations would propagate into the body and ruin it. The neck is how they are removed.",
            &[
                "Seed set to a {100} or {111} orientation (page text)",
                "Thermal shock on contact generates dislocations (page text)",
                "Dash neck pulled fast so dislocations exit the surface (US 6,866,713)",
            ],
        ),
    Beat::new("dash neck: 2-4 mm across, pulled up to about 6 mm a minute, dislocations slide out", BEAT_MS)
        .note(
            "A thin neck is pulled quickly. Dislocations are inclined and glide outward, so they reach the neck surface and leave the crystal. Roughly 100-125 mm of neck is needed. The neck is drawn thicker than life so the lines inside it show.",
            "the neck growing down from the seed as it rises, red lines inside it sliding sideways out through its surface",
        )
        .detail(
            "The neck only has to be thin and long enough to purge dislocations. A longer neck costs time, a shorter one lets defects through.",
            &[
                "Neck pulled up to about 6 mm/min (US 6,866,713)",
                "About 100-125 mm of neck purges dislocations (US 6,866,713)",
                "Another neck method pulls 1.0-3.0 mm/min, e.g. 2.4 mm/min over 200 mm (US 5,578,284)",
            ],
        ),
    Beat::new("the neck carries the whole crystal: a dash neck is limited to about 100 kg", BEAT_MS)
        .note(
            "Everything hangs from the neck. Its thin cross-section can fracture under the weight, dropping the body into the crucible. A 300 mm crystal of several hundred kilograms is far past what a dash neck can hold.",
            "the shoulder and body growing under the neck, a red arrow for the weight, and a red ring flashing on the neck",
        )
        .detail(
            "A neck break is the most expensive single failure: the whole crystal drops into hot silicon.",
            &[
                "Dash-necked crystals are limited to about 100 kg (US 6,866,713)",
                "A 300 mm crystal is several hundred kg (Wikipedia)",
                "Dash-free necks at 0.5 mm/min or less are an alternative (US 7,179,330)",
            ],
        ),
    Beat::new("a dislocation that gets past the neck runs into the body and forces a remelt", BEAT_MS)
        .note(
            "If a dislocation survives the neck it propagates into the body. The crystal is then lowered back into the melt and the pull starts again.",
            "a red line running down the body, then the body sinking back into the melt until only the shoulder is left",
        )
        .detail(
            "This is why the neck is checked before the shoulder is grown. Any dislocation found there is a reason to stop early.",
            &[
                "A retained dislocation propagates into the body and forces a remelt (page text)",
                "Neck breaks and remelts are the most expensive failures in the process (page text)",
                "A slower neck, 1.0-3.0 mm/min, is used in some methods (US 5,578,284)",
            ],
        ),
];

pub const CONV_BEATS: &[Beat] = &[
    Beat::new("the melt convects: the hot crucible wall drives buoyancy flow, and rotation adds more", BEAT_MS)
        .note(
            "Heat enters at the hot crucible wall, so melt rises there, runs in along the surface and sinks under the cooler crystal. Crystal and crucible rotation add forced convection on top of that.",
            "bright packets racing round two loops on the cut face: up the walls, in under the surface, down beneath the crystal",
        )
        .detail(
            "Convection makes the temperature and oxygen uneven across the growth front. That unevenness is what limits 300 mm growth.",
            &[
                "A 2023 modelling study found convection makes temperature, growth rate and oxygen uneven at the interface",
                "Buoyancy flow from the hot wall; rotation adds forced flow (page text)",
                "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
            ],
        ),
    Beat::new("a horizontal magnetic field brakes the flow, since molten silicon conducts electricity", BEAT_MS)
        .note(
            "Coils outside the chamber put a horizontal field across the melt (HMCZ). Its force opposes the moving liquid, so the convection slows and settles. Makers adopted these fields as melt volumes grew.",
            "the copper coils either side of the furnace, blue field lines across the melt, and only a few packets left, moving slowly",
        )
        .detail(
            "Damping the flow is what lets the interface stay stable at 300 mm, so oxygen and dopant come out uniform.",
            &[
                "Horizontal (HMCZ) and cusp fields damp the melt (patent background)",
                "Cusp-field studies show the zero-Gauss plane changes convection and oxygen transport",
                "Molten silicon is a good conductor, so the field acts directly on it",
            ],
        ),
    Beat::new("the solid-liquid interface flattens: a flat front gives uniform oxygen and dopant", BEAT_MS)
        .note(
            "The crystal's bottom bulges into the melt when the flow is strong. As the flow damps, the interface relaxes to a flat front across the diameter.",
            "the grey dome under the crystal shrinking until the crystal's base is flat on the melt",
        )
        .detail(
            "A calmer, flatter interface means uniform oxygen and dopant across the wafer, which means more in-spec wafers per crystal.",
            &[
                "The axial gradient in the COMSOL model drops from 500 to 100 C per metre (model)",
                "Flat interface gives uniform oxygen and dopant (page text)",
                "Pull rates faster than 1.0-1.6 mm/min push the interface convex or concave (page text)",
            ],
        ),
    Beat::new("SiO from the quartz: the crucible wall dissolves and oxygen freezes into the crystal", BEAT_MS)
        .note(
            "The melt dissolves the inner surface of the quartz crucible, forming SiO. Most of it evaporates from the surface, but some freezes into the crystal as interstitial oxygen. Crucible rotation, melt depth, pull speed and magnetic fields tune the level.",
            "pale bubbles leaving the crucible wall and rising out of the melt, then red specks appearing on the crystal near the melt",
        )
        .detail(
            "Oxygen is the main impurity the field and rotation are used to control. Too much makes the wafer brittle; too little changes device behaviour.",
            &[
                "SiO2 + Si gives 2SiO; most SiO evaporates (page text, textbook)",
                "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
                "Crucible rotation and melt depth tune the oxygen (page text)",
            ],
        ),
];

pub const HOT_BEATS: &[Beat] = &[
    Beat::new("a graphite heater surrounds the crucible, wrapped in felt insulation", BEAT_MS)
        .note(
            "The resistive graphite heater rings the crucible, and graphite felt insulates it from the water-cooled chamber. The quartz crucible sits in a graphite susceptor. Hot-zone parts are consumables that are changed periodically.",
            "the orange heater ring, the brown felt outside it, and the graphite susceptor holding the quartz crucible",
        )
        .detail(
            "The hot zone is the main know-how of a wafer maker and is typically proprietary. Its parts wear and are replaced.",
            &[
                "The COMSOL model uses a 310 kW graphite heater",
                "Heater, felt, susceptor and heat shield are consumables (page text)",
                "Graphite reacts with SiO to make CO, so argon carries it out (page text)",
            ],
        ),
    Beat::new("heat leaves through the crystal: the axial gradient runs from about 500 to 100 C per metre", BEAT_MS)
        .note(
            "Heat from the melt flows up the crystal and out to the cooler chamber, so the crystal carries a temperature gradient. Near the melt it is close to 1414 C; higher up it is much cooler.",
            "colour bands up the crystal, glowing orange at the melt and fading to grey-violet higher up",
        )
        .detail(
            "The gradient sets the stress and defect density in the crystal. A steep gradient at the interface drives defects, so the shape of the hot zone matters.",
            &[
                "The COMSOL model gradient falls from 500 to 100 C per metre (model)",
                "Model reaches steady contact temperature after about 400 minutes (model)",
                "Melt near 1414 C (COMSOL); 1425 C on Wikipedia for semiconductor grade",
            ],
        ),
    Beat::new("a heat shield above the melt limits the radiant heat reaching the crystal", BEAT_MS)
        .note(
            "A heat shield hangs around the crystal just above the melt. It controls how much heat the growing crystal sees from the melt, shaping the axial gradient and the cooling rate.",
            "yellow packets of radiant heat leaving the melt and stopping on the underside of the grey shield",
        )
        .detail(
            "The shield sets how fast the crystal cools, which trades growth speed against defects and stress.",
            &[
                "A thick heat shield above the melt is used in some pullers (US 8,524,000)",
                "Insulation above the reflector controls axial heat flow (US 8,524,000)",
                "A 1.6 mm/min pull used 4.97% less power in one simulation (2023 study)",
            ],
        ),
    Beat::new("argon enters at the top, sweeps past the crystal, and leaves the base with SiO and CO", BEAT_MS)
        .note(
            "Argon is the carrier gas. It flows down past the crystal and out of the bottom, taking SiO and CO away so they do not condense on cold parts and fall back into the melt.",
            "pale blue argon running down the pull chamber, past the shield and out of the exhaust pipes, with white SiO and grey CO going with it",
        )
        .detail(
            "Low pressure speeds up SiO evaporation, which lowers the oxygen picked up by the melt.",
            &[
                "Argon at 100 L/min and 2500 Pa in the COMSOL model (model, not a vendor spec)",
                "Argon carries SiO and CO out of the bottom (page text)",
                "Graphite and SiO form CO (page text)",
            ],
        ),
];

static NECK: Cell = std::sync::OnceLock::new();
static CONV: Cell = std::sync::OnceLock::new();
static HOT: Cell = std::sync::OnceLock::new();

pub fn neck() -> Box<dyn Scene> {
    page(
        &NECK,
        include_bytes!("../../../../../tools/pbr3d/assets/melt_neck.glb"),
        NECK_BEATS,
    )
}

pub fn conv() -> Box<dyn Scene> {
    page(
        &CONV,
        include_bytes!("../../../../../tools/pbr3d/assets/melt_conv.glb"),
        CONV_BEATS,
    )
}

pub fn hot() -> Box<dyn Scene> {
    page(
        &HOT,
        include_bytes!("../../../../../tools/pbr3d/assets/melt_hot.glb"),
        HOT_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("neck", neck as fn() -> Box<dyn Scene>),
            ("conv", conv),
            ("hot", hot),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
