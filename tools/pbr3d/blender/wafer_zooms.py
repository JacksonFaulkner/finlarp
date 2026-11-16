"""The four WAFER zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the wafer pieces in wafer_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/wafer_zooms.py [-- sites epi soi spec]

For each zoom it writes blender/wafer_zoom_<name>.blend and assets/wafer_zoom_<name>.glb.

  a sites  the wafer cut into scanner-field sites; a scan bar reads them; edge sites; one site
           that passes on paper but can fail the focus budget on the chuck
  b epi    bulk substrate, a gas stream of trichlorosilane, an epi layer grown by CVD, devices
           sitting in the layer
  c soi    SOI by Smart Cut: hydrogen implant, bond to a handle wafer, anneal split, the device
           layer on the buried oxide
  d spec   the spec sheet: thickness, TTV, edge exclusion, and the site grid (SFQR)

Cross-sections are drawn thicker than life (the text says so). One beat is SEC (8) seconds at
24 fps; every zoom is four beats.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, beat, box, disc, empty, key, label, pivot, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
from poly_overview import run  # noqa: E402
import wafer_kit as K  # noqa: E402
from wafer_kit import END, R, THICK  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="wafer")
    K.mats(m)
    return m, root


# ---- a: flatness sites ------------------------------------------------------------------


def sites():
    m, root = begin("sites")
    K.wafer(root, m, "wafer")
    cells = K.site_cells()
    bad_keys = {(5, 0), (-4, -3)}  # two edge sites that fail
    bump = (2, -1)  # an interior site that passes on paper and lifts on the chuck
    edge = {(i, j) for i, j, _, _, e in cells if e}

    def is_bad(i, j, *_):
        return (i, j) in bad_keys

    K.grid(root, m, "grey", cells, "site", THICK, [(0, F(1, 0.5))])
    K.grid(root, m, "green", cells, "ok", THICK, [(F(1, 0.5), END)],
           keep=lambda i, j, cx, cz, e: not e and not is_bad(i, j))
    K.grid(root, m, "gold", cells, "edge", THICK, [(F(1, 0.5), END)],
           keep=lambda i, j, cx, cz, e: e and not is_bad(i, j))
    K.grid(root, m, "red", cells, "bad", THICK, [(F(2, 0), END)], keep=lambda i, j, cx, cz, e: is_bad(i, j))

    # beat 1: the scan bar sweeps across the disc at the height of the sites
    scan = empty("scan", root)
    bar = box("scan_bar", (-2, THICK + 3, -R - 5), (2, THICK + 7, R + 5), m["scan"], scan)
    key(bar, F(1, 0), "location", P(-R - 20, THICK + 5, 0), linear=True)
    key(bar, F(1, 0.95), "location", P(R + 20, THICK + 5, 0), linear=True)
    show(scan, [(F(1, 0), F(2, 0))])
    label("scan bar reads each site", (60, 28, -60), root, [(F(1, 0.1), F(2, 0))])

    # beat 3: a site lifts on the chuck
    cx, cz = next((c[2], c[3]) for c in cells if (c[0], c[1]) == bump)
    lift = empty("chuck_lift", root)
    box("lift", (cx - 8, THICK, cz - 8), (cx + 8, THICK + 10, cz + 8), m["red"], lift)
    show(lift, [(F(3, 0), END)])

    label("scanner-field sites", (-110, 28, 60), root, beat(0))
    label("in-spec sites turn green", (-60, 28, 110), root, [(F(1, 0.5), F(2, 0))])
    label("edge sites: ESFQR", (120, 28, -110), root, [(F(2, 0), F(3, 0))])
    label("edge exclusion 3.0 mm", (-120, 28, -40), root, [(F(2, 0), F(3, 0))])
    label("chuck: focus budget can fail", (cx, THICK + 30, cz), root, [(F(3, 0.1), END)])

    camera(root, [
        ((0.0, 6.0, 0.0), 680.0, 0.30, 0.95),
        ((0.0, 6.0, 0.0), 680.0, 0.30, 0.95),
        ((0.0, 6.0, -20.0), 640.0, 0.30, 0.95),
        ((cx, THICK, cz), 300.0, 0.30, 0.60),
    ])
    finish("zoom_sites", page="wafer")


# ---- b: the epi layer -------------------------------------------------------------------


def epi():
    m, root = begin("epi")
    K.slab(root, m, "bulk", [("bulk", 60.0, "bulk_si")])
    layer = pivot("epi_layer", (0, 60, 0), root)
    box("epi_part", (-120, 0, -60), (120, 12, 0), m["epi"], layer)
    scale_keys(layer, [(0, (1, 1, OFF)), (F(2, 0.0), (1, 1, OFF)), (F(2, 0.7), (1, 1, 1)), (END, (1, 1, 1))], until=F(2, 0.0))

    # beat 1: trichlorosilane gas streams along the top face
    run(root, "gas", 6, [(-220, 150, -20), (-120, 80, -20), (0, 76, -20), (150, 76, -20)], 8, m["gas"], 1, 0.05, 0.6, 60)
    label("trichlorosilane gas, 1100-1130 C", (0, 150, 20), root, [(F(1, 0.1), F(2, 0))])
    label("bulk Si: polished base", (-110, 30, 10), root, beat(0))
    label("epi 3-6 um typical (patents)", (-110, 70, 10), root, [(F(2, 0.2), F(3, 0))])
    label("epi drawn 10x thicker than life", (110, 130, 10), root, [(F(2, 0.2), F(3, 0))])
    label("devices sit in the epi layer", (0, 96, 10), root, [(F(3, 0.1), END)])
    label("tuned doping, fewer defects", (110, 40, 10), root, [(F(3, 0.1), END)])

    camera(root, [
        ((0.0, 40.0, -20.0), 520.0, 0.25, 0.12),
        ((0.0, 55.0, -20.0), 540.0, 0.25, 0.12),
        ((0.0, 60.0, -20.0), 540.0, 0.25, 0.12),
        ((0.0, 66.0, -20.0), 540.0, 0.25, 0.12),
    ])
    finish("zoom_epi", page="wafer")


# ---- c: SOI by Smart Cut ----------------------------------------------------------------


def soi():
    m, root = begin("soi")
    handle = K.slab(root, m, "handle", [("handle", 50.0, "handle_si")])
    show(handle, [(F(1, 0), END)])
    buried = K.slab(root, m, "box", [("box", 3.0, "buried_oxide")], y0=50.0)
    show(buried, [(F(1, 0), END)])

    # the donor: a film (bottom 4 mm, the transferred layer) and the rest of the wafer above it
    donor = pivot("donor", (0, 110, 0), root)
    film = box("film", (-120, 0, -60), (120, 4, 0), m["device"], donor)
    top = pivot("donor_top", (0, 0, 0), donor)
    box("donor_bulk", (-120, 4, -60), (120, 60, 0), m["bulk"], top)
    weak = K.pbox("weak_plane", (-120, 3.4, -60.4), (120, 4.6, 0.8), m["weak"], donor)  # pivot: show() on a box shrinks it
    show(weak, [(0, F(2, 0.3))])

    # beat 0: hydrogen ions go in through the bonding face and stop at the weak layer
    run(root, "ion", 6, [(-120, 30, -10), (-30, 100, -10), (0, 114, -10)], 5, m["ion"], 0, 0.1, 0.8, 50)
    label("H+ implant, about 2 um at 200 keV", (-110, 150, 20), root, beat(0))

    # beat 1: the donor comes down onto the oxide-covered handle
    key(donor, F(1, 0.05), "location", P(0, 110, 0))
    key(donor, F(1, 0.75), "location", P(0, 53, 0), linear=True)
    key(donor, F(2, 0.0), "location", P(0, 53, 0))
    label("bond to a handle wafer", (60, 40, 20), root, [(F(1, 0.2), F(2, 0))])  # left of centre: the tag ran off the right edge

    # beat 2: the anneal splits the donor along the weak layer; the upper part lifts away
    key(top, F(2, 0.05), "location", P(0, 0, 0))
    key(top, F(2, 0.7), "location", P(0, 90, 0), linear=True)
    show(top, [(0, F(2, 0.8))])
    label("anneal splits along the weak layer", (-110, 100, 20), root, [(F(2, 0.1), F(3, 0))])

    # beat 3: the film is left on the oxide
    label("device layer on buried oxide", (-110, 56, 20), root, [(F(3, 0.1), END)])
    label("handle wafer", (110, 25, 20), root, [(F(3, 0.1), END)])

    camera(root, [
        ((0.0, 100.0, 0.0), 560.0, 0.25, 0.12),
        ((0.0, 90.0, 0.0), 520.0, 0.25, 0.12),
        ((0.0, 80.0, 0.0), 500.0, 0.25, 0.12),
        ((0.0, 60.0, 0.0), 480.0, 0.25, 0.12),
    ])
    finish("zoom_soi", page="wafer")


# ---- d: the spec sheet ------------------------------------------------------------------


def spec():
    m, root = begin("spec")
    # beats 0-1: a cut-away piece for thickness and for TTV (a tilted top face)
    thick = empty("thickness", root)
    box("piece", (-120, 0, -60), (120, 30, 0), m["bulk"], thick)
    K.dim_marks(thick, m, 150.0, 0.0, 30.0)
    show(thick, [(0, F(1, 0))])
    label("775 +/- 25 um (not to scale)", (0, 40, 20), root, [(F(0, 0.1), F(1, 0))])

    tilt = pivot("ttv", (0, 0, 0), root)
    slab_t = box("tilted_piece", (-120, 0, -60), (120, 30, 0), m["bulk"], tilt)
    slab_t.rotation_euler = (0, 0.105, 0)  # about 6 degrees, exaggerated
    show(tilt, [(F(1, 0), F(2, 0))])
    label("TTV: max minus min, 5 um or less", (-110, 60, 20), root, [(F(1, 0.1), F(2, 0))])

    # beats 2-3: the wafer from above; an edge ring for exclusion, then the site grid
    top = empty("topview", root)
    K.wafer(top, m, "disc")
    disc("edge_ring", (0, THICK + 0.35, 0), R, 0.6, m["gold"], top, verts=128)
    disc("edge_inner", (0, THICK + 0.9, 0), R - 3.0, 1.5, m["si"], top, verts=128)
    show(top, [(F(2, 0), END)])
    label("edge exclusion 3.0 mm", (R - 2, 10, 0), root, [(F(2, 0.1), F(3, 0))])

    sites_g = K.grid(top, m, "sites", K.site_cells(), "site", THICK + 1.5, [(F(3, 0), END)])
    label("SFQR: one scanner site", (-60, 26, 60), root, [(F(3, 0.1), END)])
    label("nanotopography: SEMI M43", (60, 26, -60), root, [(F(3, 0.1), END)])

    camera(root, [
        ((0.0, 15.0, 0.0), 480.0, 0.20, 0.10),
        ((0.0, 15.0, 0.0), 500.0, 0.30, 0.15),
        ((0.0, 4.0, -20.0), 660.0, 0.20, 1.00),
        ((0.0, 4.0, -20.0), 660.0, 0.20, 1.00),
    ])
    finish("zoom_spec", page="wafer")


ZOOMS = {"sites": sites, "epi": epi, "soi": soi, "spec": spec}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ZOOMS)
    for name in which:
        ZOOMS[name]()
