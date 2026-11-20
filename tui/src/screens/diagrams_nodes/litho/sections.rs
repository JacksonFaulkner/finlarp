// LITHO sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/litho_sections.py. Beat counts: 4, 5, 5, 3, 3, 3, 3, 3, 4, 3. Section 10 is
// the sources page.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("light passes the openings in the reticle", BEAT_MS)
        .note(
            "Lithography copies a pattern onto the wafer with light. The reticle holds the pattern; light goes through its openings.",
            "the yellow source plate lights the reticle, and rays run through its gaps",
        )
        .detail(
            "Every layer of a DRAM array is printed this way, once per layer.",
            &["One reticle per layer (page text)", "The pattern is printed with light, then etched (page text)"],
        ),
    Beat::new("the lens shrinks the image onto the resist", BEAT_MS)
        .note(
            "The lens focuses the image on the light-sensitive resist at a quarter of the size, and the resist changes where the light lands.",
            "rays converge through the lens barrel, and the centre fields of the resist turn pink",
        )
        .detail(
            "The image is 4x smaller than the reticle.",
            &["Reduction: 4x (page text)", "Photoresist: the light-sensitive film on the wafer (page text)"],
        ),
    Beat::new("develop removes the exposed resist", BEAT_MS)
        .note(
            "Develop dissolves the exposed part and keeps the rest. The pattern now stands on the wafer, ready for etch.",
            "the pink fields turn cyan as the exposed resist washes away",
        )
        .detail(
            "Etch copies the pattern into the film below.",
            &["Positive resist: the exposed part develops away (page text)"],
        ),
    Beat::new("etch copies the pattern into the film", BEAT_MS)
        .note(
            "Etch cuts the pattern into the film below. The rest of the stack is renewed for the next layer.",
            "the wafer carries its fresh purple resist on top, after the pattern has gone into the film",
        )
        .detail(
            "One layer done; the wafer comes back for the next.",
            &["Each layer has its own reticle and its own alignment to the layer below (page text)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("wavelength: the source sets it", BEAT_MS)
        .note(
            "The source sets the wavelength: 193 nm for DUV ArF, 13.5 nm for EUV. A shorter wavelength prints finer lines.",
            "the yellow source plate lights above the wafer",
        )
        .detail(
            "Most of the cost of a new node is in the light source and optics for this one number.",
            &["DUV ArF: 193 nm", "EUV: 13.5 nm"],
        ),
    Beat::new("EUV source: a CO2 laser hits each tin droplet twice", BEAT_MS)
        .note(
            "Molten tin droplets are fired into the source. The first laser pulse flattens each droplet, and the second makes the plasma that emits 13.5 nm light.",
            "a grey tin droplet falls, then a yellow laser flash and a white plasma flare",
        )
        .detail(
            "Debris from the blast can coat the optics that make the light.",
            &["About 50,000 tin droplets a second (not yet sourced here)", "CO2 laser double pulse (not yet sourced here)"],
        ),
    Beat::new("multilayer mirrors: about 70% each", BEAT_MS)
        .note(
            "EUV is absorbed by air and glass, so the path is in vacuum with mirrors. Each mirror is a stack of molybdenum and silicon layers.",
            "four blue-grey mirrors stand in the beam path",
        )
        .detail(
            "The losses compound, so the source must be very bright and stable.",
            &["Each mirror keeps about 70% (not yet sourced here)"],
        ),
    Beat::new("reticle and lens: one reticle per layer, 4x", BEAT_MS)
        .note(
            "The reticle holds the pattern as chrome on clear quartz, one per layer. The lens sets the numerical aperture and prints the image 4x smaller.",
            "the chrome reticle sits above the lens barrel, with the image going down to the wafer",
        )
        .detail(
            "NA sets resolution and depth of focus together.",
            &["Reduction 4x (page text)", "One reticle per layer (page text)"],
        ),
    Beat::new("photoresist and stage: the sensor reads the marks", BEAT_MS)
        .note(
            "The photoresist is the light-sensitive film on the wafer. The stage carries the wafer, and the sensor reads the marks from the layer below so this layer lands on top.",
            "a green sensor beam runs from the sensor down to the wafer's mark; the purple resist sits on the wafer",
        )
        .detail(
            "Overlay is how well this layer lines up with the last.",
            &["NXE:3800E: 220 wafers per hour (ASML 20-F FY2025)", "Matched overlay 0.9 nm (ASML annual report 2024)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. the source flashes; light passes the reticle", BEAT_MS)
        .note(
            "Light from the source passes the openings in the reticle. Every exposure starts here.",
            "the source plate flashes yellow above the reticle",
        )
        .detail(
            "The steps are numbered along the bottom of the panel.",
            &["One exposure is five steps (page text)"],
        ),
    Beat::new("2. the lens projects the image, shrunk", BEAT_MS)
        .note(
            "The lens focuses the light from the openings onto the resist at a quarter of the size.",
            "rays pass down through the lens barrel and land on the wafer",
        )
        .detail(
            "A scanner shrinks 4x.",
            &["Reduction: 4x (page text)"],
        ),
    Beat::new("3. the exposed resist changes", BEAT_MS)
        .note(
            "Where light lands, the resist changes chemically. In the picture the exposed fields turn pink along the top of the wafer.",
            "pink fields on the wafer's top row, with the rest of the resist purple",
        )
        .detail(
            "The pattern is still hidden in the chemistry.",
            &["Exposure changes the chemistry, not the shape (page text)"],
        ),
    Beat::new("4. develop removes the exposed resist", BEAT_MS)
        .note(
            "Develop dissolves the exposed part (positive resist), so the pattern now stands in the resist.",
            "the pink fields have gone, and cyan shows where they were",
        )
        .detail(
            "The pattern now stands in the resist, ready for etch.",
            &["Positive resist: the exposed part develops away (page text)"],
        ),
    Beat::new("5. etch copies the pattern into the film", BEAT_MS)
        .note(
            "Etch cuts the gaps into the film below. One layer is done; the wafer comes back for the next.",
            "the cyan gaps show where the film has been cut",
        )
        .detail(
            "The rest of the chain works from this layer.",
            &["Etch copies the pattern into the film below (page text)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("DUV ArF immersion: 193 nm gives about 57 nm", BEAT_MS)
        .note(
            "Water between lens and wafer lets NA pass 1. At NA 1.35 and k1 0.4 the smallest line is about 57 nm.",
            "the DUV tile has the widest lines and the tallest bar",
        )
        .detail(
            "Below a k1 of about 0.25 one exposure is not enough (US 6,839,125).",
            &["CD = k1 x wavelength / NA: 193 x 0.4 / 1.35 = about 57 nm (page text)", "DUV immersion NA 1.35 (not yet sourced here)"],
        ),
    Beat::new("EUV: 13.5 nm at NA 0.33 gives about 16 nm", BEAT_MS)
        .note(
            "A 14x shorter wavelength at a smaller NA. At k1 0.4 the line is about 16 nm.",
            "the EUV tile has finer lines and a shorter bar",
        )
        .detail(
            "EUV needs vacuum and mirrors, since almost everything absorbs 13.5 nm light.",
            &["13.5 x 0.4 / 0.33 = about 16 nm (page text)", "k1 0.4 is illustrative (page text)"],
        ),
    Beat::new("High-NA EUV: 13.5 nm at NA 0.55 gives about 10 nm", BEAT_MS)
        .note(
            "Same wavelength, a wider cone. At k1 0.4 the line is about 10 nm.",
            "the High-NA tile has the finest lines and the shortest bar",
        )
        .detail(
            "ASML quotes 8 nm resolution, 1.7x smaller than NXE.",
            &["13.5 x 0.4 / 0.55 = about 10 nm (page text)", "EXE:5000: 8 nm (ASML product page)"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("NA 0.33: a long in-focus band", BEAT_MS)
        .note(
            "The image stays sharp over a band of heights around the focus: DOF = k2 x wavelength / NA^2.",
            "a purple band runs long through the focus on a flat wafer",
        )
        .detail(
            "Illustrative k2 0.5 gives about 62 nm at EUV NA 0.33.",
            &["DOF = k2 x wavelength / NA^2 (page text)", "k2 0.5 is illustrative (page text)"],
        ),
    Beat::new("NA 0.55: the band shrinks with NA squared", BEAT_MS)
        .note(
            "A wider cone prints finer lines, but the sharp band gets much shorter.",
            "the purple band closes in to about a third of its length",
        )
        .detail(
            "0.55 squared is 2.8 times 0.33 squared, so the band is 2.8 times shorter.",
            &["(0.55 / 0.33)^2 = 2.8 (page text)"],
        ),
    Beat::new("a wafer that is not flat drifts out of focus", BEAT_MS)
        .note(
            "Real wafers have height steps. Where the surface leaves the band, the image blurs.",
            "orange raised blocks on the wafer top sit outside the band",
        )
        .detail(
            "Higher NA asks for flatter wafers and thinner resist.",
            &["Higher NA needs flatter wafers and thinner resist (page text)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("one 1T1C cell is 6F^2", BEAT_MS)
        .note(
            "F is the feature size, set by the smallest line litho prints. A 1T1C cell with an open bit line covers 3F by 2F.",
            "one orange cell on a grid of grey squares",
        )
        .detail(
            "Counting in F compares layouts across processes.",
            &["1T1C cell: 6F^2 (page text, see the CELL node)"],
        ),
    Beat::new("shrink F by 0.7 and the cell area halves", BEAT_MS)
        .note(
            "Area goes with F squared: 0.7 x 0.7 = 0.49, so the grid tightens and the cell shrinks with it.",
            "the grid tightens and the orange cell shrinks with it",
        )
        .detail(
            "That is why every node is chasing a smaller F.",
            &["Shrinking F by 0.7 halves the cell area (page text)", "0.7 x 0.7 = 0.49 (arithmetic)"],
        ),
    Beat::new("the same patch holds about twice the cells", BEAT_MS)
        .note(
            "More cells per die means more bits per wafer, at roughly the same wafer cost.",
            "three more orange cells join the first in the same patch",
        )
        .detail(
            "Overlay and pitch limits set how far this goes.",
            &["Fits about twice the cells in the same space (page text)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("too tight for one exposure: the lines merge", BEAT_MS)
        .note(
            "When k1 falls below about 0.25, one exposure cannot separate the lines.",
            "the lines merge into one orange smear",
        )
        .detail(
            "k1 of about 0.25 is the single-exposure floor (US 6,839,125).",
            &["k1 floor about 0.25 (US 6,839,125)"],
        ),
    Beat::new("split it: mask A, then mask B in the gaps", BEAT_MS)
        .note(
            "Print every other line with one mask, then the rest with a second (LELE). Spacer methods like SADP do something similar with one litho step.",
            "pink lines from mask A alternate with cyan lines from mask B",
        )
        .detail(
            "Each pass prints a pitch the scanner can manage.",
            &["LELE: litho-etch, litho-etch (page text)", "SADP: self-aligned double patterning (page text)"],
        ),
    Beat::new("the cost: overlay error between the passes", BEAT_MS)
        .note(
            "Any overlay error between the passes leaves the spacing uneven, and every extra pass adds cost and time.",
            "the cyan lines slide toward their pink neighbours",
        )
        .detail(
            "Memory makers use several such layers.",
            &["Overlay error adds up per exposure (page text)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("ASML: EUV and DUV scanners", BEAT_MS)
        .note(
            "ASML is the only maker of EUV scanners, and also makes DUV scanners.",
            "ASML's scanner is lit with its gold tag; the other two stand dark",
        )
        .detail(
            "Every EUV layer in the world runs on an ASML tool.",
            &["ASML is the only EUV scanner maker (page text)"],
        ),
    Beat::new("Nikon (7731.T): DUV scanners", BEAT_MS)
        .note(
            "Nikon makes DUV scanners.",
            "Nikon's scanner is lit with its gold tag",
        )
        .detail(
            "Nikon and Canon make DUV scanners (page text).",
            &["Nikon ticker: 7731.T (page text)"],
        ),
    Beat::new("Canon (7751.T): DUV scanners", BEAT_MS)
        .note(
            "Canon makes DUV scanners.",
            "Canon's scanner is lit with its gold tag",
        )
        .detail(
            "Canon and Nikon make DUV scanners (page text).",
            &["Canon ticker: 7751.T (page text)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("one EUV maker, no second source", BEAT_MS)
        .note(
            "EUV scanners come from one company, and its sources and optics come from very few suppliers.",
            "a single grey tower stands between two empty plinths",
        )
        .detail(
            "Any delay at ASML or its suppliers delays every EUV fab.",
            &["ASML is the only EUV scanner maker (page text)"],
        ),
    Beat::new("mirrors and the tin source are single points of failure", BEAT_MS)
        .note(
            "Mirror optics (Zeiss, for ultra-flat optics) and the tin-droplet source are single points of failure.",
            "a row of blue-grey mirrors stands beside the tower",
        )
        .detail(
            "A dozen mirrors leave about 1% of the light.",
            &["A dozen mirrors leave about 1% (not yet sourced here)", "Each mirror keeps about 70% (not yet sourced here)"],
        ),
    Beat::new("stochastic defects: too few photons", BEAT_MS)
        .note(
            "At small features and low doses, few photons land on each spot, and random breaks and bridges appear.",
            "a few sparse photons fall, and orange defect marks sit on the lines",
        )
        .detail(
            "Raising the dose fixes it but slows the scanner.",
            &["Defects grow as doses fall (page text)"],
        ),
    Beat::new("export controls fence off advanced scanners", BEAT_MS)
        .note(
            "Export rules limit which advanced scanners can be sold abroad. Check the current rules.",
            "a fence of orange posts stands around the scanner area",
        )
        .detail(
            "A rule change can cut a maker off from a market overnight.",
            &["Export controls limit advanced scanners; check current rules (page text)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("ASML product and High-NA pages", BEAT_MS)
        .note(
            "Two cards: the EXE:5000 product page (NA 0.55, 8 nm) and ASML's High-NA explainer from 2024.",
            "two cards light gold along their top edge",
        )
        .detail(
            "The product page and the explainer are the source for the High-NA figures.",
            &["EXE:5000: NA 0.55, 8 nm, 1.7x smaller than NXE (ASML product page)", "5 things about High NA EUV (ASML, 2024)"],
        ),
    Beat::new("SEC filings: throughput and overlay", BEAT_MS)
        .note(
            "The ASML annual report 2024 and the 20-F for FY2025 give the wafers per hour and the matched overlay.",
            "two filing cards light gold",
        )
        .detail(
            "The throughput figures are targets, not measured yields.",
            &["NXE:3600D 160 wafers per hour; NXE:3800E target 220 (annual report 2024)", "NXE:3800E at full spec, 220 wafers per hour (20-F FY2025)"],
        ),
    Beat::new("patent and open notes", BEAT_MS)
        .note(
            "US 6,839,125 gives the resolution and depth-of-focus formulas. Some figures on this page are not yet sourced.",
            "the patent card lights gold, with a note card below it",
        )
        .detail(
            "The formulas are from the patent; the numbers built on them are worked examples.",
            &["R = k1 x wavelength / NA; DOF = k2 x wavelength / NA^2 (US 6,839,125)", "EUV source and mirror figures are not yet sourced here (page text)"],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/litho_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [4, 5, 5, 3, 3, 3, 3, 3, 4, 3]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
