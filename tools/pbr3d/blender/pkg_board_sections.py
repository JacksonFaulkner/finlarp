"""The BOARD page's nine numbered sections. Section N illustrates heading N of
tui/src/screens/diagrams_pages/PKG_BOARD.txt (10, Sources, is text only). Three beats each.

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_board_sections.py -- <n>

Writes assets/pkg_board_section_<n>.glb. The module, the 4x column close-up (at BY) and the tray and
rack (at TRAY_Y) come from pkg_board_detail.py.

  1 what happens    the module; power climbs; heat leaves into the coolant
  2 the parts       the column cut open: board half; package half; thermal half
  3 in order        VRM to plane; up the column; die to coolant
  4 power delivery  phases and plane; decoupling caps on the back; I x R per level
  5 cooling         heat up the column; coolant in the fins; the hoses in and out
  6 modules, links  the module's parts; die to NVLink connector; a tray to its switch
  7 racks           the rack; its coolant loop; switch trays and cables
  8 who makes it    makers tagged on chips, board and power, cooling and links
  9 chokepoints     rising power; air runs out; warpage at the corners
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_board_detail as K  # noqa: E402
from pkg_board_detail import frame, camera_path, run, present, tags, empty  # noqa: E402

PAGE = "pkg_board"
BEATS = 3
BY = K.BY
S4 = 4.0


def Y(y):
    return BY + y * S4


def col(m, root, beats_on):
    g = empty("col_grp", root)
    _, pts = K.column(m, g)
    present(g, [iv for b in beats_on for iv in beat(b)])
    return pts


def trayset(m, root, beats_on, gap=90.0):
    tr = empty("tray_grp", root)
    _, tp = K.tray(m, tr)
    K.switch_tray(m, tr, K.TRAY_Y + gap)
    K.nvl_cables(m, tr, K.TRAY_Y, K.TRAY_Y + gap)
    present(tr, [iv for b in beats_on for iv in beat(b)])
    return tp


def rackset(m, root, beats_on):
    rk = empty("rack_grp", root)
    _, ys, top = K.rack(m, rk)
    present(rk, [iv for b in beats_on for iv in beat(b)])
    return ys, top


V_WIDE = frame((0.0, 6.0, -60.0), 300.0, 0.45, 0.50)
V_CUT = frame((0.0, 12.0, 0.0), 130.0, 0.12, 0.12)
V_TOPCUT = frame((0.0, 34.0, -10.0), 110.0, 0.25, 0.25)
V_TRAY = frame((0.0, K.TRAY_Y + 40.0, -90.0), 430.0, 0.40, 0.40)
V_RACK = frame((0.0, K.TRAY_Y + 170.0, -80.0), 460.0, 0.55, 0.20, pad=1.0)


def sec1(m, root):
    s = K.module(m, root)
    K.swap(s, "sub", "sub_ghost", beat(1), F(BEATS, 0))
    present(s["dies"], [(0, F(2, 0))])
    present(s["dies_hot"], beat(2))
    K.swap(s, "plate", "plate_ghost", beat(2), F(BEATS, 0))
    K.power(m, root, "s1p", 1, ks=(0, 1))
    K.heat(m, root, "s1h", 2, n=8)
    K.coolant(m, root, "s1c", 2, n=12)
    tags(root, [
        [("module board", (-150.0, 0.0, -20.0)), ("GPU package under its cold plate", (0.0, K.COVER[1], -30.0)),
         ("VRM phases", (-98.0, 14.0, -36.0)), ("NVLink connector", (142.0, 12.0, -30.0))],
        [("hundreds of amps", (-98.0, 14.0, -10.0)), ("up through the BGA", (36.0, 1.5, 0.0)), ("into the die", (0.0, 24.0, 0.0))],
        [("every watt becomes heat", (0.0, 24.0, 0.0)), ("out through the lid", (40.0, K.LID[1], 0.0)), ("into the coolant", (-20.0, 38.0, 0.0))],
    ])
    camera_path(root, [V_WIDE, frame((-30.0, 6.0, -10.0), 170.0, 0.15, 0.25), V_TOPCUT])


def sec2(m, root):
    c = col(m, root, [0, 1, 2])
    tags(root, [
        [("BGA ball", c["ball"]), ("plated via", c["via"]), ("power plane", c["plane"]), ("solder mask + pads", (0.0, Y(0.0), 0.0))],
        [("ABF build-up + microvias", c["buildup"]), ("glass-fibre core", c["core"]), ("through-hole", c["pth"]), ("C4 bump", c["c4"]),
         ("TSV in silicon", c["tsv"]), ("RDL", c["rdl"]), ("microbump", c["ubump"]), ("GPU die", c["die"])],
        [("TIM1", c["tim1"]), ("lid", c["lid"]), ("TIM2", c["tim2"]), ("cold plate", c["plate"]), ("fins", c["fins"])],
    ])
    camera_path(root, [
        frame((0.0, Y(-4.0), 0.0), 90.0, 0.25, 0.12),
        frame((0.0, Y(14.0), 0.0), 100.0, 0.25, 0.10),
        frame((0.0, Y(34.0), 0.0), 85.0, 0.25, 0.14),
    ])


def sec3(m, root):
    s = K.module(m, root)
    for k in ("sub", "ip"):
        K.swap(s, k, k + "_ghost", beat(0), F(BEATS, 0))
    present(s["dies"], [(0, F(2, 0))])
    present(s["dies_hot"], beat(2))
    K.swap(s, "plate", "plate_ghost", beat(2), F(BEATS, 0))
    c = col(m, root, [1])
    K.power(m, root, "s3p", 0, sides=(-1,), ks=(0, 1, 2), n=5)
    run(root, "s3c", K.column_power(), 8, 2.2, m["amp"], 1, 0.0, 0.8, 80)
    K.heat(m, root, "s3h", 2, n=8)
    K.coolant(m, root, "s3c2", 2, n=12)
    tags(root, [
        [("1 VRM steps down to <1 V", (-98.0, 14.0, -10.0)), ("power plane", (-60.0, K.PWR_Y, 0.0))],
        [("2 ball", c["ball"]), ("through-hole", c["pth"]), ("C4", c["c4"]), ("TSV", c["tsv"]), ("3 the die", c["die"])],
        [("4 heat crosses the lid", (40.0, K.LID[1], 0.0)), ("5 coolant carries it off", (-20.0, 38.0, 0.0))],
    ])
    camera_path(root, [
        frame((-60.0, 4.0, -10.0), 140.0, -0.15, 0.25),
        frame((0.0, Y(10.0), 0.0), 110.0, 0.20, 0.10, pad=1.0),
        V_TOPCUT,
    ])


def sec4(m, root):
    s = K.module(m, root)
    present(s["lid"], [(F(1, 0), F(BEATS, 0))])
    present(s["plate"], [(F(1, 0), F(BEATS, 0))])
    c = col(m, root, [2])
    K.power(m, root, "s4p", 0, sides=(-1,), ks=(0, 1, 2, 3), n=4)
    for k, x in enumerate((-36.0, -20.0, 20.0, 36.0)):
        run(root, f"s4d{k}", [(x, K.BOT - 2.0, -3.0), (x, K.PWR_Y, -3.0), (x * 0.8, K.PWR_Y, -3.0)], 3, 1.4, m["v12"], 1, 0.05 + 0.05 * k, 0.8, 40)
    run(root, "s4c", K.column_power(), 8, 2.2, m["amp"], 2, 0.0, 0.8, 80)
    tags(root, [
        [("power stage: switches 12 V", (-84.0, 3.0, -10.0)), ("inductor: smooths it", (-104.0, 14.0, -36.0)),
         ("thick copper power plane", (-50.0, K.PWR_Y, 0.0))],
        [("MLCC decaps on the back", (0.0, K.BOT - 2.0, -3.0)), ("they cover fast load steps", (-30.0, K.BOT - 2.0, -15.0)),
         ("steel bolster plate", (-66.0, K.BOT - 5.0, -20.0))],
        [("I x R at the plane", c["plane"]), ("at the ball", c["ball"]), ("at the bumps", c["c4"]), ("the die gets ~0.8 V", c["die"])],
    ])
    camera_path(root, [
        frame((-80.0, 4.0, -30.0), 100.0, -0.35, 0.45),
        frame((0.0, K.BOT - 2.0, -20.0), 110.0, 0.30, -0.35),
        frame((0.0, Y(10.0), 0.0), 110.0, 0.20, 0.10, pad=1.0),
    ])


def sec5(m, root):
    s = K.module(m, root)
    present(s["dies"], [(F(1, 0), F(BEATS, 0))])
    present(s["dies_hot"], beat(0))
    K.swap(s, "plate", "plate_ghost", [(F(1, 0), F(BEATS, 0))], F(BEATS, 0))
    c = col(m, root, [0])
    for k, x in enumerate((-30.0, -15.0, 0.0, 15.0, 30.0)):
        run(root, f"s5h{k}", K.column_heat(x), 3, 2.2, m["heat"], 0, 0.04 * k, 0.8, 60)
    K.coolant(m, root, "s5c", 1, n=16)
    K.heat(m, root, "s5hh", 1, n=6, size=1.3)
    for k, x in enumerate((-22.0, 22.0)):
        mat_ = m["cool"] if k == 0 else m["heat"]
        pts = [(x, K.COVER[1] + 24.0, -150.0), (x, K.COVER[1] + 22.0, -70.0), (x, K.COVER[1] + 8.0, -60.0), (x, K.COVER[1], -60.0)]
        run(root, f"s5w{k}", pts if k == 0 else list(reversed(pts)), 6, 1.8, mat_, 2, 0.0, 0.8, 60)
    tags(root, [
        [("die: the heat source", c["die"]), ("TIM1", c["tim1"]), ("lid spreads it", c["lid"]), ("TIM2", c["tim2"]), ("into the plate", c["plate"])],
        [("coolant between fins", (-10.0, 38.0, 0.0)), ("fins add area", (25.0, K.FINS[1], 0.0))],
        [("cool water in", (-22.0, K.COVER[1] + 22.0, -80.0)), ("warm water out", (22.0, K.COVER[1] + 22.0, -80.0)),
         ("to the rack manifold", (0.0, K.COVER[1] + 24.0, -140.0))],
    ])
    camera_path(root, [
        frame((0.0, Y(30.0), 0.0), 100.0, 0.25, 0.12, pad=1.0),
        frame((0.0, 38.0, -10.0), 90.0, 0.25, 0.30),
        frame((0.0, 50.0, -80.0), 170.0, 0.70, 0.35),
    ])


def sec6(m, root):
    s = K.module(m, root)
    present(s["lid"], [(0, F(1, 0))])
    present(s["plate"], [(0, F(1, 0))])
    tp = trayset(m, root, [2])
    run(root, "s6s", K.signal_path(), 10, 1.3, m["sig"], 1, 0.0, 0.85, 70)
    for k in range(4):
        run(root, f"s6n{k}", K.nvl_path(k, K.TRAY_Y, K.TRAY_Y + 90.0), 5, 2.0, m["sig"], 2, 0.05 + 0.04 * k, 0.8, 60)
    tags(root, [
        [("MODULE: one board", (-150.0, 0.0, -20.0)), ("GPU package", (0.0, K.COVER[1], -30.0)), ("power stages", (-98.0, 14.0, -62.0)),
         ("connectors", (142.0, 12.0, -30.0))],
        [("NVLink lanes leave the die", (14.0, 22.0, 0.0)), ("through the board", (90.0, K.SIG_Y, 0.0)), ("out on twinax", (180.0, 14.0, -30.0))],
        [("modules on a tray", tp["mods"][0]), ("NVLink switch", (80.0, K.TRAY_Y + 100.0, -70.0)), ("many GPUs act as one", (0.0, K.TRAY_Y + 30.0, -160.0))],
    ])
    camera_path(root, [V_WIDE, frame((80.0, 8.0, -10.0), 180.0, 0.25, 0.25), V_TRAY])


def sec7(m, root):
    ys, top = rackset(m, root, [0, 1])
    tp = trayset(m, root, [2])
    for k, y in enumerate(ys):
        run(root, f"s7c{k}", [(-188.0, y + 20.0, -157.0), (188.0, y + 20.0, -157.0)], 4, 2.2, m["cool"], 1, 0.03 * k, 0.8, 80)
    run(root, "s7u", [(-188.0, K.TRAY_Y - 10.0, -168.0), (-188.0, top, -168.0)], 8, 2.6, m["cool"], 1, 0.0, 0.7, 80)
    run(root, "s7d", [(188.0, top, -168.0), (188.0, K.TRAY_Y - 10.0, -168.0)], 8, 2.6, m["heat"], 1, 0.1, 0.8, 80)
    for k in range(4):
        run(root, f"s7n{k}", K.nvl_path(k, K.TRAY_Y, K.TRAY_Y + 90.0), 5, 2.0, m["sig"], 2, 0.05 + 0.04 * k, 0.8, 60)
    tags(root, [
        [("RACK: trays stacked", (0.0, top, -80.0)), ("compute trays", (0.0, ys[0] + 14.0, -72.0)), ("switch trays", (0.0, K.TRAY_Y + 130.0, -70.0))],
        [("cool supply manifold", (-188.0, K.TRAY_Y + 100.0, -160.0)), ("warm return manifold", (188.0, K.TRAY_Y + 200.0, -160.0)),
         ("to a CDU (Network+Cool tab)", (0.0, top, -150.0))],
        [("GPU tray", tp["mods"][1]), ("NVLink cables", (0.0, K.TRAY_Y + 30.0, -160.0)), ("switch tray", (80.0, K.TRAY_Y + 100.0, -70.0))],
    ])
    camera_path(root, [V_RACK, frame((0.0, K.TRAY_Y + 170.0, -150.0), 460.0, -0.65, 0.15, pad=1.0), V_TRAY])


def sec8(m, root):
    s = K.module(m, root)
    K.swap(s, "plate", "plate_ghost", beat(2), F(BEATS, 0))
    present(s["lid"], [(0, F(1, 0)), (F(2, 0), F(BEATS, 0))])
    tags(root, [
        [("GPU: NVIDIA, AMD", (0.0, 24.0, 0.0)), ("CoWoS: TSMC", (-40.0, K.IP[1], 0.0)), ("HBM: SK hynix, Samsung, Micron", (38.0, 26.0, 0.0)),
         ("substrate: Ibiden, Unimicron", (-50.0, 8.0, 0.0))],
        [("VRM: Infineon, MPS, Renesas", (-98.0, 14.0, -10.0)), ("board + assembly: Foxconn, Quanta, Wistron", (-150.0, 0.0, -20.0)),
         ("MLCCs: Murata, Samsung EM", (0.0, K.BOT - 2.0, -3.0))],
        [("cold plates: Cooler Master, AVC, Boyd", (0.0, K.FINS[1], 0.0)), ("connectors + cables: Amphenol", (142.0, 12.0, -30.0)),
         ("CDUs: Vertiv", (0.0, K.COVER[1] + 24.0, -140.0))],
    ])
    camera_path(root, [V_CUT, frame((-60.0, 0.0, -20.0), 220.0, 0.35, 0.35), frame((40.0, 30.0, -40.0), 240.0, 0.45, 0.40)])


def sec9(m, root):
    s = K.module(m, root)
    present(s["dies"], [(F(2, 0), F(BEATS, 0))])
    present(s["dies_hot"], [(0, F(2, 0))])
    K.swap(s, "sub", "sub_ghost", beat(0), F(BEATS, 0))
    K.swap(s, "plate", "plate_ghost", beat(1), F(BEATS, 0))
    present(s["lid"], [(F(1, 0), F(BEATS, 0))])
    K.power(m, root, "s9p", 0, ks=(0, 1, 2, 3), n=6)
    K.heat(m, root, "s9h", 1, n=10)
    K.coolant(m, root, "s9c", 1, n=16)
    warp = empty("warp_grp", root)
    K.halfballs("warpballs", [(x, 1.5, 0.0) for x in (-52.0, -48.0, 48.0, 52.0)], K.BGA_R * 1.05, m["warp"], warp)
    present(warp, beat(2))
    tags(root, [
        [("power per package keeps rising", (0.0, 24.0, 0.0)), ("more amps, more I x R loss", (-60.0, K.PWR_Y, 0.0))],
        [("air cooling runs out", (0.0, K.COVER[1], -30.0)), ("liquid needs new plumbing", (-20.0, 38.0, 0.0))],
        [("bigger packages warp", (0.0, K.SUB_BU1[1], 0.0)), ("corner balls crack first", (52.0, 1.5, 0.0))],
    ])
    camera_path(root, [frame((-30.0, 8.0, -10.0), 170.0, 0.15, 0.25), V_TOPCUT, frame((25.0, 5.0, 0.0), 90.0, 0.10, 0.10)])


SECTIONS = {str(i): f for i, f in enumerate((sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9), start=1)}


def run_section(n):
    name = f"section_{n}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(K.materials())
    SECTIONS[n](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in SECTIONS:
        raise SystemExit("usage: blender -b --python pkg_board_sections.py -- <1..9>")
    run_section(argv[0])
