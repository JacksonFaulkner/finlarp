// SAND / BLEND: the burden recipe for the silicon arc furnace.
use super::{Card, Sec};
use crate::screens::diagrams_vis::{Visual, spot};

const TOP_ART: &str = r#"# Burden per tonne of Si: stoichiometry sets the floor, the plant adds the rest

  QUARTZ LUMPS                  CARBON REDUCTANTS (mix varies by plant)
  ┌────────────────────┐        ┌────────────┐ ┌────────────┐ ┌────────────┐
  │ SiO2   10-100 mm   │        │ COAL       │ │ COKE       │ │ WOOD CHIPS │
  │ floor: 2.14 t      │        │ fixed C    │ │ fixed C    │ │ open the   │
  │ (calc, 100% yield) │        │ cheap      │ │ low ash    │ │ burden     │
  └─────────┬──────────┘        └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
            │                         └──────────────┼──────────────┘
            │                                        │
            │         carbon floor: 0.86 t C (calc), real charge runs above it
            └─────────────────────┬──────────────────┘
                                  ▼
                    ┌────────────────────────────┐
                    │ BLENDED CHARGE             │
                    │ SiO2 + 2C ▶ Si + 2CO       │
                    └─────────────┬──────────────┘
                                  ▼
          ┌───────────────────────────────────────────────────┐
          │ per 28.09 g Si:  60.08 g SiO2 + 24.02 g C         │
          │ per 1 t Si:      2.14 t SiO2 + 0.86 t C           │
          │ off-gas:         1.99 t CO (calc)                 │
          └───────────────────────────────────────────────────┘
  (floor = molar masses only; losses as SiO and fume push real inputs higher)
"#;

const TOP_SPOTS: &[crate::screens::diagrams_vis::Spot] = &[
    spot(
        "QUARTZ LUMPS",
        0,
        0,
        "Lumpy quartz, roughly 10-100 mm, with good purity and thermal strength is preferred (Silicon journal literature, Springer 2017).",
    ),
    spot(
        "COAL",
        0,
        0,
        "Metallurgical coal, low ash. Cheapest fixed carbon, used alone in the all-coal route (SMM, silicon metal cost review).",
    ),
    spot(
        "COKE",
        0,
        0,
        "Coke or petcoke: dense fixed carbon, low ash. Coal-coke is one of three common routes (SMM).",
    ),
    spot(
        "WOOD CHIPS",
        0,
        0,
        "Wood chips (or charcoal) add porosity so CO and SiO gas can pass up through the burden, and carry little ash.",
    ),
    spot(
        "2.14 t",
        0,
        0,
        "60.08 / 28.09 = 2.14 t SiO2 per t Si. Calculated from molar masses, not a plant figure.",
    ),
    spot(
        "0.86 t C",
        0,
        0,
        "2 x 12.01 / 28.09 = 0.86 t carbon per t Si. Calculated; real plants charge more carbon and lose some as SiO and fume.",
    ),
    spot(
        "1.99 t CO",
        0,
        0,
        "2 x 28.01 / 28.09 = 1.99 t CO per t Si. Calculated.",
    ),
];

const MIX_ART: &str = r#"# Three carbons, three jobs

  coal    ┌────────────────┐  cheap fixed C
          │ ░ reactivity   │  high ash
  coke    ├────────────────┤  dense fixed C
          │ ▓ strength     │  low ash
  chips   ├────────────────┤  porosity, low ash
          │ ≈ gas path     │  lots of volatiles
          └────────────────┘

  all-coal | coal+coke | charcoal
  (three common routes, SMM)
"#;

const ASH_ART: &str = r#"# Ash goes into the metal

  carbon ash:  Al   Fe   Ca   B   P
                │    │    │   │   │
                └────┴────┴───┴───┘
                        ▼
              ┌───────────────────┐
              │ molten silicon    │
              └─────────┬─────────┘
                        ▼
       B and P are the hard ones to remove
       (polysilicon needs them near ppb)
"#;

const BAL_ART: &str = r#"# Carbon balance

  too little C      right      too much C
  ┌───────────┐ ┌───────────┐ ┌───────────┐
  │ SiO gas   │ │ Si + CO   │ │ SiC builds│
  │ escapes   │ │ clean tap │ │ at bottom │
  └───────────┘ └───────────┘ └───────────┘
   lost yield                  hard to tap
"#;

pub const CARD: Card = Card {
    top: Visual {
        art: TOP_ART,
        spots: TOP_SPOTS,
    },
    desc: "Blending sets the recipe the furnace will see for weeks: quartz lumps plus a carbon mix of coal, coke and wood chips (or charcoal). The reaction needs about two carbon atoms per silicon, but the mix also has to let gas out and keep boron and phosphorus low. Get the ratio wrong and you lose silicon as SiO gas or choke the hearth with SiC.",
    secs: &[
        Sec {
            title: "Three carbons",
            text: "Coal and coke supply the fixed carbon that strips oxygen off SiO2. Wood chips supply little carbon but open the burden so CO and SiO gas can rise through it, and they bring little ash. Plants run all-coal, coal plus coke, or charcoal routes depending on price and purity targets (SMM, silicon metal cost review).",
            vis: Visual {
                art: MIX_ART,
                spots: &[
                    spot("coal", 0, 0, "Cheapest fixed carbon, higher ash."),
                    spot("coke", 0, 0, "Dense, strong, low ash."),
                    spot("chips", 0, 0, "Porosity for gas flow, low ash."),
                ],
            },
        },
        Sec {
            title: "Purity",
            text: "Whatever ash the carbon carries ends up in the melt: aluminum, iron, calcium, boron, phosphorus. Boron and phosphorus matter most downstream because they are the dopants polysilicon purification must push to ppb levels (textbook; see the wikichip metallurgical-grade silicon page). That is why low-ash coke and wood often cost more.",
            vis: Visual {
                art: ASH_ART,
                spots: &[spot(
                    "B and P",
                    0,
                    0,
                    "Boron (acceptor) and phosphorus (donor) are the costly impurities to remove later.",
                )],
            },
        },
        Sec {
            title: "Carbon balance",
            text: "Stoichiometry gives 0.86 t carbon per tonne Si (my calculation from molar masses), but yield depends on getting the mix right in the furnace. Too little carbon lets SiO escape up the stack; too much builds silicon carbide at the bottom and makes tapping hard (textbook). Reported petcoke and coal ratios per tonne Si differ by furnace size (Silicon journal, Springer 2017).",
            vis: Visual {
                art: BAL_ART,
                spots: &[
                    spot(
                        "SiO gas",
                        0,
                        0,
                        "SiO that leaves with the off-gas is silicon not tapped.",
                    ),
                    spot(
                        "SiC builds",
                        0,
                        0,
                        "Excess carbon forms SiC, which sinks and fouls the hearth.",
                    ),
                ],
            },
        },
    ],
};
