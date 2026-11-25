"""TRM_EXPORT_CONTROLS: the Terms-tab overview for US export controls on chips and tools.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_export_controls.py

Left: a chip warehouse with GPU crates and a fab-tool crate. Centre: a BIS checkpoint (booth, scan
arch, barrier arms) where the conveyor splits. The allied lane runs to an open port (blue beads);
the China lane hits a closed barrier and its red beads pile up. An Entity List sheet stands by the
booth. Beat 3: the stranded crates turn red and the inventory bar is written down. Beat 4: a
cut-down SKU (smaller crate) passes under the threshold.

Beats:
  0 rules     BIS decides what ships where
  1 split     allied lane open, China lane barred
  2 entity    the Entity List names specific firms
  3 charge    barred stock becomes an inventory charge
  4 skus      cut-down SKUs; revenue mix shifts
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, present  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_EXPORT_CONTROLS"
BEATS = [
    ("Export controls decide which chips ship where",
     "The US Commerce Department's Bureau of Industry and Security (BIS) writes rules that say which chips, "
     "chipmaking tools and design software need a license to ship, and to which countries. Without a license, "
     "the sale cannot happen even if a customer is ready to pay."),
    ("Since 2022, top AI GPUs and fab tools are barred from China",
     "Rules from October 2022, 2023 and later cap the compute and memory bandwidth of AI chips sold into China, "
     "and restrict advanced lithography, etch and deposition tools. Shipments to allied countries keep flowing; "
     "the China lane needs a license that is usually denied."),
    ("The Entity List names specific companies",
     "Beyond country rules, BIS puts named firms on the Entity List. Selling them almost anything made with US "
     "technology needs a license. Huawei, SMIC and many Chinese AI labs and server makers are on it."),
    ("A sudden ban can strand inventory",
     "When a rule changes fast, chips already built for China cannot be sold. Companies then write the inventory "
     "down: NVIDIA took about a $4.5B charge in 2025 when its H20 needed a license, and AMD took about $800M on its MI308."),
    ("Chipmakers redesign SKUs and revenue shifts",
     "Vendors build cut-down versions that fall under the thresholds, and tool makers watch China's share of sales. "
     "Filings list export controls as a key risk. Related: NVIDIA (NVDA), AMD (AMD), Applied Materials (AMAT), "
     "Lam Research (LRCX), KLA (KLAC)."),
]

GX = 0.0  # checkpoint x


def mats(m):
    m["floor"] = mat("ec_floor", (0.16, 0.17, 0.19), rough=0.85)
    m["road"] = mat("ec_road", (0.26, 0.27, 0.30), rough=0.8)
    m["wall"] = mat("ec_wall", (0.70, 0.72, 0.76), rough=0.6)
    m["roof"] = mat("ec_roof", (0.42, 0.45, 0.50), metal=0.4, rough=0.5)
    m["belt"] = mat("ec_belt", (0.12, 0.12, 0.13), rough=0.7)
    m["arm_w"] = mat("ec_arm_w", (0.92, 0.92, 0.92), rough=0.5)
    m["arm_r"] = mat("ec_arm_r", (0.80, 0.14, 0.12), rough=0.5)
    m["ok"] = mat("ec_ok", (0.30, 0.90, 0.45), emit=(0.30, 0.90, 0.45), strength=3.5)
    m["no"] = mat("ec_no", (1.0, 0.25, 0.18), emit=(1.0, 0.25, 0.18), strength=3.5)
    m["gpu"] = mat("ec_gpu", (0.18, 0.20, 0.22), metal=0.7, rough=0.3)
    m["gpu_g"] = mat("ec_gpu_g", (0.45, 0.85, 0.30), emit=(0.45, 0.85, 0.30), strength=2.5)
    m["crate_r"] = mat("ec_crate_r", (0.60, 0.16, 0.12), rough=0.7)
    m["bar_inv"] = mat("ec_bar_inv", (0.55, 0.40, 0.25), rough=0.7)
    m["hull"] = mat("ec_hull", (0.20, 0.30, 0.45), rough=0.5)
    m["box1"] = mat("ec_box1", (0.75, 0.35, 0.15), rough=0.6)
    m["box2"] = mat("ec_box2", (0.20, 0.50, 0.65), rough=0.6)


def gpu_card(m, parent, name, c, s=1.0):
    """A GPU module on its crate: heat-spreader block, die window and a green edge strip."""
    x, y, z = c
    bx(f"{name}_pcb", (x - 8 * s, y, z - 5 * s), (x + 8 * s, y + 1 * s, z + 5 * s), m["pcb_blue"], parent)
    bx(f"{name}_lid", (x - 5 * s, y + 1 * s, z - 4 * s), (x + 5 * s, y + 3 * s, z + 4 * s), m["gpu"], parent)
    bx(f"{name}_led", (x - 8 * s, y + 1 * s, z + 4.4 * s), (x + 8 * s, y + 1.6 * s, z + 5 * s), m["gpu_g"], parent)


def barrier(m, parent, name, x, z, length, closed=True):
    g = empty(name, parent)
    bx(f"{name}_post", (x - 2.0, 0.0, z - 2.0), (x + 2.0, 12.0, z + 2.0), m["wall"], g)
    n = 6
    for k in range(n):
        mt = m["arm_r"] if k % 2 == 0 else m["arm_w"]
        if closed:
            bx(f"{name}_a{k}", (x + 2.0 + k * length / n, 9.0, z - 1.0), (x + 2.0 + (k + 1) * length / n, 11.0, z + 1.0), mt, g)
        else:
            bx(f"{name}_a{k}", (x - 1.0, 12.0 + k * length / n, z - 1.0), (x + 1.0, 12.0 + (k + 1) * length / n, z + 1.0), mt, g)
    return g


def ship(m, parent, name, x, z):
    g = empty(name, parent)
    bx(f"{name}_hull", (x - 40.0, 0.0, z - 10.0), (x + 40.0, 10.0, z + 10.0), m["hull"], g)
    bx(f"{name}_bridge", (x + 26.0, 10.0, z - 8.0), (x + 36.0, 24.0, z + 8.0), m["wall"], g)
    for i in range(5):
        for j in range(2):
            mt = m["box1"] if (i + j) % 2 else m["box2"]
            bx(f"{name}_c{i}{j}", (x - 36.0 + 11.0 * i, 10.0 + 6.0 * j, z - 7.0), (x - 26.5 + 11.0 * i, 15.5 + 6.0 * j, z + 7.0), mt, g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    fx = empty("fx", root)
    present(fx, [(F(0, 0), F(5, 0))])
    bx("floor", (-240.0, -4.0, -180.0), (240.0, -2.0, 140.0), m["floor"], fx)

    # warehouse (left), cut open: crate stacks with GPUs on top, one fab-tool crate
    WX = -150.0
    bx("wh_slab", (WX - 50.0, 0.0, -40.0), (WX + 40.0, 1.0, 40.0), m["road"], fx)
    bx("wh_back", (WX - 50.0, 1.0, -40.0), (WX + 40.0, 40.0, -37.0), m["wall"], fx)
    bx("wh_side", (WX - 50.0, 1.0, -40.0), (WX - 47.0, 40.0, 40.0), m["wall"], fx)
    bx("wh_roof", (WX - 50.0, 40.0, -40.0), (WX + 40.0, 42.0, -5.0), m["roof"], fx)
    K.order_stack(m, fx, "wh_crates", (WX - 10.0, 1.0, -10.0), 4, 3, "ldg_crate", s=10.0)
    for k in range(4):
        gpu_card(m, fx, f"wh_gpu{k}", (WX - 25.0 + 10.0 * k, 31.0, -14.0), 0.55)
    bx("tool_crate", (WX + 18.0, 1.0, 10.0), (WX + 36.0, 22.0, 32.0), m["ldg_crate"], fx)
    bx("tool_lens", (WX + 22.0, 22.0, 14.0), (WX + 32.0, 28.0, 28.0), m["gpu"], fx)

    # conveyor to the checkpoint, then splitting
    bx("belt_in", (WX + 40.0, 4.0, -4.0), (GX - 10.0, 6.0, 4.0), m["belt"], fx)
    for k in range(12):
        x = WX + 44.0 + k * 11.0
        bx(f"roller{k}", (x - 0.6, 2.0, -5.0), (x + 0.6, 4.0, 5.0), m["steel"], fx)
    bx("belt_ally", (GX + 10.0, 4.0, -4.0), (GX + 150.0, 6.0, 4.0), m["belt"], fx)
    bx("belt_cn", (GX - 4.0, 4.0, -120.0), (GX + 4.0, 6.0, -12.0), m["belt"], fx)

    # BIS checkpoint: booth, scan arch with lamps
    bx("booth", (GX - 30.0, 0.0, 12.0), (GX - 12.0, 22.0, 28.0), m["wall"], fx)
    bx("booth_win", (GX - 30.5, 10.0, 15.0), (GX - 29.8, 18.0, 25.0), m["ldg_glass"], fx)
    bx("booth_roof", (GX - 32.0, 22.0, 10.0), (GX - 10.0, 24.0, 30.0), m["roof"], fx)
    bx("arch_l", (GX - 12.0, 0.0, -8.0), (GX - 8.0, 30.0, -4.0), m["steel"], fx)
    bx("arch_r", (GX + 8.0, 0.0, -8.0), (GX + 12.0, 30.0, -4.0), m["steel"], fx)
    bx("arch_t", (GX - 12.0, 30.0, -8.0), (GX + 12.0, 34.0, -4.0), m["steel"], fx)
    ok = empty("lamp_ok_g", fx)
    bx("lamp_ok", (GX + 2.0, 34.0, -7.0), (GX + 8.0, 38.0, -5.0), m["ok"], ok)
    no = empty("lamp_no_g", fx)
    bx("lamp_no", (GX - 8.0, 34.0, -7.0), (GX - 2.0, 38.0, -5.0), m["no"], no)
    present(ok, [(F(0, 0), F(5, 0))])
    present(no, [(F(1, 0.1 + 0.2 * k), F(1, 0.2 + 0.2 * k)) for k in range(4)]
            + [(F(b, 0.1), F(b, 0.9)) for b in (2, 3)])

    # allied lane: open barrier, port with a ship
    barrier(m, fx, "bar_ally", GX + 60.0, 8.0, 24.0, closed=False)
    ship(m, fx, "ship", GX + 190.0, 0.0)
    bx("quay", (GX + 140.0, 0.0, -20.0), (GX + 240.0, 1.0, -12.0), m["road"], fx)
    # China lane: closed barrier, flag of red beads stacking up
    barrier(m, fx, "bar_cn", GX - 14.0, -70.0, 28.0, closed=True)
    bx("cn_gate", (GX - 30.0, 0.0, -140.0), (GX + 30.0, 30.0, -132.0), m["wall"], fx)
    bx("cn_gate_door", (GX - 10.0, 0.0, -132.5), (GX + 10.0, 22.0, -131.5), m["arm_r"], fx)

    ally = [(WX + 40.0, 9.0, 0.0), (GX, 9.0, 0.0), (GX + 150.0, 9.0, 0.0), (GX + 170.0, 18.0, 0.0)]
    run(fx, "flow0", ally, 14, 3.0, m["ldg_blue_b"], [0, 1, 4], 0.0, 0.8, 50)
    cn = [(WX + 40.0, 9.0, 0.0), (GX, 9.0, 0.0), (GX, 9.0, -60.0), (GX, 9.0, -66.0)]
    run(fx, "flow_cn", cn, 10, 3.0, m["ldg_red_b"], [1, 2], 0.0, 0.8, 40)
    # stranded crates piled at the closed barrier (beat 1 on)
    pile = empty("pile", fx)
    K.order_stack(m, pile, "pile_c", (GX + 18.0, 0.0, -80.0), 3, 2, "ldg_crate", s=8.0)
    present(pile, [(F(1, 0.5), F(3, 0))])
    redpile = empty("redpile", fx)
    K.order_stack(m, redpile, "pile_r", (GX + 18.0, 0.0, -80.0), 3, 2, "crate_r", s=8.0)
    present(redpile, [(F(3, 0), F(4, 0))])

    # Entity List sheet by the booth, names lighting in beat 2
    K.ledger_sheet(m, fx, "entity", (GX - 60.0, 17.0, 30.0), 26.0, 34.0, lines=8)
    for k in range(3):
        hl = empty(f"hl{k}", fx)
        bx(f"hl{k}_b", (GX - 72.0, 26.0 - 6.0 * k, 30.6), (GX - 48.0, 28.0 - 6.0 * k, 31.2), m["no"], hl)
        present(hl, [(F(2, 0.15 + 0.2 * k), F(3, 0))])

    # inventory bar written down in beat 3
    K.ledger_bar(m, fx, "inv", GX + 60.0, -80.0, 14.0, {0: 50.0, 3: 50.0, 4: 18.0}, "bar_inv")
    K.ledger_bar(m, fx, "inv_wd", GX + 80.0, -80.0, 14.0, {0: 0.01, 3: 32.0}, "crate_r")
    # cut-down SKU (beat 4): small crates passing the China barrier, which opens
    sku = empty("sku", fx)
    for k in range(3):
        bx(f"sku{k}", (GX - 4.0, 6.0, -20.0 - 30.0 * k), (GX + 4.0, 12.0, -14.0 - 30.0 * k), m["ldg_crate"], sku)
        gpu_card(m, sku, f"sku_gpu{k}", (GX, 12.0, -17.0 - 30.0 * k), 0.35)
    present(sku, [(F(4, 0), F(5, 0))])
    run(fx, "flow_sku", [(GX, 9.0, 0.0), (GX, 9.0, -125.0)], 8, 2.0, m["ldg_gold_b"], [4], 0.1, 0.8, 40)

    C.tags(root, {
        0: [("BIS checkpoint", (GX - 20.0, 30.0, 20.0)), ("GPUs + fab tools", (WX, 46.0, -10.0)),
            ("license needed?", (GX, 42.0, -6.0))],
        1: [("allies: ships", (GX + 190.0, 30.0, 0.0)), ("China: barred", (GX, 20.0, -70.0)),
            ("stranded orders", (GX + 18.0, 24.0, -80.0))],
        2: [("Entity List", (GX - 60.0, 40.0, 30.0)), ("Huawei, SMIC, AI labs", (GX - 60.0, 16.0, 34.0))],
        3: [("inventory charge", (GX + 80.0, 40.0, -80.0)), ("NVDA H20: ~$4.5B", (GX + 30.0, 30.0, -90.0)),
            ("AMD MI308: ~$800M", (GX + 60.0, 58.0, -80.0))],
        4: [("cut-down SKU under cap", (GX, 22.0, -50.0)), ("NVDA AMD AMAT LRCX KLAC", (GX + 100.0, 30.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-70.0, 20.0, 0.0), 260.0, 0.25, 0.40, pad=1.0),
        frame((40.0, 15.0, -40.0), 320.0, -0.35, 0.55, pad=1.0),
        frame((GX - 40.0, 20.0, 20.0), 100.0, 0.25, 0.25),
        frame((GX + 50.0, 20.0, -80.0), 120.0, -0.25, 0.40),
        frame((GX + 20.0, 15.0, -50.0), 220.0, 0.55, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
