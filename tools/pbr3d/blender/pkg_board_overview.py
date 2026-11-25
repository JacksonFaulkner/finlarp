"""The BOARD overview (PACKAGING tab): one GPU module cut through its middle (pkg_board_detail.py).

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_board_overview.py

Writes assets/pkg_board_overview.glb. Seven beats of 8 s (diagrams_nodes/packaging/board/overview.rs):
  0 the package on its module   board, VRM phases, package, lid, cold plate, NVLink connector
  1 BGA balls underneath        the cut face: half balls on pads between board and substrate
  2 power climbs the levels     red current from the phases, plane, via, ball, PTH, C4, TSV, die
  3 all of it becomes heat      the dies glow; heat climbs through TIM1, lid, TIM2 into the plate
  4 lid, TIM and cold plate     the thermal stack named layer by layer
  5 liquid cooling              coolant runs between the skived fins (cover see-through)
  6 trays linked by NVLink      four modules on a tray, cables to a switch tray, signals riding
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_board_detail as K  # noqa: E402
from pkg_board_detail import frame, camera_path, run, present, tags  # noqa: E402

PAGE = "pkg_board"
NAME = "overview"
BEATS = 7


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(K.materials())
    s = K.module(m, root)
    T = F(BEATS, 0)
    end6 = [(0, F(6, 0))]
    for k in ("board", "bga", "dies", "back", "vrm", "nvl"):
        present(s[k], end6)
    K.swap(s, "sub", "sub_ghost", beat(2), F(6, 0))
    K.swap(s, "ip", "ip_ghost", beat(2), F(6, 0))
    present(s["lid"], [(0, F(2, 0)), (F(3, 0), F(6, 0))])
    present(s["lid_ghost"], beat(2))
    present(s["plate"], [(0, F(2, 0)), (F(3, 0), F(5, 0))])
    present(s["plate_ghost"], beat(5))
    present(s["dies"], [(0, F(3, 0)), (F(4, 0), F(6, 0))])
    present(s["dies_hot"], beat(3))
    K.power(m, root, "pw", 2, ks=(0, 1, 2))
    K.heat(m, root, "ht", 3, n=10)
    K.heat(m, root, "ht5", 5, n=5, size=1.3)
    K.coolant(m, root, "cl", 5, n=16)

    tr = K.empty("tray_grp", root)
    _, tp = K.tray(m, tr)
    K.switch_tray(m, tr, K.TRAY_Y + 90.0)
    K.nvl_cables(m, tr, K.TRAY_Y, K.TRAY_Y + 90.0)
    present(tr, beat(6))
    for k in range(4):
        run(root, f"nv{k}", K.nvl_path(k, K.TRAY_Y, K.TRAY_Y + 90.0), 5, 1.6, m["sig"], 6, 0.05 + 0.04 * k, 0.8, 60)

    Y = K.TRAY_Y
    tags(root, [
        [("GPU package", (0.0, K.COVER[1], -30.0)), ("VRM phases", (-98.0, 14.0, -36.0)), ("NVLink connector", (142.0, 12.0, -30.0)),
         ("module board", (-150.0, 0.0, -20.0))],
        [("BGA balls, ~1 mm pitch", (30.0, 1.5, 0.0)), ("substrate", (-50.0, 8.0, 0.0)), ("board", (-80.0, -4.0, 0.0))],
        [("VRM: under 1 V", (-98.0, 14.0, -10.0)), ("power plane", (-60.0, K.PWR_Y, 0.0)), ("up the BGA, substrate, C4", (36.0, 8.0, 0.0)),
         ("into the die", (10.0, 24.0, 0.0))],
        [("~1,000 W of heat", (0.0, 24.0, 0.0)), ("through the lid", (30.0, K.LID[1], 0.0))],
        [("TIM1", (-40.0, K.TIM1[1], 0.0)), ("lid", (45.0, K.LID[1], 0.0)), ("TIM2", (-46.0, K.TIM2[1], 0.0)),
         ("cold plate fins", (20.0, K.FINS[1], 0.0))],
        [("coolant between fins", (-20.0, 38.0, 0.0)), ("in (cool)", (-22.0, K.COVER[1] + 22.0, -70.0)), ("out (warm)", (22.0, K.COVER[1] + 22.0, -70.0))],
        [("four GPU modules", tp["mods"][1]), ("NVLink cables", (0.0, Y + 30.0, -160.0)), ("switch tray", (80.0, Y + 100.0, -70.0))],
    ])
    camera_path(root, [
        frame((0.0, 6.0, -60.0), 300.0, 0.45, 0.50),
        frame((0.0, 4.0, 0.0), 70.0, 0.12, 0.08),
        frame((-30.0, 6.0, -10.0), 170.0, 0.15, 0.25),
        frame((0.0, 30.0, 0.0), 90.0, 0.10, 0.12),
        frame((0.0, 32.0, 0.0), 100.0, 0.25, 0.18),
        frame((0.0, 38.0, -20.0), 110.0, 0.30, 0.45),
        frame((0.0, Y + 40.0, -80.0), 430.0, 0.35, 0.40),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
