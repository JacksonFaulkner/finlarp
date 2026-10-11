use super::{Card, Sec};
use crate::screens::diagrams_vis::{Visual, spot};

pub const CARD: Card = Card {
    top: Visual {
        art: r#"
  QUARTZITE        ┌─────────┐      ┌─────────┐      ┌─────────────────────────┐
  run of mine ────▶│ CRUSHER │─────▶│ SCREEN  │─────▶│ LUMPS  ~20 to 80-150 mm │──▶ BLEND
  up to ~1 m       └─────────┘      └────┬────┘      └─────────────────────────┘
                                         │ over/undersize
                                    ┌────┴─────┐
                                    │  FINES   │ below ~20 mm: sold, briquetted
                                    └──────────┘

  Lump size window (mm)
   0        20                        80                 150
   │▓▓▓▓▓▓▓▓│                          │                   │
   │ fines  │██████████████████████████│ ▒ too coarse      │
   │ melt   │  charge window           │ centre stays cold │
   │ high up│  gas rises, solid sinks  │ hot zone cools    │
   └────────┴──────────────────────────┴───────────────────┘

  (practice quoted: no fines below 20 mm, top size about 80 mm; reviews cite 10-150 mm quartz)
  (carbon 1-30 mm sits in the same burden)
"#,
        spots: &[
            spot(
                "CRUSHER",
                0,
                0,
                "Jaw or gyratory crusher breaks run-of-mine quartzite down to charge size.",
            ),
            spot(
                "SCREEN",
                0,
                0,
                "Screen sends undersize out. Fines below about 20 mm melt high in the charge and choke gas flow.",
            ),
            spot(
                "charge window",
                0,
                0,
                "The window the furnace wants: porous enough for CO and SiO gas to rise.",
            ),
            spot(
                "hot zone cools",
                0,
                0,
                "Oversize lumps reach the hot zone with a cold core, lowering temperature and pushing SiO out the off-gas.",
            ),
        ],
    },
    desc: "Crushing and screening turn quarry quartzite into lumps in a controlled size window. The furnace burden has to stay open so hot CO and SiO gas rises through it while solids sink evenly. Too many fines choke the bed, too many big lumps heat unevenly. Both raise SiO loss, which is silicon you paid to smelt and then vented.",
    secs: &[
        Sec {
            title: "Size window",
            text: "Quartz and quartzite for silicon is crushed and screened to lumps, with one practice described as top size about 80 mm and no fines below 20 mm because fines melt in the upper charge and cut gas permeability (ispatguru ferrosilicon overview). Broader reviews give 10-150 mm for quartz and 1-30 mm for carbon (Springer, JOM 2022). Exact windows vary by plant and quartz source, so treat the numbers as ranges, not a standard.",
            vis: Visual {
                art: r#"
 mm   0    20        80      150
      ├─────┼─────────┼────────┤
      fines  LUMPS     coarse
      ░░░░░  ████████  ▒▒▒▒▒▒▒▒
      sell   charge    recrush
"#,
                spots: &[spot(
                    "LUMPS",
                    0,
                    0,
                    "Target fraction, roughly 20 to 80 mm in the practice quoted.",
                )],
            },
        },
        Sec {
            title: "Fines and decrepitation",
            text: "Fines come from crushing and also from the quartz itself. Raw quartz decrepitates (cracks) on heating, and the amount of fines created varies strongly with the quartz source (NTNU, industrial quartz thermal degradation). The quartz to cristobalite change carries a theoretical 17% volume increase, which can close pores further (same NTNU work). This is why operators test quartz for thermal strength, not just chemistry.",
            vis: Visual {
                art: r#"
 cold lump  ──heat──▶  cracks
 ┌───────┐            ┌─╲─┬─╱─┐
 │       │            │ ╱ │ ╲ │
 │       │            └───┴───┘
 └───────┘          fines fill gaps
                    gas path closes
   quartz ─▶ cristobalite  +17% vol
"#,
                spots: &[spot(
                    "+17% vol",
                    0,
                    0,
                    "Theoretical volume increase of the quartz to cristobalite transition (NTNU).",
                )],
            },
        },
        Sec {
            title: "Cost of getting it wrong",
            text: "Oversize lumps reach the hot zone with a cold centre, which lowers hot-zone temperature and raises the SiO to CO ratio, so more SiO leaves in the off-gas (ispatguru and Springer summaries). Low permeability also lets SiO escape through gas channels or condense into a sticky mix. An old US DOE study of a DC silicon furnace put fume loss at about 19.5% of silicon charged (OSTI 87367). Sizing is one lever, not the only one.",
            vis: Visual {
                art: r#"
 charge Si  ████████████████████ 100%
 fume loss  ████                 ~19.5%
            (DOE DC furnace, OSTI 87367)
"#,
                spots: &[spot(
                    "~19.5%",
                    0,
                    0,
                    "Silicon lost to fume in the cited DOE DC furnace study.",
                )],
            },
        },
    ],
};
