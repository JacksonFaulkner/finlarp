// IMPLANT: the page's overview, a Blender scene (tools/pbr3d/blender/implant_overview.py, GLB
// tools/pbr3d/assets/implant_overview.glb). One ion-implanter beamline cut open along the beam:
// gas cabinet, arc source, extraction, analyzer magnet, mass slit, accelerator column, scanner
// and the wafer in the end station beside a Faraday cup; dopant beads ride the beam.

use crate::screens::diagrams_nodes::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/implant_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match implant_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the source makes the ions", BEAT_MS)
        .note(
            "A gas cabinet feeds an arc chamber that strips electrons off dopant molecules, leaving charged ions. Electrodes pull the ions out as a beam. Boron, phosphorus and arsenic are the dopants, each from its own gas: BF3 or decaborane for boron, PH3 for phosphorus, AsH3 for arsenic.",
            "Left to right: the gas cabinet, a feed line into the source, a glowing plasma chamber, and the extraction plates. A blue beam runs along the axis and orange dopant beads leave the source toward the magnet.",
        )
        .detail(
            "Gas in, ions out, no film left behind.",
            &["Dopants: boron, phosphorus, arsenic", "Boron: BF3, BF2 or decaborane; P: PH3; As: AsH3"],
        ),
    Beat::new("the magnet picks one species", BEAT_MS)
        .note(
            "The analyzer magnet bends each ion by its mass and charge, so only one species at the chosen charge state threads the mass slit. The other masses curve into the slit and stop. Applied Materials' VIISta 900XP puts a filter magnet at the source and a dual-magnet design to keep beam-borne contamination off the wafer.",
            "The dark magnet block across the beam lights up. Grey beads curve off the axis and stop at the slit plates, while the orange beads pass through the gap and carry on.",
        )
        .detail(
            "Bend radius set by mass and charge.",
            &["Right species passes the slit; the rest stop", "VIISta 900XP: filter magnet + dual magnet"],
        ),
    Beat::new("energy sets the depth", BEAT_MS)
        .note(
            "The accelerator column gives each ion its energy, from about 10 to 500 keV in a typical implanter. Energy sets how deep the ion travels, roughly 10 nm to 1 micrometer, and lighter ions go farther than heavy ones at the same energy. The VIISta 900XP reaches 300 keV with singly charged ions and 600 keV with doubly charged ions.",
            "The column is a clear tube with a ring for each stage along the beam. The beam runs through it and the beads speed up as they pass the rings toward the scanner.",
        )
        .detail(
            "Higher energy means deeper ions.",
            &["Typical energy ~10-500 keV", "Range ~10 nm to 1 um", "VIISta 900XP: 300 keV (+), 600 keV (++)"],
        ),
    Beat::new("scan, count and tilt", BEAT_MS)
        .note(
            "Scanner plates sweep the beam, or the wafer moves, so the dose lands evenly across the wafer. A Faraday cup counts the beam current, and dose is that charge spread over the area. The wafer is tilted a few degrees off the beam and spun, so ions do not run straight down a crystal lane.",
            "The scanner plates stand across the beam ahead of the end station. The wafer tilts a few degrees on its holder, and the Faraday cup beside it counts the beads that reach it.",
        )
        .detail(
            "Dose: ions per square centimeter.",
            &["Dose = beam current x time, per area", "Very high dose: above 1e16 ions/cm2", "Tilt and spin limit channeling"],
        ),
    Beat::new("the ions break the crystal", BEAT_MS)
        .note(
            "Each ion knocks silicon atoms off their lattice sites. At a high enough dose the top layer turns amorphous, and the dopants sit between atoms where they are not electrically active. An anneal heats the wafer to regrow the crystal and move dopant onto lattice sites, but the heat also lets dopant diffuse, so every anneal trades activation against spreading.",
            "The wafer's face turns dark red as a damaged skin forms. Then a hot ring lights around the wafer, and the skin clears as the anneal repairs the crystal.",
        )
        .detail(
            "Implant damages; anneal repairs and activates.",
            &["High dose can make the surface amorphous", "Anneal: regrow crystal, activate dopant", "Anneal trades activation against diffusion"],
        ),
    Beat::new("who makes the implanter", BEAT_MS)
        .note(
            "Applied Materials, through its Varian line, and Axcelis are the main makers of implanters. Applied's VIISta 900XP is a medium-current tool for precision doping, rated at 500 wafers an hour. The dopant gases, arsine and phosphine, are toxic, so the gas cabinet and exhaust are tightly controlled.",
            "The wide view of the whole beamline, with the beam switched off. The labels name the two makers and the gas cabinet at the start of the line.",
        )
        .detail(
            "Applied (Varian) and Axcelis lead.",
            &["VIISta 900XP: 500 wafers per hour (mechanical)", "Arsine and phosphine are toxic gases"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        crate::screens::diagrams_nodes::blender::explained(s.as_ref(), "IMPLANT overview");
        assert!(s.zooms().is_empty());
    }

    #[test]
    fn overview_draws_every_beat() {
        crate::screens::diagrams_nodes::blender::draws_every_beat(
            build().as_ref(),
            "IMPLANT overview",
        );
    }
}
