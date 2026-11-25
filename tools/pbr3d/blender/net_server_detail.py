"""Part builders for the NETWORK+COOL tab's SERVER page (net_server_*.py): one 8-GPU node, an
HGX-class server drawn with its lid off. Units as everywhere (docs/diagram-pages.md): Y up, x across
the chassis, z toward the camera (the front panel is at z = 0, the rear at z = -600).

  gpu board   the HGX baseboard at the back: 8 GPU modules in two rows of four, each a package
              (two dies, eight HBM stacks) under a copper cold plate with microchannel fins. The
              front-left module's cold plate is cut open. Two NVSwitch chips sit between the rows
              and copper NVLink traces run from every GPU to both.
  coolant     a supply header (blue) and a return header (orange) along the rear, rails down each
              GPU column, drops into every cold plate, quick disconnects to the rack manifold.
  host board  the front half: two CPUs under cold plates, 16 DIMMs each, four PCIe switches (one
              per GPU column, two GPUs and two NICs each, plus an NVMe drive), cables across the
              gap from the baseboard.
  front edge  ten cards: eight ConnectX NICs (one per GPU, the compute fabric) and two BlueField
              DPUs in the middle (front-end and storage), each with OSFP cages and port LEDs.
  out         a transceiver in every cage and a cable up to the leaf switch above (or, with
              `rails`, eight rail switches with neighbour servers cabled in), and the DPUs' cables
              to a front-end switch at the right.

`gpu` and `nic` take an origin and a scale so sections can draw one far larger. Beads ride paths
returned by the *_path functions; part builders and camera helpers come from power_vrm_detail.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, empty, show, tube, ball, mat  # noqa: E402
import power_vrm_detail as V  # noqa: E402
from power_vrm_detail import bx, join, wire, arc, bead, run, rise, present, blink, frame, camera_path, polyline  # noqa: E402,F401


def materials():
    return {
        "chassis": mat("srv_chassis", (0.30, 0.32, 0.36), metal=0.8, rough=0.45),
        "floor": mat("srv_floor", (0.20, 0.21, 0.24), metal=0.7, rough=0.55),
        "pcb": mat("srv_pcb", (0.06, 0.28, 0.15), rough=0.55),
        "pcb_host": mat("srv_pcb_host", (0.05, 0.18, 0.22), rough=0.55),
        "pcb_nic": mat("srv_pcb_nic", (0.08, 0.22, 0.12), rough=0.55),
        "pcb_dpu": mat("srv_pcb_dpu", (0.22, 0.10, 0.30), rough=0.55),
        "sub": mat("srv_sub", (0.30, 0.22, 0.14), rough=0.7),
        "die": mat("srv_die", (0.26, 0.20, 0.42), metal=0.4, rough=0.3),
        "hbm": mat("srv_hbm", (0.20, 0.34, 0.62), metal=0.4, rough=0.35),
        "sw_die": mat("srv_sw_die", (0.18, 0.40, 0.36), metal=0.4, rough=0.3),
        "copper": mat("srv_copper", (0.82, 0.48, 0.28), metal=0.9, rough=0.3),
        "trace": mat("srv_trace", (0.78, 0.52, 0.30), metal=0.9, rough=0.35),
        "alu": mat("srv_alu", (0.72, 0.74, 0.78), metal=0.85, rough=0.3),
        "fin": mat("srv_fin", (0.60, 0.62, 0.66), metal=0.85, rough=0.35),
        "dark": mat("srv_dark", (0.10, 0.10, 0.12), rough=0.6),
        "dimm": mat("srv_dimm", (0.10, 0.30, 0.18), rough=0.5),
        "chip": mat("srv_chip", (0.08, 0.08, 0.09), rough=0.5),
        "ihs": mat("srv_ihs", (0.70, 0.70, 0.72), metal=0.9, rough=0.25),
        "cable": mat("srv_cable", (0.16, 0.17, 0.20), rough=0.7),
        "ribbon": mat("srv_ribbon", (0.45, 0.45, 0.50), rough=0.6),
        "fiber": mat("srv_fiber", (0.92, 0.75, 0.20), rough=0.5),
        "fiber_aqua": mat("srv_fiber_aqua", (0.25, 0.75, 0.80), rough=0.5),
        "tube_s": mat("srv_tube_s", (0.10, 0.30, 0.80), rough=0.4),
        "tube_r": mat("srv_tube_r", (0.85, 0.35, 0.10), rough=0.4),
        "qd": mat("srv_qd", (0.80, 0.80, 0.84), metal=0.95, rough=0.2),
        "switch": mat("srv_switch", (0.14, 0.15, 0.18), metal=0.5, rough=0.45),
        "port": mat("srv_port", (0.03, 0.03, 0.04), rough=0.4),
        "ghost": mat("srv_ghost", (0.32, 0.34, 0.40), metal=0.5, rough=0.5),
        "ink": mat("srv_ink", (0.85, 0.85, 0.80), rough=0.6),
        # glows
        "nvl": mat("srv_nvl", (0.40, 1.0, 0.45), emit=(0.30, 1.0, 0.40), strength=6.0),
        "pcie": mat("srv_pcie", (1.0, 0.75, 0.25), emit=(1.0, 0.68, 0.18), strength=6.0),
        "pkt": mat("srv_pkt", (1.0, 0.35, 0.85), emit=(1.0, 0.30, 0.85), strength=6.0),
        "fe": mat("srv_fe", (0.35, 0.80, 1.0), emit=(0.30, 0.75, 1.0), strength=6.0),
        "mem": mat("srv_mem", (0.75, 0.60, 1.0), emit=(0.70, 0.55, 1.0), strength=5.0),
        "cold": mat("srv_cold", (0.25, 0.55, 1.0), emit=(0.20, 0.50, 1.0), strength=4.0),
        "warm": mat("srv_warm", (1.0, 0.45, 0.15), emit=(1.0, 0.40, 0.10), strength=4.0),
        "heat": mat("srv_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=4.0),
        "die_hot": mat("srv_die_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=1.4),
        "led": mat("srv_led", (0.30, 1.0, 0.40), emit=(0.30, 1.0, 0.40), strength=5.0),
        "led_amb": mat("srv_led_amb", (1.0, 0.70, 0.20), emit=(1.0, 0.65, 0.15), strength=5.0),
        "fail": mat("srv_fail", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=3.0),
    }


# ---- layout ---------------------------------------------------------------------------------

CH = (-260.0, 260.0, -600.0, 0.0)  # chassis x0, x1, z0, z1
GB = (-240.0, 240.0, -560.0, -235.0)  # GPU baseboard
HB = (-240.0, 240.0, -205.0, -12.0)  # host board
GX = (-165.0, -55.0, 55.0, 165.0)  # GPU columns
GZ = (-300.0, -490.0)  # GPU rows: front, back
SWX = (-60.0, 60.0)  # NVSwitch chips
SWZ = -395.0
CPUX = (-130.0, 130.0)
CPUZ = -112.0
PX = (-180.0, -60.0, 60.0, 180.0)  # PCIe switches, one per GPU column
PZ = -188.0
CARD_X = [-216.0 + 48.0 * i for i in range(10)]  # front-edge cards
NIC_X = CARD_X[:4] + CARD_X[6:]  # eight NICs
DPU_X = CARD_X[4:6]  # two DPUs
NIC_Z = (-56.0, -6.0)
CP_TOP = 24.0  # top of a cold plate
SUP_Y, RET_Y = 40.0, 50.0  # coolant rail heights
HDR_Z = -572.0
LEAF = (-230.0, 230.0, 200.0, 236.0, 30.0, 100.0)  # x0, x1, y0, y1, z0, z1
FE = (290.0, 380.0, 110.0, 140.0, 20.0, 90.0)


def gpu_index(r, c):
    return r * 4 + c


def gpu_xz(k):
    return GX[k % 4], GZ[k // 4]


def nic_of(k):
    """The NIC paired with GPU k: two per PCIe switch (one per column)."""
    c, r = k % 4, k // 4
    return NIC_X[2 * c + r]


# ---- parts ----------------------------------------------------------------------------------


def gpu(m, parent, name, gx, gz, y0=0.0, s=1.0, cut_open=False):
    """One GPU module at (gx, gz) on a board whose top is y0 (+4): substrate, two dies, eight HBM
    stacks, a copper cold plate with microchannel fins and an aluminium cover, two coolant barbs.
    Returns its group, its die glow group and named points."""
    g = empty(f"{name}_g", parent)

    def B(nm, a, b, mt):
        return bx(f"{name}_{nm}", (gx + a[0] * s, y0 + a[1] * s, gz + a[2] * s), (gx + b[0] * s, y0 + b[1] * s, gz + b[2] * s), mt, g)

    pkg = [B("sub", (-36, 4, -36), (36, 7, 36), m["sub"])]
    dies = [B("die0", (-20, 7, -14), (-1, 10, 14), m["die"]), B("die1", (1, 7, -14), (20, 10, 14), m["die"])]
    hb = []
    for i, zc in enumerate((-21, -7, 7, 21)):
        for sd in (-1, 1):
            x0, x1 = (-33, -23) if sd < 0 else (23, 33)
            hb.append(B(f"hbm{i}{sd}", (x0, 7, zc - 6), (x1, 11.5, zc + 6), m["hbm"]))
    base = B("cp_base", (-38, 11.5, -38), (38, 15, 38), m["copper"])
    fins = [B(f"fin{i}", (-31 + 4.6 * i, 15, -32), (-29.8 + 4.6 * i, 21, 32), m["copper"]) for i in range(14)]
    walls = [B("w0", (-38, 15, -38), (-34, 21, 38), m["copper"]), B("w1", (34, 15, -38), (38, 21, 38), m["copper"]),
             B("w2", (-34, 15, -38), (34, 21, -34), m["copper"])]
    cover = B("cover", (-38, 21, -38), (38, CP_TOP, 38), m["alu"])
    barbs = [tube(f"{name}_barb{sd}", (gx + sd * 28 * s, y0 + CP_TOP * s, gz), (gx + sd * 28 * s, y0 + (CP_TOP + 6) * s, gz), 3.2 * s, m["qd"], g, 12)
             for sd in (-1, 1)]
    if not cut_open:
        walls.append(B("w3", (-34, 15, 34), (34, 21, 38), m["copper"]))
    objs = pkg + dies + hb + [base, cover] + fins + walls
    if cut_open:
        for o in objs + barbs:
            O.cut(o, gz)
        # cover lifted off the front half only: remove nothing more; the cut face shows the fins
    join(pkg + hb, f"{name}_pkg")
    join(fins + walls + [base], f"{name}_plate")
    glow = empty(f"{name}_glow", g)
    zf = 0.0 if cut_open else 14.0
    bx(f"{name}_hot", (gx - 20.5 * s, y0 + 9.8 * s, gz - 14.5 * s), (gx + 20.5 * s, y0 + 10.4 * s, gz + zf * s), m["die_hot"], glow)
    pts = {
        "top": (gx, y0 + CP_TOP * s, gz),
        "die": (gx - 10 * s, y0 + 10 * s, gz),
        "hbm": (gx - 28 * s, y0 + 11.5 * s, gz),
        "fins": (gx, y0 + 18 * s, gz),
        "in": (gx - 28 * s, y0 + (CP_TOP + 6) * s, gz),
        "out": (gx + 28 * s, y0 + (CP_TOP + 6) * s, gz),
        "sub": (gx + 30 * s, y0 + 5.5 * s, gz),
    }
    return g, glow, pts


def nvswitch(m, parent, name, x, z, y0=0.0, s=1.0):
    g = empty(f"{name}_g", parent)

    def B(nm, a, b, mt):
        return bx(f"{name}_{nm}", (x + a[0] * s, y0 + a[1] * s, z + a[2] * s), (x + b[0] * s, y0 + b[1] * s, z + b[2] * s), mt, g)

    sub = B("sub", (-22, 4, -22), (22, 7, 22), m["sub"])
    die = B("die", (-13, 7, -13), (13, 9.5, 13), m["sw_die"])
    base = B("hs", (-22, 9.5, -22), (22, 12, 22), m["fin"])
    fins = [B(f"f{i}", (-22 + 4 * i, 12, -22), (-20.8 + 4 * i, 24, 22), m["fin"]) for i in range(12)]
    join([sub, die], f"{name}_chip")
    join([base] + fins, f"{name}_sink")
    return g, {"top": (x, y0 + 24 * s, z), "die": (x, y0 + 8 * s, z + 13 * s)}


def finned(m, parent, name, x0, x1, z0, z1, y0, y1, n, mt="fin"):
    parts = [bx(f"{name}_b", (x0, y0, z0), (x1, y0 + 2.0, z1), m[mt], parent)]
    w = (x1 - x0) / n
    for i in range(n):
        parts.append(bx(f"{name}_{i}", (x0 + w * i, y0 + 2.0, z0), (x0 + w * i + w * 0.35, y1, z1), m[mt], parent))
    return join(parts, name)


def nic(m, parent, name, nx, y0=0.0, s=1.0, dpu=False, z0=NIC_Z[0], z1=NIC_Z[1]):
    """A ConnectX NIC (or, with `dpu`, a BlueField DPU) lying flat at the front edge: PCB, chip
    under a finned sink, OSFP cage(s) poking out of the front (z = z1 .. z1 + 12), a port LED on
    each. Returns group, LED groups and points."""
    g = empty(f"{name}_g", parent)
    zc = lambda u: z1 + (u - z1) * s  # noqa: E731

    def B(nm, a, b, mt):
        return bx(f"{name}_{nm}", (nx + a[0] * s, y0 + a[1] * s, zc(a[2])), (nx + b[0] * s, y0 + b[1] * s, zc(b[2])), mt, g)

    parts = [B("conn", (-14, 3.5, z0 + 4), (14, 5, z0 + 10), m["dark"]),
             B("pcb", (-20, 5, z0), (20, 6.6, z1), m["pcb_dpu" if dpu else "pcb_nic"]),
             B("chip", (-9, 6.6, -40), (9, 8.2, -24), m["chip"])]
    if dpu:
        parts += [B(f"ddr{i}", (-17 + 9 * i, 6.6, -52), (-11 + 9 * i, 7.8, -46), m["chip"]) for i in range(4)]
    join(parts, f"{name}_card")
    finned(m, g, f"{name}_sink", nx - 11 * s, nx + 11 * s, zc(-42), zc(-22), y0 + 8.2 * s, y0 + 16 * s, 8)
    cages = [(-18, -2), (2, 18)] if dpu else [(-11, 11)]
    leds, ports = [], []
    for i, (a, b) in enumerate(cages):
        B(f"cage{i}", (a, 6.6, -16), (b, 19, z1 + 12), m["alu"])
        B(f"mouth{i}", (a + 1.5, 8.5, z1 + 11.6), (b - 1.5, 17, z1 + 12.2), m["port"])
        lg = empty(f"{name}_led{i}", g)
        bx(f"{name}_ledm{i}", (nx + (a + 2) * s, y0 + 19 * s, zc(z1 + 9)), (nx + (a + 5) * s, y0 + 20.2 * s, zc(z1 + 12)), m["led"], lg)
        leds.append(lg)
        ports.append((nx + (a + b) / 2 * s, y0 + 12.8 * s, zc(z1 + 12)))
    pts = {"chip": (nx, y0 + 16 * s, zc(-32)), "cage": (nx, y0 + 19 * s, zc(z1 + 4)), "ports": ports,
           "pcb": (nx + 14 * s, y0 + 6.6 * s, zc(-10))}
    return g, leds, pts


def cpu(m, parent, name, cx, cz):
    g = empty(f"{name}_g", parent)
    parts = [bx(f"{name}_sock", (cx - 32, 3.5, cz - 38), (cx + 32, 6, cz + 38), m["dark"], g),
             bx(f"{name}_ihs", (cx - 26, 6, cz - 30), (cx + 26, 9, cz + 30), m["ihs"], g),
             bx(f"{name}_cp", (cx - 24, 9, cz - 28), (cx + 24, 18, cz + 28), m["copper"], g)]
    join(parts, f"{name}_body")
    for sd in (-1, 1):
        tube(f"{name}_barb{sd}", (cx + sd * 16, 18, cz), (cx + sd * 16, 24, cz), 2.6, m["qd"], g, 10)
    dimms = []
    for sd in (-1, 1):
        for i in range(8):
            x = cx + sd * (42 + 5.5 * i)
            dimms.append(bx(f"{name}_d{sd}{i}", (x - 1.2, 3.5, cz - 52), (x + 1.2, 32, cz + 52), m["dimm"], g))
            for j in range(4):
                zz = cz - 44 + 24 * j
                dimms.append(bx(f"{name}_c{sd}{i}{j}", (x - 1.8, 12, zz), (x + 1.8, 22, zz + 14), m["chip"], g))
    join(dimms, f"{name}_dimms")
    return g, {"top": (cx, 18, cz), "dimm": (cx + 60, 32, cz), "dimm_l": (cx - 60, 32, cz), "in": (cx - 16, 24, cz), "out": (cx + 16, 24, cz)}


def pcie_switch(m, parent, name, x, z):
    g = empty(f"{name}_g", parent)
    join([bx(f"{name}_sub", (x - 14, 3.5, z - 14), (x + 14, 5.5, z + 14), m["sub"], g),
          bx(f"{name}_die", (x - 8, 5.5, z - 8), (x + 8, 7, z + 8), m["chip"], g),
          bx(f"{name}_nvme", (x + 20, 3.5, z - 12), (x + 30, 6, z + 12), m["dark"], g),
          bx(f"{name}_nvl", (x + 21, 6, z - 10), (x + 29, 6.6, z + 10), m["ink"], g)], f"{name}_chip")
    finned(m, g, f"{name}_sink", x - 14, x + 14, z - 14, z + 14, 7, 17, 7)
    return g, {"top": (x, 17, z), "nvme": (x + 25, 6.6, z)}


# ---- paths ----------------------------------------------------------------------------------

Y_TR = 4.6  # traces on the baseboard
Y_HT = 4.0  # traces on the host board


def nvl_edge(k, sw):
    gx, gz = gpu_xz(k)
    sxx = SWX[sw]
    sgn = -1.0 if gz > SWZ else 1.0  # front row leaves from its back edge
    ez = gz + sgn * 38.0
    return [(gx + (sxx - gx) * 0.12, Y_TR, ez), (gx + (sxx - gx) * 0.55, Y_TR, SWZ - sgn * 46.0),
            (sxx + (gx - sxx) * 0.15, Y_TR, SWZ - sgn * 23.0)]


def nvl_path(a, b, sw):
    """GPU a to GPU b through NVSwitch sw (0 left, 1 right)."""
    ga, gb = gpu_xz(a), gpu_xz(b)
    up = [(ga[0], 10.0, ga[1])] + nvl_edge(a, sw) + [(SWX[sw], 8.0, SWZ)]
    down = list(reversed(nvl_edge(b, sw))) + [(gb[0], 10.0, gb[1])]
    return up + down


def pcie_path(k):
    """GPU k down its column to its PCIe switch, across the host board to its NIC, out the cage."""
    gx, gz = gpu_xz(k)
    c = k % 4
    px = PX[c]
    nx = nic_of(k)
    pts = [(gx, 10.0, gz), (gx + 30.0, Y_TR, gz + 42.0)]
    if gz < SWZ:  # back row runs forward between the front GPUs
        pts += [(gx + 44.0, Y_TR, GZ[0] - 40.0), (gx + 44.0, Y_TR, GZ[0] + 44.0)]
    pts += [(px, Y_TR, -238.0), (px, 9.0, -222.0), (px, 9.0, -206.0), (px, 7.0, PZ),
            (nx, Y_HT, -100.0), (nx, Y_HT, -66.0), (nx, 8.0, -32.0), (nx, 12.8, 6.0)]
    return pts


def cpu_path(c):
    """CPU (left for columns 0-1, right for 2-3) to PCIe switch c."""
    cx = CPUX[0] if c < 2 else CPUX[1]
    return [(cx, 9.0, CPUZ), (cx + (PX[c] - cx) * 0.5, Y_HT, CPUZ - 46.0), (PX[c], Y_HT, PZ + 18.0), (PX[c], 7.0, PZ)]


def cable_path(nx, lx):
    """OSFP cage at nx out through a transceiver, forward and up to the leaf's port at lx."""
    return [(nx, 12.8, 18.0), (nx, 12.8, 44.0), (nx + (lx - nx) * 0.3, 70.0, 66.0), (lx, LEAF[2] - 2.0, 64.0)]


def fe_path(dx, i):
    zx = FE[0] + 10.0 + 14.0 * i
    return [(dx, 12.8, 18.0), (dx, 14.0, 34.0), (dx + 60.0, 30.0, 40.0 + 4.0 * i), (zx, FE[2] - 2.0, 50.0)]


def leaf_x(n):
    return -196.0 + 56.0 * n


def coolant_path(k):
    gx, gz = gpu_xz(k)
    return [(gx - 28.0, SUP_Y, HDR_Z), (gx - 28.0, SUP_Y, gz), (gx - 28.0, CP_TOP + 2.0, gz), (gx - 28.0, 18.0, gz),
            (gx + 28.0, 18.0, gz), (gx + 28.0, CP_TOP + 2.0, gz), (gx + 28.0, RET_Y, gz), (gx + 28.0, RET_Y, HDR_Z - 8.0)]


def rack_supply_path():
    return [(-40.0, 180.0, -620.0), (-40.0, SUP_Y, -620.0), (-40.0, SUP_Y, HDR_Z), (-150.0, SUP_Y, HDR_Z)]


def rack_return_path():
    return [(150.0, RET_Y, HDR_Z - 8.0), (40.0, RET_Y, HDR_Z - 8.0), (40.0, RET_Y, -630.0), (40.0, 180.0, -630.0)]


# ---- the whole node -------------------------------------------------------------------------


def scene(m, root, cut=True, rails=True, out=True):
    """The node. Returns a dict of groups (for show/present) and named points (for tags)."""
    s = {"gpu": {}, "glow": [], "nic": {}, "leds": [], "dpu": {}}
    body = empty("srv_body", root)
    # chassis: floor, low side walls, rear wall (front left open)
    join([bx("ch_floor", (CH[0], -5.0, CH[2]), (CH[1], 0.0, CH[3]), m["floor"], body),
          bx("ch_wl", (CH[0] - 4.0, -5.0, CH[2]), (CH[0], 34.0, CH[3]), m["chassis"], body),
          bx("ch_wr", (CH[1], -5.0, CH[2]), (CH[1] + 4.0, 34.0, CH[3]), m["chassis"], body),
          bx("ch_wb", (CH[0], -5.0, CH[2] - 4.0), (CH[1], 34.0, CH[2]), m["chassis"], body)], "chassis")
    # boards
    bx("gpu_board", (GB[0], 0.0, GB[2]), (GB[1], 4.0, GB[3]), m["pcb"], body)
    bx("host_board", (HB[0], 0.0, HB[2]), (HB[1], 3.5, HB[3]), m["pcb_host"], body)
    # GPUs
    gg = empty("gpus", root)
    for k in range(8):
        gx, gz = gpu_xz(k)
        g, glow, pts = gpu(m, gg, f"gpu{k}", gx, gz, cut_open=(cut and k == 0))
        s["gpu"][k] = pts
        s["glow"].append(glow)
    # NVSwitch and NVLink traces
    s["sw"] = []
    for i, x in enumerate(SWX):
        g, pts = nvswitch(m, body, f"nvsw{i}", x, SWZ)
        s["sw"].append(pts)
    tr = empty("nvl_traces", body)
    for k in range(8):
        for sw in (0, 1):
            e = nvl_edge(k, sw)
            gx, gz = gpu_xz(k)
            for j in range(-1, 2):
                off = j * 3.0
                polyline(f"nvl_{k}_{sw}_{j}", [(p[0] + off, 4.3, p[2]) for p in e], 0.7, m["trace"], tr)
    # baseboard-to-host cables (MCIO) and connectors
    for c, px in enumerate(PX):
        bx(f"mcio_a{c}", (px - 12, 4.0, -246.0), (px + 12, 11.0, -236.0), m["dark"], body)
        bx(f"mcio_b{c}", (px - 12, 3.5, -205.0), (px + 12, 10.0, -197.0), m["dark"], body)
        for j in range(3):
            polyline(f"mcio_c{c}{j}", arc((px - 6 + 6 * j, 10.0, -241.0), (px - 6 + 6 * j, 9.0, -201.0), 14.0, 8), 1.6, m["ribbon"], body)
    # host: CPUs, PCIe switches, cards
    s["cpu"] = [cpu(m, body, f"cpu{i}", x, CPUZ)[1] for i, x in enumerate(CPUX)]
    s["psw"] = [pcie_switch(m, body, f"psw{c}", x, PZ)[1] for c, x in enumerate(PX)]
    for i, nx in enumerate(NIC_X):
        g, leds, pts = nic(m, body, f"nic{i}", nx)
        s["nic"][i] = pts
        s["leds"] += leds
    for i, dx in enumerate(DPU_X):
        g, leds, pts = nic(m, body, f"dpu{i}", dx, dpu=True)
        s["dpu"][i] = pts
        s["leds"] += leds
    # host traces: CPU to switches, switch to NICs
    ht = empty("host_traces", body)
    for c in range(4):
        cp = cpu_path(c)
        polyline(f"ht_cpu{c}", [(p[0], 3.7, p[2]) for p in cp[:3]], 0.9, m["trace"], ht)
        for r in range(2):
            pp = pcie_path(gpu_index(r, c))
            polyline(f"ht_nic{c}{r}", [(p[0], 3.7, p[2]) for p in pp[7:10]], 0.9, m["trace"], ht)
    # coolant: headers, rails, drops, quick disconnects, rack manifold
    cool = empty("coolant", root)
    s["cool"] = cool
    polyline("hdr_s", [(-200.0, SUP_Y, HDR_Z), (200.0, SUP_Y, HDR_Z)], 5.0, m["tube_s"], cool)
    polyline("hdr_r", [(-200.0, RET_Y, HDR_Z - 8.0), (200.0, RET_Y, HDR_Z - 8.0)], 5.0, m["tube_r"], cool)
    for c, gx in enumerate(GX):
        polyline(f"rail_s{c}", [(gx - 28.0, SUP_Y, HDR_Z), (gx - 28.0, SUP_Y, GZ[0])], 3.2, m["tube_s"], cool)
        polyline(f"rail_r{c}", [(gx + 28.0, RET_Y, HDR_Z - 8.0), (gx + 28.0, RET_Y, GZ[0])], 3.2, m["tube_r"], cool)
        for gz in GZ:
            polyline(f"drop_s{c}{gz}", [(gx - 28.0, SUP_Y, gz), (gx - 28.0, CP_TOP + 5.0, gz)], 2.6, m["tube_s"], cool)
            polyline(f"drop_r{c}{gz}", [(gx + 28.0, RET_Y, gz), (gx + 28.0, CP_TOP + 5.0, gz)], 2.6, m["tube_r"], cool)
    for sd, mt in ((-1, "tube_s"), (1, "tube_r")):
        zz = -620.0 if sd < 0 else -630.0
        yy = SUP_Y if sd < 0 else RET_Y
        hz = HDR_Z if sd < 0 else HDR_Z - 8.0
        polyline(f"qd_line{sd}", [(sd * 40.0, yy, hz), (sd * 40.0, yy, zz)], 4.0, m[mt], cool)
        tube(f"qd{sd}", (sd * 40.0, yy, CH[2] - 6.0), (sd * 40.0, yy, CH[2] - 18.0), 6.5, m["qd"], cool, 16)
        polyline(f"manifold{sd}", [(sd * 40.0, -80.0, zz), (sd * 40.0, 200.0, zz)], 9.0, m[mt], cool)
    # CPU cold plate loops to the headers along the side walls
    for i, cx in enumerate(CPUX):
        sd = -1 if cx < 0 else 1
        polyline(f"cpu_s{i}", [(cx - 16, 24, CPUZ), (cx - 16, SUP_Y - 4, CPUZ), (sd * 248.0, SUP_Y - 4, CPUZ),
                               (sd * 248.0, SUP_Y - 4, HDR_Z), (sd * 200.0, SUP_Y, HDR_Z)], 2.4, m["tube_s"], cool)
        polyline(f"cpu_r{i}", [(cx + 16, 24, CPUZ), (cx + 16, RET_Y + 4, CPUZ), (sd * 254.0, RET_Y + 4, CPUZ),
                               (sd * 254.0, RET_Y + 4, HDR_Z - 8.0), (sd * 200.0, RET_Y, HDR_Z - 8.0)], 2.4, m["tube_r"], cool)
    # out of the node: transceivers, cables, the leaf (or rails) and the front-end switch
    outg = empty("out", root)
    s["out"] = outg
    for i, nx in enumerate(NIC_X + DPU_X):
        n = 2 if i >= 8 else 1
        for j in range(n):
            px = s["dpu"][i - 8]["ports"][j][0] if i >= 8 else nx
            bx(f"xcvr{i}{j}", (px - 7.5, 8.5, 6.0), (px + 7.5, 17.0, 20.0), m["alu"], outg)
            bx(f"pull{i}{j}", (px - 2.0, 11.5, 20.0), (px + 2.0, 13.5, 28.0), m["fiber_aqua"], outg)
    leaf = empty("leaf", root)
    s["leaf"] = leaf
    lx0, lx1, ly0, ly1, lz0, lz1 = LEAF
    join([bx("leaf_box", (lx0, ly0, lz0), (lx1, ly1, lz1), m["switch"], leaf)]
         + [bx(f"leaf_p{i}", (lx0 + 14 + 13.6 * i, ly0 + 8, lz1), (lx0 + 24 + 13.6 * i, ly0 + 18, lz1 + 0.8), m["port"], leaf) for i in range(32)]
         + [bx(f"leaf_q{i}", (lx0 + 14 + 13.6 * i, ly0 + 21, lz1), (lx0 + 24 + 13.6 * i, ly0 + 31, lz1 + 0.8), m["port"], leaf) for i in range(32)],
         "leaf_body")
    s["leaf_leds"] = []
    for i in range(0, 32, 2):
        lg = empty(f"leaf_led{i}", leaf)
        bx(f"leaf_ledm{i}", (lx0 + 16 + 13.6 * i, ly0 + 18.5, lz1), (lx0 + 20 + 13.6 * i, ly0 + 20.5, lz1 + 1.2), m["led"], lg)
        s["leaf_leds"].append(lg)
    for i, nx in enumerate(NIC_X):
        polyline(f"cab{i}", cable_path(nx, leaf_x(i)), 1.6, m["fiber"], leaf)
    fe = empty("fe", root)
    s["fe"] = fe
    fx0, fx1, fy0, fy1, fz0, fz1 = FE
    join([bx("fe_box", (fx0, fy0, fz0), (fx1, fy1, fz1), m["switch"], fe)]
         + [bx(f"fe_p{i}", (fx0 + 6 + 10 * i, fy0 + 10, fz1), (fx0 + 13 + 10 * i, fy0 + 20, fz1 + 0.8), m["port"], fe) for i in range(8)], "fe_body")
    for i, dx in enumerate(DPU_X):
        for j in range(2):
            px = s["dpu"][i]["ports"][j][0]
            polyline(f"fecab{i}{j}", fe_path(px, 2 * i + j), 1.4, m["fiber_aqua"], fe)
    if rails:
        rg = empty("rails", root)
        s["rails"] = rg
        for n in range(8):
            x = leaf_x(n)
            join([bx(f"rail{n}", (x - 24, ly0, lz0), (x + 24, ly1, lz1), m["switch"], rg)]
                 + [bx(f"rail{n}_p{i}", (x - 20 + 10 * i, ly0 + 12, lz1), (x - 13 + 10 * i, ly0 + 22, lz1 + 0.8), m["port"], rg) for i in range(4)],
                 f"rail{n}_body")
            polyline(f"rcab{n}", cable_path(NIC_X[n], x), 1.6, m["fiber"], rg)
        for sd in (-1, 1):
            g = empty(f"nbr{sd}", rg)
            x0, x1 = (-900.0, -420.0) if sd < 0 else (420.0, 900.0)
            join([bx(f"nbr{sd}_b", (x0, -5.0, -600.0), (x1, 30.0, 0.0), m["ghost"], g)]
                 + [bx(f"nbr{sd}_c{i}", (x0 + 30 + 56 * i, 6.0, 0.0), (x0 + 44 + 56 * i, 19.0, 10.0), m["alu"], g) for i in range(8)], f"nbr{sd}_body")
            for n in range(8):
                nx = x0 + 37 + 56 * n
                polyline(f"nbr{sd}_cab{n}", [(nx, 12.8, 10.0), (nx, 20.0, 40.0), (nx + (leaf_x(n) - nx) * 0.5, 150.0, 70.0), (leaf_x(n) + sd * 10.0, LEAF[2] - 2.0, 60.0)],
                          1.2, m["fiber"], g)
    s["body"] = body
    s["gpus"] = gg
    return s


def node_bounds():
    return (CH[0], CH[1], CH[2], CH[3])
