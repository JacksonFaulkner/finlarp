"""TRM_SOCAMM: the Terms-tab overview for SOCAMM LPDDR modules, on a Grace-style CPU board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_socamm.py

Writes assets/term_TRM_SOCAMM.glb. Captions live in specs/terms/TRM_SOCAMM.json.

A CPU package with flat SOCAMM modules screwed down on both sides (four LPDDR5X packages each,
compression connector underneath). One module lifts off to show it is replaceable. Bench bars
compare power per module against a DDR5 RDIMM.

Beats:
  0 board    CPU with SOCAMM modules lying flat beside it
  1 module   four LPDDR5X packages on a small board, compression connector
  2 swap     two screws out, the module lifts off: no soldering
  3 power    LPDDR power vs DDR5 RDIMM, bandwidth on the channels
  4 market   who makes it and why
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import trm_ddr_sdram as S  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty  # noqa: E402
from power_vrm_detail import bx, frame, present, run, tube  # noqa: E402

SLUG = "TRM_SOCAMM"
BEATS = [
    ("SOCAMM puts low-power LPDDR on a module beside the CPU",
     "NVIDIA's Grace and Vera CPUs use LPDDR, the phone-style DRAM, because it uses far less power than server DDR5. "
     "Until now LPDDR had to be soldered to the board. SOCAMM mounts it on small flat modules that sit right next to "
     "the CPU package."),
    ("Four LPDDR5X packages on a thin board",
     "Each module carries four stacked LPDDR5X packages on a board about 14 x 90 mm. There is no buffer chip: the "
     "short traces let LPDDR run at 8533 MT/s or more. A compression connector underneath replaces the gold-finger "
     "slot of a DIMM."),
    ("Two screws and it lifts off: memory becomes replaceable",
     "With soldered LPDDR, one bad chip scraps the whole CPU board and capacity is fixed at build time. A SOCAMM is "
     "held by screws, so a data centre can swap a failed module or fit a bigger one. That makes LPDDR practical for "
     "servers."),
    ("About a third of the power of DDR5 RDIMMs",
     "Memory makers quote SOCAMM at roughly one third the power of an RDIMM of the same capacity, with more "
     "bandwidth per module. Across a rack of Grace or Vera CPUs, that frees power for GPUs."),
    ("A new product line for memory makers",
     "Micron shipped SOCAMM first, with Samsung and SK hynix following; SOCAMM2 is being standardised at JEDEC. It "
     "adds an AI server memory line alongside HBM. Related: Micron (MU), Samsung (005930.KS), SK hynix (000660.KS), "
     "Nvidia (NVDA)."),
]

CPU = (-20.0, 0.0, -50.0)


def socamm(m, parent, name, x0, z0, w=16.0, l=80.0):
    """A flat module from (x0, z0) running along z. Returns dict of points."""
    g = empty(name, parent)
    bx(f"{name}_con", (x0 + 1, 0.0, z0 + 4), (x0 + w - 1, 2.0, z0 + l - 4), m["dark"], g)
    bx(f"{name}_pcb", (x0, 2.0, z0), (x0 + w, 3.2, z0 + l), m["mask"], g)
    pk = []
    for k in range(4):
        za = z0 + 5 + k * (l - 10) / 4
        bx(f"{name}_lp{k}", (x0 + 2, 3.2, za + 1), (x0 + w - 2, 5.0, za + (l - 10) / 4 - 1), m["mold"], g)
        pk.append((x0 + w / 2, 5.0, za + (l - 10) / 8))
    scr = []
    for z in (z0 + 2.0, z0 + l - 2.0):
        tube(f"{name}_scr{z:.0f}", (x0 + w / 2, 3.2, z), (x0 + w / 2, 4.6, z), 1.2, m["steel"], g, 12)
        scr.append((x0 + w / 2, 4.6, z))
    return g, {"pk": pk, "scr": scr, "con": (x0 + w, 1.0, z0 + l / 2), "top": (x0 + w / 2, 5.0, z0 + l / 2)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    S.mobo(m, root, x0=-110.0, x1=180.0)
    S.cpu(m, root, c=CPU, s=40.0, hot=[0])
    mods = []
    for k, x0 in enumerate((-78.0, -60.0, 8.0, 26.0)):
        g, p = socamm(m, root, f"so{k}", x0, -90.0)
        mods.append((g, p))
    # the outer right module: in place except in beat 2, where a lifted copy shows instead
    g3, p3 = mods[3]
    present(g3, [(F(0, 0), F(2, 0.1)), (F(3, 0), F(5, 0))])
    lift = empty("lift", root)
    lg, lp = socamm(m, lift, "solift", 26.0, -90.0)
    lg.location = (14.0, 22.0, 0.0)
    lg.rotation_euler = (0.0, 0.0, 0.35)
    present(lift, [(F(2, 0.1), F(3, 0))])
    # bandwidth beads module -> CPU
    for k, (g, p) in enumerate(mods):
        for j in range(4):
            a = p["pk"][j]
            ex = CPU[0] + (24.0 if a[0] > CPU[0] else -24.0)
            path = [a, (ex, 1.0, a[2] * 0.5 + CPU[2] * 0.5)]
            C.trace(m, root, f"t{k}{j}", [(a[0], 0.0, a[2]), (ex, 0.0, path[1][2])], w=0.8)
            run(root, f"b{k}{j}", path, 3, 0.7, m["bit"], [0, 3], 0.0, 0.8, 25)
    for k, s in enumerate(p3["scr"]):  # screws glow before removal
        gl = empty(f"scrglow{k}", root)
        bx(f"scrglow{k}_b", (s[0] - 1.6, s[1], s[2] - 1.6), (s[0] + 1.6, s[1] + 0.4, s[2] + 1.6), m["h_amber"], gl)
        present(gl, [(F(2, 0), F(2, 0.1))])

    tops = [S.bar(m, root, "pw0", 100.0, -60.0, 14.0, 36.0, "steel", 3, 5),
            S.bar(m, root, "pw1", 128.0, -60.0, 14.0, 12.0, "copper", 3, 5)]

    C.tags(root, {
        0: [("CPU package", (CPU[0], 6.4, CPU[2])), ("SOCAMM modules, lying flat", mods[1][1]["top"]),
            ("LPDDR5X to the CPU", mods[2][1]["pk"][1])],
        1: [("4 LPDDR5X packages", p3["pk"][2]), ("compression connector", p3["con"]), ("no buffer chip", p3["pk"][0])],
        2: [("module lifted out", (40.0, 27.0, -50.0)), ("screws, not solder", p3["scr"][0]),
            ("swap or upgrade capacity", (34.0, 2.0, -50.0))],
        3: [("DDR5 RDIMM power", tops[0]), ("SOCAMM ~1/3 the power", tops[1])],
        4: [("Micron first; Samsung, SK hynix", mods[0][1]["top"]), ("SOCAMM2 at JEDEC", mods[2][1]["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((-20.0, 4.0, -50.0), 160.0, 0.30, 0.70),
        frame((34.0, 4.0, -50.0), 90.0, 0.40, 0.55),
        frame((34.0, 12.0, -50.0), 110.0, 0.40, 0.40),
        frame((114.0, 18.0, -60.0), 80.0, 0.25, 0.30),
        frame((10.0, 4.0, -50.0), 220.0, 0.30, 0.55),
    ], root)


if __name__ == "__main__":
    build()
