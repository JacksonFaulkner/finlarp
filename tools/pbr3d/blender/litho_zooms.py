"""The six LITHO zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the scanner pieces in litho_kit.py. Keys match the procedural
page: a the reticle, b the lens and NA, c inside the resist, d step and scan, e overlay, f EUV.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/litho_zooms.py [-- reticle lens ...]

For each zoom it writes blender/litho_<name>.blend and assets/litho_<name>.glb. Every zoom is four
beats (32 s). The names are the GLB names: reticle, lens, resist, scan, overlay, euv.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, disc, empty, key, label, mat, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
from poly_overview import run  # noqa: E402
import litho_kit as K  # noqa: E402
from litho_kit import END, RES_TOP, RET_Y  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="litho")
    K.mats(m)
    return m, root


# ---- a: the reticle -----------------------------------------------------------------------

DIE_X = (-75.0, 15.0, 75.0)  # three dies below the mask, under the openings
DIE_Y0, DIE_Y1 = 80.0, 110.0


def reticle():
    m, root = begin("reticle")
    K.source(root, m, on=[(F(1, 0), END)])
    K.reticle(root, m)
    for k, x in enumerate(DIE_X):
        box(f"die{k}", (x - 20, DIE_Y0, -40), (x + 20, DIE_Y1, 0), m["silicon"], root)
    # one speck in the opening at x = 15 on the mask, and the same flaw on each die (beat 2)
    speck = empty("speck", root)
    box("speck_m", (12, RET_Y + 12, -8), (18, RET_Y + 18, -2), m["red"], speck)
    show(speck, [(F(2, 0.0), END)])
    for k, x in enumerate(DIE_X):
        fl = empty(f"flaw{k}", root)
        box(f"flaw{k}_m", (x + 4, DIE_Y1 - 2, -10), (x + 10, DIE_Y1 + 2, -4), m["red"], fl)
        show(fl, [(F(2, 0.3), END)])
    K.rays(root, m, 1, 0.0, 0.7, lambda x: [(x, K.SRC_GLOW[0], K.RAY_Z), (x, DIE_Y1 + 4, K.RAY_Z)], n=3, life=44)
    K.rays(root, m, 3, 0.0, 0.7, lambda x: [(x, K.SRC_GLOW[0], K.RAY_Z), (x, DIE_Y1 + 4, K.RAY_Z)], n=3, life=44)
    label("chrome bars block the light", (-150, RET_Y + 22, 20), root, [(F(0, 0), F(1, 0))])
    label("clear quartz passes it", (-150, RET_Y - 10, 20), root, [(F(1, 0), F(2, 0))])
    label("speck: one flaw in the mask", (40, RET_Y + 30, 20), root, [(F(2, 0), F(3, 0))])
    label("same flaw on every die", (-75, DIE_Y1 + 20, 20), root, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 650.0, 0.0), 560.0, 0.30, 0.14),
        ((0.0, 360.0, 0.0), 1250.0, 0.26, 0.12),
        ((0.0, 650.0, 0.0), 520.0, 0.26, 0.14),
        ((0.0, 105.0, 0.0), 420.0, 0.22, 0.18),
    ])
    finish("reticle", page="litho")


# ---- b: the lens, numerical aperture and the in-focus band --------------------------------

FOCUS = (0.0, RES_TOP + 2, 0.0)
NA_LOW_R, NA_HIGH_R = 60.0, 100.0  # the cone's radius at the lens top, for NA 0.33 and 0.55


def cone_rays(root, m, b, r, n_angles=6):
    """The cone of light from the lens top to the focus, shown in beat b."""
    g = empty(f"cone{b}", root)
    for j in range(n_angles):
        a = 2 * math.pi * j / n_angles
        tube(f"cone{b}_{j}", (r * math.cos(a), K.LENS_Y1 + 30, r * math.sin(a)), FOCUS, 1.6, m["light"], g, verts=6)
    show(g, beat(b))


def lens():
    m, root = begin("lens")
    K.lens(root, m, slit_on=[])
    K.wafer(root, m)
    # NA 0.33 in beats 0 and 2; NA 0.55 in beats 1 and 3
    cone_rays(root, m, 0, NA_LOW_R)
    cone_rays(root, m, 2, NA_LOW_R)
    cone_rays(root, m, 1, NA_HIGH_R)
    cone_rays(root, m, 3, NA_HIGH_R)
    # the in-focus band: long at NA 0.33 (beat 2), short at NA 0.55 (beat 3), shorter by NA^2
    long_b = empty("band_long", root)
    tube("band_long_m", (0, RES_TOP - 150, 14), (0, RES_TOP + 150, 14), 10, m["band"], long_b, verts=12)
    show(long_b, [(F(2, 0.1), F(3, 0.0))])
    short_b = empty("band_short", root)
    half = 150.0 * (0.33 / 0.55) ** 2
    tube("band_short_m", (0, RES_TOP - half, 14), (0, RES_TOP + half, 14), 10, m["band"], short_b, verts=12)
    show(short_b, [(F(3, 0.1), END)])
    label("NA 0.33: narrow cone", (120, 300, 20), root, [(F(0, 0), F(1, 0))])
    label("NA 0.55: wider cone, finer line", (120, 300, 20), root, [(F(1, 0), F(2, 0))])
    label("NA 0.33: long in-focus band", (60, RES_TOP + 150, 20), root, [(F(2, 0.1), F(3, 0))])
    label("NA 0.55: band about 2.8x shorter", (60, RES_TOP + 60, 20), root, [(F(3, 0.1), END)])
    camera(root, [
        ((0.0, 300.0, 0.0), 1200.0, 0.25, 0.10),
        ((0.0, 300.0, 0.0), 1200.0, 0.25, 0.10),
        ((0.0, 200.0, 0.0), 900.0, 0.25, 0.10),
        ((0.0, 200.0, 0.0), 900.0, 0.25, 0.10),
    ])
    finish("lens", page="litho")


# ---- c: inside the resist -----------------------------------------------------------------

COL_X = (-60.0, 0.0, 60.0)  # exposed columns
COL_W = 24.0
FILM_Y0, FILM_Y1, RES_Y0, RES_Y1 = 30.0, 36.0, 36.0, 46.0


def resist():
    m, root = begin("resist")
    # the substrate, the film, and the resist between the columns (purple, always there)
    box("substrate", (-140, 0, -60), (140, FILM_Y0, 0), m["silicon"], root)
    segs = [(-140, -72), (-48, -12), (12, 48), (72, 140)]
    for k, (x0, x1) in enumerate(segs):
        box(f"film_seg{k}", (x0, FILM_Y0, -60), (x1, FILM_Y1, 0), m["film"], root)
        box(f"res_seg{k}", (x0, RES_Y0, -60), (x1, RES_Y1, 0), m["purple"], root)
    # under each exposed column: film (cut away by etch) and a column of resist
    gap = empty("film_gap", root)
    for k, x in enumerate(COL_X):
        box(f"gap_film{k}", (x - COL_W / 2, FILM_Y0, -60), (x + COL_W / 2, FILM_Y1, 0), m["film"], gap)
    show(gap, [(0, F(2, 0.25)), (F(3, 0.0), END)])
    # exposed columns: pink, with acid dots in beat 0; they sink away in beat 1
    cols = empty("exposed", root)
    for k, x in enumerate(COL_X):
        box(f"col{k}", (x - COL_W / 2, RES_Y0, -60), (x + COL_W / 2, RES_Y1, 0), m["exposed"], cols)
    key(cols, F(1, 0.0), "location", P(0, 0, 0), linear=True)
    key(cols, F(1, 0.75), "location", P(0, -RES_Y1 + RES_Y0 - 2, 0), linear=True)
    show(cols, [(0, F(1, 0.85))])
    acid = empty("acid", root)
    for k, x in enumerate(COL_X):
        for j, y in enumerate((39.0, 42.0, 44.0)):
            ball(f"acid{k}_{j}", (x + (j - 1) * 6, y, 1.0), 2.2, m["acid"], acid, 12)
    show(acid, [(F(0, 0.3), F(1, 0.8))])
    # the etch: ions fall down the trenches once the film gap is open (beat 2)
    for k, x in enumerate(COL_X):
        run(root, f"ion{k}_", 3, [(x, 70.0, -14), (x, FILM_Y0 + 1, -14)], 3.5, m["acid"], 2, 0.1 + 0.25 * k / 3, 0.55, 36)
    # refill (beat 3): fresh film and resist come back where the columns were
    fresh = empty("fresh", root)
    for k, x in enumerate(COL_X):
        box(f"fresh_res{k}", (x - COL_W / 2, RES_Y0, -60), (x + COL_W / 2, RES_Y1, 0), m["purple"], fresh)
    show(fresh, [(F(3, 0.0), END)])
    label("expose: acid forms in the resist", (-120, 60, 20), root, [(F(0, 0), F(1, 0))])
    label("develop: exposed resist sinks away", (-120, 60, 20), root, [(F(1, 0), F(2, 0))])
    label("etch: film cut where resist is gone", (-120, 60, 20), root, [(F(2, 0), F(3, 0))])
    label("fresh resist for the next layer", (-120, 60, 20), root, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 30.0, 0.0), 560.0, 0.22, 0.20),
        ((0.0, 30.0, 0.0), 560.0, 0.22, 0.20),
        ((0.0, 30.0, 0.0), 560.0, 0.22, 0.20),
        ((0.0, 30.0, 0.0), 560.0, 0.22, 0.20),
    ])
    finish("resist", page="litho")


# ---- d: step and scan ---------------------------------------------------------------------


def scan():
    m, root = begin("scan")
    K.frame(root, m)
    K.source(root, m, on=[(F(0, 0), END)])
    ret = K.reticle(root, m)
    w0 = K.plan(F(0, 0.10), 0.85 * 192, 1)  # beat 0: one field scanned slowly
    w1 = K.plan(F(1, 0.0), 0.20 * 192, 4)  # beat 1: four fields stepped, scans alternating in time
    windows = w0 + w1
    lens = K.lens(root, m, slit_on=[(f0, f1) for f0, f1, _, _ in windows])  # noqa: F841
    wg, tiles = K.wafer(root, m)
    key(wg, 0, "location", P(0, 0, 0))
    key(wg, F(0, 0.0), "location", P(K.X_START, 0, 0))
    K.scan_keys(wg, ret, windows, k0=0)
    for k in range(5):
        f1 = windows[k][1]
        pink, cy = tiles[k]
        show(pink, [(f1, END)])
    # beat 2 and 3: High-NA halves each field; the orange line marks the split
    splits = empty("splits", root)
    for k in range(5):
        c = K.field_x(k)
        box(f"split{k}", (c - 0.8, RES_TOP, -26), (c + 0.8, RES_TOP + 3, 0), m["alarm"], splits)
    show(splits, [(F(2, 0.0), END)])
    label("slit: one strip of the field", (-30, K.LENS_Y0 - 10, 20), root, [(F(0, 0), F(1, 0))])
    label("step, then scan the next field", (0, RES_TOP + 40, 20), wg, [(F(1, 0), F(2, 0))])
    label("High-NA: fields half as tall", (0, RES_TOP + 40, 20), wg, [(F(2, 0), F(3, 0))])
    label("so a wafer takes about twice the exposures", (0, RES_TOP + 40, 20), wg, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 120.0, 0.0), 1000.0, 0.22, 0.14),
        ((0.0, 40.0, 0.0), 720.0, 0.22, 0.42),
        ((0.0, 40.0, 0.0), 620.0, 0.22, 0.42),
        ((0.0, 40.0, 0.0), 620.0, 0.22, 0.42),
    ])
    finish("scan", page="litho")


# ---- e: overlay ---------------------------------------------------------------------------

LINE_PITCH = 40.0
LINE_W = 20.0
LINES = [-120.0 + LINE_PITCH * k for k in range(7)]
NEW_Y0, NEW_Y1 = 30.0, 50.0
OLD_Y0, OLD_Y1 = 0.0, 20.0


def overlay():
    m, root = begin("overlay")
    old = empty("old_layer", root)
    for k, x in enumerate(LINES):
        box(f"old{k}", (x - LINE_W / 2, OLD_Y0, -40), (x + LINE_W / 2, OLD_Y1, 0), m["cyan"], old)
    # alignment marks printed on the layer below (beat 1 reads them)
    for k, x in enumerate((-150.0, 150.0)):
        box(f"mark{k}_x", (x - 8, OLD_Y1, -2), (x + 8, OLD_Y1 + 2, 0), m["steel"], root)
    new = empty("new_layer", root)
    for k, x in enumerate(LINES):
        box(f"new{k}", (x - LINE_W / 2, NEW_Y0, -40), (x + LINE_W / 2, NEW_Y1, 0), m["exposed"], new)
    OFFSET = 24.0
    key(new, 0, "location", P(OFFSET, 0, 0))
    key(new, F(1, 0.1), "location", P(OFFSET, 0, 0))
    key(new, F(1, 0.7), "location", P(0, 0, 0), linear=True)
    key(new, F(2, 0.0), "location", P(0, 0, 0))
    key(new, F(3, 0.1), "location", P(-10, 0, 0), linear=True)  # the next wafer lands off again
    key(new, F(3, 0.9), "location", P(-10, 0, 0))
    # the sensor beams from above read the marks (beat 1)
    beams = empty("sensor_beams", root)
    for k, x in enumerate((-150.0, 150.0)):
        box(f"sens{k}", (x - 10, 120, -10), (x + 10, 130, 0), m["sensor"], beams)
        tube(f"sbeam{k}", (x, 120, -4), (x, OLD_Y1 + 2, -4), 3, m["sensor"], beams, verts=8)
    show(beams, [(F(1, 0.0), F(2, 0.0))])
    label("new layer sits off the one below", (60, 90, 20), root, [(F(0, 0), F(1, 0))])
    label("sensor reads the marks; the stage corrects", (-60, 150, 20), root, [(F(1, 0), F(2, 0))])
    label("budget: a few nanometres", (60, 90, 20), root, [(F(2, 0), F(3, 0))])
    label("the next wafer drifts off again", (60, 90, 20), root, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 30.0, 0.0), 560.0, 0.20, 0.18),
        ((0.0, 60.0, 0.0), 620.0, 0.20, 0.18),
        ((0.0, 30.0, 0.0), 540.0, 0.20, 0.18),
        ((0.0, 30.0, 0.0), 540.0, 0.20, 0.18),
    ])
    finish("overlay", page="litho")


# ---- f: EUV light -------------------------------------------------------------------------

MIRRORS = [(-160.0, 180.0, -40.0), (-40.0, 110.0, 30.0), (80.0, 40.0, -30.0), (190.0, -30.0, 20.0)]


def euv():
    m, root = begin("euv")
    # beat 0: two pulses hit each falling droplet. The pre-pulse flattens it into a disk; the main
    # pulse turns the disk into plasma, which glows at 13.5 nm and throws off debris (web: two-pulse
    # tin-droplet scheme, pre-pulse makes a flattened disk, main pulse makes the EUV plasma)
    m["pre"] = mat("prepulse", (1.0, 0.55, 0.15), emit=(1.0, 0.55, 0.15), strength=3.0)
    m["euv"] = mat("euv_glow", (0.55, 0.80, 1.0), emit=(0.55, 0.80, 1.0), strength=1.5, alpha=0.25)
    # timing (beat 0 = 8 s): the drop falls at one constant speed from y 330 to y 30 over 0.80 of the
    # beat. It crosses the pre-pulse beam (y 62-67) at 0.70 and the main beam (y 44-52) at 0.75, so
    # the lasers meet it on the way down and it never slows.
    drop = empty("droplet", root)
    key(drop, F(0, 0.0), "location", P(0, 330, 0), linear=True)
    key(drop, F(0, 0.80), "location", P(0, 30, 0), linear=True)
    show(drop, [(F(0, 0.0), F(0, 0.68))])
    # the drop flattens as the pre-pulse reaches it (0.70 -> 0.76), radius 9 -> 22, height 18 -> 4
    squash = pivot("squash", (0, 0, 0), drop)
    ball("drop_m", (0, 0, 0), 9, m["tin"], squash, 24)
    scale_keys(squash, [
        (0, (1, 1, 1)),
        (F(0, 0.55), (1, 1, 1)),
        (F(0, 0.565), (1.5, 1.5, 0.62)),
        (F(0, 0.58), (2.1, 2.1, 0.34)),
        (F(0, 0.60), (2.45, 2.45, 0.22)),
        (F(0, 0.80), (2.45, 2.45, 0.22)),
    ], until=F(0, 0.55))
    # the pre-pulse beam from its machine, on while the drop crosses it
    # it fires out of its mouth and reaches the drop in about 0.03 of the beat
    pre = empty("prepulse", root)
    mouth = (-224.0, 90.5, -6.0)  # the drop's centre crosses this height at about 0.64
    grow_pre = pivot("pre_grow", mouth, pre)
    box("pre_m", rel(mouth, (-224, 88, -10)), rel(mouth, (0, 93, -2)), m["pre"], grow_pre)
    scale_keys(grow_pre, [(0, (0.01, 1, 1)), (F(0, 0.50), (0.01, 1, 1)), (F(0, 0.53), (1, 1, 1)), (F(0, 0.64), (1, 1, 1))], until=F(0, 0.50))
    show(pre, [(F(0, 0.50), F(0, 0.64))])
    # the machines: a solid-state pre-pulse laser and the CO2 main laser, each with its beam mouth
    src = empty("laser_machines", root)
    box("pre_housing", (-300, 82, -40), (-220, 100, 10), m["grey"], src)
    box("pre_mouth", (-224, 86, -14), (-218, 95, -6), m["pre"], src)
    box("co2_housing", (-300, 8, -40), (-220, 52, 10), m["grey"], src)
    box("co2_mouth", (-224, 44, -14), (-218, 52, -6), m["light"], src)
    show(src, [(F(0, 0.0), F(1, 0.0))])
    label("pre-pulse laser", (-290, 122, 20), root, [(F(0, 0.0), F(1, 0.0))])
    label("CO2 laser", (-290, -40, 20), root, [(F(0, 0.0), F(1, 0.0))])
    # the main pulse from the CO2 laser, through the flat drop at y 48; plasma and debris follow
    flash = empty("laser_flash", root)
    box("laser_m", (-224, 44, -10), (200, 52, -2), m["light"], flash)
    show(flash, [(F(0, 0.67), F(0, 0.86))])
    plasma = empty("plasma", root)
    grow = pivot("plasma_grow", (0, 48, 0), plasma)
    ball("plasma_m", (0, 48, 0), 28, m["plasma"], grow, 16)
    ball("euv_m", (0, 48, 0), 40, m["euv"], grow, 16)
    scale_keys(grow, [(0, (0.05, 0.05, 0.05)), (F(0, 0.68), (0.05, 0.05, 0.05)), (F(0, 0.86), (1.0, 1.0, 1.0)), (F(1, 0.0), (1.2, 1.2, 1.2))], until=F(0, 0.68))
    show(plasma, [(F(0, 0.68), F(1, 0.0))])
    run(root, "debris_", 8, [(0, 48, 0), (110, 90, 40)], 4, m["tin"], 0, 0.68, 0.78, 30)
    label("tin droplet falls: laser hits it twice", (40, 200, 20), root, [(F(0, 0), F(0, 0.50))])
    label("1st pulse flattens the droplet", (-150, 150, 20), root, [(F(0, 0.56), F(0, 0.66))])
    label("2nd pulse makes the plasma", (-150, 130, 20), root, [(F(0, 0.68), F(1, 0.0))])
    label("13.5 nm EUV light", (-70, 175, 20), root, [(F(0, 0.72), F(1, 0.0))])

    # beat 1: light bounces off mirrors; each keeps about 70%
    for k, (x, y, a) in enumerate(MIRRORS):
        mir = empty(f"mirror{k}", root)
        box(f"mirror{k}_m", (x - 40, y - 8, -30), (x + 40, y + 8, 0), m["mirror"], mir)
        mir.rotation_euler = (0, 0, math.radians(a))
        show(mir, [(F(1, 0.0), END)])
    pts = [(-260, 200, 10)] + [(x, y + 14, 10) for x, y, _ in MIRRORS] + [(260, -110, 10)]
    run(root, "beam_", 12, pts, 8, m["light"], 1, 0.0, 0.8, 48)
    # beat 2: the parts that must hold sub-nanometre alignment: a pile, and one mirror trembles
    pile = empty("parts", root)
    for k in range(9):
        rr = 26 + 10 * (k % 3)
        x = -200 + 50 * (k % 5)
        y = -170 + 20 * (k // 5)
        box(f"part{k}", (x - rr, y - rr / 2, -40), (x + rr, y + rr / 2, -10), m["grey"], pile)
    show(pile, [(F(2, 0.0), END)])
    tremble = empty("tremble", root)
    key(tremble, F(2, 0.0), "rotation_euler", (0, 0, 0), linear=True)
    key(tremble, F(2, 0.5), "rotation_euler", (0, 0, math.radians(2.0)), linear=True)
    key(tremble, F(2, 0.9), "rotation_euler", (0, 0, math.radians(-1.0)), linear=True)
    key(tremble, F(3, 0.0), "rotation_euler", (0, 0, 0), linear=True)
    label("Zeiss: ultra-flat optics", (-120, -40, 20), root, [(F(2, 0), F(3, 0))])
    label("a dozen mirrors leave about 1%", (60, 230, 20), root, [(F(3, 0), END)])
    label("70% per mirror", (-190, 260, 20), root, [(F(1, 0), F(2, 0))])
    camera(root, [
        ((-90.0, 110.0, 0.0), 800.0, 0.20, 0.10),
        ((0.0, 120.0, 0.0), 900.0, 0.20, 0.10),
        ((0.0, 40.0, 0.0), 900.0, 0.20, 0.10),
        ((0.0, 70.0, 0.0), 900.0, 0.20, 0.10),
    ])
    finish("euv", page="litho")


BUILDS = {
    "reticle": reticle,
    "lens": lens,
    "resist": resist,
    "scan": scan,
    "overlay": overlay,
    "euv": euv,
}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDS)
    for name in which:
        BUILDS[name]()
