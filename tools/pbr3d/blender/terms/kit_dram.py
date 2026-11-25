"""Memory-DRAM kit for the Terms-tab overviews (terms/trm_*.py). Shared by every DRAM term.

Scene units are the POWER pages' millimetres-ish (Y up, board top at y = 0), built with the
term_common / power_vrm_detail helpers. Every part takes the materials dict m and a parent.

API
  mats(m)
      Adds the dram_* materials (cell capacitor, wordline, bitline, sense amp, row buffer, and the
      glow variants). Call once per scene, after C.setup.
  bank(m, parent, name, x0, x1, z0, z1, rows=8, cols=12, y0=0.6)
      A cut-open DRAM bank on the bench: a grid of cell pillars (1T1C), wordlines along x (one per
      row), bitlines along z (one per column), a sense-amp strip and a row buffer at the z1 edge.
      Returns dict:
        g        group of the whole bank (use present()/show() to bring it in)
        wl       list of (plain, glow) groups, one pair per row
        sa_on    glow group over the sense-amp strip
        rb_on    glow group over the row buffer
        bl_hi    glow group over all bitlines, bitlines at full swing (show it with bl_show)
        bl_eq    glow group over all bitlines, bitlines equalized to half (show it with bl_show)
        cols     column count
        pts      dict: top, cell(r, c), wl(r), bl(c), sa(c), rb(c), io, row_z(r), col_x(c)
  row_open(bk, row, spans)
      Show row `row`'s wordline glow, the sense amps and the row buffer during each (f0, f1) frame
      span. Use F(beat, u) for the spans.
  charge_share(m, bk, row, beat, u0, u1)
      Beads from each cell in `row` up onto its bitline and down into the sense amp (ACTIVATE).
  write_back(m, bk, row, beat, u0, u1)
      Beads from the row buffer back down into each cell of `row` (PRECHARGE).
  io_flow(m, bk, cols, beat, u0, u1)
      Beads from the row buffer out to the bank's I/O edge, one per column in `cols` (READ/WRITE).
  bl_show(bk, key, spans)
      Show a bitline state group, key "hi" or "eq", during the (f0, f1) spans.
  fill(m, parent, name, x0, x1, y, z, beat, u0, u1, until_beat, n=10, mt="dram_timer")
      A bar that fills from left to right in n blocks during beat/u0..u1, then stays full until the
      end of `until_beat`. Returns the group (a timer or timing bar).
  cmd_strip(m, parent, name, x0, x1, z, y=0.6)
      A thin plate for a command timeline on the bench (the base line for fill() bars).
  tick(m, parent, name, x, z, y=0.6)
      A small upright marker on a timeline (a command issue point).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import bx, join, mat, run  # noqa: E402


def mats(m):
    m["dram_cap"] = mat("dram_cap", (0.80, 0.70, 0.52), metal=0.0, rough=0.6)
    m["dram_sub"] = mat("dram_sub", (0.16, 0.17, 0.20), metal=0.4, rough=0.45)
    m["dram_wl"] = mat("dram_wl", (0.40, 0.46, 0.60), metal=0.6, rough=0.35)
    m["dram_wl_on"] = mat("dram_wl_on", (1.0, 0.62, 0.20), emit=(1.0, 0.55, 0.15), strength=3.0)
    m["dram_bl"] = mat("dram_bl", (0.70, 0.74, 0.80), metal=0.9, rough=0.25)
    m["dram_bl_hi"] = mat("dram_bl_hi", (1.0, 0.42, 0.20), emit=(1.0, 0.36, 0.14), strength=2.5)
    m["dram_bl_eq"] = mat("dram_bl_eq", (0.35, 0.72, 1.0), emit=(0.30, 0.66, 1.0), strength=2.5)
    m["dram_sa"] = mat("dram_sa", (0.30, 0.34, 0.42), metal=0.5, rough=0.35)
    m["dram_sa_on"] = mat("dram_sa_on", (1.0, 0.92, 0.70), emit=(1.0, 0.90, 0.65), strength=2.5)
    m["dram_rb"] = mat("dram_rb", (0.24, 0.30, 0.36), metal=0.4, rough=0.4)
    m["dram_rb_on"] = mat("dram_rb_on", (0.45, 0.95, 1.0), emit=(0.40, 0.90, 1.0), strength=2.5)
    m["dram_bead"] = mat("dram_bead", (0.45, 0.90, 1.0), emit=(0.40, 0.86, 1.0), strength=3.5)
    m["dram_bead_w"] = mat("dram_bead_w", (1.0, 0.95, 0.80), emit=(1.0, 0.92, 0.75), strength=3.5)
    m["dram_timer"] = mat("dram_timer", (0.85, 0.86, 0.90), metal=0.6, rough=0.3)
    m["dram_tick"] = mat("dram_tick", (0.95, 0.95, 0.92), rough=0.5)
    return m


def bank(m, parent, name, x0, x1, z0, z1, rows=8, cols=12, y0=0.6):
    g = empty(name, parent)
    px = (x1 - x0) / cols
    pz = (z1 - z0) / rows
    zsa = z1 + 2.5  # sense-amp strip, one block per column
    zrb = z1 + 7.0  # row buffer strip, one full-row block
    ybl = y0 + 10.0  # bitline height
    xc = lambda c: x0 + px * (c + 0.5)  # noqa: E731
    zr = lambda r: z0 + pz * (r + 0.5)  # noqa: E731

    bx(f"{name}_sub", (x0 - 3.0, y0 - 0.6, z0 - 3.0), (x1 + 3.0, y0 + 0.4, zrb + 3.0), m["dram_sub"], g)
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append(bx(f"{name}_c{r}_{c}", (xc(c) - 0.7, y0 + 1.0, zr(r) - 0.7),
                            (xc(c) + 0.7, y0 + 8.0, zr(r) + 0.7), m["dram_cap"], g))
    join(cells, f"{name}_cells")

    wl = []
    for r in range(rows):
        plain = bx(f"{name}_wl{r}", (x0 - 1.0, y0 + 8.6, zr(r) - 0.4), (x1 + 1.0, y0 + 9.2, zr(r) + 0.4), m["dram_wl"], g)
        glow = bx(f"{name}_wlg{r}", (x0 - 1.0, y0 + 8.6, zr(r) - 0.45), (x1 + 1.0, y0 + 9.25, zr(r) + 0.45), m["dram_wl_on"], g)
        show(glow, [])
        wl.append((plain, glow))

    bl_bars, bl_hi, bl_eq = [], [], []
    for c in range(cols):
        bl_bars.append(bx(f"{name}_bl{c}", (xc(c) - 0.3, ybl, z0 - 1.0), (xc(c) + 0.3, ybl + 0.6, zsa + 2.0), m["dram_bl"], g))
        bl_hi.append(bx(f"{name}_blh{c}", (xc(c) - 0.4, ybl - 0.05, z0 - 1.0), (xc(c) + 0.4, ybl + 0.7, zsa + 2.0), m["dram_bl_hi"], g))
        bl_eq.append(bx(f"{name}_ble{c}", (xc(c) - 0.4, ybl - 0.05, z0 - 1.0), (xc(c) + 0.4, ybl + 0.7, zsa + 2.0), m["dram_bl_eq"], g))
    join(bl_bars, f"{name}_bl")
    hi_g = join(bl_hi, f"{name}_bl_hi")
    eq_g = join(bl_eq, f"{name}_bl_eq")
    show(hi_g, [])
    show(eq_g, [])

    sa_plain, sa_glow = [], []
    for c in range(cols):
        sa_plain.append(bx(f"{name}_sa{c}", (xc(c) - 0.9, y0, zsa), (xc(c) + 0.9, y0 + 3.0, zsa + 2.0), m["dram_sa"], g))
        sa_glow.append(bx(f"{name}_sag{c}", (xc(c) - 0.95, y0 - 0.05, zsa - 0.05), (xc(c) + 0.95, y0 + 3.05, zsa + 2.05), m["dram_sa_on"], g))
    join(sa_plain, f"{name}_sa")
    sa_on = join(sa_glow, f"{name}_sa_on")
    show(sa_on, [])

    bx(f"{name}_rb", (x0, y0, zrb - 1.0), (x1, y0 + 2.6, zrb + 1.0), m["dram_rb"], g)
    rb_on = bx(f"{name}_rb_on", (x0 + 0.4, y0 + 0.2, zrb - 1.2), (x1 - 0.4, y0 + 2.8, zrb + 1.2), m["dram_rb_on"], g)
    show(rb_on, [])

    pts = {
        "top": ((x0 + x1) / 2, y0 + 9.2, (z0 + z1) / 2),
        "cell": lambda r, c: (xc(c), y0 + 8.0, zr(r)),
        "wl": lambda r: (x1 + 1.0, y0 + 8.9, zr(r)),
        "bl": lambda c: (xc(c), ybl + 0.6, z0 - 1.0 + (zsa - z0) / 2),
        "sa": lambda c: (xc(c), y0 + 1.5, zsa + 1.0),
        "rb": lambda c: (xc(c), y0 + 1.2, zrb),
        "io": (x1 + 12.0, y0 + 1.5, zrb),
        "row_z": zr,
        "col_x": xc,
    }
    return {"g": g, "wl": wl, "sa_on": sa_on, "rb_on": rb_on, "bl_hi": hi_g, "bl_eq": eq_g, "pts": pts,
            "cols": cols}


def row_open(bk, row, spans):
    plain, glow = bk["wl"][row]
    show(glow, spans)
    show(bk["sa_on"], spans)
    show(bk["rb_on"], spans)


def _beads(m, parent, name, paths, mt, beat, u0, u1, life=40, n=3, size=0.7):
    for k, p in enumerate(paths):
        run(parent, f"{name}{k}", p, n, size, mt, [beat], u0, u1, life)


def charge_share(m, bk, row, beat, u0, u1):
    """Cell charge moves onto the bitline and into the sense amp (ACTIVATE)."""
    pts = bk["pts"]
    g = empty(f"dram_share{row}_{beat}", bk["g"])
    paths = []
    for c in range(bk["cols"]):
        cx, cy, cz = pts["cell"](row, c)
        _, bly, blz = pts["bl"](c)
        sx, sy, sz = pts["sa"](c)
        paths.append([(cx, cy + 0.4, cz), (cx, bly, cz), (cx, bly, blz), (sx, sy, sz)])
    _beads(m, g, "sh", paths, m["dram_bead"], beat, u0, u1)
    return g


def write_back(m, bk, row, beat, u0, u1):
    """Row buffer data goes back down into each cell of `row` (PRECHARGE)."""
    pts = bk["pts"]
    g = empty(f"dram_wb{row}_{beat}", bk["g"])
    paths = []
    for c in range(bk["cols"]):
        cx, cy, cz = pts["cell"](row, c)
        _, bly, blz = pts["bl"](c)
        sx, sy, sz = pts["sa"](c)
        paths.append([(sx, sy, sz), (cx, bly, blz), (cx, bly, cz), (cx, cy + 0.4, cz)])
    _beads(m, g, "wb", paths, m["dram_bead_w"], beat, u0, u1)
    return g


def io_flow(m, bk, cols, beat, u0, u1):
    """READ/WRITE: data leaves the open row through the row buffer to the bank's I/O edge."""
    pts = bk["pts"]
    g = empty(f"dram_io_{beat}", bk["g"])
    io = pts["io"]
    paths = []
    for c in cols:
        rx, ry, rz = pts["rb"](c)
        paths.append([(rx, ry + 1.0, rz), (rx, ry + 4.0, rz), (io[0] - 4.0, io[1] + 2.0, rz), io])
    _beads(m, g, "io", paths, m["dram_bead"], beat, u0, u1, life=30)
    return g


def bl_show(bk, key, spans):
    """Bitline state: key "hi" (full swing) or "eq" (equalized to half), shown during the spans."""
    show(bk["bl_" + key], spans)


def fill(m, parent, name, x0, x1, y, z, beat, u0, u1, until_beat, n=10, mt="dram_timer"):
    """Timer bar: blocks appear left to right over beat/u0..u1, and stay until the end of until_beat."""
    g = empty(name, parent)
    w = (x1 - x0) / n
    end = F(until_beat + 1, 0)
    for k in range(n):
        a = x0 + w * k
        blk = bx(f"{name}_{k}", (a + 0.2, y, z - 1.2), (a + w - 0.2, y + 1.0, z + 1.2), m[mt], g)
        show(blk, [(F(beat, u0 + (u1 - u0) * k / n), end)])
    return g


def cmd_strip(m, parent, name, x0, x1, z, y=0.6):
    return bx(name, (x0, y - 0.2, z - 1.2), (x1, y + 0.4, z + 1.2), m["dram_sub"], parent)


def tick(m, parent, name, x, z, y=0.6):
    return bx(name, (x - 0.3, y, z - 2.5), (x + 0.3, y + 4.0, z + 2.5), m["dram_tick"], parent)
