"""The LITHO exposure scanner as reusable Blender pieces for the LITHO pictures (overview, zooms,
sections). Built on the SAND helpers (sand_overview, sand_zooms) and poly_overview's tube runs.

Schematic millimetres, Y up, cut-away at z = 0 with the camera on +z (docs/diagram-pages.md).
The scanner runs top to bottom: a source (light plate) above the reticle (chrome on quartz), a
projection lens (4x), a slit, and the wafer on its chuck. The wafer's field row lies on the cut
face, and the wafer slides under the slit while the reticle slides the other way, 4x as far.

Groups sit at the origin and their children are built in absolute coordinates; a group that moves
is keyed by its location (P(dx, 0, 0)). A group that switches on and off is an empty wrapped
around its boxes: `show()` scales the empty, never a box (a box's scale is its size).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, cut, disc, empty, key, label, mat, show, tube, M  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402,F401
from poly_overview import run, shell  # noqa: E402,F401

END = F(40, 0)  # "until the end" for intervals

WR = 150.0  # wafer radius (300 mm)
SUB_T = 30.0  # substrate, y 0..30
FILM_T = 6.0  # film, y 30..36
RES_T = 10.0  # photoresist, y 36..46
RES_TOP = SUB_T + FILM_T + RES_T  # 46

FIELD_PITCH = 30.0  # one field's width on the wafer, and the stage step
FIELDS = 9  # fields across the row on the cut face
X_START = 135.0  # wafer x before field 0's scan (its centre sits under the slit)

LENS_R = 120.0
LENS_Y0, LENS_Y1 = 170.0, 600.0
RET_Y = 660.0  # reticle, centred on this height
RET_HALF = 130.0
OPENINGS = [-105.0, -45.0, 15.0, 75.0]  # clear gaps in the chrome, centres
OPEN_W = 30.0
SRC_GLOW = (776.0, 792.0)  # the light plate under the source housing
SENSOR_X = 260.0  # the alignment sensor, beside the lens
MARK_X = 110.0  # an alignment mark on the wafer
RAY_Z = 6.0  # light rays run just in front of the cut plane, so the opaque plates don't hide them


def mats(m):
    """The LITHO materials, added to the shared set from M()."""
    m["chrome"] = mat("litho_chrome", (0.78, 0.80, 0.84), metal=0.95, rough=0.18)
    m["light"] = mat("litho_light", (1.0, 0.90, 0.45), emit=(1.0, 0.88, 0.40), strength=4.0)
    m["exposed"] = mat("litho_exposed", (1.0, 0.45, 0.78), emit=(1.0, 0.40, 0.72), strength=2.0)
    m["purple"] = mat("litho_purple", (0.42, 0.22, 0.62), rough=0.5)
    m["film"] = mat("litho_film", (0.50, 0.52, 0.56), metal=0.3, rough=0.6)
    m["cyan"] = mat("litho_cyan", (0.25, 0.85, 0.95), emit=(0.25, 0.85, 0.95), strength=1.5)
    m["sensor"] = mat("litho_sensor", (0.20, 1.0, 0.45), emit=(0.20, 1.0, 0.45), strength=3.5)
    m["alarm"] = mat("litho_alarm", (1.0, 0.50, 0.12), emit=(1.0, 0.50, 0.12), strength=3.0)
    m["band"] = mat("litho_band", (0.72, 0.50, 1.0), emit=(0.72, 0.50, 1.0), strength=1.6, alpha=0.5)
    m["tin"] = mat("litho_tin", (0.72, 0.74, 0.78), metal=0.9, rough=0.25)
    m["plasma"] = mat("litho_plasma", (1.0, 0.95, 0.85), emit=(1.0, 0.95, 0.85), strength=12.0)
    m["mirror"] = mat("litho_mirror", (0.25, 0.35, 0.50), metal=0.85, rough=0.15)
    m["acid"] = mat("litho_acid", (0.25, 0.55, 1.0), emit=(0.25, 0.55, 1.0), strength=2.0)
    m["cell"] = mat("litho_cell", (1.0, 0.55, 0.20), emit=(1.0, 0.50, 0.15), strength=1.2)
    m["glass_l"] = mat("litho_glass", (0.70, 0.85, 1.0), rough=0.05, alpha=0.3)
    m["grey"] = mat("litho_grey", (0.55, 0.57, 0.62), rough=0.7)
    m["gold"] = mat("litho_gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["red"] = mat("litho_red", (0.90, 0.22, 0.18), emit=(0.90, 0.15, 0.10), strength=2.5)
    m["plinth"] = mat("litho_plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("litho_paper", (0.90, 0.88, 0.82), rough=0.85)
    m["gold_glow"] = mat("litho_gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.30), strength=2.5)
    m["ghost"] = mat("litho_ghost", (0.60, 0.75, 0.95), rough=0.2, alpha=0.18)
    return m


def chrome_bars():
    """The chrome intervals of the reticle: the gaps between the openings, across the plate."""
    edges = [-RET_HALF]
    for c in OPENINGS:
        edges += [c - OPEN_W / 2, c + OPEN_W / 2]
    edges.append(RET_HALF)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


def frame(root, m):
    """The stage base and the two columns and beam that hold the source, behind the cut plane."""
    g = empty("frame", root)
    box("stage_base", (-260, -150, -190), (260, -40, 0), m["dark_steel"], g)
    box("column_l", (-300, -40, -200), (-270, 900, -170), m["steel"], g)
    box("column_r", (270, -40, -200), (300, 900, -170), m["steel"], g)
    box("top_beam", (-300, 880, -200), (300, 900, -170), m["steel"], g)
    return g


def source(root, m, on=None):
    """The source housing and its light plate. `on` are the intervals the plate glows."""
    g = empty("source", root)
    box("source_housing", (-220, 792, -190), (220, 880, 0), m["steel"], g)
    glow = empty("source_glow", g)
    box("source_plate", (-200, SRC_GLOW[0], -180), (200, SRC_GLOW[1], 0), m["light"], glow)
    if on is not None:
        show(glow, on)
    return g


def reticle(root, m):
    """The reticle: a quartz plate with chrome bars on top, between the openings. It moves in x by
    keys on this group (see scan_keys)."""
    g = empty("reticle", root)
    box("reticle_quartz", (-RET_HALF, RET_Y - 10, -130), (RET_HALF, RET_Y + 10, 0), m["quartz"], g)
    for x0, x1 in chrome_bars():
        box(f"chrome_{x0:+.0f}", (x0, RET_Y + 10, -130), (x1, RET_Y + 22, 0), m["chrome"], g)
    return g


def lens(root, m, slit_on=None):
    """The projection lens: a half-cut barrel with five glass elements. The slit under it glows
    while a field is exposed (`slit_on` intervals)."""
    g = empty("lens", root)
    cut(shell("barrel", 0, 0, LENS_R, LENS_Y0, LENS_Y1, 14, m["steel"], g), 0.0)
    for k, y in enumerate((220, 300, 380, 460, 540)):
        cut(disc(f"element{k}", (0, y, 0), LENS_R - 14, 10, m["glass_l"], g, 48), 0.0)
    slit = empty("slit", g)
    box("slit_m", (-14, LENS_Y0 - 16, -40), (14, LENS_Y0 - 2, 0), m["light"], slit)
    if slit_on is not None:
        show(slit, slit_on)
    return g


def wafer(root, m):
    """The wafer and its chuck: substrate, film and resist cut at z = 0, an alignment mark, and
    one pink (exposed) and one cyan (developed) tile per field on the row. Returns the group and
    {field index: (pink tile, cyan tile)}; the tiles are switched by the scene."""
    g = empty("wafer", root)
    cut(disc("chuck", (0, -20, 0), 175, 40, m["dark_steel"], g), 0.0)
    cut(disc("substrate", (0, SUB_T / 2, 0), WR, SUB_T, m["silicon"], g), 0.0)
    cut(disc("film", (0, SUB_T + FILM_T / 2, 0), WR, FILM_T, m["film"], g), 0.0)
    cut(disc("resist", (0, SUB_T + FILM_T + RES_T / 2, 0), WR, RES_T, m["purple"], g), 0.0)
    mark = empty("mark", g)
    box("mark_x", (MARK_X - 7, RES_TOP, -1.5), (MARK_X + 7, RES_TOP + 1.5, 0), m["steel"], mark)
    box("mark_z", (MARK_X - 1.5, RES_TOP, -7), (MARK_X + 1.5, RES_TOP + 1.5, 0), m["steel"], mark)
    tiles = {}
    for k in range(FIELDS):
        c = field_x(k)
        pink = empty(f"field{k}_exp", g)
        box(f"field{k}_exp_m", (c - 13, RES_TOP, -26), (c + 13, RES_TOP + 1.5, 0), m["exposed"], pink)
        cy = empty(f"field{k}_dev", g)
        box(f"field{k}_dev_m", (c - 13, RES_TOP, -26), (c + 13, RES_TOP + 1.5, 0), m["cyan"], cy)
        tiles[k] = (pink, cy)
    return g, tiles


def field_x(k):
    """The centre of field k on the row, in wafer coordinates."""
    return -120.0 + FIELD_PITCH * k


def sensor(root, m, beam_on):
    """The alignment sensor beside the lens; its green beam reads the mark on the wafer."""
    g = empty("sensor", root)
    box("sensor_body", (SENSOR_X - 38, 230, -60), (SENSOR_X + 38, 292, 0), m["steel"], g)
    box("sensor_face", (SENSOR_X - 32, 226, -50), (SENSOR_X + 32, 230, 0), m["sensor"], g)
    beam = empty("sensor_beam", g)
    tube("beam_m", (SENSOR_X - 2, 226, -6), (MARK_X, RES_TOP + 2, -6), 3, m["sensor"], beam, verts=8)
    show(beam, beam_on)
    return g


def plan(first_f, per, n):
    """Windows for n fields, `per` frames each: scan for the first 60%, hold 20%, reset 20%.
    Returns [(f0, f1, f2, f3)] with f1 the end of the scan."""
    out = []
    for k in range(n):
        f0 = round(first_f + per * k)
        out.append((f0, round(f0 + 0.6 * per), round(f0 + 0.8 * per), round(f0 + per)))
    return out


def scan_keys(wg, ret, windows, k0=0):
    """Scan the fields in `windows` (from field k0 on). For each: the wafer slides one field width
    under the slit (x from X_START - k*pitch down by a pitch), and the reticle slides 4x that the
    other way; the reticle then rests and returns to 0 before the next window."""
    for i, (f0, f1, f2, f3) in enumerate(windows):
        x0 = X_START - (k0 + i) * FIELD_PITCH
        key(wg, f0, "location", P(x0, 0, 0), linear=True)
        key(wg, f1, "location", P(x0 - FIELD_PITCH, 0, 0), linear=True)
        key(ret, f0, "location", P(0, 0, 0), linear=True)
        key(ret, f1, "location", P(4 * FIELD_PITCH, 0, 0), linear=True)
        key(ret, f2, "location", P(4 * FIELD_PITCH, 0, 0), linear=True)
        key(ret, f3, "location", P(0, 0, 0), linear=True)


def rays(root, m, b, u0, u1, path_of, xs=OPENINGS, n=3, life=40):
    """Light through each opening: `n` blobs per opening, launched in beat b between u0 and u1
    and flying path_of(x) (a poly polyline from the source to where the light stops)."""
    for x in xs:
        run(root, f"ray{x:+.0f}_", n, path_of(x), 5, m["light"], b, u0, u1, life)


def light_path_to_reticle(x):
    return [(x, SRC_GLOW[0], RAY_Z), (x, RET_Y - 10, RAY_Z)]


def light_path_to_wafer(x):
    return [(x, SRC_GLOW[0], RAY_Z), (x, RET_Y - 10, RAY_Z), (x / 4.0, RES_TOP + 2, RAY_Z)]


def tag_on_wafer(text, x, parent, intervals, z=20):
    """A tag on the wafer's local coordinates (x along the row, y up from the wafer top)."""
    return label(text, (x, RES_TOP + 40, z), parent, intervals)
