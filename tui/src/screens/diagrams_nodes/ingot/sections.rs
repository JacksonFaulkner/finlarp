// INGOT sections 1-9 and the sources in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/ingot_sections.py: one picture per `# ` heading of INGOT.txt, in order.
// Section 1 is five beats, 2-4 four, 5-6 three, 7 four, 8-9 three, and the sources four.
//
// Sources, from the old per-section files:
//   Section 1 (rod, crop, test, grind, notch, saw): US 8,376,809 (Sumco grinder, https://patents.google.com/patent/US8376809);
//     US 11,551,922 (periphery grind and notch, https://patents.google.com/patent/US11551922);
//     SV029 datasheet (https://svmi.com/wp-content/uploads/2021/01/SV029.pdf); INGOT page text.
//   Section 2 (the rod, side view): US 8,256,407 (multi-wire saw, https://patents.google.com/patent/US8256407);
//     US 9,873,159 (diamond-coated wire saw, https://patents.google.com/patent/US9873159);
//     US 12,183,616 (V notch on wafers over 200 mm, https://patents.google.com/patent/US12183616).
//     The 150 mm test-cut pitch and kerf in US 8,256,407 are not used: the page gives no 300 mm kerf.
//   Section 3 (physics): US 5,529,051 (https://patents.google.com/patent/US5529051); Miller and notch text from the
//     INGOT page (Wikipedia-attributed); US 10056395 and US 5993292 seen in search snippets only.
//   Section 4 (wafer numbers): Wikipedia, Wafer (electronics) (https://en.wikipedia.org/wiki/Wafer_(electronics));
//     University Wafer 300 mm sheet (https://www.universitywafer.com/300mm-silicon-wafers.html);
//     SV027 and SV025 datasheets (search snippets; PDFs not parsed).
//   Section 5-6 (size ladder, mass and dies): Wikipedia, Wafer (electronics), standards table.
//   Section 7 (who makes it): Report Prime 2024 ranking (https://www.reportprime.com/large-semiconductor-wafers-r3643/company);
//     Omdia 2020 shares via KED Global (https://www.kedglobal.com/newsView/ked202203160007).
//     The five-firm 68.5% and the 31.5% rest are computed from the 2024 shares; no source prints them.
//   Section 8 (structure and risks): SEMI 2023 release via Mark LaPedus's post
//     (https://marklapedus.substack.com/p/silicon-wafer-market-upturn-higher); Shin-Etsu's LTA comment in the same post.
//     Five-firm share and the LTA rule are INGOT page text.
//   Section 9 (listed names): tickers are general knowledge, not a fetched source. The page gives Siltronic as
//     SSG.DE; that is kept here as the page says. Xetra lists Siltronic as WAF, so the page text should be checked by its owner.
//   Sources (section 10): the page's list [1]-[8] (INGOT.txt).

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("crop: blades cut the seed and tail cones off at the joints", BEAT_MS)
        .note(
            "The as-pulled rod has a seed cone at one end and a tail cone at the other. Blades cut both off at the crop lines, and the cones fall away as scrap, leaving flat cut faces.",
            "two thin steel blades at the joints of the grey rod, and the dark cones dropping away below it",
        )
        .detail(
            "Crop lines are placed by measurement, not at fixed distances, because the usable length depends on where resistivity and defects stay in spec.",
            &[
                "Cropping removes the seed cone with its neck and the tail cone (INGOT page)",
                "Cropping also removes zones with voids or contamination (patent text, US 12617032)",
                "A conservative crop loses silicon; an aggressive one passes marginal wafers (INGOT details)",
            ],
        ),
    Beat::new("test: X-ray on the cut face checks orientation before grinding", BEAT_MS)
        .note(
            "A test sample is taken from the cut face, and X-rays are aimed at it. The spots that come back show the crystal plane, and the orientation is confirmed before grinding.",
            "a cyan X-ray beam onto the flat end face, a reflected beam to a detector block, and bright spots on the face",
        )
        .detail(
            "This is the last cheap point to reject a crystal. Rejecting after slicing wastes saw time and wire.",
            &[
                "Orientation is checked by X-ray diffraction against the intended Miller plane (INGOT details)",
                "The notch tolerance is <110> +/- 1 degree (vendor datasheet)",
                "{100} for logic and CMOS, {111} for bipolar, power and MEMS (Wikipedia infobox)",
            ],
        ),
    Beat::new("grind OD: a wheel brings the rod round to 300 mm", BEAT_MS)
        .note(
            "A grind wheel runs along the rough rod and takes the oversize skin off, so the body is round and at the target outer diameter.",
            "a dark wheel pressed onto the top of the rod, a row of sparks where it touches, and the pale skin going",
        )
        .detail(
            "Diameter control matters because wafer handling robots, FOUPs and every downstream tool assume the 300 mm standard.",
            &[
                "Diameter 300 mm, tolerance +/- 0.2 mm (vendor datasheet, SV029)",
                "A grind wheel brings the ingot to target outer diameter and length (patent text, US 12617032)",
                "Grinding removes silicon that was already pulled and paid for (INGOT details)",
            ],
        ),
    Beat::new("notch: a 90 degree V groove marks <110> along the full length", BEAT_MS)
        .note(
            "A V groove is ground along the whole length of the body. It marks the <110> direction, so every tool can align the wafer to the crystal.",
            "an orange-gold V groove along the top edge of the grey cylinder, from one end to the other",
        )
        .detail(
            "Wafers of 200 mm and up carry one notch instead of flats, because a notch wastes less area. The notch does not show doping type.",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle, <110> +/- 1 degree (vendor datasheet, SV029)",
                "Periphery grind and notch: an arc or approximate V groove marks <110> (US 11,551,922)",
                "The notch marks <110> and does not show doping type (INGOT page)",
            ],
        ),
    Beat::new("wire saw: a diamond wire web cuts the ingot into wafers", BEAT_MS)
        .note(
            "The ingot is bonded to a mounting beam and fed down through a web of diamond-abrasive wire, which cuts every wafer at once. The wire pitch sets the thickness plus the kerf.",
            "the grey rod with a pale mounting beam on top, wires crossing the web, and kerf gaps opening along the body",
        )
        .detail(
            "Saw loss is silicon that was already grown, so thinner wire is a direct yield gain.",
            &[
                "Wafer thickness 775 um, +/- 25 um in vendor sheets (INGOT page)",
                "Wire pitch sets wafer thickness plus kerf (INGOT page)",
                "No kerf, speed or wafers-per-ingot number for 300 mm sawing was found (INGOT page)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("the rod in side view: a seed cone and a tail cone, with the crop lines at the joints", BEAT_MS)
        .note(
            "This is the as-pulled rod from the side. The gold rings mark the crop lines, where the cones meet the body and are cut off.",
            "a grey rod with a seed cone at the left and a tail cone at the right, each joint ringed in gold",
        )
        .detail(
            "Where the cut goes is decided by measurement, after the crystal is characterised.",
            &[
                "Cropping: patent text, US 12617032",
                "The resistivity check step: no source found (INGOT page)",
                "The crop lines mark the seed and tail ends (INGOT details)",
            ],
        ),
    Beat::new("crop: the cones fall away as scrap, and the single-crystal body is kept", BEAT_MS)
        .note(
            "Once cropped, the seed and tail cones drop off as scrap. What is left is the single-crystal body, with a flat end at each side.",
            "a grey body with flat ends, and the two dark cones falling below it",
        )
        .detail(
            "The tail is the most contaminated end, and the seed end is limited by the dislocation-free start.",
            &[
                "The tail is the most contaminated zone; segregation concentrates dopants (textbook)",
                "A conservative crop loses silicon; an aggressive one passes marginal wafers (INGOT details)",
                "Crop length is part of the wafers-per-pull figure, which no source here gives",
            ],
        ),
    Beat::new("notch: a V groove runs the full length of the body, marking <110>", BEAT_MS)
        .note(
            "The groove is ground along the top of the body, so the crystal direction is marked along the whole ingot, not just at one point.",
            "a gold V groove along the top edge of the body, from end to end",
        )
        .detail(
            "The notch depth and angle are fixed by the datasheet, so every wafer cut from the body lines up the same way.",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle (vendor datasheet, SV029)",
                "<110> +/- 1 degree (vendor datasheet, SV029)",
                "US 12,183,616: a V notch on wafers over 200 mm, 1.0 to 1.05 mm deep, 90 degrees (patent text)",
            ],
        ),
    Beat::new("saw: the ingot is fed down through the wire web and cut into wafers", BEAT_MS)
        .note(
            "A single wire is wound around grooved rollers to make a web. The ingot, bonded to its mounting beam, is fed down through the wires, and each gap leaves a wafer.",
            "the rod with a pale mounting beam, wires in a web across the lower part of the rod, and the cut wafers forming",
        )
        .detail(
            "Diamond abrasive on the wire does the cutting, so all the wafers are cut in one pass.",
            &[
                "A single wire is wound around grooved rollers to form a web (INGOT page)",
                "US 9,873,159: a diamond-coated wire saw, the beam lowered at table speed (patent text)",
                "No kerf number for 300 mm sawing was found (INGOT page)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("{100}: the top face is a square grid, the standard for logic and CMOS", BEAT_MS)
        .note(
            "Silicon atoms form a repeating lattice. On the top face, the atoms sit on a square grid; that is the {100} plane.",
            "a cube of grey atoms with its top layer lit gold, showing the square grid",
        )
        .detail(
            "The Miller index says which atomic plane faces up. Orientation is set by the seed in the MELT + PULL step.",
            &[
                "{100} for standard logic and CMOS (Wikipedia infobox)",
                "Orientation is set by the seed in MELT + PULL (INGOT page)",
                "Miller index sets which atomic plane faces up (INGOT page)",
            ],
        ),
    Beat::new("{111}: a diagonal plane with a triangular grid, used for bipolar, power and MEMS", BEAT_MS)
        .note(
            "A slanted plane through the same lattice shows a triangular grid. That is the {111} plane, used for bipolar, power and MEMS.",
            "a tilted tan plate cutting diagonally through the cube of grey atoms",
        )
        .detail(
            "The plane a wafer is cut on sets which devices it suits, so the orientation is chosen at the seed.",
            &[
                "{111} for bipolar, power and MEMS (Wikipedia infobox)",
                "Orientation is set by the seed in MELT + PULL (INGOT page)",
                "A mis-seeded crystal is discovered at the test step (INGOT details)",
            ],
        ),
    Beat::new("the notch marks <110>, where a flat would waste edge area", BEAT_MS)
        .note(
            "A wafer of 200 mm and up carries one small notch instead of flats. The notch marks the <110> direction; it does not show doping type.",
            "a grey wafer face on, with a gold notch cut into its rim at the top",
        )
        .detail(
            "450 mm wafers were to be notchless, with a laser mark instead.",
            &[
                "The notch marks <110>, not doping type (INGOT page)",
                "US 5,529,051: <110> found by X-ray, flat or notch ground to it, about 1 degree (patent text)",
                "The usual <110> orientation tolerance is +/- 1 degree (search snippet, US 5993292)",
            ],
        ),
    Beat::new("dopant: boron or phosphorus atoms set the resistivity, at 1e13 to 1e16 per cm3", BEAT_MS)
        .note(
            "A few blue dopant atoms sit in the silicon lattice in place of silicon atoms. The dopant level sets the resistivity of the crystal.",
            "the grey lattice with a few blue dopant atoms scattered through it",
        )
        .detail(
            "The purity is high: transition metals are held below ppb, and any metal loaded into the melt cannot be removed later.",
            &[
                "Doping 1e13 to 1e16 atoms per cm3 (Wikipedia, via INGOT page)",
                "Purity still above 99.9999%, transition metals below ppb (INGOT page)",
                "Boron, phosphorus, arsenic or antimony are the dopants named (INGOT page)",
            ],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("a 300 mm wafer: 300 mm across, within +/- 0.2 mm", BEAT_MS)
        .note(
            "The wafer is 300 mm across. The vendor datasheet allows a tolerance of plus or minus 0.2 mm on the diameter.",
            "a grey wafer disc face on, with a gold bar across its diameter",
        )
        .detail(
            "The diameter is the reason the grind step exists: the finished body must meet this number.",
            &[
                "300 mm, tolerance +/- 0.2 mm (vendor datasheet)",
                "300 mm wafer, +/- 0.2 mm (University Wafer 300 mm sheet)",
                "SV027 search snippet: 300 +/- 0.20 mm (SV027 PDF not parsed)",
            ],
        ),
    Beat::new("thickness: about 775 um, +/- 25 um in vendor sheets", BEAT_MS)
        .note(
            "The wafer is about 775 um thick. Vendor sheets show +/- 25 um; a drawing on the page shows +/- 20 um. The thickness here is schematic.",
            "the grey wafer face, with its thickness shown in the gold label beside it",
        )
        .detail(
            "The 775 um figure came in with the 300 mm size in 1999; the page warns the thickness relates to when each size was introduced.",
            &[
                "775 um, introduced 1999 (Wikipedia, Wafer (electronics) standards table)",
                "+/- 25 um in vendor sheets; +/- 20 um in a drawing (INGOT page)",
                "SV027 search snippet: 775 +/- 25 um (SV027 PDF not parsed)",
            ],
        ),
    Beat::new("a notch 1.0 mm deep, 90 degrees, on <110> +/- 1 degree", BEAT_MS)
        .note(
            "The notch on the rim is 1.0 mm deep, with a 90 degree included angle. Its direction is <110>, to within plus or minus 1 degree.",
            "a gold block at the top rim of the grey wafer, the notch, drawn larger than life",
        )
        .detail(
            "The notch replaces the flat. It does not show doping type.",
            &[
                "Depth 1.0 mm (+0.25 / -0.00), 90 degree included angle (vendor datasheet, SV025 snippet)",
                "<110> +/- 1 degree (vendor datasheet)",
                "SEMI M1 governs polished wafers; its PDF was not read (INGOT page)",
            ],
        ),
    Beat::new("about 125 g per wafer, and about 640 dies of 100 mm2 (ideal count)", BEAT_MS)
        .note(
            "A 300 mm wafer weighs about 125 g. Laid out on a 100 mm2 die, the ideal count is about 640 dies. The grid is illustrative.",
            "a grid of small tan die squares inside a circle, the wafer face not drawn here",
        )
        .detail(
            "The die count is an ideal figure; real yield depends on defects and the process, which this page does not quantify.",
            &[
                "About 125 g per wafer (Wikipedia, Wafer (electronics))",
                "About 640 dies of 100 mm2, ideal count (Wikipedia)",
                "The die size is from INGOT.details.txt, not the page table",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("100, 150 and 200 mm wafers: 525, 675 and 725 um thick", BEAT_MS)
        .note(
            "The size ladder shows the thickness for each diameter, from the Wikipedia standards table. Each bar is the thickness in micrometres for its size.",
            "three grey bars standing in a row, each taller than the last",
        )
        .detail(
            "The thicknesses grow with diameter, because larger wafers need more thickness to stay rigid.",
            &[
                "100 mm (1976): 525 um; 150 mm (1983): 675 um; 200 mm (1992): 725 um (Wikipedia)",
                "The table warns the thicknesses relate to when each size was introduced (INGOT page)",
                "Bar lengths are scaled to 925 um (drawn)",
            ],
        ),
    Beat::new("300 mm is the size in use: 775 um", BEAT_MS)
        .note(
            "The 300 mm bar is lit in gold: it is the size in use. Its thickness is 775 um, from the 1999 standard.",
            "the 300 mm bar lit in gold among the grey bars",
        )
        .detail(
            "The 300 mm row is the one the rest of the page works from.",
            &[
                "300 mm (1999): 775 um (Wikipedia)",
                "+/- 25 um in vendor sheets (INGOT page)",
                "SEMI M1 is listed on the page but not fetched",
            ],
        ),
    Beat::new("450 mm was proposed and never built: 925 um, drawn as an outline", BEAT_MS)
        .note(
            "The 450 mm bar is drawn as an outline, not a solid bar, because it was never built. It was proposed for 2018 and stopped in 2016.",
            "a hollow grey outline standing at the end of the row, taller than the rest",
        )
        .detail(
            "Tool makers declined the retooling cost, so the size was dropped.",
            &[
                "450 mm: 925 um, never built (Wikipedia, via INGOT page)",
                "Proposed for 2018 and stopped in 2016; tool makers declined the retooling cost (INGOT page)",
                "A 450 mm crystal would have weighed about 1 tonne (INGOT details)",
            ],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("mass per wafer: about 10, 53, 125 and 342 g", BEAT_MS)
        .note(
            "Mass grows with diameter: about 10 g for 100 mm, 53 g for 200 mm, 125 g for 300 mm and 342 g for the proposed 450 mm.",
            "four grey slabs, growing from left to right; the 300 mm slab lit in gold and the 450 mm slab drawn as an outline",
        )
        .detail(
            "The 300 mm mass is the figure the rest of the page uses.",
            &[
                "Mass per wafer, Wikipedia standards table (INGOT page)",
                "About 125 g per 300 mm wafer (Wikipedia)",
                "The 450 mm figure is for a size that was never built (INGOT page)",
            ],
        ),
    Beat::new("dies per wafer: about 56, 269, 640 and 1490, as ideal counts", BEAT_MS)
        .note(
            "Ideal dies per wafer grow the same way: 56 for 100 mm, 269 for 200 mm, 640 for 300 mm and 1490 for the proposed 450 mm.",
            "four bars of tan and grey, with the 640-die bar for 300 mm lit in gold",
        )
        .detail(
            "These are ideal counts for a 100 mm2 die; real counts depend on yield.",
            &[
                "Dies per wafer from the same table as section 5 (INGOT page)",
                "100 mm2 die size (INGOT details; ideal count, Wikipedia)",
                "The counts are ideal, before yield (INGOT page)",
            ],
        ),
    Beat::new("450 mm was proposed for 2018 and stopped in 2016", BEAT_MS)
        .note(
            "The 450 mm size is shown as a cancelled size, drawn as an outline. It was proposed for 2018 and stopped in 2016.",
            "the 450 mm bars drawn as hollow outlines at the right of each row",
        )
        .detail(
            "Tool makers declined the retooling cost, which is why the program ended.",
            &[
                "Proposed for 2018, stopped in 2016 (INGOT page)",
                "Tool makers declined the retooling cost (INGOT page)",
                "450 mm would have needed a new tool set (INGOT details)",
            ],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("Shin-Etsu at 19.9% and SUMCO at 17.2%: the two largest makers", BEAT_MS)
        .note(
            "The two largest silicon wafer makers, Shin-Etsu and SUMCO, hold 19.9% and 17.2% of the large-wafer market in 2024. The shares are a Report Prime estimate.",
            "two gold bars at the top, the longest in the chart",
        )
        .detail(
            "The shares come from a low-reliability aggregator; the ranking is stable across sources.",
            &[
                "Report Prime 2024 estimate: Shin-Etsu 19.9%, SUMCO 17.2% (INGOT page)",
                "Shin-Etsu and SUMCO are first in every source the page reads (INGOT page)",
                "Shin-Etsu + SUMCO above 55% (Omdia 2020 basis, INGOT details)",
            ],
        ),
    Beat::new("GlobalWafers at 12.9% and Siltronic at 9.9%", BEAT_MS)
        .note(
            "GlobalWafers of Taiwan holds 12.9% and Siltronic of Germany holds 9.9%, on the 2024 estimate.",
            "two grey bars below the gold ones, the third and fourth in the chart",
        )
        .detail(
            "Omdia 2020 gave different shares for the same makers, so the ranking holds but the values move.",
            &[
                "Report Prime 2024: GlobalWafers 12.9%, Siltronic 9.9% (INGOT page)",
                "Omdia 2020 via KED Global: GlobalWafers 16.7%, Siltronic 12.3% (INGOT page)",
                "Geography: Taiwan (GlobalWafers), Germany (Siltronic) (INGOT page)",
            ],
        ),
    Beat::new("SK Siltron at 8.6%", BEAT_MS)
        .note(
            "SK Siltron, of Korea, holds 8.6% on the 2024 estimate: the smallest of the five in this chart.",
            "a fifth grey bar at the bottom of the chart",
        )
        .detail(
            "SK Siltron is owned by SK Inc; the 2020 Omdia share was 10.6%.",
            &[
                "Report Prime 2024: SK Siltron 8.6% (INGOT page)",
                "Omdia 2020: SK Siltron 10.6% (INGOT page)",
                "SK Siltron is owned by SK Inc, 034730.KS (INGOT page)",
            ],
        ),
    Beat::new("the five firms together: 68.5%, with the rest of the market at 31.5%", BEAT_MS)
        .note(
            "All five bars are stacked against the whole market: the five firms hold 68.5% and the rest holds 31.5%. Those two totals are computed from the five 2024 shares; no source prints them.",
            "the five bars and a long grey band for the market, with the five-firm share shaded in",
        )
        .detail(
            "The totals are an estimate. Five firms make nearly all wafers, 82-94% depending on source and year (INGOT page).",
            &[
                "Five-firm 68.5%, rest 31.5%: computed from the 2024 shares, not printed by a source",
                "Five firms 82-94% depending on source and year (INGOT page)",
                "Shin-Etsu and SUMCO first in every source (INGOT page)",
            ],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("five firms make 82-94% of wafers, and entrants rarely win share", BEAT_MS)
        .note(
            "Five firms make nearly all wafers, 82-94% depending on source and year. Qualification takes chipmakers years, so new entrants rarely win share.",
            "a long gold bar with a grey band at its end, and five grey blocks beneath it",
        )
        .detail(
            "The concentration is the reason a single supplier fault matters to the whole chain.",
            &[
                "Five firms: 82-94% of wafers (INGOT page)",
                "Qualification takes chipmakers years (INGOT page)",
                "Shin-Etsu + SUMCO above 55% (INGOT details)",
            ],
        ),
    Beat::new("the 2023 downturn: wafer revenue -10.9%, area shipped -14.3%", BEAT_MS)
        .note(
            "SEMI says 2023 wafer revenue fell 10.9% to $12.3B, and area shipped fell 14.3%. Polished 300 mm fell 13% and epitaxial 300 mm fell 5%. The bars are schematic.",
            "four pairs of bars, each with a pale full-length bar and a shorter gold bar for the fall",
        )
        .detail(
            "The 2023 numbers are from a SEMI release quoted in a substack post; they were not re-checked against SEMI.",
            &[
                "SEMI 2023: revenue -10.9% to $12.3B; area -14.3% to 12,602 million sq in (INGOT page)",
                "Polished 300 mm -13%; epi 300 mm -5% (INGOT page)",
                "Source: SEMI release via Mark LaPedus's post (INGOT page)",
            ],
        ),
    Beat::new("the supply chain: quartz from Spruce Pine, crucible and polysilicon are the chokepoints", BEAT_MS)
        .note(
            "The upstream chokepoints are crucible quartz, from Spruce Pine, and electronic-grade polysilicon. Long-term agreements set prices, and a fixed-price customer sees no 2024 increase.",
            "stacked boxes for the crucible, the polysilicon and the pull, with the quartz block at the start of the chain",
        )
        .detail(
            "Spruce Pine is the same chokepoint the SAND page covers; LTAs are a pricing lever in a tight market.",
            &[
                "Chokepoints: crucible quartz (Spruce Pine) and electronic-grade polysilicon (INGOT page)",
                "Fixed-LTA customers see no 2024 increase; step-up LTAs may (INGOT page)",
                "Shin-Etsu says LTA prices should rise on capex and raw material costs (SEMI post)",
            ],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("Shin-Etsu 4063.T and SUMCO 3436.T: the two largest makers", BEAT_MS)
        .note(
            "The two largest makers are listed on the Tokyo exchange: Shin-Etsu Chemical as 4063.T and SUMCO as 3436.T.",
            "five cards in a row, the first two lit gold",
        )
        .detail(
            "The tickers are general knowledge, not a fetched source, and no prices are shown.",
            &[
                "Shin-Etsu Chemical 4063.T; SUMCO 3436.T (INGOT page)",
                "Tickers are general knowledge, not fetched (INGOT page)",
                "The ranking that orders the cards is from section 7",
            ],
        ),
    Beat::new("GlobalWafers 6488.TWO and Siltronic SSG.DE", BEAT_MS)
        .note(
            "GlobalWafers is listed in Taipei as 6488.TWO. Siltronic is listed as SSG.DE, as the page gives it.",
            "the third and fourth cards lit gold",
        )
        .detail(
            "Siltronic's exchange line is worth checking before use: the page gives SSG.DE.",
            &[
                "GlobalWafers 6488.TWO; Siltronic SSG.DE (INGOT page)",
                "Tickers are general knowledge, not fetched (INGOT page)",
                "Siltronic's listing as the page gives it: SSG.DE",
            ],
        ),
    Beat::new("SK Siltron is owned by SK Inc, 034730.KS; the tickers are not fetched", BEAT_MS)
        .note(
            "SK Siltron is owned by SK Inc, which is listed as 034730.KS. A red stamp marks that these tickers are general knowledge, not a fetched source.",
            "the fifth card lit gold, and a red stamp across the bottom reading general knowledge",
        )
        .detail(
            "Listed names are a starting point for lookup; the page gives no prices.",
            &[
                "SK Siltron is owned by SK Inc, 034730.KS (INGOT page)",
                "The tickers were not fetched (INGOT page)",
                "No prices are shown on this page",
            ],
        ),
];

const SOURCES: &[Beat] = &[
    Beat::new("sources [1] and [2]: Wikipedia on wafers and the Czochralski method", BEAT_MS)
        .note(
            "The first two cards are encyclopedia entries: the wafer standards table and the Czochralski method for ingot length and mass.",
            "eight cards in two rows; the first two lit gold",
        )
        .detail(
            "Wikipedia is cited for broad figures; where sources differ, the page says so.",
            &[
                "[1] Wikipedia, Wafer (electronics): standards table",
                "[2] Wikipedia, Czochralski method: ingot length and mass",
                "Where sources differ, the page says so (INGOT page)",
            ],
        ),
    Beat::new("sources [3] and [4]: a University Wafer sheet and two USPTO patents", BEAT_MS)
        .note(
            "Card [3] is the University Wafer 300 mm sheet for the diameter and notch. Card [4] covers two USPTO patents, 12617032 and 12605863, for the crop, grind, notch and saw steps.",
            "cards [3] and [4] lit gold",
        )
        .detail(
            "The patents were read as text, so their drawings are schematic in this page.",
            &[
                "[3] University Wafer: 300 mm diameter and notch (INGOT page)",
                "[4] USPTO 12617032 and 12605863: crop, grind, notch and saw steps (patent text)",
                "The patent drawings are not used; the rod is schematic",
            ],
        ),
    Beat::new("sources [5] and [6]: Report Prime's shares and Omdia 2020 via KED Global", BEAT_MS)
        .note(
            "Card [5] is the Report Prime wafer-share page, a low-reliability aggregator. Card [6] is Omdia's 2020 share data as reported by KED Global.",
            "cards [5] and [6] lit gold",
        )
        .detail(
            "These are market figures from different years (2020 and 2024); don't read them as one period.",
            &[
                "[5] Report Prime, large silicon wafers: 2024 estimate (INGOT page)",
                "[6] Omdia 2020 via KED Global (INGOT page)",
                "Low reliability: an aggregator estimate (INGOT page)",
            ],
        ),
    Beat::new("sources [7] and [8]: SEMI 2023 via a substack post, and the SEMI M1 listing", BEAT_MS)
        .note(
            "Card [7] carries the SEMI 2023 release and Shin-Etsu's LTA comment, as quoted in a substack post. Card [8] is the SEMI M1 specification, which was not fetched.",
            "cards [7] and [8] lit gold",
        )
        .detail(
            "SEMI M1 governs polished wafers; its tables were not read for this page.",
            &[
                "[7] SEMI 2023 data via a substack post (INGOT page)",
                "[8] SEMI M1 specification for polished single-crystal wafers (not fetched)",
                "Shin-Etsu LTA comment via the same post (INGOT page)",
            ],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/ingot_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order; the last is the sources.
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
    section!(10, SOURCES),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [5, 4, 4, 4, 3, 3, 4, 3, 3, 4]);
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
