"""The R&D 3D DRAM page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_overview.py

Writes blender/rnd_3d_dram_overview.blend and assets/rnd_3d_dram_overview.glb. One beat is 8 s.

Three subjects side by side, all cut open at z = 0 (rnd_3d_dram_kit.py): today's planar 6F2 cells
on the left, a 4F2 VCT cell array bonded onto its periphery in the middle, and a stacked 3D DRAM
block on the right.

Beats (match the seven beats in diagrams_nodes/dram3d/overview.rs):
  0 planar     six planar 1T1C cells: transistor flat in the silicon, tall capacitor, 6F2 tile
  1 stall      the capacitors squeeze narrower and stretch taller through a red yield line
  2 VCT        the 4F2 array (still lifted): pillars, wrapped word lines, buried bit lines
  3 bonding    the array comes down onto its periphery wafer; the Cu-Cu bond line glows
  4 stacked    eight layers of sideways cells pull apart around the vertical bit lines
  5 floating   holes pile up in one pillar's body; the Id-Vg curve slides left
  6 road       all three, with the reported dates
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, label  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "overview"
BEATS = 7

XP, XV, XS = -3000.0, 0.0, 3300.0  # planar row, VCT bonded die, stacked block
LIFT = 1200.0  # the VCT array hangs this far above its periphery until beat 3
STEP = 70.0  # stacked layer pull-apart per layer

POSES = [
    ((XP, 750.0, -200.0), 6600.0, 0.35, 0.16),
    ((XP, 1150.0, -200.0), 7600.0, 0.35, 0.14),
    ((XV, 2250.0, -500.0), 5300.0, 0.45, 0.28),
    ((XV, 900.0, -300.0), 7600.0, 0.35, 0.16),
    ((XS, 1200.0, -300.0), 7000.0, 0.30, 0.16),
    ((-960.0, 600.0, 0.0), 2500.0, 0.10, 0.06),
    ((450.0, 800.0, -300.0), 15500.0, 0.22, 0.14),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    # ---- planar 6F2 row ----
    pa = K.planar_array(root, m, (XP, 0.0, 0.0), nx=3, nz=2, name="pa")
    c1 = pa.cells[(1, 0)]
    for (i, j), c in pa.cells.items():
        if j == 0:
            on(c.charge, span(0, 0.0, 2, 0.0) + beat(6))
    on(c1.tile, beat(0) + span(2, 0.0, 7, 0.0))  # off while the capacitors stretch through it
    on(c1.wl_on, span(0, 0.45, 0, 0.95))
    on(c1.chan_on, span(0, 0.5, 0, 0.95))
    on(c1.bl_on, span(0, 0.6, 0, 0.98))
    K.beads(root, m, "pread", c1.read_path, 4, 0, 0.5, 0.75, life=60)
    for cap in pa.caps:
        scale_keys(cap, [(F(1, 0.1), 1.0), (F(1, 0.6), (0.58, 0.58, 1.35)), (F(1, 0.99), (0.58, 0.58, 1.35)), (F(2, 0.0), 1.0)])
    wall = K.hidden("yield_wall", root)
    box("yield_wall_m", (XP - 1000, 2380, -560), (XP + 1000, 2410, 220), m["wall"], wall)
    on(wall, span(1, 0.55, 2, 0.0))

    # ---- VCT array on its periphery ----
    bd = K.bonded_die(root, m, (XV, 0.0, 0.0), nx=4, nz=4, name="bd", holes_at=[(0, 0)], tile_at=(2, 0))
    arr = bd.arr
    K.lift(bd.top, [(0, LIFT), (F(3, 0.12), LIFT), (F(3, 0.55), 0.0)])
    on(bd.line, span(3, 0.55, 3, 1.0) + beat(6))
    on(arr.wl_on[1], span(2, 0.3, 2, 0.95))
    on(arr.bl_on[0], span(2, 0.5, 2, 0.95))
    for i in range(4):
        on(arr.cells[(i, 0)].charge, span(2, 0.0, 4, 0.0) + beat(6))
    for p in bd.peri.sa_on:
        on(p, span(3, 0.65, 4, 0.0))
    for p in bd.peri.dec_on:
        on(p, span(3, 0.75, 4, 0.0))
    # a read in beat 2: down cell (1,0) into its bit line (array still lifted: offset the path)
    rp = [(x, y + LIFT, z) for x, y, z in arr.cells[(1, 0)].read_path]
    K.beads(root, m, "vread", rp, 4, 2, 0.55, 0.8, life=55)
    # beat 3: once bonded, signals drop through the pads into the sense amps
    for i, x in enumerate(arr.xs[1:3]):
        K.beads(root, m, f"bdrop{i}", [(x - 100, K.V_BASE + 30, 14.0), (x - 100, -K.PE_BOND - 60, 14.0),
                                       (x - 100, -K.PE_BOND - K.PE_ILD + 60, 14.0)], 2, 3, 0.62, 0.82, life=36, size=20.0)

    # floating body (beat 5) on the front-left cell
    fb = arr.cells[(0, 0)]
    for k, hg in enumerate(fb.holes):
        on(hg, span(5, 0.1 + 0.06 * k, 6, 0.0))
    on(fb.body, span(5, 0.35, 6, 0.0))
    on(arr.wl_on[0], span(5, 0.0, 5, 0.12))
    vt = K.vt_gauge(root, m, (-1560.0, 260.0, 160.0), w=470.0, h=420.0, name="vt")
    K.on(vt.g, beat(5))
    K.vt_shift(vt, [(F(5, 0.3), 0.0), (F(5, 0.8), -130.0)])

    # ---- stacked block ----
    sk = K.stacked_3d(root, m, (XS, 0.0, 0.0), n=8, nz=3, name="sk")
    K.lift_layers(sk, [(F(4, 0.08), 0.0), (F(4, 0.38), 1.0), (F(4, 0.8), 1.0), (F(4, 0.97), 0.0)], STEP)
    on(sk.wl_on[5], span(4, 0.4, 4, 0.8))
    on(sk.bl_on[0], span(4, 0.5, 4, 0.82) + span(6, 0.3, 6, 0.9))
    for k in range(8):
        for ch in sk.charges[k]:
            on(ch, span(4, 0.0, 5, 0.0) + beat(6))
    # beat 4's read: layer 5's right capacitor into the bit line (layers are apart, offset by 5*STEP)
    path = [(x, y + 5 * STEP, z) for x, y, z in K.stack_read_path(sk, (XS, 0.0, 0.0), 5, 1)[:3]]
    path.append((XS, 5 * STEP + 120.0, 12.0))
    K.beads(root, m, "sread", path, 4, 4, 0.45, 0.68, life=45)
    K.beads(root, m, "sread6", K.stack_read_path(sk, (XS, 0.0, 0.0), 3, -1), 2, 6, 0.3, 0.7, life=60)
    K.beads(root, m, "pread6", c1.read_path, 2, 6, 0.3, 0.7, life=60)

    # ---- tags ----
    pp = c1.pts
    lp = (XP + 900.0, 0.0, 0.0)
    tags = {
        0: [("transistor lies flat in the silicon", (XP - 900.0, -300.0, 0.0)), ("buried word line", pp["wl"]),
            ("tall capacitor holds the bit", (XP + 950.0, 1500.0, 0.0)), ("6F2 cell: 2F x 3F", pp["tile"])],
        2: [("silicon pillar: the channel", (XV - 600.0 + 75.0, LIFT + 520.0, 0.0)),
            ("word line wraps the pillar", (XV + 760.0, LIFT + 520.0, 0.0)),
            ("buried bit line", (XV + 800.0, LIFT + 175.0, 0.0)),
            ("4F2 cell: 2F x 2F", arr.cells[(2, 0)].pts["tile"])],
        4: [("capacitor lies sideways", (XS + 1100.0, 8 * STEP + 7 * K.S_LP + 230.0, 0.0)),
            ("vertical bit line", (XS, 8 * STEP + 8 * K.S_LP + 60.0, 0.0)),
            ("one word line per layer", (XS - 400.0, 3 * STEP + 3 * K.S_LP + 175.0, 0.0)),
            ("8 of 16 layers drawn", (XS - 1500.0, 2 * STEP + 2 * K.S_LP + 130.0, 0.0))],
        5: [("pillar body: no tie to the silicon", (-600.0 + 75.0, K.V_BASE + 640.0, 0.0)),
            ("threshold drops", (-1560.0 + 235.0, 720.0, 160.0))],
    }
    late = {
        1: [("narrower cap must grow taller", (XP + 1000.0, 2000.0, 0.0), 0.35),
            ("tall caps yield poorly", (XP - 1000.0, 2400.0, 0.0), 0.58)],
        3: [("cell wafer on top", (XV + 1000.0, 1400.0, 0.0), 0.0), ("periphery wafer underneath", (XV + 1200.0, -450.0, 0.0), 0.15),
            ("Cu-Cu hybrid bond", (XV - 1200.0, 0.0, 0.0), 0.55), ("sense amps, decoders", (XV - 300.0, -700.0, 0.0), 0.68)],
        5: [("holes pile up in the body", (-600.0 - 30.0, K.V_BASE + 300.0, 20.0), 0.25)],
        6: [("planar 6F2: today", (XP, 2700.0, 0.0), 0.05), ("Samsung 16 Gb VCT: ISSCC 2026", (XV, 2400.0, 0.0), 0.2),
            ("4F2 mass production: 2028 target", (XV, -1100.0, 0.0), 0.4), ("stacked 3D DRAM: early 2030s", (XS, 2500.0, 0.0), 0.6)],
    }
    _ = lp
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
    K.finish(NAME, page=PAGE)
