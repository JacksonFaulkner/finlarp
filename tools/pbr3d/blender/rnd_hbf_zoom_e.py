"""The R&D HBF page's zoom-in e, "reads and writes", in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_zoom_e.py

Writes blender/rnd_hbf_zoom_e.blend and assets/rnd_hbf_zoom_e.glb. One beat is 8 s.

The overview's package held on the GPU with one HBM stack on its left and one HBF stack on its
right (rnd_hbf_kit.py on hbm_kit.py), plus a wear meter beside the flash stack.

Beats (match diagrams_nodes/hbf/zooms/e.rs):
  0 reads      weights stream down the HBF stack into the GPU; nothing is written
  1 writes     the KV cache is rewritten: most writes go to HBM, some to the flash, and the
               flash's wear meter climbs
  2 scheduler  writes to the flash nearly stop; the write-lifetime bars go from 1.2 to 14.8 years
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import TSV_X, die_top  # noqa: E402
from rnd_hbf_kit import HBF_TOP  # noqa: E402

PAGE = "rnd_hbf"
NAME = "zoom_e"
BEATS = 3

HBM_X, HBF_X = -850.0, 850.0
METER_X0, METER_Y = 620.0, 680.0  # the wear meter, laid flat over the flash stack
SEGS = 10
SEG_W, SEG_GAP, SEG_T = 38.0, 6.0, 40.0

POSES = [
    ((100.0, 330.0, 0.0), 3400.0, 0.16, 0.12),
    ((100.0, 430.0, 0.0), 3600.0, 0.14, 0.12),
    ((100.0, 470.0, 0.0), 3700.0, 0.12, 0.12),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def rev(path):
    return list(reversed(path))


def flash_reads(root, m, b, u0, u1, tag):
    """Weights read down the flash stack's TSVs, then across the interposer into the GPU."""
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"{tag}r{i}_", [(HBF_X + tx, HBF_TOP - 8, 0.0), (HBF_X + tx, 30.0, 0.0)],
                3, "page", b, u0, u0 + (u1 - u0) * 0.5, 60, size=13.0)
    HK.dots(root, m, f"{tag}b_", K.bus_path(HBF_X), 4, "data", b, u0 + (u1 - u0) * 0.4, u1, 70, size=24.0)


def writes(root, m, b, x, top, n, u0, u1, tag, size=18.0):
    """KV writes leave the GPU, cross the interposer to a stack and climb its TSVs."""
    HK.dots(root, m, f"{tag}b_", rev(K.bus_path(x)), n, "heat", b, u0, u1, 60, size=size)
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"{tag}u{i}_", [(x + tx, 30.0, 0.0), (x + tx, top - 10, 0.0)],
                max(1, n // 3), "heat", b, u0 + 0.12, min(0.95, u1 + 0.1), 50, size=size * 0.6)


def meter(root, m):
    """A wear meter over the flash stack, read left to right: a frame and segments that fill in
    beat 1."""
    x0, y0 = METER_X0, METER_Y
    w = SEGS * (SEG_W + SEG_GAP)
    frame = HK.gbox("wear_frame", (x0 - 10, y0 - 10, -60.0), (x0 + w + 4, y0 + SEG_T + 10, -40.0), m["grey"], root)
    show(frame, span(1, 0.0, 3, 0.0))
    for s in range(SEGS):
        lo = x0 + s * (SEG_W + SEG_GAP)
        g = HK.gbox(f"wear_{s}", (lo, y0, -40.0), (lo + SEG_W, y0 + SEG_T, -20.0), m["hot"], root)
        if s < 8:
            # beat 1: climbs one segment at a time; beat 2: back to two once the scheduler holds writes
            on = F(1, 0.15 + 0.08 * s)
            show(g, [(on, F(2, 0.15))] + (span(2, 0.15, 3, 0.0) if s < 2 else []))
        else:
            show(g, [])


def life_bars(root, m):
    """Beat 2: write lifetime, 1.2 years before the scheduler and 14.8 after (bars to scale),
    laid flat over the meter."""
    x0 = METER_X0
    y_old, y_new = METER_Y + 90.0, METER_Y + 160.0
    per_year = 30.0
    show(HK.gbox("life_old", (x0, y_old, -60.0), (x0 + 1.2 * per_year, y_old + 40.0, -20.0), m["gold"], root),
         span(2, 0.2, 3, 0.0))
    steps = 6
    for k in range(steps):
        lo = x0 + 14.8 * per_year * k / steps
        hi = x0 + 14.8 * per_year * (k + 1) / steps
        g = HK.gbox(f"life_new{k}", (lo, y_new, -60.0), (hi, y_new + 40.0, -20.0), m["array"], root)
        show(g, span(2, 0.35 + 0.06 * k, 3, 0.0))
    return (x0 + 1.2 * per_year, y_old + 20.0), (x0 + 14.8 * per_year, y_new + 20.0)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)
    HK.stack(root, m, HBM_X, 8, "hbm", phy=1)
    fs = K.flash_stack(root, m, HBF_X, "hbf", ucie=-1)
    for bd in fs.bonds:
        show(bd, [])
    for b in fs.bumps:
        show(b, [])
    show(K.gpu_glow(root, m), span(0, 0.5, 1, 0.0) + span(2, 0.5, 3, 0.0))

    # beat 0: reads only
    flash_reads(root, m, 0, 0.05, 0.85, "rd0")
    # beat 1: KV writes, mostly to HBM, some to the flash; weights still read
    writes(root, m, 1, HBM_X, die_top(7), 9, 0.08, 0.8, "kvh")
    writes(root, m, 1, HBF_X, HBF_TOP, 6, 0.12, 0.8, "kvf")
    meter(root, m)
    # beat 2: the scheduler keeps KV in HBM; one write in a long while reaches the flash
    flash_reads(root, m, 2, 0.05, 0.6, "rd2")
    writes(root, m, 2, HBM_X, die_top(7), 9, 0.08, 0.8, "kvh2")
    writes(root, m, 2, HBF_X, HBF_TOP, 1, 0.5, 0.55, "kvf2")
    p_old, p_new = life_bars(root, m)

    tags = {
        0: [("weights: read from HBF", (HBF_X, HBF_TOP + 20.0, 0.0)), ("into the GPU", (0.0, 400.0, 0.0)),
            ("read far more than written", (HBF_X + 200.0, 200.0, 0.0))],
    }
    late = {
        1: [("KV cache: rewritten constantly", (0.0, 400.0, 0.0), 0.05), ("kept mostly in HBM", (HBM_X, die_top(7) + 20.0, 0.0), 0.15),
            ("writes wear the flash", (METER_X0 + 300.0, METER_Y + 40.0, -20.0), 0.4)],
        2: [("94% fewer HBF KV writes", (HBF_X + 190.0, 300.0, 0.0), 0.1), ("1.2 yr", (p_old[0], p_old[1], -20.0), 0.25),
            ("14.8 yr write life (est.)", (p_new[0], p_new[1], -20.0), 0.7),
            ("KV writes: 5-13.9% of run time", (HBM_X, die_top(7) + 20.0, 0.0), 0.4)],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    for i, items in late.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
