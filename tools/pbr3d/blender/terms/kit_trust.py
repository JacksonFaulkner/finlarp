"""Security-trust kit: shared parts for the trust terms (on-die enclaves, keys, roots of trust, PQC).

Used by trm_tee.py, trm_confidential_computing.py, trm_hardware_root_of_trust.py and
trm_post_quantum_cryptography.py. Every part takes a materials dict `m` (from materials()) and a
parent object, and returns a group or a dict of points. Coordinates are scene units: the base
board's top is y = 0, and the bench (term_common.BENCH) is x 150..248.

API (also in scratchpad/kit_api/trust.md):
  materials(m)                             add the trust_* materials into m (call once per scene)
  die(m, parent, name, x0, x1, z0, z1, y0, y1, mt="trust_silicon")
                                           one silicon slab; returns the box
  enclave(m, parent, name, x0, x1, z0, z1, y0, y1, wall=1.2)
                                           a sealed region on a die: teal core + barrier walls;
                                           returns {"group", "core", "walls", "gate"} (gate = point
                                           on the front wall (+z side, facing the camera) where requests cross)
  fuse_row(m, parent, name, x0, x1, z, y, n, blown=())
                                           n fuse cells in a row; the indexes in `blown` are dark;
                                           returns {"group", "pts"} (pts = list of cell centres)
  padlock(m, parent, name, c, s=1.0, mt="trust_key")
                                           a padlock standing at c (base at c, size s); returns group
  vm_box(m, parent, name, lo, hi, encrypted=True)
                                           a block (a whole VM) with a padlock on top; purple
                                           ciphertext when encrypted, teal plaintext when not;
                                           returns {"group", "lock", "top"}
  chain(m, parent, name, x, z0, n, y0, w, h, gap, mt=None)
                                           n stacked blocks (boot stages); returns {"group",
                                           "blocks", "top", "tops"} with the top-centre of each
  lattice(m, parent, name, c, n=4, s=6.0, r=0.45)
                                           an n x n x n grid of nodes joined by edges, centred at c;
                                           returns {"group", "nodes"} (nodes = dict (i,j,k)->point)
  key_bar(m, parent, name, a, b, r=0.3, teeth=5)
                                           a key: shaft from a to b with teeth; returns group
  hsm(m, parent, name, c, w, d, h)         a hardware security module box with a status light;
                                           returns {"group", "light", "top"}
  verifier(m, parent, name, c, w=8.0)      a remote verifier panel (screen with a check bar);
                                           returns {"group", "ok", "top"}
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path[:0] = [HERE, BL]
import sand_overview as O  # noqa: E402
from sand_overview import P, ball, empty, mat, tube  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx  # noqa: E402


def materials(m):
    """The trust_* materials. Names are prefixed so they never clash with another family's."""
    m["trust_silicon"] = mat("trust_silicon", (0.40, 0.44, 0.52), metal=0.5, rough=0.3)
    m["trust_core"] = mat("trust_core", (0.30, 0.34, 0.40), metal=0.4, rough=0.35)
    m["trust_enclave"] = mat("trust_enclave", (0.12, 0.55, 0.55), metal=0.3, rough=0.3,
                             emit=(0.10, 0.90, 0.85), strength=1.0)
    m["trust_wall"] = mat("trust_wall", (0.90, 0.62, 0.25), metal=0.5, rough=0.3)
    m["trust_gate"] = mat("trust_gate", (0.35, 1.0, 0.60), emit=(0.35, 1.0, 0.60), strength=2.5)
    m["trust_deny"] = mat("trust_deny", (1.0, 0.25, 0.15), emit=(1.0, 0.25, 0.15), strength=3.0)
    m["trust_key"] = mat("trust_key", (0.95, 0.75, 0.30), metal=0.95, rough=0.25,
                         emit=(1.0, 0.80, 0.30), strength=1.5)
    m["trust_fuse"] = mat("trust_fuse", (0.85, 0.80, 0.55), metal=0.8, rough=0.3)
    m["trust_fuse_blown"] = mat("trust_fuse_blown", (0.20, 0.18, 0.18), rough=0.6)
    m["trust_cipher"] = mat("trust_cipher", (0.35, 0.25, 0.75), emit=(0.45, 0.30, 1.0), strength=1.8)
    m["trust_clear"] = mat("trust_clear", (0.40, 1.0, 0.80), emit=(0.40, 1.0, 0.80), strength=2.5)
    m["trust_hash"] = mat("trust_hash", (0.30, 0.36, 0.46), metal=0.3, rough=0.4)
    m["trust_lat"] = mat("trust_lat", (0.85, 0.92, 1.0), emit=(0.80, 0.90, 1.0), strength=1.5)
    m["trust_lat_edge"] = mat("trust_lat_edge", (0.45, 0.60, 0.85), metal=0.2, rough=0.4)
    m["trust_rsa"] = mat("trust_rsa", (0.62, 0.64, 0.70), metal=0.7, rough=0.3)
    m["trust_plastic"] = mat("trust_plastic", (0.10, 0.10, 0.12), rough=0.6)
    m["trust_ok"] = mat("trust_ok", (0.30, 1.0, 0.50), emit=(0.30, 1.0, 0.50), strength=2.5)
    m["trust_screen"] = mat("trust_screen", (0.04, 0.06, 0.09), rough=0.3)
    return m


def die(m, parent, name, x0, x1, z0, z1, y0, y1, mt="trust_silicon"):
    return bx(name, (x0, y0, z0), (x1, y1, z1), m[mt], parent)


def enclave(m, parent, name, x0, x1, z0, z1, y0, y1, wall=1.2):
    """A sealed region: the teal core inside a ring of barrier walls, all standing on the die."""
    g = empty(name, parent)
    core = bx(f"{name}_core", (x0 + wall, y0, z0 + wall), (x1 - wall, y1, z1 - wall), m["trust_enclave"], g)
    walls = empty(f"{name}_walls", g)
    bx(f"{name}_wf", (x0, y0, z0), (x1, y1 + 1.2, z0 + wall), m["trust_wall"], walls)
    bx(f"{name}_wb", (x0, y0, z1 - wall), (x1, y1 + 1.2, z1), m["trust_wall"], walls)
    bx(f"{name}_wl", (x0, y0, z0), (x0 + wall, y1 + 1.2, z1), m["trust_wall"], walls)
    bx(f"{name}_wr", (x1 - wall, y0, z0), (x1, y1 + 1.2, z1), m["trust_wall"], walls)
    gate = (x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2 + 0.4, z1 - wall / 2)
    return {"group": g, "core": core, "walls": walls, "gate": gate}


def fuse_row(m, parent, name, x0, x1, z, y, n, blown=()):
    g = empty(name, parent)
    pitch = (x1 - x0) / n
    pts = []
    for i in range(n):
        xc = x0 + pitch * (i + 0.5)
        mt = "trust_fuse_blown" if i in blown else "trust_fuse"
        bx(f"{name}_f{i}", (xc - pitch * 0.3, y, z - pitch * 0.3), (xc + pitch * 0.3, y + 2.0, z + pitch * 0.3), m[mt], g)
        pts.append((xc, y + 2.0, z))
    return {"group": g, "pts": pts}


def padlock(m, parent, name, c, s=1.0, mt="trust_key"):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_body", (x - 1.6 * s, y, z - 1.2 * s), (x + 1.6 * s, y + 3.0 * s, z + 1.2 * s), m[mt], g)
    r = 1.1 * s
    arc = []
    for k in range(9):
        a0 = math.pi * k / 8
        a1 = math.pi * (k + 1) / 8
        p0 = (x - r * math.cos(a0), y + 3.0 * s + r * math.sin(a0), z)
        p1 = (x - r * math.cos(a1), y + 3.0 * s + r * math.sin(a1), z)
        arc.append(tube(f"{name}_sh{k}", p0, p1, 0.35 * s, m[mt], g, 6))
    D.join(arc, f"{name}_shackle")
    return g


def vm_box(m, parent, name, lo, hi, encrypted=True):
    g = empty(name, parent)
    mt = "trust_cipher" if encrypted else "trust_clear"
    blk = bx(f"{name}_blk", lo, hi, m[mt], g)
    cx = (lo[0] + hi[0]) / 2
    cz = (lo[2] + hi[2]) / 2
    top = (cx, hi[1], cz)
    lock = padlock(m, g, f"{name}_lock", (cx, hi[1] + 0.2, cz), s=min(1.8, (hi[0] - lo[0]) / 8.0), mt="trust_key")
    return {"group": g, "lock": lock, "top": top, "block": blk}


def chain(m, parent, name, x, z0, n, y0, w, h, gap, mt=None):
    g = empty(name, parent)
    blocks, tops = [], []
    for i in range(n):
        y = y0 + i * (h + gap)
        mat_ = mt[i] if isinstance(mt, (list, tuple)) else (mt or "trust_hash")
        blocks.append(bx(f"{name}_b{i}", (x - w / 2, y, z0 - w / 2), (x + w / 2, y + h, z0 + w / 2), m[mat_], g))
        tops.append((x, y + h, z0))
    return {"group": g, "blocks": blocks, "top": tops[-1] if tops else None, "tops": tops}


def lattice(m, parent, name, c, n=4, s=6.0, r=0.45):
    g = empty(name, parent)
    half = (n - 1) * s / 2
    nodes = {}
    for i in range(n):
        for j in range(n):
            for k in range(n):
                p = (c[0] - half + i * s, c[1] - half + j * s, c[2] - half + k * s)
                nodes[(i, j, k)] = p
                ball(f"{name}_n{i}{j}{k}", p, r, m["trust_lat"], g, 10)
    edges = []
    for (i, j, k), p in nodes.items():
        for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            q = (i + d[0], j + d[1], k + d[2])
            if q in nodes:
                edges.append(tube(f"{name}_e{i}{j}{k}{d[0]}{d[1]}{d[2]}", p, nodes[q], 0.08, m["trust_lat_edge"], g, 4))
    D.join(edges, f"{name}_edges")
    return {"group": g, "nodes": nodes}


def key_bar(m, parent, name, a, b, r=0.3, teeth=5):
    g = empty(name, parent)
    parts = [tube(f"{name}_shaft", a, b, r, m["trust_key"], g, 8)]
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    for t in range(teeth):
        f = 0.25 + 0.7 * t / max(1, teeth - 1)
        p = (a[0] + dx * f, a[1] + dy * f, a[2] + dz * f)
        q = (p[0], p[1] - 1.5, p[2])  # teeth hang below the shaft
        parts.append(tube(f"{name}_t{t}", p, q, r, m["trust_key"], g, 6))
    D.join(parts, f"{name}_m")
    return g


def hsm(m, parent, name, c, w, d, h):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_box", (x - w / 2, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["trust_plastic"], g)
    light = bx(f"{name}_light", (x + w * 0.25, y + h, z - d * 0.1), (x + w * 0.35, y + h + 0.3, z + d * 0.1), m["trust_ok"], g)
    return {"group": g, "light": light, "top": (x, y + h, z)}


def verifier(m, parent, name, c, w=8.0):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_body", (x - w / 2, y, z - 0.6), (x + w / 2, y + w * 0.6, z + 0.6), m["trust_plastic"], g)
    ok = bx(f"{name}_ok", (x - w * 0.3, y + w * 0.2, z + 0.6), (x + w * 0.3, y + w * 0.3, z + 0.8), m["trust_ok"], g)
    return {"group": g, "ok": ok, "top": (x, y + w * 0.6, z)}
