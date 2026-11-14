// WAFER sections 1-8 and the sources page (9), each a Blender picture from
// tools/pbr3d/blender/wafer_sections.py in the picture-and-panel template. Beats per section:
// 4, 3, 4, 4, 4, 4, 4, 3, 3. Section 9 is the sources page: nine cards lit three at a time.
//
// Sources: [1] SEMI, 2025 annual silicon wafer shipments and revenue (10 Feb 2026); [2] vendor 300 mm
// datasheets SV029 and SV031; [3] SEMI M1 and M43; [4] SFQR / ESFQR patent US 12,635,427; [5] Semiconductor
// Engineering, market shares 2021; [6] GEP, top-five concentration 2018; [7] SOI implant depth US 8,497,187;
// [8] 300 mm market blog, low confidence; [9] China wafer landscape report 2026.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("polished: a 300 mm prime wafer with a mirror top face", BEAT_MS)
        .note(
            "The finished substrate starts at a polish station: a mirror top face on a 300 mm disc. Almost every chipmaker buys this wafer, so the step names here are textbook.",
            "a grey disc on a station block at the left of the track, its top face catching the light",
        )
        .detail(
            "The wafer is the flat reference for every later layer, so its surface is the first thing the fab checks.",
            &[
                "775 +/- 25 um, 300 mm p-type Cz (SV029, [2])",
                "pi x (150 mm)^2 = 70,686 mm2 per face (page arithmetic)",
            ],
        ),
    Beat::new("optional epi or SOI: a layer is added for the AI-grade wafers", BEAT_MS)
        .note(
            "The disc moves to the second station, where an optional epi or SOI layer can go on. Epi is grown by the wafer maker by CVD; SOI bonds a device layer over a buried oxide.",
            "the disc at the second station with a tan epi layer now coating its top face",
        )
        .detail(
            "Epi and SOI are the upgrades that separate commodity wafers from AI-grade ones. Each step up costs more and has fewer qualified suppliers (textbook).",
            &[
                "Epi about 3 to 6 um typical (patents)",
                "Advanced epi for sub-3nm logic is a 2025 demand driver (SEMI, [1])",
            ],
        ),
    Beat::new("inspect: TTV, SFQR and particles decide whether a wafer ships", BEAT_MS)
        .note(
            "The inspection station checks flatness as TTV, SFQR and nanotopography, and counts surface particles by laser scanning (textbook). A cyan scan bar passes over the wafer.",
            "a cyan scan bar passes over the wafer at the inspection station",
        )
        .detail(
            "A wafer can pass for one fab and fail another. SFQR is a lithography number as much as a wafer one.",
            &[
                "TTV 5 um or less on commodity 300 mm sheets (SV029, [2])",
                "SFQR and edge exclusion: US 12,635,427 ([4])",
            ],
        ),
    Beat::new("pack: a FOUP carrier, then litho, etch, deposit and CMP", BEAT_MS)
        .note(
            "Finished wafers ship in sealed carriers. The FOUP (front opening unified pod) holds 25 wafers at a 10 mm slot pitch (secondary sources). From here the wafer goes to the fab, where litho, etch, deposit and CMP start.",
            "the wafer slides into a clear glass-walled carrier on the last station, with a tag for the fab steps",
        )
        .detail(
            "Every DEPOSIT, LITHO and ETCH step starts from this flat reference (section 8).",
            &[
                "25 wafers at a 10 mm slot pitch (secondary sources)",
                "Entegris A300: 25-slot and 13-slot versions (datasheet)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("polished (bulk): one single crystal, 775 um thick, mirror top", BEAT_MS)
        .note(
            "A polished wafer is one slab of single-crystal silicon. Its top face is mirror polished, and the bulk is the same material all the way through.",
            "a uniform grey cut-away block with a bright top edge",
        )
        .detail(
            "The bulk is the mechanical base for every layer added on top, so its thickness and flatness are set on the datasheet.",
            &["775 +/- 25 um, TTV 5 um or less, edge exclusion 3.0 mm (SV029, SV031, [2])"],
        ),
    Beat::new("epitaxial (epi on bulk): a few um layer grown by CVD from gas", BEAT_MS)
        .note(
            "An epi wafer adds a thin single-crystal layer on top of the bulk, grown by CVD from gas. The layer can differ in doping and purity, which gives fewer crystal defects where the transistors sit.",
            "the grey bulk with a tan band on top, the epi layer, drawn thicker than life",
        )
        .detail(
            "The layer is grown by the wafer maker, not the chipmaker. Advanced epi wafers are one of the 2025 demand drivers.",
            &[
                "Epi 1 to 10 um, about 3 to 6 um typical (patents)",
                "Grown from trichlorosilane at 1100 to 1130 C (patents)",
            ],
        ),
    Beat::new("SOI (silicon on insulator): a device layer over a buried oxide", BEAT_MS)
        .note(
            "SOI sandwiches a buried oxide between a thin device layer and a handle wafer. Soitec makes it with Smart Cut: implant, bond and split. The implant depth limits the top layer.",
            "three bands: a teal device layer on top, a gold oxide line, and the grey handle wafer beneath, drawn thicker than life",
        )
        .detail(
            "The buried oxide isolates the devices from the handle. The cost rises with each rung of the ladder (textbook).",
            &[
                "SOI layer about 2 um max at roughly 200 keV implant (US 8,497,187, [7])",
                "Soitec is the SOI name in the share table, 5.5% about 2021 ([5])",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("thickness: 775 um +/- 25 um on a typical 300 mm p-type vendor sheet", BEAT_MS)
        .note(
            "A typical 300 mm p-type Cz vendor sheet specifies a thickness of 775 +/- 25 um. The gold dimension bar marks the range; the picture is not to scale.",
            "a grey slab with a gold dimension bar at its right end and a tag marking the picture as not to scale",
        )
        .detail(
            "Thickness is the coarse number. The tighter ones are TTV, SFQR and nanotopography.",
            &[
                "775 +/- 25 um, TTV 5 um or less, edge exclusion 3.0 mm (SV029, SV031, [2])",
                "Spec fields as printed on the vendor sheets",
            ],
        ),
    Beat::new("TTV: the thickness spread across the wafer, 5 um or less", BEAT_MS)
        .note(
            "TTV is the maximum minus the minimum thickness across the wafer. Commodity 300 mm sheets allow 5 um or less; leading-edge specs are much tighter.",
            "the slab's top face is tilted, exaggerated, so one end sits higher than the other",
        )
        .detail(
            "Vendor guidance quotes TTV under 1 um at 10 nm nodes and beyond, far tighter than the commodity spec.",
            &[
                "TTV 5 um or less (SV029, SV031, [2])",
                "TTV under 1 um at 10 nm nodes and beyond (vendor guidance, not a standard)",
            ],
        ),
    Beat::new("SFQR: flatness within each scanner-field site", BEAT_MS)
        .note(
            "Site flatness (SFQR) is the range of wafer topography within one scanner-field-sized site, measured against a best-fit focal plane. Its grid of sites is tiled across the disc.",
            "a top-down disc with a grid of grey sites tiled across it, with a tag for SFQR on one site",
        )
        .detail(
            "SFQR maps most directly onto lithography focus. Patents argue it is computed as if the wafer were chucked on an ideal plane, which a scanner does not do.",
            &[
                "SFQR and ESFQR with edge exclusion (US 12,635,427, [4])",
                "Site flatness under 0.1 um at 10 nm nodes and beyond (vendor guidance, not a standard)",
            ],
        ),
    Beat::new("area: about 70,686 mm2 on each face, about 109.6 sq in", BEAT_MS)
        .note(
            "One face of a 300 mm wafer is pi times (150 mm) squared, about 70,686 mm2, or about 109.6 square inches. A gold ring marks the rim, and the area is the basis for the per-area figures in section 4.",
            "a top-down disc ringed in gold, with its area tagged on the rim",
        )
        .detail(
            "The area is the page's own arithmetic, not a sourced figure.",
            &[
                "pi x (150 mm)^2 = 70,686 mm2 (page arithmetic)",
                "About 109.6 square inches per face (page arithmetic)",
            ],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("shipments: 12,973 million square inches in 2025, up 5.8%", BEAT_MS)
        .note(
            "SEMI reported 2025 silicon wafer shipments of 12,973 million square inches (MSI), up 5.8%. The 2024 bar is back-calculated from the percentage change, so it is derived, not reported.",
            "two bars: a grey 2024 bar, derived, and the taller gold 2025 bar",
        )
        .detail(
            "Shipments measure area sold, not money. That is why revenue can fall while area rises.",
            &[
                "12,973 MSI in 2025, up 5.8% (SEMI, [1])",
                "About 12,262 MSI in 2024, derived from the percentage change",
            ],
        ),
    Beat::new("revenue: $11.4 billion in 2025, down 1.2%", BEAT_MS)
        .note(
            "Revenue fell 1.2% to $11.4 billion in 2025 (SEMI). The 2024 bar is derived from the percentage change and is about $11.5 billion.",
            "two bars of nearly equal height: the gold 2025 bar, and the derived grey 2024 bar",
        )
        .detail(
            "SEMI attributes the softness mostly to slow momentum in traditional applications, where pricing has yet to improve.",
            &[
                "$11.4 billion in 2025, down 1.2% (SEMI, [1])",
                "About $11.5 billion in 2024 (derived)",
            ],
        ),
    Beat::new("area against revenue: area up 5.8%, revenue down 1.2%", BEAT_MS)
        .note(
            "Area sold rose 5.8% while revenue fell 1.2%. Revenue per square inch is about $0.88 on the page's arithmetic, and it is falling.",
            "a tall blue bar for area up 5.8% beside a small red bar below the line for revenue down 1.2%",
        )
        .detail(
            "A falling price per area is a margin risk for makers, and it sits against the two-speed market.",
            &[
                "Area +5.8% and revenue -1.2% (SEMI, [1])",
                "About $0.88 per square inch, all diameters mixed (page arithmetic)",
            ],
        ),
    Beat::new("300 mm: 67% of polished wafers in 2023, from one low-confidence blog", BEAT_MS)
        .note(
            "One market-research blog puts the 300 mm share of the polished-wafer market at 67% in 2023, and the top five at 85%. Its basis is unclear, so treat it as low confidence. AI demand for advanced epi and HBM polished wafers is the strong part.",
            "a single gold bar at 67, with a tag marking the figure as low confidence",
        )
        .detail(
            "The blog's market size differs from SEMI's. Read the share as a rough scale, not a measured figure.",
            &[
                "67% of the polished-wafer market in 2023; top five 85% (blog, [8], low confidence)",
                "AI: advanced epi for sub-3nm logic and polished wafers for HBM (SEMI, [1])",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("the top two: Shin-Etsu 29.4% and SUMCO 21.9%, about 2021", BEAT_MS)
        .note(
            "About 2021, Shin-Etsu held 29.4% of the wafer market and SUMCO 21.9%, from the GlobalWafers figures via Semiconductor Engineering. These are the top two makers.",
            "two tall gold bars at the left of the row, each tagged with its maker and share",
        )
        .detail(
            "Shin-Etsu also sells the photoresist and other materials seen on the COAT page.",
            &[
                "Shin-Etsu 29.4%, SUMCO 21.9% (Semiconductor Engineering, [5])",
                "Shin-Etsu Chemical 4063.T and SUMCO 3436.T (tickers are textbook)",
            ],
        ),
    Beat::new("the next three: GlobalWafers 15.2%, Siltronic 11.5%, SK Siltron 11.4%", BEAT_MS)
        .note(
            "The next three makers hold 15.2%, 11.5% and 11.4%. GlobalWafers is the largest of them, and Siltronic and SK Siltron are close behind.",
            "three blue bars in the middle of the row, each tagged with its maker and share",
        )
        .detail(
            "Five makers dominate the market, so the rest of the bars are small.",
            &[
                "GlobalWafers 15.2%, Siltronic 11.5%, SK Siltron 11.4% (about 2021, [5])",
                "Top five above 90% (GEP 2018, [6])",
            ],
        ),
    Beat::new("the top five hold 85%; Soitec, the SOI name, holds 5.5%", BEAT_MS)
        .note(
            "Soitec, the SOI name, holds 5.5%. Adding the top five gives about 85% in one 2023 blog, which is low confidence. A 2018 GEP outlook puts the top five above 90%. A red bracket spans the five.",
            "a small grey bar at the right for Soitec, and a red bracket over the top five with tags for each total",
        )
        .detail(
            "The concentration is the chokepoint: five suppliers, mostly in Japan.",
            &[
                "Top five above 90% (GEP 2018, [6])",
                "Top five 85% (blog, [8], low confidence); Soitec 5.5% (about 2021, [5])",
            ],
        ),
    Beat::new("a 2025-ish source puts Shin-Etsu at 28% and SUMCO at 25%", BEAT_MS)
        .note(
            "A 2025-ish source gives Shin-Etsu about 28%, SUMCO about 25%, GlobalWafers 15, Siltronic 12 and SK Siltron 11. Two pale ghost blocks show that source behind the 2021 bars.",
            "two pale ghost blocks behind the gold Shin-Etsu and SUMCO bars, showing the 2025-ish share",
        )
        .detail(
            "Shares move between sources and years, so compare them with care. The 2021 chart stays the main source.",
            &[
                "2025-ish source: Shin-Etsu about 28%, SUMCO about 25% (China report, [9])",
                "2021 chart: Shin-Etsu 29.4%, SUMCO 21.9% ([5])",
            ],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("five makers dominate, each with its own listing", BEAT_MS)
        .note(
            "Shin-Etsu Chemical (4063.T), SUMCO (3436.T), GlobalWafers (6488.TWO), Siltronic (WAF.DE) and SK Siltron (owned by SK Inc, 034730.KS) make most of the wafers. The tickers are textbook, not sourced.",
            "five paper cards fly in, each with a maker and its ticker, each with a gold rule",
        )
        .detail(
            "The top five hold more than 90% of the market (GEP 2018); the list has been consistent since.",
            &[
                "Top five above 90% (GEP 2018, [6])",
                "Soitec (SOI.PA) is the SOI name (textbook ticker)",
            ],
        ),
    Beat::new("SK Siltron is held by SK Inc, so it is not a standalone listing", BEAT_MS)
        .note(
            "SK Siltron is owned by SK Inc (034730.KS), so it is one of the five but not a standalone listing. The picture slides it into the SK Inc card.",
            "a large SK Inc card, with a blue SK Siltron block sliding into it",
        )
        .detail(
            "A parent company's filings show the wafer maker inside its own results, not as a separate line (textbook).",
            &[
                "SK Siltron owned by SK Inc, 034730.KS (page)",
                "Top five above 90% (GEP 2018, [6])",
            ],
        ),
    Beat::new("two Japanese firms held over 60% of 300 mm epi in 2H 2020", BEAT_MS)
        .note(
            "In the second half of 2020 two Japanese firms held more than 60% of 300 mm epitaxial wafers (SEMI, via Semiconductor Engineering). The gold block is those two; the blue block is everyone else.",
            "a tall gold block for the two Japanese firms beside a shorter blue block for the rest",
        )
        .detail(
            "Two Japanese makers leading is the concentration risk: a quake or outage in Japan would hit every maker at once.",
            &[
                "Over 60% of 300 mm epi, 2H 2020 (SEMI, via Semiconductor Engineering)",
                "Top five above 90% (GEP 2018, [6])",
            ],
        ),
    Beat::new("GlobalWafers and Siltronic: a planned deal to 26.7%, not completed", BEAT_MS)
        .note(
            "GlobalWafers' planned purchase of Siltronic would have combined them at 26.7%, making GlobalWafers the second largest maker. The deal did not complete (textbook).",
            "one stacked bar: blue GlobalWafers at the base, gold Siltronic on top, totalling 26.7%",
        )
        .detail(
            "The combined share is the page's arithmetic from the 2021 shares; the deal itself is not in the sources.",
            &[
                "GlobalWafers 15.2% + Siltronic 11.5% = 26.7% (about 2021, [5])",
                "The deal did not complete (textbook)",
            ],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("a quake or outage in Japan can stop all five makers at once", BEAT_MS)
        .note(
            "Five suppliers, mostly in Japan: a quake or outage hits everyone at once (textbook). Five grey wafer discs stand in a row, and a red quake block drops over them.",
            "five grey wafer discs in a row, and a red quake block dropping over them, with a tag for the outage",
        )
        .detail(
            "Concentration is the single biggest supply risk the page names.",
            &[
                "Top five above 90% (GEP 2018, [6])",
                "Two Japanese firms held over 60% of 300 mm epi (SEMI)",
            ],
        ),
    Beat::new("switching supplier takes many months: each fab qualifies per process", BEAT_MS)
        .note(
            "Each fab qualifies wafers per process, so changing supplier takes many months (textbook; the page gives no number). That gives incumbents stickiness.",
            "a long grey track with a wafer sliding along it to the far end",
        )
        .detail(
            "Capacity additions are long-lead bets, so supply responds slowly to demand.",
            &[
                "Qualification is per process; no number is given on the page (textbook)",
                "UBS: capacity expansion would need price rises of roughly 40% to 50% (broker view)",
            ],
        ),
    Beat::new("the market runs two-speed: AI epi and HBM strong, mature nodes soft", BEAT_MS)
        .note(
            "AI epi and HBM polished wafers are strong, while mature-node wafers for auto, industrial and consumer uses are still soft. SEMI calls this two-track.",
            "a tall gold bar for AI epi and HBM beside a short grey bar for mature nodes",
        )
        .detail(
            "The two tracks mean makers' results can diverge even within one year.",
            &[
                "AI epi and HBM strong, mature nodes soft (SEMI, two-track, [1])",
                "UBS: 12-inch utilization 84% in 2026, rising to 99% in 2028 (broker view)",
            ],
        ),
    Beat::new("2025: area rose 5.8% while revenue fell 1.2%, so price per area is falling", BEAT_MS)
        .note(
            "Area rose 5.8% in 2025 but revenue fell 1.2%, so the price per square inch is falling. That is a margin risk for makers. China is also building domestic 300 mm capacity.",
            "a tall gold bar for area up 5.8% and a short red bar for revenue down 1.2%, with a tag on China's new capacity",
        )
        .detail(
            "Falling price per area squeezes makers who have already built capacity, which is why the page treats it as a risk.",
            &[
                "2025 area +5.8%, revenue -1.2% (SEMI, [1])",
                "China building domestic 300 mm capacity (China report, [9])",
            ],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("upstream: SLICE + POLISH makes the surface; POLY, MELT and PULL make the crystal", BEAT_MS)
        .note(
            "The wafer comes from upstream. SLICE + POLISH makes the surface, and POLYSILICON with MELT and PULL make the crystal the surface is cut from.",
            "two dark blocks at the left, each tagged with its upstream step, and the wafer disc at the centre",
        )
        .detail(
            "The wafer is the handover point: the upstream steps set its crystal and its surface.",
            &[
                "SLICE + POLISH and POLYSILICON + MELT + PULL are the upstream nodes (WAFER page, section 8)",
                "A wafer is bought, not made, by almost every chipmaker (textbook)",
            ],
        ),
    Beat::new("the flat top face is the reference every later layer is built on", BEAT_MS)
        .note(
            "The polished top face is the flat reference for every later layer. Its flatness feeds the focus budget at the lithography scanner, so SFQR is a lithography number as much as a wafer one.",
            "the grey disc at the centre, with two tags on its top face",
        )
        .detail(
            "A flat reference keeps every later layer in focus. A warped one leaves less focus budget for the scanner.",
            &[
                "SFQR is a lithography number as much as a wafer one (WAFER page, section 8)",
                "Site flatness under 0.1 um at 10 nm nodes and beyond (vendor guidance, not a standard)",
            ],
        ),
    Beat::new("downstream: DEPOSIT, LITHO and ETCH all start from this flat reference", BEAT_MS)
        .note(
            "Every DEPOSIT, LITHO and ETCH step starts from this flat reference. Wafer quality that arrives at the fab shows up later as yield (textbook).",
            "the wafer at the centre, and two dark tool blocks rising at the right",
        )
        .detail(
            "Defects, warp or particles that arrive with the wafer travel through hundreds of process steps and are rarely recoverable.",
            &[
                "Hundreds of process steps before the wafer is done (textbook)",
                "GlobalWafers, Aug 4 2026: existing 300 mm capacity fully utilized (company call)",
            ],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("sources 1 to 3: the shipments release, vendor datasheets, SEMI M1 and M43", BEAT_MS)
        .note(
            "Card [1] is SEMI's 2025 annual shipment and revenue release. Card [2] collects the vendor 300 mm datasheets, and card [3] the SEMI M1 scope and M43 nanotopography guide.",
            "three source cards at the front of the layout light up in gold, one after another",
        )
        .detail(
            "These are the primary sources for the flatness terms in section 3 and the market figures in section 4.",
            &[
                "[1] SEMI, 2025 annual silicon wafer shipments and revenue (10 Feb 2026)",
                "[2] vendor datasheets SV029 and SV031; [3] SEMI M1 and M43",
            ],
        ),
    Beat::new("sources 4 to 6: the SFQR patent, 2021 shares and the top-five outlook", BEAT_MS)
        .note(
            "Card [4] is the SFQR and edge-exclusion patent, card [5] the 2021 share chart from Semiconductor Engineering, and card [6] the GEP 2018 top-five outlook.",
            "the middle row of cards lights up in turn",
        )
        .detail(
            "These back the flatness terms in section 3 and the share and concentration figures in sections 5 and 6.",
            &[
                "[4] US 12,635,427 (SFQR, ESFQR)",
                "[5] Semiconductor Engineering, 2021; [6] GEP, top five above 90% (2018)",
            ],
        ),
    Beat::new("sources 7 to 9: the SOI implant patent, a low-confidence blog, China", BEAT_MS)
        .note(
            "Card [7] is the SOI implant-depth patent, card [8] a 300 mm market blog with low confidence, and card [9] the China wafer landscape report for 2026.",
            "the front row of cards lights up, and the blog card is marked low confidence",
        )
        .detail(
            "Card [8] is the basis for the 67% share and the 85% top-five figures; treat it as low confidence.",
            &[
                "[7] US 8,497,187 (SOI implant depth)",
                "[8] 300 mm blog (low confidence); [9] China wafer landscape (2026)",
            ],
        ),
];

static CELLS: [Cell; 9] = [const { std::sync::OnceLock::new() }; 9];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/wafer_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order; section 9 is the sources.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [4, 3, 4, 4, 4, 4, 4, 3, 3]);
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
