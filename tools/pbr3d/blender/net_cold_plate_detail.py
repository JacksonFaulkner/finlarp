"""Part builders for the NETWORK+COOL tab's COLD PLATE page (net_cold_plate_*.py): direct-to-chip
liquid cooling.

One GPU compute tray, drawn about 3x life size and cut through the middle of the GPU along z = 0
(the camera sits on +z), so the cut face shows the stack: board, package, die and HBM, thermal
interface (TIM), the copper cold plate base, its microchannel fins and the nickel cover. Units as
everywhere (docs/diagram-pages.md): Y up, x across the tray, z toward the camera.

  tray        the board, the GPU package (two dies, HBM stacks), regulator blocks beside it
  plate       TIM, copper base, skived microchannel fins (channels run along z), cover with a
              centre inlet slot above the dies and an outlet plenum at the back; spring screws
  hoses       inlet (cool, x = -30) and outlet (warm, x = +30) hoses running back to the tray's
              rear edge
  qd          blind-mate quick disconnects at the rear: tray halves (on the tray group) and
              manifold halves, with blue / red collars
  manifold    the rack's supply and return manifolds (vertical pipes behind the tray) with stubs
              to dummy trays above and below

Coolant is beads riding real paths (`run` from power_vrm_detail): blue going in, orange coming
out. Heat is orange beads rising on the cut face. `fin_bench`, `tim_bench` and `qd_bench` draw
one sub-part far larger for the sections.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, empty, fly, key, show, tube, mat  # noqa: E402,F401
import power_vrm_detail as V  # noqa: E402
from power_vrm_detail import bead, bx, join, polyline, run, rise, present, blink, frame, camera_path  # noqa: E402,F401

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "mask": mat("cp_mask", (0.07, 0.30, 0.16), rough=0.55),
        "fr4": mat("cp_fr4", (0.55, 0.47, 0.30), rough=0.8),
        "substrate": mat("cp_substrate", (0.40, 0.26, 0.15), rough=0.75),
        "solder": mat("cp_solder", (0.74, 0.76, 0.80), metal=0.9, rough=0.25),
        "silicon": mat("cp_silicon", (0.42, 0.44, 0.50), metal=0.6, rough=0.3),
        "die": mat("cp_die", (0.26, 0.20, 0.42), metal=0.4, rough=0.3),
        "hbm": mat("cp_hbm", (0.20, 0.34, 0.62), metal=0.4, rough=0.35),
        "tim": mat("cp_tim", (0.80, 0.82, 0.86), metal=0.7, rough=0.45),
        "copper": mat("cp_copper", (0.85, 0.47, 0.26), metal=0.92, rough=0.28),
        "fin": mat("cp_fin", (0.92, 0.55, 0.32), metal=0.92, rough=0.24),
        "nickel": mat("cp_nickel", (0.62, 0.64, 0.68), metal=0.85, rough=0.32),
        "steel": mat("cp_steel", (0.70, 0.72, 0.76), metal=0.9, rough=0.25),
        "hose": mat("cp_hose", (0.08, 0.08, 0.09), rough=0.7),
        "blue": mat("cp_blue", (0.10, 0.32, 0.85), metal=0.3, rough=0.4),
        "red": mat("cp_red", (0.80, 0.16, 0.10), metal=0.3, rough=0.4),
        "pipe_s": mat("cp_pipe_s", (0.20, 0.38, 0.75), metal=0.6, rough=0.35),
        "pipe_r": mat("cp_pipe_r", (0.70, 0.30, 0.20), metal=0.6, rough=0.35),
        "dark": mat("cp_dark", (0.16, 0.17, 0.20), metal=0.5, rough=0.5),
        "mold": mat("cp_mold", (0.07, 0.07, 0.08), rough=0.6),
        "ferrite": mat("cp_ferrite", (0.22, 0.22, 0.24), rough=0.7),
        "frame": mat("cp_frame", (0.24, 0.26, 0.30), metal=0.6, rough=0.45),
        "tray": mat("cp_tray", (0.36, 0.38, 0.42), metal=0.7, rough=0.4),
        "air": mat("cp_air", (0.05, 0.05, 0.06), rough=0.9),
        "rubber": mat("cp_rubber", (0.12, 0.10, 0.10), rough=0.8),
        # glows
        "cool": mat("cp_cool", (0.30, 0.70, 1.0), emit=(0.22, 0.62, 1.0), strength=4.5),
        "warm": mat("cp_warm", (1.0, 0.55, 0.15), emit=(1.0, 0.48, 0.10), strength=4.5),
        "hotw": mat("cp_hotw", (1.0, 0.25, 0.10), emit=(1.0, 0.20, 0.06), strength=4.5),
        "heat": mat("cp_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=5.0),
        "die_hot": mat("cp_die_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=1.4),
        "chan": mat("cp_chan", (0.15, 0.40, 0.95), emit=(0.10, 0.35, 0.95), strength=0.9),
        "chan_w": mat("cp_chan_w", (0.95, 0.40, 0.10), emit=(0.95, 0.32, 0.06), strength=0.9),
        "led_g": mat("cp_led_g", (0.3, 1.0, 0.4), emit=(0.25, 1.0, 0.35), strength=5.0),
        "fail": mat("cp_fail", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=4.0),
        "drop": mat("cp_drop", (0.5, 0.8, 1.0), emit=(0.45, 0.75, 1.0), strength=3.0),
    }


# ---- layout ---------------------------------------------------------------------------------

BRD = (-180.0, 180.0, -5.0, 0.0, -180.0)  # x0, x1, y0, y1, back z
SUB_Y = (0.0, 5.0)
SUB_X = 62.0
DIE_Y = (5.0, 11.0)
DIES = ((-30.0, -1.0), (1.0, 30.0))
DIE_Z = -40.0
HBM_X = (34.0, 48.0)
TIM_Y = (11.0, 12.2)
BASE_Y = (12.2, 18.0)
FIN_Y = (18.0, 32.0)
COV_Y = (32.0, 40.0)
PL_X = 64.0  # plate half width
PL_Z = -80.0  # plate back
FIN_X = 46.0
FIN_PITCH = 3.4
FIN_T = 1.1
FIN_Z = (-62.0, 0.0)
SLOT_Z = (-14.0, -2.0)
OUT_Z = (-76.0, -62.0)  # outlet plenum (behind the fins)
HOSE_Y = 66.0
IN_X, OUT_X = -30.0, 30.0
QD_Z = (-200.0, -213.0, -226.0)  # tray half front, mating face, manifold half back
MAN_Z = -250.0
MAN_Y = (-170.0, 230.0)
TRAY_DY = 110.0  # dummy trays above and below


def fins_x():
    n = int(2 * FIN_X / FIN_PITCH)
    return [-FIN_X + FIN_PITCH * (k + 0.5) for k in range(n)]


def chan_x():
    """x centres of channels (between fins)."""
    xs = fins_x()
    return [(xs[k] + xs[k + 1]) / 2 for k in range(len(xs) - 1)]


# ---- parts ----------------------------------------------------------------------------------


def board(m, g):
    x0, x1, y0, y1, zb = BRD
    bx("brd_core", (x0, y0, zb), (x1, y1 - 0.8, 0.0), m["fr4"], g)
    bx("brd_mask", (x0, y1 - 0.8, zb), (x1, y1, 0.0), m["mask"], g)
    bx("tray_floor", (x0 - 12.0, y0 - 6.0, zb - 18.0), (x1 + 12.0, y0 - 2.0, 6.0), m["tray"], g)
    for s in (-1, 1):
        bx(f"tray_wall{s}", (s * (x1 + 8.0), y0 - 6.0, zb - 18.0), (s * (x1 + 12.0), 20.0, 6.0), m["tray"], g)


def package(m, g):
    """Package cut through its middle: balls, substrate, two dies, HBM. Returns points and the
    die glow (hidden)."""
    for k in range(13):
        x = -54.0 + 9.0 * k
        ball(f"bga{k}", (x, 0.0, -1.5), 1.6, m["solder"], g, 10)
    bx("substrate", (-SUB_X, SUB_Y[0] + 0.6, -62.0), (SUB_X, SUB_Y[1], 0.0), m["substrate"], g)
    bx("interposer", (-50.0, SUB_Y[1], -44.0), (50.0, SUB_Y[1] + 1.2, 0.0), m["silicon"], g)
    for i, (a, b) in enumerate(DIES):
        bx(f"die{i}", (a, SUB_Y[1] + 1.2, DIE_Z), (b, DIE_Y[1], 0.0), m["die"], g)
    for s in (-1, 1):
        for j in range(2):
            z0 = -40.0 + 21.0 * j
            bx(f"hbm{s}{j}", (s * HBM_X[0], SUB_Y[1] + 1.2, z0), (s * HBM_X[1], DIE_Y[1], z0 + 18.0), m["hbm"], g)
            for L in range(7):
                y = SUB_Y[1] + 2.0 + 1.25 * L
                bx(f"hbm_l{s}{j}{L}", (s * (HBM_X[0] + 0.6), y, z0 + 17.9), (s * (HBM_X[1] - 0.6), y + 0.35, z0 + 18.1),
                   m["copper"], g)
    glow = empty("die_glow", g)
    for i, (a, b) in enumerate(DIES):
        bx(f"die_glow{i}", (a + 0.5, DIE_Y[1] - 1.6, DIE_Z + 0.5), (b - 0.5, DIE_Y[1] - 0.2, 0.25), m["die_hot"], glow)
    return {"top": (0.0, DIE_Y[1], -20.0), "die_face": (-15.0, 8.0, 0.0), "hbm": (HBM_X[1], DIE_Y[1], -10.0),
            "sub": (-55.0, 3.0, 0.0)}, glow


def vrms(m, g):
    for s in (-1, 1):
        for k in range(4):
            z = -12.0 - 22.0 * k
            bx(f"vrm_st{s}{k}", (s * 80.0, 0.0, z - 6.0), (s * 92.0, 3.0, z + 6.0), m["mold"], g)
            bx(f"vrm_in{s}{k}", (s * 98.0, 0.0, z - 8.0), (s * 116.0, 12.0, z + 8.0), m["ferrite"], g)


def plate(m, g):
    """TIM, base, fins, cover with inlet slot and outlet plenum, spring screws, barbs. Returns
    points and the channel glows (cool / warm, hidden)."""
    bx("tim", (-50.0, TIM_Y[0], -44.0), (50.0, TIM_Y[1], 0.0), m["tim"], g)
    bx("base", (-PL_X, BASE_Y[0], PL_Z), (PL_X, BASE_Y[1], 0.0), m["copper"], g)
    fins = [bx(f"fin{k}", (x - FIN_T / 2, FIN_Y[0], FIN_Z[0]), (x + FIN_T / 2, FIN_Y[1], FIN_Z[1]), m["fin"], g)
            for k, x in enumerate(fins_x())]
    join(fins, "fins")
    # cover: side walls, back wall beyond the plenum, top with slot cut over the dies
    for s in (-1, 1):
        bx(f"cov_side{s}", (s * (FIN_X + 0.6), FIN_Y[0], PL_Z), (s * PL_X, COV_Y[0], 0.0), m["nickel"], g)
    bx("cov_back", (-PL_X, FIN_Y[0], PL_Z), (PL_X, COV_Y[0], OUT_Z[0]), m["nickel"], g)
    bx("cov_top_a", (-PL_X, COV_Y[0], PL_Z), (PL_X, COV_Y[1], SLOT_Z[0]), m["nickel"], g)
    bx("cov_top_b", (-PL_X, COV_Y[0], SLOT_Z[1]), (PL_X, COV_Y[1], 0.0), m["nickel"], g)
    for s in (-1, 1):
        bx(f"slot_side{s}", (s * 20.0, COV_Y[0], SLOT_Z[0]), (s * PL_X, COV_Y[1], SLOT_Z[1]), m["nickel"], g)
    # inlet riser above the slot, outlet barb above the plenum
    tube("in_riser", (0.0, COV_Y[1], -8.0), (0.0, HOSE_Y, -8.0), 5.5, m["nickel"], g, 20)
    tube("out_riser", (OUT_X, COV_Y[1], -69.0), (OUT_X, HOSE_Y, -69.0), 5.5, m["nickel"], g, 20)
    # spring screws at the corners
    for i, (x, z) in enumerate(((-58.0, -74.0), (58.0, -74.0), (-58.0, -6.0), (58.0, -6.0))):
        tube(f"screw{i}", (x, 0.0, z), (x, COV_Y[1] + 9.0, z), 1.6, m["steel"], g, 10)
        tube(f"cap{i}", (x, COV_Y[1] + 7.0, z), (x, COV_Y[1] + 10.0, z), 3.6, m["steel"], g, 16)
        coil = [(x + 2.6 * V.math.cos(t * 0.6), COV_Y[1] + 0.3 + 0.28 * t, z + 2.6 * V.math.sin(t * 0.6)) for t in range(24)]
        polyline(f"spring{i}", coil, 0.45, m["steel"], g)
    ch = empty("chan_cool", g)
    cw = empty("chan_warm", g)
    for k, x in enumerate(chan_x()):
        bx(f"chc{k}", (x - 0.7, FIN_Y[0] + 0.3, -1.0), (x + 0.7, FIN_Y[1] - 0.3, 0.15), m["chan"], ch)
        bx(f"chw{k}", (x - 0.7, FIN_Y[0] + 0.3, -1.0), (x + 0.7, FIN_Y[1] - 0.3, 0.15), m["chan_w"], cw)
    return {"tim": (-40.0, TIM_Y[1], 0.0), "base": (-PL_X + 6.0, BASE_Y[1], 0.0), "fins": (-20.0, FIN_Y[1], 0.0),
            "cover": (40.0, COV_Y[1], -40.0), "slot": (0.0, COV_Y[1], -8.0), "plenum": (OUT_X, COV_Y[0], -70.0),
            "spring": (58.0, COV_Y[1] + 10.0, -6.0), "inlet": (0.0, HOSE_Y, -8.0), "outlet": (OUT_X, HOSE_Y, -69.0)}, ch, cw


def hoses(m, g):
    pin = [(0.0, HOSE_Y, -8.0), (0.0, HOSE_Y + 6.0, -14.0), (IN_X, HOSE_Y + 6.0, -40.0), (IN_X, HOSE_Y + 6.0, QD_Z[0])]
    pout = [(OUT_X, HOSE_Y, -69.0), (OUT_X, HOSE_Y + 6.0, -80.0), (OUT_X, HOSE_Y + 6.0, QD_Z[0])]
    polyline("hose_in", pin, 4.2, m["hose"], g)
    polyline("hose_out", pout, 4.2, m["hose"], g)
    for x, mt in ((IN_X, "blue"), (OUT_X, "red")):
        tube(f"band{x}", (x, HOSE_Y + 6.0, -120.0), (x, HOSE_Y + 6.0, -126.0), 4.6, m[mt], g, 16)
    return pin, pout


QY = HOSE_Y + 6.0


def qd_tray(m, g):
    """Tray halves of the two quick disconnects (on the tray, they slide with it)."""
    for x, mt in ((IN_X, "blue"), (OUT_X, "red")):
        tube(f"qdt_body{x}", (x, QY, QD_Z[0]), (x, QY, QD_Z[1] + 2.0), 6.0, m["steel"], g, 24)
        tube(f"qdt_col{x}", (x, QY, QD_Z[0] - 2.0), (x, QY, QD_Z[0] - 5.0), 7.2, m[mt], g, 24)
        tube(f"qdt_nose{x}", (x, QY, QD_Z[1] + 2.0), (x, QY, QD_Z[1]), 4.2, m["steel"], g, 20)
    bx("qd_plate", (-48.0, QY - 12.0, QD_Z[0] + 2.0), (48.0, QY + 12.0, QD_Z[0] + 5.0), m["frame"], g)


def qd_rack(m, g, y=QY, name="qdr"):
    for x, mt in ((IN_X, "blue"), (OUT_X, "red")):
        tube(f"{name}_body{x}", (x, y, QD_Z[1]), (x, y, QD_Z[2]), 6.8, m["steel"], g, 24)
        tube(f"{name}_col{x}", (x, y, QD_Z[2] + 3.0), (x, y, QD_Z[2] + 7.0), 7.8, m[mt], g, 24)
        tube(f"{name}_stub{x}", (x, y, QD_Z[2]), (x, y, MAN_Z), 3.4, m["pipe_s" if x < 0 else "pipe_r"], g, 16)


def manifold(m, g):
    for x, mt in ((IN_X, "pipe_s"), (OUT_X, "pipe_r")):
        tube(f"man{x}", (x, MAN_Y[0], MAN_Z), (x, MAN_Y[1], MAN_Z), 8.0, m[mt], g, 24)
    for s in (-1, 1):
        bx(f"post{s}", (s * 196.0, MAN_Y[0], MAN_Z - 14.0), (s * 204.0, MAN_Y[1], MAN_Z - 6.0), m["frame"], g)
    # dummy trays above and below, each with its own QDs and lit status LED
    o = empty("others", g)
    leds = []
    for j, dy in enumerate((-TRAY_DY, TRAY_DY, 2 * TRAY_DY - 20.0)):
        y = BRD[2] + dy
        bx(f"dtray{j}", (BRD[0] - 12.0, y - 6.0, BRD[4] - 18.0), (BRD[1] + 12.0, y + 44.0, 6.0), m["tray"], o)
        bx(f"dtray_lid{j}", (BRD[0] - 10.0, y + 44.0, BRD[4] - 16.0), (BRD[1] + 10.0, y + 46.0, 4.0), m["frame"], o)
        qd_rack(m, o, QY + dy, f"dq{j}")
        for x in (IN_X, OUT_X):
            tube(f"dq_t{j}{x}", (x, QY + dy, QD_Z[0] + 4.0), (x, QY + dy, QD_Z[1]), 6.0, m["steel"], o, 20)
        le = empty(f"dled{j}", o)
        bx(f"dled{j}_b", (150.0, y + 30.0, 6.0), (158.0, y + 34.0, 7.0), m["led_g"], le)
        leds.append(le)
    # the CDU feed at the bottom
    bx("cdu_box", (-90.0, MAN_Y[0] - 40.0, MAN_Z - 40.0), (90.0, MAN_Y[0], MAN_Z + 30.0), m["dark"], g)
    return leds, o


def man_supply(y_qd=QY):
    """Supply: up the supply manifold from the CDU, then out the stub to a tray's QD."""
    return [(IN_X, MAN_Y[0] - 10.0, MAN_Z), (IN_X, y_qd, MAN_Z), (IN_X, y_qd, QD_Z[2]), (IN_X, y_qd, QD_Z[0])]


def man_return(y_qd=QY):
    return [(OUT_X, y_qd, QD_Z[0]), (OUT_X, y_qd, QD_Z[2]), (OUT_X, y_qd, MAN_Z), (OUT_X, MAN_Y[1] - 10.0, MAN_Z)]


def plate_paths():
    """Cool water down the inlet riser into the slot; along each channel toward the back (cool,
    then warm halves); up through the plenum to the outlet riser."""
    zin = 0.7  # ride the cut face so the beads read
    down = [(0.0, HOSE_Y, -8.0), (0.0, COV_Y[0] + 2.0, -8.0)]
    chans = {}
    for x in chan_x()[::3]:
        y = (FIN_Y[0] + FIN_Y[1]) / 2
        chans[x] = ([(x * 0.3, COV_Y[0] - 1.0, -8.0), (x, y, -6.0), (x, y, -34.0)], [(x, y, -34.0), (x, y, -64.0), (OUT_X, COV_Y[0] - 2.0, -69.0)])
    up = [(OUT_X, COV_Y[0], -69.0), (OUT_X, HOSE_Y, -69.0)]
    face = [[(x, FIN_Y[0] + 1.0, zin), (x, FIN_Y[1] - 1.0, zin)] for x in chan_x()[1::4]]
    return {"down": down, "chans": chans, "up": up, "face": face}


def scene(m, root):
    """The tray with plate, hoses and tray-side QDs (group 'tray', which can slide), plus the rack
    manifold, rack QDs and dummy trays. Returns a dict of groups and points."""
    tray = empty("tray", root)
    board(m, tray)
    pk, glow = package(m, tray)
    vrms(m, tray)
    pp, ch, cw = plate(m, tray)
    pin, pout = hoses(m, tray)
    qd_tray(m, tray)
    show(glow, [])
    show(ch, [])
    show(cw, [])
    rack = empty("rack", root)
    qd_rack(m, rack)
    leds, others = manifold(m, rack)
    present(others, [])
    led = empty("led", tray)
    bx("led_b", (150.0, 6.0, 6.0), (158.0, 10.0, 7.0), m["led_g"], led)
    return {"tray": tray, "pkg": pk, "die_glow": glow, "plate": pp, "chan_cool": ch, "chan_warm": cw, "pin": pin, "pout": pout,
            "leds": leds + [led], "others": others, "qd": (0.0, QY, QD_Z[1]), "man": (IN_X, 150.0, MAN_Z), "cdu": (0.0, MAN_Y[0] - 20.0, MAN_Z + 30.0)}


# ---- flows (shared by overview, zooms, sections) --------------------------------------------


def flow_in(m, root, beats, u0=0.0, u1=0.8, n=6):
    run(root, "f_sup", man_supply(), n, 2.0, m["cool"], beats, u0, u1, 70)
    pin = hoses_in_path()
    run(root, "f_hin", pin, n, 2.0, m["cool"], beats, u0 + 0.08, u1, 80)


def hoses_in_path():
    return [(IN_X, QY, QD_Z[0]), (IN_X, QY, -40.0), (0.0, QY, -14.0), (0.0, HOSE_Y, -8.0)]


def hoses_out_path():
    return [(OUT_X, HOSE_Y, -69.0), (OUT_X, QY, -80.0), (OUT_X, QY, QD_Z[0])]


def flow_plate(m, root, beats, u0=0.0, u1=0.8, n=3):
    pp = plate_paths()
    run(root, "f_down", pp["down"], 4, 1.8, m["cool"], beats, u0, u1, 30)
    for i, (x, (a, b)) in enumerate(pp["chans"].items()):
        run(root, f"f_ca{i}", a, n, 1.2, m["cool"], beats, u0 + 0.05, u1, 40)
        run(root, f"f_cb{i}", b, n, 1.2, m["warm"], beats, u0 + 0.15, u1, 40)
    run(root, "f_up", pp["up"], 4, 1.8, m["warm"], beats, u0 + 0.2, u1, 30)


def flow_out(m, root, beats, u0=0.0, u1=0.8, n=6):
    run(root, "f_hout", hoses_out_path(), n, 2.0, m["warm"], beats, u0, u1, 80)
    run(root, "f_ret", man_return(), n, 2.0, m["hotw"], beats, u0 + 0.08, u1, 90)


def heat_up(m, root, beats, u0=0.05, u1=0.85, n=8, name="h"):
    """Heat climbing from the dies through TIM and base into the fins, on the cut face."""
    for i, x in enumerate((-22.0, -9.0, 9.0, 22.0)):
        rise(root, f"{name}{i}", (x, DIE_Y[1] - 0.5, 0.8), n // 4 + 1, 0.9, m["heat"], beats, u0 + 0.03 * i, u1, FIN_Y[1] - DIE_Y[1] - 2.0, 50, (3.0, 0.0))


def rack_flows(m, root, beats, u0=0.0, u1=0.8):
    for j, dy in enumerate((-TRAY_DY, TRAY_DY, 2 * TRAY_DY - 20.0)):
        y = QY + dy
        run(root, f"rs{j}", [(IN_X, MAN_Y[0] - 10.0, MAN_Z), (IN_X, y, MAN_Z), (IN_X, y, QD_Z[1])], 3, 1.8, m["cool"], beats, u0 + 0.04 * j, u1, 70)
        run(root, f"rr{j}", [(OUT_X, y, QD_Z[1]), (OUT_X, y, MAN_Z), (OUT_X, MAN_Y[1] - 10.0, MAN_Z)], 3, 1.8, m["hotw"], beats, u0 + 0.1 + 0.04 * j, u1, 70)


def slide(tray, b, out=60.0):
    """Pull the tray out toward the camera in beat b (QDs part), push it back by the beat's end."""
    key(tray, 0, "location", P(0.0, 0.0, 0.0), linear=True)
    key(tray, F(b, 0.1), "location", P(0.0, 0.0, 0.0), linear=True)
    key(tray, F(b, 0.4), "location", P(0.0, 0.0, out), linear=True)
    key(tray, F(b, 0.65), "location", P(0.0, 0.0, out), linear=True)
    key(tray, F(b, 0.92), "location", P(0.0, 0.0, 0.0), linear=True)


# ---- benches (sections): one part drawn large ----------------------------------------------

BY = 320.0


def fin_bench(m, parent, name="fb"):
    """A slice of base and fins, 5x: fins 1 unit apart become 5; channels between. Returns the
    group, channel x list and points."""
    g = empty(name, parent)
    s = 5.0
    bx(f"{name}_base", (-60.0, BY, -60.0), (60.0, BY + 6.0 * s * 0.5, 0.0), m["copper"], g)
    y0 = BY + 15.0
    xs = [-54.0 + 9.0 * k for k in range(13)]
    fins = [bx(f"{name}_f{k}", (x - 2.0, y0, -60.0), (x + 2.0, y0 + 45.0, 0.0), m["fin"], g) for k, x in enumerate(xs)]
    join(fins, f"{name}_fins")
    bx(f"{name}_cov", (-60.0, y0 + 45.0, -60.0), (60.0, y0 + 52.0, 0.0), m["nickel"], g)
    bx(f"{name}_die", (-40.0, BY - 12.0, -60.0), (40.0, BY - 2.0, 0.0), m["die"], g)
    bx(f"{name}_tim", (-42.0, BY - 2.0, -60.0), (42.0, BY, 0.0), m["tim"], g)
    chans = [(xs[k] + xs[k + 1]) / 2 for k in range(len(xs) - 1)]
    return g, chans, {"fin": (xs[3], y0 + 45.0, 0.0), "chan": (chans[6], y0 + 22.0, 0.0), "base": (-50.0, BY + 15.0, 0.0),
                      "cov": (30.0, y0 + 52.0, -30.0), "y0": y0, "die": (-30.0, BY - 7.0, 0.0)}


def tim_bench(m, parent, name="tb"):
    """Die top and plate bottom, 20x, with their roughness; air voids (hidden group) and a TIM
    layer (hidden group)."""
    g = empty(name, parent)
    bx(f"{name}_die", (-70.0, BY - 30.0, -40.0), (70.0, BY, 0.0), m["die"], g)
    bx(f"{name}_cu", (-70.0, BY + 12.0, -40.0), (70.0, BY + 40.0, 0.0), m["copper"], g)
    for k in range(14):
        x = -65.0 + 10.0 * k
        h1 = 2.0 + 2.5 * abs(V.math.sin(1.3 * k))
        h2 = 2.0 + 2.5 * abs(V.math.cos(0.9 * k + 0.4))
        bx(f"{name}_pd{k}", (x - 3.5, BY, -40.0), (x + 3.5, BY + h1, 0.0), m["die"], g)
        bx(f"{name}_pc{k}", (x - 4.0, BY + 12.0 - h2, -40.0), (x + 4.0, BY + 12.0, 0.0), m["copper"], g)
    air = empty(f"{name}_air", g)
    for k in range(13):
        ball(f"{name}_a{k}", (-60.0 + 10.0 * k, BY + 6.0, 0.5), 2.4, m["air"], air, 10)
    tim = empty(f"{name}_tim", g)
    bx(f"{name}_t", (-70.0, BY + 0.2, -40.0), (70.0, BY + 11.8, 0.4), m["tim"], tim)
    return g, air, tim


def qd_bench(m, parent, name="qb"):
    """One quick disconnect cut open, 4x: two halves, each with a spring-loaded poppet (groups
    'pa' / 'pb' that can move), O-rings, the latch sleeve."""
    g = empty(name, parent)
    a = empty(f"{name}_a", g)  # tray half (left)
    b = empty(f"{name}_b", g)  # rack half (right)
    r = 22.0
    for side, grp, x0, x1, mt in ((-1, a, -90.0, -2.0, "blue"), (1, b, 2.0, 90.0, "steel")):
        # shell top and bottom walls (cut open: we see the bore)
        bx(f"{name}_w1{side}", (x0, BY + r - 5.0, -26.0), (x1, BY + r, 0.0), m["steel"], grp)
        bx(f"{name}_w2{side}", (x0, BY - r, -26.0), (x1, BY - r + 5.0, 0.0), m["steel"], grp)
        bx(f"{name}_bk{side}", (x0, BY - r, -26.0), (x1, BY + r, -24.0), m["steel"], grp)
        xc = (x0 + x1) / 2
        bx(f"{name}_col{side}", (xc - 10.0, BY + r, -26.0), (xc + 10.0, BY + r + 6.0, 0.0), m[mt if side < 0 else "red"], grp)
        for yy in (BY + r - 6.0, BY - r + 5.0):
            bx(f"{name}_or{side}{yy}", (side * 4.0, yy, -26.0), (side * 8.0, yy + 1.2, 0.2), m["rubber"], grp)
    pa = empty(f"{name}_pa", a)
    pb = empty(f"{name}_pb", b)
    for side, grp in ((-1, pa), (1, pb)):
        bx(f"{name}_pop{side}", (side * 2.0, BY - 12.0, -20.0), (side * 14.0, BY + 12.0, 0.1), m["nickel"], grp)
        coil = [(side * (14.0 + 1.6 * t), BY + 7.0 * V.math.sin(t * 0.9), 0.3) for t in range(26)]
        polyline(f"{name}_spr{side}", coil, 0.9, m["steel"], grp)
    return {"a": a, "b": b, "pa": pa, "pb": pb, "face": (0.0, BY + r + 6.0, 0.0), "pop": (-8.0, BY + 12.0, 0.0),
            "spring": (40.0, BY + 7.0, 0.0), "oring": (6.0, BY + r - 5.0, 0.0)}
