"""3D DRAM section 3, "From planar to stacked, in order" (heading 3 of RND_3D_DRAM.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_3.py

Writes blender/rnd_3d_dram_section_3.blend and assets/rnd_3d_dram_section_3.glb. The page's five
numbered steps happen IN ONE PLACE (the overview lays them side by side): each step replaces the last
on the same spot while the camera swings round it. Three 8 s beats:
  0 steps 1-2  two planar cells, then their capacitors squeeze narrower and stretch taller
  1 steps 3-4  the planar cells sink away and a 2 x 2 VCT array rises in their place; then a
               periphery block slides in underneath it from the side and the bond line glows
  2 step 5     the VCT die sinks and a stack of sideways cells builds up, layer by layer, round a
               vertical bit line
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, empty, label  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_3"
BEATS = 3
NS = 8

POSES = [
    ((0.0, 1150.0, -200.0), 7000.0, 0.65, 0.16),
    ((0.0, 520.0, -300.0), 6300.0, 0.05, 0.16),
    ((0.0, 1000.0, -300.0), 6400.0, -0.50, 0.18),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    # ---- beat 0: planar cells (steps 1, 2); they sink away at the start of beat 1 ----
    psw = K.hidden("planar_sw", root)
    on(psw, span(0, 0.0, 1, 0.14))
    pl = empty("planar_lift", psw)
    K.lift(pl, [(F(1, 0.0), 0.0), (F(1, 0.13), -3600.0)])
    pa = K.planar_array(pl, m, (0.0, 0.0, 0.0), nx=2, nz=1, name="pa", tile_at=None)
    for c in pa.cells.values():
        on(c.charge, span(0, 0.0, 1, 0.14))
    for cap in pa.caps:
        scale_keys(cap, [(F(0, 0.48), 1.0), (F(0, 0.78), (0.6, 0.6, 1.35))])
    c0 = pa.cells[(0, 0)]
    on(c0.wl_on, span(0, 0.1, 0, 0.4))
    on(c0.chan_on, span(0, 0.14, 0, 0.4))
    K.beads(root, m, "pread", c0.read_path, 2, 0, 0.15, 0.3, life=50)

    # ---- beat 1: VCT array rises (step 3), periphery slides under (step 4) ----
    vsw = K.hidden("vct_sw", root)
    on(vsw, span(1, 0.0, 2, 0.14))
    vl = empty("vct_lift", vsw)
    K.lift(vl, [(F(1, 0.0), -3200.0), (F(1, 0.08), -3200.0), (F(1, 0.28), 0.0), (F(2, 0.0), 0.0), (F(2, 0.13), -3600.0)])
    va = K.vct_array(vl, m, (0.0, K.V_BASE, 0.0), nx=2, nz=2, name="va", tile_at=(1, 0))
    for c in va.cells.values():
        on(c.charge, span(1, 0.25, 2, 0.14))
    on(va.cells[(1, 0)].tile, span(1, 0.3, 1, 0.5))
    on(va.wl_on[0], span(1, 0.3, 1, 0.48))

    esw = K.hidden("peri_sw", root)
    on(esw, span(1, 0.42, 2, 0.14))
    el = empty("peri_slide", esw)
    for f, (dx, dy) in ((F(1, 0.0), (-4200.0, 0.0)), (F(1, 0.45), (-4200.0, 0.0)), (F(1, 0.64), (0.0, 0.0)),
                        (F(2, 0.0), (0.0, 0.0)), (F(2, 0.13), (0.0, -3600.0))):
        K.key(el, f, "location", K.P(dx, dy, 0.0))
    x0, x1 = va.x0 - 200.0, va.x1 + 200.0
    pe = K.periphery(el, m, (0.0, 0.0, 0.0), x0, x1, va.zb, "pe",
                     pad_xs=[x + s * 100 for x in va.xs for s in (-1, 1)], pad_zs=list(va.zs))
    for p in pe.sa_on:
        on(p, span(1, 0.72, 2, 0.0))
    for p in pe.dec_on:
        on(p, span(1, 0.78, 2, 0.0))
    line = K.hidden("bondline", root)
    box("bondline_m", (x0 - 10, -7.0, va.zb - 10), (x1 + 10, 7.0, 6.0), m["bond"], line)
    on(line, span(1, 0.64, 2, 0.0))

    # ---- beat 2: stacked layers build up (step 5) ----
    ssw = K.hidden("stack_sw", root)
    on(ssw, span(2, 0.12, 3, 0.0))
    sk = K.stacked_3d(ssw, m, (0.0, 0.0, 0.0), n=NS, nz=3, name="sk")
    for k, lg in enumerate(sk.layers):
        u = 0.14 + 0.05 * k
        on(lg, span(2, u, 3, 0.0))
        for ch in sk.charges[k]:
            on(ch, span(2, u + 0.04, 3, 0.0))
    on(sk.layers_top, span(2, 0.14 + 0.05 * NS, 3, 0.0))
    on(sk.bl_on[0], span(2, 0.62, 2, 0.96))
    on(sk.wl_on[6], span(2, 0.6, 2, 0.9))
    K.beads(root, m, "sread", K.stack_read_path(sk, (0.0, 0.0, 0.0), 6, 1), 3, 2, 0.62, 0.8, life=45)

    # ---- numbered tags ----
    pp = c0.pts
    label("1  today: flat transistor, tall capacitor, 6F2", (pp["drain"][0], pp["drain"][1], 0.0), root, span(0, 0.05, 0, 0.5))
    label("2  narrower capacitor must grow taller", (pa.cells[(1, 0)].pts["cap_top"][0] + 80.0, 2200.0, 0.0), root, span(0, 0.55, 1, 0.0))
    label("3  transistor stands up as a pillar: 4F2", (va.xs[1] + K.V_PW, K.V_BASE + 400.0, 0.0), root, span(1, 0.28, 2, 0.0))
    label("4  periphery on its own wafer, bonded under", (x1, -K.PE_BOND - K.PE_ILD - 80.0, 0.0), root, span(1, 0.64, 2, 0.0))
    label("5  cells on their sides, stacked in layers", (-K.S_W, 5 * K.S_LP + 130.0, 0.0), root, span(2, 0.4, 3, 0.0))
    label("shared vertical bit line", (60.0, NS * K.S_LP - 80.0, 0.0), root, span(2, 0.6, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
