// GRID: the page's overview, a Blender scene (tools/pbr3d/blender/power_grid_overview.py, GLB
// tools/pbr3d/assets/power_grid_overview.glb). One diorama from the power plant's generator, through the
// step-up transformer and four lattice towers, to the campus substation, the utility meter and the data
// hall; glowing beads ride the conductors, cables and busways.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match power_grid_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a campus on the grid", BEAT_MS)
        .note(
            "Everything a data center runs on arrives over one connection to the grid. A power plant makes the electricity, high-voltage lines carry it across the country on steel towers, and a substation at the campus edge steps it down. How much power the utility can deliver there sets how big the campus can be.",
            "The whole run, left to right: the plant's turbine hall with its stack, the step-up transformer, four grey lattice towers with silver conductors, the substation's gantry and transformer, then the white data hall. Yellow beads ride the conductors from the plant toward the campus.",
        )
        .detail(
            "Its size is set by its grid connection.",
            &["Campus: hundreds of MW to over 1 GW", "Lines: 115-345 kV on steel towers"],
        ),
    Beat::new("transmission: 115 to 345 kV", BEAT_MS)
        .note(
            "Transmission lines carry the power long distances at 115 to 345 kV and up. Each double-circuit tower holds two circuits, one on each side, and each circuit is three conductors: the grid's standard three-phase power.",
            "Grey lattice towers march away from the step-up transformer. Three silver conductors hang from each side on teal insulator strings, and yellow beads ride all six of them tower to tower.",
        )
        .detail(
            "High voltage, low current, low loss.",
            &["115-345 kV and up", "Three phases per circuit"],
        ),
    Beat::new("high voltage keeps loss small", BEAT_MS)
        .note(
            "Wire loss grows with the square of the current. For the same power, ten times the voltage means a tenth of the current and a hundredth of the loss, which is why the lines run at hundreds of kilovolts and only step down near the load.",
            "Close on one tower: teal strings of glass discs hang from each cross-arm, the silver conductors sag between towers, and the thin earth wire runs over the peaks. A few yellow beads move slowly along the conductors.",
        )
        .detail(
            "Loss goes with current squared (I squared R).",
            &["10x the voltage = 1/100 the loss", "Power = voltage x current"],
        ),
    Beat::new("into the substation", BEAT_MS)
        .note(
            "At the campus edge the line ends on a substation's gantry. Drops lead down to a rigid bus on post insulators, and a transformer steps the voltage down for the site; past the utility's meter, cables run to the data hall.",
            "The steel gantry where the conductors land, white post insulators carrying the bus, the cut-open step-down transformer with its brown bushings and copper windings, and the grey meter cabinet. Beads drop down the leads into the transformer and out along the black cables.",
        )
        .detail(
            "The utility's equipment ends at the meter.",
            &["Step-down at the campus substation", "Utility meter: where the campus begins"],
        ),
    Beat::new("data centers: 4.4% of US power", BEAT_MS)
        .note(
            "US data centers used about 176 TWh in 2023, 4.4% of the country's electricity, up from 58 TWh in 2014. Berkeley Lab projects 325-580 TWh by 2028, 6.7% to 12% of the total, driven mostly by AI servers.",
            "The data hall cut open: rows of black racks with green status lights, a gold busway over each row with taps down to the racks, the grey switchboard by the wall, and cooling units on the roof. Beads come in by cable and run along the busways.",
        )
        .detail(
            "AI servers drive the growth (LBNL, Dec 2024).",
            &["176 TWh in 2023 (4.4%)", "325-580 TWh projected for 2028", "6.7-12% of US electricity"],
        ),
    Beat::new("waiting in the queue", BEAT_MS)
        .note(
            "Every new plant or large load is studied before it may connect. Berkeley Lab counted about 1,400 GW of generation and 890 GW of storage waiting in US queues at the end of 2024, and projects built in 2024 took 55 months from request to operation.",
            "Projects line the road to the substation's gate: solar arrays, white battery containers, gas plants, wind turbines. A cyan ring circles the one at the gate, under study, and the board beside it lights one gold tile per month.",
        )
        .detail(
            "The queue, not chips, often sets when a campus opens.",
            &["~1,400 GW generation + 890 GW storage queued", "55 months, request to operation (2024)", "LBNL Queued Up 2025"],
        ),
    Beat::new("PUE: how much reaches the chips", BEAT_MS)
        .note(
            "Power usage effectiveness is total site power divided by the power that reaches IT equipment. The rest goes to cooling and conversion losses; efficient hyperscale sites run near 1.1-1.2.",
            "Yellow beads run along the busways into the racks, while orange beads climb a riser to the cooling units on the roof. Orange blobs of heat rise off the fans.",
        )
        .detail(
            "At PUE 1.2, 100 MW of IT needs 120 MW.",
            &["PUE = site power / IT power", "Efficient sites ~1.1-1.2"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_and_zooms_are_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::super::blender::explained(s.as_ref(), "GRID overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in s.zooms() {
            assert_eq!((z.build)().beats().len(), 3, "zoom {}", z.key);
        }
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::super::blender::draws_every_beat(build().as_ref(), "GRID overview");
    }
}
