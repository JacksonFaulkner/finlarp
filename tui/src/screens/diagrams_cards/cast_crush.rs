// CAST + CRUSH card (SAND page). Sources: USGS MCS 2026 silicon; Roskill 2017 release; PCC BakkiSilicon grade table; Ferroglobe 6-K Q2 2026.
use super::{Card, Sec};
use crate::screens::diagrams_vis::{TO_EOL, Visual, spot};

pub const CARD: Card = Card {
    top: Visual {
        art: r#"┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ CAST + CRUSH : tapped liquid silicon becomes sized lumps, sold as MG-Si 98-99%                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TAP ladle ▶ cast in beds / moulds ▶ cool to solid slab ▶ jaw crush ▶ screen ▶ lump + fines          │
│  (liquid metal)  (poured into beds)          (solid slab)       (sized to order)  (bagged / bulk)    │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ GRADE   Si min   Fe max   Al max   Ca max    WHAT THE NUMBERS MEAN                                   │
│  553    98.5 %   0.5 %    0.5 %    0.3 %     cheapest; aluminum foundry alloys                       │
│  441    99.0 %   0.4 %    0.4 %    0.1 %     cleaner; alloys and some silicones                      │
│  3303   99.0 %   0.3 %    0.3 %    0.03 %    low Ca; silicones and the chemical route                │
│ Code digits = max Fe, Al, Ca in tenths of a percent (553 = 0.5 / 0.5 / 0.3). Limits vary by supplier.│
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ WHO BUYS IT (world silicon metal, Roskill 2016 data; polysilicon+other = remainder, estimate)        │
│  Aluminum alloys    ██████████████████████████  ~50 %                                                │
│  Silicones          ███████████████             ~30 %                                                │
│  Polysilicon+other  ██████████                  ~20 %                                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Price: US silicon metal 130 c/lb Jan-Oct 2025 avg, about $2,870/t (USGS MCS 2026); 170 c/lb in 2024. │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘"#,
        spots: &[
            spot(
                "553",
                0,
                0,
                "Cheapest standard grade: Si 98.5% min, Fe 0.5, Al 0.5, Ca 0.3 max (PCC BakkiSilicon).",
            ),
            spot(
                "3303",
                0,
                0,
                "Tightest common grade here: Fe 0.3, Al 0.3, Ca 0.03 max.",
            ),
            spot(
                "Aluminum alloys",
                0,
                0,
                "Largest outlet, roughly half (Roskill, 2016 data).",
            ),
            spot(
                "130 c/lb",
                0,
                TO_EOL,
                "USGS MCS 2026: Jan-Oct 2025 mean, 2025e.",
            ),
        ],
    },
    desc: "Casting and crushing is the last physical step before the metal leaves the plant. Liquid silicon from the tap is poured into beds or moulds, cooled to a solid slab, then crushed and screened into lump and fines. The product is metallurgical-grade silicon at 98-99% Si; the buyer's spec (553, 441, 3303) sets the allowed iron, aluminum and calcium.",
    secs: &[
        Sec {
            title: "Product form and grade",
            text: "Tapped metal is cast into beds or moulds and cooled, then jaw-crushed and screened to the size the customer orders (lump, fines). Purity is set earlier in the furnace; this step mostly avoids picking up contamination and sizes the product. Grades are named by max Fe, Al and Ca in tenths of a percent: 553 is 0.5/0.5/0.3 (98.5% Si min), 441 is 0.4/0.4/0.1, 3303 is 0.3/0.3/0.03 (PCC BakkiSilicon spec table; limits vary by supplier).",
            vis: Visual {
                art: r#"┌──────────────────────────────────┐
│ Product form                     │
│                                  │
│  ladle ▶ bed / mould             │
│           ▼                      │
│  solid slab, slow cool           │
│           ▼                      │
│  jaw crusher ▶ screen            │
│           ▼                      │
│  ▓▓ lump     ▓ fines             │
│  98.5-99 % Si                    │
└──────────────────────────────────┘"#,
                spots: &[spot(
                    "jaw crusher",
                    0,
                    0,
                    "Jaw crusher then screens set the lump and fines split.",
                )],
            },
        },
        Sec {
            title: "Where it goes",
            text: "USGS says the main US consumers of silicon metal are aluminum alloy makers and the chemical industry, mainly silicones. USGS gives no percentages. Roskill (2017 release, 2016 data) put aluminum at roughly half of consumption and silicones at roughly 30%, with polysilicon the third outlet. The ~20% remainder is our estimate. China made almost 80% of world silicon materials in 2025 (USGS MCS 2026).",
            vis: Visual {
                art: r#"┌──────────────────────────────────┐
│ Silicon metal demand (est.)      │
│                                  │
│  aluminum alloys  ~50 %          │
│  █████████████████████████       │
│  silicones        ~30 %          │
│  ███████████████                 │
│  polysilicon+oth  ~20 %          │
│  ██████████                      │
│  (Roskill, 2016 data)            │
└──────────────────────────────────┘"#,
                spots: &[],
            },
        },
        Sec {
            title: "Price",
            text: "USGS MCS 2026 shows the US average silicon metal price (S&P Global Platts import mean) falling from 361.86 c/lb in 2022 to 170.34 in 2024 and about 130 in 2025e (Jan-Oct mean), roughly $2,870/t. USGS blamed oversupply, weak aluminum and silicones demand and polysilicon stocks. Ferroglobe reported $2,592/t for Q2 2026 (6-K, Aug 2026).",
            vis: Visual {
                art: r#"┌──────────────────────────────────┐
│ US silicon metal, c/lb (USGS)    │
│                                  │
│  2022  362  ██████████████████   │
│  2024  170  ████████▌            │
│  2025e 130  ██████▌              │
│                                  │
│  2025e = about $2,870/t          │
└──────────────────────────────────┘"#,
                spots: &[spot(
                    "2025e",
                    0,
                    TO_EOL,
                    "USGS MCS 2026: about 130 c/lb, Jan-Oct mean.",
                )],
            },
        },
    ],
};
