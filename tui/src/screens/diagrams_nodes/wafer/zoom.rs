// WAFER zoom-ins a-d in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/wafer_zooms.py: a flatness sites, b the epi layer, c SOI by Smart Cut,
// d the spec sheet. Four beats each. Cross-sections are drawn thicker than life.
//
// Sources: SEMI 2025 wafer shipments and revenue [1]; vendor 300 mm datasheets SV029 and SV031 [2];
// SEMI M1 and M43 [3]; SFQR / ESFQR patent US 12,635,427 [4]; SOI implant depth US 8,497,187 [7].

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

pub const SITES_BEATS: &[Beat] = &[
    Beat::new("the wafer is cut into scanner-field sites, with a 3 mm rim left out", BEAT_MS)
        .note(
            "A lithography scanner exposes the wafer one field at a time, so flatness is judged site by site. The disc is tiled with square sites, and the sites that fit inside the rim with 3.0 mm edge exclusion are the ones that count.",
            "a grey grid of square sites tiles the top of the disc, with a thin gap between each site and the grey rim at the edge",
        )
        .detail(
            "SFQR is the number that maps most directly onto lithography focus, so it is checked one site at a time.",
            &[
                "SFQR: site flatness within one scanner-field-sized site (SEMI M1 family, page section 3)",
                "Edge exclusion 3.0 mm on 300 mm p-type Cz vendor sheets (SV029, SV031)",
                "ESFQR is the same idea on the edge sites, where partial sites count too (US 12,635,427)",
            ],
        ),
    Beat::new("a scan bar reads each site against a best-fit focal plane", BEAT_MS)
        .note(
            "A scan bar crosses the disc and reads the sites as it goes. Each site is measured against a best-fit focal plane; sites that pass light up green, and the rim sites turn gold as they are read.",
            "a cyan bar sweeps across the grid from the left; behind it the interior sites turn green and the rim sites go gold",
        )
        .detail(
            "The scanner's focus has to hold across every site in the field, so one bad site can cost yield even when the average is good.",
            &[
                "SFQR and ESFQR and edge exclusion are defined in US 12,635,427 (page source [4])",
                "SEMI M1 numeric SFQR limits are not public in what the page found; buyers set them per node",
            ],
        ),
    Beat::new("edge sites: ESFQR must hold on partial sites, with only 3.0 mm of edge exclusion", BEAT_MS)
        .note(
            "The rim is the hardest part of the wafer to keep flat. ESFQR applies to the edge sites, and flatness must hold on partial sites with only the small edge exclusion left.",
            "a ring of gold edge sites round the disc, and two red sites near the rim that fail the limit",
        )
        .detail(
            "A failing site is a reason to reject the wafer or send it elsewhere. Buyers set limits per node and per customer, so a wafer can pass for one fab and fail for another.",
            &[
                "Edge exclusion 3.0 mm (SV029, SV031 datasheets)",
                "ESFQR on partial sites with tiny edge exclusion (US 12,635,427)",
                "Buyers set SFQR limits per node (page section 3)",
            ],
        ),
    Beat::new("one site can pass on paper and still miss the focus budget on the chuck", BEAT_MS)
        .note(
            "A patent argues SFQR is computed as if the wafer lay on an ideal plane, but the scanner holds it on its own chuck. A site that is flat by SFQR can therefore push critical-dimension variation out of tolerance.",
            "one red site rises as a raised block in the grid, with a tag reading chuck: focus budget can fail",
        )
        .detail(
            "This is why chucked flatness matters as much as the datasheet number, and why SFQR is a lithography figure as well as a wafer one.",
            &[
                "A wafer flat by SFQR can still exceed the focus budget (patent US 7,474,386)",
                "An older interferometry paper cites an ITRS nanotopography projection of 13 nm or less by 2010 (dated)",
            ],
        ),
];

pub const EPI_BEATS: &[Beat] = &[
    Beat::new("the bulk wafer is the base that an epi layer is grown on", BEAT_MS)
        .note(
            "Epi is a thin single-crystal layer grown on top of a bulk substrate, done by the wafer maker. This cut-away shows the bulk substrate alone, with its polished top face.",
            "a grey block cut open at the front: the bulk silicon, with a pale polished top face",
        )
        .detail(
            "The substrate sets the mechanical base. The layer on top is where the electrical properties of the transistors are set.",
            &[
                "775 +/- 25 um thickness on a typical 300 mm p-type sheet (SV029)",
                "TTV 5 um or less on the same sheet (SV029, SV031)",
                "The block is drawn thicker than life; this picture is not to scale",
            ],
        ),
    Beat::new("trichlorosilane gas flows over the hot wafer and silicon deposits on it", BEAT_MS)
        .note(
            "Gas carrying silicon flows over the heated wafer, and silicon deposits on the top face as a single-crystal layer. The patent examples grow the layer from trichlorosilane at 1100 to 1130 C on 300 mm wafers.",
            "pale blue gas blobs drift along the top face from left to right over the grey block",
        )
        .detail(
            "The grower picks gas, temperature and time, which set the layer's thickness and doping. That is why epi is made by the wafer maker, not the chipmaker.",
            &[
                "Trichlorosilane at 1100 to 1130 C on 300 mm wafers (patents, not a standard)",
                "Epi is grown by CVD from gas (page section 2)",
            ],
        ),
    Beat::new("the epi layer grows up on the bulk: 1 to 10 um in patents, about 3 to 6 um typical", BEAT_MS)
        .note(
            "The tan layer builds up on the substrate until it sits on the bulk. It is a thin single-crystal film, continuing the crystal below it (textbook).",
            "a tan band grows up along the top of the grey block until it covers the whole top face",
        )
        .detail(
            "Patent examples put the layer at 1 to 10 um, with about 3 to 6 um typical. The page says these are patent figures, not a standard.",
            &[
                "Epi 1 to 10 um, about 3 to 6 um typical (patents)",
                "For imaging sensors one patent prefers 3 to 6 um (patent)",
                "Epi drawn about 10 times thicker than life here",
            ],
        ),
    Beat::new("devices sit in the epi layer, where doping and purity are tuned", BEAT_MS)
        .note(
            "The layer can differ in doping and purity from the substrate, giving fewer crystal defects and better-controlled electrical properties where the transistors sit. SEMI ties advanced epi to sub-3nm logic.",
            "the tan epi band on top of the grey bulk, with tags on the layer and on its tuned doping",
        )
        .detail(
            "Advanced epi for sub-3nm logic is one of the demand drivers SEMI named for 2025, and the segment is lumpy because it follows foundry utilisation.",
            &[
                "Advanced epi for sub-3nm logic is a 2025 demand driver (SEMI)",
                "Two Japanese firms held over 60% of 300 mm epi in 2H 2020 (SEMI)",
            ],
        ),
];

pub const SOI_BEATS: &[Beat] = &[
    Beat::new("a hydrogen implant forms a weak layer in the donor wafer", BEAT_MS)
        .note(
            "SOI is made with Smart Cut: hydrogen ions are implanted into a donor wafer to a set depth. That depth bounds how thick the top silicon layer can be.",
            "a grey donor block sits high in the frame; cyan ions rise into its underside, and a thin gold plane marks the weak layer",
        )
        .detail(
            "The donor wafer is reused after the split, which is part of the economics of the process.",
            &[
                "Implant depth about 2 um max at roughly 200 keV (patent US 8,497,187)",
                "Smart Cut: implant, bond, split, then CMP polish (Electronic Design)",
            ],
        ),
    Beat::new("the donor is pressed face down onto the oxide-covered handle wafer", BEAT_MS)
        .note(
            "The implanted face of the donor comes down onto a handle wafer that already carries a buried oxide. The two are pressed together to form the bond.",
            "the grey donor comes down over the handle, meeting its gold oxide band",
        )
        .detail(
            "Bonding sets up the stack: the slice of the donor above the implant becomes the device layer.",
            &[
                "SOI stacks a device layer over a buried oxide on a handle wafer (WAFER page, section 2)",
                "Soitec is the SOI name in the share table: 5.5% about 2021 (Semiconductor Engineering)",
            ],
        ),
    Beat::new("an anneal splits the donor along the hydrogen layer; the rest lifts away", BEAT_MS)
        .note(
            "An anneal splits the donor at the hydrogen layer. The thin film stays bonded to the handle, and the rest of the donor lifts clear. A polish then smooths the transferred film.",
            "the upper part of the donor rises away from the film, which stays on the oxide; the gold weak plane is gone",
        )
        .detail(
            "The split is what leaves a thin film on the handle. The donor is not thrown away.",
            &[
                "Anneal splits at the hydrogen layer, then CMP polishes the film (Electronic Design)",
                "The donor wafer is reused (Soitec process)",
            ],
        ),
    Beat::new("the device layer sits on the buried oxide, over the handle wafer", BEAT_MS)
        .note(
            "The finished SOI stack has a thin top silicon device layer, a buried oxide and a handle wafer. Implant settings give good control of the top-layer thickness.",
            "three bands: a teal device layer on top, a gold oxide line, and the grey handle wafer beneath, with tags naming each",
        )
        .detail(
            "The buried oxide isolates the devices from the handle. Each rung up the wafer ladder costs more and has fewer qualified suppliers (textbook).",
            &[
                "Device layer about 2 um max, bounded by implant depth (US 8,497,187)",
                "Soitec 5.5% share about 2021; no current FD-SOI capacity figures were found",
            ],
        ),
];

pub const SPEC_BEATS: &[Beat] = &[
    Beat::new("thickness: 775 um +/- 25 um on a typical 300 mm p-type vendor sheet", BEAT_MS)
        .note(
            "The spec sheet starts with thickness. A typical 300 mm p-type Cz vendor sheet specifies 775 +/- 25 um, with a 3.0 mm edge exclusion. The gold dimension bar marks the range and is not to scale.",
            "a grey slab cut open, with a gold dimension bar at its right and a tag marking the thickness as not to scale",
        )
        .detail(
            "Thickness is the coarse number. The tighter ones follow: TTV, then the site flatness measures.",
            &[
                "775 +/- 25 um, TTV 5 um or less, edge exclusion 3.0 mm (SV029, SV031)",
                "Spec fields as printed on the vendor sheets (page section 3)",
            ],
        ),
    Beat::new("TTV: the maximum minus the minimum thickness across the wafer", BEAT_MS)
        .note(
            "Total thickness variation is the maximum minus the minimum thickness across the wafer. Commodity 300 mm sheets allow 5 um or less, and leading-edge specs are much tighter.",
            "the slab's top face is tilted, exaggerated, so one end sits higher than the other",
        )
        .detail(
            "Tighter TTV and SFQR means more polishing and metrology at the wafer maker, which is part of why leading-edge wafers price above commodity.",
            &[
                "TTV 5 um or less (SV029, SV031)",
                "Vendor guidance: TTV under 1 um at 10 nm nodes and beyond (guidance, not a standard)",
            ],
        ),
    Beat::new("SFQR: flatness within each scanner-field site, against a best-fit plane", BEAT_MS)
        .note(
            "Site flatness (SFQR) is the range of wafer topography within one scanner-field-sized site, measured against a best-fit focal plane. It is the number that maps most directly onto lithography focus.",
            "a top-down disc with a grid of grey sites tiled across it, tags naming SFQR for one site",
        )
        .detail(
            "The patents argue SFQR is computed as if the wafer were perfectly chucked, which a real scanner does not do. That is why flatness is also measured in a chucked state.",
            &[
                "SFQR and ESFQR with edge exclusion (US 12,635,427)",
                "Site flatness under 0.1 um at 10 nm nodes and beyond (vendor guidance, not a standard)",
            ],
        ),
    Beat::new("area: pi times (150 mm) squared, about 70,686 mm2 on each face", BEAT_MS)
        .note(
            "One face of a 300 mm wafer has an area of pi times 150 mm squared, about 70,686 mm2, which is about 109.6 square inches. The gold ring marks the rim.",
            "a top-down disc with a gold ring at its rim and a tag giving the face area",
        )
        .detail(
            "Area is the denominator for the per-area price in section 4. The arithmetic is the page's own, so it is not a sourced figure.",
            &[
                "pi x (150 mm)^2 = 70,686 mm2 (page arithmetic)",
                "About 109.6 square inches per face (page arithmetic)",
            ],
        ),
];

static SITES: Cell = std::sync::OnceLock::new();
static EPI: Cell = std::sync::OnceLock::new();
static SOI: Cell = std::sync::OnceLock::new();
static SPEC: Cell = std::sync::OnceLock::new();

pub fn sites() -> Box<dyn Scene> {
    page(
        &SITES,
        include_bytes!("../../../../../tools/pbr3d/assets/wafer_zoom_sites.glb"),
        SITES_BEATS,
    )
}

pub fn epi() -> Box<dyn Scene> {
    page(
        &EPI,
        include_bytes!("../../../../../tools/pbr3d/assets/wafer_zoom_epi.glb"),
        EPI_BEATS,
    )
}

pub fn soi() -> Box<dyn Scene> {
    page(
        &SOI,
        include_bytes!("../../../../../tools/pbr3d/assets/wafer_zoom_soi.glb"),
        SOI_BEATS,
    )
}

pub fn spec() -> Box<dyn Scene> {
    page(
        &SPEC,
        include_bytes!("../../../../../tools/pbr3d/assets/wafer_zoom_spec.glb"),
        SPEC_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("sites", sites as fn() -> Box<dyn Scene>),
            ("epi", epi),
            ("soi", soi),
            ("spec", spec),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
