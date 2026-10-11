use super::{Card, Sec};
use crate::screens::diagrams_vis::{TO_EOL, Visual, spot};

const TOP: &str = r#"# QUARTZITE: the oxygen is the cargo

  QUARTZITE ──▶ CRUSH ──▶ BLEND ──▶ ARC FURNACE ──▶ TAP ──▶ CAST+CRUSH ──▶ MG-Si 98-99%
  ▲ you are here

  SiO2  +  2 C   ──(~2000 C, electric arc)──▶   Si   +   2 CO

  per tonne of silicon, pure-stoichiometry mass balance (calculated):

  ┌────────────────────────────────────────────────────────────────────────────────────┐
  │ IN   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ │
  │      quartz 2.14 t (71%)                                       carbon 0.86 t (29%) │
  │                                                                                    │
  │ OUT  ██████████████████████                                                        │
  │      Si 1.00 t (33%)       CO gas 1.99 t (67%) burned off or captured at the hood  │
  └────────────────────────────────────────────────────────────────────────────────────┘

  47% of the quartz is silicon by mass, 53% is oxygen that has to leave as CO.
  Real plants run above this floor: SiO fume and slag losses push quartz use up.
  Electricity is the other input, roughly 11-13 MWh per tonne of metal (NTNU/SINTEF).

  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────────────────────┐
  │ LUMP, hard       │   │ LOW Fe, Al, Ca   │   │ CHEAP, BULK                        │
  │ no fines         │   │ they stay in Si  │   │ power and permits are the limit    │
  └──────────────────┘   └──────────────────┘   └────────────────────────────────────┘
"#;

const TOP_SPOTS: &[crate::screens::diagrams_vis::Spot] = &[
    spot(
        "SiO2  +  2 C",
        0,
        0,
        "Carbothermic reduction. The overall reaction hides several steps, with SiO gas as an intermediate.",
    ),
    spot(
        "quartz 2.14 t (71%)",
        0,
        0,
        "60.08 / 28.09 g/mol = 2.14 t SiO2 per t Si. Our arithmetic, a floor. Real plants use more.",
    ),
    spot(
        "CO gas 1.99 t",
        0,
        TO_EOL,
        "2 x 28.01 / 28.09 = 1.99 t CO per t Si. Our arithmetic from the reaction.",
    ),
    spot(
        "LUMP, hard",
        0,
        0,
        "Fines choke gas flow through the burden and cause blowouts (textbook furnace practice).",
    ),
];

const S1: &str = r#"# Why lump

   gas up        charge down
     ▲              ▼
  ┌──────────────────────┐
  │  ■  ■■  ■   ■■  ■    │
  │ ■  ■   ■■  ■  ■   ■  │  lumps leave
  │  ■■  ■   ■   ■■  ■   │  gaps for gas
  └──────────────────────┘

  ┌──────────────────────┐
  │  ░░░▒▒░░▒▒░░░▒░░▒    │
  │ ░▒▒░░▒▒▒░░▒▒░░▒░░    │  fines pack,
  │  ▒░░▒▒░░▒░░░▒▒░░▒    │  gas blocks
  └──────────────────────┘
"#;

const S2: &str = r#"# Quartz in, silicon out

  1 t Si  needs  2.14 t SiO2  (floor)
  ┌──────────────────────────────────────┐
  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ 2.14 t SiO2
  │ ██████████████████                   │ 1.00 t Si
  └──────────────────────────────────────┘

  World Si metal 2025, USGS est.

  China  ████████████████████ ~4.0 Mt
  Rest   ███                  ~0.6 Mt
"#;

const S3: &str = r#"# Scarce vs bulk

  ┌───────────────┐        ┌───────────────┐
  │ QUARTZITE     │        │ HPQ 99.998+%  │
  │ cheap, bulk   │        │ Spruce Pine   │
  └───────┬───────┘        └───────┬───────┘
          ▼                        ▼
  ┌───────────────┐        ┌───────────────┐
  │ MG-Si 98-99%  │        │ CRUCIBLES for │
  │ (furnace)     │        │ wafer ingots  │
  └───────────────┘        └───────────────┘
"#;

pub const CARD: Card = Card {
    top: Visual {
        art: TOP,
        spots: TOP_SPOTS,
    },
    desc: "Quartzite is metamorphosed sandstone that is nearly pure SiO2, and it is the oxygen carrier at the start of the silicon chain. The furnace strips the oxygen with carbon and keeps the silicon. Over half the rock's mass leaves as CO, so the input tonnage is large. It is cheap bulk rock; the real constraints sit downstream in power and permits.",
    secs: &[
        Sec {
            title: "Hard lump, low impurity",
            text: "The furnace burden has to stay porous. Hot CO and SiO gas rises through it while the charge sinks, so operators want hard lumps that survive the trip down without crumbling (textbook furnace practice). Lumpy quartz of roughly 10-100 mm is typical in published descriptions. Fines choke the gas path. Iron, aluminum and calcium in the rock mostly carry through into the metal, which sets how much cleaning polysilicon must do later.",
            vis: Visual {
                art: S1,
                spots: &[],
            },
        },
        Sec {
            title: "How much rock",
            text: "Silicon is 47% of SiO2 by mass, so the floor is 2.14 t of quartz per tonne of Si (our stoichiometry: 60.08 / 28.09). Real use is higher because SiO escapes as fume; an old DOE-funded DC furnace test measured silicon loss to fume at 19.5% of the charge. USGS (MCS 2026) puts China at almost 80% of 2025 world silicon materials output, and we carry about 4.6 Mt world Si metal for 2025, about 4.0 Mt China (USGS, estimated).",
            vis: Visual {
                art: S2,
                spots: &[],
            },
        },
        Sec {
            title: "Bulk vs scarce quartz",
            text: "Furnace quartzite is not the bottleneck. USGS lists domestic quartzite as the primary US silicon feed, and silicon metal prices fell in 2025 on oversupply (USGS MCS 2026: Jan-Oct average about 21% below the 2024 average). The scarce quartz is high-purity (HPQ, 99.998+% SiO2), mined at Spruce Pine, NC, for fused crucibles. Different grade, different market.",
            vis: Visual {
                art: S3,
                spots: &[],
            },
        },
    ],
};
