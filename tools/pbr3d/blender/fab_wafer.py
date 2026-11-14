"""The WAFER page, as 3D pictures from Blender through pbr3d: four zoom-ins and nine sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fab_wafer.py

Writes assets/wafer_<name>.glb and blender/wafer_<name>.blend for each scene. The overview is
wafer_overview.glb (wafer_overview.py), unchanged.

  zooms  a sites   flatness sites across the disc, a scanner bar reads them
         b epi     an epi layer grown by CVD from gas
         c soi     SOI: implant, bond, split
         d spec    the spec sheet: thickness, TTV, edge exclusion
  sections 1 what it is   the flow: polished, optional epi or SOI, inspect, pack, fab
           2 cross sections   bulk, epi, SOI, one at a time
           3 specs and flatness   thickness, TTV and the site grid
           4 by the numbers   shipments, revenue, the 300 mm share
           5 market share     six suppliers, the top two first
           6 market structure five makers, a merger that did not complete
           7 chokepoints      a quake, a long qualification, two speeds
           8 how it connects  upstream into the wafer, then downstream
           9 sources          nine source cards, three per beat
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbr_kit import *  # noqa: F401,F403  (the shared helpers, see pbr_kit.py)

BF = BEAT_FRAMES
THICK = 6.0  # the disc is drawn 6 mm thick, about 8x exaggerated, as in wafer_overview.py
R = 150.0  # 300 mm


def wafer_mats():
    return dict(
        si=mat("silicon_mirror", (0.50, 0.53, 0.58), metal=0.9, rough=0.16),
        epi=mat("epi_layer", (0.62, 0.58, 0.52), metal=0.3, rough=0.4),
        oxide=mat("oxide_band", (0.90, 0.70, 0.30), rough=0.3, emit=(0.9, 0.6, 0.2), strength=0.4),
        handle=mat("handle_si", (0.42, 0.44, 0.48), metal=0.8, rough=0.3),
        steel=mat("steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4),
        ion=mat("ion", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=3.0),
        cut=mat("cut_plane", (1.0, 0.8, 0.3), emit=(1.0, 0.8, 0.3), strength=4.0),
        bar=mat("bar_fill", (0.55, 0.58, 0.64), metal=0.5, rough=0.35),
        hi=mat("bar_high", (0.85, 0.45, 0.25), emit=(0.85, 0.45, 0.25), strength=0.4),
        scan=mat("scan_bar", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=2.0),
        lit=mat("site_lit", (0.45, 0.95, 0.8), emit=(0.45, 0.95, 0.8), strength=1.6),
        bad=mat("site_bad", (1.0, 0.25, 0.2), emit=(1.0, 0.25, 0.2), strength=2.5),
        card=mat("card", (0.92, 0.92, 0.90), rough=0.8),
        frame=mat("frame", (0.5, 0.5, 0.55), alpha=0.1, rough=0.2),
        gas=mat("gas", (0.90, 0.90, 0.95), emit=(0.9, 0.9, 0.95), strength=0.8, alpha=0.5),
        lump=mat("lump", (0.30, 0.30, 0.32), rough=0.9),
        quake=mat("quake_block", (0.75, 0.35, 0.2), rough=0.6),
        dash=mat("broken_link", (0.9, 0.5, 0.2), emit=(0.9, 0.5, 0.2), strength=1.5),
        clay=mat("clay", (0.42, 0.32, 0.22), rough=0.9),
        dot=mat("marker", (1.0, 0.9, 0.6), emit=(1.0, 0.9, 0.6), strength=3.0),
    )


def boxg(name, lo, hi, m, parent=None):
    """A box inside its own empty: the empty can be keyed or shown without losing the box's size."""
    g = empty(name, parent)
    box(f"{name}_box", lo, hi, m, g)
    return g


def bulk_wafer(root, m, centre=(0, 3, 0), name="wafer"):
    return disc(name, centre, R, THICK, m["si"], root)


# ---- zoom a: flatness sites ------------------------------------------------------------


def zoom_sites():
    root = start("zoom_sites", 4)
    m = wafer_mats()
    bulk_wafer(root, m)
    sites = []
    pitch = 44.0
    for i in range(-4, 4):
        for j in range(-4, 4):
            x, z = (i + 0.5) * pitch, (j + 0.5) * pitch
            if x * x + z * z > 128 * 128:
                continue
            err = 1.2 * math.sin(1.7 * i + 0.9 * j) + 0.6 * math.cos(2.3 * j)
            h = 3.0 + 2.2 * err
            tile = box(f"site_{i}_{j}", (x - 18, THICK, z - 18), (x + 18, THICK + h, z + 18), m["bar"])
            lit = boxg(f"lit_{i}_{j}", (x - 18, THICK + h + 0.5, z - 18), (x + 18, THICK + h + 1.5, z + 18), m["lit"])
            sites.append((x, z, lit))
    # the scanner bar sweeps in z across the disc, one pass per beat
    scan = empty("scanner", root)
    box("scan_bar", (-165, 46, -2), (165, 52, 2), m["scan"], scan)
    travel(scan, [(0, 0, -150), (0, 0, 150)], 0, 4 * BF - 1, steps=4)
    # each site lights when the bar passes it
    for x, z, lit in sites:
        f_pass = round((z + 150) / 300 * (4 * BF - 1))
        envelope(lit, [(f_pass - 1, f_pass, 4 * BF - 1, 4 * BF)])
    # one site misses the spec: a red flag from beat 2
    bad = boxg("site_bad", (110 - 18, THICK + 9.5, 22 - 18), (110 + 18, THICK + 11, 22 + 18), m["bad"])
    envelope(bad, [(2 * BF, 2 * BF + 1, 4 * BF - 1, 4 * BF)])
    camera(root, [((0, 12, 0), 420, 0.6, 0.6), ((0, 12, 0), 380, 0.9, 0.55),
                  ((80, 12, 0), 360, 0.4, 0.6), ((0, 12, 0), 400, 1.2, 0.5)])
    finish("wafer_zoom_sites")


# ---- zoom b: epi -----------------------------------------------------------------------


def zoom_epi():
    root = start("zoom_epi", 4)
    m = wafer_mats()
    bulk_wafer(root, m)
    layer = empty("epi_grow", root)
    disc("epi_layer", (0, THICK, 0), R - 1, 2.0, m["epi"], layer)
    # bare for beat 0, then the layer thickens through beats 1-2 and holds
    track(layer, [(0, (1, 0.01, 1)), (BF, (1, 0.01, 1)), (3 * BF, (1, 1.5, 1)), (4 * BF - 1, (1, 1.5, 1))])
    # the gas inlet and the gas it brings across the wafer, beats 1-3
    tube("inlet", (-300, 90, 0), (-200, 30, 0), 12, m["steel"], root, verts=12)
    for k in range(6):
        p = ball(f"gas{k}", (-260, 40, 0), 12, m["gas"], root)
        f0 = BF + 6 * k
        travel(p, [(-260, 40, 0), (0, 20, 0), (260, 40, 0)], f0, f0 + 40, steps=2)
        show(p, [(BF, 4 * BF)])
    camera(root, [((0, 6, 0), 380, 0.6, 0.35), ((0, 8, 0), 380, 0.7, 0.35),
                  ((0, 10, 0), 400, 0.8, 0.3), ((0, 12, 0), 420, 0.8, 0.3)])
    finish("wafer_zoom_epi")


# ---- zoom c: SOI, implant, bond, split -------------------------------------------------


def zoom_soi():
    root = start("zoom_soi", 4)
    m = wafer_mats()
    disc("handle", (0, 3, 0), R, THICK, m["handle"], root)
    disc("oxide", (0, THICK + 0.5, 0), R, 1.0, m["oxide"], root)
    # the donor, flipped over, is device layer (thin, bottom) plus the rest of the wafer above it
    donor = empty("donor", root)
    dev = disc("device_layer", (0, 7.6, 0), R, 1.2, m["si"], donor)
    upper = empty("donor_upper", donor)
    disc("donor_body", (0, 13.0, 0), R, 9.6, m["si"], upper)
    # beat 0: the donor sits high while ions are fired into it at the implant depth
    key(donor, 0, "location", P(0, 10, 0))
    key(donor, BF, "location", P(0, 10, 0))
    key(donor, 2 * BF, "location", P(0, 0, 0))
    key(donor, 4 * BF - 1, "location", P(0, 0, 0))
    # beat 2: the upper part lifts away along the cut, leaving the device layer bonded
    key(upper, 2 * BF, "location", P(0, 0, 0))
    key(upper, 3 * BF, "location", P(0, 0, 0))
    key(upper, 4 * BF - 1, "location", P(0, 60, 0), linear=True)
    # the cut plane glows at the implant depth while the split happens
    cut = boxg("cut", (-R - 4, 8.0, -R - 4), (R + 4, 8.4, R + 4), m["cut"])
    show(cut, [(2 * BF, 3 * BF)])
    # ions drop from above into the donor's implant depth during beat 0
    for k, (x, z) in enumerate(ring(8, 90)):
        ion = ball(f"ion{k}", (x, 40, z), 6, m["ion"])
        travel(ion, [(x, 40, z), (x, 18.0, z)], 4 * k, 4 * k + 14, steps=2)
        show(ion, [(0, BF)])
    camera(root, [((0, 10, 0), 520, 0.6, 0.25), ((0, 9, 0), 480, 0.8, 0.25),
                  ((0, 9, 0), 480, 1.0, 0.25), ((0, 14, 0), 520, 0.6, 0.3)])
    finish("wafer_zoom_soi")


# ---- zoom d: the spec sheet ------------------------------------------------------------


def zoom_spec():
    root = start("zoom_spec", 4)
    m = wafer_mats()
    bulk_wafer(root, m)
    # beat 0: thickness, a caliper bracket at the rim, 775 +/- 25 um (the bracket is the spread)
    cal = empty("caliper", root)
    box("caliper_jaw_top", (R + 10, THICK + 2, -10), (R + 60, THICK + 4, 10), m["steel"], cal)
    box("caliper_jaw_bot", (R + 10, -2, -10), (R + 60, 0, 10), m["steel"], cal)
    box("caliper_bar", (R + 52, -2, -3), (R + 58, THICK + 4, 3), m["scan"], cal)
    show(cal, [(0, BF)])
    # beat 1: TTV, the spread of thickness across the disc, as a profile line of bars
    prof = empty("profile", root)
    for k in range(-7, 8):
        x = k * 19.0
        h = 2.5 * math.sin(0.25 * k) + 1.0
        box(f"prof_{k}", (x - 6, THICK + 0.5, -R - 30), (x + 6, THICK + 0.5 + h, -R - 20), m["lit"], prof)
    show(prof, [(BF, 2 * BF)])
    # beat 2: edge exclusion, the outer 3 mm of the disc
    edge = empty("edge", root)
    for k, (x, z) in enumerate(ring(64, R - 1.5)):
        ang = 2 * math.pi * k / 64
        box(f"edge_{k}", (x - 2, THICK + 0.6, z - 2), (x + 2, THICK + 2.0, z + 2), m["bad"], edge)
    show(edge, [(2 * BF, 3 * BF)])
    # beat 3: the three numbers side by side as bars
    for k, (name, v) in enumerate([("thick", 775), ("ttv", 5), ("edge", 3)]):
        x = -200 + k * 200
        grow_bar(root, name, x - 40, x + 40, v / 4, m["bar"], 3 * BF, 4 * BF - 1, z0=-60, z1=60)
    camera(root, [((0, 20, 0), 620, 0.5, 0.55), ((0, 20, 0), 560, 0.7, 0.35),
                  ((0, 20, 0), 560, 0.7, 0.35), ((0, 40, 0), 560, 0.2, 0.35)])
    finish("wafer_zoom_spec")


# ---- sections --------------------------------------------------------------------------


def sec1_what_it_is():
    root = start("sec1", 3)
    m = wafer_mats()
    steel = m["steel"]
    stations = ["POLISHED", "EPI or SOI", "INSPECT", "PACK", "FAB"]
    xs = [-1200, -600, 0, 600, 1200]
    for k, x in enumerate(xs):
        box(f"station{k}", (x - 150, 0, -200), (x + 150, 300, 200), steel, root)
    box("track", (-1400, -40, -260), (1400, 0, 260), m["frame"], root)
    d = bulk_wafer(root, m, centre=(-1200, 300 + 3, 0), name="disc")
    # the disc rides the track station to station, one leg per beat
    travel(d, [(-1200, 303, 0), (-600, 303, 0), (0, 303, 0), (600, 303, 0)], 0, 3 * BF - 1, steps=3)
    epi = empty("epi_tag", root)
    disc("epi_coat", (-600, 303 + THICK, 0), R - 1, 2.0, m["epi"], epi)
    show(epi, [(BF, 2 * BF)])
    foup = empty("foup", root)
    box("foup", (560, 300, -150), (640, 420, 150), m["frame"], foup)
    show(foup, [(2 * BF, 3 * BF)])
    camera(root, [((-900, 300, 0), 2600, 0.3, 0.3), ((-200, 300, 0), 2600, 0.3, 0.3),
                  ((600, 320, 0), 2600, 0.3, 0.3)])
    finish("wafer_sec1")


def sec2_cross_sections():
    root = start("sec2", 3)
    m = wafer_mats()
    # three flavours side by side in profile; one is in focus per beat, the rest sit back
    bulk = empty("bulk", root, loc=(-600, 0, 0))
    disc("bulk_slab", (-600, 0, 0), 200, 1, m["si"], root)
    disc("bulk_body", (-600, 40, 0), 200, 60, m["si"], bulk)
    epi = empty("epi", root, loc=(0, 0, 0))
    disc("epi_body", (0, 40, 0), 200, 60, m["si"], epi)
    disc("epi_layer", (0, 71, 0), 199, 6, m["epi"], epi)
    soi = empty("soi", root, loc=(600, 0, 0))
    disc("soi_handle", (600, 40, 0), 200, 60, m["handle"], soi)
    disc("soi_oxide", (600, 71, 0), 200, 4, m["oxide"], soi)
    disc("soi_device", (600, 78, 0), 200, 8, m["si"], soi)
    for g, k in [(bulk, 0), (epi, 1), (soi, 2)]:
        envelope(g, [(k * BF, k * BF + 2, (k + 1) * BF - 2, (k + 1) * BF + 4)])
    camera(root, [((-600, 50, 0), 620, 0.5, 0.3), ((0, 60, 0), 620, 0.5, 0.3),
                  ((600, 70, 0), 620, 0.5, 0.3)])
    finish("wafer_sec2")


def sec3_specs():
    root = start("sec3", 3)
    m = wafer_mats()
    bulk_wafer(root, m)
    sites = empty("sites", root)
    pitch = 60.0
    for i in range(-2, 3):
        for j in range(-2, 3):
            x, z = (i + 0.5) * pitch, (j + 0.5) * pitch
            if x * x + z * z > 130 * 130:
                continue
            h = 2.0 + 1.5 * math.sin(1.3 * i + 0.7 * j)
            box(f"s{i}_{j}", (x - 22, THICK, z - 22), (x + 22, THICK + h, z + 22), m["lit"], sites)
    show(sites, [(BF, 3 * BF)])
    cal = empty("caliper", root)
    box("cal_bar", (R + 20, -2, -3), (R + 26, THICK + 6, 3), m["scan"], cal)
    show(cal, [(0, BF)])
    camera(root, [((0, 10, 0), 720, 0.5, 0.5), ((0, 10, 0), 640, 0.9, 0.45),
                  ((0, 10, 0), 640, 1.3, 0.45)])
    finish("wafer_sec3")


def sec4_numbers():
    root = start("sec4", 3)
    m = wafer_mats()
    # three columns: shipments (million sq in), revenue ($B), 300 mm share (%)
    cols = [(-600, 12973 / 60, m["bar"]), (0, 11.4 * 20, m["hi"]), (600, 67 * 4, m["bar"])]
    for k, (x, h, mm) in enumerate(cols):
        grow_bar(root, f"num{k}", x - 130, x + 130, h, mm, k * BF, (k + 1) * BF, z0=-150, z1=150)
    marker(root, "ship_arrow", -600, 12973 / 60 + 20, m["dot"], r=40)
    camera(root, [((-600, 200, 0), 2200, 0.3, 0.2), ((0, 200, 0), 2200, 0.3, 0.2),
                  ((600, 200, 0), 2200, 0.3, 0.2)])
    finish("wafer_sec4")


def sec5_share():
    root = start("sec5", 3)
    m = wafer_mats()
    data = [("Shin-Etsu", 29.4), ("SUMCO", 21.9), ("GlobalWafers", 15.2), ("Siltronic", 11.5),
            ("SK Siltron", 11.4), ("Soitec", 5.5)]
    for k, (name, pct) in enumerate(data):
        x = -750 + k * 300
        mm = m["hi"] if k < 2 else m["bar"]
        f0 = 0 if k < 2 else (BF if k < 5 else 2 * BF)
        grow_bar(root, name, x - 100, x + 100, pct * 12, mm, f0, f0 + BF)
    # the top five bracket in beat 2: a bar laid across their tops
    span = boxg("top5_bracket", (-750 - 120, 390, -20), (-750 + 4 * 300 + 120, 400, 20), m["lit"])
    show(span, [(2 * BF, 3 * BF)])
    camera(root, [((-400, 150, 0), 2600, 0.2, 0.2), ((0, 150, 0), 2600, 0.2, 0.2),
                  ((0, 180, 0), 2800, 0.2, 0.2)])
    finish("wafer_sec5")


def sec6_structure():
    root = start("sec6", 3)
    m = wafer_mats()
    # five makers as towers, their shares summing above 90 percent
    shares = [30, 24, 18, 13, 9]
    for k, s in enumerate(shares):
        x = -600 + k * 300
        grow_bar(root, f"maker{k}", x - 100, x + 100, s * 12, m["bar"] if k else m["hi"], 0, BF)
    # beat 1: a merger that would have made GlobalWafers number two; the link breaks
    link = empty("merger_link", root)
    tube("merger_arc", (-300, 380, 0), (0, 400, 0), 8, m["dash"], link, verts=8)
    tube("merger_arc2", (0, 400, 0), (300, 380, 0), 8, m["dash"], link, verts=8)
    show(link, [(BF, 2 * BF)])
    # beat 2: Japanese makers hold most of the 300 mm epitaxial wafers
    jp = grow_bar(root, "jp_epi", 300, 500, 60 * 12, m["hi"], 2 * BF, 3 * BF)
    camera(root, [((0, 200, 0), 2600, 0.2, 0.2), ((0, 250, 0), 2600, 0.2, 0.2),
                  ((300, 300, 0), 2400, 0.2, 0.2)])
    finish("wafer_sec6")


def sec7_risks():
    root = start("sec7", 3)
    m = wafer_mats()
    # beat 0: one supplier shakes, the rest feel it
    blocks = []
    for k in range(5):
        x = -800 + k * 400
        b = empty(f"supplier{k}", root)
        box(f"supplier_box{k}", (x - 120, 0, -120), (x + 120, 220, 120), m["quake"] if k == 0 else m["steel"], b)
        blocks.append(b)
    wobble(blocks[0], 0, BF, 40, every=4)
    # beat 1: a qualification timeline: a long bar, a slow marker moving along it
    q = grow_bar(root, "qualification", -900, 900, 60, m["bar"], BF, BF + 2)
    mk = marker(root, "qual_marker", -900, 60, m["dot"], r=60)
    travel(mk, [(-900, 60, 0), (900, 60, 0)], BF, 2 * BF, steps=2)
    # beat 2: two speeds: AI and HBM wafers up, mature nodes down
    grow_bar(root, "ai_up", -300, -100, 400, m["hi"], 2 * BF, 3 * BF)
    grow_bar(root, "mature_down", 100, 300, 180, m["bar"], 2 * BF, 3 * BF)
    camera(root, [((0, 150, 0), 3200, 0.3, 0.25), ((0, 120, 0), 2600, 0.3, 0.2),
                  ((0, 200, 0), 2600, 0.3, 0.2)])
    finish("wafer_sec7")


def sec8_connects():
    root = start("sec8", 3)
    m = wafer_mats()
    names = [("SLICE + POLISH", -1200), ("POLYSILICON", -1200), ("MELT + PULL", -1200)]
    up = [(-1600, 200, 500), (-1600, 200, 0), (-1600, 200, -500)]
    for k, (x, y, z) in enumerate(up):
        box(f"upstream{k}", (x - 150, 0, z - 120), (x + 150, 240, z + 120), m["steel"], root)
    box("wafer_centre", (-150, 0, -150), (150, 300, 150), m["frame"], root)
    down = [(900, 200, 500), (900, 200, 0), (900, 200, -500)]
    for k, (x, y, z) in enumerate(down):
        box(f"downstream{k}", (x - 150, 0, z - 120), (x + 150, 240, z + 120), m["steel"], root)
    # beat 0: the upstream steps feed the wafer, beat 1 the wafer sits at the centre, beat 2 it goes on
    for k, (x, y, z) in enumerate(up):
        lump = ball(f"feed{k}", (x + 150, 120, z), 60, m["lump"], root)
        travel(lump, [(x + 150, 120, z), (-150, 120, 0)], k * 4, BF - 6, steps=2)
        show(lump, [(0, BF)])
    disc("wafer", (0, 150, 0), R, THICK, m["si"], root)
    for k, (x, y, z) in enumerate(down):
        d = ball(f"out{k}", (150, 120, 0), 60, m["lump"], root)
        travel(d, [(150, 120, 0), (x - 150, 120, z)], 2 * BF + 4 * k, 3 * BF - 4, steps=2)
        show(d, [(2 * BF, 3 * BF)])
    camera(root, [((-700, 200, 0), 3200, 0.3, 0.3), ((0, 200, 0), 3000, 0.3, 0.3),
                  ((700, 200, 0), 3200, 0.3, 0.3)])
    finish("wafer_sec8")


def sec9_sources():
    root = start("sec9", 3)
    m = wafer_mats()
    cards = empty("cards", root)
    for k in range(9):
        beat = k // 3
        y0 = 4 + k * 6
        card = empty(f"card{k}_grp", cards)
        box(f"card{k}", (-250, y0, -175), (250, y0 + 4, 175), m["card"], card)
        start_x = -1200 if k % 2 == 0 else 1200
        angle = 0.9 if k % 2 == 0 else -0.9
        f0 = beat * BF + 2 * (k % 3)
        f1 = f0 + BF - 6
        key(card, f0, "location", P(start_x, 0, 0))
        key(card, f0, "rotation_euler", (0, 0, angle))
        key(card, f1, "location", P(0, 0, 0))
        key(card, f1, "rotation_euler", (0, 0, 0))
    camera(root, [((0, 80, 0), 2000, 0.6, 0.7), ((0, 80, 0), 2000, 0.9, 0.7),
                  ((0, 80, 0), 2000, 0.3, 0.8)])
    finish("wafer_sec9")


def build_all():
    zoom_sites()
    zoom_epi()
    zoom_soi()
    zoom_spec()
    sec1_what_it_is()
    sec2_cross_sections()
    sec3_specs()
    sec4_numbers()
    sec5_share()
    sec6_structure()
    sec7_risks()
    sec8_connects()
    sec9_sources()


if __name__ == "__main__":
    build_all()
