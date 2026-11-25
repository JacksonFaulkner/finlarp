"""TRM_TARIFFS: the Terms-tab overview for import tariffs on servers, parts and tools.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tariffs.py

Back left: an Asian assembly plant loading a container ship. Centre: the US port with a customs
booth; each container that lands pays gold coins into a treasury stack (the tariff, paid by the
importer). Right: the importer's warehouse and a unit-cost bar that steps up. Beat 2: a Mexico
plant to the south ships by truck at a lower rate. Beat 3: crates rush in before a deadline.
Beat 4: gross-margin bar shrinks unless costs are passed on.

Beats:
  0 tax       a tariff is a tax paid at the border by the importer
  1 cost      Section 301 / 232 raise server and part costs
  2 shift     assembly moves to Mexico, Taiwan, SE Asia
  3 pull      orders pulled forward before deadlines
  4 margin    margin squeeze in filings; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, bx, empty, mat  # noqa: E402
from power_vrm_detail import frame, run, present, rise  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_TARIFFS"
BEATS = [
    ("A tariff is a tax paid at the border",
     "A tariff is an import tax charged when goods cross into a country. The importer of record pays it to "
     "customs, not the foreign seller, so a US server maker importing boards from Asia writes the check."),
    ("Section 301 and 232 tariffs raise hardware costs",
     "Section 301 tariffs hit many Chinese-made goods, and Section 232 national-security actions cover steel, "
     "aluminum and are being used to probe semiconductors. A 25% duty on a $10,000 part adds $2,500 to the "
     "landed cost of every unit."),
    ("Companies move assembly to avoid the duty",
     "Tariffs depend on country of origin, so server and electronics makers shift final assembly to Mexico, "
     "Taiwan, Vietnam or Thailand. Moving a line takes quarters and capex, but can cut the duty to near zero under trade deals."),
    ("Deadlines pull orders forward",
     "When a new tariff is announced with a start date, buyers rush to import before it hits. That inflates "
     "revenue and inventory for a quarter or two, then demand can dip after the deadline."),
    ("Filings show it in gross margin and risk factors",
     "Companies either absorb the duty, which shrinks gross margin, or pass it on in prices, which can hurt "
     "volume. Look for tariff lines in risk factors and margin guidance. Related: Dell (DELL), Super Micro (SMCI), "
     "Apple (AAPL), Applied Materials (AMAT), Celestica (CLS)."),
]

PX = 30.0  # US port customs x


def mats(m):
    m["floor"] = mat("tf_floor", (0.16, 0.17, 0.19), rough=0.85)
    m["sea"] = mat("tf_sea", (0.10, 0.20, 0.32), metal=0.2, rough=0.15)
    m["road"] = mat("tf_road", (0.26, 0.27, 0.30), rough=0.8)
    m["wall"] = mat("tf_wall", (0.72, 0.74, 0.78), rough=0.6)
    m["roof"] = mat("tf_roof", (0.42, 0.45, 0.50), metal=0.4, rough=0.5)
    m["hull"] = mat("tf_hull", (0.20, 0.30, 0.45), rough=0.5)
    m["box1"] = mat("tf_box1", (0.75, 0.35, 0.15), rough=0.6)
    m["box2"] = mat("tf_box2", (0.20, 0.50, 0.65), rough=0.6)
    m["box3"] = mat("tf_box3", (0.35, 0.55, 0.30), rough=0.6)
    m["crane"] = mat("tf_crane", (0.95, 0.70, 0.10), metal=0.3, rough=0.5)
    m["bar_cost"] = mat("tf_bar_cost", (0.80, 0.30, 0.22), rough=0.6)
    m["bar_base"] = mat("tf_bar_base", (0.45, 0.48, 0.55), rough=0.6)
    m["bar_margin"] = mat("tf_bar_margin", (0.25, 0.55, 0.40), rough=0.6)
    m["smoke"] = mat("tf_smoke", (0.85, 0.87, 0.90), rough=0.9, alpha=0.5)
    m["truck"] = mat("tf_truck", (0.85, 0.85, 0.88), metal=0.3, rough=0.4)


def ship(m, parent, name, x, z):
    g = empty(name, parent)
    bx(f"{name}_hull", (x - 40.0, -2.0, z - 10.0), (x + 40.0, 8.0, z + 10.0), m["hull"], g)
    bx(f"{name}_bridge", (x + 26.0, 8.0, z - 8.0), (x + 36.0, 22.0, z + 8.0), m["wall"], g)
    mts = [m["box1"], m["box2"], m["box3"]]
    for i in range(5):
        for j in range(2):
            bx(f"{name}_c{i}{j}", (x - 36.0 + 11.0 * i, 8.0 + 6.0 * j, z - 7.0), (x - 26.5 + 11.0 * i, 13.5 + 6.0 * j, z + 7.0),
               mts[(i + 2 * j) % 3], g)
    return g


def plant(m, parent, name, cx, cz, s=1.0):
    g = empty(name, parent)
    w, d, h = 50.0 * s, 30.0 * s, 18.0 * s
    bx(f"{name}_body", (cx - w / 2, 0.0, cz - d / 2), (cx + w / 2, h, cz + d / 2), m["wall"], g)
    for k in range(4):  # saw-tooth roof
        x0 = cx - w / 2 + k * w / 4
        bx(f"{name}_r{k}", (x0, h, cz - d / 2), (x0 + w / 4 - 1.0, h + 5.0 * s, cz + d / 2), m["roof"], g)
    bx(f"{name}_stack", (cx + w / 2 - 6 * s, h, cz - d / 2 + 2 * s), (cx + w / 2 - 2 * s, h + 18 * s, cz - d / 2 + 6 * s), m["roof"], g)
    bx(f"{name}_dock", (cx - 8 * s, 0.0, cz + d / 2), (cx + 8 * s, 10 * s, cz + d / 2 + 1.0), m["road"], g)
    return g


def truck(m, parent, name, x, z):
    g = empty(name, parent)
    bx(f"{name}_box", (x - 12.0, 3.0, z - 4.0), (x + 6.0, 12.0, z + 4.0), m["box3"], g)
    bx(f"{name}_cab", (x + 6.0, 3.0, z - 4.0), (x + 12.0, 10.0, z + 4.0), m["truck"], g)
    for dx in (-8.0, 0.0, 9.0):
        bx(f"{name}_w{dx}", (x + dx - 2.0, 0.0, z - 4.5), (x + dx + 2.0, 3.5, z + 4.5), m["ink"] if "ink" in m else m["road"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    fx = empty("fx", root)
    present(fx, [(F(0, 0), F(5, 0))])
    bx("land", (-20.0, -4.0, -40.0), (260.0, -1.0, 140.0), m["floor"], fx)
    bx("sea", (-260.0, -5.0, -200.0), (-20.0, -3.0, 140.0), m["sea"], fx)
    bx("sea_n", (-20.0, -5.0, -200.0), (260.0, -3.0, -40.0), m["sea"], fx)

    # Asia: plant on a far quay, ship crossing the sea to the US port
    bx("asia_quay", (-250.0, -3.0, -190.0), (-150.0, 0.0, -130.0), m["road"], fx)
    plant(m, fx, "asia_plant", -200.0, -165.0, 1.0)
    rise(fx, "asia_smoke", (-177.0, 42.0, -178.0), 6, 2.0, m["smoke"], [0, 1], h=20.0, spread=(3.0, 3.0))
    sh = ship(m, fx, "ship", -60.0, -20.0)
    K.slide(sh, 0, (-120.0, 0.0, -100.0), (0.0, 0.0, 0.0), 0.0, 0.5)

    # US port: quay crane, customs booth, gate
    bx("us_quay", (-20.0, -1.0, -20.0), (120.0, 1.0, 20.0), m["road"], fx)
    bx("crane_l", (-40.0, 0.0, -14.0), (-36.0, 50.0, -10.0), m["crane"], fx)
    bx("crane_r", (-40.0, 0.0, 10.0), (-36.0, 50.0, 14.0), m["crane"], fx)
    bx("crane_b", (-80.0, 50.0, -14.0), (-10.0, 54.0, 14.0), m["crane"], fx)
    bx("booth", (PX - 10.0, 1.0, 22.0), (PX + 8.0, 22.0, 38.0), m["wall"], fx)
    bx("booth_win", (PX - 10.5, 10.0, 25.0), (PX - 9.8, 18.0, 35.0), m["ldg_glass"], fx)
    bx("booth_roof", (PX - 12.0, 22.0, 20.0), (PX + 10.0, 24.0, 40.0), m["roof"], fx)
    for k in range(6):
        mt = m["bar_cost"] if k % 2 == 0 else m["wall"]
        bx(f"gate{k}", (PX + 10.0, 10.0, 18.0 - 6.0 * k), (PX + 12.0, 12.0, 12.0 - 6.0 * k), mt, fx)
    # containers through customs into the warehouse; coins split off into the treasury
    WX = 170.0
    bx("wh", (WX - 30.0, 0.0, -30.0), (WX + 30.0, 30.0, -27.0), m["wall"], fx)
    bx("wh_side", (WX + 27.0, 0.0, -30.0), (WX + 30.0, 30.0, 20.0), m["wall"], fx)
    bx("wh_roof", (WX - 30.0, 30.0, -30.0), (WX + 30.0, 32.0, -5.0), m["roof"], fx)
    bx("wh_slab", (WX - 30.0, 0.0, -30.0), (WX + 30.0, 1.0, 20.0), m["road"], fx)
    stock = empty("stock", fx)
    K.order_stack(m, stock, "stock0", (WX - 5.0, 1.0, -10.0), 3, 2, "ldg_crate", s=8.0)
    present(stock, [(F(0, 0), F(5, 0))])
    rush = empty("rush", fx)
    K.order_stack(m, rush, "rush0", (WX - 5.0, 17.0, -10.0), 3, 2, "ldg_crate", s=8.0)
    K.order_stack(m, rush, "rush1", (WX + 15.0, 1.0, 8.0), 2, 3, "ldg_crate", s=8.0)
    present(rush, [(F(3, 0.5), F(5, 0))])
    road = [(0.0, 6.0, 0.0), (PX + 11.0, 6.0, 0.0), (WX - 20.0, 6.0, 0.0), (WX - 10.0, 10.0, -6.0)]
    run(fx, "goods", road, 10, 3.0, m["ldg_blue_b"], [0, 1, 2], 0.3, 0.8, 50)
    run(fx, "goods_rush", road, 22, 3.0, m["ldg_blue_b"], [3], 0.0, 0.5, 30)
    duty = [(PX + 8.0, 8.0, 10.0), (PX + 20.0, 20.0, 40.0), (PX + 40.0, 10.0, 60.0)]
    run(fx, "duty", duty, 10, 2.6, m["ldg_gold_b"], [0, 1, 3], 0.35, 0.85, 40)
    bx("treasury_plinth", (PX + 28.0, 0.0, 50.0), (PX + 72.0, 1.5, 72.0), m["roof"], fx)
    K.coin_row(m, fx, "treasury", PX + 34.0, 60.0, 11.0, [10, 16, 22, 14], r=4.5, h=1.6)

    # unit cost bar (base + duty slice) beside the warehouse, stepping up in beat 1
    K.ledger_bar(m, fx, "cost_base", WX + 50.0, 30.0, 12.0, {0: 50.0}, "bar_base")
    K.ledger_bar(m, fx, "cost_duty", WX + 66.0, 30.0, 12.0, {0: 4.0, 1: 14.0, 2: 3.0, 3: 14.0}, "bar_cost")

    # Mexico (beat 2): plant to the south, trucks crossing a land border
    mx = empty("mx", fx)
    plant(m, mx, "mx_plant", 100.0, 110.0, 0.8)
    bx("mx_road", (100.0, 0.0, 60.0), (108.0, 0.6, 96.0), m["road"], mx)
    bx("border", (60.0, 0.0, 70.0), (150.0, 6.0, 72.0), m["bar_cost"], mx)
    truck(m, mx, "truck0", 104.0, 80.0)
    present(mx, [(F(2, 0), F(5, 0))])
    run(fx, "mx_goods", [(104.0, 6.0, 96.0), (104.0, 6.0, 40.0), (WX - 20.0, 6.0, 4.0), (WX - 10.0, 10.0, -6.0)], 8, 3.0,
        m["ldg_blue_b"], [2, 4], 0.0, 0.8, 50)

    # margin bars (beat 4): before/after
    mg = empty("mg", fx)
    bx("mg_plinth", (WX + 40.0, 0.0, 50.0), (WX + 80.0, 1.0, 80.0), m["roof"], mg)
    present(mg, [(F(4, 0), F(5, 0))])
    K.ledger_bar(m, fx, "mg_before", WX + 50.0, 65.0, 10.0, {0: 0.01, 4: 40.0}, "bar_margin")
    K.ledger_bar(m, fx, "mg_after", WX + 68.0, 65.0, 10.0, {0: 0.01, 4: 26.0}, "bar_margin")

    C.tags(root, {
        0: [("ship lands at US port", (-30.0, 30.0, 0.0)), ("customs", (PX, 30.0, 30.0)),
            ("importer pays duty", (PX + 50.0, 30.0, 62.0))],
        1: [("Section 301 / 232", (PX, 30.0, 30.0)), ("unit cost + duty", (WX + 50.0, 52.0, 30.0)),
            ("25% on $10k = +$2.5k", (WX + 66.0, 20.0, 34.0))],
        2: [("assembly moves to Mexico", (100.0, 34.0, 110.0)), ("duty near zero", (WX + 66.0, 6.0, 30.0))],
        3: [("rush before the deadline", (WX, 40.0, -10.0)), ("inventory piles up", (WX + 15.0, 30.0, 8.0))],
        4: [("margin before / after", (WX + 60.0, 48.0, 65.0)), ("DELL SMCI AAPL AMAT CLS", (PX + 50.0, 20.0, 62.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 15.0, -40.0), 300.0, 0.30, 0.45, pad=1.0),
        frame((150.0, 25.0, 25.0), 230.0, -0.25, 0.35),
        frame((160.0, 15.0, 60.0), 250.0, -0.30, 0.55),
        frame((WX, 20.0, -5.0), 110.0, 0.30, 0.40),
        frame((WX - 10.0, 25.0, 55.0), 170.0, -0.10, 0.40),
    ], root)


if __name__ == "__main__":
    build()
