"""The MICROBUMP overview (PACKAGING tab), rebuilt on the POWER-page pattern: the whole 2.5D package
cut open along z = 0 so every joint level shows in section (pkg_microbump_detail.py).

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_microbump_overview.py

Writes assets/pkg_microbump_overview.glb. Beats (match diagrams_nodes/packaging/microbump/overview.rs):
  0 the package cut open   board, BGA, substrate, C4, interposer, microbumps, logic die and HBM
  1 three levels of joints the levels lift apart: BGA balls, C4 bumps, microbumps
  2 inside one microbump   close on the cut row: pad, solder, nickel, copper pillar, die pad
  3 signals and power      power climbs BGA > PTH > C4 > TSV > microbump; a signal crosses the RDL
  4 underfill              epoxy fills under the dies and under the interposer
  5 heat and stress        the die heats; the corner joints take the strain
  6 hybrid bonds           the bumps vanish; the die bonds flat, copper to copper
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_microbump_detail as K  # noqa: E402
from power_vrm_detail import camera_path, run, rise  # noqa: E402

PAGE = "pkg_microbump"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def steps(obj, seq):
    """seq: [(beat, dy)]: ramp to dy over the first 40% of that beat, hold."""
    keys, prev = [], 0.0
    for b, dy in seq:
        keys += [(F(b, 0.0), prev), (F(b, 0.4), dy)]
        prev = dy
    K.lower(obj, keys)


def power_and_signal(m, root, beats, tag="ov"):
    for k, x in enumerate((K.POWER_X, K.POWER_X + 9.0, K.POWER_X + 18.0)):
        run(root, f"{tag}_pwr{k}", K.power_path(x), 6, 0.35, m["pwr"], beats, 0.05 + 0.04 * k, 0.85, 70)
    run(root, f"{tag}_sig", K.signal_path(), 8, 0.22, m["sig"], beats, 0.0, 0.9, 40)


def build():
    m, root = start("overview", beats=BEATS, page=PAGE)
    m.update(K.materials())
    s = K.stack(m, root, hybrid=True)
    die, hb = s["die"], s["hbm_grp"]

    # beat 1 lifts the levels apart; beat 2 closes them again; beat 6 drops the die onto the hybrid layer
    steps(die, [(1, 7.0), (2, 0.0), (6, -0.96)])
    steps(hb, [(1, 7.0), (2, 0.0)])
    steps(s["ip"], [(1, 3.5), (2, 0.0)])
    for g in (s["board"], s["bga"]):
        steps(g, [(1, -4.0), (2, 0.0)])

    show(s["uf_die"], span(0, 0.0, 1, 0.0) + span(4, 0.35, 6, 0.0))
    show(s["uf_c4"], span(0, 0.0, 1, 0.0) + span(4, 0.15, 7, 0.0))
    show(s["ub_joint"], span(0, 0.0, 6, 0.3))
    show(s["ip_pads"], span(0, 0.0, 6, 0.3))
    show(s["hyb"], span(6, 0.3, 7, 0.0))

    power_and_signal(m, root, [3])
    # underfill wicking in from the die edge (beat 4)
    run(root, "ov_uf", [(K.LOGIC_X[0] - 2.0, 8.6, K.ZB), (K.HBM_X[1], 8.6, K.ZB)], 10, 0.3, m["melt"], 4, 0.0, 0.35, 60)
    run(root, "ov_uf2", [(-36.0, 3.0, K.ZB), (34.0, 3.0, K.ZB)], 10, 0.5, m["melt"], 4, 0.0, 0.2, 60)
    # heat and the stressed corner joints (beat 5)
    rise(root, "ov_heat", (-11.0, K.DIE_TOP + 0.3, -6.0), 12, 0.35, m["heat"], 5, 0.05, 0.85, 8.0, 60, (12.0, 5.0))
    for x in (K.UB_XS[0], K.UB_XS[1]):
        K.glow_box(m, root, f"ov_st{x}", (x - 0.3, 8.0, -0.2), (x + 0.3, 9.2, 0.25), m["stress"], span(5, 0.3, 6, 0.0))
    for x in (K.C4_XS[0], K.C4_XS[-1]):
        K.glow_box(m, root, f"ov_stc{x}", (x - 1.2, 1.7, -0.2), (x + 1.2, 3.9, 0.3), m["stress"], span(5, 0.3, 6, 0.0))

    p = s["pts"]
    tags(root, [
        [("logic die", p["logic"]), ("HBM stack", p["hbm"]), ("silicon interposer", p["ip"]), ("substrate", p["sub"]), ("board", p["board"])],
        [("MICROBUMP ~40 um", (K.UB_XS[8], 8.6 + 7.0, 0.3)), ("C4 BUMP ~150 um", (p["c4"][0], p["c4"][1] + 3.5, 0.4)), ("BGA ~1 mm", (p["bga"][0], p["bga"][1] - 4.0, 0.4))],
        [("CU PILLAR", (K.UB_XS[2], 8.85, 0.3)), ("solder cap", (K.UB_XS[4], 8.25, 0.3)), ("RDL", (-24.0, 7.5, 0.2)), ("TSV", p["tsv"])],
        [("power: up every level", (K.POWER_X, -3.0, K.ZB)), ("TSV", p["tsv"]), ("signal across the RDL", (5.5, 7.6, K.ZB))],
        [("UNDERFILL under the dies", (-6.0, 8.6, 0.2)), ("underfill under the interposer", (0.0, 3.0, 0.2))],
        [("die heats and expands", p["logic"]), ("corner joints strain", (K.UB_XS[0], 8.6, 0.3)), ("CTE mismatch", (K.C4_XS[0], K.C4_Y, 0.4))],
        [("HYBRID BOND: no bumps", (-16.0, 8.1, 0.2)), ("copper to copper", (-20.0, 8.1, 0.2))],
    ])
    camera_path(root, [
        K.frame((0.0, -1.0, -4.0), 78.0, 0.35, 0.28),
        K.frame((-4.0, 1.0, -4.0), 80.0, 0.30, 0.10),
        K.frame((-21.0, 8.4, 0.0), 9.0, 0.18, 0.10),
        K.frame((-10.0, 0.0, 0.0), 44.0, 0.12, 0.05),
        K.frame((-14.0, 5.5, 0.0), 30.0, 0.20, 0.15),
        K.frame((-18.0, 7.0, -2.0), 36.0, 0.35, 0.30),
        K.frame((-18.0, 8.6, 0.0), 10.0, 0.20, 0.12),
    ])
    return root


if __name__ == "__main__":
    K.finish(build(), "overview", PAGE)
