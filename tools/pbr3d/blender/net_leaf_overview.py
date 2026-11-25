"""The LEAF page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/net_leaf_overview.py

Writes blender/net_leaf_overview.blend and assets/net_leaf_overview.glb. One beat is 8 s.

A row of GPU racks round a network rack whose leaf switch is cut open (net_leaf_detail.py), three
more rows behind, four spine switches in a spine row at the right, and the overhead fibre trays
that tie every leaf to every spine.

Beats (match the seven beats in diagrams_nodes/netcool/leaf/overview.rs):
  0 the row      the row, its leaf near the top, the rows behind, the spines
  1 downlinks    cyan packets leave each server's NIC on copper DAC / aqua AOC into the leaf
  2 the ASIC     packets run the SerDes traces into the switch chip, which glows; fans blow
  3 uplinks      yellow light leaves the top row of ports on single-mode fibre to the spines
  4 ECMP         flows from leaf 0 spread across all four spines and drop into another row's leaf
  5 congestion   too much traffic for one uplink: a queue builds, pause frames run back
  6 the fabric   every leaf to every spine, every link busy
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_leaf_detail as D  # noqa: E402
from net_leaf_detail import frame, camera_path, run, rise  # noqa: E402

PAGE = "net_leaf"
NAME = "overview"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def downlinks(m, root, s, beats, step=1, u0=0.0, u1=0.6, life=70, name="dl"):
    for i in range(0, D.N_PORT, step):
        run(root, f"{name}{i}", D.to_leaf(s, i), 2, 0.7, m["pkt"], beats, u0 + 0.01 * (i % 8), u1, life)


def uplinks(m, root, s, beats, u0=0.0, u1=0.6, life=90, name="ul", spines=range(4)):
    for j in spines:
        for i in (8 * j + 1, 8 * j + 5):
            run(root, f"{name}{i}", D.to_spine(s, 0, j, i), 2, 0.8, m["up"], beats, u0 + 0.03 * j, u1, life)


def ecmp(m, root, s, beats, dst=3, u0=0.0, u1=0.7, name="ec", n=3):
    """Flows from leaf 0 hashed across all four spines, then down to leaf `dst`."""
    for j in range(4):
        path = D.to_spine(s, 0, j) + D.from_spine(s, dst, j)
        run(root, f"{name}{j}", path, n, 0.9, m["spine"], beats, u0 + 0.05 * j, u1, 120)


def blink_leds(lf, beats, n=8):
    for gi, g in enumerate(lf["leds"]):
        iv = []
        for b in beats:
            w = 1.0 / n
            for k in range(n):
                if (k + gi) % 2 == 0:
                    iv.append((F(b, w * k + 0.02 * gi), F(b, w * (k + 0.6))))
        show(g, iv)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    lf = s["leaf"]
    blink_leds(lf, range(BEATS))
    for k, sp in enumerate(s["spines"]):
        show(sp["leds"], span(3, 0.3, 7, 0.0))

    # beat 1: downlinks; beat 6 again
    downlinks(m, root, s, [1, 6], step=1)
    # beat 2: inside the leaf
    for i in range(0, D.N_PORT, 4):
        run(root, f"tin{i}", lf["tr_down"][i][::-1], 2, 0.45, m["pkt"], 2, 0.0 + 0.02 * (i // 4), 0.7, 30)
        run(root, f"tout{i}", lf["tr_up"][i], 2, 0.45, m["up"], 2, 0.15 + 0.02 * (i // 4), 0.85, 30)
    show(lf["die_glow"], span(2, 0.1, 3, 0.0) + span(4, 0.0, 7, 0.0))
    for k, fp in enumerate(lf["fans"]):
        run(root, f"air{k}", [(fp[0], fp[1], D.ROW_Z[0] + 2.0), (fp[0], fp[1], fp[2] - 20.0)], 2, 0.5, m["cool"], 2, 0.02 * k, 0.8, 40)
    rise(root, "asic_heat", lf["top"], 5, 0.6, m["heat"], 2, 0.05, 0.85, 22.0, 60, (6.0, 8.0))
    # beat 3: uplinks
    uplinks(m, root, s, [3, 6])
    # beat 4: ECMP across the spines
    ecmp(m, root, s, [4, 6])
    for r in (1, 2):
        for j in range(4):
            run(root, f"bg{r}{j}", D.to_spine(s, r, j), 2, 0.8, m["up"], [4, 6], 0.1 + 0.04 * j, 0.7, 90)
    # beat 5: congestion: everything aims at one uplink
    for i in range(0, D.N_PORT, 2):
        run(root, f"cg{i}", D.to_leaf(s, i), 2, 0.7, m["pkt"], 5, 0.0, 0.35, 60)
    run(root, "cg_up", D.to_spine(s, 0, 1, 9), 4, 0.8, m["up"], 5, 0.1, 0.8, 90)
    D.queue(m, root, (lf["up"][9][0], lf["up"][9][1] + 3.0, lf["up"][9][2] + 2.0), 9, 5, 0.15, 0.55, 1.1, "qbuild")
    for i in (0, 6, 25, 31):
        run(root, f"pfc{i}", D.from_leaf(s, i), 2, 0.8, m["fail"], 5, 0.5, 0.75, 60)

    sp = s["spines"]
    ports = s["srv_ports"]
    tags = {
        0: [("leaf switch, top of the network rack", lf["top"]), ("GPU servers, 8 GPUs each", (D.GPU_RACKS[0], D.TRAY_Y[2] + 20.0, 0.0)),
            ("spine switches", sp[1]["top"]), ("more rows, a leaf each", (0.0, D.RACK_H, D.ROW_Z[2]))],
        1: [("copper DAC: racks beside the leaf", (D.GPU_RACKS[1], D.CM_Y[0], 2.0)), ("AOC: the outer racks", (D.GPU_RACKS[3], D.CM_Y[0], 2.0)),
            ("800G NIC ports", ports[0]), ("32 downlinks", lf["down"][16])],
        2: [("switch ASIC: 51.2 Tb/s", lf["parts"]["heatsink"]), ("SerDes traces to 64 ports", lf["tr_down"][4][1]),
            ("fans blow front to back", lf["fans"][3])],
        3: [("32 uplinks, 800G optics", lf["up"][24]), ("single-mode fibre overhead", (200.0, D.TRAY_TOP + 6.0, -35.0)),
            ("to every spine", sp[0]["top"])],
        4: [("ECMP: flows hashed over 4 spines", (D.SPINE_X - 30.0, D.TRAY_TOP + 10.0, -300.0)),
            ("leaf to spine to leaf: 3 hops", (0.0, D.LEAF_Y + 14.0, D.ROW_Z[3])), ("every leaf meets every spine", sp[2]["top"])],
        5: [("queue on one uplink", lf["up"][9]), ("pause frames back to the NICs", ports[6]),
            ("32 down, 32 up: 1:1", lf["down"][28])],
        6: [("leaf", lf["top"]), ("spine", sp[3]["top"]), ("4 rows x 32 servers' ports", (D.GPU_RACKS[0], D.RACK_H, D.ROW_Z[1]))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((240.0, 120.0, -330.0), 980.0, 0.50, 0.45, pad=0.9),
        frame((0.0, 150.0, -10.0), 300.0, 0.15, 0.20),
        frame((0.0, D.LEAF_Y + 4.0, -28.0), 70.0, 0.35, 0.80),
        frame((200.0, 200.0, -200.0), 650.0, 0.45, 0.45, pad=0.9),
        frame((300.0, 150.0, -380.0), 1050.0, 0.35, 0.60, pad=0.85),
        frame((0.0, 160.0, -10.0), 260.0, -0.15, 0.18),
        frame((260.0, 120.0, -360.0), 1050.0, 0.55, 0.45, pad=0.85),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
