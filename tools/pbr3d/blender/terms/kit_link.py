"""kit_link: shared parts for the networking-links family (SerDes, retimers, PCIe).

Import from a term script with:  import kit_link as K  (this folder is on sys.path via term_common).
Every part takes a materials dict m, a parent group and a name, and returns a group or a points
dict. Call K.materials(m) once per scene, after C.setup(), to add the lnk_* materials.

API (name(args) -> returns, one line each):
  materials(m)                                  add lnk_* materials (idempotent)
  lane_die(m, parent, name, x0, x1, z0, lanes=8)
                                                cut-open SerDes/retimer die on the bench: parallel
                                                input bus, RX CDR columns, serializer, TX driver.
                                                -> (group, pts): pts keys par, cdr, ser, out, top
  lane_ring(m, parent, name, xs, z, n=8)        row of small SerDes macros on the board at z
                                                -> (group, [top points])
  diff_pair(m, parent, name, x0, x1, z, sep=1.6, w=0.45)
                                                flat differential pair traces on the board top
                                                -> (pts_p, pts_n) polylines at y = 0.4
  retimer(m, parent, name, c, w=30.0, d=30.0, h=3.0)
                                                retimer package on the board (pins on 4 sides)
                                                -> dict top (x,y,z), left (x,y,z), right (x,y,z)
  pcie_slot(m, parent, name, x0, x1, z, lanes=16)
                                                PCIe edge connector: dark housing, gold fingers
                                                -> dict lanes [(x,y,z) per lane], top (x,y,z)
  pcie_card(m, parent, name, x0, x1, z, h=12.0)
                                                add-in card standing in the slot, with gold edge
                                                -> group
  eye(m, parent, name, c, w, h)                 eye diagram drawn as glowing traces on a dark panel
                                                -> group
  speed_bars(m, parent, name, base, rates=(32, 64, 128), x_gap=14.0, scale=0.22)
                                                one bar per rate, height proportional to GT/s
                                                -> dict tops [(x,y,z) per bar]
"""

from sand_overview import empty  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, join, polyline, mat  # noqa: E402


def materials(m):
    if "lnk_si" in m:
        return
    m["lnk_si"] = mat("lnk_si", (0.36, 0.38, 0.46), metal=0.5, rough=0.35)
    m["lnk_rx"] = mat("lnk_rx", (0.30, 0.55, 0.80), metal=0.2, rough=0.4)
    m["lnk_tx"] = mat("lnk_tx", (0.80, 0.52, 0.25), metal=0.2, rough=0.4)
    m["lnk_cdr"] = mat("lnk_cdr", (0.55, 0.45, 0.80), metal=0.2, rough=0.4)
    m["lnk_eq"] = mat("lnk_eq", (0.35, 0.70, 0.55), metal=0.2, rough=0.4)
    m["lnk_pkg"] = mat("lnk_pkg", (0.10, 0.11, 0.13), metal=0.0, rough=0.5)
    m["lnk_ceramic"] = mat("lnk_ceramic", (0.20, 0.21, 0.24), metal=0.0, rough=0.4)
    m["lnk_bus"] = mat("lnk_bus", (0.95, 0.95, 1.0), emit=(0.95, 0.95, 1.0), strength=2.5)
    m["lnk_eye"] = mat("lnk_eye", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=2.5)
    m["lnk_bar"] = mat("lnk_bar", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=1.5, metal=0.0, rough=0.3)
    m["lnk_panel"] = mat("lnk_panel", (0.02, 0.04, 0.06), metal=0.0, rough=0.7)


def lane_die(m, parent, name, x0, x1, z0, lanes=8):
    """A SerDes (or retimer) die cut at z = 0: silicon base, one RX column with a CDR per lane,
    one shared serializer tree and TX driver on the right. Returns (group, points)."""
    g = empty(name, parent)
    pitch = (x1 - x0) / lanes
    bx(f"{name}_si", (x0, 0.6, z0), (x1, 3.0, 0.0), m["lnk_si"], g)
    rx_cols = []
    for i in range(lanes):
        xa = x0 + pitch * i + pitch * 0.15
        xb = x0 + pitch * (i + 1) - pitch * 0.15
        rx_cols.append(bx(f"{name}_rx{i}", (xa, 3.0, z0 + 3.0), (xb, 9.0, -3.0), m["lnk_rx"], g))
    bx(f"{name}_cdr", (x0, 9.0, z0 + 3.0), (x1 - (x1 - x0) * 0.2, 12.0, -3.0), m["lnk_cdr"], g)
    bx(f"{name}_ser", (x0 + (x1 - x0) * 0.55, 12.0, z0 + 3.0), (x1, 17.0, -3.0), m["lnk_tx"], g)
    bx(f"{name}_drv", (x1 - (x1 - x0) * 0.18, 17.0, z0 + 3.0), (x1, 21.0, -3.0), m["lnk_tx"], g)
    bx(f"{name}_eq", (x0 + (x1 - x0) * 0.1, 12.0, z0 + 3.0), (x0 + (x1 - x0) * 0.40, 15.0, -3.0), m["lnk_eq"], g)
    join(rx_cols, f"{name}_rxcols")
    pts = {
        "par": (x0 + pitch / 2, 6.0, z0 / 2),
        "cdr": ((x0 + x1) / 2, 10.5, z0 / 2),
        "ser": (x0 + (x1 - x0) * 0.75, 14.5, z0 / 2),
        "out": (x1 - 2.0, 19.0, z0 / 2),
        "top": ((x0 + x1) / 2, 21.0, z0 / 2),
    }
    return g, pts


def lane_ring(m, parent, name, xs, z, n=8):
    """A row of small SerDes macros along the board at depth z, from xs[0] to xs[1]."""
    g = empty(name, parent)
    x0, x1 = xs
    step = (x1 - x0) / n
    tops = []
    parts = []
    for i in range(n):
        xa = x0 + step * i + step * 0.2
        xb = x0 + step * (i + 1) - step * 0.2
        parts.append(bx(f"{name}_m{i}", (xa, 0.0, z - 3.0), (xb, 2.6, z + 3.0), m["lnk_si"], g))
        tops.append(((xa + xb) / 2, 2.6, z))
    join(parts, f"{name}_mesh")
    return g, tops


def diff_pair(m, parent, name, x0, x1, z, sep=1.6, w=0.45):
    """Two flat traces along x, sep apart in z, on the board top. Returns (pts_p, pts_n)."""
    g = empty(name, parent)
    for s, tag in ((-1, "p"), (1, "n")):
        zc = z + s * sep / 2
        bx(f"{name}_{tag}", (x0, 0.0, zc - w / 2), (x1, 0.35, zc + w / 2), m["copper"], g)
    yy = 0.4
    pts_p = [(x0, yy, z - sep / 2), (x1, yy, z - sep / 2)]
    pts_n = [(x0, yy, z + sep / 2), (x1, yy, z + sep / 2)]
    return pts_p, pts_n


def retimer(m, parent, name, c, w=30.0, d=30.0, h=3.0):
    """A retimer package: black body with leads on all four sides. Returns its anchor points."""
    x, y, z = c
    g = empty(name, parent)
    bx(f"{name}_b", (x - w / 2, y + 0.3, z - d / 2), (x + w / 2, y + h, z + d / 2), m["lnk_pkg"], g)
    pitch = w / 9
    for side in (-1, 1):
        for i in range(8):
            px = x - w / 2 + pitch * (i + 1)
            bx(f"{name}_pz{side}{i}", (px - 0.4, y, z + side * d / 2), (px + 0.4, y + 0.5, z + side * (d / 2 + 1.2)), m["tin"], g)
    for side in (-1, 1):
        for i in range(6):
            pz = z - d / 2 + d * (i + 1) / 7
            bx(f"{name}_px{side}{i}", (x + side * w / 2, y, pz - 0.4), (x + side * (w / 2 + 1.2), y + 0.5, pz + 0.4), m["tin"], g)
    D.tube(f"{name}_dot", (x - w / 2 + 1.2, y + h, z - d / 2 + 1.2), (x - w / 2 + 1.2, y + h + 0.05, z - d / 2 + 1.2), 0.4, m["ink"], g, 10)
    return {"top": (x, y + h, z), "left": (x - w / 2 - 1.0, y + 0.5, z), "right": (x + w / 2 + 1.0, y + 0.5, z)}


def pcie_slot(m, parent, name, x0, x1, z, lanes=16):
    """A PCIe x16 edge connector: dark housing on the board with a gold finger pair per lane."""
    g = empty(name, parent)
    bx(f"{name}_h", (x0, 0.0, z - 2.5), (x1, 6.0, z + 2.5), m["lnk_pkg"], g)
    pitch = (x1 - x0) / lanes
    fingers = []
    lane_pts = []
    for i in range(lanes):
        xc = x0 + pitch * (i + 0.5)
        fingers.append(bx(f"{name}_f{i}", (xc - 0.3, 6.0, z - 1.0), (xc + 0.3, 6.6, z + 1.0), m["gold"], g))
        lane_pts.append((xc, 3.0, z))
    join(fingers, f"{name}_fingers")
    return {"lanes": lane_pts, "top": ((x0 + x1) / 2, 6.0, z)}


def pcie_card(m, parent, name, x0, x1, z, h=12.0):
    """An add-in card stood in the slot: green board with a row of gold edge fingers."""
    g = empty(name, parent)
    bx(f"{name}_pcb", (x0, 6.0, z - 0.8), (x1, 6.0 + h, z + 0.8), m["fr4"], g)
    bx(f"{name}_edge", (x0, 5.2, z - 0.8), (x1, 6.0, z + 0.8), m["gold"], g)
    return g


def eye(m, parent, name, c, w, h):
    """An eye diagram: dark panel with a glowing diamond outline and two crossing traces."""
    cx, cy, cz = c
    g = empty(name, parent)
    bx(f"{name}_p", (cx - w / 2 - 2, cy - h / 2 - 2, cz - 1.5), (cx + w / 2 + 2, cy + h / 2 + 2, cz - 0.5), m["lnk_panel"], g)
    diam = [(cx - w / 2, cy, cz), (cx, cy + h / 2, cz), (cx + w / 2, cy, cz), (cx, cy - h / 2, cz), (cx - w / 2, cy, cz)]
    polyline(f"{name}_d", diam, 0.22, m["lnk_eye"], g)
    rise = [(cx - w / 2, cy - h * 0.3, cz), (cx, cy - h * 0.02, cz), (cx + w / 2, cy + h * 0.3, cz)]
    fall = [(cx - w / 2, cy + h * 0.3, cz), (cx, cy + h * 0.02, cz), (cx + w / 2, cy - h * 0.3, cz)]
    polyline(f"{name}_r", rise, 0.2, m["lnk_eye"], g)
    polyline(f"{name}_f", fall, 0.2, m["lnk_eye"], g)
    return g


def speed_bars(m, parent, name, base, rates=(32, 64, 128), x_gap=14.0, scale=0.22):
    """One bar per rate (GT/s), standing on `base` (x, y, z) and rising in +y."""
    g = empty(name, parent)
    bx_, by, bz = base
    tops = []
    for i, r in enumerate(rates):
        xa = bx_ + i * x_gap
        hgt = r * scale
        bx(f"{name}_b{i}", (xa, by, bz - 3.0), (xa + 6.0, by + hgt, bz + 3.0), m["lnk_bar"], g)
        tops.append((xa + 3.0, by + hgt + 1.0, bz))
    return {"tops": tops, "group": g}
