use super::{Card, Sec};
use crate::screens::diagrams_vis::{Visual, spot};

const TOP: &str = r#"# Tap: furnace to ladle to casting

            electrodes
              │  │  │
      ┌───────┴──┴──┴───────┐
      │   ≈≈ SiO gas ≈≈     │
      │ ▓▓▓ charge ▓▓▓▓▓▓▓▓ │        TAP HOLE  (opened by burning or drilling)
      │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
      │ ░░░░ liquid Si ░░░░░├──●══▶  LAUNDER (refractory channel)
      │ ░░░░░░░░░░░░░░░░░░░ │              │
      └─────────────────────┘              ▼
                                   ┌───────────────┐   fume + SiO
                                   │ ░ liquid Si ░ │  ≈≈≈≈≈▲≈≈≈▶ HOOD + BAGHOUSE
                                   │ ░░░░░░░░░░░░░ │         (burns to microsilica)
                                   │ ▓ slag (Ca,Al │
                                   │   oxides) ▓▓▓ │
                                   └───────┬───────┘
                                           ▲
                                    O2 + air via POROUS PLUG
                                   refine at about 1550-1600 C
                                           │
                                           ▼
                              CASTING BED ──▶ crush ──▶ MG-Si 98-99%
"#;

const TOP_SPOTS: &[crate::screens::diagrams_vis::Spot] = &[
    spot(
        "TAP HOLE",
        0,
        0,
        "Opened periodically by burning (oxygen lance) or drilling so liquid silicon runs out. Large furnaces tap for about 1.5-2 h (NTNU, Silicon for the Chemical and Solar Industry XIII).",
    ),
    spot(
        "LAUNDER",
        0,
        0,
        "Refractory-lined channel from tap hole to ladle.",
    ),
    spot(
        "POROUS PLUG",
        0,
        0,
        "Oxygen-enriched air is purged through a plug in the ladle bottom while tapping and after (Oxidative Ladle Refining, NTNU/SINTEF).",
    ),
    spot(
        "1550-1600 C",
        0,
        0,
        "Preferred refining window, 1823-1873 K, in the OLR literature. Silicon melts at 1414 C.",
    ),
    spot(
        "HOOD + BAGHOUSE",
        0,
        0,
        "Tap-floor fume is captured under a hood and sent to the fume filter; it is sold as microsilica.",
    ),
    spot(
        "slag (Ca,Al",
        0,
        0,
        "Oxygen oxidizes dissolved Ca and Al into a CaO-Al2O3-SiO2 slag that floats off the metal.",
    ),
];

const S1: &str = r#"  furnace      ladle
  ┌──────┐   ┌──────┐
  │ Si   │   │ Si   │
  │      ├═▶ │  ░░░ │
  │ tap  │   │      │
  │ hole │   │ ▓▓▓  │
  └──────┘   └──┬───┘
   open: burn    ▲
   or drill      plug
   (1.5-2 h)
"#;

const S2: &str = r#"   tap floor
   ┌────────┐
   │ ladle  │──▶ ≈≈≈ SiO ≈≈≈
   └────────┘        │ + O2 (air)
                     ▼
              SiO2 particles
                     │
                     ▼
   ┌──────────────────────────┐
   │ HOOD ──▶ off-gas ──▶     │
   │ FUME FILTER (microsilica)│
   └──────────────────────────┘
"#;

const S3: &str = r#"  charged Si = 100
  ┌──────────────────────────┐
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ tapped metal
  └──────────────────────────┘
  ┌──────┐
  │▓▓▓   │ fume / SiO loss
  └──────┘
  ┌────┐
  │ ▓  │ slag + other
  └────┘
  recovery 65-90% depending on source
"#;

pub const CARD: Card = Card {
    top: Visual {
        art: TOP,
        spots: TOP_SPOTS,
    },
    desc: "Every few hours a tap hole at the furnace bottom is opened and liquid silicon runs through a launder into a ladle. In the ladle, air or oxygen is bubbled through the metal to oxidize calcium and aluminum into a slag. The metal is then cast, cooled and crushed. This step sets the final purity, and it is where much of the plant's fume escapes.",
    secs: &[
        Sec {
            title: "Tapping and refining",
            text: "The tap hole is opened by burning or drilling. On large furnaces tapping takes about 1.5 to 2 hours, and the silicon is normally refined while it runs: oxygen-enriched air goes in through a porous plug in the ladle bottom (NTNU, Silicon for the Chemical and Solar Industry XIII). The oxygen forms a slag that takes up dissolved Ca and Al. Oxidative ladle refining is the most widely used route for this, preferably at 1823-1873 K (SINTEF/NTNU OLR papers, Metall. Mater. Trans. B 2016).",
            vis: Visual {
                art: S1,
                spots: &[],
            },
        },
        Sec {
            title: "Fume at the tap floor",
            text: "Tapping and refining both throw off gas containing SiO. It oxidizes in the air to microsilica, so the tap area needs hoods feeding the main off-gas line to the fume filter (US 11874064, hood for Si-metal tapping; NTNU chapter). Elkem's Thamshavn plant hosted a measurement campaign on tapping gas, dust and NOx (JOM 2022).",
            vis: Visual {
                art: S2,
                spots: &[],
            },
        },
        Sec {
            title: "Recovery and yield",
            text: "Not all silicon charged ends up as metal. A metallurgical overview gives 80-90% recovery, with the rest leaving as fume. A 2024 preprint puts end-to-end recovery at 65-75%, and a US patent cites about 75% for a conventional 200 kVA furnace versus 88% for its own process (US 4897852). Sources disagree, so treat any single figure as plant-specific.",
            vis: Visual {
                art: S3,
                spots: &[],
            },
        },
    ],
};
