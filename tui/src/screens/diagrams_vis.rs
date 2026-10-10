// Right-hand visual for each section of a detail card. Keyed by (card label,
// section heading). Same conventions as diagrams_art.rs: box lines dim,
// arrows accent, ▓ accent, █ green, "(notes)" dim italic, `# ` heading.

/// A selectable spot in a visual: the `nth` occurrence of `needle` in the art.
/// `width` 0 highlights the needle itself, `TO_EOL` runs to the end of its line.
pub struct Spot {
    pub needle: &'static str,
    pub nth: usize,
    pub width: u16,
    pub info: &'static str,
}

pub const TO_EOL: u16 = u16::MAX;

pub const fn spot(needle: &'static str, nth: usize, width: u16, info: &'static str) -> Spot {
    Spot {
        needle,
        nth,
        width,
        info,
    }
}

pub struct Visual {
    pub art: &'static str,
    pub spots: &'static [Spot],
}

/// A spot placed on the art grid.
pub struct Placed {
    pub row: u16,
    pub col: u16,
    pub len: u16,
    pub info: &'static str,
}

impl Visual {
    /// Spots located in the art, sorted top-to-bottom, left-to-right.
    pub fn placed(&self) -> Vec<Placed> {
        let lines: Vec<&str> = self.art.lines().collect();
        let mut out: Vec<Placed> = self
            .spots
            .iter()
            .filter_map(|sp| {
                let mut seen = 0;
                for (row, line) in lines.iter().enumerate() {
                    for (byte, _) in line.match_indices(sp.needle) {
                        if seen < sp.nth {
                            seen += 1;
                            continue;
                        }
                        let col = line[..byte].chars().count() as u16;
                        let len = match sp.width {
                            0 => sp.needle.chars().count() as u16,
                            TO_EOL => (line.chars().count() as u16).saturating_sub(col),
                            w => w,
                        };
                        return Some(Placed {
                            row: row as u16,
                            col,
                            len,
                            info: sp.info,
                        });
                    }
                }
                None
            })
            .collect();
        out.sort_by_key(|p| (p.row, p.col));
        out
    }
}

/// Nearest spot in direction (dx, dy). Rows count triple (cells are ~2x tall).
pub fn step(spots: &[Placed], cur: usize, dx: i32, dy: i32) -> usize {
    let Some(c) = spots.get(cur) else {
        return cur;
    };
    let (cx, cy) = (c.col as i32, c.row as i32 * 3);
    spots
        .iter()
        .enumerate()
        .filter(|(i, _)| *i != cur)
        .filter_map(|(i, p)| {
            let (ddx, ddy) = (p.col as i32 - cx, p.row as i32 * 3 - cy);
            let (along, across) = if dx != 0 {
                (ddx * dx, ddy.abs())
            } else {
                (ddy * dy, ddx.abs())
            };
            (along > 0).then_some((along + 2 * across, i))
        })
        .min()
        .map_or(cur, |(_, i)| i)
}

/// Visual for (page, card, section). `page` is the diagrams_desc.rs table key
/// ("SAND", "MELT + PULL", ...), `card` the `== LABEL` of the details file,
/// `section` its `# heading`. Each helper file owns a slice of the pages.
pub fn visual_for(page: &str, card: &str, section: &str) -> Option<Visual> {
    local(page, card, section)
        .or_else(|| super::diagrams_vis_a::lookup(page, card, section))
        .or_else(|| super::diagrams_vis_b::lookup(page, card, section))
        .or_else(|| super::diagrams_vis_c::lookup(page, card, section))
        .or_else(|| super::diagrams_vis_d::lookup(page, card, section))
        .or_else(|| super::diagrams_vis_e::lookup(page, card, section))
}

fn local(page: &str, card: &str, section: &str) -> Option<Visual> {
    match (page, card, section) {
        ("SAND", "QUARTZITE", "Feed rock") => Some(Visual {
            art: FEED_ROCK,
            spots: FEED_SPOTS,
        }),
        ("SAND", "QUARTZITE", "How much") => Some(Visual {
            art: HOW_MUCH,
            spots: HOW_SPOTS,
        }),
        ("SAND", "QUARTZITE", "Not the scarce one") => Some(Visual {
            art: TWO_ROCKS,
            spots: ROCK_SPOTS,
        }),
        ("POLYSILICON", "SiHCl3 + H2", "Deposition and recycle") => Some(Visual {
            art: TCS_LOOP,
            spots: TCS_SPOTS,
        }),
        _ => None,
    }
}

/// Test helper for the vis files: every spot resolves and none sits on a
/// `# ` heading line (headings render one column narrower).
#[cfg(test)]
pub fn check(v: &Visual, what: &str) {
    let placed = v.placed();
    assert_eq!(placed.len(), v.spots.len(), "unresolved spot in {what}");
    for p in &placed {
        let line = v.art.lines().nth(p.row as usize).unwrap();
        assert!(!line.starts_with("# "), "{what}: spot on heading: {line}");
    }
    let w = v.art.lines().map(|l| l.chars().count()).max().unwrap_or(0);
    assert!(w <= 78, "{what}: art is {w} cols, max 78");
}

const FEED_SPOTS: &[Spot] = &[
    spot(
        "(CO + SiO gas)",
        0,
        0,
        "Hot CO and SiO gas made lower in the furnace rises through the charge and leaves at the top. The charge sinks the other way. Both flows share the same gaps between lumps.",
    ),
    spot(
        "┌─",
        0,
        TO_EOL,
        "Lump quartz leaves gaps, so gas passes evenly and the burden sinks smoothly. Operators want lumps that survive sinking through hot gas without crumbling (textbook).",
    ),
    spot(
        "(even flow, the charge sinks smoothly)",
        0,
        0,
        "Even gas flow means steady reactions and steady output.",
    ),
    spot(
        "┌─",
        1,
        TO_EOL,
        "Fines fill the gaps. Gas cannot get through, so it channels, the charge sinters, and the furnace loses silicon as fume.",
    ),
    spot(
        "(pressure builds: blowouts and eruptions)",
        0,
        0,
        "Choked gas builds pressure until it breaks through suddenly: the blowouts and eruptions the textbook warns about. This is why the feed is sorted and washed lump rock.",
    ),
];

const HOW_SPOTS: &[Spot] = &[
    spot(
        "quartz in",
        0,
        TO_EOL,
        "SiO2 is 60.08 mass units, of which Si is 28.09. So 1 t of Si needs 60.08 / 28.09 = 2.14 t of quartz, before any yield loss. One overview puts silicon yield at 80-90% of charged silicon, so real consumption is higher.",
    ),
    spot(
        "silicon out",
        0,
        TO_EOL,
        "The product: 1 t of silicon, about 98-99% pure (metallurgical grade).",
    ),
    spot(
        "oxygen out",
        0,
        TO_EOL,
        "The other 1.14 t is oxygen. Carbon strips it off and it leaves the furnace as CO gas. That is why carbon (coal, coke, wood chips) is in the blend.",
    ),
    spot(
        "████████████████████████████▓",
        0,
        TO_EOL,
        "47% of the rock's mass is silicon, 53% is oxygen. The furnace's whole job is to remove that oxygen.",
    ),
    spot(
        "4.6 Mt silicon metal",
        0,
        TO_EOL,
        "USGS puts world silicon metal output at about 4.6 million tonnes in 2025 (estimated), with China about 4.0 million.",
    ),
    spot(
        "= at least 9.8 Mt quartz",
        0,
        TO_EOL,
        "4.6 Mt x 2.14 = 9.8 Mt, a floor. Nothing here is scarce in geology: the constraint is cheap electricity and permitted furnace sites, not rock.",
    ),
];

const ROCK_SPOTS: &[Spot] = &[
    spot(
        "BULK",
        0,
        0,
        "Bulk quartzite: hard lump rock, low in clay and iron. Cheap industrial feed, a far cheaper product than the quartz mined for crucibles.",
    ),
    spot(
        "ARC FURNACE",
        0,
        0,
        "Quartzite plus carbon heated by electric arcs at about 2000 C. Output is metallurgical-grade silicon.",
    ),
    spot(
        "MG-Si",
        0,
        0,
        "Metallurgical-grade silicon, roughly 98-99% pure. It still has to be purified into polysilicon before it can become wafers.",
    ),
    spot(
        "SPRUCE PINE",
        0,
        0,
        "Spruce Pine, North Carolina: the dominant source of high-purity quartz (Sibelco, Quartz Corp). Hurricane Helene shut the mines in 2024 and showed the risk.",
    ),
    spot(
        "CRUSH +",
        0,
        0,
        "The ore is crushed, then flotation separates the quartz from other minerals.",
    ),
    spot(
        "ACID LEACH",
        0,
        0,
        "Acid leaching dissolves the remaining metal impurities out of the quartz grains.",
    ),
    spot(
        "HPQ",
        0,
        0,
        "High-purity quartz, 99.998+ percent SiO2. Alternatives (Norway, Russia, Brazil, synthetic quartz) exist but have not matched qualification at scale.",
    ),
    spot(
        "FUSED QUARTZ",
        0,
        0,
        "Fused-quartz crucibles hold the ~1420 C silicon melt during crystal pulling. Each is consumed per ingot pull, so HPQ supply gates 300mm wafer output.",
    ),
];

const TCS_SPOTS: &[Spot] = &[
    spot(
        "SiHCl3 + H2",
        0,
        0,
        "Feed gas: trichlorosilane (TCS) carried in hydrogen, in through nozzles in the base plate.",
    ),
    spot(
        "BELL JAR",
        0,
        0,
        "Hydrogen reduces TCS on the 1000-1150 C rod surface, giving silicon and 3 HCl. Silicon deposits on the rod; the gas leaves.",
    ),
    spot(
        "Si on the rod",
        0,
        0,
        "Silicon builds up on the heated rod, becoming polysilicon at 9N-11N purity.",
    ),
    spot(
        "off-gas: HCl, H2, STC, TCS",
        0,
        0,
        "What leaves the jar: HCl, H2, silicon tetrachloride (STC, from the side reaction 4SiHCl3 giving Si + 3SiCl4 + 2H2) and unreacted TCS. Conversion per pass is modest.",
    ),
    spot(
        "condense + separate",
        0,
        0,
        "Off-gas is condensed and separated into its parts, and the recycle loops carry the economics.",
    ),
    spot(
        "│  H2   │",
        0,
        0,
        "Hydrogen is recycled back to the reactor.",
    ),
    spot(
        "│  HCl  │",
        0,
        0,
        "HCl is recycled, and can be used to make more TCS from metallurgical silicon.",
    ),
    spot(
        "│    STC    │",
        0,
        0,
        "Silicon tetrachloride, the unwanted by-product.",
    ),
    spot(
        "sold, or back to TCS",
        0,
        0,
        "STC is sold for silicones and silica, or hydrogenated back to TCS in modified Siemens routes.",
    ),
];

const FEED_ROCK: &str = "\
# Lumps: gas rises through the gaps

        ▲   ▲   ▲   ▲   ▲   ▲      (CO + SiO gas)
  ┌──────────────────────────────────────────────────────┐
  │ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓│
  │    ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓│
  │ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓│
  │    ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓│
  │ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓│
  └──────────────────────────────────────────────────────┘
  (even flow, the charge sinks smoothly)


# Fines: gas is choked

        ✕   ✕   ✕   ✕   ✕   ✕
  ┌──────────────────────────────────────────────────────┐
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
  └──────────────────────────────────────────────────────┘
  (pressure builds: blowouts and eruptions)
";

const HOW_MUCH: &str = "\
# Per 1 tonne of silicon

  quartz in    ███████████████████████████████████████████ 2.14 t SiO2

  silicon out  ████████████████████ 1.00 t Si

  oxygen out   ███████████████████████ 1.14 t O
  (the oxygen leaves with carbon as CO)


# Where the mass goes in SiO2

  ████████████████████████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  Si 47% stays                O 53% leaves

  SiO2 ──▶ Si + O


# World, 2025

  4.6 Mt silicon metal (USGS, estimated)
  x 2.14 t quartz per t Si
  = at least 9.8 Mt quartz
  (textbook arithmetic, before yield losses)
";

const TWO_ROCKS: &str = "\
# Two different rocks

  ┌───────────────┐    ┌───────────────┐    ┌──────────────┐
  │ BULK          │    │ ARC FURNACE   │    │    MG-Si     │
  │ QUARTZITE     │──▶ │ + coal, coke  │──▶ │   98-99%     │
  └───────────────┘    └───────────────┘    └──────────────┘
  (cheap and plentiful: the limit is power and permits, not rock)


  ┌───────────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────┐
  │ SPRUCE PINE   │   │ CRUSH +      │   │ ACID LEACH  │   │    HPQ     │
  │ ORE           │──▶│ FLOTATION    │──▶│             │──▶│ 99.998+%   │
  └───────────────┘   └──────────────┘   └─────────────┘   └─────┬──────┘
                                                                 │
                                                                 ▼
                                                    ┌─────────────────────┐
                                                    │ FUSED QUARTZ        │
                                                    │ CRUCIBLE            │
                                                    └─────────────────────┘
                                                    (holds the ~1420C melt)

  (one crucible per ingot pull: HPQ gates 300mm wafers)
";

const TCS_LOOP: &str = "\
# Reduction and recycle

  SiHCl3 + H2 ──▶ ┌───────────────┐ ──▶ Si on the rod
                  │   BELL JAR    │     (1000-1150 C)
                  └───────┬───────┘
                          │ off-gas: HCl, H2, STC, TCS
                          ▼
          ┌───────────────────────────────┐
          │       condense + separate     │
          └───┬───────────┬───────────┬───┘
              ▼           ▼           ▼
          ┌───────┐   ┌───────┐   ┌───────────┐
          │  H2   │   │  HCl  │   │    STC    │
          └───────┘   └───────┘   └───────────┘
          recycled    recycled    sold, or back to TCS
";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_spot_is_found_in_its_art() {
        for (p, c, s) in [
            ("SAND", "QUARTZITE", "Feed rock"),
            ("SAND", "QUARTZITE", "How much"),
            ("SAND", "QUARTZITE", "Not the scarce one"),
            ("POLYSILICON", "SiHCl3 + H2", "Deposition and recycle"),
        ] {
            check(&visual_for(p, c, s).unwrap(), &format!("{p}/{c}/{s}"));
        }
    }
}
