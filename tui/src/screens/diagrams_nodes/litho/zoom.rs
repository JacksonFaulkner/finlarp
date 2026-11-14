// LITHO zoom-ins a-f in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/litho_zooms.py: a the reticle, b the lens and NA, c inside the resist,
// d step and scan, e overlay, f EUV light. Four beats each.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

pub const RETICLE_BEATS: &[Beat] = &[
    Beat::new("the pattern is chrome on clear quartz", BEAT_MS)
        .note(
            "A reticle is a quartz plate with the layer's pattern in chrome. Clear openings pass light; chrome blocks it.",
            "a pale quartz plate with raised chrome bars and clear gaps between them, above three grey dies",
        )
        .detail(
            "Each layer of the array has its own reticle.",
            &["One reticle per layer (page text)"],
        ),
    Beat::new("light gets through the openings only", BEAT_MS)
        .note(
            "Light falls on the whole plate. In the openings it carries on down to the dies; on the chrome it stops.",
            "yellow light runs down through the gaps and lands on the three dies below; the chrome throws none",
        )
        .detail(
            "The dies below are all printed from the same openings.",
            &["Same mask, every die"],
        ),
    Beat::new("a speck on the mask prints on every die", BEAT_MS)
        .note(
            "Dirt in one opening blocks light there, so the same flaw appears on every die printed from the mask, until it is cleaned off.",
            "a red speck sits in one opening of the mask, and a red flaw appears at the same place on all three dies",
        )
        .detail(
            "A mask flaw is copied many times over, which is why masks are inspected and kept clean.",
            &["Every error on the mask is copied onto every die that uses it (page text)"],
        ),
    Beat::new("one flaw, every die: mask quality sets the yield", BEAT_MS)
        .note(
            "Every error on the reticle is copied onto every die that uses it, so mask quality sets the yield of a whole layer.",
            "the speck and its three copies stay lit, and the rest of the mask is unchanged",
        )
        .detail(
            "A reticle is where the pattern is defined, so its errors set the yield of a layer.",
            &["Mask quality sets the yield of a whole layer (page text)"],
        ),
];

pub const LENS_BEATS: &[Beat] = &[
    Beat::new("NA 0.33: a narrow cone prints wide lines", BEAT_MS)
        .note(
            "Numerical aperture (NA) is the sine of the cone's half-angle. A narrow cone collects less of the light that carries fine detail, so lines come out wide.",
            "a narrow cone of yellow rays converges from the lens top to one point on the wafer",
        )
        .detail(
            "CD = k1 x wavelength / NA: at EUV 13.5 nm, NA 0.33 and k1 0.4, about 16 nm.",
            &["EUV NXE: NA 0.33 (page text)", "CD about 16 nm at k1 0.4 (page text)"],
        ),
    Beat::new("NA 0.55: a wider cone prints finer lines", BEAT_MS)
        .note(
            "A bigger lens at the same distance collects a wider cone. With NA 0.55 the same light prints lines about 10 nm wide.",
            "the cone opens wider, and its rays still meet the wafer at one point",
        )
        .detail(
            "High-NA EUV prints features 1.7x smaller than NXE (ASML).",
            &["High-NA EXE:5000: NA 0.55, 8 nm resolution (ASML product page)", "CD about 10 nm at k1 0.4 (page text)"],
        ),
    Beat::new("the price: less depth stays in focus", BEAT_MS)
        .note(
            "The zone around the focus that stays sharp shrinks with NA squared. At NA 0.33 it is long.",
            "a purple band marks the in-focus height through the focus, and at NA 0.33 it is long",
        )
        .detail(
            "Higher NA needs flatter wafers and thinner resist.",
            &["DOF = k2 x wavelength / NA^2 (page text, k2 illustrative)"],
        ),
    Beat::new("NA 0.55: the in-focus band is 2.8x shorter", BEAT_MS)
        .note(
            "Going from NA 0.33 to 0.55 makes the in-focus band (0.55 / 0.33)^2 = 2.8 times shorter, so the wafer must be flatter.",
            "the purple band shrinks to about a third of its length around the focus",
        )
        .detail(
            "Depth of focus falls with NA squared, which is why the wafer must be flatter at high NA.",
            &["(0.55 / 0.33)^2 = 2.8 (page text)", "Higher NA needs flatter wafers and thinner resist (page text)"],
        ),
];

pub const RESIST_BEATS: &[Beat] = &[
    Beat::new("expose: light changes the resist where it lands", BEAT_MS)
        .note(
            "Light through the openings changes the resist where it lands. In the chemistry, acid forms there (textbook).",
            "three pink columns of resist, with blue acid specks inside them; the rest of the resist stays purple",
        )
        .detail(
            "The shape has not changed yet: the pattern is hidden in the chemistry.",
            &["Positive resist: the exposed part develops away (page text)", "Acid forming in the resist is textbook, not sourced here"],
        ),
    Beat::new("develop: the exposed resist sinks away", BEAT_MS)
        .note(
            "Develop dissolves the exposed part, leaving the pattern standing on the wafer. The unexposed resist stays and protects the film below during etch.",
            "the pink columns sink down into the film and drop out of sight, with the purple resist either side",
        )
        .detail(
            "Over- or under-develop changes the line width, so develop is part of the critical dimension.",
            &["Develop fixes the shape of the pattern (page text)", "Over- or under-develop changes the line width (page text)"],
        ),
    Beat::new("etch: the film is cut where the resist is gone", BEAT_MS)
        .note(
            "Etch cuts the gaps into the film below, where the resist is no longer there. The resist that remains protects the rest.",
            "the film under each gap is removed, and blue ions drop down the trenches while the purple resist stays",
        )
        .detail(
            "The resist only has to last through etch; the film keeps the pattern.",
            &["Etch copies the pattern into the film below (page text)"],
        ),
    Beat::new("fresh resist for the next layer", BEAT_MS)
        .note(
            "The film and resist are renewed where they were cut, and the wafer goes back for the next layer.",
            "the trenches are refilled, leaving one flat stack of grey film and purple resist",
        )
        .detail(
            "Each layer has its own reticle and its own alignment to the layer below.",
            &["Each layer has its own reticle (page text)"],
        ),
];

pub const SCAN_BEATS: &[Beat] = &[
    Beat::new("scan: the slit sweeps one field", BEAT_MS)
        .note(
            "The slit lights a thin strip. The wafer moves under it and the reticle moves the opposite way, 4x as far, printing one field.",
            "the wafer slides under the yellow slit and the first field turns pink; the reticle moves the other way, out of frame",
        )
        .detail(
            "Only a slit of the lens is used, which keeps the optics' errors small.",
            &["Reticle travel is 4x the wafer travel (the reduction)"],
        ),
    Beat::new("step: field after field", BEAT_MS)
        .note(
            "The stage steps to the next field and scans again, until every field on the wafer is exposed.",
            "the wafer hops along the row and the fields fill in pink one after another",
        )
        .detail(
            "Throughput sets the cost per layer.",
            &["NXE:3800E: 220 wafers per hour (ASML 20-F FY2025)"],
        ),
    Beat::new("High-NA: fields half as tall", BEAT_MS)
        .note(
            "High-NA's anamorphic optics print each field half the size, so an orange line splits every field in half.",
            "an orange line splits each exposed field across its middle",
        )
        .detail(
            "Half fields cost throughput, part of the price of finer lines.",
            &["High-NA fields are half the NXE size (ASML, 2024)"],
        ),
    Beat::new("so a wafer takes about twice the exposures", BEAT_MS)
        .note(
            "Half-size fields mean about twice as many exposures per wafer, which costs throughput.",
            "the same row of fields, now with an orange split across every one",
        )
        .detail(
            "High-NA: half-size fields, about twice the exposures (page text).",
            &["High-NA fields are half size (ASML, 2024)"],
        ),
];

pub const OVERLAY_BEATS: &[Beat] = &[
    Beat::new("the new layer sits off the one below", BEAT_MS)
        .note(
            "The layer below is already etched. If the wafer sits a little off, the new lines print beside the old ones instead of on them.",
            "pink new lines sit offset from the cyan lines below them",
        )
        .detail(
            "Every layer has to connect to the ones below, so a shift breaks contacts.",
            &["Overlay is how exactly one layer lines up with the layers below it (page text)"],
        ),
    Beat::new("the sensor reads the marks and the stage corrects", BEAT_MS)
        .note(
            "The alignment sensor measures the marks printed in the layer below, and the stage moves the wafer until the new image lands on top.",
            "green sensor beams read the marks at both ends, and the pink lines slide over onto the cyan ones",
        )
        .detail(
            "Alignment happens on every wafer before it is exposed.",
            &["The scanner aligns each wafer using marks printed on earlier layers (page text)"],
        ),
    Beat::new("budget: a few nanometres", BEAT_MS)
        .note(
            "Overlay error has to stay at a few nanometres, a small fraction of the line width, or contacts miss their targets.",
            "the pink lines sit square on the cyan ones",
        )
        .detail(
            "A matched machine holds this budget with room to spare.",
            &["NXE:3800E matched-machine overlay 0.9 nm (ASML annual report 2024)"],
        ),
    Beat::new("the next wafer drifts off again", BEAT_MS)
        .note(
            "Every wafer arrives with its own offset, so alignment runs again on each one.",
            "the pink lines drift a little off the cyan ones again",
        )
        .detail(
            "Overlay error adds up with every extra exposure, which is one cost of multi-patterning.",
            &["Overlay error adds up per exposure (page text)"],
        ),
];

pub const EUV_BEATS: &[Beat] = &[
    Beat::new("EUV light: a laser hits each tin droplet twice", BEAT_MS)
        .note(
            "EUV light does not exist in usable form, so the scanner makes it. A tin droplet falls and a CO2 laser flashes it into plasma that emits 13.5 nm light.",
            "a grey tin droplet falls into a yellow laser flash, and a white plasma flares where it lands",
        )
        .detail(
            "Debris from the blast can coat the optics that make the light.",
            &["13.5 nm light from the plasma (page text)", "About 50,000 tin droplets a second (not yet sourced here)"],
        ),
    Beat::new("no glass: the light bounces off mirrors", BEAT_MS)
        .note(
            "EUV is absorbed by nearly everything, air and glass included, so the whole path is in vacuum with mirrors.",
            "a yellow beam zig-zags between blue-grey mirrors",
        )
        .detail(
            "Each mirror is a stack of molybdenum and silicon layers.",
            &["Each mirror keeps about 70% (not yet sourced here)"],
        ),
    Beat::new("sub-nanometre parts from a long supply chain", BEAT_MS)
        .note(
            "The optics must hold sub-nanometre alignment. Zeiss supplies the ultra-flat optics, and few suppliers make these parts.",
            "a pile of grey parts sits below the mirror row, and one mirror tilts a little",
        )
        .detail(
            "Mirror optics and the tin-droplet source are single points of failure.",
            &["Mirror optics (Zeiss, for ultra-flat optics) are a single point of failure (page text)"],
        ),
    Beat::new("a dozen mirrors leave about 1%", BEAT_MS)
        .note(
            "The losses compound, so a dozen mirrors leave about 1% of the EUV energy before it reaches the wafer.",
            "the yellow beam runs through the mirror row, and the tag marks the total loss",
        )
        .detail(
            "That is why the source must be very bright and stable, and why the optics are so hard to build.",
            &["A dozen mirrors leave about 1% (not yet sourced here)"],
        ),
];

static RETICLE: Cell = std::sync::OnceLock::new();
static LENS: Cell = std::sync::OnceLock::new();
static RESIST: Cell = std::sync::OnceLock::new();
static SCAN: Cell = std::sync::OnceLock::new();
static OVERLAY: Cell = std::sync::OnceLock::new();
static EUV: Cell = std::sync::OnceLock::new();

pub fn reticle() -> Box<dyn Scene> {
    page(&RETICLE, include_bytes!("../../../../../tools/pbr3d/assets/litho_reticle.glb"), RETICLE_BEATS)
}

pub fn lens() -> Box<dyn Scene> {
    page(&LENS, include_bytes!("../../../../../tools/pbr3d/assets/litho_lens.glb"), LENS_BEATS)
}

pub fn resist() -> Box<dyn Scene> {
    page(&RESIST, include_bytes!("../../../../../tools/pbr3d/assets/litho_resist.glb"), RESIST_BEATS)
}

pub fn scan() -> Box<dyn Scene> {
    page(&SCAN, include_bytes!("../../../../../tools/pbr3d/assets/litho_scan.glb"), SCAN_BEATS)
}

pub fn overlay() -> Box<dyn Scene> {
    page(&OVERLAY, include_bytes!("../../../../../tools/pbr3d/assets/litho_overlay.glb"), OVERLAY_BEATS)
}

pub fn euv() -> Box<dyn Scene> {
    page(&EUV, include_bytes!("../../../../../tools/pbr3d/assets/litho_euv.glb"), EUV_BEATS)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("reticle", reticle as fn() -> Box<dyn Scene>),
            ("lens", lens),
            ("resist", resist),
            ("scan", scan),
            ("overlay", overlay),
            ("euv", euv),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
