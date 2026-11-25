"""Zoom-ins (a-e) for the BOARD page, three beats each, own cameras and beads
(diagrams_nodes/packaging/board/zooms.rs):

  a BGA to the board              the ball field; one joint cut open at 4x; power and signal ride it
  b power climbs the levels       phases and plane; up the column; voltage lost at every level
  c cooling: cold plate, liquid   heat off the die into TIM1; the lid and TIM2; coolant in the fins
  d modules and NVLink            die to connector; the connector and twinax; tray to switch tray
  e size and cooling              a liquid-cooled rack; coolant through its manifolds; warpage

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_board_zooms.py -- a

Writes assets/pkg_board_zoom_<letter>.glb.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_board_detail as K  # noqa: E402
from pkg_board_detail import frame, camera_path, run, rise, present, tags, empty, bx  # noqa: E402

PAGE = "pkg_board"
BEATS = 3
T = None


def col(m, root, beats_on):
    g = empty("col_grp", root)
    _, pts = K.column(m, g)
    present(g, [iv for b in beats_on for iv in beat(b)])
    return pts


def zoom_a(m, root):
    s = K.module(m, root)
    c = col(m, root, [1, 2])
    for x in (-36.0, -20.0, 20.0, 36.0):
        run(root, f"a_p{x}", [(x, K.PWR_Y, 0.4), (x, K.BGA[1] + 1.0, 0.4)], 3, 1.2, m["amp"], 0, 0.1, 0.8, 40)
    run(root, "a_cp", K.column_power()[:4], 6, 2.2, m["amp"], 2, 0.0, 0.8, 60)
    sp = [(-28.0, K.BY - 1.0 * 4, 0.6), (0.0, K.BY - 1.0 * 4, 0.6), (0.0, K.BY + 13.0 * 4, 0.6)]
    run(root, "a_sig", sp, 5, 1.8, m["sig"], 2, 0.1, 0.85, 50)
    tags(root, [
        [("~1 mm pitch", (8.0, 1.5, 0.0)), ("thousands of balls", (-40.0, 1.5, 0.0)), ("board pads", (-20.0, 0.0, 0.0)),
         ("substrate pads", (20.0, 3.0, 0.0))],
        [("solder ball", c["ball"]), ("copper pad, gold finish", (0.0, K.BY + 0.3 * 4, 0.0)), ("plated via", c["via"]),
         ("power plane", c["plane"])],
        [("power: many balls in parallel", c["ball"]), ("signal: one ball each", (-20.0, K.BY - 4.0, 0.0)), ("plane under it", c["plane"])],
    ])
    camera_path(root, [
        frame((0.0, 1.5, 0.0), 60.0, 0.05, 0.05),
        frame((0.0, K.BY + 0.0, 0.0), 80.0, 0.20, 0.10),
        frame((-4.0, K.BY + 0.0, 0.0), 95.0, 0.25, 0.12),
    ])
    return s


def zoom_b(m, root):
    s = K.module(m, root)
    for k in ("sub", "ip"):
        K.swap(s, k, k + "_ghost", [(F(1, 0), F(2, 0))], F(BEATS, 0))
    present(s["lid"], [])
    present(s["plate"], [])
    c = col(m, root, [2])
    K.power(m, root, "b0", 0, sides=(-1,), ks=(0, 1, 2, 3), n=4)
    K.power(m, root, "b1", 1, ks=(0, 2), n=6)
    run(root, "b_col", K.column_power(), 8, 2.2, m["amp"], 2, 0.0, 0.8, 80)
    tags(root, [
        [("power stage", (-84.0, 3.0, -10.0)), ("inductor", (-104.0, 14.0, -10.0)), ("output caps", (-60.0, 2.4, -10.0)),
         ("thick power plane", (-50.0, K.PWR_Y, 0.0))],
        [("via + ball", (36.0, 1.5, 0.0)), ("through-hole in the core", (-36.0, 8.0, 0.0)), ("C4 + TSV", (20.0, 16.0, 0.0)),
         ("into the die", (0.0, 24.0, 0.0))],
        [("I x R lost at the plane", c["plane"]), ("at the ball", c["ball"]), ("at the bumps", c["c4"]), ("the die gets ~0.8 V", c["die"])],
    ])
    camera_path(root, [
        frame((-70.0, 4.0, -30.0), 110.0, -0.35, 0.40),
        frame((0.0, 8.0, 0.0), 110.0, 0.10, 0.12),
        frame((0.0, K.BY + 40.0, 0.0), 110.0, 0.20, 0.10, pad=1.0),
    ])
    return s


def zoom_c(m, root):
    s = K.module(m, root)
    present(s["dies"], [])
    present(s["dies_hot"], [(0, F(BEATS, 0))])
    K.swap(s, "plate", "plate_ghost", beat(2), F(BEATS, 0))
    K.heat(m, root, "c0", 0, n=8)
    K.heat(m, root, "c1", 1, n=10)
    K.coolant(m, root, "c2", 2, n=16)
    K.heat(m, root, "c2h", 2, n=6, size=1.3)
    tags(root, [
        [("the die: nearly all the power", (-10.0, 24.0, 0.0)), ("TIM1: metal or gel", (30.0, K.TIM1[1], 0.0))],
        [("copper lid, nickel plated", (40.0, K.LID[1], 0.0)), ("TIM2: grease or pad", (-40.0, K.TIM2[1], 0.0)),
         ("lid glued to substrate", (50.0, 14.0, 0.0))],
        [("skived copper fins", (25.0, K.FINS[1], 0.0)), ("coolant flows between", (-10.0, 38.0, 0.0)),
         ("heat into the water", (0.0, K.PLATE[1], 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 25.0, 0.0), 70.0, 0.10, 0.10),
        frame((15.0, 29.0, 0.0), 75.0, 0.20, 0.12),
        frame((0.0, 38.0, -20.0), 100.0, 0.30, 0.42),
    ])
    return s


def zoom_d(m, root):
    s = K.module(m, root)
    present(s["lid"], [])
    present(s["plate"], [])
    tr = empty("tray_grp", root)
    _, tp = K.tray(m, tr)
    K.switch_tray(m, tr, K.TRAY_Y + 90.0)
    K.nvl_cables(m, tr, K.TRAY_Y, K.TRAY_Y + 90.0)
    present(tr, beat(2))
    run(root, "d_sig", K.signal_path(), 10, 1.3, m["sig"], [0, 1], 0.0, 0.85, 70)
    for k in range(4):
        run(root, f"d_nv{k}", K.nvl_path(k, K.TRAY_Y, K.TRAY_Y + 90.0), 5, 2.0, m["sig"], 2, 0.05 + 0.04 * k, 0.8, 60)
    tags(root, [
        [("from the GPU die", (14.0, 22.0, 0.0)), ("down through the package", (32.0, 8.0, 0.0)), ("a trace in the board", (90.0, K.SIG_Y, 0.0))],
        [("NVLink connector", (142.0, 12.0, -10.0)), ("gold contacts", (140.0, 6.0, 0.0)), ("twinax cables", (180.0, 14.0, -30.0))],
        [("four GPUs per tray", tp["mods"][0]), ("cables at the back", (0.0, K.TRAY_Y + 20.0, -160.0)),
         ("NVLink switch tray", (80.0, K.TRAY_Y + 100.0, -70.0))],
    ])
    camera_path(root, [
        frame((60.0, 8.0, 0.0), 160.0, 0.15, 0.15),
        frame((150.0, 8.0, -20.0), 90.0, 0.55, 0.30),
        frame((0.0, K.TRAY_Y + 40.0, -90.0), 430.0, -0.45, 0.35),
    ])
    return s


def zoom_e(m, root):
    rk = empty("rack_grp", root)
    _, ys, top = K.rack(m, rk)
    present(rk, [(0, F(2, 0))])
    for k, y in enumerate(ys):
        run(root, f"e_c{k}", [(-188.0, y + 20.0, -157.0), (188.0, y + 20.0, -157.0)], 4, 2.2, m["cool"], 1, 0.03 * k, 0.8, 80)
    run(root, "e_up", [(-188.0, K.TRAY_Y - 10.0, -168.0), (-188.0, top, -168.0)], 8, 2.6, m["cool"], 1, 0.0, 0.7, 80)
    run(root, "e_dn", [(188.0, top, -168.0), (188.0, K.TRAY_Y - 10.0, -168.0)], 8, 2.6, m["heat"], 1, 0.1, 0.8, 80)
    s = K.module(m, root, extras=False)
    for k in ("board", "bga", "sub", "ip", "dies", "lid", "plate"):
        present(s[k], beat(2))
    warp = empty("warp_grp", root)
    for k, x in enumerate((-52.0, -48.0, 48.0, 52.0)):
        o = K.halfballs(f"wb{k}", [(x, 1.5, 0.0)], K.BGA_R * 1.05, m["warp"], warp)
        o.name = f"warpball{k}"
    present(warp, beat(2))
    tags(root, [
        [("a liquid-cooled rack", (0.0, top, -80.0)), ("compute trays", (0.0, ys[0] + 14.0, -72.0)), ("switch trays", (0.0, K.TRAY_Y + 130.0, -70.0))],
        [("cool water up one side", (-188.0, K.TRAY_Y + 100.0, -160.0)), ("warm water down the other", (188.0, K.TRAY_Y + 200.0, -160.0)),
         ("a loop to every plate", (0.0, ys[1] + 20.0, -146.0))],
        [("bigger packages warp more", (0.0, K.SUB_BU1[1], 0.0)), ("corner balls strain most", (52.0, 1.5, 0.0)),
         ("stiffener and bolster fight it", (-60.0, -4.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, K.TRAY_Y + 170.0, -80.0), 460.0, 0.55, 0.20, pad=1.0),
        frame((0.0, K.TRAY_Y + 170.0, -150.0), 460.0, -0.65, 0.15, pad=1.0),
        frame((20.0, 6.0, 0.0), 110.0, 0.10, 0.10),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(K.materials())
    ZOOMS[letter](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python pkg_board_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
