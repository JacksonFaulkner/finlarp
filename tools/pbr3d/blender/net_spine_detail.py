"""Part builders for the NETWORK+COOL tab's SPINE page (net_spine_*.py).

A 51.2 Tb/s spine switch (a Broadcom Tomahawk 5 class ASIC in an Arista / Cisco style 2RU box), drawn at
life size in millimetres with its lid lifted off, plus the leaf-spine fabric it sits in. Units as
everywhere (docs/diagram-pages.md): Y up, x across the box, z toward the camera (the front panel is at
z = 0 and faces the camera).

  chassis    floor pan, side walls, rear wall, a lid that lifts away (present()), a green main board
  ports      64 OSFP cages in 4 rows of 16 across the front, each with an 800G module plugged in and a
             link LED above it (LEDs blink in four groups)
  asic       the switch ASIC in the middle of the board: substrate, lid, a finned heatsink that can
             lift away (`hs` present group, `hs_lift` keyed group)
  traces     16 copper SerDes trace bundles from the ASIC's edge forward to each column of cages
  fans       a fan wall of 4 fans (rotors spin all the time), two PSUs at the back corners, a small CPU
             board
  fabric     three more (plain) spines beside it and 8 leaf switches below and in front; a fibre from
             every leaf to every spine (ECMP), paths returned by `fiber(spine, leaf)`

Close-ups for the sections (built at height BY, away from the fabric):
  asic_close   the ASIC package at 1.6x: BGA, substrate, die with a SerDes ring, ingress pipes, the
               shared packet buffer, egress pipes
  optic_close  one OSFP 800G module at 4x, shell cut open: edge fingers, DSP, drivers, 8 lasers, lens,
               fibre ribbon, MPO connector, photodiodes, top fins
  eye          a PAM4 eye: four levels, transitions, the sampling point

Generic helpers (bx, run, rise, present, blink, frame, camera_path...) come from power_vrm_detail.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, empty, key, show, tube, mat, rel, pivot  # noqa: E402
import power_vrm_detail as V  # noqa: E402
from power_vrm_detail import bx, join, polyline, bead, run, rise, present, blink, frame, camera_path  # noqa: E402,F401


def materials():
    return {
        "steel": mat("spn_steel", (0.55, 0.57, 0.60), metal=0.85, rough=0.35),
        "chassis": mat("spn_chassis", (0.18, 0.19, 0.21), metal=0.6, rough=0.45),
        "lid": mat("spn_lid", (0.30, 0.31, 0.34), metal=0.7, rough=0.4),
        "face": mat("spn_face", (0.10, 0.10, 0.11), metal=0.4, rough=0.5),
        "mask": mat("spn_mask", (0.06, 0.30, 0.16), rough=0.55),
        "copper": mat("spn_copper", (0.85, 0.50, 0.28), metal=0.9, rough=0.3),
        "cage": mat("spn_cage", (0.70, 0.72, 0.75), metal=0.9, rough=0.3),
        "module": mat("spn_module", (0.42, 0.44, 0.48), metal=0.8, rough=0.35),
        "tab": mat("spn_tab", (0.10, 0.35, 0.75), rough=0.5),
        "substrate": mat("spn_substrate", (0.30, 0.22, 0.14), rough=0.7),
        "die": mat("spn_die", (0.24, 0.20, 0.40), metal=0.4, rough=0.3),
        "silicon": mat("spn_silicon", (0.40, 0.42, 0.48), metal=0.6, rough=0.3),
        "alu": mat("spn_alu", (0.72, 0.74, 0.78), metal=0.85, rough=0.3),
        "solder": mat("spn_solder", (0.74, 0.76, 0.80), metal=0.9, rough=0.25),
        "gold": mat("spn_gold", (0.88, 0.72, 0.30), metal=0.95, rough=0.25),
        "plastic": mat("spn_plastic", (0.12, 0.12, 0.13), rough=0.7),
        "fan": mat("spn_fan", (0.08, 0.08, 0.09), rough=0.6),
        "psu": mat("spn_psu", (0.36, 0.37, 0.40), metal=0.6, rough=0.4),
        "leaf": mat("spn_leaf", (0.22, 0.23, 0.26), metal=0.6, rough=0.45),
        "strip": mat("spn_strip", (0.55, 0.57, 0.60), metal=0.8, rough=0.35),
        "fiber": mat("spn_fiber", (0.85, 0.75, 0.15), rough=0.5),
        "fiber_dim": mat("spn_fiber_dim", (0.45, 0.42, 0.20), rough=0.6),
        "pipe_in": mat("spn_pipe_in", (0.20, 0.55, 0.35), metal=0.3, rough=0.4),
        "pipe_out": mat("spn_pipe_out", (0.75, 0.42, 0.18), metal=0.3, rough=0.4),
        "buffer": mat("spn_buffer", (0.20, 0.36, 0.70), metal=0.3, rough=0.4),
        "serdes": mat("spn_serdes", (0.80, 0.62, 0.25), metal=0.5, rough=0.35),
        "laser": mat("spn_laser", (0.55, 0.15, 0.18), metal=0.5, rough=0.35),
        "lens": mat("spn_lens", (0.70, 0.85, 0.95), rough=0.1),
        "screen": mat("spn_screen", (0.03, 0.05, 0.07), rough=0.3),
        "grid": mat("spn_grid", (0.24, 0.30, 0.36), rough=0.5),
        # glows
        "led": mat("spn_led", (0.3, 1.0, 0.4), emit=(0.2, 1.0, 0.3), strength=5.0),
        "pkt": mat("spn_pkt", (0.3, 0.9, 1.0), emit=(0.2, 0.88, 1.0), strength=6.0),
        "pkt2": mat("spn_pkt2", (1.0, 0.85, 0.3), emit=(1.0, 0.8, 0.2), strength=6.0),
        "pkt3": mat("spn_pkt3", (1.0, 0.35, 0.85), emit=(1.0, 0.3, 0.85), strength=6.0),
        "pkt4": mat("spn_pkt4", (0.5, 1.0, 0.35), emit=(0.45, 1.0, 0.3), strength=6.0),
        "light": mat("spn_light", (1.0, 0.25, 0.2), emit=(1.0, 0.2, 0.15), strength=6.0),
        "cool": mat("spn_cool", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0),
        "heat": mat("spn_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=5.0),
        "die_hot": mat("spn_die_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=0.7),
        "lit": mat("spn_lit", (0.35, 0.85, 1.0), emit=(0.3, 0.8, 1.0), strength=0.6),
        "fail": mat("spn_fail", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=4.0),
        "level": mat("spn_level", (0.3, 0.9, 1.0), emit=(0.25, 0.85, 1.0), strength=2.0),
    }


# ---- layout -----------------------------------------------------------------------------------

CX0, CX1 = -220.0, 220.0  # chassis x
CH = 88.0  # 2RU
CZ0 = -560.0  # rear
PCB_Y = (4.0, 6.0)
TY = 6.4  # trace height
COLS = [-187.5 + 25.0 * c for c in range(16)]  # cage column centres
ROWS = [10.0, 29.0, 50.0, 69.0]  # cage row bottoms (14 high)
CAGE_D = 62.0  # cages run back to z = -62
MOD_OUT = 26.0  # modules stick out to z = +26
ASIC = (0.0, -260.0)  # x, z centre
SUBH = 42.0  # substrate half size
HS = (-62.0, 62.0, -330.0, -190.0)  # heatsink x0, x1, z0, z1
HS_Y = (14.0, 82.0)
FAN_Z = (-445.0, -415.0)
FANS = [-90.0, -30.0, 30.0, 90.0]
FAN_Y = 44.0
FAN_R = 27.0
SPINES = [-1800.0, -900.0, 0.0, 900.0]  # x of the four spines; index 2 is the detailed one
DETAIL = 2
LEAVES = [-2025.0 + 450.0 * i for i in range(8)]
LY = -520.0  # leaf bottom
LH = 44.0
LZ = (300.0, 620.0)
BY = 1500.0  # close-ups live up here


def port(c, r):
    """Front centre of cage column c, row r (on the module's pull end)."""
    return (COLS[c], ROWS[r] + 7.0, MOD_OUT)


def trace_path(c, r=1):
    """ASIC edge -> along the board -> up into the cage of column c, row r."""
    x = COLS[c]
    xa = max(-SUBH + 2, min(SUBH - 2, x * 0.2))
    return [(xa, TY + 4.0, ASIC[1] + SUBH * 0.6), (xa, TY, ASIC[1] + SUBH + 4.0), (xa, TY, -170.0),
            (x, TY, -100.0), (x, TY, -66.0), (x, ROWS[r] + 7.0, -50.0), (x, ROWS[r] + 7.0, 0.0)]


def spine_port(k, leaf):
    """The front port on spine k that goes to `leaf`."""
    x0 = SPINES[k]
    return (x0 + COLS[2 * leaf], ROWS[3] + 7.0, MOD_OUT if k == DETAIL else 4.0)


def leaf_port(leaf, k):
    x = LEAVES[leaf] - 150.0 + 100.0 * k
    return (x, LY + LH * 0.6, LZ[1] + 4.0)


def fiber(k, leaf):
    """Polyline of the fibre from spine k to `leaf` (spine end first)."""
    a = spine_port(k, leaf)
    b = leaf_port(leaf, k)
    mx = (a[0] + b[0]) / 2
    return [a, (a[0], a[1], a[2] + 50.0), (a[0], a[1] - 50.0, a[2] + 120.0), (mx, (a[1] + b[1]) / 2, 330.0),
            (b[0], b[1] + 20.0, b[2] + 80.0), (b[0], b[1], b[2] + 30.0), b]


def flow(src, k, dst):
    """A packet's whole trip leaf src -> spine k -> leaf dst. Through the detailed spine it rides the
    traces through the ASIC."""
    up = list(reversed(fiber(k, src)))
    down = fiber(k, dst)
    if k == DETAIL:
        c0, c1 = 2 * src, 2 * dst
        mid = list(reversed(trace_path(c0, 3)))[1:] + [(ASIC[0], 18.0, ASIC[1])] + trace_path(c1, 3)[:-1]
        return up + mid + down
    return up + [(SPINES[k], 60.0, -200.0)] + down


# ---- chassis ----------------------------------------------------------------------------------


def chassis(m, root):
    g = empty("chassis", root)
    parts = [
        bx("floor", (CX0, 0.0, CZ0), (CX1, 2.0, 0.0), m["chassis"], g),
        bx("wall_l", (CX0, 0.0, CZ0), (CX0 + 2.0, CH, 0.0), m["chassis"], g),
        bx("wall_r", (CX1 - 2.0, 0.0, CZ0), (CX1, CH, 0.0), m["chassis"], g),
        bx("rear", (CX0, 0.0, CZ0), (CX1, CH, CZ0 + 2.0), m["chassis"], g),
        bx("face_top", (CX0, CH - 4.0, -2.0), (CX1, CH, 0.0), m["face"], g),
        bx("face_bot", (CX0, 0.0, -2.0), (CX1, 8.0, 0.0), m["face"], g),
        bx("face_l", (CX0, 0.0, -2.0), (COLS[0] - 13.0, CH, 0.0), m["face"], g),
        bx("face_r", (COLS[-1] + 13.0, 0.0, -2.0), (CX1, CH, 0.0), m["face"], g),
    ]
    join(parts, "chassis_mesh")
    bx("pcb", (CX0 + 4, PCB_Y[0], CZ0 + 20.0), (CX1 - 4, PCB_Y[1], -2.0), m["mask"], g)
    # lid, lifted away in beats where we look inside
    lid = empty("lid_g", root)
    join([bx("lid", (CX0, CH, CZ0), (CX1, CH + 2.0, 0.0), m["lid"], lid),
          bx("lid_lip", (CX0, CH - 6.0, CZ0), (CX0 + 3.0, CH, 0.0), m["lid"], lid)], "lid_mesh")
    return {"g": g, "lid": lid}


def ports(m, root):
    g = empty("ports", root)
    cages, mods, tabs, fins = [], [], [], []
    for c, x in enumerate(COLS):
        for r, y in enumerate(ROWS):
            cages.append(bx(f"cage{c}_{r}", (x - 11.5, y, -CAGE_D), (x + 11.5, y + 14.5, 0.5), m["cage"], g))
            mods.append(bx(f"mod{c}_{r}", (x - 10.5, y + 1.0, -CAGE_D + 4), (x + 10.5, y + 13.0, MOD_OUT - 4), m["module"], g))
            tabs.append(bx(f"tab{c}_{r}", (x - 4.0, y + 5.0, MOD_OUT - 4), (x + 4.0, y + 9.0, MOD_OUT), m["tab"], g))
            for f in range(3):
                fx = x - 7.0 + 7.0 * f
                fins.append(bx(f"fin{c}_{r}_{f}", (fx - 0.6, y + 13.0, 0.5), (fx + 0.6, y + 14.0, MOD_OUT - 6), m["alu"], g))
    join(cages, "cages")
    join(mods + fins, "modules")
    join(tabs, "tabs")
    leds = []
    for grp in range(4):
        e = empty(f"led_g{grp}", root)
        parts = []
        for c in range(grp, 16, 4):
            for r in range(4):
                x, y = COLS[c], ROWS[r]
                parts.append(bx(f"led{c}_{r}", (x + 8.0, y + 10.5, 0.2), (x + 10.5, y + 12.5, 1.2), m["led"], e))
        join(parts, f"leds{grp}")
        leds.append(e)
    return {"g": g, "leds": leds}


def asic(m, root):
    ax, az = ASIC
    g = empty("asic", root)
    sub = bx("asic_sub", (ax - SUBH, PCB_Y[1], az - SUBH), (ax + SUBH, PCB_Y[1] + 4.0, az + SUBH), m["substrate"], g)
    bx("asic_lid", (ax - 30, PCB_Y[1] + 4.0, az - 30), (ax + 30, PCB_Y[1] + 8.0, az + 30), m["silicon"], g)
    glow = empty("asic_glow", root)
    bx("asic_glow_b", (ax - 30.5, PCB_Y[1] + 4.0, az - 30.5), (ax + 30.5, PCB_Y[1] + 8.4, az + 30.5), m["die_hot"], glow)
    show(glow, [])
    caps = []
    for i in range(10):
        t = -36.0 + 8.0 * i
        caps.append(bx(f"cap_a{i}", (ax + t, PCB_Y[1] + 4.0, az + 35), (ax + t + 3, PCB_Y[1] + 5.5, az + 37), m["solder"], g))
        caps.append(bx(f"cap_b{i}", (ax + t, PCB_Y[1] + 4.0, az - 37), (ax + t + 3, PCB_Y[1] + 5.5, az - 35), m["solder"], g))
    join(caps, "asic_caps")
    # heatsink: hs (present) > hs_lift (keyed) > parts
    hs = empty("hs_g", root)
    lift = empty("hs_lift", hs)
    x0, x1, z0, z1 = HS
    parts = [bx("hs_base", (x0, HS_Y[0], z0), (x1, HS_Y[0] + 5.0, z1), m["copper"], lift)]
    n = 22
    for i in range(n):
        x = x0 + 2 + (x1 - x0 - 4) * i / (n - 1)
        parts.append(bx(f"hs_fin{i}", (x - 0.7, HS_Y[0] + 5.0, z0), (x + 0.7, HS_Y[1], z1), m["alu"], lift))
    for i, x in enumerate((-30.0, -10.0, 10.0, 30.0)):
        parts.append(tube(f"hs_pipe{i}", (x, HS_Y[0] + 3.0, z1 - 4), (x, HS_Y[1] - 4, z1 - 4), 2.6, m["copper"], lift, 12))
    join(parts, "heatsink")
    return {"g": g, "sub": sub, "glow": glow, "hs": hs, "lift": lift,
            "top": (ax, HS_Y[1], az), "die": (ax, PCB_Y[1] + 8.0, az)}


def traces(m, root):
    g = empty("traces", root)
    objs = []
    for c in range(16):
        for r, dx in ((1, -1.4), (3, 1.4)):
            pts = [(p[0] + dx, p[1], p[2]) for p in trace_path(c, r)][:5]
            objs.append(polyline(f"tr{c}_{r}", pts, 0.6, m["copper"], g))
    join(objs, "traces_mesh")
    return g


def fan_rotor(m, parent, name, c, r, beats):
    """A spinning rotor (hub + 7 blades) at c, axis along z, one turn every 2 s."""
    pv = pivot(name, c, parent)
    parts = [V.O.disc(f"{name}_hub", (0, 0, 0), r * 0.3, 6.0, m["fan"], pv)]
    parts[0].rotation_euler = (math.pi / 2, 0, 0)
    for i in range(7):
        a = 2 * math.pi * i / 7
        p0 = (r * 0.25 * math.cos(a), r * 0.25 * math.sin(a), 0.0)
        p1 = (r * 0.95 * math.cos(a + 0.35), r * 0.95 * math.sin(a + 0.35), 0.0)
        parts.append(tube(f"{name}_bl{i}", p0, p1, r * 0.16, m["fan"], pv, 4))
    join(parts, f"{name}_mesh")
    end = F(beats, 0)
    pv.rotation_mode = "XYZ"
    key(pv, 0, "rotation_euler", (0.0, 0.0, 0.0), linear=True)
    key(pv, end, "rotation_euler", (0.0, end / 48.0 * 2 * math.pi, 0.0), linear=True)
    return pv


def fans(m, root, beats):
    g = empty("fans", root)
    parts = []
    z0, z1 = FAN_Z
    for i, x in enumerate(FANS):
        parts.append(bx(f"fanbox_t{i}", (x - 30, FAN_Y + 28, z0), (x + 30, FAN_Y + 31, z1), m["plastic"], g))
        parts.append(bx(f"fanbox_b{i}", (x - 30, FAN_Y - 31, z0), (x + 30, FAN_Y - 28, z1), m["plastic"], g))
        parts.append(bx(f"fanbox_l{i}", (x - 30, FAN_Y - 31, z0), (x - 28, FAN_Y + 31, z1), m["plastic"], g))
        parts.append(bx(f"fanbox_r{i}", (x + 28, FAN_Y - 31, z0), (x + 30, FAN_Y + 31, z1), m["plastic"], g))
        parts.append(tube(f"fan_ring{i}", (x, FAN_Y, z0 + 2), (x, FAN_Y, z0 + 4), FAN_R + 1, m["plastic"], g, 24))
    join(parts, "fanboxes")
    rotors = [fan_rotor(m, root, f"rotor{i}", (x, FAN_Y, (z0 + z1) / 2), FAN_R, beats) for i, x in enumerate(FANS)]
    # PSUs and CPU board
    p = []
    for s in (-1, 1):
        xa, xb = (CX0 + 4, CX0 + 84) if s < 0 else (CX1 - 84, CX1 - 4)
        p.append(bx(f"psu{s}", (xa, PCB_Y[1], CZ0 + 2), (xb, 42.0, CZ0 + 180), m["psu"], g))
        for k in range(6):
            p.append(bx(f"psu_g{s}{k}", (xa + 6 + 12 * k, 12.0, CZ0 + 180), (xa + 12 + 12 * k, 36.0, CZ0 + 181.5), m["grid"], g))
    p.append(bx("cpu_board", (130.0, PCB_Y[1], -330.0), (200.0, PCB_Y[1] + 2, -240.0), m["mask"], g))
    p.append(bx("cpu", (150.0, PCB_Y[1] + 2, -300.0), (178.0, PCB_Y[1] + 6, -272.0), m["silicon"], g))
    p.append(bx("dimm", (135.0, PCB_Y[1] + 2, -325.0), (195.0, PCB_Y[1] + 30, -321.0), m["plastic"], g))
    join(p, "psus")
    return {"g": g, "rotors": rotors, "psu": (CX0 + 44, 42.0, CZ0 + 90), "cpu": (164.0, 12.0, -286.0)}


def plain_box(m, parent, name, x, y0, h, z0, z1, ports_n=16, mat_body="leaf"):
    """A closed switch: body, a port strip across the front, LEDs."""
    parts = [bx(f"{name}_body", (x - 220, y0, z0), (x + 220, y0 + h, z1), m[mat_body], parent),
             bx(f"{name}_strip", (x - 200, y0 + h * 0.2, z1), (x + 200, y0 + h * 0.8, z1 + 1.5), m["strip"], parent)]
    for i in range(ports_n):
        px = x - 190 + 380 * i / (ports_n - 1)
        parts.append(bx(f"{name}_p{i}", (px - 8, y0 + h * 0.3, z1 + 1.5), (px + 8, y0 + h * 0.7, z1 + 3), m["face"], parent))
    join(parts, f"{name}_mesh")


def fabric(m, root):
    g = empty("fabric", root)
    for k, x in enumerate(SPINES):
        if k != DETAIL:
            plain_box(m, g, f"spine{k}", x, 0.0, CH, CZ0, 0.0)
    for i, x in enumerate(LEAVES):
        plain_box(m, g, f"leaf{i}", x, LY, LH, LZ[0], LZ[1], 12)
    fib = empty("fibers", root)
    objs = [polyline(f"fib{k}_{i}", fiber(k, i), 1.6, m["fiber"], fib) for k in range(4) for i in range(8)]
    join(objs, "fibers_mesh")
    leds = empty("fab_leds", root)
    lp = []
    for i, x in enumerate(LEAVES):
        for j in range(4):
            lp.append(bx(f"fl{i}_{j}", (x + 150 + 12 * j, LY + LH * 0.82, LZ[1]), (x + 158 + 12 * j, LY + LH * 0.92, LZ[1] + 2), m["led"], leds))
    join(lp, "fab_leds_mesh")
    return {"g": g, "fib": fib, "leds": leds}


def airflow(root, m, beats, n=10, u0=0.0, u1=0.85):
    """Front-to-back air: cool beads in through the front, over the heatsink, hot out the back."""
    for i, x in enumerate((-150.0, -45.0, 0.0, 45.0, 150.0)):
        y = 40.0 + 8.0 * (i % 2)
        run(root, f"air_c{i}", [(x, y, 60.0), (x, y, -40.0), (x * 0.8, y + 10, HS[3])], n // 2, 2.2, m["cool"], beats, u0, u1, 70)
        fx = FANS[min(3, int((x + 180) / 90))]
        run(root, f"air_h{i}", [(x * 0.8, y + 10, HS[3]), (x * 0.6, y + 6, HS[0]), (fx, FAN_Y, FAN_Z[1]),
                                (fx, FAN_Y, CZ0 - 120.0)], n // 2, 2.2, m["heat"], beats, u0 + 0.12, min(1.0, u1 + 0.1), 80)


def scene(m, root, beats, fab=True):
    s = {}
    s.update(chassis(m, root))
    s["ports"] = ports(m, root)
    s["asic"] = asic(m, root)
    s["traces"] = traces(m, root)
    s["fans"] = fans(m, root, beats)
    if fab:
        s["fabric"] = fabric(m, root)
    return s


def leds_on(s, beats_list):
    for gi, e in enumerate(s["ports"]["leds"]):
        iv = []
        for b in beats_list:
            for j in range(8):
                if (j + gi) % 3 != 0:
                    iv.append((F(b, j / 8), F(b, (j + 0.6) / 8)))
        show(e, iv)


# ---- close-ups --------------------------------------------------------------------------------

AS = 1.6  # asic close-up scale


def asic_close(m, parent, y0=BY):
    """The ASIC package at 1.6x, centred on (0, y0, 0). Returns named points."""
    g = empty("ac", parent)
    s = AS
    H = 80.0 * s  # substrate half
    D_ = 50.0 * s  # die half
    parts = [bx("ac_sub", (-H, y0, -H), (H, y0 + 6 * s, H), m["substrate"], g)]
    balls = []
    for i in range(9):
        for j in range(9):
            balls.append(ball(f"ac_b{i}_{j}", (-H + 14 + (2 * H - 28) * i / 8, y0 - 2.5, -H + 14 + (2 * H - 28) * j / 8), 4.0, m["solder"], g, 8))
    join(balls, "ac_balls")
    parts.append(bx("ac_die", (-D_, y0 + 6 * s, -D_), (D_, y0 + 9 * s, D_), m["die"], g))
    join(parts, "ac_pkg")
    top = y0 + 9 * s
    tiles = []
    n = 8
    w = 2 * D_ / n
    for i in range(n):
        a = -D_ + w * i + 1.5
        b = a + w - 3
        tiles += [bx(f"ac_tn{i}", (a, top, -D_ + 1), (b, top + 2.5, -D_ + 18), m["serdes"], g),
                  bx(f"ac_ts{i}", (a, top, D_ - 18), (b, top + 2.5, D_ - 1), m["serdes"], g),
                  bx(f"ac_tw{i}", (-D_ + 1, top, a), (-D_ + 18, top + 2.5, b), m["serdes"], g),
                  bx(f"ac_te{i}", (D_ - 18, top, a), (D_ - 1, top + 2.5, b), m["serdes"], g)]
    join(tiles, "ac_serdes")
    pin, pout = [], []
    for i in range(4):
        z = -48.0 + 32.0 * i
        pin.append(bx(f"ac_in{i}", (-D_ + 24, top, z - 10), (-34, top + 5, z + 10), m["pipe_in"], g))
        pout.append(bx(f"ac_out{i}", (34, top, z - 10), (D_ - 24, top + 5, z + 10), m["pipe_out"], g))
    join(pin, "ac_ingress")
    join(pout, "ac_egress")
    buf = bx("ac_buffer", (-28, top, -54), (28, top + 7, 54), m["buffer"], g)
    lit = empty("ac_lit", parent)
    bx("ac_buf_lit", (-28.5, top, -54.5), (28.5, top + 7.5, 54.5), m["lit"], lit)
    show(lit, [])
    return {"g": g, "lit": lit, "top": top, "buf": (0.0, top + 7, 0.0), "in": (-50.0, top + 5, -48.0),
            "out": (50.0, top + 5, 48.0), "serdes": (-D_ + 9, top + 2.5, 30.0), "sub": (H, y0 + 6 * s, H * 0.6),
            "balls": (-H + 14, y0 - 4, H - 14), "D": D_}


def asic_path(ac, zi, zo):
    t = ac["top"] + 6
    D_ = ac["D"]
    return [(-D_ - 60, t, zi), (-D_ + 9, t, zi), (-40.0, t, zi), (-20.0, t + 4, zi * 0.4), (0.0, t + 6, 0.0),
            (20.0, t + 4, zo * 0.4), (40.0, t, zo), (D_ - 9, t, zo), (D_ + 60, t, zo)]


OS_ = 4.0  # optic close-up scale


def optic_close(m, parent, y0=BY):
    """One OSFP 800G module at 4x, shell open on top, its length along z (front, the fibre end, +z)."""
    g = empty("oc", parent)
    W, L = 45.0, 215.0
    shell = [bx("oc_floor", (-W, y0, -L), (W, y0 + 3, L), m["module"], g),
             bx("oc_wall_l", (-W, y0, -L), (-W + 3, y0 + 52, L), m["module"], g),
             bx("oc_wall_r", (W - 3, y0, -L), (W, y0 + 52, L), m["module"], g)]
    join(shell, "oc_shell")
    top = empty("oc_top_g", parent)
    tparts = [bx("oc_lid", (-W, y0 + 52, -L), (W, y0 + 55, L - 30), m["module"], top)]
    for i in range(9):
        x = -W + 6 + (2 * W - 12) * i / 8
        tparts.append(bx(f"oc_fin{i}", (x - 1.2, y0 + 55, -L + 10), (x + 1.2, y0 + 72, L - 40), m["alu"], top))
    join(tparts, "oc_top")
    pcb = [bx("oc_pcb", (-W + 4, y0 + 8, -L - 6), (W - 4, y0 + 11, L - 60), m["mask"], g)]
    for i in range(10):
        x = -36 + 8 * i
        pcb.append(bx(f"oc_finger{i}", (x - 2.5, y0 + 11, -L - 6), (x + 2.5, y0 + 11.6, -L + 24), m["gold"], g))
    join(pcb, "oc_pcb_mesh")
    top_pcb = y0 + 11
    chips = [bx("oc_dsp", (-24, top_pcb, -110), (24, top_pcb + 6, -62), m["silicon"], g)]
    for i in range(8):
        x = -31.5 + 9 * i
        chips.append(bx(f"oc_drv{i}", (x - 3, top_pcb, -20), (x + 3, top_pcb + 3, -10), m["plastic"], g))
        chips.append(bx(f"oc_las{i}", (x - 2, top_pcb, 20), (x + 2, top_pcb + 4, 28), m["laser"], g))
    chips.append(bx("oc_lens", (-38, top_pcb, 38), (38, top_pcb + 8, 46), m["lens"], g))
    chips.append(bx("oc_pd", (-34, top_pcb, 0), (34, top_pcb + 3, 6), m["gold"], g))
    chips.append(bx("oc_mpo", (-26, top_pcb - 4, L - 30), (26, top_pcb + 14, L + 2), m["plastic"], g))
    join(chips, "oc_chips")
    fibs = []
    for i in range(8):
        x = -31.5 + 9 * i
        fibs.append(polyline(f"oc_f{i}", [(x, top_pcb + 4, 46), (x, top_pcb + 6, 110), (x * 0.6, top_pcb + 5, L - 30)], 1.2, m["fiber"], g))
    join(fibs, "oc_fibres")
    return {"g": g, "top": top, "dsp": (0.0, top_pcb + 6, -86.0), "fingers": (0.0, top_pcb + 1, -L + 10),
            "las": (0.0, top_pcb + 4, 24.0), "mpo": (0.0, top_pcb + 14, L - 14), "drv": (0.0, top_pcb + 3, -15.0),
            "pd": (0.0, top_pcb + 3, 3.0), "fins": (0.0, y0 + 72, -40.0), "L": L, "tp": top_pcb}


def optic_lanes(oc, i):
    """Electrical lane i: fingers -> DSP -> driver -> laser. Then light: laser -> fibre -> out."""
    x = -31.5 + 9 * i
    t = oc["tp"]
    L = oc["L"]
    elec = [(x * 0.8, t + 1.5, -L - 4), (x * 0.5, t + 1.5, -110), (x * 0.4, t + 7, -86), (x, t + 4, -62), (x, t + 4, -15)]
    light = [(x, t + 4, 24), (x, t + 5, 46), (x, t + 6, 110), (x * 0.6, t + 5, L - 30), (x * 0.6, t + 5, L + 60)]
    return elec, light


LEVELS = [10.0, 40.0, 70.0, 100.0]


def eye(m, parent, y0=BY):
    """A PAM4 eye: a dark scope, four level lines, every transition between them across one unit
    interval (x -60..60). Returns the group."""
    g = empty("eye", parent)
    join([bx("eye_scope", (-150, y0 - 15, -6), (150, y0 + 125, -3), m["screen"], g),
          bx("eye_frame", (-156, y0 - 21, -9), (156, y0 + 131, -6), m["plastic"], g)], "eye_bg")
    curves = []
    for a in LEVELS:
        for b in LEVELS:
            pts = []
            for j in range(13):
                t = j / 12
                x = -130 + 260 * t
                s = 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, (t - 0.25) * 2)))
                pts.append((x, y0 + a + (b - a) * s, 0.0))
            curves.append(polyline(f"eye_{a}_{b}", pts, 0.9, m["level"], g))
    join(curves, "eye_curves")
    return g
