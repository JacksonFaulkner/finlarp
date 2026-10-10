// Per-node descriptions for the `diagrams` screen, shown on Enter. Keyed by
// the node's first label line (exact match, else longest key that prefixes
// it). Researched from public sources; plain ASCII.

pub const DESCS: &[(&str, &str)] = &[
    (
        "CLEAN",
        "Wet benches and single-wafer tools strip photoresist and residue with chemicals (SPM, SC1/SC2, dilute HF), then rinse in ultrapure water and dry. Cleaning repeats many times per wafer since particles kill yield. SCREEN Holdings (7735.T) is the top wet-cleaning supplier, about 35% share (Morningstar 2025); Lam Research (LRCX) and Tokyo Electron (8035.T) compete.",
    ),
    (
        "KLAC",
        "KLA tools inspect and measure wafers after critical layers, optically (light scattering, imaging) and with e-beam, finding particles, defects and overlay or CD errors at nanometer scale. Results feed back to the next layer's litho and etch settings to protect yield. KLA (KLAC) holds over 50% of process control, with a very large optical inspection share.",
    ),
    (
        "WAFER SORT",
        "A prober steps across the finished wafer while a probe card touches thousands of tiny contacts on each die, and a tester checks function and speed. Bad die are inkmapped and skipped at packaging. FormFactor (FORM) leads advanced probe cards, about 32% share (VLSIresearch 2020). Advantest (ATEYY, 6857.T) is the top tester supplier.",
    ),
    (
        "DICE",
        "A diamond blade saw, or a laser, cuts the thinned wafer along scribe streets into individual die, with streets only tens of microns wide. Laser grooving first removes fragile low-k film, then the blade finishes the cut. Disco (6146.T) dominates dicing saws, with more than 4,000 laser saws shipped by Feb 2026.",
    ),
    (
        "PICK",
        "Probed wafers are diced and only known-good die are picked, then attached to a substrate or interposer by thermocompression or hybrid bonding. Probe screening matters because one bad die can scrap a whole multi-chip package. Advanced logic yield is often quoted at 60-80 percent. TSM makes the die; AMKR and ASX handle assembly; TER and Advantest 6857.T supply wafer probe testers.",
    ),
    (
        "PACKAGE",
        "Die are wire or flip-chip bonded, underfilled and molded. HBM stacks 8-12 thinned DRAM dies joined by TSVs, then sits beside the GPU on a silicon interposer in CoWoS packaging. TrendForce estimates TSMC CoWoS capacity at 120-140k wafers per month in 2026, with 50-60k more at OSATs. Nvidia takes over half. TSM leads; AMKR and ASX add overflow capacity.",
    ),
    (
        "FINAL TEST",
        "Finished packages are tested on automated test equipment (ATE) and burned in at high temperature and voltage, typically hours, to weed out early failures. Chips are then speed-binned by maximum clock and power into sellable grades. Test time per AI chip runs minutes, and it is a growing cost share. TER and Advantest 6857.T dominate ATE; AMKR and ASX run the test floors.",
    ),
    (
        "SHIP",
        "Tested modules are mounted on boards and built into servers and full racks, such as the Nvidia NVL72 with 72 GPUs, by ODMs and OEMs. Foxconn 2317.TW leads AI rack shipments at roughly 40-44 percent share, ahead of Quanta (2382.TW) and Wistron (3231.TW). Morgan Stanley expects 80-85k NVL72 racks in 2026, up from about 26.5k in 2025. Dell (DELL) and SMCI ship to cloud and enterprise customers.",
    ),
    (
        "SAND",
        "Quartz sand (SiO2) is heated with carbon in arc furnaces at about 2000 C. This yields metallurgical-grade silicon, roughly 98-99 percent pure. Ultra-pure quartz from Spruce Pine, North Carolina, is also used for crucibles. Key players are Sibelco (private), Quartz Corp (private), Ferroglobe (GSM) and Elkem (ELK.OL).",
    ),
    (
        "POLYSILICON",
        "Metallurgical silicon reacts with HCl to form trichlorosilane. It is distilled, then deposited as silicon onto electrically heated rods at about 1100 C in Siemens bell-jar reactors. The result is polysilicon at 9N-11N purity. Producers include Wacker (WCH.DE), Hemlock (Corning/Shin-Etsu owned), OCI (010060.KS), Tokuyama (4043.T) and REC Silicon.",
    ),
    (
        "MELT + PULL",
        "Polysilicon chunks melt in a quartz crucible at about 1420 C under argon, with dopants like boron or phosphorus added. A seed crystal is dipped in, then slowly rotated and pulled up at roughly 1 mm per minute. The melt freezes onto it as one single crystal. Main operators are Shin-Etsu (4063.T), SUMCO (3436.T), GlobalWafers (6488.TW), Siltronic (WAF.DE) and SK Siltron.",
    ),
    (
        "INGOT",
        "The result is a single-crystal cylinder about 300 mm wide and 1-2 m long, weighing over 100 kg. It is ground to a precise diameter, marked with a notch, then sliced by wire saw into wafers about 775 microns thick. Shin-Etsu and SUMCO together hold roughly half of the global wafer market, with GlobalWafers third.",
    ),
    (
        "SLICE + POLISH",
        "A diamond-wire saw slices the 300mm silicon ingot into discs about 0.8mm thick. Lapping, etching and chemical-mechanical planarization (CMP) then grind and polish them to a mirror finish with nanometer-scale flatness. Wafer makers: Shin-Etsu 4063.T, SUMCO 3436.T, GlobalWafers 6488.TWO, Siltronic WAF.DE. CMP tools and slurries: AMAT, Ebara 6361.T, Entegris ENTG.",
    ),
    (
        "WAFER",
        "The blank wafer is a 300mm (12 inch) disc of ultra-pure monocrystalline silicon, about 775 microns thick and roughly 125 g. Its surface is polished to atomic-scale smoothness. Five makers (Shin-Etsu 4063.T, SUMCO 3436.T, GlobalWafers 6488.TWO, Siltronic WAF.DE, SK Siltron) supply about 85 percent of the world's wafers, with Shin-Etsu and SUMCO largest.",
    ),
    (
        "DEPOSIT",
        "Thin films of insulators, metals and barriers are grown layer by layer. CVD uses reactive gases, ALD adds one atomic layer per cycle, and PVD sputters metal. Films range from under 1nm to several microns, at roughly 25-700 C. Leaders: AMAT, LRCX, TEL 8035.T, ASM International ASM.AS, Kokusai Electric 6525.T.",
    ),
    (
        "COAT",
        "On a track, the wafer spins at thousands of rpm while liquid photoresist is dispensed, leaving a uniform film about 20-200nm thick (EUV resists are thinner). A soft bake then drives off solvent. TEL 8035.T holds roughly 90 percent of coater/developer tools, followed by Screen 7735.T. Resists come from JSR (taken private in 2024), Tokyo Ohka 4186.T and Shin-Etsu 4063.T.",
    ),
    (
        "EXPOSE",
        "ASML's EUV scanners (ASML) fire 13.5nm light, made by hitting tin droplets with a laser, through a mirror-based mask onto resist-coated wafers. Low-NA (0.33) tools cost about $180M; High-NA (0.55) EXE tools resolve about 8nm and cost about $380M. ASML is the sole EUV supplier.",
    ),
    (
        "DEVELOP",
        "After exposure, the wafer is baked and a developer chemical, typically TMAH, washes away the light-changed resist to reveal the circuit pattern. This happens on a coater/developer track tied to the scanner. Tokyo Electron (8035.T) leads, with Screen Holdings the only other major supplier; together they hold about 88% of the market.",
    ),
    (
        "ETCH",
        "Plasma etch bombards the wafer with reactive ions in a vacuum chamber, carving the film only where resist does not protect it. Features are nanometers wide, with channels etched dozens of times deeper than wide, as in 3D NAND. Lam Research (LRCX), Tokyo Electron (8035.T) and Applied Materials (AMAT) lead.",
    ),
    (
        "IMPLANT",
        "Ion implanters ionize dopant atoms like boron, phosphorus or arsenic and accelerate them with electric fields into silicon, changing its conductivity. Energies range from under 1 keV to MeV, and dose control is precise. Axcelis (ACLS) and Applied Materials (AMAT) are key suppliers.",
    ),
];

/// Art shown above the description in the node popup (same conventions as
/// diagrams_art.rs: box lines dim, arrows accent, "(notes)" dim).
pub const VISUALS: &[(&str, &str)] = &[
    ("SAND", include_str!("diagrams_pages/SAND.txt")),
    (
        "POLYSILICON",
        include_str!("diagrams_pages/POLYSILICON.txt"),
    ),
    ("MELT + PULL", include_str!("diagrams_pages/MELT_PULL.txt")),
    ("INGOT", include_str!("diagrams_pages/INGOT.txt")),
    (
        "SLICE + POLISH",
        include_str!("diagrams_pages/SLICE_POLISH.txt"),
    ),
    ("WAFER", include_str!("diagrams_pages/WAFER.txt")),
    ("DEPOSIT", include_str!("diagrams_pages/DEPOSIT.txt")),
    ("COAT", include_str!("diagrams_pages/COAT.txt")),
    ("EXPOSE", include_str!("diagrams_pages/EXPOSE.txt")),
    ("DEVELOP", include_str!("diagrams_pages/DEVELOP.txt")),
    ("ETCH", include_str!("diagrams_pages/ETCH.txt")),
    ("IMPLANT", include_str!("diagrams_pages/IMPLANT.txt")),
    ("CLEAN", include_str!("diagrams_pages/CLEAN.txt")),
    ("KLAC", include_str!("diagrams_pages/KLAC.txt")),
    ("WAFER SORT", include_str!("diagrams_pages/WAFER_SORT.txt")),
    ("DICE", include_str!("diagrams_pages/DICE.txt")),
    ("PICK", include_str!("diagrams_pages/PICK.txt")),
    ("PACKAGE", include_str!("diagrams_pages/PACKAGE.txt")),
    ("FINAL TEST", include_str!("diagrams_pages/FINAL_TEST.txt")),
    ("SHIP", include_str!("diagrams_pages/SHIP.txt")),
];

fn lookup(table: &'static [(&str, &str)], label: &str) -> Option<&'static str> {
    let label = label.trim();
    if let Some((_, d)) = table.iter().find(|(k, _)| *k == label) {
        return Some(d);
    }
    table
        .iter()
        .filter(|(k, _)| label.starts_with(k))
        .max_by_key(|(k, _)| k.len())
        .map(|(_, d)| *d)
}

/// The VISUALS key a node label resolves to (the page's stable name).
pub fn page_key(label: &str) -> Option<&'static str> {
    let label = label.trim();
    if let Some((k, _)) = VISUALS.iter().find(|(k, _)| *k == label) {
        return Some(k);
    }
    VISUALS
        .iter()
        .filter(|(k, _)| label.starts_with(k))
        .max_by_key(|(k, _)| k.len())
        .map(|(k, _)| *k)
}

pub fn describe(label: &str) -> Option<&'static str> {
    lookup(DESCS, label)
}

pub fn visual(label: &str) -> Option<&'static str> {
    lookup(VISUALS, label)
}

/// Per-page hotspot cards (`diagrams_pages/<SLUG>.details.txt`): a header line
/// `== LABEL` (optionally `== LABEL @N`, N = 1-based page line) then a body.
pub const DETAILS: &[(&str, &str)] = &[
    ("SAND", include_str!("diagrams_pages/SAND.details.txt")),
    (
        "POLYSILICON",
        include_str!("diagrams_pages/POLYSILICON.details.txt"),
    ),
    (
        "MELT + PULL",
        include_str!("diagrams_pages/MELT_PULL.details.txt"),
    ),
    ("INGOT", include_str!("diagrams_pages/INGOT.details.txt")),
    (
        "SLICE + POLISH",
        include_str!("diagrams_pages/SLICE_POLISH.details.txt"),
    ),
    ("WAFER", include_str!("diagrams_pages/WAFER.details.txt")),
    (
        "DEPOSIT",
        include_str!("diagrams_pages/DEPOSIT.details.txt"),
    ),
    ("COAT", include_str!("diagrams_pages/COAT.details.txt")),
    ("EXPOSE", include_str!("diagrams_pages/EXPOSE.details.txt")),
    (
        "DEVELOP",
        include_str!("diagrams_pages/DEVELOP.details.txt"),
    ),
    ("ETCH", include_str!("diagrams_pages/ETCH.details.txt")),
    (
        "IMPLANT",
        include_str!("diagrams_pages/IMPLANT.details.txt"),
    ),
    ("CLEAN", include_str!("diagrams_pages/CLEAN.details.txt")),
    ("KLAC", include_str!("diagrams_pages/KLAC.details.txt")),
    (
        "WAFER SORT",
        include_str!("diagrams_pages/WAFER_SORT.details.txt"),
    ),
    ("DICE", include_str!("diagrams_pages/DICE.details.txt")),
    ("PICK", include_str!("diagrams_pages/PICK.details.txt")),
    (
        "PACKAGE",
        include_str!("diagrams_pages/PACKAGE.details.txt"),
    ),
    (
        "FINAL TEST",
        include_str!("diagrams_pages/FINAL_TEST.details.txt"),
    ),
    ("SHIP", include_str!("diagrams_pages/SHIP.details.txt")),
];

pub struct Card {
    pub label: &'static str,
    pub line: Option<usize>,
    pub body: &'static str,
}

pub fn cards(label: &str) -> Vec<Card> {
    let Some(raw) = lookup(DETAILS, label) else {
        return Vec::new();
    };
    let mut out: Vec<Card> = Vec::new();
    let mut body_start = 0;
    let mut off = 0;
    for line in raw.split_inclusive('\n') {
        let start = off;
        off += line.len();
        let Some(head) = line.trim_end().strip_prefix("== ") else {
            continue;
        };
        if let Some(c) = out.last_mut() {
            c.body = raw[body_start..start].trim();
        }
        let (label, line_no) = match head.rsplit_once(" @") {
            Some((l, n)) if n.parse::<usize>().is_ok() => (l, n.parse().ok()),
            _ => (head, None),
        };
        out.push(Card {
            label: label.trim(),
            line: line_no,
            body: "",
        });
        body_start = off;
    }
    if let Some(c) = out.last_mut() {
        c.body = raw[body_start..].trim();
    }
    out
}
