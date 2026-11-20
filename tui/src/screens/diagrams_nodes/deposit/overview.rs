// DEPOSIT: the page's overview, a Blender scene (tools/pbr3d/blender/deposit_overview.py, GLB
// tools/pbr3d/assets/deposit_overview.glb). One process chamber cut open: gas through the showerhead
// onto a heated wafer, a CVD film, ALD layers, a PVD metal target, a trench test and a flake from the wall.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/deposit_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match deposit_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("grow film", BEAT_MS)
        .note(
            "Deposition adds the thin films that make up a chip's layers. A gas or metal source feeds a vacuum chamber, and the film grows on a heated wafer. Three methods do it: CVD and ALD build the film from gas, and PVD sputters it off a solid metal target.",
            "The chamber cut open: gas comes down the feed from the gas cabinet, through the showerhead, onto a wafer on a heated pedestal. The pump at the bottom draws the leftover gas out. A thin film starts on the wafer.",
        )
        .detail(
            "Three ways to add a film.",
            &["CVD: gas reacts on the surface", "ALD: one atomic layer per cycle", "PVD: sputter atoms off a metal target", "Tools: Applied Materials (AMAT), Lam Research (LRCX)"],
        ),
    Beat::new("CVD: gas reacts on a hot wafer", BEAT_MS)
        .note(
            "In chemical vapor deposition, precursor gases flow over the wafer and react or break down at its hot surface, leaving a solid film. The by-products are pumped out. The film forms by a surface reaction rather than atoms flying in a straight line, so CVD covers steps well.",
            "Orange beads fall from the showerhead, flare where they reach the glowing wafer, and a tan film rises from the surface. By-product beads drop down the pump port.",
        )
        .detail(
            "The surface does the work.",
            &["Precursor gases react or break down on the hot surface", "The film forms at the surface, so steps get covered", "The pump removes the by-products"],
        ),
    Beat::new("ALD: one layer per cycle", BEAT_MS)
        .note(
            "Atomic layer deposition runs in cycles of four pulses. Pulse A puts a precursor on the surface, where it sticks to every open site until they are full. A purge clears the excess, pulse B reacts with that layer, and a second purge clears the by-products. Each cycle adds about one atomic layer.",
            "Close on the wafer: orange dots settle across the surface, a pale sweep of gas clears them, blue reactant beads react, and a teal layer appears. Three cycles stack three layers.",
        )
        .detail(
            "Self-limiting, so cycles set the thickness.",
            &["Al2O3 from TMA and water: about 1 angstrom per cycle", "Standard for thin high-k gate dielectrics", "Slow, so it goes where conformality matters most"],
        ),
    Beat::new("PVD: sputter a metal", BEAT_MS)
        .note(
            "Physical vapor deposition sputters metal. Argon is ionized into a plasma, and its ions hit the metal target hard enough to knock atoms loose. The atoms cross the vacuum and land on the wafer. Sputtering is the most widely used PVD method in semiconductor manufacturing, and it suits metal layers such as barriers and seeds.",
            "A metal target sits above the wafer under a violet argon plasma. Violet ion beads climb into the target, and silver atoms fly down in straight lines and gather into a metal layer on the wafer.",
        )
        .detail(
            "A knock-out, not a chemical reaction.",
            &["Argon is almost always the working gas", "Directional: flat tops coat well, deep trenches less so", "Metal layers: barriers and copper seeds"],
        ),
    Beat::new("conformality: the trench test", BEAT_MS)
        .note(
            "Whether a film can follow a trench decides which method is used. ALD coats the walls, floor and top evenly. PVD builds up across the top and lands thinly down the sides, so the opening can pinch shut.",
            "Close on a trench cut in silicon. First an even teal ALD film on the walls, floor and top; then the PVD version, with a thick overhang at the mouth and thin metal down the walls and floor.",
        )
        .detail(
            "Conformality picks the method.",
            &["ALD: best conformality and thickness control", "PVD: directional, so it thins on the sidewalls", "Films often must follow complex surface shapes"],
        ),
    Beat::new("chamber clean: flakes cost yield", BEAT_MS)
        .note(
            "By-products leave through the pump, but some film also coats the chamber walls. That coating can flake off and land on wafers as particles, which cut yield, so chambers are cleaned regularly. Deposition repeats for each film in the stack.",
            "The chamber from the gas side: beads run down the pump port. A deposit patch on the wall cracks, and a grey flake drops past the showerhead and lands on the wafer.",
        )
        .detail(
            "Wall buildup is a yield risk.",
            &["Buildup varies process results and lowers yield", "Heavy deposits can cause catastrophic tool failure", "So chambers need frequent cleaning"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_draws_every_beat() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "DEPOSIT overview");
        super::super::super::blender::draws_every_beat(s.as_ref(), "DEPOSIT overview");
    }
}
