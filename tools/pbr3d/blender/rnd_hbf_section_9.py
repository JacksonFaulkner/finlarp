"""HBF section 9: who is building it, timing and risks (heading 9 of
tui/src/screens/diagrams_pages/RND_HBF.txt), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_9.py

Writes blender/rnd_hbf_section_9.blend and assets/rnd_hbf_section_9.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s9.rs):
  0 who        SanDisk and SK hynix stacks on the package; a ghost Samsung stack; Kioxia's PCIe
               card standing off the package
  1 timing     four milestones on a plinth, appearing left to right in date order: the MOU, the
               OCP spec, a sample stack, an inference device
  2 risks      back on the package: writes wear the flash (a wear meter drains), figures are
               claims and simulations, one interface does not make parts swappable
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, key, label, pivot, rel, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, DIE_HALF, GPU_X, GPU_Y1  # noqa: E402
from rnd_hbf_kit import HBF_TOP, HBF_XS  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_9"
BEATS = 3

# beat 1's milestones stand on their own plinth, right of the package
MILE_XS = (4700.0, 5800.0, 6900.0, 8000.0)
MILE_U = (0.05, 0.27, 0.49, 0.71)  # when each milestone appears (date order)

POSES = [
    ((1050.0, 260.0, 0.0), 7800.0, 0.14, 0.18),
    ((6300.0, 250.0, 0.0), 7200.0, 0.0, 0.20),
    ((700.0, 300.0, 0.0), 5600.0, 0.18, 0.16),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def kioxia_card(root, m, x0=2450.0, x1=3150.0):
    """A PCIe add-in card standing in a slot beside the package: green board, flash packages on
    its face, gold edge fingers."""
    g = HK.empty("kioxia", root)
    box("kx_slot", (x0 - 60, -80.0, -90.0), (x1 + 60, 30.0, 40.0), m["plinth"], g)
    box("kx_board", (x0, 30.0, -30.0), (x1, 560.0, 0.0), m["substrate"], g)
    box("kx_fingers", (x0 + 80, 30.0, -32.0), (x1 - 80, 70.0, 2.0), m["gold"], g)
    for i in range(3):
        cx = x0 + 50 + i * 220
        box(f"kx_chip{i}", (cx, 180.0, 0.0), (cx + 160, 420.0, 18.0), m["cmos"], g)
    return g


def samsung_ghost(root, m, x=-850.0):
    """A translucent outline of a stack where Samsung's own design would go."""
    g = HK.empty("samsung", root)
    box("ss_base", (x - BASE_HALF, 0.0, -BASE_HALF), (x + BASE_HALF, HK.BASE_T, 0.0), m["ghost"], g)
    box("ss_stack", (x - DIE_HALF, HK.BASE_T + 10.0, -DIE_HALF), (x + DIE_HALF, HBF_TOP, 0.0), m["ghost"], g)
    return g


def milestones(root, m):
    """Beat 1: the MOU, the spec, a sample stack and an inference device, each on the plinth."""
    x0, x1 = MILE_XS[0] - 500, MILE_XS[-1] + 500
    plinth = HK.gbox("mile_plinth", (x0, -80.0, -500.0), (x1, 0.0, 0.0), m["plinth"], root)
    show(plinth, beat(1))
    groups = []
    # 1 MOU: one signed sheet with two signature bars
    x = MILE_XS[0]
    g = HK.empty("mile_mou", root)
    box("mou_sheet", (x - 220, 0.0, -360.0), (x + 220, 10.0, -60.0), m["paper"], g)
    box("mou_sig_a", (x - 180, 10.0, -120.0), (x - 30, 16.0, -100.0), m["array"], g)
    box("mou_sig_b", (x + 30, 10.0, -120.0), (x + 180, 16.0, -100.0), m["base"], g)
    groups.append((g, (x, 20.0, -200.0)))
    # 2 OCP spec: a stack of sheets with a gold cover band
    x = MILE_XS[1]
    g = HK.empty("mile_spec", root)
    for i in range(5):
        off = 8.0 * i
        box(f"spec_sheet{i}", (x - 220 + off, i * 14.0, -380.0 + off), (x + 220 + off, i * 14.0 + 12.0, -60.0 + off), m["paper"], g)
    box("spec_band", (x - 200, 70.0, -230.0), (x + 240, 78.0, -190.0), m["gold"], g)
    groups.append((g, (x, 90.0, -200.0)))
    # 3 memory samples: one HBF stack
    x = MILE_XS[2]
    s = K.flash_stack(root, m, x, "mile_stack", z0=-60.0, detail=False, ucie=0)
    for bd in s.bonds:
        show(bd, [])
    for b in s.bumps:
        show(b, [])
    groups.append((s.g, (x, HBF_TOP, -100.0)))
    # 4 inference device: a small GPU with flash beside it on an interposer
    x = MILE_XS[3]
    g = HK.empty("mile_dev", root)
    box("dev_inter", (x - 420, 0.0, -420.0), (x + 420, 40.0, -60.0), m["interposer"], g)
    box("dev_gpu", (x - 380, 40.0, -360.0), (x + 20, 300.0, -120.0), m["gpu"], g)
    for i, sx in enumerate((x + 110, x + 290)):
        box(f"dev_hbf{i}", (sx - 70, 40.0, -300.0), (sx + 70, 320.0, -160.0), m["array"], g)
    groups.append((g, (x, 330.0, -200.0)))
    for (g, _), u in zip(groups, MILE_U):
        show(g, span(1, u, 2, 0.0))
    return [p for _, p in groups]


def wear_meter(root, m, x=2000.0):
    """Beat 2: a gauge beside the outer HBF stack whose hot fill drains as writes land."""
    frame = HK.gbox("wear_frame", (x - 10, -10.0, -60.0), (x + 90, 520.0, -40.0), m["grey"], root)
    show(frame, beat(2))
    at = (x + 40, 0.0, -30.0)
    pv = pivot("wear_pv", at, root)
    box("wear_fill", rel(at, (x + 5, 0.0, -40.0)), rel(at, (x + 75, 500.0, -20.0)), m["hot"], pv)
    # the fill drains from full to a quarter over the beat (a separate empty carries show())
    vis = HK.empty("wear_vis", root)
    pv.parent = vis
    show(vis, beat(2))
    for f, s in ((F(2, 0.1), 1.0), (F(2, 0.85), 0.25)):
        key(pv, f, "scale", (1.0, 1.0, s))
    return (x + 40, 520.0, -40.0)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)
    front = [K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1) for x in HBF_XS]
    for s in front:
        for bd in s.bonds:
            show(bd, [])
        for b in s.bumps:
            show(b, [])
    show(samsung_ghost(root, m), beat(0))
    show(kioxia_card(root, m), beat(0))
    pts = milestones(root, m)
    meter_top = wear_meter(root, m)

    # beat 2: writes (hot dots) land on the outer stack's top dies; reads (green) leave it
    x_out = HBF_XS[1]
    for i, tx in enumerate((-90.0, 0.0, 90.0)):
        HK.dots(root, m, f"wr{i}_", [(x_out + tx, HBF_TOP + 420.0, 0.0), (x_out + tx, HBF_TOP + 5.0, 0.0)],
                4, "heat", 2, 0.08 + 0.03 * i, 0.8, 40, size=16.0)
    HK.dots(root, m, "rd_", K.bus_path(HBF_XS[0]), 3, "data", 2, 0.2, 0.8, 70, size=24.0)

    sd, sk = HBF_XS
    tags0 = [
        ("SanDisk (SNDK)", (sd - DIE_HALF, 380.0, 0.0)),
        ("SK hynix", (sk + DIE_HALF, 380.0, 0.0)),
        ("Samsung: zHBF, early design", (-850.0, HBF_TOP, 0.0)),
        ("Kioxia: PCIe card, off-package", (2800.0, 560.0, 0.0)),
    ]
    for text, pos in tags0:
        label(text, pos, root, beat(0))
    dates = ["Feb 2026: MOU", "Aug 2026: first OCP spec", "H2 2026: memory samples", "early 2027: device samples"]
    for text, pos, u in zip(dates, pts, MILE_U):
        label(text, pos, root, span(1, u + 0.04, 2, 0.0))
    tags2 = [
        ("nothing on sale yet", (0.0, GPU_Y1 + 10.0, 0.0), 0.05),
        ("figures: claims and simulations", (-GPU_X, 120.0, 0.0), 0.25),
        ("writes wear the flash", meter_top, 0.45),
        ("one interface, not swappable parts", (sd - BASE_HALF, 40.0, 0.0), 0.65),
    ]
    for text, pos, u in tags2:
        label(text, pos, root, span(2, u, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
