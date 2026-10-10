// Visuals for pages WAFER, DEPOSIT, COAT, EXPOSE (generated from scratchpad
// data, then maintained by hand). See diagrams_vis.rs for the template.

#[allow(unused_imports)]
use super::diagrams_vis::{Spot, TO_EOL, Visual, spot};

pub fn lookup(page: &str, card: &str, section: &str) -> Option<Visual> {
    match (page, card, section) {
        ("WAFER", "POLISHED", "Prime wafer") => Some(Visual {
            art: V1.trim_start_matches('\n'),
            spots: V1S,
        }),
        ("WAFER", "POLISHED", "Why it matters") => Some(Visual {
            art: V2.trim_start_matches('\n'),
            spots: V2S,
        }),
        ("WAFER", "OPTIONAL", "Epitaxy") => Some(Visual {
            art: V3.trim_start_matches('\n'),
            spots: V3S,
        }),
        ("WAFER", "OPTIONAL", "The upgrade ladder") => Some(Visual {
            art: V4.trim_start_matches('\n'),
            spots: V4S,
        }),
        ("WAFER", "INSPECT", "What is checked") => Some(Visual {
            art: V5.trim_start_matches('\n'),
            spots: V5S,
        }),
        ("WAFER", "INSPECT", "Why flatness gets attention") => Some(Visual {
            art: V6.trim_start_matches('\n'),
            spots: V6S,
        }),
        ("WAFER", "PACK", "The FOUP") => Some(Visual {
            art: V7.trim_start_matches('\n'),
            spots: V7S,
        }),
        ("WAFER", "PACK", "Who and why purge") => Some(Visual {
            art: V8.trim_start_matches('\n'),
            spots: V8S,
        }),
        ("WAFER", "FAB", "Wafer quality is yield") => Some(Visual {
            art: V9.trim_start_matches('\n'),
            spots: V9S,
        }),
        ("WAFER", "FAB", "Market tone 2026") => Some(Visual {
            art: V10.trim_start_matches('\n'),
            spots: V10S,
        }),
        ("WAFER", "EPITAXIAL", "What epi is") => Some(Visual {
            art: V11.trim_start_matches('\n'),
            spots: V11S,
        }),
        ("WAFER", "EPITAXIAL", "Demand signal") => Some(Visual {
            art: V12.trim_start_matches('\n'),
            spots: V12S,
        }),
        ("WAFER", "SOI (silicon on insulator)", "Smart Cut steps") => Some(Visual {
            art: V13.trim_start_matches('\n'),
            spots: V13S,
        }),
        ("WAFER", "SOI (silicon on insulator)", "What you get") => Some(Visual {
            art: V14.trim_start_matches('\n'),
            spots: V14S,
        }),
        ("WAFER", "TTV", "Definition and spec") => Some(Visual {
            art: V15.trim_start_matches('\n'),
            spots: V15S,
        }),
        ("WAFER", "TTV", "Commodity vs leading edge") => Some(Visual {
            art: V16.trim_start_matches('\n'),
            spots: V16S,
        }),
        ("WAFER", "SFQR", "What it measures") => Some(Visual {
            art: V17.trim_start_matches('\n'),
            spots: V17S,
        }),
        ("WAFER", "SFQR", "The catch") => Some(Visual {
            art: V18.trim_start_matches('\n'),
            spots: V18S,
        }),
        ("WAFER", "Shin-Etsu", "Position") => Some(Visual {
            art: V19.trim_start_matches('\n'),
            spots: V19S,
        }),
        ("WAFER", "Shin-Etsu", "2026 commentary") => Some(Visual {
            art: V20.trim_start_matches('\n'),
            spots: V20S,
        }),
        ("WAFER", "2025 revenue", "Area up, revenue down") => Some(Visual {
            art: V21.trim_start_matches('\n'),
            spots: V21S,
        }),
        ("WAFER", "2025 revenue", "Why price per area fell") => Some(Visual {
            art: V22.trim_start_matches('\n'),
            spots: V22S,
        }),
        ("WAFER", "long qualification", "Why switching is slow") => Some(Visual {
            art: V23.trim_start_matches('\n'),
            spots: V23S,
        }),
        ("WAFER", "long qualification", "Supply picture") => Some(Visual {
            art: V24.trim_start_matches('\n'),
            spots: V24S,
        }),
        ("WAFER", "SUMCO", "Position") => Some(Visual {
            art: V25.trim_start_matches('\n'),
            spots: V25S,
        }),
        ("WAFER", "SUMCO", "Concentration risk") => Some(Visual {
            art: V26.trim_start_matches('\n'),
            spots: V26S,
        }),
        ("DEPOSIT", "GAS / TARGET", "Three kinds of source") => Some(Visual {
            art: V27.trim_start_matches('\n'),
            spots: V27S,
        }),
        ("DEPOSIT", "GAS / TARGET", "Precursors as a chokepoint") => Some(Visual {
            art: V28.trim_start_matches('\n'),
            spots: V28S,
        }),
        ("DEPOSIT", "CHAMBER", "Process windows") => Some(Visual {
            art: V29.trim_start_matches('\n'),
            spots: V29S,
        }),
        ("DEPOSIT", "CHAMBER", "Batch vs single wafer") => Some(Visual {
            art: V30.trim_start_matches('\n'),
            spots: V30S,
        }),
        ("DEPOSIT", "FILM", "How films are judged") => Some(Visual {
            art: V31.trim_start_matches('\n'),
            spots: V31S,
        }),
        ("DEPOSIT", "FILM", "Conformality is the AI-era requirement") => Some(Visual {
            art: V32.trim_start_matches('\n'),
            spots: V32S,
        }),
        ("DEPOSIT", "PUMP", "By-products out") => Some(Visual {
            art: V33.trim_start_matches('\n'),
            spots: V33S,
        }),
        ("DEPOSIT", "PUMP", "Where service revenue comes from") => Some(Visual {
            art: V34.trim_start_matches('\n'),
            spots: V34S,
        }),
        ("DEPOSIT", "CMP/ETCH", "The repeat loop") => Some(Visual {
            art: V35.trim_start_matches('\n'),
            spots: V35S,
        }),
        ("DEPOSIT", "CMP/ETCH", "Copper side") => Some(Visual {
            art: V36.trim_start_matches('\n'),
            spots: V36S,
        }),
        ("DEPOSIT", "SHOWERHEAD", "Spreading the gas") => Some(Visual {
            art: V37.trim_start_matches('\n'),
            spots: V37S,
        }),
        ("DEPOSIT", "SHOWERHEAD", "Who") => Some(Visual {
            art: V38.trim_start_matches('\n'),
            spots: V38S,
        }),
        ("DEPOSIT", "HEATED PEDESTAL", "Temperature sets rate") => Some(Visual {
            art: V39.trim_start_matches('\n'),
            spots: V39S,
        }),
        ("DEPOSIT", "HEATED PEDESTAL", "Failure mode") => Some(Visual {
            art: V40.trim_start_matches('\n'),
            spots: V40S,
        }),
        ("DEPOSIT", "1 PULSE A", "The ALD cycle") => Some(Visual {
            art: V41.trim_start_matches('\n'),
            spots: V41S,
        }),
        ("DEPOSIT", "1 PULSE A", "Cycle numbers") => Some(Visual {
            art: V42.trim_start_matches('\n'),
            spots: V42S,
        }),
        ("DEPOSIT", "1 PULSE A", "Business") => Some(Visual {
            art: V43.trim_start_matches('\n'),
            spots: V43S,
        }),
        ("DEPOSIT", "TARGET (Ta, Ti, Cu)", "Sputtering") => Some(Visual {
            art: V44.trim_start_matches('\n'),
            spots: V44S,
        }),
        ("DEPOSIT", "TARGET (Ta, Ti, Cu)", "Where it is used") => Some(Visual {
            art: V45.trim_start_matches('\n'),
            spots: V45S,
        }),
        ("DEPOSIT", "TEOS SiO2", "The reaction") => Some(Visual {
            art: V46.trim_start_matches('\n'),
            spots: V46S,
        }),
        ("DEPOSIT", "TEOS SiO2", "Speed vs density") => Some(Visual {
            art: V47.trim_start_matches('\n'),
            spots: V47S,
        }),
        ("DEPOSIT", "Tungsten fill", "Reaction and sequence") => Some(Visual {
            art: V48.trim_start_matches('\n'),
            spots: V48S,
        }),
        ("DEPOSIT", "Tungsten fill", "What replaces it") => Some(Visual {
            art: V49.trim_start_matches('\n'),
            spots: V49S,
        }),
        ("DEPOSIT", "ASM International", "FY2025") => Some(Visual {
            art: V50.trim_start_matches('\n'),
            spots: V50S,
        }),
        ("DEPOSIT", "ASM International", "Mix and risks") => Some(Visual {
            art: V51.trim_start_matches('\n'),
            spots: V51S,
        }),
        ("DEPOSIT", "Mo ALD", "Why swap metals") => Some(Visual {
            art: V52.trim_start_matches('\n'),
            spots: V52S,
        }),
        ("DEPOSIT", "Mo ALD", "Hurdle") => Some(Visual {
            art: V53.trim_start_matches('\n'),
            spots: V53S,
        }),
        ("DEPOSIT", "Applied Materials", "FY2025 segment") => Some(Visual {
            art: V54.trim_start_matches('\n'),
            spots: V54S,
        }),
        ("DEPOSIT", "Applied Materials", "Products and share") => Some(Visual {
            art: V55.trim_start_matches('\n'),
            spots: V55S,
        }),
        ("DEPOSIT", "Kokusai Electric", "Position") => Some(Visual {
            art: V56.trim_start_matches('\n'),
            spots: V56S,
        }),
        ("DEPOSIT", "Kokusai Electric", "Recent numbers") => Some(Visual {
            art: V57.trim_start_matches('\n'),
            spots: V57S,
        }),
        ("COAT", "PRIME+BARC", "Primer and BARC") => Some(Visual {
            art: V58.trim_start_matches('\n'),
            spots: V58S,
        }),
        ("COAT", "PRIME+BARC", "Thin-film pressure") => Some(Visual {
            art: V59.trim_start_matches('\n'),
            spots: V59S,
        }),
        ("COAT", "DISPENSE", "Dispense") => Some(Visual {
            art: V60.trim_start_matches('\n'),
            spots: V60S,
        }),
        ("COAT", "DISPENSE", "Defects and dry resist") => Some(Visual {
            art: V61.trim_start_matches('\n'),
            spots: V61S,
        }),
        ("COAT", "SPIN", "Spin physics") => Some(Visual {
            art: V62.trim_start_matches('\n'),
            spots: V62S,
        }),
        ("COAT", "SPIN", "Recipe numbers") => Some(Visual {
            art: V63.trim_start_matches('\n'),
            spots: V63S,
        }),
        ("COAT", "EDGE BEAD", "Why the rim piles up") => Some(Visual {
            art: V64.trim_start_matches('\n'),
            spots: V64S,
        }),
        ("COAT", "EDGE BEAD", "Scale") => Some(Visual {
            art: V65.trim_start_matches('\n'),
            spots: V65S,
        }),
        ("COAT", "SOFT BAKE", "What the bake does") => Some(Visual {
            art: V66.trim_start_matches('\n'),
            spots: V66S,
        }),
        ("COAT", "SOFT BAKE", "Why the temperature is bounded") => Some(Visual {
            art: V67.trim_start_matches('\n'),
            spots: V67S,
        }),
        ("COAT", "COOL", "Chill plate") => Some(Visual {
            art: V68.trim_start_matches('\n'),
            spots: V68S,
        }),
        ("COAT", "COOL", "Track keeps pace") => Some(Visual {
            art: V69.trim_start_matches('\n'),
            spots: V69S,
        }),
        ("COAT", "NOZZLE", "Dispense control") => Some(Visual {
            art: V70.trim_start_matches('\n'),
            spots: V70S,
        }),
        ("COAT", "NOZZLE", "Direction of travel") => Some(Visual {
            art: V71.trim_start_matches('\n'),
            spots: V71S,
        }),
        ("COAT", "CHUCK", "Vacuum chuck") => Some(Visual {
            art: V72.trim_start_matches('\n'),
            spots: V72S,
        }),
        ("COAT", "CHUCK", "Link to wafer specs") => Some(Visual {
            art: V73.trim_start_matches('\n'),
            spots: V73S,
        }),
        ("COAT", "EBR nozzle", "Rim-only solvent") => Some(Visual {
            art: V74.trim_start_matches('\n'),
            spots: V74S,
        }),
        ("COAT", "EBR nozzle", "Cost of getting it wrong") => Some(Visual {
            art: V75.trim_start_matches('\n'),
            spots: V75S,
        }),
        ("COAT", "PGMEA", "What is in resist") => Some(Visual {
            art: V76.trim_start_matches('\n'),
            spots: V76S,
        }),
        ("COAT", "PGMEA", "Chemical amplification") => Some(Visual {
            art: V77.trim_start_matches('\n'),
            spots: V77S,
        }),
        ("COAT", "EUV film", "Thin film, few photons") => Some(Visual {
            art: V78.trim_start_matches('\n'),
            spots: V78S,
        }),
        ("COAT", "EUV film", "Industry response") => Some(Visual {
            art: V79.trim_start_matches('\n'),
            spots: V79S,
        }),
        ("COAT", "Tokyo Electron", "Position") => Some(Visual {
            art: V80.trim_start_matches('\n'),
            spots: V80S,
        }),
        ("COAT", "Tokyo Electron", "Why it matters") => Some(Visual {
            art: V81.trim_start_matches('\n'),
            spots: V81S,
        }),
        ("COAT", "SCREEN Holdings", "Number two") => Some(Visual {
            art: V82.trim_start_matches('\n'),
            spots: V82S,
        }),
        ("COAT", "SCREEN Holdings", "Risk") => Some(Visual {
            art: V83.trim_start_matches('\n'),
            spots: V83S,
        }),
        ("COAT", "striations / comets", "What they are") => Some(Visual {
            art: V84.trim_start_matches('\n'),
            spots: V84S,
        }),
        ("COAT", "striations / comets", "Impact and fixes") => Some(Visual {
            art: V85.trim_start_matches('\n'),
            spots: V85S,
        }),
        ("COAT", "thickness drift", "Why thickness moves") => Some(Visual {
            art: V86.trim_start_matches('\n'),
            spots: V86S,
        }),
        ("COAT", "thickness drift", "Scale") => Some(Visual {
            art: V87.trim_start_matches('\n'),
            spots: V87S,
        }),
        ("EXPOSE", "TIN DROPLET", "Why tin") => Some(Visual {
            art: V88.trim_start_matches('\n'),
            spots: V88S,
        }),
        ("EXPOSE", "TIN DROPLET", "Droplets and debris") => Some(Visual {
            art: V89.trim_start_matches('\n'),
            spots: V89S,
        }),
        ("EXPOSE", "2 LASER SHOTS", "Why two pulses") => Some(Visual {
            art: V90.trim_start_matches('\n'),
            spots: V90S,
        }),
        ("EXPOSE", "2 LASER SHOTS", "Efficiency and alternatives") => Some(Visual {
            art: V91.trim_start_matches('\n'),
            spots: V91S,
        }),
        ("EXPOSE", "PLASMA", "The 13.5 nm emitter") => Some(Visual {
            art: V92.trim_start_matches('\n'),
            spots: V92S,
        }),
        ("EXPOSE", "PLASMA", "Source power") => Some(Visual {
            art: V93.trim_start_matches('\n'),
            spots: V93S,
        }),
        ("EXPOSE", "COLLECTOR", "A consumable mirror") => Some(Visual {
            art: V94.trim_start_matches('\n'),
            spots: V94S,
        }),
        ("EXPOSE", "COLLECTOR", "Wear and cleaning") => Some(Visual {
            art: V95.trim_start_matches('\n'),
            spots: V95S,
        }),
        ("EXPOSE", "INTERMEDIATE FOCUS", "Handoff between source and scanner") => Some(Visual {
            art: V96.trim_start_matches('\n'),
            spots: V96S,
        }),
        ("EXPOSE", "INTERMEDIATE FOCUS", "A pinch point") => Some(Visual {
            art: V97.trim_start_matches('\n'),
            spots: V97S,
        }),
        ("EXPOSE", "ILLUMINATOR", "Shaping the beam") => Some(Visual {
            art: V98.trim_start_matches('\n'),
            spots: V98S,
        }),
        ("EXPOSE", "ILLUMINATOR", "Light budget") => Some(Visual {
            art: V99.trim_start_matches('\n'),
            spots: V99S,
        }),
        ("EXPOSE", "RETICLE + MIRRORS", "A reflective mask") => Some(Visual {
            art: V100.trim_start_matches('\n'),
            spots: V100S,
        }),
        ("EXPOSE", "RETICLE + MIRRORS", "Inspection and vendors") => Some(Visual {
            art: V101.trim_start_matches('\n'),
            spots: V101S,
        }),
        ("EXPOSE", "Pellicle", "Dust cover that must be transparent") => Some(Visual {
            art: V102.trim_start_matches('\n'),
            spots: V102S,
        }),
        ("EXPOSE", "Pellicle", "Carbon nanotubes next") => Some(Visual {
            art: V103.trim_start_matches('\n'),
            spots: V103S,
        }),
        ("EXPOSE", "PROJECTION OPTICS", "Six mirrors, no lenses") => Some(Visual {
            art: V104.trim_start_matches('\n'),
            spots: V104S,
        }),
        ("EXPOSE", "PROJECTION OPTICS", "High-NA optics") => Some(Visual {
            art: V105.trim_start_matches('\n'),
            spots: V105S,
        }),
        ("EXPOSE", "WAFER on stage", "Where the photons are counted") => Some(Visual {
            art: V106.trim_start_matches('\n'),
            spots: V106S,
        }),
        ("EXPOSE", "WAFER on stage", "Stochastics and overlay") => Some(Visual {
            art: V107.trim_start_matches('\n'),
            spots: V107S,
        }),
        ("EXPOSE", "Rayleigh resolution", "The equations") => Some(Visual {
            art: V108.trim_start_matches('\n'),
            spots: V108S,
        }),
        ("EXPOSE", "Rayleigh resolution", "The price of NA") => Some(Visual {
            art: V109.trim_start_matches('\n'),
            spots: V109S,
        }),
        ("EXPOSE", "91.8 eV", "Photon arithmetic") => Some(Visual {
            art: V110.trim_start_matches('\n'),
            spots: V110S,
        }),
        ("EXPOSE", "91.8 eV", "Sensitivity vs defects") => Some(Visual {
            art: V111.trim_start_matches('\n'),
            spots: V111S,
        }),
        ("EXPOSE", "NXE:3800E", "Specs") => Some(Visual {
            art: V112.trim_start_matches('\n'),
            spots: V112S,
        }),
        ("EXPOSE", "NXE:3800E", "Cost and power") => Some(Visual {
            art: V113.trim_start_matches('\n'),
            spots: V113S,
        }),
        ("EXPOSE", "EXE:5000", "High-NA: first generation") => Some(Visual {
            art: V114.trim_start_matches('\n'),
            spots: V114S,
        }),
        ("EXPOSE", "EXE:5000", "Adoption and doubt") => Some(Visual {
            art: V115.trim_start_matches('\n'),
            spots: V115S,
        }),
        ("EXPOSE", "ASML 2025", "Scale of the franchise") => Some(Visual {
            art: V116.trim_start_matches('\n'),
            spots: V116S,
        }),
        ("EXPOSE", "ASML 2025", "Reading the numbers") => Some(Visual {
            art: V117.trim_start_matches('\n'),
            spots: V117S,
        }),
        ("EXPOSE", "Chokepoints", "Single points of failure") => Some(Visual {
            art: V118.trim_start_matches('\n'),
            spots: V118S,
        }),
        ("EXPOSE", "Chokepoints", "Tickers and risks") => Some(Visual {
            art: V119.trim_start_matches('\n'),
            spots: V119S,
        }),
        _ => None,
    }
}

const V1: &str = r##"
# Bulk polished wafer, side view

  mirror-polished top face (devices go here)
┌──────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│ ▓▓▓▓ single-crystal silicon, 775 um ▓▓▓▓     │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
└──────────────────────────────────────────────┘
  300 mm across, 775 um +/- 25 um thick
  (TTV 5 um or less, 3.0 mm edge exclusion)
"##;
const V1S: &[Spot] = &[
    spot(
        "mirror-polished top face",
        0,
        0,
        "Only the top face is polished to a mirror; every later film, resist coat and exposure starts from this surface.",
    ),
    spot(
        "single-crystal silicon, 775 um",
        0,
        0,
        "Sliced from a single-crystal ingot, then lapped, etched and polished. Typical 300 mm product is 775 um thick.",
    ),
    spot(
        "775 um +/- 25 um thick",
        0,
        0,
        "Thickness spec on the vendor 300 mm sheets (SVMI SV029 / SV031): 775 +/- 25 um.",
    ),
    spot(
        "TTV 5 um or less",
        0,
        0,
        "Total thickness variation, max minus min across the wafer. 5 um or less on the commodity 300 mm sheets; tighter for leading edge.",
    ),
    spot(
        "3.0 mm edge exclusion",
        0,
        0,
        "The outer 3.0 mm is excluded from the flatness spec on these sheets, so the edge is already a marginal zone.",
    ),
];

const V2: &str = r##"
# Shipments, million square inches (SEMI)

  2025          ██████████████████████ 12,973 (+5.8%)
  2028 forecast ██████████████████████████ 15,485 (record)

  revenue 2025: $11.4B, down 1.2%
  (area up, revenue down: price per sq in fell)
"##;
const V2S: &[Spot] = &[
    spot(
        "12,973",
        0,
        0,
        "SEMI: 2025 shipments of 12,973 MSI, up 5.8%.",
    ),
    spot(
        "15,485",
        0,
        0,
        "SEMI's Oct 2025 forecast: a record 15,485 MSI by 2028. Supply side is expected to keep expanding.",
    ),
    spot(
        "revenue 2025: $11.4B, down 1.2%",
        0,
        0,
        "SEMI: revenue fell 1.2% to $11.4 billion even as area rose 5.8%.",
    ),
    spot(
        "(area up, revenue down: price per sq in fell)",
        0,
        0,
        "About $0.88 per sq in on the page's arithmetic ($11.4B / 12,973 MSI, all diameters mixed).",
    ),
];

const V3: &str = r##"
# Epi on a polished wafer

  SiHCl3 + H2 gas in, ~1100-1130 C
       ↓   ↓   ↓   ↓
┌────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░ epi layer, ~3-6 um ░░░░░░░        │
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│ ▓▓▓▓▓ polished substrate ▓▓▓▓▓▓        │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
└────────────────────────────────────────┘
  (layer can differ in doping and purity)
"##;
const V3S: &[Spot] = &[
    spot(
        "SiHCl3 + H2 gas in, ~1100-1130 C",
        0,
        0,
        "Trichlorosilane is the source gas for 300 mm epi, with 1100 to 1130 C as the growth region in current production (patent).",
    ),
    spot(
        "epi layer, ~3-6 um",
        0,
        0,
        "Patent examples grow about 3 um at 1100 C; one patent prefers 1 to 15 um and more preferably 1 to 7 um. Treat as examples, not a standard.",
    ),
    spot(
        "polished substrate",
        0,
        0,
        "The bulk wafer underneath. The epi layer is grown on its polished face.",
    ),
    spot(
        "(layer can differ in doping and purity)",
        0,
        0,
        "The epi layer can differ in doping and purity from the substrate, giving fewer crystal defects and better-controlled electrical properties where transistors sit.",
    ),
];

const V4: &str = r##"
# Variant ladder: more steps, fewer suppliers

  ┌────────────┐   ┌────────────────┐   ┌─────────────────┐
  │ BULK       │   │ EPI            │   │ SOI             │
  │ polished   │──▶│ + device layer │──▶│ + buried oxide, │
  └────────────┘   └────────────────┘   │ bonded          │
                                        └─────────────────┘

  price per wafer and supplier scarcity rise left to right
  (SOI name in the share table: Soitec, 5.5% about 2021)
"##;
const V4S: &[Spot] = &[
    spot(
        "BULK",
        0,
        0,
        "Bulk polished wafer: the commodity baseline, many qualified suppliers.",
    ),
    spot(
        "EPI",
        0,
        0,
        "Adds a device-quality layer grown by CVD. SEMI notes strong 2025 demand for advanced epi in logic.",
    ),
    spot(
        "SOI",
        0,
        0,
        "Adds a buried oxide, made by bonding (Smart Cut). Fewest qualified suppliers.",
    ),
    spot(
        "(SOI name in the share table: Soitec, 5.5% about 2021)",
        0,
        0,
        "Share figure from the 2021 Semiconductor Engineering article cited on the page.",
    ),
];

const V5: &str = r##"
# Three flatness numbers, from coarse to fine

  TTV   ████████████████████████  whole wafer, max - min
  SFQR  █████                     one scanner-field-sized site
  nano  ██                        short-wavelength surface height

  particles: counted by laser scanning of the surface
  (limits set per node and per customer)
"##;
const V5S: &[Spot] = &[
    spot(
        "TTV   ████",
        0,
        0,
        "Total thickness variation: thickest minus thinnest point across the whole wafer. 5 um or less on commodity 300 mm sheets.",
    ),
    spot(
        "whole wafer, max - min",
        0,
        0,
        "The coarse number. One patent notes wafer shape runs from a few to a few hundred um, while TTV is tens to hundreds of nm on good product.",
    ),
    spot(
        "one scanner-field-sized site",
        0,
        0,
        "SFQR: topography range inside one scanner-field-sized site. It maps most directly to lithography focus.",
    ),
    spot(
        "short-wavelength surface height",
        0,
        0,
        "Nanotopography, reported per SEMI M43, a separate guide from M1.",
    ),
    spot(
        "particles: counted by laser scanning",
        0,
        0,
        "Surface particles are counted by laser scattering (textbook).",
    ),
];

const V6: &str = r##"
# Rated flat is not always flat in the scanner

  SFQR assumes            scanner chuck is real
  an ideal plane          and the wafer follows it
  ──────────────          ╭──╮    ╭──╮
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓         ▓▓╯▓▓▓▓▓▓╯▓▓▓

  result: focus budget exceeded, CD variation rises
  vendor guidance: TTV < 1 um, site flatness < 0.1 um (10 nm nodes)
"##;
const V6S: &[Spot] = &[
    spot(
        "SFQR assumes",
        0,
        0,
        "SFQR is computed from the thickness distribution as if chucked on an ideal plane (patents).",
    ),
    spot(
        "scanner chuck is real",
        0,
        0,
        "The scanner holds the wafer on its own chuck, so the shape it sees differs from the ideal-plane model.",
    ),
    spot(
        "result: focus budget exceeded, CD variation rises",
        0,
        0,
        "A wafer flat by SFQR can underperform in the scanner and raise critical-dimension variation. This motivates measuring flatness in a chucked state.",
    ),
    spot(
        "vendor guidance: TTV < 1 um, site flatness < 0.1 um (10 nm nodes)",
        0,
        0,
        "Quoted by University Wafer as vendor guidance, not a standard.",
    ),
];

const V7: &str = r##"
# FOUP, side view

  ┌───────────────────────┐
  │ ═══════════ wafer 25  │
  │ ═══════════ wafer 24  │
  │      ...   10 mm pitch│
  │ ═══════════ wafer 2   │
  │ ═══════════ wafer 1   │
  └───────┬───────────────┘
   front-opening door      (robot docks here)
"##;
const V7S: &[Spot] = &[
    spot(
        "┌───────",
        0,
        0,
        "Sealed carrier: wafers travel between tools without exposure to the cleanroom air.",
    ),
    spot("wafer 25", 0, 0, "A standard 300 mm FOUP has 25 slots."),
    spot(
        "10 mm pitch",
        0,
        0,
        "Slot pitch for 300 mm FOUPs is 10 mm (Wikipedia; patent notes SEMI sets it). 13-slot versions can use wider pitch.",
    ),
    spot(
        "front-opening door",
        0,
        0,
        "The door faces the tool's load port; the pod replaced SMIF pods in the mid-1990s.",
    ),
];

const V8: &str = r##"
# Purging a FOUP between steps

  inert gas in ──▶ ┌───────────────┐ ──▶ gas out
                   │  wafers       │
                   │  (dry, clean) │
                   └───────────────┘

  Entegris: A300 25-slot / 13-slot (bonded, thin wafers)
           Spectra: purge + hydrophobic materials
"##;
const V8S: &[Spot] = &[
    spot(
        "inert gas in",
        0,
        0,
        "Spectra FOUPs add inert gas purge to control moisture and volatile organics inside the carrier (Entegris datasheet).",
    ),
    spot(
        "(dry, clean)",
        0,
        0,
        "The carrier is part of the contamination budget, not just packaging: moisture and airborne molecular contamination can corrupt a wafer between steps.",
    ),
    spot(
        "A300 25-slot / 13-slot",
        0,
        0,
        "Entegris A300: 25-slot for standard wafers, 13-slot for bonded and thin wafers.",
    ),
    spot(
        "Spectra: purge + hydrophobic materials",
        0,
        0,
        "Entegris Spectra line, with inert gas purge and hydrophobic materials.",
    ),
];

const V9: &str = r##"
# A defect in the wafer rides through every layer

   ▲   ▲   defect shows up in every film above it
  ┌─────────────────────────────┐
  │ ETCH / CMP    (repeat)      │
  │ EXPOSE + DEVELOP            │
  │ COAT                        │
  │ DEPOSIT                     │
  │▓▓▓ WAFER: flat reference ▓▓▓│
  └─────────────────────────────┘
"##;
const V9S: &[Spot] = &[
    spot(
        "defect shows up in every film above it",
        0,
        0,
        "Defects, warp or particles arriving with the wafer travel through hundreds of steps and are rarely recoverable.",
    ),
    spot(
        "EXPOSE + DEVELOP",
        0,
        0,
        "Flatness feeds the scanner's focus budget, so SFQR is a lithography number as much as a wafer one.",
    ),
    spot(
        "DEPOSIT",
        0,
        0,
        "Every deposition step builds on the wafer's flat top face.",
    ),
    spot(
        "WAFER: flat reference",
        0,
        0,
        "Wafers are bought, not made, by almost every chipmaker.",
    ),
];

const V10: &str = r##"
# 12-inch utilization, UBS projection

  2026  ██████████████████████████████████ 84%
  2028  ████████████████████████████████████████ 99%

  GlobalWafers (4 Aug 2026): existing 300 mm capacity fully utilized
  Shin-Etsu (24 Jul 2026): 300 mm growth mid-single digit, record June
  (broker and company commentary, not audited data)
"##;
const V10S: &[Spot] = &[
    spot(
        "84%",
        0,
        0,
        "UBS (Sept 18, 2026): 12-inch utilization 84% in 2026. Broker view.",
    ),
    spot(
        "99%",
        0,
        0,
        "UBS projects 99% by 2028 and says new capacity would need price rises of roughly 40% to 50% or more, otherwise a severe shortage could follow after 2028.",
    ),
    spot(
        "GlobalWafers (4 Aug 2026)",
        0,
        TO_EOL,
        "Said on its Aug 4, 2026 Q2 call that existing 300 mm capacity, excluding new lines, is fully utilized.",
    ),
    spot(
        "Shin-Etsu (24 Jul 2026)",
        0,
        TO_EOL,
        "Said on its July 24 call that 300 mm growth was mid-single digit year on year, with a record June shipment month.",
    ),
];

const V11: &str = r##"
# Where the transistors sit

┌──────────────────────────────────────────────┐
│ ░░░ EPI: grown from gas, chosen doping ░░░   │
│       few crystal defects, ~3-6 um           │
└──────────────────────────────────────────────┘
┌──────────────────────────────────────────────┐
│ ▓▓▓ SUBSTRATE: the bulk polished wafer ▓▓▓   │
└──────────────────────────────────────────────┘

  CVD at ~1100-1130 C from trichlorosilane (300 mm, patents)
"##;
const V11S: &[Spot] = &[
    spot(
        "EPI: grown from gas, chosen doping",
        0,
        0,
        "The epi layer's doping is set by the grower, independent of the substrate.",
    ),
    spot(
        "few crystal defects, ~3-6 um",
        0,
        0,
        "Fewer crystal defects where transistors sit. Patent examples: 1 to 10 um, about 3 to 6 um typical.",
    ),
    spot(
        "SUBSTRATE: the bulk polished wafer",
        0,
        0,
        "The polished wafer the layer is grown on.",
    ),
    spot(
        "CVD at ~1100-1130 C from trichlorosilane",
        0,
        TO_EOL,
        "Per a patent on current 300 mm epi production: trichlorosilane source gas, 1100 to 1130 C growth region.",
    ),
];

const V12: &str = r##"
# 300 mm epitaxial wafers, 2H 2020

  two Japanese makers  ████████████████████████████████ >60%
  everyone else        ████████████████████ <40%

  2025: demand strong at sub-3nm logic, lumpy quarter to quarter
"##;
const V12S: &[Spot] = &[
    spot(
        "two Japanese makers",
        0,
        TO_EOL,
        "More than 60% of 300 mm epitaxial wafers in 2H 2020 (SEMI via Semiconductor Engineering).",
    ),
    spot("everyone else", 0, TO_EOL, "The remainder, under 40%."),
    spot(
        "2025: demand strong at sub-3nm logic",
        0,
        TO_EOL,
        "SEMI's 2025 review singles out advanced epi for sub-3nm logic; Q3 2025 data showed sequential softness.",
    ),
];

const V13: &str = r##"
# Smart Cut

  ┌────────────────────┐
  │ 1 DONOR + OXIDE    │
  │ hydrogen implant   │
  │ (weak layer)       │
  └────────────────────┘
              │
              ▼
  ┌────────────────────┐
  │ 2 BOND to handle   │
  │ wafer              │
  └────────────────────┘
              │ anneal ~400-600 C
              ▼
  ┌────────────────────────┐
  │ 3 SPLIT at the H layer │
  │ + CMP polish film      │
  └────────────────────────┘
     donor wafer goes back to step 1
"##;
const V13S: &[Spot] = &[
    spot(
        "1 DONOR + OXIDE",
        0,
        0,
        "Oxide grown on the donor becomes the buried oxide (BOX) of the finished wafer.",
    ),
    spot(
        "hydrogen implant",
        0,
        0,
        "A patent example: 50 to 150 keV, dose 2e16 to 1e17 ions/cm2, hydrogen-rich layer about 0.5 to 1 um below the surface.",
    ),
    spot(
        "2 BOND to handle",
        0,
        0,
        "The donor is bonded face-down onto a handle wafer.",
    ),
    spot(
        "anneal ~400-600 C",
        0,
        TO_EOL,
        "Papers describe annealing at about 400 to 600 C to coalesce hydrogen cavities and split the wafer; one saw splitting only with a slow ramp to about 500 C.",
    ),
    spot(
        "3 SPLIT at the H layer",
        0,
        0,
        "The film separates at the hydrogen layer; CMP then polishes the transferred film.",
    ),
    spot(
        "donor wafer goes back to step 1",
        0,
        0,
        "Donor reuse is a cited advantage of the process.",
    ),
];

const V14: &str = r##"
# SOI cross-section

  thin top Si device layer (set by implant depth)
┌────────────────────────────────────────┐
│ Si device layer                        │
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│ ═══ buried oxide (BOX) ═══             │
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│ ▓▓▓▓▓ handle wafer ▓▓▓▓▓               │
└────────────────────────────────────────┘

  Soitec share about 2021: █████ 5.5%
"##;
const V14S: &[Spot] = &[
    spot(
        "thin top Si device layer",
        0,
        TO_EOL,
        "Top-layer thickness is controlled through implant parameters (patent, Electronic Design overview).",
    ),
    spot(
        "buried oxide (BOX)",
        0,
        0,
        "Insulating oxide layer; it comes from the oxide grown on the donor.",
    ),
    spot("handle wafer", 0, 0, "Carries the stack mechanically."),
    spot(
        "Soitec share about 2021",
        0,
        TO_EOL,
        "5.5% in the 2021 Semiconductor Engineering table cited on the page.",
    ),
];

const V15: &str = r##"
# TTV, exaggerated side view

  thickest point ──▶ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁   TTV = max - min
  thinnest point ──▶ ▁                  (5 um or less)

  spec on the vendor sheet:
    thickness 775 +/- 25 um    edge exclusion 3.0 mm
"##;
const V15S: &[Spot] = &[
    spot(
        "thickest point",
        0,
        0,
        "TTV is the thickest point minus the thinnest point across the wafer.",
    ),
    spot("thinnest point", 0, 0, "The other end of the range."),
    spot(
        "(5 um or less)",
        0,
        0,
        "TTV spec on the SVMI 300 mm p-type Cz datasheets (SV029 / SV031).",
    ),
    spot(
        "thickness 775 +/- 25 um",
        0,
        TO_EOL,
        "Vendor-sheet thickness for 300 mm. 3.0 mm edge exclusion applies.",
    ),
];

const V16: &str = r##"
# TTV limit, um

  commodity  ████████████████████ 5 um or less (vendor sheet)
  10 nm nodes████ < 1 um (vendor guidance)

  tighter = more polishing + metrology, lower wafer-maker yield
"##;
const V16S: &[Spot] = &[
    spot(
        "commodity",
        0,
        TO_EOL,
        "5 um or less on the SVMI 300 mm datasheets.",
    ),
    spot(
        "10 nm nodes",
        0,
        TO_EOL,
        "Under 1 um at 10 nm nodes and beyond, per vendor guidance quoted by University Wafer (not a standard).",
    ),
    spot(
        "tighter = more polishing",
        0,
        TO_EOL,
        "A tighter TTV and SFQR costs the wafer maker yield, which helps explain the price premium.",
    ),
];

const V17: &str = r##"
# The wafer divided into scanner-sized sites

        ┌──┬──┬──┬──┐
     ┌──┼──┼──┼──┼──┼──┐
     │  │  │▓▓│  │  │  │
     └──┼──┼──┼──┼──┼──┘
        └──┴──┴──┴──┘

  ▓▓ one site: SFQR = topography range in that site
  (ESFQR: same, on the edge sites)
"##;
const V17S: &[Spot] = &[
    spot(
        "▓▓ one site",
        0,
        0,
        "SFQR is evaluated per site, each about the size of a scanner exposure field, against a best-fit focal plane.",
    ),
    spot(
        "SFQR = topography range in that site",
        0,
        0,
        "Range of topography within the site. Maps most directly to lithography focus.",
    ),
    spot(
        "(ESFQR: same, on the edge sites)",
        0,
        0,
        "Flatness must hold on partial edge sites too, with tiny edge exclusion.",
    ),
];

const V18: &str = r##"
# Computed flat vs scanner-flat

  ideal-plane SFQR:   ──────────────  passes
  on the real chuck:  ╭─╮  ╭──╮  ╭─╮  may fail focus

  motivation: measure flatness in a chucked state
  (no current EUV focus-budget figure found)
"##;
const V18S: &[Spot] = &[
    spot(
        "ideal-plane SFQR",
        0,
        TO_EOL,
        "Computed from the thickness distribution as if the wafer were perfectly chucked.",
    ),
    spot(
        "on the real chuck",
        0,
        TO_EOL,
        "A real scanner holds the wafer on its own chuck, so the focus budget can be exceeded and CD variation rises.",
    ),
    spot(
        "measure flatness in a chucked state",
        0,
        0,
        "The patents' proposed remedy.",
    ),
    spot(
        "(no current EUV focus-budget figure found)",
        0,
        0,
        "The sources found did not give one; do not assume a number.",
    ),
];

const V19: &str = r##"
# Wafer share by supplier, about 2021 (%)

  Shin-Etsu    █████████████████████████████ 29.4
  SUMCO        ██████████████████████ 21.9
  GlobalWafers ███████████████ 15.2
  Siltronic    ████████████ 11.5
  SK Siltron   ███████████ 11.4
  Soitec       ██████ 5.5

  (2025-ish report: Shin-Etsu 28, SUMCO 25, GW 15, Siltronic 12)
"##;
const V19S: &[Spot] = &[
    spot(
        "Shin-Etsu",
        0,
        TO_EOL,
        "29.4% about 2021 (Semiconductor Engineering, citing GlobalWafers); about 28% in a 2025 Chinese industry report.",
    ),
    spot("SUMCO", 0, TO_EOL, "21.9% about 2021."),
    spot("GlobalWafers", 0, TO_EOL, "15.2% about 2021."),
    spot("Soitec", 0, TO_EOL, "5.5%, the SOI specialist."),
    spot(
        "(2025-ish report: Shin-Etsu 28, SUMCO 25, GW 15, Siltronic 12)",
        0,
        0,
        "A more recent source with a similar ranking.",
    ),
];

const V20: &str = r##"
# Timeline

  24 Jul 2026  Shin-Etsu call: 300 mm +mid-single digit, record June
   4 Aug 2026  GlobalWafers call: existing capacity fully utilized
  18 Sep 2026  UBS: 12-inch utilization 84% (2026) to 99% (2028)
     after 2028 ──▶ possible severe shortage if prices lag

  UBS ratings: Shin-Etsu, GlobalWafers, Siltronic Buy; SUMCO Neutral
"##;
const V20S: &[Spot] = &[
    spot(
        "24 Jul 2026",
        0,
        TO_EOL,
        "Shin-Etsu: 300 mm market growth mid-single digit year on year; wafer makers appear at full capacity.",
    ),
    spot("4 Aug 2026", 0, TO_EOL, "GlobalWafers' Q2 call."),
    spot("18 Sep 2026", 0, TO_EOL, "UBS note (secondary report)."),
    spot(
        "after 2028",
        0,
        TO_EOL,
        "UBS says new capacity would need roughly 40% to 50% price rises or more; otherwise a severe shortage could follow after 2028 (broker view).",
    ),
    spot(
        "UBS ratings",
        0,
        TO_EOL,
        "Secondary report of the Sept 2026 UBS note.",
    ),
];

const V21: &str = r##"
# 2025 vs 2024 (SEMI)

  area      ▲ +5.8%   12,973 MSI
  revenue   ▼ -1.2%   $11.4 billion

  $11.4B / 12,973 MSI = about $0.88 per sq in
  (arithmetic here, all wafer diameters mixed)
"##;
const V21S: &[Spot] = &[
    spot(
        "▲ +5.8%",
        0,
        TO_EOL,
        "SEMI: 2025 shipments 12,973 MSI, up 5.8%.",
    ),
    spot(
        "▼ -1.2%",
        0,
        TO_EOL,
        "SEMI: 2025 revenue $11.4 billion, down 1.2%.",
    ),
    spot(
        "about $0.88 per sq in",
        0,
        0,
        "Computed here from the two SEMI figures; all diameters are mixed, so it is a blended average.",
    ),
];

const V22: &str = r##"
# Two-speed market

┌────────────────────────────────┐
│ STRONG                         │
│ advanced epi (sub-3nm logic)   │
│ polished wafers for HBM        │
└────────────────────────────────┘
┌────────────────────────────────────┐
│ SOFT                               │
│ mature nodes: auto, industrial,    │
│ consumer; inventories normalizing  │
└────────────────────────────────────┘

  Oct 2025 forecast: 12,824 MSI (2025), 15,485 MSI (2028)
"##;
const V22S: &[Spot] = &[
    spot(
        "STRONG",
        0,
        0,
        "Advanced epitaxial wafers for sub-3nm logic and polished wafers for HBM drove demand.",
    ),
    spot(
        "SOFT",
        0,
        0,
        "Demand and pricing have yet to improve in traditional applications; inventories began to normalize.",
    ),
    spot(
        "12,824 MSI (2025)",
        0,
        0,
        "SEMI's Oct 2025 forecast for 2025; the actual figure came in higher at 12,973.",
    ),
    spot("15,485 MSI (2028)", 0, 0, "Forecast record by 2028."),
];

const V23: &str = r##"
# Qualifying a new wafer supplier (textbook flow)

  ┌───────────┐   ┌───────────────────┐   ┌──────────────┐
  │ SAMPLE    │   │ RUN THROUGH       │   │ QUALIFIED    │
  │ wafers    │──▶│ the fab's process │──▶│ for volume   │
  └───────────┘   └───────────────────┘   └──────────────┘

  repeated per process and per node: many months in total
  (no sourced duration)
"##;
const V23S: &[Spot] = &[
    spot(
        "SAMPLE",
        0,
        0,
        "The fab receives sample wafers from the candidate supplier.",
    ),
    spot(
        "RUN THROUGH",
        0,
        0,
        "Wafers run through the fab's own process, since each fab qualifies per process.",
    ),
    spot(
        "QUALIFIED",
        0,
        0,
        "Only then are volume orders placed. Incumbents benefit from the stickiness.",
    ),
    spot(
        "many months in total",
        0,
        0,
        "Textbook claim on the page; no source gave a specific duration.",
    ),
];

const V24: &str = r##"
# Price increases by wafer size (Taiwan News)

  6-inch   ████████████████████ hikes done
  8-inch   ██████████░░░░░░░░░░ under negotiation
  12-inch  ██████████░░░░░░░░░░ under negotiation

  UBS: new capacity needs +40-50% prices or more (broker view)
"##;
const V24S: &[Spot] = &[
    spot(
        "6-inch",
        0,
        TO_EOL,
        "Per Taiwan News, 6-inch price hikes are done.",
    ),
    spot("8-inch", 0, TO_EOL, "8-inch hikes under negotiation."),
    spot("12-inch", 0, TO_EOL, "12-inch hikes under negotiation."),
    spot(
        "UBS: new capacity needs +40-50% prices or more",
        0,
        0,
        "Broker view, reported secondhand.",
    ),
];

const V25: &str = r##"
# SUMCO share

  about 2021  ██████████████████████ 21.9%
  2025-vintage█████████████████████████ ~25%

  UBS (Sept 2026): Neutral
  (different sources, different bases: compare with care)
"##;
const V25S: &[Spot] = &[
    spot(
        "about 2021",
        0,
        TO_EOL,
        "21.9% in the 2021 Semiconductor Engineering table.",
    ),
    spot(
        "2025-vintage",
        0,
        TO_EOL,
        "About 25% in a 2025-vintage Chinese industry report.",
    ),
    spot(
        "UBS (Sept 2026): Neutral",
        0,
        0,
        "Secondary report of the UBS note.",
    ),
];

const V26: &str = r##"
# Five makers, one geography problem

  ┌───────────┐  ┌─────────┐  ┌──────────────┐
  │ Shin-Etsu │  │ SUMCO   │  │ GlobalWafers │
  │ JP        │  │ JP      │  │ TW           │
  └───────────┘  └─────────┘  └──────────────┘
  ┌───────────┐  ┌────────────┐
  │ Siltronic │  │ SK Siltron │
  │ DE        │  │ KR         │
  └───────────┘  └────────────┘

  a Japan quake or outage hits the top two at once
"##;
const V26S: &[Spot] = &[
    spot("Shin-Etsu", 0, 0, "Largest wafer maker."),
    spot(
        "SUMCO",
        0,
        0,
        "Second largest; said in 2021 that 300 mm logic supply was struggling and 200 mm was tight (auto).",
    ),
    spot("GlobalWafers", 0, 0, "Taiwan-based."),
    spot(
        "a Japan quake or outage hits the top two at once",
        0,
        0,
        "The page's concentration risk; textbook, see crucibles in SAND.",
    ),
];

const V27: &str = r##"
# Source decides the method

  ┌──────────────────┐  ┌───────────────────┐  ┌────────────────┐
  │ CVD              │  │ ALD               │  │ PVD            │
  │ precursor gas,   │  │ gas pulses,       │  │ solid target,  │
  │ continuous flow  │  │ one layer a cycle │  │ sputtered      │
  └──────────────────┘  └───────────────────┘  └────────────────┘

  gas: WF6, SiH4, H2, TEOS...      solid: Ta, Ti, Cu target
"##;
const V27S: &[Spot] = &[
    spot(
        "CVD",
        0,
        0,
        "Builds a film from reacting gases at the wafer surface, continuously.",
    ),
    spot(
        "ALD",
        0,
        0,
        "Alternates self-limiting gas pulses so each cycle adds about one atomic layer.",
    ),
    spot(
        "PVD",
        0,
        0,
        "Argon ions knock metal atoms off a solid target; line-of-sight coating.",
    ),
    spot(
        "gas: WF6, SiH4, H2, TEOS...",
        0,
        0,
        "Example precursors on the page.",
    ),
    spot(
        "solid: Ta, Ti, Cu target",
        0,
        0,
        "PVD sources for barrier and seed layers.",
    ),
];

const V28: &str = r##"
# Delivering a solid precursor

  ┌───────────────┐   ┌────────────┐   ┌────────────┐   ┌────────┐
  │ SOLID         │   │ HEATED     │   │ LINES      │   │ WAFER  │
  │ Mo precursor  │──▶│ to vapour  │──▶│ to chamber │──▶└────────┘
  └───────────────┘   └────────────┘   └────────────┘

  gas precursors skip the first two steps: easier to deliver
  AI link: more layers, more 3D structures, more steps per wafer
"##;
const V28S: &[Spot] = &[
    spot(
        "SOLID",
        0,
        0,
        "The ALD molybdenum precursor is a solid, which complicates delivery (Counterpoint).",
    ),
    spot(
        "HEATED",
        0,
        0,
        "A solid must be turned to vapour before it can be dosed; this is the added step compared with gases.",
    ),
    spot(
        "LINES",
        0,
        0,
        "Lam's ALTUS Halo was built to handle Mo delivery; a Japanese report cites over 50% resistivity improvement versus tungsten (company-derived).",
    ),
    spot(
        "AI link: more layers",
        0,
        TO_EOL,
        "GAA, HBM and 3D NAND mean more deposition steps per wafer, so AI-driven chips raise deposition intensity.",
    ),
];

const V29: &str = r##"
# Temperature windows, C

                0         200       400       600       800
  ALD Al2O3 (O3)     ████████ data
  PECVD TEOS              ██████████ patent
  W fill (CVD)                      █████ wafer
  LPCVD TEOS                                    ████████ <5 Torr

  lower temperature protects earlier layers (back-end metal)
"##;
const V29S: &[Spot] = &[
    spot(
        "ALD Al2O3 (O3)",
        0,
        TO_EOL,
        "Ozone Al2O3 ALD grows about 0.6 A/cycle at 100 C and 0.9 A/cycle at 250 C (UPenn).",
    ),
    spot(
        "PECVD TEOS",
        0,
        TO_EOL,
        "One patent claims 200 to 400 C up to 50 Torr; typical PECVD is under 1 Torr.",
    ),
    spot(
        "W fill (CVD)",
        0,
        TO_EOL,
        "Tungsten fill runs the wafer at about 400 to 500 C.",
    ),
    spot(
        "LPCVD TEOS",
        0,
        TO_EOL,
        "650 to 800 C, rate rising exponentially with temperature, below about 5 Torr (patents).",
    ),
    spot(
        "lower temperature protects earlier layers",
        0,
        0,
        "Higher temperature can violate thermal budgets of earlier layers; that is why PECVD and ALD matter in back-end metal (textbook).",
    ),
];

const V30: &str = r##"
# Two ways to fill a chamber

  ┌────────────────────────┐  ┌──────────────────────────┐
  │ BATCH (Kokusai)        │  │ SINGLE WAFER (ASM)       │
  │ ▓▓▓▓▓▓▓▓▓▓▓▓           │  │ ▓▓▓▓                     │
  │ many wafers, one run   │  │ one wafer, one chamber   │
  └────────────────────────┘  └──────────────────────────┘

  batch ALD share: Kokusai ~70%, TEL most of the rest (SemiAnalysis,
  undated)
"##;
const V30S: &[Spot] = &[
    spot(
        "BATCH (Kokusai)",
        0,
        0,
        "Batch furnaces process many wafers per run, trading per-wafer control for throughput.",
    ),
    spot(
        "SINGLE WAFER (ASM)",
        0,
        0,
        "ASM and others use single-wafer chambers.",
    ),
    spot(
        "Kokusai ~70%",
        0,
        0,
        "SemiAnalysis, undated. Kokusai itself claims No.1 revenue share in batch-ALD-compatible equipment for 2025.",
    ),
];

const V31: &str = r##"
# Coverage in a narrow trench

    PVD (line of sight)        ALD (self-limiting)
   ░░░░▓       ▓░░░░          ░░░░▓░░░░░░░▓░░░░
   ░░░░▓       ▓░░░░               ▓░     ░▓
        ▓.     .▓                  ▓░     ░▓
        ▓.     .▓                  ▓░     ░▓
        ▓░░░░░░░▓                  ▓░░░░░░░▓

  PVD: thick on top and bottom, thin on sidewalls
"##;
const V31S: &[Spot] = &[
    spot(
        "PVD (line of sight)",
        0,
        0,
        "Coats surfaces facing the target; sidewalls get little, so ALD or CVD takes over as trenches narrow (textbook).",
    ),
    spot(
        "ALD (self-limiting)",
        0,
        0,
        "Each cycle coats every exposed surface equally, so coverage is conformal.",
    ),
    spot(
        "PVD: thick on top and bottom, thin on sidewalls",
        0,
        0,
        "The cost of line-of-sight deposition in deep, narrow features.",
    ),
];

const V32: &str = r##"
# 3D NAND wordline, schematic

        vertical channel
   ▓▓▓▓▓▓▓▓▓│▓▓▓▓▓▓▓▓▓   ◀── metal fills horizontal slots
   ░░░░░░░░░│░░░░░░░░░       through a vertical hole
   ▓▓▓▓▓▓▓▓▓│▓▓▓▓▓▓▓▓▓
   ░░░░░░░░░│░░░░░░░░░

  ASM: Mo ALD in HVM for 2nm; GAA 1.4nm adds est. $450-500M (company)
"##;
const V32S: &[Spot] = &[
    spot(
        "vertical channel",
        0,
        0,
        "3D NAND needs conformal deposition in vertical and horizontal wordline structures (Counterpoint).",
    ),
    spot(
        "metal fills horizontal slots",
        0,
        0,
        "Wordline metal must enter a deep hole and fill sideways: a job for ALD.",
    ),
    spot(
        "ASM: Mo ALD in HVM for 2nm",
        0,
        TO_EOL,
        "ASM says Mo ALD and area-selective deposition entered high-volume manufacturing for 2nm and it expects more GAA share at 1.4nm (company estimate).",
    ),
];

const V33: &str = r##"
# Exhaust path

  ┌──────────────────────┐   ┌────────┐   ┌──────────────┐
  │ CHAMBER              │   │ PUMP   │   │ SCRUBBER     │
  │ film + by-products   │──▶└────────┘──▶│ abatement    │
  └──────────────────────┘                └──────────────┘

  tungsten recipe by-products: HF, SiF4 (corrosive, toxic)
  WF6 + 3H2 -> W + 6HF    2WF6 + 3SiH4 -> 2W + 3SiF4 + 6H2
"##;
const V33S: &[Spot] = &[
    spot(
        "CHAMBER",
        0,
        0,
        "By-products that do not leave condense as particles or flakes on chamber walls.",
    ),
    spot(
        "PUMP",
        0,
        0,
        "Keeps the chamber at its low process pressure and removes volatile by-products.",
    ),
    spot(
        "SCRUBBER",
        0,
        0,
        "Abatement of toxic exhaust is a real part of tool cost and uptime (textbook).",
    ),
    spot(
        "HF, SiF4",
        0,
        0,
        "Corrosive and toxic by-products of the tungsten recipes on the page.",
    ),
    spot(
        "WF6 + 3H2 -> W + 6HF",
        0,
        TO_EOL,
        "Textbook tungsten fill reactions from the page.",
    ),
];

const V34: &str = r##"
# The clean loop

  deposit ──▶ film also grows on walls ──▶ flakes fall on wafers
     ▲                                           │
     └── plasma clean + replace parts ◀──────────┘

  ASM spares+svc 2025   ███ +18%
  Kokusai service FY2026█████████████████████ +127% (verify)
"##;
const V34S: &[Spot] = &[
    spot(
        "flakes fall on wafers",
        0,
        0,
        "Particles from wall deposits land on wafers, so chambers need periodic plasma cleaning.",
    ),
    spot(
        "plasma clean + replace parts",
        0,
        0,
        "Cleaning and consumables are recurring revenue for tool makers.",
    ),
    spot(
        "ASM spares+svc 2025",
        0,
        TO_EOL,
        "ASM reported spares and services up 18% in 2025.",
    ),
    spot(
        "Kokusai service FY2026",
        0,
        TO_EOL,
        "Up 127.4% per one aggregator; verify before relying on it.",
    ),
];

const V35: &str = r##"
# One layer, repeated

  ┌──────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
  │ DEPOSIT  │   │ LITHO    │   │ ETCH    │   │ CMP      │
  │ film     │──▶│ pattern  │──▶│ carve   │──▶│ flatten  │
  └──────────┘   └──────────┘   └─────────┘   └──────────┘
     ▲                                          │
     └──────── next layer, many times ◀─────────┘
"##;
const V35S: &[Spot] = &[
    spot(
        "DEPOSIT",
        0,
        0,
        "Tool demand scales with layer count (textbook).",
    ),
    spot("ETCH", 0, 0, "Patterns the film."),
    spot(
        "CMP",
        0,
        0,
        "Flattens the wafer after tungsten or copper fill.",
    ),
    spot(
        "next layer, many times",
        0,
        0,
        "More layers per chip means more deposition steps.",
    ),
];

const V36: &str = r##"
# Copper wire cross-section, schematic

  ┌▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┐   ▓ dielectric
  │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│   ▒ Ta(N)/Ta barrier (PVD)
  │▒ ░░░░░░░░░░░░░░░░░░░░░░░ ▒│   ░ Cu seed, then Cu fill
  │▒ ░         copper       ░▒│
  └▒▒░░░░░░░░░░░░░░░░░░░░░░░▒▒┘

  Applied: Endura CuBS RF XT (barrier + seed), Volta Ru CVD (liner)
"##;
const V36S: &[Spot] = &[
    spot(
        "Ta(N)/Ta barrier (PVD)",
        0,
        0,
        "Applied's Endura CuBS RF XT deposits the Ta(N)/Ta barrier, then the copper seed, under high vacuum.",
    ),
    spot(
        "Cu seed, then Cu fill",
        0,
        0,
        "The seed conducts current for the copper fill that follows.",
    ),
    spot(
        "Endura CuBS RF XT",
        0,
        0,
        "PVD barrier and seed tool for logic and memory.",
    ),
    spot(
        "Volta Ru CVD (liner)",
        0,
        0,
        "Ruthenium CVD liner to keep copper viable at 2nm-class and beyond (Applied).",
    ),
];

const V37: &str = r##"
# Showerhead reactor

      gas in (WF6, SiH4, H2)
            │
  ══════════▼═══════════  showerhead (RF electrode in PECVD)
    ↓  ↓  ↓  ↓  ↓  ↓  ↓
  ▓▓▓▓▓▓▓▓ wafer ▓▓▓▓▓▓▓▓
  ═════ heated pedestal ═════
"##;
const V37S: &[Spot] = &[
    spot("gas in (WF6, SiH4, H2)", 0, 0, "Typical gases on the page."),
    spot(
        "showerhead (RF electrode in PECVD)",
        0,
        0,
        "A perforated plate; in PECVD it is also the RF electrode that ignites the plasma.",
    ),
    spot(
        "↓  ↓  ↓",
        0,
        0,
        "Hole pattern and spacing set film uniformity (textbook).",
    ),
    spot(
        "heated pedestal",
        0,
        0,
        "Holds and heats the wafer to hundreds of degrees C.",
    ),
];

const V38: &str = r##"
# Lam ALTUS Halo, four chambers (Japanese report)

  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
  │ CH 1   │  │ CH 2   │  │ CH 3   │  │ CH 4   │
  └────────┘  └────────┘  └────────┘  └────────┘

  ALTUS family: CVD + ALD for tungsten or molybdenum
  (Lam FY2025 10-K)
"##;
const V38S: &[Spot] = &[
    spot(
        "CH 1",
        0,
        0,
        "Four-chamber configuration per a Japanese report; chamber detail not independently confirmed.",
    ),
    spot(
        "ALTUS family",
        0,
        TO_EOL,
        "Combines CVD and ALD for tungsten or molybdenum metallization in logic and memory (Lam FY2025 10-K).",
    ),
    spot("(Lam FY2025 10-K)", 0, 0, "SEC filing cited on the page."),
];

const V39: &str = r##"
# ALD growth per cycle, angstrom

  O3 Al2O3 100C  ████████████ 0.6
  O3 Al2O3 250C  ██████████████████ 0.9
  HfO2 <400C     ████████████████████████████ 1.2-1.6

  higher temperature: more growth, better crystal (HfO2 above 300C)
"##;
const V39S: &[Spot] = &[
    spot(
        "O3 Al2O3 100C",
        0,
        TO_EOL,
        "About 0.6 A/cycle at 100 C with ozone (UPenn).",
    ),
    spot(
        "O3 Al2O3 250C",
        0,
        TO_EOL,
        "About 0.9 A/cycle at 250 C with ozone (UPenn).",
    ),
    spot(
        "HfO2 <400C",
        0,
        TO_EOL,
        "TDMAH plus water gives 1.2 to 1.6 A per cycle below 400 C (PMC).",
    ),
    spot(
        "higher temperature: more growth",
        0,
        0,
        "HfO2 gets better crystal quality and higher dielectric constant above 300 C (PMC).",
    ),
];

const V40: &str = r##"
# Heat across the wafer

  uniform pedestal        non-uniform pedestal
  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒         ░░▒▒▓▓▓▓▓▒▒░░
  same film everywhere    thicker film where it runs hotter

  ceramic heaters wear: a consumable (textbook)
"##;
const V40S: &[Spot] = &[
    spot(
        "uniform pedestal",
        0,
        0,
        "The goal: the same temperature across the 300 mm wafer.",
    ),
    spot(
        "non-uniform pedestal",
        0,
        0,
        "Gives thickness and stress variation across the wafer (textbook).",
    ),
    spot(
        "ceramic heaters wear",
        0,
        TO_EOL,
        "Textbook; no lifetime figure sourced.",
    ),
];

const V41: &str = r##"
# One ALD cycle (Al2O3 example)

  ┌──────────────┐   ┌───────────┐   ┌─────────────┐   ┌──────────┐
  │ 1 PULSE A    │   │ 2 PURGE   │   │ 3 PULSE B   │   │ 4 PURGE  │
  │ TMA on all   │──▶│ inert gas │──▶│ H2O reacts  │──▶└──────────┘
  │ sites        │   └───────────┘   └─────────────┘
  └──────────────┘

  Al(CH3)3 + surface-OH -> surface-O-Al(CH3)2 + CH4      (A)
  surface-Al-CH3 + H2O -> surface-Al-OH + CH4              (B)
"##;
const V41S: &[Spot] = &[
    spot(
        "1 PULSE A",
        0,
        0,
        "The precursor saturates every surface site, then stops reacting: self-limiting.",
    ),
    spot(
        "2 PURGE",
        0,
        0,
        "Inert gas removes excess precursor so the gases never meet in the gas phase.",
    ),
    spot(
        "3 PULSE B",
        0,
        0,
        "The second reactant converts layer A into the desired film and re-prepares the surface.",
    ),
    spot(
        "4 PURGE",
        0,
        0,
        "Removes by-products; then the cycle repeats.",
    ),
    spot(
        "Al(CH3)3 + surface-OH",
        0,
        TO_EOL,
        "TMA half reaction, from the page.",
    ),
];

const V42: &str = r##"
# Time to grow Al2O3 on the UPenn recipe

  one cycle: 2 x 0.015 s pulses + 2 x 8 s purges = ~16 s
   10 cycles   █            ~1 nm    ~3 min
  100 cycles   ██████████   ~10 nm   ~27 min
  300 cycles   ██████████████████████████████  ~30 nm  ~80 min

  (about 1 A per cycle; lab recipe, production tools are faster)
"##;
const V42S: &[Spot] = &[
    spot(
        "2 x 0.015 s pulses",
        0,
        TO_EOL,
        "UPenn recipe at 200 C: 0.015 s pulses, 8 s purges, precursor lines at 150 C.",
    ),
    spot("10 cycles", 0, TO_EOL, "About 1 nm at about 1 A per cycle."),
    spot(
        "100 cycles",
        0,
        TO_EOL,
        "About 10 nm; about 27 minutes on the lab timings (arithmetic here).",
    ),
    spot(
        "300 cycles",
        0,
        TO_EOL,
        "About 30 nm; about 80 minutes on the lab timings (arithmetic here).",
    ),
    spot(
        "(about 1 A per cycle",
        0,
        0,
        "Stanford SNF ALD tutorial gives roughly 1 A per cycle for Al2O3.",
    ),
];

const V43: &str = r##"
# ASM International revenue, EUR billion

  2025      ████████████████ 3.2 (+12% cc)
  2030 goal ████████████████████████████ > 5.7

  gross margin 51.8% (record), adjusted operating margin 30.2%
  drivers: ALD and epitaxy
"##;
const V43S: &[Spot] = &[
    spot(
        "2025",
        0,
        TO_EOL,
        "Record EUR 3.2 billion, up 12% constant currency.",
    ),
    spot(
        "2030 goal",
        0,
        TO_EOL,
        "Revenue above EUR 5.7 billion, with ALD and epitaxy as main growth drivers.",
    ),
    spot(
        "gross margin 51.8% (record)",
        0,
        TO_EOL,
        "Gross margin 51.8% and adjusted operating margin 30.2% for 2025.",
    ),
];

const V44: &str = r##"
# PVD chamber

     Ar+ ions ↓ ↓ ↓
  ┌───────────────────────┐
  │ TARGET (Ta, Ti, Cu)   │  biased negative
  └───────────────────────┘
     metal atoms ↓ ↓ ↓  fly across the vacuum gap
  ┌───────────────────────┐
  │▓▓▓▓▓▓ wafer ▓▓▓▓▓▓▓▓▓▓│  (chuck sometimes RF-biased)
  └───────────────────────┘
"##;
const V44S: &[Spot] = &[
    spot(
        "Ar+ ions",
        0,
        0,
        "Argon ions accelerate into the negatively biased target.",
    ),
    spot(
        "TARGET (Ta, Ti, Cu)",
        0,
        0,
        "Struck atoms are knocked out of the target.",
    ),
    spot(
        "metal atoms",
        0,
        0,
        "They fly across the vacuum gap in straight lines, so coverage is line-of-sight.",
    ),
    spot(
        "chuck sometimes RF-biased",
        0,
        0,
        "RF bias helps trench bottom coverage.",
    ),
];

const V45: &str = r##"
# Handoff as trenches narrow

  wide trench    PVD barrier + seed fits
  narrow trench  Ru CVD liner (Volta) / ALD
  2nm and below  copper stays in use (Applied)

  Endura CuBS RF XT: Ta(N)/Ta barrier, Cu seed, high vacuum
"##;
const V45S: &[Spot] = &[
    spot(
        "wide trench",
        0,
        TO_EOL,
        "PVD's line-of-sight coverage is good enough in wide features.",
    ),
    spot(
        "narrow trench",
        0,
        TO_EOL,
        "Ruthenium CVD liners (Applied's Volta) and ALD take over.",
    ),
    spot(
        "2nm and below",
        0,
        TO_EOL,
        "Applied says copper can stay in use for 2nm-class and beyond.",
    ),
    spot(
        "Endura CuBS RF XT",
        0,
        TO_EOL,
        "Applied PVD tool for barrier and seed.",
    ),
];

const V46: &str = r##"
# TEOS to oxide

  Si(OC2H5)4 ──heat or plasma──▶ SiO2 + organic by-products
  (TEOS liquid, vapour fed to the chamber)

  thermal (LPCVD):  hot, dense film
  plasma (PECVD):   cooler, faster, lower density
"##;
const V46S: &[Spot] = &[
    spot(
        "Si(OC2H5)4",
        0,
        0,
        "Tetraethyl orthosilicate, the standard SiO2 precursor.",
    ),
    spot("SiO2", 0, 0, "The insulating film between wires."),
    spot(
        "thermal (LPCVD)",
        0,
        TO_EOL,
        "650 to 800 C below about 5 Torr (patents).",
    ),
    spot(
        "plasma (PECVD)",
        0,
        TO_EOL,
        "Plasma lowers the temperature so back-end layers are not damaged.",
    ),
];

const V47: &str = r##"
# PECVD rate example (patent)

  41 A/s  = ~2,460 A/min   at 4 Torr, 200 C
  fast film  ────────────────────▶  low density
  slow film  ◀────────────────────  high density

  LPCVD: 650-800 C, < ~5 Torr, rate rises exponentially with T
"##;
const V47S: &[Spot] = &[
    spot(
        "41 A/s",
        0,
        TO_EOL,
        "Reported PECVD rate (about 2,460 A/min) at 4 Torr and 200 C.",
    ),
    spot(
        "fast film",
        0,
        TO_EOL,
        "High deposition rate means low film density.",
    ),
    spot("slow film", 0, TO_EOL, "Slower growth gives denser film."),
    spot(
        "LPCVD: 650-800 C",
        0,
        TO_EOL,
        "Rate rises exponentially with temperature (patents).",
    ),
];

const V48: &str = r##"
# Tungsten fill in three steps

  ┌────────────────────┐   ┌─────────────────┐   ┌──────────┐
  │ 1 SiH4 nucleation  │   │ 2 H2 bulk fill  │   │ 3 CMP    │
  │ layer < 100 nm     │──▶│ WF6 + 3H2       │──▶│ flatten  │
  └────────────────────┘   └─────────────────┘   └──────────┘

  WF6 + 3H2 -> W + 6HF      2WF6 + 3SiH4 -> 2W + 3SiF4 + 6H2
  wafer at ~400-500 C (patents)
"##;
const V48S: &[Spot] = &[
    spot(
        "1 SiH4 nucleation",
        0,
        0,
        "Silane makes a nucleation layer under 100 nm and protects Ti and Si from WF6.",
    ),
    spot(
        "2 H2 bulk fill",
        0,
        0,
        "H2 reduction gives a conformal, low-resistance bulk film.",
    ),
    spot(
        "3 CMP",
        0,
        0,
        "Chemical mechanical planarization flattens the fill.",
    ),
    spot(
        "WF6 + 3H2 -> W + 6HF",
        0,
        TO_EOL,
        "Textbook reactions on the page.",
    ),
    spot("~400-500 C", 0, 0, "Wafer temperature window from patents."),
];

const V49: &str = r##"
# Tungsten vs molybdenum

  ┌────────────────────┐  ┌─────────────────────────────┐
  │ TUNGSTEN (today)   │  │ MOLYBDENUM                  │
  │ WF6 chemistry      │  │ lower resistivity           │
  │ HF by-product      │  │ barrierless (Counterpoint)  │
  └────────────────────┘  └─────────────────────────────┘

  Lam CEO (Q4 2024 call): W to Mo in NAND begins in 2025
  (no independent confirmation of 2025 volume found)
"##;
const V49S: &[Spot] = &[
    spot(
        "TUNGSTEN (today)",
        0,
        0,
        "The incumbent contact and via fill metal.",
    ),
    spot(
        "MOLYBDENUM",
        0,
        0,
        "Counterpoint credits Mo with lower resistivity and barrierless deposition.",
    ),
    spot(
        "Lam CEO (Q4 2024 call)",
        0,
        TO_EOL,
        "Said the W to Mo transition in NAND would begin in 2025.",
    ),
    spot(
        "(no independent confirmation",
        0,
        0,
        "Treat 2025 adoption timing as a company claim.",
    ),
];

const V50: &str = r##"
# ASM International

  2025 revenue  ████████████████ EUR 3.2B
  2030 goal     ████████████████████████████ > EUR 5.7B

  driver 2025: advanced logic + foundry, 2nm GAA capacity
  tech: Mo ALD + area-selective deposition in HVM for 2nm
"##;
const V50S: &[Spot] = &[
    spot(
        "2025 revenue",
        0,
        TO_EOL,
        "A record EUR 3.2 billion, up 12% constant currency.",
    ),
    spot("2030 goal", 0, TO_EOL, "Revenue above EUR 5.7 billion."),
    spot(
        "driver 2025",
        0,
        TO_EOL,
        "Mostly advanced logic and foundry, as customers added 2nm GAA capacity.",
    ),
    spot(
        "tech: Mo ALD",
        0,
        TO_EOL,
        "Entered high-volume manufacturing for 2nm; ASM sees an extra $450-500M served market at 1.4nm (company estimates).",
    ),
];

const V51: &str = r##"
# Exposure, 2025

  China (revenue)  ██████████████████████████████ > 30%
  Memory (equip.)  ████████████████ 16%
  Spares+services  ██████████████████ +18% growth

  China means export-control risk
"##;
const V51S: &[Spot] = &[
    spot(
        "China (revenue)",
        0,
        TO_EOL,
        "More than 30% of 2025 revenue, an export-control exposure.",
    ),
    spot("Memory (equip.)", 0, TO_EOL, "16% of equipment sales."),
    spot(
        "Spares+services",
        0,
        TO_EOL,
        "Up 18% in 2025 (growth rate, not a share).",
    ),
    spot(
        "China means export-control risk",
        0,
        0,
        "Export-control changes could hit this exposure.",
    ),
];

const V52: &str = r##"
# What Mo is credited with

  tungsten   ████████████████████  resistivity (reference)
  molybdenum ██████████░░░░░░░░░░  lower (report: >50% better)
                                   company-derived, unverified

  also: barrierless deposition (Counterpoint, white paper with Lam)
"##;
const V52S: &[Spot] = &[
    spot(
        "tungsten",
        0,
        TO_EOL,
        "The reference metal for contacts and wordlines.",
    ),
    spot(
        "molybdenum",
        0,
        TO_EOL,
        "Lower resistivity; a Japanese report cites over 50% improvement depending on application (company-derived, unverified).",
    ),
    spot(
        "barrierless deposition",
        0,
        TO_EOL,
        "Counterpoint, in a white paper with Lam, credits Mo with barrierless deposition.",
    ),
];

const V53: &str = r##"
# Two hurdles

  ┌────────────────────┐  ┌──────────────────────────┐
  │ SOLID PRECURSOR    │  │ 3D NAND                  │
  │ harder to deliver  │  │ conformal in vertical    │
  │ than a gas         │  │ and horizontal wordlines │
  └────────────────────┘  └──────────────────────────┘

  Lam ALTUS Halo and ASM Mo ALD both target these
"##;
const V53S: &[Spot] = &[
    spot(
        "SOLID PRECURSOR",
        0,
        0,
        "Complicates delivery; Lam built ALTUS Halo for it.",
    ),
    spot(
        "3D NAND",
        0,
        0,
        "NAND needs ALD that deposits conformally in vertical and horizontal wordline structures.",
    ),
    spot(
        "Lam ALTUS Halo and ASM Mo ALD",
        0,
        TO_EOL,
        "Both vendors are in this metal swap.",
    ),
];

const V54: &str = r##"
# Semiconductor Systems by end market, FY2025 (%)

  foundry/logic ██████████████████████████████████ 67 (68 prior)
  DRAM          █████████████ 26 (28 prior)
  NAND          ████ 7 (4 prior)

  segment: $20.80B, 73% of $28.37B total, up 4%
"##;
const V54S: &[Spot] = &[
    spot(
        "foundry/logic",
        0,
        TO_EOL,
        "67% of the segment, versus 68% the prior year.",
    ),
    spot("DRAM", 0, TO_EOL, "26%, versus 28%."),
    spot("NAND", 0, TO_EOL, "7%, versus 4%."),
    spot(
        "segment: $20.80B",
        0,
        TO_EOL,
        "FY2025 Semiconductor Systems revenue, per the SEC filing.",
    ),
];

const V55: &str = r##"
# Applied's deposition products

  ┌──────────────────────┐  ┌───────────────┐
  │ Endura CuBS RF XT    │  │ Endura Volta  │
  │ PVD barrier + seed   │  │ Ru CVD liner  │
  └──────────────────────┘  └───────────────┘

  2009 share (old): Applied 49%, TEL 17%, Novellus 16%
  Substack: Applied, TEL lost share in 2025 (paywalled)
"##;
const V55S: &[Spot] = &[
    spot(
        "Endura CuBS RF XT",
        0,
        0,
        "PVD barrier and seed for copper interconnect.",
    ),
    spot("Endura Volta", 0, 0, "Ruthenium CVD for copper liners."),
    spot(
        "2009 share (old)",
        0,
        TO_EOL,
        "Old chart, shown for structure only.",
    ),
    spot(
        "Substack: Applied, TEL lost share",
        0,
        TO_EOL,
        "Paywalled; treat as a secondary claim.",
    ),
];

const V56: &str = r##"
# Batch ALD share (SemiAnalysis, undated)

  Kokusai  ███████████████████████████████████ ~70%
  TEL+     ███████████████ most of the rest

  Kokusai also claims No.1 revenue share in 2025 (company)
"##;
const V56S: &[Spot] = &[
    spot(
        "Kokusai  ",
        0,
        TO_EOL,
        "About 70% of batch ALD per an undated SemiAnalysis piece.",
    ),
    spot("TEL+", 0, TO_EOL, "TEL holds most of the remainder."),
    spot(
        "Kokusai also claims No.1",
        0,
        TO_EOL,
        "Company claim for 2025 batch-ALD-compatible equipment.",
    ),
];

const V57: &str = r##"
# Nine months FY2026, JPY billion (aggregator, verify)

  China prior  ██████████████████████████████████████████ 83.0
  China now    █████████████████████████████████████ 73.2
  Op profit prior████████████████████ 39.7
  Op profit now  ████████████████ 32.5

  customers: CXMT 20.4%, Samsung 13.3%, TSMC 12.9%
"##;
const V57S: &[Spot] = &[
    spot(
        "China prior",
        0,
        TO_EOL,
        "JPY 83.0B in the prior-year nine months.",
    ),
    spot("China now", 0, TO_EOL, "JPY 73.2B; Korea rose."),
    spot(
        "Op profit now",
        0,
        TO_EOL,
        "Operating profit fell to about JPY 32.5B from 39.7B.",
    ),
    spot(
        "customers: CXMT",
        0,
        TO_EOL,
        "Largest customers per the aggregator; verify before use.",
    ),
];

const V58: &str = r##"
# The coating stack, bottom to top

   ▲ light in
┌──────────────────────────────────────────────────┐
│ ░░░░ RESIST (imaging layer)                      │
│ ▒▒▒▒ BARC / underlayer (absorbs reflections)     │
│      primer (adhesion)                           │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓ WAFER ▓▓▓▓▓▓▓                            │
└──────────────────────────────────────────────────┘

  no BARC: light bounces off the substrate -> standing waves
"##;
const V58S: &[Spot] = &[
    spot(
        "RESIST (imaging layer)",
        0,
        0,
        "The photosensitive film that records the pattern.",
    ),
    spot(
        "BARC / underlayer",
        0,
        0,
        "Absorbs light that would reflect off the substrate. Textbook for DUV ArF; EUV stacks use thin underlayers and details differ by fab.",
    ),
    spot(
        "primer (adhesion)",
        0,
        0,
        "Adhesion failure lifts or collapses small resist lines (textbook).",
    ),
    spot(
        "standing waves",
        0,
        0,
        "Reflections create standing waves and linewidth variation (textbook).",
    ),
];

const V59: &str = r##"
# Where EUV photons go in a ~20 nm resist

  photons in   ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
  resist 20 nm ▒  absorbs only ~10% (1 in 10)
  passes on    ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓   ~90% into the underlayer

  so underlayers must be thin and uniform
"##;
const V59S: &[Spot] = &[
    spot("photons in", 0, TO_EOL, "EUV photons arrive at the resist."),
    spot(
        "resist 20 nm",
        0,
        TO_EOL,
        "About 20 nm thick, absorbs only about 10% of 13.5 nm light (Frederick Chen).",
    ),
    spot(
        "passes on",
        0,
        TO_EOL,
        "Roughly 90% passes through into what lies beneath.",
    ),
    spot(
        "so underlayers must be thin and uniform",
        0,
        0,
        "Every layer under an EUV resist must be thin and very uniform.",
    ),
];

const V60: &str = r##"
# Dispense at the centre

      pump + filter
           │
        ┌──┴──┐
        │NOZZLE│
        └──┬──┘
           ▼ drop
        ░░░░░  puddle (liquid resist)
  ═══════════════════ wafer, 300 mm
"##;
const V60S: &[Spot] = &[
    spot(
        "pump + filter",
        0,
        0,
        "Resist is metered by a pump and filtered at point of use.",
    ),
    spot("NOZZLE", 0, 0, "Swings to the wafer centre."),
    spot(
        "puddle (liquid resist)",
        0,
        0,
        "Too little gives voids; too much wastes expensive resist.",
    ),
    spot(
        "wafer, 300 mm",
        0,
        0,
        "Spin then spreads the puddle across the wafer.",
    ),
];

const V61: &str = r##"
# Wet vs dry resist application

  ┌────────────────┐  ┌────────────────────┐
  │ WET: dispense, │  │ DRY (Lam): deposit │
  │ spin, bake     │  │ in vacuum          │
  └────────────────┘  └────────────────────┘

  wet: bubbles and dried particles -> striations, comets
  dry: < 10 post-develop particles per 300 mm blanket wafer (lab)
"##;
const V61S: &[Spot] = &[
    spot(
        "WET: dispense,",
        0,
        0,
        "The conventional route: liquid resist from a nozzle.",
    ),
    spot(
        "DRY (Lam): deposit",
        0,
        0,
        "Lam's dry photoresist is deposited in vacuum rather than spun.",
    ),
    spot(
        "wet: bubbles and dried particles",
        0,
        TO_EOL,
        "Dispense-line defects leave striations and comets.",
    ),
    spot(
        "dry: < 10 post-develop particles",
        0,
        TO_EOL,
        "SPIE paper, lab result, not production.",
    ),
];

const V62: &str = r##"
# Thickness vs spin speed, AZ 4533 (um)

  2000 rpm  ████████████████████████████████████████ 4.0
  4000 rpm  █████████████████████████████████ 3.3
  6000 rpm  ███████████████████████ 2.3

  faster spin, thinner film (not exactly 1/sqrt(w))
"##;
const V62S: &[Spot] = &[
    spot("2000 rpm", 0, TO_EOL, "4.0 um (LBL reference data)."),
    spot("4000 rpm", 0, TO_EOL, "3.3 um."),
    spot("6000 rpm", 0, TO_EOL, "2.3 um."),
    spot(
        "not exactly 1/sqrt(w)",
        0,
        0,
        "Inverse square root is an empirical fit for photoresist; resist viscosity, solids content and bake matter.",
    ),
];

const V63: &str = r##"
# A spin recipe, schematic

  rpm
  4000 ┤      ┌──────────────┐
       │     /               \
       │    /                 \
     0 ┴───/───────────────────\──── time
          ramp   hold 20-30 s    stop

  TEL Mark 8 example: 1500-4000 rpm to a 280 nm film (patent)
"##;
const V63S: &[Spot] = &[
    spot(
        "ramp",
        0,
        0,
        "The wafer ramps to a few thousand rpm after dispense.",
    ),
    spot(
        "hold 20-30 s",
        0,
        0,
        "Conventional spin: 2000 to 4000 rpm for 20 to 30 s.",
    ),
    spot(
        "stop",
        0,
        0,
        "Stopping early makes thickness depend on spin time.",
    ),
    spot(
        "TEL Mark 8 example",
        0,
        TO_EOL,
        "From a patent: 1500 to 4000 rpm to reach a 280 nm film.",
    ),
];

const V64: &str = r##"
# Wafer edge, side view

                     ░░░  edge bead (resist piles up)
  ░░░░░░░░░░░░░░░░░░░░░░░░
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  wafer

  a flaking bead = particles on tools and neighbouring dies
"##;
const V64S: &[Spot] = &[
    spot(
        "edge bead (resist piles up)",
        0,
        0,
        "Surface tension piles resist at the rim after spinning.",
    ),
    spot(
        "wafer",
        0,
        0,
        "The bead sits at the wafer edge where clamps and handlers touch.",
    ),
    spot(
        "a flaking bead",
        0,
        TO_EOL,
        "Can flake off, contaminate tools, and interfere with scanner handling and clamping.",
    ),
];

const V65: &str = r##"
# Rim bands, edge of the wafer to the centre

  edge ┤ EBR band: ~1-5 mm (patents)
       ┤ vendor edge exclusion: 3.0 mm (SVMI)
       ▼
   active area: dies

  both are partial-die territory: edge yield loss
"##;
const V65S: &[Spot] = &[
    spot(
        "EBR band: ~1-5 mm",
        0,
        TO_EOL,
        "Patents describe the EBR annulus as generally 1 to 5 mm wide.",
    ),
    spot(
        "vendor edge exclusion: 3.0 mm",
        0,
        TO_EOL,
        "SVMI 300 mm datasheets: 3.0 mm edge exclusion.",
    ),
    spot(
        "active area: dies",
        0,
        0,
        "Good die are expected right up to the edge, so edge defects matter.",
    ),
    spot(
        "edge yield loss",
        0,
        0,
        "Partial dies already suffer at the edge (textbook).",
    ),
];

const V66: &str = r##"
# Before and after the bake

  ┌──────────────────┐                   ┌────────────────┐
  │ polymer + PAG    │                   │ polymer + PAG  │
  │ + lots of solvent│ ──▶ hot plate ──▶ │ (solvent gone) │
  └──────────────────┘                   └────────────────┘

  90-110 C, a few minutes (patent text)
  TEL Mark 8 example: 60 s at 110 C
"##;
const V66S: &[Spot] = &[
    spot(
        "polymer + PAG",
        0,
        0,
        "The liquid resist is mostly solvent when dispensed.",
    ),
    spot(
        "hot plate",
        0,
        0,
        "Drives off solvent, densifies the film, improves adhesion, stabilises exposure response.",
    ),
    spot("90-110 C", 0, TO_EOL, "Typical window from patent text."),
    spot(
        "TEL Mark 8 example",
        0,
        TO_EOL,
        "Baked 60 s at 110 C and used 1500-4000 rpm to reach a 280 nm film.",
    ),
];

const V67: &str = r##"
# Bake window

  too cool   residual solvent: outgasses, thickness shifts
  90-110 C   window: solvent out, PAG intact
  too hot    PAG damaged, dissolution shifts

  hot plate uniformity -> linewidth uniformity
"##;
const V67S: &[Spot] = &[
    spot(
        "too cool",
        0,
        TO_EOL,
        "Textbook: under-bake leaves residual solvent that outgasses in the scanner and evaporates unevenly.",
    ),
    spot(
        "90-110 C",
        0,
        TO_EOL,
        "The acid generator survives this bake intact.",
    ),
    spot(
        "too hot",
        0,
        TO_EOL,
        "Textbook: over-bake changes dissolution and sensitivity.",
    ),
    spot(
        "hot plate uniformity",
        0,
        TO_EOL,
        "Plate temperature uniformity maps to linewidth uniformity (textbook).",
    ),
];

const V68: &str = r##"
# Temperature path

  hot plate ▓▓▓▓▓▓▓ ~110 C (example bake)
      │
      ▼
  chill plate ▒▒▒ ──▶ room temperature ──▶ scanner

  warm wafer: thickness, chemistry, alignment all drift
"##;
const V68S: &[Spot] = &[
    spot(
        "hot plate",
        0,
        TO_EOL,
        "The soft bake temperature example is 110 C.",
    ),
    spot(
        "chill plate",
        0,
        TO_EOL,
        "Returns the wafer to room temperature (textbook).",
    ),
    spot(
        "warm wafer",
        0,
        TO_EOL,
        "Changes resist thickness and chemistry and distorts the wafer when the scanner measures it.",
    ),
];

const V69: &str = r##"
# Track modules, stacked

  ┌───────────────┐   robot
  │ COOL          │◀──────┐
  │ BAKE          │       │ shuttles wafers
  │ COAT          │       │ between modules
  └───────────────┘───────┘
     │ hands off to the SCANNER

  scheduling software keeps wafers from waiting too long
"##;
const V69S: &[Spot] = &[
    spot(
        "COOL",
        0,
        0,
        "Cooling modules are stacked vertically to save floor space.",
    ),
    spot(
        "robot",
        0,
        0,
        "Robot arms shuttle the wafer between modules.",
    ),
    spot(
        "hands off to the SCANNER",
        0,
        0,
        "The track is inline with the scanner and must match its wafers-per-hour.",
    ),
    spot(
        "scheduling software",
        0,
        TO_EOL,
        "Textbook; wait-time limits are not sourced here.",
    ),
];

const V70: &str = r##"
# Nozzle tip

     from pump + filter
           │
      ┌────┴────┐
      │ NOZZLE  │  ◀── suck-back pulls the meniscus up
      └────┬────┘      so resist does not dry at the tip
           ▼ metered drop
"##;
const V70S: &[Spot] = &[
    spot(
        "from pump + filter",
        0,
        0,
        "Metering and filtration upstream set drop volume and cleanliness.",
    ),
    spot(
        "suck-back",
        0,
        0,
        "A standard countermeasure against dried resist crusting at the tip (textbook).",
    ),
    spot(
        "metered drop",
        0,
        0,
        "Volume and timing set thickness uniformity and cost per wafer.",
    ),
];

const V71: &str = r##"
# Where the nozzle goes

  today    dispense ──▶ spin ──▶ bake        (nozzle, spin cup)
  dry      vacuum deposit ──▶ expose ──▶ dry develop

  Lam: homogeneous metal oxide network
  SPIE report: < 10 particles per 300 mm wafer (lab)
"##;
const V71S: &[Spot] = &[
    spot(
        "today",
        0,
        TO_EOL,
        "The wet process with nozzle, spin cup and bake.",
    ),
    spot(
        "dry",
        0,
        TO_EOL,
        "Dry deposition and dry development remove the nozzle and the wet developer.",
    ),
    spot(
        "Lam: homogeneous metal oxide network",
        0,
        0,
        "Lam's description of the dry resist.",
    ),
    spot("SPIE report", 0, TO_EOL, "Lab result, not production."),
];

const V72: &str = r##"
# Spin chuck cross-section

  ═══════════════ wafer ═══════════════
        ┌───────────┐
        │   CHUCK   │ ◀── holds the wafer by backside vacuum
        └─────┬─────┘
              │ spindle: a few thousand rpm
              ▼ motor + vacuum line
"##;
const V72S: &[Spot] = &[
    spot(
        "wafer",
        0,
        0,
        "A bowed or warped wafer can leak vacuum and wobble (textbook).",
    ),
    spot(
        "CHUCK",
        0,
        0,
        "Concentricity, seal and flatness of the chuck couple into film uniformity.",
    ),
    spot(
        "backside vacuum",
        0,
        0,
        "Holds the wafer without touching the top face.",
    ),
    spot(
        "spindle: a few thousand rpm",
        0,
        0,
        "The motor ramps the wafer to the spin speed.",
    ),
];

const V73: &str = r##"
# Backside particles travel

  ┌────────────────────┐   ┌────────────────┐   ┌──────────────────┐
  │ CHUCK              │   │ WAFER          │   │ SCANNER STAGE    │
  │ backside particle  │──▶│ particle moves │──▶│ focus defect     │
  └────────────────────┘   └────────────────┘   └──────────────────┘

  incoming spec: 775 +/- 25 um, TTV 5 um or less, 3.0 mm edge excl.
"##;
const V73S: &[Spot] = &[
    spot(
        "CHUCK",
        0,
        0,
        "Backside particles from the chuck transfer onto the wafer.",
    ),
    spot("WAFER", 0, 0, "Carries the particle to the next tool."),
    spot(
        "SCANNER STAGE",
        0,
        0,
        "Backside particles there cause focus defects.",
    ),
    spot(
        "incoming spec",
        0,
        TO_EOL,
        "SVMI 300 mm datasheets: 775 +/- 25 um, TTV 5 um or less, 3.0 mm edge exclusion.",
    ),
];

const V74: &str = r##"
# Rim trim on the spinning wafer

                 ┌────────┐
                 │EBR     │ solvent, rim only
                 └───┬────┘
                     ▼
  ░░░░░░░░░░░░░░░░░░░▒▒▒  ◀ bead dissolved here
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ wafer
"##;
const V74S: &[Spot] = &[
    spot("EBR", 0, 0, "A solvent nozzle aimed at the rim only."),
    spot(
        "solvent, rim only",
        0,
        0,
        "Solvent choice, flow and distance from the edge are set per resist (textbook).",
    ),
    spot(
        "bead dissolved here",
        0,
        0,
        "The band is typically 1 to 5 mm wide (patents).",
    ),
];

const V75: &str = r##"
# Three outcomes

  too little   ▒▒▒▒░░░  bead left, peels, makes particles
  just right   ░░░░░░░  clean rim, active area untouched
  too much     ░░ ░░░░  solvent wicks inward, edge dies ruined

  (cheap module, outsized edge-yield impact; no defect rates sourced)
"##;
const V75S: &[Spot] = &[
    spot("too little", 0, TO_EOL, "Leaves a bead that peels."),
    spot("just right", 0, TO_EOL, "Rim trimmed, active area intact."),
    spot(
        "too much",
        0,
        TO_EOL,
        "Solvent wicks inward and ruins edge dies.",
    ),
    spot(
        "(cheap module",
        0,
        0,
        "Textbook; no defect rates found in sources.",
    ),
];

const V76: &str = r##"
# Resist ingredients

  POLYMER   the backbone of the film
  PAG       photo-acid generator: releases acid under exposure
  QUENCHER  base: limits how far the acid reaches
  SOLVENT   PGMEA is common: most of the liquid,
            most of it leaves in the soft bake

  liquid: mostly solvent    baked film: polymer + PAG
"##;
const V76S: &[Spot] = &[
    spot("POLYMER", 0, TO_EOL, "The backbone of the film."),
    spot(
        "PAG",
        0,
        TO_EOL,
        "The photo-acid generator releases acid under exposure.",
    ),
    spot(
        "QUENCHER",
        0,
        TO_EOL,
        "A base; its concentration and uniformity matter for roughness and defects (2024 review).",
    ),
    spot(
        "SOLVENT",
        0,
        TO_EOL,
        "PGMEA is common; it is most of the liquid as dispensed.",
    ),
];

const V77: &str = r##"
# Amplification chain

  photon ──▶ PAG ──▶ acid ──(PEB heat)──▶ many polymer sites changed
                      │
                      └ quencher base limits the spread

  suppliers: JSR, TOK, Shin-Etsu, Sumitomo Chemical (textbook)
"##;
const V77S: &[Spot] = &[
    spot(
        "photon",
        0,
        0,
        "The exposure photon converts a PAG molecule into acid.",
    ),
    spot(
        "acid",
        0,
        0,
        "In a chemically amplified resist the acid catalyses a solubility change during the post-exposure bake.",
    ),
    spot(
        "quencher base limits the spread",
        0,
        0,
        "Quencher and PAG distribution and PEB temperature are critical for roughness and defects (2024 review).",
    ),
    spot(
        "suppliers: JSR",
        0,
        TO_EOL,
        "Textbook; no share figure sourced. SemiAnalysis has a note on the Lam, TEL and JSR resist battle.",
    ),
];

const V78: &str = r##"
# Few photons caught per pixel

  incoming     ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
  absorbed     ● (about 1 in 10)
  result       random counts: shot noise

  stochastic defects: line roughness, missing or merged features
  1 nm error on a 20 nm film = 5%
"##;
const V78S: &[Spot] = &[
    spot("incoming", 0, TO_EOL, "EUV photons reaching the resist."),
    spot(
        "absorbed",
        0,
        TO_EOL,
        "About 10% are absorbed in a ~20 nm film.",
    ),
    spot(
        "shot noise",
        0,
        0,
        "Random photon counts cause stochastic defects.",
    ),
    spot(
        "stochastic defects",
        0,
        TO_EOL,
        "Line roughness and missing or merged features.",
    ),
    spot("1 nm error on a 20 nm film = 5%", 0, 0, "Page arithmetic."),
];

const V79: &str = r##"
# Three routes to fewer stochastic defects

  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐
  │ CHEMICALLY   │  │ METAL OXIDE   │  │ DRY (Lam)       │
  │ AMPLIFIED    │  │ (Inpria)      │  │ vacuum deposit  │
  │ random components│  │ P28 single exp.│  │ dose/rough/defect│
  └──────────────┘  └───────────────┘  └─────────────────┘

  (P28 on 0.33 NA is a lab result)
"##;
const V79S: &[Spot] = &[
    spot(
        "CHEMICALLY",
        0,
        0,
        "Random component distribution adds to stochastics.",
    ),
    spot(
        "METAL OXIDE",
        0,
        0,
        "Positioned to improve resolution, sensitivity and stochastic defects.",
    ),
    spot(
        "P28 single exp.",
        0,
        0,
        "A study reports single-exposure P28 with Inpria MOx on a 0.33 NA scanner (lab).",
    ),
    spot(
        "DRY (Lam)",
        0,
        0,
        "Aims to break the dose, roughness and defect trade-off.",
    ),
];

const V80: &str = r##"
# TEL coater/developer share

  all, CY2025   ██████████████████████████████ 91%
  EUV-attached  █████████████████████████████████ ~100%

  Feb 2026 call: more than 90% global share
  treat 80-100% as near-monopoly (figures conflict)
"##;
const V80S: &[Spot] = &[
    spot(
        "all, CY2025",
        0,
        TO_EOL,
        "91% for CY2025 per Envalith; a Feb 2026 call describes more than 90%.",
    ),
    spot(
        "EUV-attached",
        0,
        TO_EOL,
        "TrendForce (Oct 2025), citing Nikkan Kogyo: 100% of coater/developers used with EUV scanners. Approximate.",
    ),
    spot("Feb 2026 call", 0, TO_EOL, "Earnings-call transcript."),
    spot(
        "treat 80-100%",
        0,
        TO_EOL,
        "Share figures conflict across aggregators.",
    ),
];

const V81: &str = r##"
# One inline system

  ┌──────────────────────┐    ┌───────────────┐
  │ TEL track            │    │ ASML scanner  │
  │ coat, bake, develop  │◀──▶│ expose        │
  └──────────────────────┘    └───────────────┘

  a TEL outage stalls the scanner next to it
  TrendForce: TEL net profit expected down, FY to Mar 2026
"##;
const V81S: &[Spot] = &[
    spot(
        "TEL track",
        0,
        0,
        "Coats, bakes and develops, inline with the scanner.",
    ),
    spot(
        "ASML scanner",
        0,
        0,
        "Exposure happens in between coat and develop.",
    ),
    spot(
        "a TEL outage stalls the scanner",
        0,
        0,
        "Inline integration means the track and scanner run as one system.",
    ),
    spot(
        "TrendForce: TEL net profit",
        0,
        TO_EOL,
        "TrendForce reported expected net profit to fall for the fiscal year ending March 2026.",
    ),
];

const V82: &str = r##"
# Coater/developer sales (aggregator, not audited)

  TEL + SCREEN  ████████████████████████████████████████████ ~88%
  everyone else ██████ ~12%

  others: SUSS MicroTec, Tazmo, Kingsemi, Litho Tech Japan, SEMES
"##;
const V82S: &[Spot] = &[
    spot(
        "TEL + SCREEN",
        0,
        TO_EOL,
        "About 88% combined by an industry overview (aggregator, not audited).",
    ),
    spot(
        "everyone else",
        0,
        TO_EOL,
        "The remainder, split among smaller makers.",
    ),
    spot(
        "others: SUSS MicroTec",
        0,
        TO_EOL,
        "Names from market listings; SEMES supplies Korean tracks, no share figure found.",
    ),
];

const V83: &str = r##"
# Duopoly and challengers

  ┌──────┐  ┌────────┐
  │ TEL  │  │ SCREEN │
  └──────┘  └────────┘
      ▲
      │ challengers: Kingsemi (China), SUSS, Tazmo

  one outage or export action hits the whole industry
"##;
const V83S: &[Spot] = &[
    spot("TEL", 0, 0, "The dominant maker."),
    spot(
        "SCREEN",
        0,
        0,
        "The only scaled alternative; natural second source on non-EUV layers.",
    ),
    spot(
        "challengers: Kingsemi",
        0,
        TO_EOL,
        "China's domestic efforts are the main long-term challenger; no sourced figures.",
    ),
    spot(
        "one outage or export action",
        0,
        TO_EOL,
        "The page's duopoly risk.",
    ),
];

const V84: &str = r##"
# Wafer from above

         ╱ ╱ ╱ ╱  radial streaks (striations)
      ╭───────────╮
     │    ●─────── │  ● particle, ─── its comet tail
     │  ╱ ╱ ╱ ╱   │
      ╰───────────╯

  cause: dried particles or bubbles in the dispense line
"##;
const V84S: &[Spot] = &[
    spot(
        "radial streaks (striations)",
        0,
        0,
        "Radial streaks in the film.",
    ),
    spot(
        "● particle",
        0,
        0,
        "A comet is a tail behind a particle or bubble.",
    ),
    spot(
        "cause: dried particles or bubbles",
        0,
        TO_EOL,
        "Originate in the dispense line (page).",
    ),
];

const V85: &str = r##"
# Cause to consequence

  particle or bubble ──▶ thickness error ──▶ pattern defect

  fixes:  point-of-use filter | bubble-free pump | clean room
  dry resist avoids spin defects (Lam, lab: < 10 particles)
"##;
const V85S: &[Spot] = &[
    spot("particle or bubble", 0, 0, "Starts in the dispense line."),
    spot(
        "thickness error",
        0,
        0,
        "A local thickness error turns into a pattern defect after exposure and development.",
    ),
    spot(
        "fixes:",
        0,
        TO_EOL,
        "Textbook countermeasures; point-of-use filter optimisation is an active SPIE topic.",
    ),
    spot(
        "dry resist avoids spin defects",
        0,
        TO_EOL,
        "Lab result from Lam via SPIE.",
    ),
];

const V86: &str = r##"
# Knobs that move thickness

  temperature ┐
  humidity    ├──▶ solvent evaporation rate ──▶ FILM THICKNESS
  spin speed  ┤
  spin time   ┘

  thickness ──▶ exposure dose ──▶ linewidth at the scanner
"##;
const V86S: &[Spot] = &[
    spot("temperature", 0, 0, "Shifts solvent evaporation rate."),
    spot("humidity", 0, 0, "Also shifts evaporation (page)."),
    spot(
        "FILM THICKNESS",
        0,
        0,
        "Controlled airflow and chemistry are managed together to hold it.",
    ),
    spot(
        "linewidth at the scanner",
        0,
        0,
        "Thickness changes the dose needed, so drift appears as linewidth variation (textbook).",
    ),
];

const V87: &str = r##"
# Slope of AZ 4533 thickness vs speed (arithmetic)

  2000 -> 4000 rpm   -0.7 um   ~ -0.35 um per 1000 rpm
  4000 -> 6000 rpm   -1.0 um   ~ -0.50 um per 1000 rpm

  thick resist, MEMS-class: not an EUV film
  at 20 nm, a 1 nm error is already 5%
"##;
const V87S: &[Spot] = &[
    spot(
        "2000 -> 4000 rpm",
        0,
        TO_EOL,
        "From 4.0 um to 3.3 um: slope about 0.35 um per 1000 rpm (arithmetic here).",
    ),
    spot(
        "4000 -> 6000 rpm",
        0,
        TO_EOL,
        "From 3.3 um to 2.3 um: about 0.5 um per 1000 rpm (arithmetic here).",
    ),
    spot(
        "thick resist, MEMS-class",
        0,
        TO_EOL,
        "These are thick-resist numbers; thin DUV and EUV films are tighter in absolute terms.",
    ),
    spot("at 20 nm, a 1 nm error", 0, 0, "Page arithmetic."),
];

const V88: &str = r##"
# Emission and mirror line up

  tin plasma emission        ░░░░▒▒██▒▒░░░░
  Mo/Si mirror reflectivity     ░▒▒██▒▒░
                                    ▲
                                13.5 nm

  no practical laser or lamp makes 13.5 nm directly
"##;
const V88S: &[Spot] = &[
    spot(
        "tin plasma emission",
        0,
        TO_EOL,
        "Highly ionised tin ions radiate strongly in a band around 13.5 nm (textbook).",
    ),
    spot(
        "Mo/Si mirror reflectivity",
        0,
        TO_EOL,
        "Molybdenum/silicon multilayer mirrors reflect best around the same wavelength (textbook).",
    ),
    spot("13.5 nm", 0, 0, "About 92 eV per photon."),
    spot(
        "no practical laser or lamp",
        0,
        TO_EOL,
        "Which is why a plasma is used.",
    ),
];

const V89: &str = r##"
# Droplet stream across the source vessel

  DROPLET GENERATOR ──▶  ●   ●   ●   ●   ●   ~25 um, ~50 kHz
                                  │
                                  ▼  laser hits each drop
                              ✺ plasma + tin vapour, ions, fragments
                                  ╲ debris flies toward the optics

  fix: hydrogen flow; the collector is a consumable
"##;
const V89S: &[Spot] = &[
    spot(
        "DROPLET GENERATOR",
        0,
        0,
        "Fires a stream of tiny tin drops across the source vessel.",
    ),
    spot(
        "~25 um, ~50 kHz",
        0,
        0,
        "Droplet size on the page; the drive laser is pulsed at 50 kHz (Laser Focus World).",
    ),
    spot(
        "laser hits each drop",
        0,
        0,
        "Every drop must be hit at the right place and moment, tens of thousands of times a second.",
    ),
    spot(
        "debris flies toward the optics",
        0,
        0,
        "Tin vapour, ions and fragments from every pulse.",
    ),
    spot(
        "fix: hydrogen flow",
        0,
        TO_EOL,
        "Hydrogen flow keeps the collector cleaner but does not eliminate contamination.",
    ),
];

const V90: &str = r##"
# Pre-pulse then main pulse

  ┌──────────────┐   ┌─────────────────────┐   ┌────────────────────┐
  │ 1  ●         │   │ 2  PRE-PULSE        │   │ 3  CO2 MAIN        │
  │ ~30 um drop  │──▶│ flattens to >100 um │──▶│ 10.6 um, 15-25 ns  │
  └──────────────┘   │ pancake / mist      │   │ plasma             │
                     └─────────────────────┘   └────────────────────┘

  Cymer (2013): about 2x conversion efficiency, aimed at 250 W
"##;
const V90S: &[Spot] = &[
    spot("1  ●", 0, 0, "The original droplet, roughly 30 um."),
    spot(
        "2  PRE-PULSE",
        0,
        0,
        "A low-intensity pulse reshapes the drop into a pancake or mist, over 100 um across.",
    ),
    spot(
        "3  CO2 MAIN",
        0,
        0,
        "The 10.6 um main pulse hits a larger, better-matched target.",
    ),
    spot(
        "Cymer (2013)",
        0,
        TO_EOL,
        "Said pre-pulse would give about a 2x conversion-efficiency improvement, aimed at 250 W.",
    ),
];

const V91: &str = r##"
# Conversion efficiency, % of laser light to in-band EUV

  ASML-type LPP   ██████████████████████ ~5-6 (page)
  Gigaphoton peak █████████████████████ 5.2 (150 mJ CO2)
  solid-state 2018█████████████ 3.2 (paper)

  drive laser: > 20 kW, 50 kHz, built by TRUMPF (textbook)
"##;
const V91S: &[Spot] = &[
    spot(
        "ASML-type LPP",
        0,
        TO_EOL,
        "The page quotes about 5-6% of laser light into in-band EUV.",
    ),
    spot(
        "Gigaphoton peak",
        0,
        TO_EOL,
        "Reported a peak 5.2% with 150 mJ CO2 pulses; not in ASML scanners.",
    ),
    spot(
        "solid-state 2018",
        0,
        TO_EOL,
        "A 2018 paper showed 3.2% with solid-state lasers.",
    ),
    spot(
        "drive laser",
        0,
        TO_EOL,
        "More than 20 kW at only a few percent efficiency, pulsed at 50 kHz (Laser Focus World). TRUMPF is textbook, not sourced here.",
    ),
];

const V92: &str = r##"
# Where the laser energy goes

  laser in  ██████████████████████████████████████ 100%
  13.5 nm   ██ ~5-6% in-band EUV (page)
  the rest  heat and out-of-band light (textbook)

  plasma: ~100 um across, electron temperature 20-50 eV
"##;
const V92S: &[Spot] = &[
    spot(
        "laser in",
        0,
        TO_EOL,
        "CO2 main pulse energy delivered to the target.",
    ),
    spot(
        "13.5 nm",
        0,
        TO_EOL,
        "Only about 5 to 6 percent ends up as usable in-band EUV.",
    ),
    spot(
        "the rest",
        0,
        TO_EOL,
        "Lost as heat and out-of-band light, which is why the collector and vessel need heavy thermal management (textbook).",
    ),
    spot("plasma: ~100 um across", 0, TO_EOL, "Per the page."),
];

const V93: &str = r##"
# EUV source power, watts

  210 W demo    ████████ 210 (2015-16)
  current tools ██████████ ~250 at IF
  NXE:3800E     ████████████████████ 500 (ASML)

  more watts = same dose in less time = more wafers per hour
"##;
const V93S: &[Spot] = &[
    spot(
        "210 W demo",
        0,
        TO_EOL,
        "210 W for one hour on a modified NXE:3300B in 2015-2016.",
    ),
    spot(
        "current tools",
        0,
        TO_EOL,
        "About 250 W at the intermediate focus (Wikipedia).",
    ),
    spot(
        "NXE:3800E",
        0,
        TO_EOL,
        "A 500 W source (ASML, Nov 2024), reaching 220 wafers per hour.",
    ),
    spot(
        "more watts",
        0,
        TO_EOL,
        "Source power is the throughput limit of the whole machine.",
    ),
];

const V94: &str = r##"
# Collector and plasma

        ╭──────────────────────╮
       ╱   COLLECTOR (ellipse)  ╲
      │          ✺ plasma        │──▶ to intermediate focus
       ╲    tin debris ↑↑↑      ╱
        ╰──── H2 flow ────────╯

  H2 + tin -> stannane SnH4, pumped away (patent)
"##;
const V94S: &[Spot] = &[
    spot(
        "COLLECTOR (ellipse)",
        0,
        0,
        "A large ellipsoidal Mo/Si multilayer mirror ringed around the plasma.",
    ),
    spot(
        "✺ plasma",
        0,
        0,
        "The emitter sits at the first focus of the ellipse.",
    ),
    spot(
        "tin debris",
        0,
        0,
        "Deposited tin is the dominant contamination mechanism (patent).",
    ),
    spot(
        "H2 flow",
        0,
        0,
        "Hydrogen reacts with tin to form stannane (SnH4), which is pumped away, but does not fully prevent contamination.",
    ),
    spot(
        "to intermediate focus",
        0,
        0,
        "The ellipse's second focus, where the beam enters the scanner.",
    ),
];

const V95: &str = r##"
# The collector lifecycle

  new mirror ──▶ billions of pulses ──▶ reflectivity falls
       ▲                                      │
       └─ remove, clean or replace (downtime) ┘

  research: in-situ tin removal by surface-wave plasma,
  etch rate 20x the contamination rate (Qerimi 2022)
"##;
const V95S: &[Spot] = &[
    spot(
        "billions of pulses",
        0,
        0,
        "The page says the collector loses reflectivity over billions of pulses.",
    ),
    spot(
        "remove, clean or replace (downtime)",
        0,
        0,
        "Standard practice; downtime hits scanner availability.",
    ),
    spot(
        "research: in-situ tin removal",
        0,
        TO_EOL,
        "Academic work (Qerimi et al., 2022), not a product.",
    ),
    spot(
        "etch rate 20x the contamination rate",
        0,
        0,
        "The reported ratio for the surface-wave plasma technique.",
    ),
];

const V96: &str = r##"
# Power along the light path

  ┌───────────┐  ┌─────────┐  ┌─────────────────┐  ┌─────────┐
  │ SOURCE    │  │ IF      │  │ SCANNER         │  │ WAFER   │
  │ collector │─▶│ ~250 W  │─▶│ illuminator,    │─▶│ ~1 W    │
  └───────────┘  └─────────┘  │ reticle, mirrors│  └─────────┘
                              └─────────────────┘

  the page's budget: ~100 W in, ~1 W at the wafer
  'at IF' vs 'at wafer' differ by roughly 100x
"##;
const V96S: &[Spot] = &[
    spot("SOURCE", 0, 0, "The light-source module."),
    spot(
        "IF",
        0,
        0,
        "Power is quoted here: about 250 W in current tools.",
    ),
    spot(
        "SCANNER",
        0,
        0,
        "Everything downstream can only lose light.",
    ),
    spot(
        "WAFER",
        0,
        0,
        "Roughly 1 W at the wafer from 100 W in (page budget).",
    ),
    spot(
        "'at IF' vs 'at wafer'",
        0,
        TO_EOL,
        "Read power claims carefully; they differ by roughly 100x.",
    ),
];

const V97: &str = r##"
# The IF as a filter

  source side           IF           scanner side
  tin debris ──▶ ╲      │      ╱ ──▶ clean EUV only
  10.6 um CO2 ──▶  ╲  ▌ ▐  ╱
                    small aperture

  gas flow + vacuum separation keep the scanner clean
"##;
const V97S: &[Spot] = &[
    spot(
        "tin debris",
        0,
        TO_EOL,
        "Debris from the source vessel is blocked at the small aperture (textbook).",
    ),
    spot(
        "10.6 um CO2",
        0,
        TO_EOL,
        "Residual drive-laser light is blocked too.",
    ),
    spot("small aperture", 0, 0, "The pinch point (textbook)."),
    spot(
        "gas flow + vacuum separation",
        0,
        TO_EOL,
        "Keep the scanner clean from the contaminated source vessel (textbook).",
    ),
];

const V98: &str = r##"
# Illumination modes (pupil shapes)

   conventional        annular            dipole
     ▓▓▓▓▓▓           ▓▓▓▓▓▓▓▓           ▓▓      ▓▓
     ▓▓▓▓▓▓           ▓▓    ▓▓           ▓▓      ▓▓
     ▓▓▓▓▓▓           ▓▓▓▓▓▓▓▓           ▓▓      ▓▓

  mode tunes which diffraction orders reach the projection optics
"##;
const V98S: &[Spot] = &[
    spot(
        "conventional",
        0,
        0,
        "A filled disc of illumination angles.",
    ),
    spot("annular", 0, 0, "A ring of angles."),
    spot(
        "dipole",
        0,
        0,
        "Two opposing poles, used for dense lines in one direction.",
    ),
    spot(
        "mode tunes which diffraction orders",
        0,
        TO_EOL,
        "That tunes the achievable k1 in CD = k1 * lambda / NA (textbook).",
    ),
];

const V99: &str = r##"
# Light left after n reflections (0.70 each)

  1 mirror   ███████████████████████████████████ 70%
  2 mirrors  ████████████████████████ 49%
  4 mirrors  ████████████ 24%
  6 mirrors  ██████ 12%
  10 mirrors █ 2.8% (1.8% at 0.67)

  0.7^10 = 2.8%, 0.67^10 = 1.8%: the page's 'under 2%'
"##;
const V99S: &[Spot] = &[
    spot(
        "2 mirrors",
        0,
        TO_EOL,
        "Illuminator mirrors alone cut power to about half.",
    ),
    spot("6 mirrors", 0, TO_EOL, "Arithmetic here: 0.7^6 = 11.8%."),
    spot(
        "10 mirrors",
        0,
        TO_EOL,
        "About 10 reflections in total leave under 2 to 3%.",
    ),
    spot(
        "0.7^10 = 2.8%",
        0,
        TO_EOL,
        "Computed on the page; matches the under-2% patent figure at 0.67.",
    ),
];

const V100: &str = r##"
# Reticle cross-section

       ╲ light in     ╱ reflected, carries the pattern
        ╲            ╱
     ▓▓▓▓▓▓      ▓▓▓▓▓▓      ◀ Ta-based absorber (the pattern)
  ═══════════════════════════ Mo/Si multilayer mirror
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ substrate

  light arrives at an angle: tall absorbers cast shadows
"##;
const V100S: &[Spot] = &[
    spot(
        "Ta-based absorber",
        0,
        0,
        "Draws the pattern by absorbing light; tall features cast shadows (mask 3D effects, textbook).",
    ),
    spot(
        "Mo/Si multilayer mirror",
        0,
        0,
        "All materials absorb 13.5 nm light, so the reticle must be a mirror.",
    ),
    spot("light in", 0, 0, "Arrives at a small angle off the normal."),
    spot(
        "cast shadows",
        0,
        0,
        "Shift the printed pattern (textbook).",
    ),
];

const V101: &str = r##"
# Mask supply chain

  ┌──────────────────┐   ┌───────────┐   ┌───────────────────┐
  │ BLANK            │   │ PATTERN   │   │ INSPECT           │
  │ Hoya (textbook)  │──▶│ absorber  │──▶│ actinic, 13.5 nm  │
  └──────────────────┘   └───────────┘   └───────────────────┘

  inspectors named by Canatu: Lasertec, KLA, Applied, Zeiss
  Lasertec PELMIS EPM200 (Jul 2025): inspects CNT pellicles
"##;
const V101S: &[Spot] = &[
    spot("BLANK", 0, 0, "Hoya supplies mask blanks (textbook)."),
    spot(
        "INSPECT",
        0,
        0,
        "A defect buried in the multilayer prints on every die, so inspection is a yield gate.",
    ),
    spot(
        "inspectors named by Canatu",
        0,
        TO_EOL,
        "Sources disagree on how exclusive Lasertec is.",
    ),
    spot(
        "Lasertec PELMIS EPM200",
        0,
        TO_EOL,
        "Released July 2025 to inspect carbon-nanotube pellicles for particles.",
    ),
];

const V102: &str = r##"
# Pellicle over the reticle

    ● dust falls ──▶ lands on the membrane, out of focus
  ═══════════════════════  pellicle (thin membrane)
      ╎ gap ╎
  ▓▓▓▓▓▓      ▓▓▓▓▓▓    reticle pattern
  ══════════════════════

  EUV passes through twice: transmission 85-90% (NXE:3400B)
"##;
const V102S: &[Spot] = &[
    spot(
        "● dust falls",
        0,
        TO_EOL,
        "Particles land on the membrane, out of focus, instead of printing.",
    ),
    spot(
        "pellicle (thin membrane)",
        0,
        0,
        "Free-standing and extremely thin, since any solid absorbs EUV.",
    ),
    spot(
        "gap",
        0,
        0,
        "Keeps the particle plane away from the pattern plane.",
    ),
    spot(
        "transmission 85-90% (NXE:3400B)",
        0,
        0,
        "Per the page; ASML earlier reported 83% for a silicon-based pellicle (Bits&Chips, undated).",
    ),
];

const V103: &str = r##"
# Pellicle EUV transmission, %

  silicon (older) ████████████████████████████ 83 (ASML, undated)
  NXE:3400B       █████████████████████████████ 85-90
  CNT (imec)      ████████████████████████████████ > 95
  CNT (academic)  █████████████████████████████████ up to 99

  CNT risk: hydrogen radicals; needs ASML certification (Canatu)
"##;
const V103S: &[Spot] = &[
    spot(
        "silicon (older)",
        0,
        TO_EOL,
        "ASML earlier reported 83% for its silicon-based pellicle (Bits&Chips, undated).",
    ),
    spot(
        "NXE:3400B",
        0,
        TO_EOL,
        "85-90% transmission (page, Wikipedia).",
    ),
    spot(
        "CNT (imec)",
        0,
        TO_EOL,
        "Imec reports greater than 95% EUV transmission.",
    ),
    spot(
        "CNT (academic)",
        0,
        TO_EOL,
        "An academic abstract reports up to 99%.",
    ),
    spot(
        "CNT risk",
        0,
        TO_EOL,
        "Instability in the hydrogen radical environment; Canatu says ASML certification is required.",
    ),
];

const V104: &str = r##"
# Reticle to wafer through six mirrors

   RETICLE ▓
      ╲
       M1 ◀──▶ M2     the pattern zig-zags, 4x reduction
       M3 ◀──▶ M4     (each mirror: ~67-70% reflective)
       M5 ◀──▶ M6
                ╲
                 WAFER ▓
"##;
const V104S: &[Spot] = &[
    spot("RETICLE", 0, 0, "The reflective mask is the object plane."),
    spot(
        "M1 ◀──▶ M2",
        0,
        0,
        "Six mirrors in total for the 0.33 NA tools, 4x reduction.",
    ),
    spot(
        "(each mirror: ~67-70% reflective)",
        0,
        0,
        "About 30% of the light is lost at each mirror.",
    ),
    spot("WAFER", 0, 0, "The image lands here at 1/4 size."),
];

const V105: &str = r##"
# Exposure field, mm

  0.33 NA   ┌────────────────────┐  26 x 33
            │                    │
            │                    │
            └────────────────────┘
  0.55 NA   ┌────────────────────┐  26 x 16.5
            └────────────────────┘

  half the field = about 2x the exposures per wafer
"##;
const V105S: &[Spot] = &[
    spot("0.33 NA", 0, TO_EOL, "Full 26 x 33 mm field."),
    spot(
        "0.55 NA",
        0,
        TO_EOL,
        "Anamorphic 4x/8x optics, field 26 x 16.5 mm.",
    ),
    spot(
        "half the field",
        0,
        TO_EOL,
        "Roughly twice as many exposures per wafer, hurting throughput.",
    ),
];

const V106: &str = r##"
# Synchronised scanning

  RETICLE STAGE   ─────▶   scans this way
  WAFER STAGE     ◀─────   and this way (4x slower travel)

  resist (20 nm): absorbs ~10% of 13.5 nm light
  EUV photon density: ~1/14 of 193 nm ArF
"##;
const V106S: &[Spot] = &[
    spot("RETICLE STAGE", 0, TO_EOL, "Scans one way."),
    spot(
        "WAFER STAGE",
        0,
        TO_EOL,
        "Scans the opposite way, synchronised to the reticle.",
    ),
    spot(
        "resist (20 nm)",
        0,
        TO_EOL,
        "A 20 nm film absorbs only about 10% of EUV light.",
    ),
    spot(
        "EUV photon density",
        0,
        TO_EOL,
        "About 1/14 that of ArF at the same energy dose (research summaries).",
    ),
];

const V107: &str = r##"
# The dose trade-off

  more dose ──▶ fewer stochastic defects ──▶ but slower scanner
  less dose ──▶ more wafers per hour ──▶ but more defects

  smaller features: defect probability rises exponentially
  (Monte Carlo, JM3 2020)
"##;
const V107S: &[Spot] = &[
    spot(
        "more dose",
        0,
        TO_EOL,
        "More photons per feature reduce shot noise, but cost throughput.",
    ),
    spot(
        "less dose",
        0,
        TO_EOL,
        "Faster, but risks stochastic defects such as roughness and missing features.",
    ),
    spot(
        "smaller features",
        0,
        TO_EOL,
        "Defect probability rises exponentially as feature size shrinks (JM3, 2020 study).",
    ),
    spot(
        "(Monte Carlo, JM3 2020)",
        0,
        0,
        "Highly sensitive to process and mask conditions.",
    ),
];

const V108: &str = r##"
# Smallest feature, k1 = 0.33

  CD = k1 * lambda / NA

  0.33 NA   0.33 x 13.5 / 0.33 = 13.5 nm   (ASML: 13 nm)
  0.55 NA   0.33 x 13.5 / 0.55 =  8.1 nm   (ASML:  8 nm)

  DOF = k2 * lambda / NA^2
"##;
const V108S: &[Spot] = &[
    spot(
        "CD = k1 * lambda / NA",
        0,
        0,
        "Critical dimension: the smallest printable feature.",
    ),
    spot(
        "0.33 NA",
        0,
        TO_EOL,
        "13.5 nm on the page's arithmetic; ASML quotes 13 nm.",
    ),
    spot(
        "0.55 NA",
        0,
        TO_EOL,
        "8.1 nm on the page's arithmetic; ASML quotes 8 nm.",
    ),
    spot(
        "DOF = k2 * lambda / NA^2",
        0,
        0,
        "Depth of focus falls with the square of NA.",
    ),
];

const V109: &str = r##"
# Relative depth of focus

  0.33 NA  █████████████████████████ 1.0
  0.55 NA  █████████ 0.36 (2.8x smaller)

  consequence: thinner resist, flatter wafer, tighter focus
  throughput: EXE:5000 110 wafers/h vs NXE:3800E 220
"##;
const V109S: &[Spot] = &[
    spot("0.33 NA", 0, TO_EOL, "Reference depth of focus."),
    spot("0.55 NA", 0, TO_EOL, "(0.55/0.33)^2 = 2.8x smaller."),
    spot(
        "consequence",
        0,
        TO_EOL,
        "Thin resists absorb fewer photons, worsening stochastics.",
    ),
    spot(
        "throughput",
        0,
        TO_EOL,
        "EXE:5000 at 110 wafers per hour versus 220 for the NXE:3800E (page).",
    ),
];

const V110: &str = r##"
# Photon energy and count

  E = 1239.8 eV*nm / 13.5 nm = 91.8 eV   (ArF 193 nm: 6.4 eV)
  dose 30 mJ/cm2 / 91.8 eV  = 2.0e15 photons per cm2
                            = about 20 per nm2

  same energy in ArF: 14x more photons
"##;
const V110S: &[Spot] = &[
    spot("91.8 eV", 0, 0, "Photon energy at 13.5 nm."),
    spot(
        "ArF 193 nm: 6.4 eV",
        0,
        0,
        "About 14x lower energy per photon.",
    ),
    spot(
        "2.0e15 photons per cm2",
        0,
        0,
        "At the 30 mJ/cm2 reference dose (page arithmetic).",
    ),
    spot(
        "14x more photons",
        0,
        0,
        "Equal-energy ArF dose has 14x more photons, so EUV has 14x more shot noise.",
    ),
];

const V111: &str = r##"
# NXE:3600D throughput vs dose

  20 mJ/cm2   ████████████████████████████████████ 180 wafers/h
  30 mJ/cm2   ████████████████████████████████ 160 wafers/h

  lower dose = more wafers/h, but more stochastic defects
"##;
const V111S: &[Spot] = &[
    spot(
        "20 mJ/cm2",
        0,
        TO_EOL,
        "180 wafers per hour on the 3600D (ASML deck).",
    ),
    spot("30 mJ/cm2", 0, TO_EOL, "160 wafers per hour on the 3600D."),
    spot(
        "lower dose",
        0,
        TO_EOL,
        "Reports show a strong trade-off between sensitivity and defectivity.",
    ),
];

const V112: &str = r##"
# Wafers per hour

  NXE:3600D   ████████████████ 160
  NXE:3800E   ██████████████████████ 220 (+38%)
  NXE:3800F   ██████████████████████████ 260 (reported)

  3800E: 500 W source, overlay improved 13% (ASML)
"##;
const V112S: &[Spot] = &[
    spot("NXE:3600D", 0, TO_EOL, "160 wafers per hour at 30 mJ/cm2."),
    spot(
        "NXE:3800E",
        0,
        TO_EOL,
        "220 wafers per hour spec, +38% (ASML 6-K).",
    ),
    spot(
        "NXE:3800F",
        0,
        TO_EOL,
        "A reported figure from Tom's Hardware, not verified here.",
    ),
    spot(
        "3800E: 500 W source",
        0,
        TO_EOL,
        "Source and overlay figures from ASML.",
    ),
];

const V113: &str = r##"
# Energy per wafer pass, kWh

  ArF immersion ██ 0.45
  NXE:3400C     ████████████████████████████████ 9.64

  NXE:3400C draws 1.31 MW; tool ~200 tons; low-NA ~$180M
  (Wikipedia, AnandTech)
"##;
const V113S: &[Spot] = &[
    spot(
        "ArF immersion",
        0,
        TO_EOL,
        "0.45 kWh per wafer pass (Wikipedia).",
    ),
    spot(
        "NXE:3400C",
        0,
        TO_EOL,
        "9.64 kWh per wafer pass; about 21x ArF immersion (arithmetic here).",
    ),
    spot(
        "NXE:3400C draws 1.31 MW",
        0,
        TO_EOL,
        "Power draw; the tool weighs about 200 tons and low-NA costs about $180M.",
    ),
];

const V114: &str = r##"
# Tool price, $M

  low-NA EUV  ██████████████████ ~180
  High-NA EUV ███████████████████████████████████████ ~380-400

  throughput: 110 wafers/h now, target > 200 by 2030
"##;
const V114S: &[Spot] = &[
    spot(
        "low-NA EUV",
        0,
        TO_EOL,
        "About $180M (Wikipedia, AnandTech).",
    ),
    spot(
        "High-NA EUV",
        0,
        TO_EOL,
        "EUR 350M+, about $380-400M (reported).",
    ),
    spot(
        "throughput",
        0,
        TO_EOL,
        "110 wafers per hour on the page; target above 200 by 2030.",
    ),
];

const V115: &str = r##"
# The economic question

  ┌──────────────────────┐    ┌──────────────────────┐
  │ HIGH-NA              │    │ LOW-NA               │
  │ single patterning    │    │ multi-patterning     │
  │ half the throughput, │ vs │ more steps,          │
  │ double the price     │    │ cheaper tool         │
  └──────────────────────┘    └──────────────────────┘

  EXE:5200B: Intel acceptance testing, SK Hynix installing
  TSMC timing disputed: 2028 vs 2029-2030 or later
"##;
const V115S: &[Spot] = &[
    spot(
        "HIGH-NA",
        0,
        0,
        "Single patterning at roughly half the throughput and double the price.",
    ),
    spot("LOW-NA", 0, 0, "Multi-patterning on cheaper tools."),
    spot(
        "EXE:5200B",
        0,
        TO_EOL,
        "The production successor; search results show Intel acceptance testing and SK Hynix installation.",
    ),
    spot(
        "TSMC timing disputed",
        0,
        TO_EOL,
        "Press reports range from 2028 to 2029-2030 or later; 2028 looks like the outlier.",
    ),
];

const V116: &str = r##"
# ASML FY2025, EUR billion

  net sales     ██████████████████████ 32.7
  EUV sales     ████████ 11.6 (+39%, 48 systems)
  backlog       ██████████████████████████ 38.8
  EUV backlog   █████████████████ 25.5

  net income 9.6; EUV 48% of system sales (38% in 2024)
"##;
const V116S: &[Spot] = &[
    spot("net sales", 0, TO_EOL, "EUR 32.7B in FY2025."),
    spot(
        "EUV sales",
        0,
        TO_EOL,
        "EUR 11.6B, up 39%, from 48 EUV systems.",
    ),
    spot("backlog", 0, TO_EOL, "EUR 38.8B total."),
    spot("EUV backlog", 0, TO_EOL, "EUR 25.5B of the backlog is EUV."),
    spot(
        "net income 9.6",
        0,
        TO_EOL,
        "EUR 9.6B; EUV was 48% of net system sales versus 38% in 2024.",
    ),
];

const V117: &str = r##"
# Arithmetic on the filing numbers

  EUR 11.6B / 48 systems  = about EUR 242M per system
  EUR 25.5B / EUR 11.6B   = about 2.2 years of EUV sales

  risks: export controls on China, customer capex cycles,
         pricing friction (value-based pricing)
"##;
const V117S: &[Spot] = &[
    spot(
        "EUR 11.6B / 48 systems",
        0,
        TO_EOL,
        "Computed here; blends tool types and may include upgrades, so rough.",
    ),
    spot(
        "EUR 25.5B / EUR 11.6B",
        0,
        TO_EOL,
        "Computed here: about two years of visibility.",
    ),
    spot(
        "risks: export controls",
        0,
        TO_EOL,
        "Beyond the page: export controls, capex cycles, pricing friction.",
    ),
];

const V118: &str = r##"
# Who supplies what

  ┌────────────────┐  ┌─────────────┐  ┌────────────┐
  │ ASML           │  │ ZEISS SMT   │  │ TRUMPF     │
  │ scanner, Cymer │  │ mirrors     │  │ CO2 laser  │
  └────────────────┘  └─────────────┘  └────────────┘
  ┌───────────────┐  ┌─────────────┐  ┌────────┐
  │ LASERTEC      │  │ HOYA        │  │ TEL    │
  │ mask inspect  │  │ mask blanks │  │ track  │
  └───────────────┘  └─────────────┘  └────────┘

  (all textbook; Zeiss and TRUMPF are private)
"##;
const V118S: &[Spot] = &[
    spot("ASML", 0, 0, "The only EUV scanner vendor; owns Cymer."),
    spot(
        "ZEISS SMT",
        0,
        0,
        "Mirrors and illuminator optics; private, no ticker.",
    ),
    spot("TRUMPF", 0, 0, "Builds the CO2 drive laser (textbook)."),
    spot(
        "LASERTEC",
        0,
        0,
        "Actinic mask inspection; sources disagree on how exclusive it is.",
    ),
    spot("HOYA", 0, 0, "Mask blanks (textbook)."),
    spot("TEL", 0, 0, "Tracks that attach to the scanner."),
];

const V119: &str = r##"
# Ticker map

  ASML       ASML, ASML.AS
  Lasertec   6920.T
  Hoya       7741.T
  TEL        8035.T
  Zeiss, TRUMPF   private

  customers: TSMC, Samsung, SK Hynix, Intel, Micron
"##;
const V119S: &[Spot] = &[
    spot(
        "ASML       ASML",
        0,
        TO_EOL,
        "Scanner maker; listed in Amsterdam and New York.",
    ),
    spot("Lasertec", 0, TO_EOL, "Actinic mask inspection."),
    spot("Hoya", 0, TO_EOL, "Mask blanks."),
    spot(
        "TEL        8035.T",
        0,
        TO_EOL,
        "Tracks that attach to the scanner.",
    ),
    spot(
        "Zeiss, TRUMPF   private",
        0,
        TO_EOL,
        "No ticker, so exposure is only via ASML.",
    ),
    spot("customers: TSMC", 0, TO_EOL, "Customers named on the page."),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::diagrams_vis::check;

    #[test]
    fn all_group_b_visuals_resolve() {
        let all: &[(&str, &str, &str)] = &[
            ("WAFER", "POLISHED", "Prime wafer"),
            ("WAFER", "POLISHED", "Why it matters"),
            ("WAFER", "OPTIONAL", "Epitaxy"),
            ("WAFER", "OPTIONAL", "The upgrade ladder"),
            ("WAFER", "INSPECT", "What is checked"),
            ("WAFER", "INSPECT", "Why flatness gets attention"),
            ("WAFER", "PACK", "The FOUP"),
            ("WAFER", "PACK", "Who and why purge"),
            ("WAFER", "FAB", "Wafer quality is yield"),
            ("WAFER", "FAB", "Market tone 2026"),
            ("WAFER", "EPITAXIAL", "What epi is"),
            ("WAFER", "EPITAXIAL", "Demand signal"),
            ("WAFER", "SOI (silicon on insulator)", "Smart Cut steps"),
            ("WAFER", "SOI (silicon on insulator)", "What you get"),
            ("WAFER", "TTV", "Definition and spec"),
            ("WAFER", "TTV", "Commodity vs leading edge"),
            ("WAFER", "SFQR", "What it measures"),
            ("WAFER", "SFQR", "The catch"),
            ("WAFER", "Shin-Etsu", "Position"),
            ("WAFER", "Shin-Etsu", "2026 commentary"),
            ("WAFER", "2025 revenue", "Area up, revenue down"),
            ("WAFER", "2025 revenue", "Why price per area fell"),
            ("WAFER", "long qualification", "Why switching is slow"),
            ("WAFER", "long qualification", "Supply picture"),
            ("WAFER", "SUMCO", "Position"),
            ("WAFER", "SUMCO", "Concentration risk"),
            ("DEPOSIT", "GAS / TARGET", "Three kinds of source"),
            ("DEPOSIT", "GAS / TARGET", "Precursors as a chokepoint"),
            ("DEPOSIT", "CHAMBER", "Process windows"),
            ("DEPOSIT", "CHAMBER", "Batch vs single wafer"),
            ("DEPOSIT", "FILM", "How films are judged"),
            ("DEPOSIT", "FILM", "Conformality is the AI-era requirement"),
            ("DEPOSIT", "PUMP", "By-products out"),
            ("DEPOSIT", "PUMP", "Where service revenue comes from"),
            ("DEPOSIT", "CMP/ETCH", "The repeat loop"),
            ("DEPOSIT", "CMP/ETCH", "Copper side"),
            ("DEPOSIT", "SHOWERHEAD", "Spreading the gas"),
            ("DEPOSIT", "SHOWERHEAD", "Who"),
            ("DEPOSIT", "HEATED PEDESTAL", "Temperature sets rate"),
            ("DEPOSIT", "HEATED PEDESTAL", "Failure mode"),
            ("DEPOSIT", "1 PULSE A", "The ALD cycle"),
            ("DEPOSIT", "1 PULSE A", "Cycle numbers"),
            ("DEPOSIT", "1 PULSE A", "Business"),
            ("DEPOSIT", "TARGET (Ta, Ti, Cu)", "Sputtering"),
            ("DEPOSIT", "TARGET (Ta, Ti, Cu)", "Where it is used"),
            ("DEPOSIT", "TEOS SiO2", "The reaction"),
            ("DEPOSIT", "TEOS SiO2", "Speed vs density"),
            ("DEPOSIT", "Tungsten fill", "Reaction and sequence"),
            ("DEPOSIT", "Tungsten fill", "What replaces it"),
            ("DEPOSIT", "ASM International", "FY2025"),
            ("DEPOSIT", "ASM International", "Mix and risks"),
            ("DEPOSIT", "Mo ALD", "Why swap metals"),
            ("DEPOSIT", "Mo ALD", "Hurdle"),
            ("DEPOSIT", "Applied Materials", "FY2025 segment"),
            ("DEPOSIT", "Applied Materials", "Products and share"),
            ("DEPOSIT", "Kokusai Electric", "Position"),
            ("DEPOSIT", "Kokusai Electric", "Recent numbers"),
            ("COAT", "PRIME+BARC", "Primer and BARC"),
            ("COAT", "PRIME+BARC", "Thin-film pressure"),
            ("COAT", "DISPENSE", "Dispense"),
            ("COAT", "DISPENSE", "Defects and dry resist"),
            ("COAT", "SPIN", "Spin physics"),
            ("COAT", "SPIN", "Recipe numbers"),
            ("COAT", "EDGE BEAD", "Why the rim piles up"),
            ("COAT", "EDGE BEAD", "Scale"),
            ("COAT", "SOFT BAKE", "What the bake does"),
            ("COAT", "SOFT BAKE", "Why the temperature is bounded"),
            ("COAT", "COOL", "Chill plate"),
            ("COAT", "COOL", "Track keeps pace"),
            ("COAT", "NOZZLE", "Dispense control"),
            ("COAT", "NOZZLE", "Direction of travel"),
            ("COAT", "CHUCK", "Vacuum chuck"),
            ("COAT", "CHUCK", "Link to wafer specs"),
            ("COAT", "EBR nozzle", "Rim-only solvent"),
            ("COAT", "EBR nozzle", "Cost of getting it wrong"),
            ("COAT", "PGMEA", "What is in resist"),
            ("COAT", "PGMEA", "Chemical amplification"),
            ("COAT", "EUV film", "Thin film, few photons"),
            ("COAT", "EUV film", "Industry response"),
            ("COAT", "Tokyo Electron", "Position"),
            ("COAT", "Tokyo Electron", "Why it matters"),
            ("COAT", "SCREEN Holdings", "Number two"),
            ("COAT", "SCREEN Holdings", "Risk"),
            ("COAT", "striations / comets", "What they are"),
            ("COAT", "striations / comets", "Impact and fixes"),
            ("COAT", "thickness drift", "Why thickness moves"),
            ("COAT", "thickness drift", "Scale"),
            ("EXPOSE", "TIN DROPLET", "Why tin"),
            ("EXPOSE", "TIN DROPLET", "Droplets and debris"),
            ("EXPOSE", "2 LASER SHOTS", "Why two pulses"),
            ("EXPOSE", "2 LASER SHOTS", "Efficiency and alternatives"),
            ("EXPOSE", "PLASMA", "The 13.5 nm emitter"),
            ("EXPOSE", "PLASMA", "Source power"),
            ("EXPOSE", "COLLECTOR", "A consumable mirror"),
            ("EXPOSE", "COLLECTOR", "Wear and cleaning"),
            (
                "EXPOSE",
                "INTERMEDIATE FOCUS",
                "Handoff between source and scanner",
            ),
            ("EXPOSE", "INTERMEDIATE FOCUS", "A pinch point"),
            ("EXPOSE", "ILLUMINATOR", "Shaping the beam"),
            ("EXPOSE", "ILLUMINATOR", "Light budget"),
            ("EXPOSE", "RETICLE + MIRRORS", "A reflective mask"),
            ("EXPOSE", "RETICLE + MIRRORS", "Inspection and vendors"),
            ("EXPOSE", "Pellicle", "Dust cover that must be transparent"),
            ("EXPOSE", "Pellicle", "Carbon nanotubes next"),
            ("EXPOSE", "PROJECTION OPTICS", "Six mirrors, no lenses"),
            ("EXPOSE", "PROJECTION OPTICS", "High-NA optics"),
            ("EXPOSE", "WAFER on stage", "Where the photons are counted"),
            ("EXPOSE", "WAFER on stage", "Stochastics and overlay"),
            ("EXPOSE", "Rayleigh resolution", "The equations"),
            ("EXPOSE", "Rayleigh resolution", "The price of NA"),
            ("EXPOSE", "91.8 eV", "Photon arithmetic"),
            ("EXPOSE", "91.8 eV", "Sensitivity vs defects"),
            ("EXPOSE", "NXE:3800E", "Specs"),
            ("EXPOSE", "NXE:3800E", "Cost and power"),
            ("EXPOSE", "EXE:5000", "High-NA: first generation"),
            ("EXPOSE", "EXE:5000", "Adoption and doubt"),
            ("EXPOSE", "ASML 2025", "Scale of the franchise"),
            ("EXPOSE", "ASML 2025", "Reading the numbers"),
            ("EXPOSE", "Chokepoints", "Single points of failure"),
            ("EXPOSE", "Chokepoints", "Tickers and risks"),
        ];
        for (p, c, s) in all {
            let v = lookup(p, c, s).unwrap_or_else(|| panic!("missing {p}/{c}/{s}"));
            check(&v, &format!("{p}/{c}/{s}"));
        }
    }
}
