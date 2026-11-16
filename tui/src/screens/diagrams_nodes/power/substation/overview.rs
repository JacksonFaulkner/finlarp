// SUBSTATION: the page's overview, a Blender scene (tools/pbr3d/blender/power_substation_overview.py, GLB
// tools/pbr3d/assets/power_substation_overview.glb). The yard with its incoming line and breaker, the power transformer
// whole, then cut open to its core and windings, with the flux, the amps and the heat; the lead-time rows close it.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_substation_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the substation yard", BEAT_MS)
        .note(
            "Transmission lines land on a steel gantry in the substation yard, and connect to the tall bushings on a power transformer. A 230 kV line comes in and about 34.5 kV goes out to the campus.",
            "The yard: a lattice tower at the left, a dead-end gantry with the 230 kV line landing on it, a circuit breaker, and the transformer with its bushings on the concrete pad.",
        )
        .detail(
            "The yard is where the grid's voltage steps down for the site.",
            &["Transmission: 115-345 kV in", "230 kV in, about 34.5 kV out (example)"],
        ),
    Beat::new("one power transformer", BEAT_MS)
        .note(
            "A power transformer steps the transmission voltage down to medium voltage for the site. It is a steel core and copper windings in an oil-filled tank, with bushings on the lid and radiators on the sides.",
            "A single transformer close-up: a grey tank with bushings on the lid, radiator panels on the sides, and a conservator on top.",
        )
        .detail(
            "The longest-lead item on the grid side.",
            &["Tens to hundreds of MVA", "About 128 weeks lead time (2025)"],
        ),
    Beat::new("cut open: core and windings", BEAT_MS)
        .note(
            "The tank front lifts away to show the core and windings. The core is three steel limbs of laminated electrical steel, and the copper coils are wound round each limb.",
            "The cut-open tank: a dark steel core with its coils inside, the low-voltage winding inner and the high-voltage winding outer, and a pale steel limb through each coil.",
        )
        .detail(
            "The core carries the field; the windings carry the current.",
            &["Core: stacked electrical-steel sheets", "Windings: copper coils"],
        ),
    Beat::new("the field links the coils", BEAT_MS)
        .note(
            "Alternating current in the high-voltage winding makes a changing magnetic field in the core. That field induces a voltage in the other winding, with the same volts per turn in each coil.",
            "Cyan flux beads loop round the core, reversing as the current alternates, with the coils either side of each limb.",
        )
        .detail(
            "The turns ratio sets the voltage ratio.",
            &["Same volts per turn in both coils", "230 kV to 34.5 kV: about 6.7x the turns (example)"],
        ),
    Beat::new("few amps in, many amps out", BEAT_MS)
        .note(
            "High voltage enters at low current through the tall bushings, and low voltage leaves at high current. Power stays about the same, and the transformer passes over 99% of it.",
            "A few large yellow beads enter at the tall high-voltage bushings; many smaller orange ones leave from the low-voltage side.",
        )
        .detail(
            "Voltage times current stays about constant.",
            &["Over 99% of power passes through", "Power in is about power out"],
        ),
    Beat::new("oil and radiators carry the heat", BEAT_MS)
        .note(
            "The core and windings give off heat as they work. Mineral oil fills the tank to carry it to the radiator panels on the sides, sometimes with fans and pumps.",
            "The tank glowing from within at the core and windings, the fins of the radiators on its sides, and fans below them.",
        )
        .detail(
            "Overheating ages the winding insulation.",
            &["Core loss: always on", "Copper loss: rises with load"],
        ),
    Beat::new("the longest wait on the grid", BEAT_MS)
        .note(
            "Large power transformers averaged about 128 weeks from order to delivery in Q2 2025, and generator step-up units about 144. Each is custom-built to its site's voltages.",
            "Rows of pale lead-time bars laid out in front of the transformer: about 50 weeks in 2021, about 120 in 2024, about 128 in 2025.",
        )
        .detail(
            "Custom design, few makers, long queues.",
            &["About 50 weeks (2021), 120 (2024)", "About 128 weeks large units (Q2 2025); about 144 GSU"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_and_zooms_are_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::super::blender::explained(s.as_ref(), "SUBSTATION overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in s.zooms() {
            assert_eq!((z.build)().beats().len(), 3, "zoom {}", z.key);
        }
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::super::blender::draws_every_beat(
            build().as_ref(),
            "SUBSTATION overview",
        );
    }
}
