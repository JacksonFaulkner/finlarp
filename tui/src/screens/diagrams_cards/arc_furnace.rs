// SAND / ARC FURNACE card. Sources: NTNU Silicon for the Chemical and Solar
// Industry XIII (11-13 MWh/t, >1800 C, woodchips); MDPI Appl. Sci. 14(18) 8346
// (2024, 11.2-12.1 MWh/t, 88-89% recovery); DOE/OSTI 87367; Metso silicon plant
// page (silica fume from off-gas); plasma-smelting patent US 6,696,035 context
// (10-20% of Si lost as SiO). Reaction steps are textbook.
use super::{Card, Sec};
use crate::screens::diagrams_vis::{Visual, spot};

pub const CARD: Card = Card {
    top: Visual {
        art: "\
   3-phase AC, 11-13 MWh per tonne Si          charge in: quartz lump + coal/coke/charcoal + woodchips
        │       │       │                                   │
        ▼       ▼       ▼                                   ▼
   ┌────────────────────────────────────────────────────────┐   off-gas: CO + SiO, SiO burns to
   │  ████     ████     ████   carbon electrodes            │   SiO2 fume; bag-house captures it
   │  ████     ████     ████   buried in the charge         │   (silica fume, sold)
   │  ▓▓▓▓     ▓▓▓▓     ▓▓▓▓   arc zone, above 1800 C       │   
   │                           SiO2 + C  -> SiO + CO        │   COOL, TOP: charge preheats,
   │   ▲   ▲   ▲   ▲   ▲   ▲   SiO + 2C  -> SiC + CO        │   gas rises through it
   │   ≈ SiO + CO gas rising ≈  SiC + SiO -> Si + CO        │   HOT, AT ELECTRODE TIPS
   │                           net: SiO2 + 2C -> Si + 2CO   │   
   │                                                        │   
   │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│   molten Si pools on the hearth
   └───────────────────────────────────────────────────TAP ▶┘   carbon-lined hearth, tap hole at base
   24/7 duty. Hydro-priced power. Some Si leaves as SiO: patent cites 10-20% of Si lost this way.",
        spots: &[],
    },
    desc: "A submerged arc furnace is a carbon-lined steel shell fed from the top, with three large electrodes buried in a pile of quartz and carbon. The pile is the resistor, so heat is released deep inside the charge and carbon strips the oxygen off the silica at over 1800 C. It is the bottleneck of the chain: 11-13 MWh per tonne of silicon makes it an electricity business with a quartz input.",
    secs: &[
        Sec {
            title: "Reactions and heat",
            text: "Overall: SiO2 + 2C gives Si + 2CO, but it runs in steps (textbook sequence). In the hot zone SiO2 + C gives SiO gas + CO. SiO rises, meets carbon and forms SiC, and SiC plus SiO gives liquid Si. Silicon production needs temperatures above 1800 C (NTNU, Silicon for the Chemical and Solar Industry XIII). Woodchips are added to keep the charge permeable so gas can escape. SiO that leaves unreacted is a yield loss: a patent cites 10 to 20 percent of Si lost this way.",
            vis: Visual {
                art: "\
 1) SiO2 + C   -> SiO(g) + CO      hot zone
 2) SiO + 2C   -> SiC + CO
 3) SiC + SiO  -> Si(l) + CO
    ──────────────────────────────
    SiO2 + 2C  -> Si + 2CO
 SiO(g) that escapes:
   SiO + CO -> SiO2 fume (off-gas)
 yield lost as SiO: 10-20% of Si",
                spots: &[spot("SiO(g) that escapes:", 0, 0, "unreacted SiO gas leaves the pile; it burns to silica fume")],
            },
        },
        Sec {
            title: "Power and electrodes",
            text: "Plants quote 11 to 13 MWh per tonne of silicon (NTNU). An MDPI industrial test reported 11.2 to 12.1 MWh/t at 88 to 89 percent Si recovery (Appl. Sci. 2024). A DOE/OSTI study of US plants found commercial furnaces using roughly three times the theoretical reaction energy, and electrode use of 0.144 lb per lb of Si. Closed furnaces cut energy and electrode use versus open ones (Dow Corning study). At an assumed 40 USD/MWh (estimate, not sourced), power is about 450-500 USD per tonne.",
            vis: Visual {
                art: "\
 per tonne of Si
 ┌──────────────────────────────┐
 │ power   11-13 MWh            │
 │ ████████████████████████████ │
 │ theory  ~1/3 of actual (DOE) │
 │ █████████                    │
 └──────────────────────────────┘
 electrode  0.144 lb / lb Si
 recovery   88-89% (MDPI test)",
                spots: &[spot("power   11-13 MWh", 0, 0, "11-13 MWh/t: NTNU; 11.2-12.1 in an MDPI industrial test")],
            },
        },
        Sec {
            title: "Why 24/7, why hydro",
            text: "Stopping the power lets the charge freeze, so furnaces run continuously and outages are expensive (textbook). With electricity the largest cost line, smelters cluster near cheap hydro in Norway, Iceland, Brazil and Canada. Ferroglobe books long-term energy contracts at fair value: its Q2 2026 6-K showed a 59.9 million USD gain on them. Off-gas silica fume is captured and sold (Metso), a small credit against the power bill.",
            vis: Visual {
                art: "\
 outage ──▶ charge freezes
            ──▶ restart days, lost tap
 cheap power sites
 ┌────────┬────────┬────────┐
 │ Norway │Iceland │ Brazil │
 │ hydro  │ hydro/ │ hydro  │
 │        │ geoth. │ Canada │
 └────────┴────────┴────────┘
 Ferroglobe Q2'26: +$59.9M on
 long-term energy contracts",
                spots: &[spot("charge freezes", 0, 0, "a frozen charge means a costly restart")],
            },
        },
    ],
};
