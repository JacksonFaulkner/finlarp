"""The eight WAFER numbered sections and the sources picture, authored in Blender and exported for
pbr3d in the SAND template (docs/diagram-pages.md). Pieces come from wafer_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/wafer_sections.py [-- 3 5]

For each section it writes blender/wafer_sec<N>.blend and assets/wafer_sec<N>.glb.

  1 what it is       a wafer through the stations: polish, epi or SOI, inspect, pack (four beats)
  2 cross sections   bulk, epi, SOI, one at a time (three beats; drawn thicker than life)
  3 specs            thickness, TTV, the site grid, the area of one face (four beats)
  4 by the numbers   shipments, revenue, area against revenue, the 300 mm share (four beats)
  5 market share     six suppliers, the top two first, the top five, the 2025-ish source (four)
  6 structure        five makers and tickers, SK Siltron in SK Inc, the Japan share of 300 mm
                     epi, the planned GlobalWafers and Siltronic deal (four beats)
  7 chokepoints      a quake, a long qualification, two speeds, price per area (four beats)
  8 connects         upstream into the wafer, then downstream (three beats)
  9 sources          nine source cards, three per beat (three beats)

One beat is SEC (8) seconds at 24 fps.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, beat, box, disc, empty, key, label, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import wafer_kit as K  # noqa: E402
from wafer_kit import END, R, THICK  # noqa: E402


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="wafer")
    K.mats(m)
    return m, root


def group(parent, name):
    return empty(name, parent)


# ---- 1. what it is: the stations ---------------------------------------------------------


def sec1():
    m, root = begin(1, 4)
    K.plinth(root, m, -650, 650, -200, 200, y=0.0)
    xs = [-450.0, -150.0, 150.0, 450.0]
    for k, x in enumerate(xs):
        K.station(root, m, x, f"station{k}", w=160.0, h=110.0)

    holder = K.wafer(root, m, "wafer", y0=110.0)
    key(holder, F(0, 0), "location", P(xs[0], 0, 0))
    key(holder, F(1, 0.1), "location", P(xs[0], 0, 0))
    key(holder, F(1, 0.6), "location", P(xs[1], 0, 0), linear=True)
    key(holder, F(2, 0.1), "location", P(xs[1], 0, 0))
    key(holder, F(2, 0.6), "location", P(xs[2], 0, 0), linear=True)
    key(holder, F(3, 0.1), "location", P(xs[2], 0, 0))
    key(holder, F(3, 0.6), "location", P(xs[3], 0, 0), linear=True)

    # beat 1: an epi layer appears on the top face (a switch on the holder)
    epi = group(holder, "epi")
    show(epi, [(F(1, 0), END)])
    disc("epi_disc", (0, 110.0 + THICK + 0.75, 0), R - 1, 1.5, m["epi"], epi, verts=128)

    # beat 2: inspection, a scan bar across the disc at the station
    scan = group(root, "scan")
    bar = box("scan_bar", (-2, 0, -R - 5), (2, 4, R + 5), m["scan"], scan)
    key(bar, F(2, 0), "location", P(xs[2] - R - 20, 130, 0), linear=True)
    key(bar, F(2, 0.95), "location", P(xs[2] + R + 20, 130, 0), linear=True)
    show(scan, beat(2))

    # beat 3: the FOUP at the last station
    pos = empty("pack_pos", root, P(0, 110, 0))
    foup = K.foup(pos, m, xs[3])
    show(foup, beat(3))

    label("polish: mirror top face", (xs[0], 190, 60), root, beat(0))
    label("epi or SOI: optional layer", (xs[1], 190, 60), root, beat(1))
    label("inspect: TTV, SFQR, particles", (xs[2], 190, 60), root, beat(2))
    label("pack in a FOUP, then the fab", (xs[3], 330, 60), root, beat(3))

    camera(root, [
        ((xs[0], 130.0, 0.0), 1000.0, 0.25, 0.12),
        ((xs[1], 130.0, 0.0), 1000.0, 0.25, 0.12),
        ((xs[2], 130.0, 0.0), 1000.0, 0.25, 0.12),
        ((xs[3] - 40, 190.0, 0.0), 1300.0, 0.25, 0.12),
    ])
    finish("sec1", page="wafer")


# ---- 2. cross sections ---------------------------------------------------------------------


def sec2():
    m, root = begin(2, 3)
    bulk = K.slab(root, m, "bulk_only", [("bulk", 60.0, "bulk_part")])
    show(bulk, beat(0))
    be = K.slab(root, m, "bulk_epi", [("bulk", 60.0, "bulk_part"), ("epi", 12.0, "epi_part")])
    show(be, beat(1))
    soi = K.slab(root, m, "soi", [("handle", 50.0, "handle_part"), ("box", 3.0, "box_part"), ("device", 8.0, "device_part")])
    show(soi, beat(2))

    label("bulk: one single crystal", (-110, 74, 10), root, beat(0))
    label("epi: CVD layer on bulk", (-110, 74, 10), root, beat(1))
    label("SOI: device layer, buried oxide", (-110, 90, 10), root, beat(2))

    pose = ((0.0, 40.0, 0.0), 520.0, 0.25, 0.12)
    camera(root, [pose, pose, pose])
    finish("sec2", page="wafer")


# ---- 3. specs and flatness ----------------------------------------------------------------


def sec3():
    m, root = begin(3, 4)
    thick = group(root, "thickness")
    box("piece", (-120, 0, -60), (120, 30, 0), m["bulk"], thick)
    K.dim_marks(thick, m, 150.0, 0.0, 30.0)
    show(thick, beat(0))
    label("775 +/- 25 um, vendor sheet", (0, 40, 20), root, beat(0))

    tilt = pivot("ttv", (0, 0, 0), root)
    t = box("tilted_piece", (-120, 0, -60), (120, 30, 0), m["bulk"], tilt)
    t.rotation_euler = (0, 0.105, 0)
    show(tilt, beat(1))
    label("TTV 5 um or less (vendor)", (-110, 60, 20), root, beat(1))

    top = group(root, "topview")
    K.wafer(top, m, "disc")
    show(top, [(F(2, 0), END)])
    K.grid(top, m, "sites", K.site_cells(), "site", THICK + 1.5, [(F(2, 0), END)])
    label("SFQR: flatness in one site", (-60, 26, 60), root, [(F(2, 0.1), F(3, 0))])

    ring = group(top, "area_ring")
    disc("area_outer", (0, THICK + 2.0, 0), R, 0.8, m["gold"], ring, verts=128)
    disc("area_inner", (0, THICK + 2.5, 0), R - 2.0, 1.0, m["si"], ring, verts=128)
    show(ring, [(F(3, 0), END)])
    label("area 70,686 mm2 per face", (R - 2, 14, 0), root, [(F(3, 0.1), END)])
    label("about 109.6 sq in", (-60, 26, -90), root, [(F(3, 0.1), END)])

    camera(root, [
        ((0.0, 15.0, 0.0), 480.0, 0.20, 0.10),
        ((0.0, 15.0, 0.0), 500.0, 0.30, 0.15),
        ((0.0, 4.0, -20.0), 760.0, 0.20, 1.00),
        ((0.0, 4.0, -20.0), 760.0, 0.20, 1.00),
    ])
    finish("sec3", page="wafer")


# ---- 4. by the numbers ---------------------------------------------------------------------


def sec4():
    m, root = begin(4, 4)
    K.plinth(root, m, -420, 420, -200, 200)
    s = group(root, "shipments")
    K.grow_bar(s, "ship24", -150, 0, 150, 12262 / 100.0, m["grey"], F(0, 0.05), F(0, 0.5))
    K.grow_bar(s, "ship25", 150, 0, 150, 12973 / 100.0, m["gold"], F(0, 0.1), F(0, 0.55))
    show(s, beat(0))
    label("2025: 12,973 MSI, up 5.8%", (150, 150, 0), root, beat(0))
    label("2024: about 12,262 (derived)", (-150, 150, 0), root, beat(0))

    r = group(root, "revenue")
    K.grow_bar(r, "rev24", -150, 0, 150, 115.0, m["grey"], F(1, 0.05), F(1, 0.5))
    K.grow_bar(r, "rev25", 150, 0, 150, 114.0, m["gold"], F(1, 0.1), F(1, 0.55))
    show(r, beat(1))
    label("2025: $11.4 billion, down 1.2%", (150, 150, 0), root, beat(1))
    label("2024: about $11.5B (derived)", (-150, 150, 0), root, beat(1))

    a = group(root, "area_vs_rev")
    K.grow_bar(a, "area_up", -150, 0, 150, 58.0, m["blue"], F(2, 0.05), F(2, 0.5))
    box("rev_down", (100, -12, -75), (200, 0, 75), m["red"], a)
    show(a, beat(2))
    label("area +5.8%", (-150, 80, 0), root, beat(2))
    label("revenue -1.2%", (150, -30, 0), root, beat(2))
    label("price per area is falling", (0, 150, 0), root, beat(2))

    h = group(root, "share300")
    K.grow_bar(h, "share", 0, 0, 200, 67.0, m["gold"], F(3, 0.05), F(3, 0.5))
    show(h, beat(3))
    label("300 mm: 67% of polished (blog, low confidence)", (120, 80, 0), root, beat(3))
    label("AI: advanced epi for sub-3nm logic", (0, 160, 0), root, beat(3))

    camera(root, [
        ((0.0, 60.0, 0.0), 1180.0, 0.25, 0.12),
        ((0.0, 60.0, 0.0), 1180.0, 0.25, 0.12),
        ((0.0, 60.0, 0.0), 1180.0, 0.25, 0.12),
        ((0.0, 80.0, 0.0), 1180.0, 0.25, 0.12),
    ])
    finish("sec4", page="wafer")


# ---- 5. market share ----------------------------------------------------------------------


def sec5():
    m, root = begin(5, 4)
    K.plinth(root, m, -600, 600, -200, 200)
    names = [
        ("Shin-Etsu 29.4%", 29.4, m["gold"]),
        ("SUMCO 21.9%", 21.9, m["gold"]),
        ("GlobalWafers 15.2%", 15.2, m["blue"]),
        ("Siltronic 11.5%", 11.5, m["blue"]),
        ("SK Siltron 11.4%", 11.4, m["blue"]),
        ("Soitec 5.5%", 5.5, m["grey"]),
    ]
    xs = [-450.0 + 180.0 * k for k in range(6)]
    f_on = [(0, 0.05), (0, 0.2), (1, 0.05), (1, 0.2), (1, 0.35), (2, 0.05)]
    for k, ((text, v, mm), x, (b, u)) in enumerate(zip(names, xs, f_on)):
        grow = K.grow_bar(root, f"share{k}", x, 0, 110, v * 8.0, mm, F(b, u), F(b, u + 0.4))
        label(text, (x, v * 8.0 + 20, 0), root, [(F(b, u + 0.2), END)])

    ghost = group(root, "ghost25")
    # behind the real bars (z < -60), so the 2025 outlines do not cover the 2024 bars in front
    box("ghost_sh", (xs[0] - 60, 0, -220), (xs[0] + 60, 28 * 8.0, -140), m["ghost"], ghost)
    box("ghost_su", (xs[1] - 60, 0, -220), (xs[1] + 60, 25 * 8.0, -140), m["ghost"], ghost)
    show(ghost, beat(3))
    label("2025-ish source: Shin-Etsu 28%", (xs[0], 28 * 8.0 + 60, 0), root, beat(3))

    br = group(root, "top5")
    box("bracket", (xs[0] - 60, 255, -10), (xs[4] + 60, 265, 10), m["red"], br)
    show(br, beat(2))
    label("top five: 85% (blog, low confidence)", (-60, 300, 0), root, beat(2))
    label("top five above 90% (GEP 2018)", (-60, 340, 0), root, beat(2))

    camera(root, [
        ((-270.0, 140.0, 0.0), 1100.0, 0.10, 0.10),
        ((-90.0, 150.0, 0.0), 1600.0, 0.10, 0.10),
        ((0.0, 180.0, 0.0), 1700.0, 0.10, 0.10),
        ((0.0, 160.0, 0.0), 1700.0, 0.10, 0.10),
    ])
    finish("sec5", page="wafer")


# ---- 6. market structure and tickers ----------------------------------------------------


def sec6():
    m, root = begin(6, 4)
    tiles = group(root, "makers")
    cards = [
        ("Shin-Etsu Chemical 4063.T", -900, 600),
        ("SUMCO 3436.T", 0, 600),
        ("GlobalWafers 6488.TWO", 900, 600),
        ("Siltronic WAF.DE", -450, -200),
        ("SK Siltron 034730.KS", 450, -200),
    ]
    for k, (text, x, y) in enumerate(cards):
        K.tile(tiles, f"maker{k}", x, y, 800, 300, text, F(0, 0.05 + 0.08 * k), m)
    show(tiles, beat(0))

    sk = group(root, "sk")
    K.tile(sk, "sk_inc", 0, 0, 1600, 600, "SK Inc 034730.KS", F(1, 0.05), m)
    sub = group(sk, "siltron_in_sk")
    box("siltron_b", (-400, -180, -60), (400, 80, 20), m["blue"], sub)
    key(sub, F(1, 0.3), "location", P(1000, 0, 0))
    key(sub, F(1, 0.6), "location", P(0, 0, 0))
    show(sub, [(F(1, 0.3), END)])
    label("SK Siltron: held by SK Inc", (0, 0, 40), sub, [(F(1, 0.6), END)])
    show(sk, beat(1))

    jp = group(root, "japan_epi")
    box("jp_two", (-300, 0, -60), (-60, 240, 60), m["gold"], jp)
    box("others", (60, 0, -60), (300, 160, 60), m["blue"], jp)
    show(jp, beat(2))
    label("two Japanese firms: over 60%", (-180, 260, 0), root, beat(2))
    label("300 mm epi, 2H 2020 (SEMI)", (180, 200, 0), root, beat(2))

    dl = group(root, "deal")
    box("gw", (-150, 0, -60), (150, 61, 60), m["blue"], dl)
    box("siltronic", (-150, 61, -60), (150, 107, 60), m["gold"], dl)
    show(dl, beat(3))
    label("GlobalWafers + Siltronic: 26.7%", (180, 120, 0), root, beat(3))
    label("the deal did not complete (textbook)", (0, 180, 0), root, beat(3))

    camera(root, [
        ((0.0, 350.0, 0.0), 5600.0, 0.05, 0.05),  # wide: the outer maker cards sit at x +-900
        ((0.0, 300.0, 0.0), 4600.0, 0.05, 0.10),
        ((0.0, 120.0, 0.0), 2200.0, 0.10, 0.10),
        ((0.0, 120.0, 0.0), 2200.0, 0.10, 0.10),
    ])
    finish("sec6", page="wafer")


# ---- 7. chokepoints and risks ------------------------------------------------------------


def sec7():
    m, root = begin(7, 4)
    discs = group(root, "makers_at_risk")
    for k in range(5):
        h = K.wafer(discs, m, f"maker_disc{k}", y0=0.0, notch=False)
        h.location = P(-480 + 240 * k, 0, 0)
    quake = group(root, "quake")
    box("quake_block", (-700, 0, -560), (700, 200, -200), m["quake"], quake)  # behind: it used to bury the wafers
    show(quake, [(F(0, 0.4), F(1, 0))])
    label("a Japan outage hits all five", (-300, 230, 0), root, [(F(0, 0.45), F(1, 0))])

    track = group(root, "qualification")
    K.grow_hbar(track, "months", -1200, 0, 0, 2400, 60, m["grey"], F(1, 0.05), F(1, 0.5))
    dk = K.wafer(track, m, "wafer_end", y0=40.0, notch=False)
    key(dk, F(1, 0.5), "location", P(1200, 0, 0))
    show(track, beat(1))
    label("switching supplier: many months", (0, 200, 0), root, beat(1))
    label("each fab qualifies per process", (0, 260, 0), root, beat(1))

    two = group(root, "two_speeds")
    K.grow_bar(two, "ai", -200, 0, 150, 200.0, m["gold"], F(2, 0.05), F(2, 0.5))
    K.grow_bar(two, "mature", 200, 0, 150, 80.0, m["grey"], F(2, 0.1), F(2, 0.55))
    show(two, beat(2))
    label("AI epi and HBM: strong", (-200, 230, 0), root, beat(2))
    label("mature nodes: soft (SEMI)", (200, 110, 0), root, beat(2))

    pr = group(root, "price_per_area")
    K.grow_bar(pr, "area", -150, 0, 150, 290.0, m["gold"], F(3, 0.05), F(3, 0.5))
    K.grow_bar(pr, "rev", 150, 0, 150, 60.0, m["red"], F(3, 0.1), F(3, 0.55))
    show(pr, beat(3))
    label("2025 area +5.8%", (-150, 310, 0), root, beat(3))
    label("revenue -1.2%", (150, 80, 0), root, beat(3))
    label("China building 300 mm capacity", (0, 380, 0), root, beat(3))

    camera(root, [
        ((0.0, 120.0, 0.0), 2300.0, 0.20, 0.15),
        ((1200.0, 60.0, 0.0), 1700.0, 0.05, 0.10),
        ((0.0, 150.0, 0.0), 1000.0, 0.20, 0.12),
        ((0.0, 190.0, 0.0), 1100.0, 0.20, 0.12),
    ])
    finish("sec7", page="wafer")


# ---- 8. how it connects -----------------------------------------------------------------


def sec8():
    m, root = begin(8, 3)
    up = group(root, "upstream")
    box("up_slice", (-1000, 0, 200), (-700, 200, 500), m["tool"], up)
    box("up_poly", (-1000, 0, -500), (-700, 200, -200), m["tool"], up)
    show(up, beat(0))
    label("SLICE + POLISH: the surface", (-850, 230, 350), root, beat(0))
    label("POLY + MELT + PULL: the crystal", (-850, 230, -350), root, beat(0))

    K.wafer(root, m, "wafer", y0=0.0)
    label("flat top face: the reference", (0, 60, 150), root, [(F(1, 0.1), F(3, 0))])
    label("SFQR is a litho number too", (0, 90, -150), root, [(F(1, 0.2), F(3, 0))])

    dn = group(root, "downstream")
    box("dn_dep", (700, 0, 200), (1000, 200, 500), m["tool"], dn)
    box("dn_litho", (700, 0, -500), (1000, 200, -200), m["tool"], dn)
    show(dn, beat(2))
    label("DEPOSIT, LITHO, ETCH start here", (850, 230, 0), root, beat(2))

    camera(root, [
        ((-450.0, 100.0, 0.0), 2300.0, 0.35, 0.25),  # upstream tools
        ((0.0, 50.0, 0.0), 800.0, 0.35, 0.28),  # the reference wafer fills the frame
        ((350.0, 80.0, 0.0), 2000.0, 0.35, 0.25),  # wafer and the downstream tools
    ])
    finish("sec8", page="wafer")


# ---- 9. sources --------------------------------------------------------------------------


CARDS = {
    1: "[1] SEMI 2025 shipments, revenue",
    2: "[2] vendor 300 mm datasheets",
    3: "[3] SEMI M1 and M43",
    4: "[4] SFQR patent, US 12635427",
    5: "[5] shares 2021, Semiconductor Eng.",
    6: "[6] top-5 concentration, GEP 2018",
    7: "[7] SOI implant, US 8497187",
    8: "[8] 300 mm blog, low confidence",
    9: "[9] China wafer landscape report",
}


def sec9():
    m, root = begin(9, 3)
    g = group(root, "sources")
    K.plinth(g, m, -4200, 4200, -1600, 1600)
    for n in range(1, 10):
        b = (n - 1) // 3
        x = -2400.0 + 2400.0 * ((n - 1) % 3)  # wide columns: the long source tags run about 2000 mm
        z = -1000.0 + 1000.0 * b
        box(f"card{n}", (x - 600, 0, z - 400), (x + 600, 30, z + 400), m["paper"], g)
        lit = group(g, f"lit{n}")
        box(f"lit{n}_m", (x - 500, 30, z - 300), (x + 500, 34, z - 270), m["gold_glow"], lit)
        show(lit, [(F(b, 0.15 + 0.2 * ((n - 1) % 3)), END)])
        label(CARDS[n], (x - 600, 40, z + 400), g, [(F(b, 0.15 + 0.2 * ((n - 1) % 3)), END)])
    camera(root, [
        ((0.0, 0.0, 0.0), 14000.0, 0.03, 0.85),
        ((0.0, 0.0, 0.0), 14000.0, 0.02, 0.85),
        ((0.0, 0.0, 0.0), 14000.0, -0.02, 0.85),
    ])
    finish("sec9", page="wafer")


SECTIONS = {n: globals()[f"sec{n}"] for n in range(1, 10)}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [str(n) for n in range(1, 10)]
    for n in which:
        SECTIONS[int(n)]()
