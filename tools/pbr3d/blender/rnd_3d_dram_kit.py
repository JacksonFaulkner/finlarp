"""3D DRAM as reusable Blender pieces for the R&D 3D DRAM pictures (overview, zooms a-e, sections
1-9). Same template as rnd_hbf_kit.py and the SAND pages (docs/diagram-pages.md): units are
schematic millimetres, Y up, everything cut at a z plane (normally z = 0) with the camera on +z.
Sizes are schematic, drawn big for pbr3d's 40-unit near plane: the feature size F is FS = 200.

Builders (each takes an origin o = (x, y, z); z is the cut plane, normally 0):

  planar_cell     today's 6F2 1T1C cell: a buried-channel transistor lying flat in the silicon
                  (drain n+, buried word line in a trench, source n+, a passing word line in the
                  isolation), the bit line behind on its contact, a storage-node contact and a tall
                  cylinder capacitor on top. Tile 3F (x) by 2F (z), the surface at y = o.y.
  planar_array    nx by nz planar cells (front row cut), static geometry merged.
  vct_cell        the 4F2 vertical-channel-transistor cell: buried bit line (along x) at the
                  bottom, an n+ drain, a vertical p-type silicon pillar (the channel), an n+ source
                  on top, gate oxide round the pillar, the word line (along z) wrapped round it,
                  a landing pad and the capacitor on top. Tile 2F by 2F. Body overlay (holes) for
                  the floating-body story. The cell's floor (bottom of its base oxide) is o.y - 120.
  vct_array       nx by nz VCT cells at pitch 2F: one word line per column i (along z), one
                  buried bit line per row j (along x), front row j = 0 cut, merged.
  periphery       the CMOS periphery layer: silicon with transistors, sense-amp and decoder
                  blocks, metal wiring, and the lower half of the hybrid bond (Cu pads in oxide).
                  Its top (the bond face) is at o.y.
  bonded_die      cell-over-periphery: periphery below, a vct_array on a liftable group above with
                  its own Cu pads, and a glowing bond line between (wafer-to-wafer hybrid bond).
  wafer           a wafer disc with a die grid (kind "cell" or "peri") for wafer-to-wafer scenes.
  stacked_3d      stacked 3D DRAM: n layers of sideways 1T1C cells. Per layer and column: a
                  lateral transistor (drain n+, body under a gate-all-around word line running
                  along z, source n+) and a capacitor lying along x; vertical bit lines run up
                  through the stack at x = o.x; isolation slabs between layers. Each layer is its
                  own group so layers can be pulled apart. Mirrored cells on both sides of the bit
                  line by default; optional word-line staircase at the back.
  helpers         footprint (an F-grid tile), beads (charge along a path), vt_gauge (an Id-Vg
                  curve whose live copy slides left as the threshold drops), on() (switch an
                  overlay on), lift_layers(), join().

Every overlay (lit word line, lit bit line, charge, holes, body glow, bond line, ...) is built
hidden: call on(h.wl_on[i], intervals) for the beats it should show. Groups are empties at the
origin while building, so cut faces stay at the cut plane; move only the group empties.
Material keys (mats(m) adds them, all named "d3_*" so they do not collide with older kits):
  si body nplus sti ild gox wl wl_on bl bl_on nitride contact sn diel plate charge hole
  body_glow peri_si sa sa_on dec dec_on metal cu bond tile tile_grid tile_edge tile_edge2 e
  wall axis curve_ref curve wafer die_cell die_peri
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import P, ball, box, cut, disc, empty, key, mat, show, tube, _smooth  # noqa: E402
from poly_overview import run  # noqa: E402
from power_grid_detail import finish as _finish_step  # noqa: E402


def finish(name, page="rnd_3d_dram", step=2):
    """Save the .blend and export the GLB sampled every `step` frames (halves the animation data;
    pbr3d interpolates between samples). Use this instead of sand_zooms.finish."""
    _finish_step(name, page=page, step=step)

FS = 200.0  # the feature size F, in scene units

# ---- planar cell (relative to its origin) ----
PL_SI = 600.0  # silicon depth under the surface
PL_TR = 380.0  # trench depth of the buried word line
PL_CAP0 = 360.0  # capacitor base (top of the landing pad)
PL_CAP_H = 1800.0
PL_CAP_R = 125.0
PL_SN_X = 45.0  # storage node / capacitor axis
PL_BLC_X = -235.0  # bit-line contact
PL_BL_Y = (200.0, 290.0)
PL_BL_Z = (-190.0, -110.0)

# ---- VCT cell (relative) ----
V_BASE = 120.0  # base oxide under the bit line
V_BL = (0.0, 110.0)
V_DRAIN = (110.0, 210.0)
V_BODY = (210.0, 590.0)
V_SRC = (590.0, 690.0)
V_GATE = (250.0, 550.0)
V_PAD = (690.0, 740.0)
V_CAP0 = 740.0
V_CAP_H = 1100.0
V_CAP_R = 150.0
V_PW = 70.0  # pillar half width
V_OX = 88.0  # gate-oxide outer half width
V_WL = 160.0  # word-line outer half width (x)
V_BLW = 75.0  # bit-line half width (z)
V_PITCH = 2 * FS

# ---- periphery (relative to its top face) ----
PE_BOND = 60.0  # bond oxide thickness
PE_ILD = 300.0  # wiring layers
PE_SI = 520.0  # silicon below the devices
PE_T = PE_BOND + PE_ILD + PE_SI

# ---- stacked 3D DRAM (relative) ----
S_LP = 260.0  # layer pitch
S_ZP = 420.0  # column pitch (z)
S_CAPL = 1000.0  # lateral capacitor length
S_CAP_R = 100.0
S_X = (60.0, 170.0, 350.0, 460.0)  # drain from, body from, source from, capacitor from
S_CH = (100.0, 160.0)  # channel (silicon strip) y within the layer
S_BLW = 60.0
S_W = S_X[3] + S_CAPL + 40.0  # half width of the block


def stacked_top(n):
    return n * S_LP + 25.0


# ---- materials ------------------------------------------------------------------------------


def mats(m):
    m["si"] = mat("d3_si", (0.36, 0.40, 0.48), rough=0.8)
    m["body"] = mat("d3_body", (0.66, 0.54, 0.36), rough=0.6)
    m["nplus"] = mat("d3_nplus", (0.30, 0.48, 0.92), rough=0.55)
    m["sti"] = mat("d3_sti", (0.76, 0.80, 0.86), rough=0.6)
    m["ild"] = mat("d3_ild", (0.20, 0.22, 0.27), rough=0.7)
    m["gox"] = mat("d3_gox", (0.98, 0.88, 0.40), rough=0.4)
    m["wl"] = mat("d3_wl", (0.66, 0.30, 0.44), metal=0.4, rough=0.4)
    m["wl_on"] = mat("d3_wl_on", (1.0, 0.45, 0.62), emit=(1.0, 0.40, 0.60), strength=2.6)
    m["bl"] = mat("d3_bl", (0.20, 0.62, 0.78), metal=0.5, rough=0.3)
    m["bl_on"] = mat("d3_bl_on", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.6)
    m["nitride"] = mat("d3_nitride", (0.52, 0.66, 0.56), rough=0.5)
    m["contact"] = mat("d3_contact", (0.70, 0.72, 0.78), metal=0.9, rough=0.3)
    m["sn"] = mat("d3_sn", (0.82, 0.84, 0.88), metal=0.8, rough=0.25)
    m["diel"] = mat("d3_diel", (0.90, 0.80, 0.50), rough=0.4)
    m["plate"] = mat("d3_plate", (0.40, 0.43, 0.50), metal=0.5, rough=0.4)
    m["charge"] = mat("d3_charge", (1.0, 0.55, 0.15), emit=(1.0, 0.50, 0.10), strength=2.6)
    m["hole"] = mat("d3_hole", (1.0, 0.30, 0.50), emit=(1.0, 0.25, 0.45), strength=3.5)
    m["body_glow"] = mat("d3_body_glow", (0.85, 0.22, 0.32), emit=(0.85, 0.18, 0.30), strength=1.3)
    m["peri_si"] = mat("d3_peri_si", (0.30, 0.31, 0.37), rough=0.8)
    m["sa"] = mat("d3_sa", (0.50, 0.32, 0.82), rough=0.5)
    m["sa_on"] = mat("d3_sa_on", (0.65, 0.40, 1.0), emit=(0.62, 0.36, 1.0), strength=2.6)
    m["dec"] = mat("d3_dec", (0.24, 0.62, 0.44), rough=0.5)
    m["dec_on"] = mat("d3_dec_on", (0.35, 0.95, 0.55), emit=(0.32, 0.92, 0.50), strength=2.6)
    m["metal"] = mat("d3_metal", (0.85, 0.55, 0.32), metal=0.9, rough=0.3)
    m["cu"] = mat("d3_cu", (0.96, 0.62, 0.36), metal=1.0, rough=0.22)
    m["bond"] = mat("d3_bond", (0.75, 1.0, 0.95), emit=(0.6, 1.0, 0.9), strength=3.0)
    m["tile"] = mat("d3_tile", (0.12, 0.13, 0.16), rough=0.8)
    m["tile_grid"] = mat("d3_tile_grid", (0.50, 0.53, 0.60), rough=0.6)
    m["tile_edge"] = mat("d3_tile_edge", (1.0, 0.78, 0.32), emit=(1.0, 0.72, 0.25), strength=2.6)
    m["tile_edge2"] = mat("d3_tile_edge2", (0.40, 1.0, 0.75), emit=(0.35, 1.0, 0.70), strength=2.6)
    m["e"] = mat("d3_bead", (1.0, 0.92, 0.35), emit=(1.0, 0.90, 0.30), strength=3.2)
    m["wall"] = mat("d3_wall", (1.0, 0.32, 0.25), emit=(1.0, 0.28, 0.20), strength=1.6)
    m["axis"] = mat("d3_axis", (0.88, 0.90, 0.94), emit=(0.85, 0.88, 0.92), strength=0.8)
    m["curve_ref"] = mat("d3_curve_ref", (0.48, 0.52, 0.62), rough=0.5)
    m["curve"] = mat("d3_curve", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.0)
    m["wafer"] = mat("d3_wafer", (0.70, 0.72, 0.78), metal=0.7, rough=0.25)
    m["die_cell"] = mat("d3_die_cell", (0.20, 0.58, 0.62), rough=0.45)
    m["die_peri"] = mat("d3_die_peri", (0.45, 0.32, 0.75), rough=0.45)
    return m


# ---- small helpers ------------------------------------------------------------------------


def on(obj, intervals):
    """Switch an overlay group on for `intervals` (they are built hidden)."""
    show(obj, list(intervals))
    return obj


def hidden(name, parent):
    """An empty that starts switched off (an overlay's switch)."""
    g = empty(name, parent)
    show(g, [])
    return g


def join(objs, name):
    """Merge meshes (same parent) into one object, to keep the GLB lean."""
    objs = [o for o in objs if o is not None]
    if len(objs) < 2:
        if objs:
            objs[0].name = name
        return objs[0] if objs else None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o


class Bin:
    """Collects static meshes to merge at the end."""

    def __init__(self):
        self.objs = []

    def add(self, o):
        self.objs.append(o)
        return o

    def merge(self, name):
        return join(self.objs, name)


def _front(cutp, oz, half, stagger=0.0):
    """Front z of a part centred on oz: the cut plane (+ stagger) when cut, else oz + half."""
    return oz + stagger if cutp else oz + half


def capacitor(parent, m, name, base, h, r, cutp=True, axis="y", sign=1, cut_z=0.0, bin_=None):
    """A cylinder storage capacitor, drawn as nested solids so the cut face shows the cup:
    top plate | dielectric | storage node (TiN) | dielectric | plate core. `base` is its foot on
    the axis; `axis` "y" stands it up, "x" lays it sideways (sign +1 grows to +x). Built under a
    pivot at the foot (scale the pivot to squeeze/stretch it). Returns (pivot, charge_overlay)."""
    pv = empty(f"{name}_pv", parent, P(*base))
    layers = [  # (radius fraction, start, end-from-top, material, cut stagger)
        (1.00, 0.0, 0.0, "plate", 0.0),
        (0.88, 0.0, 16.0, "diel", 1.5),
        (0.76, 0.0, 30.0, "sn", 3.0),
        (0.60, 14.0, 40.0, "diel", 4.5),
        (0.48, 26.0, 46.0, "plate", 6.0),
    ]
    parts = []

    def solid(nm, rf, a0, a1, mk, verts=24):
        if axis == "y":
            o = disc(nm, (0, (a0 + a1) / 2, 0), r * rf, a1 - a0, m[mk], pv, verts=verts)
        else:
            o = tube(nm, (sign * a0, 0, 0), (sign * a1, 0, 0), r * rf, m[mk], pv, verts=16 if verts > 16 else verts)
        return o

    if not cutp:
        layers = layers[:1]  # a whole capacitor only shows its outer plate
    for k, (rf, a0, dt, mk, st) in enumerate(layers):
        o = solid(f"{name}_{k}", rf, a0, h - dt, mk)
        if cutp:
            cut(o, cut_z - base[2] + st)
        else:
            _smooth(o)
        parts.append(o)
    if len(parts) > 1:
        join(parts, f"{name}_body")
    else:
        parts[0].name = f"{name}_body"
    ch = hidden(f"{name}_charge", pv)
    if not cutp:
        return pv, ch  # nothing inside to light: the charge switch is an empty
    o = solid(f"{name}_q", 0.78, 2.0, h - 28.0, "charge")
    o.parent = ch
    if cutp:
        cut(o, cut_z - base[2] + 3.7)
    return pv, ch


def footprint(parent, m, c, nx, nz, y, f=FS, name="tile", edge="tile_edge"):
    """An F-grid tile lying flat at height y, centred on (c[0], c[2]): nx by nz squares of side f,
    a dark plate, grey grid lines and a glowing border. Returns its group."""
    g = empty(name, parent)
    cx, cz = c[0], c[2]
    hx, hz = nx * f / 2, nz * f / 2
    objs = [box(f"{name}_plate", (cx - hx, y, cz - hz), (cx + hx, y + 10, cz + hz), m["tile"], g)]
    w = 7.0
    for i in range(1, nx):
        x = cx - hx + i * f
        objs.append(box(f"{name}_gx{i}", (x - w, y + 10, cz - hz), (x + w, y + 16, cz + hz), m["tile_grid"], g))
    for j in range(1, nz):
        z = cz - hz + j * f
        objs.append(box(f"{name}_gz{j}", (cx - hx, y + 10, z - w), (cx + hx, y + 16, z + w), m["tile_grid"], g))
    join(objs, f"{name}_grid")
    e = 14.0
    rim = [
        box(f"{name}_e0", (cx - hx - e, y, cz - hz - e), (cx + hx + e, y + 22, cz - hz + e), m[edge], g),
        box(f"{name}_e1", (cx - hx - e, y, cz + hz - e), (cx + hx + e, y + 22, cz + hz + e), m[edge], g),
        box(f"{name}_e2", (cx - hx - e, y, cz - hz - e), (cx - hx + e, y + 22, cz + hz + e), m[edge], g),
        box(f"{name}_e3", (cx + hx - e, y, cz - hz - e), (cx + hx + e, y + 22, cz + hz + e), m[edge], g),
    ]
    join(rim, f"{name}_rim")
    return g


def beads(parent, m, name, pts, n, b, u0, u1, life=60, size=22.0, mk="e"):
    """`n` glowing beads that each travel the absolute polyline `pts` in `life` frames, launched
    between fractions u0 and u1 of beat b (charge moving on a read or write)."""
    return run(parent, name, n, pts, size, m[mk], b, u0, u1, life)


class VtGauge:
    def __init__(self, g, live, knee):
        self.g = g
        self.live = live  # the bright curve's group: key its location x to shift it
        self.knee = knee  # absolute point of the live curve's knee (Vt), at build time


def vt_gauge(parent, m, o, w=600.0, h=480.0, name="vt"):
    """An Id-Vg plot standing in the x-y plane at o (its lower-left corner): axes, a dim reference
    curve and a bright live copy with a Vt tick, which `vt_shift` slides left (a lower threshold:
    the transistor turns on earlier and leaks when it should be off)."""
    ox, oy, oz = o
    g = empty(name, parent)
    ax = [
        box(f"{name}_ax", (ox, oy, oz - 8), (ox + w, oy + 10, oz + 8), m["axis"], g),
        box(f"{name}_ay", (ox, oy, oz - 8), (ox + 10, oy + h, oz + 8), m["axis"], g),
        box(f"{name}_bk", (ox, oy, oz - 30), (ox + w, oy + h, oz - 18), m["tile"], g),
    ]
    join(ax, f"{name}_axes")

    def curve(nm, mk, parent_, zoff, vt):
        pts = []
        for k in range(13):
            x = ox + 30 + (w - 60) * k / 12
            v = (x - (ox + vt)) / (0.08 * w)
            yy = oy + 20 + (h - 60) / (1 + math.exp(-v))
            pts.append((x, yy, oz + zoff))
        objs = [tube(f"{nm}{i}", a, b, 9, m[mk], parent_, verts=8) for i, (a, b) in enumerate(zip(pts, pts[1:]))]
        return join(objs, nm)

    vt = 0.58 * w
    curve(f"{name}_ref", "curve_ref", g, 0.0, vt)
    live = empty(f"{name}_live", g)
    curve(f"{name}_cv", "curve", live, 6.0, vt)
    box(f"{name}_tick", (ox + vt - 6, oy - 30, oz + 2), (ox + vt + 6, oy + 40, oz + 12), m["curve"], live)
    return VtGauge(g, live, (ox + vt, oy + 20 + (h - 60) / 2, oz))


def vt_shift(gauge, keys):
    """Keys for the live curve's shift: (frame, dx) pairs, dx negative = threshold drops."""
    for f, dx in keys:
        key(gauge.live, f, "location", P(dx, 0, 0))


# ---- planar 6F2 cell --------------------------------------------------------------------------


class PlanarCell:
    def __init__(self):
        self.g = None
        self.cap = None  # capacitor pivot at its foot: scale it to squeeze/stretch
        self.charge = None  # orange overlay inside the storage node (hidden)
        self.wl_on = None  # the buried word line lit (hidden)
        self.chan_on = None  # the U-shaped channel round the trench lit (hidden)
        self.bl_on = None  # the bit line lit (hidden)
        self.tile = None  # the 6F2 footprint tile (or None)
        self.pts = {}  # named absolute points for tags and paths
        self.read_path = []  # absolute polyline capacitor -> bit line, in front of the cut


def planar_cell(parent, m, o=(0.0, 0.0, 0.0), name="pc", cutp=True, tile=True, cap_h=PL_CAP_H,
                bl_span=None, wl_span=None, merge=True):
    """Today's 6F2 1T1C DRAM cell with a buried word line (BCAT). Tile x [-3F/2, 3F/2], z [-F, F]
    about o; silicon surface at o.y. `bl_span` (x0, x1) and `wl_span` (z0, z1) stretch the bit line
    and word lines beyond the tile (absolute), for arrays. Returns a PlanarCell."""
    ox, oy, oz = o
    h = PlanarCell()
    g = empty(name, parent)
    h.g = g
    st = Bin()

    def A(x, y, z):
        return (ox + x, oy + y, oz + z)

    hx, hz = 1.5 * FS, FS
    zf0 = _front(cutp, oz, hz)
    x0, x1 = (ox - hx, ox + hx)
    # silicon: substrate below the trenches, the active ridge, isolation (STI) behind and in front
    st.add(box(f"{name}_si", (x0, oy - PL_SI, oz - hz), (x1, oy - 450, zf0), m["si"], g))
    st.add(box(f"{name}_ridge", (x0, oy - 450, oz - 80), (x1, oy, _front(cutp, oz, 80)), m["si"], g))
    st.add(box(f"{name}_sti_b", (x0, oy - 450, oz - hz), (x1, oy - 2, oz - 80), m["sti"], g))
    if not cutp:
        st.add(box(f"{name}_sti_f", (x0, oy - 450, oz + 80), (x1, oy - 2, oz + hz), m["sti"], g))
    # isolation block for the passing word line at the right end of the tile
    st.add(box(f"{name}_sti_p", A(120, -400, -80), (ox + hx, oy + 1, _front(cutp, oz, 80, 0.8)), m["sti"], g))
    # n+ drain (bit-line side, reaching back under the bit-line contact) and source
    st.add(box(f"{name}_drain", (x0, oy - 130, oz - 180), (ox - 170, oy + 2, _front(cutp, oz, 80, 1.5)), m["nplus"], g))
    st.add(box(f"{name}_source", A(-30, -130, -80), (ox + 120, oy + 2, _front(cutp, oz, 80, 1.5)), m["nplus"], g))
    # buried word line: oxide-lined trench, metal at its bottom, nitride cap; runs along z
    wz0, wz1 = wl_span if wl_span else (oz - hz, oz + hz)
    wzf = oz if cutp else wz1
    for nm, xc, mk in ((f"{name}_wl", -100.0, "wl"), (f"{name}_pwl", 210.0, "wl")):
        st.add(box(f"{nm}_ox", (ox + xc - 70, oy - PL_TR, wz0), (ox + xc + 70, oy - 60, wzf + (1.5 if cutp else 0)), m["gox"], g))
        st.add(box(f"{nm}_m", (ox + xc - 55, oy - PL_TR + 15, wz0), (ox + xc + 55, oy - 140, wzf + (3.0 if cutp else 0)), m[mk], g))
        st.add(box(f"{nm}_cap", (ox + xc - 55, oy - 140, wz0), (ox + xc + 55, oy + 3, wzf + (3.0 if cutp else 0)), m["nitride"], g))
    h.wl_on = hidden(f"{name}_wl_on", g)
    box(f"{name}_wl_glow", (ox - 100 - 62, oy - PL_TR + 8, wz0), (ox - 100 + 62, oy - 130, wzf + (4.5 if cutp else 0)), m["wl_on"], h.wl_on)
    h.chan_on = hidden(f"{name}_chan_on", g)
    cz = oz + 4.5 if cutp else oz + 82
    for k, (lo, hi) in enumerate([((-190, -PL_TR - 22, 0), (-170, -120, 0)), ((-190, -PL_TR - 22, 0), (-10, -PL_TR, 0)),
                                  ((-30, -PL_TR - 22, 0), (-10, -120, 0))]):
        box(f"{name}_ch{k}", (ox + lo[0], oy + lo[1], cz - 30), (ox + hi[0], oy + hi[1], cz), m["bl_on"], h.chan_on)
    # bit line behind the cut plane on its contact, along x
    bx0, bx1 = bl_span if bl_span else (x0, x1)
    st.add(box(f"{name}_bl", (bx0, oy + PL_BL_Y[0], oz + PL_BL_Z[0]), (bx1, oy + PL_BL_Y[1], oz + PL_BL_Z[1]), m["bl"], g))
    st.add(tube(f"{name}_blc", A(PL_BLC_X, 1, -150), A(PL_BLC_X, PL_BL_Y[0] + 5, -150), 38, m["contact"], g, verts=12))
    h.bl_on = hidden(f"{name}_bl_on", g)
    box(f"{name}_bl_glow", (bx0, oy + PL_BL_Y[0] - 10, oz + PL_BL_Z[0] - 10), (bx1, oy + PL_BL_Y[1] + 10, oz + PL_BL_Z[1] + 10), m["bl_on"], h.bl_on)
    # storage-node contact and landing pad
    snc = tube(f"{name}_snc", A(PL_SN_X, 2, 0), A(PL_SN_X, PL_CAP0 - 30, 0), 42, m["contact"], g, verts=12)
    if cutp:
        cut(snc, oz + 2.0)
    st.add(snc)
    st.add(box(f"{name}_pad", A(PL_SN_X - 70, PL_CAP0 - 30, -70), (ox + PL_SN_X + 70, oy + PL_CAP0, _front(cutp, oz, 70, 1.0)), m["contact"], g))
    if merge:
        st.merge(f"{name}_static")
    h.cap, h.charge = capacitor(g, m, f"{name}_cap", A(PL_SN_X, PL_CAP0, 0), cap_h, PL_CAP_R, cutp, cut_z=oz)
    if tile:
        h.tile = footprint(g, m, (ox, 0, oz), 3, 2, oy + PL_CAP0 + cap_h + 160, name=f"{name}_tile")
    zt = oz + 10 if cutp else oz + hz + 10
    h.pts = {
        "cap": A(PL_SN_X + PL_CAP_R, PL_CAP0 + cap_h * 0.6, 0),
        "cap_top": A(PL_SN_X, PL_CAP0 + cap_h, 0),
        "wl": A(-100, -260, 0), "pwl": A(210, -260, 0),
        "drain": A(-260, -60, 0), "source": A(45, -60, 0),
        "bl": A(-hx, 245, -150), "blc": A(PL_BLC_X, 120, -150), "snc": A(PL_SN_X, 180, 0),
        "chan": A(-100, -PL_TR - 10, 0), "si": A(0, -520, 0),
        "tile": (ox + hx, oy + PL_CAP0 + cap_h + 170, oz),
    }
    h.read_path = [A(PL_SN_X, PL_CAP0 + cap_h * 0.5, zt - oz), A(PL_SN_X, 10, zt - oz), A(-30, -120, zt - oz),
                   A(-180, -PL_TR - 10, zt - oz), A(-190, -60, zt - oz), A(PL_BLC_X, 0, zt - oz),
                   A(PL_BLC_X, PL_BL_Y[1] + 30, zt - oz), A(-hx - 200, PL_BL_Y[1] + 30, zt - oz)]
    return h


class PlanarArray:
    def __init__(self):
        self.g = None
        self.cells = {}  # (i, j) -> PlanarCell; j = 0 is the cut front row
        self.caps = []  # every capacitor pivot


def planar_array(parent, m, o=(0.0, 0.0, 0.0), nx=3, nz=2, name="pa", cap_h=PL_CAP_H, tile_at=(1, 0)):
    """nx by nz planar cells, pitch 3F in x and 2F in z, front row (j = 0) cut at o.z. Only cell
    `tile_at` (or none) carries a footprint tile."""
    ox, oy, oz = o
    a = PlanarArray()
    a.g = empty(name, parent)
    for j in range(nz):
        for i in range(nx):
            x = ox + (i - (nx - 1) / 2) * 3 * FS
            z = oz - j * 2 * FS
            c = planar_cell(a.g, m, (x, oy, z), f"{name}{i}{j}", cutp=(j == 0), tile=(tile_at == (i, j)), cap_h=cap_h)
            a.cells[(i, j)] = c
            a.caps.append(c.cap)
    return a


# ---- VCT 4F2 cell ---------------------------------------------------------------------------


class VctCell:
    def __init__(self):
        self.g = None
        self.cap = None
        self.charge = None
        self.wl_on = None
        self.chan_on = None  # the pillar's faces next to the gate lit: the channel is on
        self.bl_on = None
        self.body = None  # dim red glow on the pillar body (hidden)
        self.holes = []  # hole groups, each hidden; show them one after another
        self.tile = None
        self.pts = {}
        self.read_path = []


def _vct_static(st, g, m, name, ox, oy, oz, cutp, body=True):
    """The pillar, its oxide, drain, source and landing pad (bit and word lines are separate)."""
    pw, gx = V_PW, V_OX

    def zf(half, s):
        return _front(cutp, oz, half, s)

    st.add(box(f"{name}_dr", (ox - pw, oy + V_DRAIN[0], oz - pw), (ox + pw, oy + V_DRAIN[1], zf(pw, 1.5)), m["nplus"], g))
    st.add(box(f"{name}_bd", (ox - pw, oy + V_BODY[0], oz - pw), (ox + pw, oy + V_BODY[1], zf(pw, 1.5)), m["body"], g))
    st.add(box(f"{name}_sr", (ox - pw, oy + V_SRC[0], oz - pw), (ox + pw, oy + V_SRC[1], zf(pw, 1.5)), m["nplus"], g))
    st.add(box(f"{name}_ox", (ox - gx, oy + V_GATE[0] - 20, oz - gx), (ox + gx, oy + V_GATE[1] + 20, zf(gx, 0.0)), m["gox"], g))
    st.add(box(f"{name}_pad", (ox - 110, oy + V_PAD[0], oz - 110), (ox + 110, oy + V_PAD[1], zf(110, 1.0)), m["contact"], g))


def vct_cell(parent, m, o=(0.0, 0.0, 0.0), name="vc", cutp=True, tile=True, cap_h=V_CAP_H, holes=8, merge=True):
    """One 4F2 VCT cell (see the module docstring). Bit line along x at the bottom, word line along
    z wrapped round the pillar, capacitor on top. Returns a VctCell."""
    ox, oy, oz = o
    h = VctCell()
    g = empty(name, parent)
    h.g = g
    st = Bin()
    hw = FS  # tile half width

    def A(x, y, z):
        return (ox + x, oy + y, oz + z)

    zb = _front(cutp, oz, hw)
    st.add(box(f"{name}_base", (ox - hw, oy - V_BASE, oz - hw), (ox + hw, oy + V_BL[0], zb), m["ild"], g))
    st.add(box(f"{name}_bl", (ox - hw, oy + V_BL[0], oz - V_BLW), (ox + hw, oy + V_BL[1], _front(cutp, oz, V_BLW)), m["bl"], g))
    _vct_static(st, g, m, name, ox, oy, oz, cutp)
    # the word line: two bars along z either side of the pillar, joined behind (and in front if
    # whole), so the gate wraps the pillar
    wy0, wy1 = oy + V_GATE[0], oy + V_GATE[1]
    for s in (-1, 1):
        lo, hi = sorted((ox + s * V_OX, ox + s * V_WL))
        st.add(box(f"{name}_wl{s}", (lo, wy0, oz - hw), (hi, wy1, zb), m["wl"], g))
    st.add(box(f"{name}_wlb", (ox - V_OX, wy0, oz - V_WL), (ox + V_OX, wy1, oz - V_OX), m["wl"], g))
    if not cutp:
        st.add(box(f"{name}_wlf", (ox - V_OX, wy0, oz + V_OX), (ox + V_OX, wy1, oz + V_WL), m["wl"], g))
    if merge:
        st.merge(f"{name}_static")
    _vct_overlays(h, g, m, name, ox, oy, oz, cutp, (oz - hw, zb), (ox - hw, ox + hw), holes)
    h.cap, h.charge = capacitor(g, m, f"{name}_cap", A(0, V_CAP0, 0), cap_h, V_CAP_R, cutp, cut_z=oz)
    if tile:
        h.tile = footprint(g, m, (ox, 0, oz), 2, 2, oy + V_CAP0 + cap_h + 160, name=f"{name}_tile", edge="tile_edge2")
    _vct_pts(h, ox, oy, oz, cutp, cap_h)
    return h


def _vct_overlays(h, g, m, name, ox, oy, oz, cutp, wl_z, bl_x, holes, wl=True, bl=True):
    wy0, wy1 = oy + V_GATE[0], oy + V_GATE[1]
    if wl:
        h.wl_on = hidden(f"{name}_wl_on", g)
        for s in (-1, 1):
            lo, hi = sorted((ox + s * (V_OX - 2), ox + s * (V_WL + 10)))
            box(f"{name}_wlg{s}", (lo, wy0 - 10, wl_z[0]), (hi, wy1 + 10, wl_z[1] + (4.5 if cutp else 10)), m["wl_on"], h.wl_on)
    if bl:
        h.bl_on = hidden(f"{name}_bl_on", g)
        box(f"{name}_blg", (bl_x[0], oy + V_BL[0] - 10, oz - V_BLW - 10), (bl_x[1], oy + V_BL[1] + 10, _front(cutp, oz, V_BLW + 10, 4.5)), m["bl_on"], h.bl_on)
    zf = oz + 4.5 if cutp else oz + V_PW + 4
    h.chan_on = hidden(f"{name}_chan_on", g)
    for s in (-1, 1):
        lo, hi = sorted((ox + s * (V_PW - 16), ox + s * (V_PW + 2)))
        box(f"{name}_chg{s}", (lo, oy + V_BODY[0] - 20, zf - 40), (hi, oy + V_BODY[1] + 20, zf), m["bl_on"], h.chan_on)
    h.body = hidden(f"{name}_body", g)
    box(f"{name}_bodyg", (ox - V_PW + 14, oy + V_BODY[0] + 6, zf - 40), (ox + V_PW - 14, oy + V_BODY[1] - 6, zf), m["body_glow"], h.body)
    h.holes = []
    for k in range(holes):
        col, row = k % 2, k // 2
        x = ox + (-26 if col == 0 else 26) + (8 if row % 2 else -8)
        y = oy + V_BODY[0] + 50 + row * 70
        hg = hidden(f"{name}_hole{k}", g)
        ball(f"{name}_h{k}", (x, y, zf + 18), 22, m["hole"], hg, segs=10)
        h.holes.append(hg)


def _vct_pts(h, ox, oy, oz, cutp, cap_h):
    def A(x, y, z):
        return (ox + x, oy + y, oz + z)

    zt = 12 if cutp else V_WL + 12
    h.pts = {
        "cap": A(V_CAP_R, V_CAP0 + cap_h * 0.6, 0), "cap_top": A(0, V_CAP0 + cap_h, 0),
        "pillar": A(V_PW, (V_BODY[0] + V_BODY[1]) / 2, 0), "body": A(0, (V_BODY[0] + V_BODY[1]) / 2, 0),
        "gate": A(V_WL, (V_GATE[0] + V_GATE[1]) / 2, 0), "gate_l": A(-V_WL, (V_GATE[0] + V_GATE[1]) / 2, 0),
        "gox": A(V_OX, V_GATE[1], 0), "drain": A(V_PW, (V_DRAIN[0] + V_DRAIN[1]) / 2, 0),
        "source": A(V_PW, (V_SRC[0] + V_SRC[1]) / 2, 0), "bl": A(FS, (V_BL[0] + V_BL[1]) / 2, 0),
        "pad": A(110, V_PAD[1], 0), "base": A(FS, -V_BASE / 2, 0),
        "tile": A(FS, V_CAP0 + cap_h + 170, 0),
    }
    h.read_path = [A(0, V_CAP0 + cap_h * 0.5, zt), A(0, V_PAD[0], zt), A(0, V_BL[1] - 20, zt),
                   A(-FS - 400, V_BL[1] - 20, zt)]


class VctArray:
    def __init__(self):
        self.g = None
        self.cells = {}  # (i, j) -> VctCell (no word/bit-line overlays per cell)
        self.wl_on = []  # word line i (column, along z) lit
        self.bl_on = []  # bit line j (row, along x) lit
        self.xs = []
        self.zs = []
        self.x0 = self.x1 = self.zb = 0.0
        self.top = 0.0


def vct_array(parent, m, o=(0.0, 0.0, 0.0), nx=4, nz=4, name="va", cap_h=V_CAP_H, holes_at=(), tile_at=None,
              base=True):
    """nx by nz VCT cells at pitch 2F about o (x centred, rows going back from z = o.z), front row
    cut. Word line i runs along z at column i, bit line j along x at row j. Cells listed in
    `holes_at` get hole overlays (front-row cells show them through the cut). Returns a VctArray."""
    ox, oy, oz = o
    a = VctArray()
    g = empty(name, parent)
    a.g = g
    xs = [ox + (i - (nx - 1) / 2) * V_PITCH for i in range(nx)]
    zs = [oz - j * V_PITCH for j in range(nz)]
    a.xs, a.zs = xs, zs
    x0, x1 = xs[0] - FS, xs[-1] + FS
    zb = zs[-1] - FS
    a.x0, a.x1, a.zb = x0, x1, zb
    a.top = oy + V_CAP0 + cap_h
    st = Bin()
    if base:
        st.add(box(f"{name}_base", (x0, oy - V_BASE, zb), (x1, oy + V_BL[0], oz), m["ild"], g))
    for j, z in enumerate(zs):
        c = j == 0
        st.add(box(f"{name}_bl{j}", (x0, oy + V_BL[0], z - V_BLW), (x1, oy + V_BL[1], z if c else z + V_BLW), m["bl"], g))
    wy0, wy1 = oy + V_GATE[0], oy + V_GATE[1]
    for i, x in enumerate(xs):
        for s in (-1, 1):
            lo, hi = sorted((x + s * V_OX, x + s * V_WL))
            st.add(box(f"{name}_wl{i}{s}", (lo, wy0, zb), (hi, wy1, oz), m["wl"], g))
        for j, z in enumerate(zs):
            # gate wrap pieces behind each pillar (and in front, except the cut row)
            st.add(box(f"{name}_wb{i}{j}", (x - V_OX, wy0, z - V_WL), (x + V_OX, wy1, z - V_OX), m["wl"], g))
            if j > 0:
                st.add(box(f"{name}_wf{i}{j}", (x - V_OX, wy0, z + V_OX), (x + V_OX, wy1, z + V_WL), m["wl"], g))
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            _vct_static(st, g, m, f"{name}c{i}{j}", x, oy, z, j == 0)
    st.merge(f"{name}_static")
    for i, x in enumerate(xs):
        e = hidden(f"{name}_wl_on{i}", g)
        for s in (-1, 1):
            lo, hi = sorted((x + s * (V_OX - 2), x + s * (V_WL + 10)))
            box(f"{name}_wlg{i}{s}", (lo, wy0 - 10, zb), (hi, wy1 + 10, oz + 4.5), m["wl_on"], e)
        a.wl_on.append(e)
    for j, z in enumerate(zs):
        e = hidden(f"{name}_bl_on{j}", g)
        box(f"{name}_blg{j}", (x0, oy + V_BL[0] - 10, z - V_BLW - 10), (x1, oy + V_BL[1] + 10, z + (4.5 if j == 0 else V_BLW + 10)), m["bl_on"], e)
        a.bl_on.append(e)
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            c = VctCell()
            c.g = g
            nm = f"{name}c{i}{j}"
            if (i, j) in holes_at:
                _vct_overlays(c, g, m, nm, x, oy, z, j == 0, (zb, oz), (x0, x1), 8, wl=False, bl=False)
            c.cap, c.charge = capacitor(g, m, f"{nm}_cap", (x, oy + V_CAP0, z), cap_h, V_CAP_R, j == 0, cut_z=oz)
            if tile_at == (i, j):
                c.tile = footprint(g, m, (x, 0, z), 2, 2, oy + V_CAP0 + cap_h + 160, name=f"{nm}_tile", edge="tile_edge2")
            _vct_pts(c, x, oy, z, j == 0, cap_h)
            a.cells[(i, j)] = c
    return a


# ---- periphery and the hybrid bond ---------------------------------------------------------


class Periphery:
    def __init__(self):
        self.g = None
        self.blocks = []  # (kind, x0, x1) of each block
        self.sa_on = []  # sense-amp block overlays (hidden)
        self.dec_on = []  # decoder block overlays (hidden)
        self.pads = []  # (x, z) of the bond pads
        self.pts = {}


def periphery(parent, m, o, x0, x1, zb, name="pe", blocks=None, pad_pitch=V_PITCH, pad_xs=None, pad_zs=None,
              bond_pads=True):
    """The CMOS periphery layer with its top (the bond face) at o.y, spanning x0..x1 and zb..o.z
    (front cut at o.z). From the bottom: silicon, device layer (transistors in sense-amp and
    decoder blocks), wiring (ILD with copper lines and vias) and the bond oxide with Cu pads.
    `blocks` lists (kind, f0, f1) as fractions of the width, kind "sa" or "dec". Pads sit at
    pad_xs x pad_zs (default: every pad_pitch). Returns a Periphery."""
    _, oy, oz = o
    p = Periphery()
    g = empty(name, parent)
    p.g = g
    st = Bin()
    y_dev = oy - PE_BOND - PE_ILD  # top of the silicon
    st.add(box(f"{name}_si", (x0, y_dev - PE_SI, zb), (x1, y_dev, oz), m["peri_si"], g))
    st.add(box(f"{name}_ild", (x0, y_dev, zb), (x1, oy - PE_BOND, oz), m["ild"], g))
    st.add(box(f"{name}_box", (x0, oy - PE_BOND, zb), (x1, oy, oz), m["sti"], g))
    blocks = blocks or [("dec", 0.02, 0.24), ("sa", 0.28, 0.72), ("dec", 0.76, 0.98)]
    W = x1 - x0
    for bi, (kind, f0, f1) in enumerate(blocks):
        bx0, bx1 = x0 + W * f0, x0 + W * f1
        p.blocks.append((kind, bx0, bx1))
        st.add(box(f"{name}_blk{bi}", (bx0, y_dev - 150, zb + 20), (bx1, y_dev - 1, oz + 0.8), m[kind], g))
        ov = hidden(f"{name}_{kind}_on{bi}", g)
        box(f"{name}_blkg{bi}", (bx0 - 6, y_dev - 156, zb + 14), (bx1 + 6, y_dev + 2, oz + 2.4), m[f"{kind}_on"], ov)
        (p.sa_on if kind == "sa" else p.dec_on).append(ov)
        # transistors in the block's front face: n+ wells in the silicon, gate oxide + gate above
        n = max(1, int((bx1 - bx0) // 180))
        for t in range(n):
            cx = bx0 + (bx1 - bx0) * (t + 0.5) / n
            for s in (-1, 1):
                st.add(box(f"{name}_sd{bi}{t}{s}", (cx + s * 55 - 30, y_dev - 60, oz - 120), (cx + s * 55 + 30, y_dev + 1, oz + 1.6), m["nplus"], g))
            st.add(box(f"{name}_go{bi}{t}", (cx - 28, y_dev, oz - 120), (cx + 28, y_dev + 10, oz + 1.6), m["gox"], g))
            st.add(box(f"{name}_gt{bi}{t}", (cx - 25, y_dev + 10, oz - 120), (cx + 25, y_dev + 70, oz + 1.6), m["wl"], g))
            st.add(box(f"{name}_ct{bi}{t}", (cx - 75, y_dev, oz - 40), (cx - 45, y_dev + 120, oz + 1.6), m["contact"], g))
    # wiring: three levels of copper lines along x with vias up to the pads
    for lv, (y0, y1) in enumerate(((y_dev + 120, y_dev + 150), (y_dev + 190, y_dev + 220), (y_dev + 255, y_dev + 285))):
        segs = 7 - lv * 2
        for s in range(segs):
            sx0 = x0 + W * (s + 0.12) / segs
            sx1 = x0 + W * (s + 0.88) / segs
            st.add(box(f"{name}_m{lv}{s}", (sx0, y0, zb + 30), (sx1, y1, oz + 1.6), m["metal"], g))
    xs = pad_xs if pad_xs is not None else [x0 + pad_pitch / 2 + k * pad_pitch for k in range(int(W // pad_pitch))]
    zs = pad_zs if pad_zs is not None else [oz - k * pad_pitch for k in range(int((oz - zb) // pad_pitch) + 1) if oz - k * pad_pitch - 50 > zb]
    if bond_pads:
        for xi, x in enumerate(xs):
            for zi, z in enumerate(zs):
                front = oz + 1.6 if zi == 0 and abs(z - oz) < 1 else z + 50
                st.add(box(f"{name}_pd{xi}{zi}", (x - 50, oy - PE_BOND, z - 50), (x + 50, oy + 2, front), m["cu"], g))
                if zi == 0:
                    st.add(box(f"{name}_vi{xi}", (x - 18, y_dev + 285, z - 18), (x + 18, oy - PE_BOND, min(front, z + 18)), m["metal"], g))
                p.pads.append((x, z))
    st.merge(f"{name}_static")
    p.pts = {"si": (x1, y_dev - PE_SI / 2, oz), "ild": (x1, (y_dev + oy - PE_BOND) / 2, oz), "bond": (x1, oy, oz),
             "dev": (x0 + W * 0.5, y_dev, oz), "top": (x1, oy, oz), "bottom": oy - PE_T}
    for kind, bx0, bx1 in p.blocks:
        p.pts.setdefault(kind, ((bx0 + bx1) / 2, y_dev - 80, oz))
    return p


class BondedDie:
    def __init__(self):
        self.g = None
        self.peri = None  # Periphery
        self.top = None  # the liftable group: the cell array and its own bond pads
        self.arr = None  # VctArray (inside top)
        self.line = None  # the glowing bond line (hidden), stays with the periphery
        self.pts = {}


def bonded_die(parent, m, o=(0.0, 0.0, 0.0), nx=4, nz=4, name="bd", margin=200.0, cap_h=V_CAP_H, holes_at=(),
               tile_at=None):
    """Cell over periphery, wafer-to-wafer: the periphery (top face at o.y) and, in the group
    `top`, a VCT array whose base oxide carries Cu pads facing down onto the periphery's pads. The
    array's cells start V_BASE above the bond. Lift `top` (key its location) to split the two
    wafers; switch `line` on at the moment they bond. Returns a BondedDie."""
    ox, oy, oz = o
    d = BondedDie()
    d.g = empty(name, parent)
    d.top = empty(f"{name}_top", d.g)
    ay = oy + V_BASE  # the array's own origin (bit-line bottom)
    d.arr = vct_array(d.top, m, (ox, ay, oz), nx, nz, f"{name}a", cap_h=cap_h, holes_at=holes_at, tile_at=tile_at,
                      base=True)
    a = d.arr
    x0, x1 = a.x0 - margin, a.x1 + margin
    pad_xs = [x + s * 100 for x in a.xs for s in (-1, 1)]
    pad_zs = list(a.zs)
    d.peri = periphery(d.g, m, (ox, oy, oz), x0, x1, a.zb, f"{name}p", pad_xs=pad_xs, pad_zs=pad_zs)
    # the array side's pads, in the array's base oxide, meeting the periphery pads at the bond
    st = Bin()
    for xi, x in enumerate(pad_xs):
        for zi, z in enumerate(pad_zs):
            front = oz + 1.6 if zi == 0 else z + 50
            st.add(box(f"{name}_tp{xi}{zi}", (x - 50, oy - 1, z - 50), (x + 50, oy + 60, front), m["cu"], d.top))
    for i, x in enumerate(a.xs):  # vias from the pads up to the bit line (front row only)
        st.add(box(f"{name}_tv{i}", (x - 118, oy + 60, oz - 18), (x - 82, ay, oz + 1.6), m["contact"], d.top))
    st.merge(f"{name}_tpads")
    d.line = hidden(f"{name}_line", d.g)
    box(f"{name}_bondl", (x0 - 10, oy - 7, a.zb - 10), (x1 + 10, oy + 7, oz + 6), m["bond"], d.line)
    d.pts = {"bond": (x1, oy, oz), "array": (a.x1, ay + 600, oz), "peri": d.peri.pts["ild"], "si": d.peri.pts["si"],
             "top": a.top, "bottom": oy - PE_T}
    return d


def lift(grp, keys, axis=1):
    """Location keys on a group: (frame, offset) along y (axis 1) or another poly axis."""
    for f, v in keys:
        off = [0.0, 0.0, 0.0]
        off[axis] = v
        key(grp, f, "location", P(*off))


def wafer(parent, m, c, r=900.0, t=40.0, kind="cell", die=150.0, name="wf", flip=False):
    """A wafer: a disc of radius r, thickness t, centred at c, with a die grid on its top face (on
    its bottom face if `flip`, the array wafer turned over for bonding). Not cut."""
    g = empty(name, parent)
    cx, cy, cz = c
    w = disc(f"{name}_disc", c, r, t, m["wafer"], g, verts=64)
    _smooth(w)
    dies = []
    n = int(r // die)
    yf = cy - t / 2 - 4 if flip else cy + t / 2
    for i in range(-n, n):
        for j in range(-n, n):
            x0, z0 = cx + i * die + 8, cz + j * die + 8
            if math.hypot(max(abs(x0 - cx), abs(x0 + die - 16 - cx)), max(abs(z0 - cz), abs(z0 + die - 16 - cz))) > r - 20:
                continue
            dies.append(box(f"{name}_d{i}_{j}", (x0, yf, z0), (x0 + die - 16, yf + 4, z0 + die - 16),
                            m["die_cell" if kind == "cell" else "die_peri"], g))
    join(dies, f"{name}_dies")
    return g


# ---- stacked 3D DRAM ------------------------------------------------------------------------


class Stacked:
    def __init__(self):
        self.g = None
        self.layers = []  # layer k's group (move it to pull layers apart)
        self.wl_on = []  # layer k's word lines lit (both sides), inside the layer group
        self.bl_on = []  # column j's vertical bit line lit, whole height (in g)
        self.charges = []  # charges[k][side] of the front column's capacitors (side 0: +x, 1: -x)
        self.caps = []  # caps[k][side] pivots, front column
        self.zs = []
        self.pts = {}
        self.top = 0.0


def stacked_3d(parent, m, o=(0.0, 0.0, 0.0), n=8, nz=3, name="sk", mirror=True, stair=False, cap_l=S_CAPL):
    """Stacked 3D DRAM: n layers of sideways 1T1C cells around vertical bit lines at x = o.x, nz
    columns going back from z = o.z (front column cut). Layer k spans y o.y + k*S_LP .. +S_LP.
    Returns a Stacked."""
    ox, oy, oz = o
    s = Stacked()
    s.g = empty(name, parent)
    zs = [oz - j * S_ZP for j in range(nz)]
    s.zs = zs
    zb = zs[-1] - S_ZP / 2
    sides = (1, -1) if mirror else (1,)
    W = S_X[3] + cap_l + 40.0
    xl = ox - W if mirror else ox - 120
    for k in range(n):
        yk = oy + k * S_LP
        lg = empty(f"{name}_L{k}", s.g)
        s.layers.append(lg)
        st = Bin()
        # isolation slab under the layer (oxide between layers)
        st.add(box(f"{name}_iso{k}", (xl, yk, zb), (ox + W, yk + 25, oz), m["sti"], lg))
        c0, c1 = yk + S_CH[0], yk + S_CH[1]
        for j, z in enumerate(zs):
            cutp = j == 0
            zf = (lambda half, stg=0.0: oz + stg) if cutp else (lambda half, stg=0.0, z=z: z + half)
            # bit-line segment through this layer
            st.add(box(f"{name}_bl{k}{j}", (ox - S_BLW, yk + 25, z - S_BLW), (ox + S_BLW, yk + S_LP + 25, zf(S_BLW)), m["bl"], lg))
            for sd in sides:
                def X(a, b):
                    return sorted((ox + sd * a, ox + sd * b))
                lo, hi = X(S_X[0], S_X[1])
                st.add(box(f"{name}_dr{k}{j}{sd}", (lo, c0, z - 80), (hi, c1, zf(80, 1.5)), m["nplus"], lg))
                lo, hi = X(S_X[1], S_X[2])
                st.add(box(f"{name}_bd{k}{j}{sd}", (lo, c0, z - 80), (hi, c1, zf(80, 1.5)), m["body"], lg))
                lo, hi = X(S_X[1] + 10, S_X[2] - 10)
                st.add(box(f"{name}_ox{k}{j}{sd}", (lo, c0 - 15, z - 95), (hi, c1 + 15, zf(95)), m["gox"], lg))
                lo, hi = X(S_X[2], S_X[3])
                st.add(box(f"{name}_sr{k}{j}{sd}", (lo, c0, z - 80), (hi, c1, zf(80, 1.5)), m["nplus"], lg))
            # isolation filler between the layer's strips, behind the body (keeps layers readable)
        for sd in sides:
            def X(a, b):
                return sorted((ox + sd * a, ox + sd * b))
            lo, hi = X(S_X[1] + 20, S_X[2] - 20)
            # word line: a bar above and below the channels, running along z the whole depth,
            # with side pieces between the columns (gate all around)
            st.add(box(f"{name}_wla{k}{sd}", (lo, c1 + 15, zb), (hi, c1 + 45, oz), m["wl"], lg))
            st.add(box(f"{name}_wlb{k}{sd}", (lo, c0 - 45, zb), (hi, c0 - 15, oz), m["wl"], lg))
            for j, z in enumerate(zs):
                st.add(box(f"{name}_wls{k}{j}{sd}", (lo, c0 - 45, z - S_ZP / 2 + 10), (hi, c1 + 45, z - 95), m["wl"], lg))
            if stair:
                ext = (n - k) * 140.0
                st.add(box(f"{name}_stp{k}{sd}", (lo, c0 - 45, zb - ext), (hi, c1 + 45, zb), m["wl"], lg))
                cx = (lo + hi) / 2
                st.add(tube(f"{name}_stc{k}{sd}", (cx, c1 + 45, zb - ext + 70), (cx, oy + n * S_LP + 120, zb - ext + 70), 22, m["contact"], lg, verts=10))
        st.merge(f"{name}_L{k}_static")
        wg = hidden(f"{name}_wl_on{k}", lg)
        for sd in sides:
            lo, hi = sorted((ox + sd * (S_X[1] + 14), ox + sd * (S_X[2] - 14)))
            box(f"{name}_wga{k}{sd}", (lo, c1 + 10, zb), (hi, c1 + 50, oz + 4.5), m["wl_on"], wg)
            box(f"{name}_wgb{k}{sd}", (lo, c0 - 50, zb), (hi, c0 - 10, oz + 4.5), m["wl_on"], wg)
        s.wl_on.append(wg)
        caps_k, ch_k, back = [], [], []
        for j, z in enumerate(zs):
            for si, sd in enumerate(sides):
                pv, ch = capacitor(lg, m, f"{name}_c{k}{j}{si}", (ox + sd * S_X[3], (c0 + c1) / 2, z), cap_l, S_CAP_R,
                                   j == 0, axis="x", sign=sd, cut_z=oz)
                if j == 0:
                    caps_k.append(pv)
                    ch_k.append(ch)
                else:
                    back.append(bpy.data.objects[f"{name}_c{k}{j}{si}_body"])
        join(back, f"{name}_L{k}_backcaps")
        s.caps.append(caps_k)
        s.charges.append(ch_k)
    top = oy + n * S_LP + 25
    s.top = top
    lg = empty(f"{name}_cap_layer", s.g)  # a last isolation slab on top
    box(f"{name}_iso_top", (xl, top - 25, zb), (ox + W, top, oz), m["sti"], lg)
    s.layers_top = lg
    for j, z in enumerate(zs):
        e = hidden(f"{name}_bl_on{j}", s.g)
        box(f"{name}_blg{j}", (ox - S_BLW - 10, oy + 25, z - S_BLW - 10), (ox + S_BLW + 10, top, z + (4.5 if j == 0 else S_BLW + 10)), m["bl_on"], e)
        s.bl_on.append(e)
    c_mid = (S_CH[0] + S_CH[1]) / 2
    s.pts = {
        "bl": (ox + S_BLW, top - S_LP / 2, oz), "wl": (ox + (S_X[1] + S_X[2]) / 2, oy + (n - 1) * S_LP + S_CH[1] + 45, oz),
        "cap": (ox + S_X[3] + cap_l * 0.6, oy + (n - 1) * S_LP + c_mid + S_CAP_R, oz),
        "iso": (ox + W, oy + 3 * S_LP + 12, oz), "layer": lambda k: (ox + W, oy + k * S_LP + c_mid, oz),
        "chan": lambda k: (ox + (S_X[1] + S_X[2]) / 2, oy + k * S_LP + c_mid, oz),
        "cap_k": lambda k: (ox + S_X[3] + cap_l * 0.5, oy + k * S_LP + c_mid, oz),
        "right": ox + W, "left": xl, "back": zb,
    }
    return s


def stack_read_path(s, o, k, side=1, z=12.0):
    """A bead path from the front capacitor of layer k (side +1/-1) through its transistor into
    the vertical bit line and down to the bottom of the stack."""
    ox, oy, oz = o
    c = oy + k * S_LP + (S_CH[0] + S_CH[1]) / 2
    return [(ox + side * (S_X[3] + 500), c, oz + z), (ox + side * S_X[0], c, oz + z), (ox, c, oz + z), (ox, oy - 60, oz + z)]


def lift_layers(s, keys, step):
    """Layer k rises by amount * step * k over `keys` [(frame, amount)]: pulls the stack apart."""
    for k, lg in enumerate(s.layers):
        for f, a in keys:
            key(lg, f, "location", P(0, a * step * k, 0))
    for f, a in keys:
        key(s.layers_top, f, "location", P(0, a * step * len(s.layers), 0))
