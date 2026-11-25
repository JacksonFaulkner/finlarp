"""Part builders, routes and bead helpers for the NETWORK+COOL tab's LEAF page (net_leaf_*.py).

The leaf (top-of-rack) tier of an AI cluster, in centimetres. Units as everywhere
(docs/diagram-pages.md): Y up, x along the row, z toward the camera; rack fronts face +z.

  row 0       the detailed row: four GPU racks (four 8-GPU servers each, two 800G NIC ports a
              server) round a network rack in the middle. Its leaf switch sits near the top (y
              196-208), front panel open: 64 OSFP cages, the bottom row of 32 downlinks, the
              top row of 32 uplinks. The lid is cut away to show the switch ASIC under its
              heatsink, SerDes traces to the cages, fans and power supplies at the back.
  downlinks   32 cables, one per server port: black copper DAC from the two racks beside the
              leaf, aqua AOC from the two outer racks (too far for passive copper at 100G/lane).
  rows 1-3    three more rows behind (z = -220 r), simplified, each with its own leaf.
  spines      four spine switches in a spine rack row at x = 520, every leaf fibred to every
              spine through overhead trays (yellow single-mode fibre): the leaf-spine fabric.

`switch(m, parent, o, s)` and `osfp(m, parent, o, s)` take an origin and scale, so the
sections can draw them far larger. The shared shape, bead and camera helpers come from
power_vrm_detail.py (bx, wire, bead, run, rise, present, blink, frame, camera_path).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402,F401
from sand_overview import F, P, ball, empty, fly, key, show, tube, mat  # noqa: E402,F401
from power_vrm_detail import (  # noqa: E402,F401
    bx, join, polyline, wire, arc, bead, run, rise, present, blink, frame, camera_path,
)

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "floor": mat("nl_floor", (0.30, 0.32, 0.35), rough=0.8),
        "tile": mat("nl_tile", (0.22, 0.24, 0.27), rough=0.7),
        "rack": mat("nl_rack", (0.10, 0.11, 0.13), metal=0.6, rough=0.45),
        "rackside": mat("nl_rackside", (0.16, 0.17, 0.20), metal=0.5, rough=0.5),
        "server": mat("nl_server", (0.26, 0.27, 0.30), metal=0.7, rough=0.35),
        "bezel": mat("nl_bezel", (0.06, 0.06, 0.07), rough=0.5),
        "chassis": mat("nl_chassis", (0.55, 0.57, 0.60), metal=0.85, rough=0.3),
        "mask": mat("nl_mask", (0.07, 0.30, 0.16), rough=0.55),
        "copper": mat("nl_copper", (0.82, 0.48, 0.28), metal=0.9, rough=0.32),
        "gold": mat("nl_gold", (0.88, 0.72, 0.30), metal=0.95, rough=0.25),
        "cage": mat("nl_cage", (0.72, 0.74, 0.78), metal=0.9, rough=0.25),
        "hole": mat("nl_hole", (0.02, 0.02, 0.03), rough=0.6),
        "substrate": mat("nl_substrate", (0.40, 0.26, 0.15), rough=0.75),
        "die": mat("nl_die", (0.26, 0.20, 0.42), metal=0.4, rough=0.3),
        "fin": mat("nl_fin", (0.70, 0.72, 0.76), metal=0.85, rough=0.3),
        "fan": mat("nl_fan", (0.08, 0.08, 0.09), rough=0.6),
        "psu": mat("nl_psu", (0.30, 0.32, 0.36), metal=0.6, rough=0.4),
        "dac": mat("nl_dac", (0.20, 0.20, 0.22), rough=0.45),
        "aoc": mat("nl_aoc", (0.15, 0.62, 0.70), rough=0.5),
        "smf": mat("nl_smf", (0.92, 0.80, 0.12), rough=0.45),
        "trayc": mat("nl_trayc", (0.50, 0.52, 0.55), metal=0.8, rough=0.4),
        "shell": mat("nl_shell", (0.62, 0.64, 0.68), metal=0.85, rough=0.3),
        "twinax": mat("nl_twinax", (0.85, 0.85, 0.82), rough=0.4),
        "glass": mat("nl_glass", (0.70, 0.85, 0.95), rough=0.1, alpha=0.6),
        "dsp": mat("nl_dsp", (0.20, 0.22, 0.26), metal=0.5, rough=0.35),
        "ib": mat("nl_ib", (0.12, 0.30, 0.18), metal=0.5, rough=0.4),
        # glows
        "pkt": mat("nl_pkt", (0.30, 0.90, 1.0), emit=(0.20, 0.85, 1.0), strength=6.0),
        "up": mat("nl_up", (1.0, 0.90, 0.30), emit=(1.0, 0.85, 0.20), strength=6.0),
        "spine": mat("nl_spine", (0.60, 1.0, 0.40), emit=(0.50, 1.0, 0.30), strength=6.0),
        "led": mat("nl_led", (0.30, 1.0, 0.40), emit=(0.25, 1.0, 0.35), strength=3.0),
        "led_a": mat("nl_led_a", (1.0, 0.70, 0.20), emit=(1.0, 0.62, 0.12), strength=3.0),
        "die_hot": mat("nl_die_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=1.4),
        "heat": mat("nl_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=4.0),
        "cool": mat("nl_cool", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=3.0),
        "fail": mat("nl_fail", (1.0, 0.12, 0.08), emit=(1.0, 0.08, 0.05), strength=5.0),
        "ecn": mat("nl_ecn", (0.75, 0.40, 1.0), emit=(0.70, 0.35, 1.0), strength=5.0),
        "credit": mat("nl_credit", (0.40, 1.0, 0.55), emit=(0.30, 1.0, 0.45), strength=5.0),
        "laser": mat("nl_laser", (1.0, 0.25, 0.20), emit=(1.0, 0.20, 0.15), strength=5.0),
        "q": mat("nl_q", (1.0, 0.45, 0.10), emit=(1.0, 0.40, 0.08), strength=4.0),
        "lit": mat("nl_lit", (0.25, 0.65, 0.90), emit=(0.20, 0.55, 0.85), strength=1.2),
    }


# ---- layout ---------------------------------------------------------------------------------

RACK_W = 60.0
PITCH = 64.0
RACK_H = 220.0
RACK_D = 120.0
RACK_X = [-128.0, -64.0, 0.0, 64.0, 128.0]  # x = 0 is the network rack
GPU_RACKS = [-128.0, -64.0, 64.0, 128.0]
TRAY_Y = [30.0, 64.0, 98.0, 132.0]  # bottom of each server
TRAY_H = 26.0
ROW_Z = [0.0, -220.0, -440.0, -660.0]  # front face of each row
LEAF_Y = 196.0  # bottom of the leaf switch
SW_W, SW_H, SW_D = 54.0, 12.0, 60.0  # switch box, half-width 27
CM_Y = (184.0, 192.0)  # cable manager under the leaf
TRAY_TOP = 252.0  # overhead fibre trays
SPINE_X = 520.0
SPINE_Z = [-60.0, -280.0, -500.0, -720.0]
SPINE_Y = 196.0
N_PORT = 32
PORT_PITCH = 1.55


def L(o, s, x, y, z):
    return (o[0] + x * s, o[1] + y * s, o[2] + z * s)


# ---- the leaf switch ------------------------------------------------------------------------


def port_x(i):
    return (i - (N_PORT - 1) / 2.0) * PORT_PITCH


def switch(m, parent, o, s=1.0, detail=True, name="sw"):
    """A 2U 64-port 800G switch, front face at o.z, lid cut away. Local box: x -27..27,
    y 0..12, z 0..-60. Returns its group, the port fronts, the ASIC centre and the parts."""
    g = empty(name, parent)
    W, H, D = SW_W / 2.0, SW_H, SW_D

    def b(n, lo, hi, mt, par=g):
        return bx(f"{name}_{n}", L(o, s, *lo), L(o, s, *hi), mt, par)

    body = [
        b("pan", (-W, 0.0, -D), (W, 0.6, 0.0), m["chassis"]),
        b("sideL", (-W, 0.0, -D), (-W + 0.5, H, 0.0), m["chassis"]),
        b("sideR", (W - 0.5, 0.0, -D), (W, H, 0.0), m["chassis"]),
        b("back", (-W, 0.0, -D), (W, H, -D + 0.5), m["chassis"]),
        b("face", (-W, 0.0, -0.8), (W, H, 0.0), m["bezel"]),
    ]
    join(body, f"{name}_body")
    out = {"g": g, "up": [], "down": [], "parts": {}}
    yd, yu = 3.2, 8.0  # port row centres
    cages, holes = [], []
    for i in range(N_PORT):
        x = port_x(i)
        for row, yc in (("down", yd), ("up", yu)):
            cages.append(b(f"c{row}{i}", (x - 0.68, yc - 1.0, -8.0), (x + 0.68, yc + 1.0, 0.25), m["cage"]))
            holes.append(b(f"h{row}{i}", (x - 0.5, yc - 0.8, 0.0), (x + 0.5, yc + 0.8, 0.3), m["hole"]))
            out[row].append(L(o, s, x, yc, 0.35))
    join(cages, f"{name}_cages")
    join(holes, f"{name}_holes")
    # port LEDs, four groups that blink apart
    out["leds"] = []
    for gi in range(4):
        lg = empty(f"{name}_ledg{gi}", g)
        ls = []
        for i in range(gi, N_PORT, 4):
            x = port_x(i)
            ls.append(b(f"ld{gi}_{i}", (x - 0.3, 5.3, 0.0), (x + 0.3, 5.9, 0.35), m["led"], lg))
            ls.append(b(f"lu{gi}_{i}", (x - 0.3, 10.2, 0.0), (x + 0.3, 10.8, 0.35), m["led_a"], lg))
        join(ls, f"{name}_leds{gi}")
        out["leds"].append(lg)
    out["asic"] = L(o, s, 0.0, 3.0, -28.0)
    out["top"] = L(o, s, 0.0, H, -28.0)
    if not detail:
        lid = b("lid", (-W, H - 0.4, -D), (W, H, 0.0), m["chassis"])
        lid.name = f"{name}_lid"
        return out
    # inside: board, ASIC, heatsink, SerDes traces, CPU, fans, PSUs
    inner = [
        b("pcb", (-W + 0.6, 0.6, -D + 6.0), (W - 0.6, 1.1, -0.8), m["mask"]),
        b("sub", (-6.0, 1.1, -34.0), (6.0, 1.8, -22.0), m["substrate"]),
        b("lidA", (-4.2, 1.8, -32.2), (4.2, 2.4, -23.8), m["cage"]),
        b("cpu", (-24.0, 1.1, -44.0), (-14.0, 2.2, -36.0), m["dsp"]),
        b("cpu2", (-23.0, 2.2, -43.0), (-15.0, 2.6, -37.0), m["mask"]),
    ]
    for k in range(10):
        z = -33.0 + 1.2 * k
        inner.append(b(f"fin{k}", (-7.0, 2.4, z), (7.0, 9.5, z + 0.4), m["fin"]))
    inner.append(b("finbase", (-7.0, 2.4, -34.0), (7.0, 3.0, -22.0), m["fin"]))
    join(inner, f"{name}_inner")
    out["parts"]["heatsink"] = L(o, s, 0.0, 9.5, -28.0)
    out["parts"]["cpu"] = L(o, s, -19.0, 2.6, -40.0)
    # die glow under the heatsink (visible from the side between fins)
    dg = empty(f"{name}_dieglow", g)
    b("dieg", (-3.0, 2.4, -31.0), (3.0, 2.9, -25.0), m["die_hot"], dg)
    out["die_glow"] = dg
    # SerDes traces: from the package edge to the cages (copper on the board)
    traces, out["tr_down"], out["tr_up"] = [], [], []
    for i in range(N_PORT):
        x = port_x(i)
        xa = -5.5 + 11.0 * i / (N_PORT - 1)
        pd = [L(o, s, xa, 1.15, -22.0), L(o, s, xa + (x - xa) * 0.5, 1.15, -14.0), L(o, s, x, 1.15, -8.0)]
        out["tr_down"].append(pd + [L(o, s, x, 3.2, -6.0), L(o, s, x, 3.2, 0.35)])
        out["tr_up"].append(pd + [L(o, s, x, 8.0, -6.0), L(o, s, x, 8.0, 0.35)])
        if i % 2 == 0:
            for k in range(len(pd) - 1):
                traces.append(tube(f"{name}_tr{i}_{k}", pd[k], pd[k + 1], 0.12 * s, m["copper"], g, 6))
    join(traces, f"{name}_traces")
    # fans (6) and PSUs (2) along the back
    fans = []
    out["fans"] = []
    for k in range(6):
        x = -20.0 + 8.0 * k
        fans.append(b(f"fanb{k}", (x - 3.6, 1.0, -D + 0.5), (x + 3.6, 9.5, -D + 5.5), m["fan"]))
        fans.append(tube(f"{name}_hub{k}", L(o, s, x, 5.2, -D + 5.6), L(o, s, x, 5.2, -D + 5.0), 1.0 * s, m["fin"], g, 12))
        out["fans"].append(L(o, s, x, 5.2, -D + 3.0))
    for k, x in enumerate((-24.5, 24.5)):
        fans.append(b(f"psu{k}", (x - 2.0, 0.8, -D + 0.5), (x + 2.0, 10.0, -D + 22.0), m["psu"]))
    join(fans, f"{name}_rear")
    out["parts"]["psu"] = L(o, s, 24.5, 10.0, -D + 10.0)
    return out


def osfp(m, parent, o, s=1.0, name="ox", lasers=True):
    """An 800G OSFP DR8 transceiver cut open along z (x across, length along -z from its plug
    end at o.z to the MPO end at o.z - 10). Returns the group and key points."""
    g = empty(name, parent)

    def b(n, lo, hi, mt):
        return bx(f"{name}_{n}", L(o, s, *lo), L(o, s, *hi), mt, g)

    parts = [
        b("shell_b", (-1.1, 0.0, -10.0), (1.1, 0.2, 0.0), m["shell"]),
        b("shell_l", (-1.1, 0.0, -10.0), (-0.95, 1.3, 0.0), m["shell"]),
        b("pcb", (-0.9, 0.35, -9.0), (0.9, 0.5, 0.4), m["mask"]),
        b("edge", (-0.9, 0.35, 0.0), (0.9, 0.5, 0.6), m["gold"]),
        b("dsp", (-0.5, 0.5, -3.2), (0.5, 0.75, -2.0), m["dsp"]),
        b("drv", (-0.5, 0.5, -5.2), (0.5, 0.65, -4.4), m["dsp"]),
        b("mpo", (-0.7, 0.4, -10.4), (0.7, 1.0, -9.2), m["glass"]),
    ]
    for k in range(6):
        z = -9.6 + 1.4 * k
        parts.append(b(f"fin{k}", (-1.1, 1.3, z), (1.1, 1.9, z + 0.6), m["shell"]))
    pts = {"edge": L(o, s, 0.0, 0.6, 0.3), "dsp": L(o, s, 0.0, 0.75, -2.6), "las": L(o, s, 0.0, 0.7, -6.4),
           "mpo": L(o, s, 0.0, 0.7, -10.4), "lanes": []}
    for k in range(8):
        x = -0.56 + 0.16 * k
        parts.append(b(f"wg{k}", (x - 0.03, 0.5, -9.2), (x + 0.03, 0.56, -6.4), m["glass"]))
        pts["lanes"].append([L(o, s, x, 0.6, -6.4), L(o, s, x, 0.6, -9.6), L(o, s, x, 0.6, -14.0)])
    join(parts, f"{name}_body")
    if lasers:
        lg = empty(f"{name}_las", g)
        for k in range(8):
            x = -0.56 + 0.16 * k
            bx(f"{name}_l{k}", L(o, s, x - 0.06, 0.5, -6.6), L(o, s, x + 0.06, 0.66, -6.2), m["laser"], lg)
        pts["las_g"] = lg
    return g, pts


# ---- racks, servers -------------------------------------------------------------------------


def frame_rack(m, parent, xc, zf, name):
    """Posts, top and sides of an open-front rack."""
    W, D = RACK_W / 2.0, RACK_D
    ps = [
        bx(f"{name}_top", (xc - W, RACK_H - 2.0, zf - D), (xc + W, RACK_H, zf - (D - 40.0 if xc == 0.0 else 0.0)), m["rack"], parent),
        bx(f"{name}_base", (xc - W, 0.0, zf - D), (xc + W, 6.0, zf), m["rack"], parent),
        bx(f"{name}_sl", (xc - W, 0.0, zf - D), (xc - W + 1.0, RACK_H, zf - 3.0), m["rackside"], parent),
        bx(f"{name}_sr", (xc + W - 1.0, 0.0, zf - D), (xc + W, RACK_H, zf - 3.0), m["rackside"], parent),
        bx(f"{name}_bk", (xc - W, 0.0, zf - D), (xc + W, RACK_H, zf - D + 1.0), m["rackside"], parent),
    ]
    for sx in (-1, 1):
        ps.append(bx(f"{name}_p{sx}", (xc + sx * (W - 3.0) - 1.0, 0.0, zf - 3.0), (xc + sx * (W - 3.0) + 1.0, RACK_H, zf - 1.0),
                     m["rack"], parent))
    return join(ps, f"{name}_frame")


def server(m, parent, xc, y0, zf, side, name):
    """An 8-GPU server: front bezel, eight GPU heat sinks seen through its open top, two 800G NIC
    ports on the side nearer the leaf. Returns the two port points."""
    W = RACK_W / 2.0 - 3.5
    parts = [
        bx(f"{name}_box", (xc - W, y0, zf - 100.0), (xc + W, y0 + TRAY_H - 6.0, zf - 1.0), m["server"], parent),
        bx(f"{name}_bz", (xc - W, y0, zf - 1.5), (xc + W, y0 + TRAY_H - 6.0, zf - 0.6), m["bezel"], parent),
    ]
    for k in range(8):
        x = xc - W + 4.0 + k * (2 * W - 8.0) / 7.0
        parts.append(bx(f"{name}_v{k}", (x - 1.6, y0 + 3.0, zf - 0.7), (x + 1.6, y0 + TRAY_H - 9.0, zf - 0.5), m["hole"], parent))
    join(parts, f"{name}_mesh")
    pts = []
    for k in range(2):
        x = xc + side * (W - 3.0 - 4.0 * k)
        pts.append((x, y0 + TRAY_H - 4.0, zf + 0.3))
    pc = [bx(f"{name}_nic{k}", (p[0] - 1.2, p[1] - 1.4, zf - 4.0), (p[0] + 1.2, p[1] + 1.4, zf + 0.2), m["cage"], parent)
          for k, p in enumerate(pts)]
    bx(f"{name}_nicb", (xc - W, y0 + TRAY_H - 6.0, zf - 30.0), (xc + W, y0 + TRAY_H - 2.0, zf - 0.6), m["bezel"], parent)
    join(pc, f"{name}_nics")
    return pts


def dac_route(p, q, k, zf):
    """A downlink from server port p to leaf port q: out, along the rack front, up the rack's
    inner edge, across under the cable manager, up into the port."""
    zc = zf + 2.0 + 0.35 * (k % 8)
    side = -1 if p[0] < 0 else 1
    rack_c = min(RACK_X, key=lambda r: abs(r - p[0]))
    lane = rack_c - side * (RACK_W / 2.0 - 1.5 - 0.6 * (k % 4))
    yc = CM_Y[0] - 1.0 - 0.6 * (k % 6)
    return [p, (p[0], p[1], zc), (lane, p[1], zc), (lane, yc, zc), (q[0], yc, zc), (q[0], q[1] - 3.0, zc),
            (q[0], q[1] - 1.0, q[2] + 0.6), q]


def fibre_route(q, r, j, zf, zl):
    """An uplink bundle from leaf r's uplink row (at q) to spine j: up to the row tray, along it to
    the spine row, along the spine tray to spine j, down into it."""
    y = TRAY_TOP + 2.0 + 2.2 * j
    zt = zl - 40.0 + 6.0 * j
    xs = SPINE_X - 30.0 + 4.0 * j
    sz = SPINE_Z[j] + 8.0 - 4.0 * r
    return [q, (q[0], q[1] + 4.0, zf + 3.0), (q[0], y, zf + 3.0), (q[0], y, zt), (xs, y, zt), (xs, y, sz),
            (SPINE_X - 24.0, y, sz), (SPINE_X - 24.0, SPINE_Y + 6.0, sz)]


def trays(m, parent):
    """Overhead cable trays: one along each row, one along the spine row."""
    g = empty("trays", parent)
    parts = []
    for r, zf in enumerate(ROW_Z):
        z0, z1 = zf - 50.0, zf - 20.0
        parts += [bx(f"tr{r}_b", (-170.0, TRAY_TOP, z0), (SPINE_X - 20.0, TRAY_TOP + 0.8, z1), m["trayc"], g),
                  bx(f"tr{r}_s", (-170.0, TRAY_TOP, z0), (SPINE_X - 20.0, TRAY_TOP + 5.0, z0 + 0.6), m["trayc"], g)]
        for x in (-150.0, 60.0, 280.0):
            parts.append(tube(f"tr{r}_h{x}", (x, TRAY_TOP, z0 + 15.0), (x, 330.0, z0 + 15.0), 0.6, m["trayc"], g, 6))
    parts += [bx("trs_b", (SPINE_X - 36.0, TRAY_TOP, -780.0), (SPINE_X - 14.0, TRAY_TOP + 0.8, 10.0), m["trayc"], g),
              bx("trs_s", (SPINE_X - 36.0, TRAY_TOP, -780.0), (SPINE_X - 35.4, TRAY_TOP + 5.0, 10.0), m["trayc"], g)]
    join(parts, "trays_mesh")
    return g


def spine_rack(m, parent, j):
    """A spine switch in its rack, in the spine row at x = 520, its ports facing -x."""
    zc = SPINE_Z[j]
    g = empty(f"spine{j}", parent)
    parts = [
        bx(f"sp{j}_rack", (SPINE_X - 20.0, 0.0, zc - 32.0), (SPINE_X + 40.0, RACK_H, zc + 32.0), m["rackside"], g),
        bx(f"sp{j}_box", (SPINE_X - 22.0, SPINE_Y, zc - 28.0), (SPINE_X + 30.0, SPINE_Y + 12.0, zc + 28.0), m["chassis"], g),
        bx(f"sp{j}_face", (SPINE_X - 22.6, SPINE_Y + 1.0, zc - 27.0), (SPINE_X - 21.8, SPINE_Y + 11.0, zc + 27.0), m["bezel"], g),
    ]
    join(parts, f"spine{j}_mesh")
    lg = empty(f"spine{j}_leds", g)
    leds = []
    for k in range(16):
        z = zc - 24.0 + 3.2 * k
        leds.append(bx(f"sp{j}_l{k}", (SPINE_X - 23.0, SPINE_Y + 8.0, z - 0.5), (SPINE_X - 22.5, SPINE_Y + 9.2, z + 0.5), m["led"], lg))
        leds.append(bx(f"sp{j}_m{k}", (SPINE_X - 23.0, SPINE_Y + 3.0, z - 0.5), (SPINE_X - 22.5, SPINE_Y + 4.2, z + 0.5), m["led_a"], lg))
    join(leds, f"spine{j}_ledm")
    return {"g": g, "leds": lg, "top": (SPINE_X - 22.0, SPINE_Y + 12.0, zc), "port": (SPINE_X - 23.0, SPINE_Y + 6.0, zc)}


def simple_row(m, parent, r):
    """A row behind: five rack blocks with server bezels, and its leaf switch near the top."""
    zf = ROW_Z[r]
    g = empty(f"row{r}", parent)
    parts = []
    for xc in RACK_X:
        parts.append(bx(f"r{r}_{xc}", (xc - 30.0, 0.0, zf - RACK_D), (xc + 30.0, RACK_H, zf - 1.0), m["rack"], g))
        if xc != 0.0:
            for y in TRAY_Y:
                parts.append(bx(f"r{r}_{xc}_{y}", (xc - 26.0, y, zf - 1.2), (xc + 26.0, y + TRAY_H - 6.0, zf), m["server"], g))
    join(parts, f"row{r}_mesh")
    sw = switch(m, g, (0.0, LEAF_Y, zf + 0.5), 1.0, detail=False, name=f"leaf{r}")
    return g, sw


def floor(m, parent):
    parts = [bx("floor", (-220.0, -2.0, -820.0), (600.0, 0.0, 120.0), m["floor"], parent)]
    for i in range(-3, 10):
        x = i * 60.0
        parts.append(bx(f"fl_x{i}", (x - 0.4, 0.0, -820.0), (x + 0.4, 0.05, 120.0), m["tile"], parent))
    join(parts, "floor_mesh")


# ---- the scene ------------------------------------------------------------------------------


def scene(m, root, rows=True, spines=True):
    """The whole fabric. Returns a dict of groups, points and routes (see the docstring)."""
    s = {}
    floor(m, root)
    zf = ROW_Z[0]
    row0 = empty("row0", root)
    for xc in RACK_X:
        frame_rack(m, row0, xc, zf, f"rk{int(xc)}")
    # network rack furniture: cable manager under the leaf, patch panel
    bx("cm", (-26.0, CM_Y[0], zf - 10.0), (26.0, CM_Y[1], zf - 1.0), m["bezel"], row0)
    leaf = switch(m, row0, (0.0, LEAF_Y, zf + 0.5), 1.0, detail=True, name="leaf0")
    s["leaf"] = leaf
    ports, s["server_names"] = [], []
    sg = empty("servers", row0)
    for xc in GPU_RACKS:
        side = 1 if xc < 0 else -1
        for t, y in enumerate(TRAY_Y):
            ports += server(m, sg, xc, y, zf, side, f"srv{int(xc)}_{t}")
    # assign ports to leaf downlinks, left racks to the left half
    ports.sort(key=lambda p: (p[0], -p[1]))
    s["srv_ports"] = ports
    dl = empty("downlinks", root)
    s["dac"], s["dac_g"], s["aoc_g"] = [], empty("dac_g", dl), empty("aoc_g", dl)
    for i, p in enumerate(ports):
        q = leaf["down"][i]
        rt = dac_route(p, q, i, zf)
        s["dac"].append(rt)
        far = abs(p[0]) > 96.0
        wire(f"dl{i}", rt, 0.42 if not far else 0.3, m["aoc"] if far else m["dac"], s["aoc_g"] if far else s["dac_g"], 6)
    # uplinks: the 32 uplink ports gather into four bundles, one per spine
    ug = empty("uplinks", root)
    s["up_g"] = ug
    s["fib"] = {}
    for i in range(N_PORT):
        j = i // 8
        q = leaf["up"][i]
        bxj = -12.0 + 8.0 * j
        polyline(f"uf{i}", [q, (q[0], q[1] + 3.0, zf + 2.6), (bxj, TRAY_TOP - 18.0, zf + 3.0), (bxj, TRAY_TOP + 2.0 + 2.2 * j, zf + 3.0)],
                 0.14, m["smf"], ug)
    s["routes_up"] = {}
    sp = []
    if spines:
        sp = [spine_rack(m, root, j) for j in range(4)]
    s["spines"] = sp
    leaves = [leaf]
    s["rows"] = []
    if rows:
        for r in (1, 2, 3):
            g, lf = simple_row(m, root, r)
            s["rows"].append(g)
            leaves.append(lf)
    s["leaves"] = leaves
    trays(m, root)
    fg = empty("fabric", root)
    s["fabric_g"] = fg
    for r, lf in enumerate(leaves):
        zr = ROW_Z[r]
        for j in range(4 if spines else 0):
            q = (-12.0 + 8.0 * j, LEAF_Y + 12.5, zr + 3.0) if r else (-12.0 + 8.0 * j, TRAY_TOP + 2.0 + 2.2 * j, zr + 3.0)
            rt = fibre_route(q, r, j, zr, zr)
            if r:
                rt = [lf["up"][8 * j + 4]] + rt
            s["routes_up"][(r, j)] = rt
            wire(f"fb{r}{j}", rt, 0.7, m["smf"], fg, 6)
    return s


# ---- paths for beads ------------------------------------------------------------------------


def to_leaf(s, i):
    """Server port i -> its DAC -> leaf downlink port -> ASIC."""
    return s["dac"][i] + s["leaf"]["tr_down"][i][::-1][1:]


def to_spine(s, r, j, port=None):
    """Leaf r's ASIC (row 0 only, through uplink port `port`) or uplink -> spine j."""
    rt = s["routes_up"][(r, j)]
    if r == 0:
        i = 8 * j + 3 if port is None else port
        lf = s["leaf"]
        start = lf["tr_up"][i] + [(lf["up"][i][0], lf["up"][i][1] + 3.0, ROW_Z[0] + 2.6),
                                  (-12.0 + 8.0 * j, TRAY_TOP - 18.0, ROW_Z[0] + 3.0)]
        return start + rt
    return rt


def from_spine(s, r, j):
    return list(reversed(to_spine(s, r, j)))


def from_leaf(s, i):
    return list(reversed(to_leaf(s, i)))


def scope_box(m, parent, c, w, h, name):
    """A dark backing panel for close-up graphs (queues, link meters)."""
    return bx(name, (c[0] - w / 2, c[1] - h / 2, c[2] - 1.0), (c[0] + w / 2, c[1] + h / 2, c[2]), m["bezel"], parent)


def bar(m, parent, x, y0, h, z, w, mt, name):
    """A vertical meter bar (inside its own empty so show/present keep its scale)."""
    g = empty(name, parent)
    bx(f"{name}_b", (x - w / 2, y0, z), (x + w / 2, y0 + h, z + 0.6), mt, g)
    return g


def dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def queue(m, parent, at, n, beats, u0, u1, dy=1.3, name="q", mt="q"):
    """A queue building at `at`: bead k appears at u0 + (u1-u0) k/n of each beat and stays to the
    end of that beat, stacking up in y."""
    bl = [beats] if isinstance(beats, int) else list(beats)
    g = empty(name, parent)
    for k in range(n):
        e = empty(f"{name}{k}", g)
        bead(f"{name}{k}_s", (at[0], at[1] + dy * k, at[2]), 0.6 * dy, m[mt], e, 8)
        show(e, [(F(b, u0 + (u1 - u0) * k / n), F(b + 1, 0)) for b in bl])
    return g
