"""Part builders for the NETWORK+COOL tab's CDU page (net_cdu_*.py).

A coolant distribution unit (CDU) standing in a row beside the GPU rack it cools, both cut open
along their front faces (z = 0, the camera sits on +z). Units are centimetres; Y up, x across,
z toward the camera (docs/diagram-pages.md).

  cabinet     the in-row CDU, 60 cm wide and 2 m tall, its front panel removed:
                plate heat exchanger (PHE)   a stack of stainless plates between two frame plates,
                                             tie bolts at the corners; the facility loop and the
                                             secondary loop run through alternate gaps, counterflow
                pumps A and B                redundant (N+1) centrifugal pumps on a common suction
                                             header; A runs, B stands by; A's volute is cut open
                filter                       a canister strainer on the pump discharge, cut open
                reservoir                    the expansion tank that takes up the coolant's swell
                control valve                a two-way valve on the facility supply, its actuator
                sensors                      temperature, pressure and flow points on each pipe
                controller                   a PLC with a touch screen at the top of the door frame
  facility    the facility water loop rising out of the floor into the PHE and back down
  rack        a liquid-cooled rack: eight trays with copper cold plates, supply and return
              manifolds at the back with a quick disconnect at every tap
  inrack      an in-rack CDU (4U, at the bottom of the rack) with its own small PHE and pumps
  row         three more racks to the right, for the in-row CDU that feeds a whole row

Beads ride the pipes (`run` from power_vrm_detail): facility water is blue, the secondary supply
cyan, the secondary return orange. Heat rises off the GPUs and hops across the PHE's plates.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, cut, empty, key, show, tube, mat, disc  # noqa: E402
import power_vrm_detail as V  # noqa: E402
from power_vrm_detail import bx, join, polyline, bead, run, rise, present, blink, frame, camera_path  # noqa: E402,F401

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "panel": mat("cdu_panel", (0.18, 0.19, 0.22), metal=0.5, rough=0.45),
        "panel_lt": mat("cdu_panel_lt", (0.55, 0.57, 0.60), metal=0.6, rough=0.35),
        "frame": mat("cdu_frame", (0.10, 0.10, 0.12), metal=0.4, rough=0.5),
        "steel": mat("cdu_steel", (0.62, 0.64, 0.68), metal=0.9, rough=0.25),
        "plate_a": mat("cdu_plate_a", (0.70, 0.72, 0.76), metal=0.9, rough=0.22),
        "plate_b": mat("cdu_plate_b", (0.50, 0.53, 0.58), metal=0.9, rough=0.3),
        "pheframe": mat("cdu_pheframe", (0.12, 0.26, 0.48), metal=0.4, rough=0.45),
        "bolt": mat("cdu_bolt", (0.80, 0.80, 0.82), metal=0.95, rough=0.2),
        "pump": mat("cdu_pump", (0.10, 0.32, 0.55), metal=0.5, rough=0.4),
        "motor": mat("cdu_motor", (0.22, 0.24, 0.27), metal=0.6, rough=0.4),
        "impeller": mat("cdu_impeller", (0.78, 0.62, 0.32), metal=0.9, rough=0.3),
        "filter": mat("cdu_filter", (0.75, 0.76, 0.78), metal=0.8, rough=0.3),
        "mesh": mat("cdu_mesh", (0.86, 0.84, 0.70), rough=0.8),
        "tank": mat("cdu_tank", (0.80, 0.82, 0.86), metal=0.7, rough=0.3),
        "fluid": mat("cdu_fluid", (0.20, 0.70, 0.80), emit=(0.15, 0.65, 0.80), strength=1.0),
        "valve": mat("cdu_valve", (0.62, 0.18, 0.12), metal=0.5, rough=0.4),
        "actuator": mat("cdu_actuator", (0.85, 0.66, 0.15), rough=0.5),
        "screen": mat("cdu_screen", (0.15, 0.45, 0.60), emit=(0.15, 0.50, 0.70), strength=1.2),
        "plc": mat("cdu_plc", (0.85, 0.86, 0.88), rough=0.5),
        "pipe_fac": mat("cdu_pipe_fac", (0.10, 0.25, 0.65), metal=0.5, rough=0.35),
        "pipe_sup": mat("cdu_pipe_sup", (0.10, 0.55, 0.62), metal=0.5, rough=0.35),
        "pipe_ret": mat("cdu_pipe_ret", (0.68, 0.30, 0.12), metal=0.5, rough=0.35),
        "hose": mat("cdu_hose", (0.06, 0.06, 0.07), rough=0.7),
        "qd": mat("cdu_qd", (0.80, 0.70, 0.30), metal=0.9, rough=0.25),
        "tray": mat("cdu_tray", (0.30, 0.32, 0.35), metal=0.6, rough=0.4),
        "pcb": mat("cdu_pcb", (0.07, 0.28, 0.15), rough=0.55),
        "copper": mat("cdu_copper", (0.85, 0.50, 0.28), metal=0.95, rough=0.28),
        "gpu": mat("cdu_gpu", (0.24, 0.20, 0.40), metal=0.4, rough=0.3),
        "floor": mat("cdu_floor", (0.22, 0.23, 0.25), rough=0.8),
        "tile": mat("cdu_tile", (0.30, 0.31, 0.33), rough=0.7),
        "ghost": mat("cdu_ghost", (0.25, 0.27, 0.30), metal=0.5, rough=0.5),
        # glows
        "b_fac": mat("cdu_b_fac", (0.25, 0.45, 1.0), emit=(0.20, 0.40, 1.0), strength=4.0),
        "b_facw": mat("cdu_b_facw", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=4.0),
        "b_sup": mat("cdu_b_sup", (0.30, 0.95, 1.0), emit=(0.20, 0.92, 1.0), strength=4.0),
        "b_ret": mat("cdu_b_ret", (1.0, 0.50, 0.15), emit=(1.0, 0.45, 0.10), strength=4.5),
        "heat": mat("cdu_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=5.0),
        "gpu_hot": mat("cdu_gpu_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=1.5),
        "led_g": mat("cdu_led_g", (0.3, 1.0, 0.4), emit=(0.25, 1.0, 0.35), strength=5.0),
        "led_a": mat("cdu_led_a", (1.0, 0.75, 0.2), emit=(1.0, 0.70, 0.15), strength=5.0),
        "led_r": mat("cdu_led_r", (1.0, 0.15, 0.1), emit=(1.0, 0.10, 0.05), strength=5.0),
        "sig": mat("cdu_sig", (0.95, 0.95, 0.60), emit=(1.0, 1.0, 0.55), strength=5.0),
        "leak": mat("cdu_leak", (1.0, 0.12, 0.08), emit=(1.0, 0.10, 0.05), strength=4.0),
    }


# ---- layout ---------------------------------------------------------------------------------

CAB = (-70.0, -10.0, 0.0, 200.0, -120.0, 0.0)  # x0 x1 y0 y1 z0 z1
PHE = (-62.0, -30.0, 118.0, 168.0, -88.0, -42.0)  # plate stack x0 x1 y0 y1 z0 z1
N_PLATES = 18
PUMPS = {"A": -54.0, "B": -34.0}  # pump x centres; axis along z
PUMP_Y = 30.0
PUMP_Z = -62.0  # volute centre
FILT = (-20.0, 64.0, 100.0, -26.0, 7.0)  # x, y0, y1, z, radius
RES = (-16.0, 140.0, 186.0, -30.0, 6.0)
HDR_Z = -96.0  # suction header  # reservoir x, y0, y1, z, radius
VALVE = (-66.0, 84.0, -78.0)
RACK = (10.0, 70.0, 0.0, 214.0, -110.0, 0.0)
TRAY_Y = [34.0 + 22.0 * k for k in range(8)]
MAN_SUP_X, MAN_RET_X, MAN_Z = 52.0, 62.0, -102.0
R_PIPE = 2.6
R_HOSE = 0.9


def p_fac_in():
    """Facility supply: up from under the floor, through the valve, into the PHE's top-left port."""
    return [(-66.0, -40.0, -78.0), (-66.0, 160.0, -78.0), (-62.0, 160.0, -78.0)]


def p_fac_out():
    return [(-62.0, 126.0, -52.0), (-66.0, 126.0, -52.0), (-66.0, -40.0, -52.0)]


def p_fac_phe():
    """Facility water down through the plate gaps (counterflow to the secondary)."""
    x0, x1, y0, y1, z0, z1 = PHE
    zf = z1 + 1.2  # drawn on the stack's front face so the beads show
    return [(x0 + 1.0, 160.0, -78.0), (x0 + 4.0, 160.0, zf), (x1 - 6.0, 152.0, zf), (x0 + 6.0, 144.0, zf),
            (x1 - 6.0, 136.0, zf), (x0 + 4.0, 128.0, zf), (x0 + 1.0, 126.0, -52.0)]


def p_sec_ret():
    """Secondary return: warm water from the rack's return manifold into the reservoir."""
    return [(MAN_RET_X, 200.0, MAN_Z), (MAN_RET_X, 222.0, MAN_Z), (RES[0], 222.0, MAN_Z),
            (RES[0], 222.0, RES[3]), (RES[0], RES[2] + 2.0, RES[3])]


def p_sec_pump(name="A"):
    """Reservoir, down the suction line, the header, through pump `name`, up the discharge."""
    x = PUMPS[name]
    return [(RES[0], RES[1], RES[3]), (RES[0], RES[1] - 6.0, HDR_Z), (RES[0], PUMP_Y, HDR_Z), (x, PUMP_Y, HDR_Z),
            (x, PUMP_Y, PUMP_Z - 6.0), (x, PUMP_Y, PUMP_Z), (x, PUMP_Y + 12.0, PUMP_Z),
            (x, 56.0, PUMP_Z), (FILT[0], 56.0, PUMP_Z), (FILT[0], 56.0, FILT[3]), (FILT[0], FILT[1], FILT[3])]


def p_sec_filter():
    """Through the filter and on into the PHE's bottom-right port."""
    return [(FILT[0], FILT[1], FILT[3]), (FILT[0], FILT[2], FILT[3]), (FILT[0], 110.0, FILT[3]),
            (FILT[0], 110.0, -52.0), (FILT[0], 126.0, -52.0), (PHE[1], 126.0, -52.0)]


def p_sec_phe():
    """Secondary water up through the alternate plate gaps, cooling as it climbs."""
    x0, x1, zf = PHE[0], PHE[1], PHE[5] + 1.2
    return [(x1, 126.0, -52.0), (x1 - 4.0, 130.0, zf), (x0 + 6.0, 138.0, zf), (x1 - 6.0, 146.0, zf),
            (x0 + 6.0, 154.0, zf), (x1 - 4.0, 158.0, zf), (x1, 160.0, -78.0)]


def p_sec_sup():
    """Cool secondary supply: out of the PHE, up out of the cabinet, over to the supply manifold."""
    return [(PHE[1], 160.0, -78.0), (-24.0, 160.0, -78.0), (-24.0, 214.0, -78.0),
            (MAN_SUP_X, 214.0, -78.0), (MAN_SUP_X, 214.0, MAN_Z), (MAN_SUP_X, TRAY_Y[0], MAN_Z)]


def p_tray(k):
    """Supply manifold tap, through tray k's two cold plates, back to the return manifold."""
    y = TRAY_Y[k] + 5.0
    return [(MAN_SUP_X, y, MAN_Z), (MAN_SUP_X, y, -60.0), (40.0, y, -30.0), (24.0, y, -30.0),
            (24.0, y, -60.0), (40.0, y, -62.0), (MAN_RET_X, y, -70.0), (MAN_RET_X, y, MAN_Z)]


def p_man_ret(k):
    return [(MAN_RET_X, TRAY_Y[k] + 5.0, MAN_Z), (MAN_RET_X, 200.0, MAN_Z)]


# ---- builders -------------------------------------------------------------------------------


def pipe(name, pts, m, parent, r=R_PIPE):
    return polyline(name, pts, r, m, parent)


def floor(m, parent):
    g = empty("floor", parent)
    bx("floor_slab", (-110.0, -3.0, -140.0), (300.0, 0.0, 30.0), m["floor"], g)
    for i in range(-2, 6):
        bx(f"tile_seam{i}", (-110.0 + 60.0 * (i + 2), -0.2, -140.0), (-109.4 + 60.0 * (i + 2), 0.1, 30.0), m["tile"], g)
    return g


def cabinet(m, parent):
    x0, x1, y0, y1, z0, z1 = CAB
    g = empty("cabinet", parent)
    parts = [
        bx("cab_back", (x0, y0, z0), (x1, y1, z0 + 2.0), m["panel"], g),
        bx("cab_left", (x0, y0, z0), (x0 + 2.0, 40.0, z1), m["panel"], g),
        bx("cab_right", (x1 - 2.0, y0, z0), (x1, 40.0, z1), m["panel"], g),
        bx("cab_top", (x0, y1 - 2.0, z0), (x1, y1, z1), m["panel"], g),
        bx("cab_base", (x0, y0, z0), (x1, 8.0, z1), m["frame"], g),
        bx("cab_shelf", (x0 + 2.0, 108.0, z0 + 2.0), (x1 - 2.0, 110.0, -30.0), m["panel_lt"], g),
    ]
    # door frame lip round the cut face
    parts += [bx("lip_l", (x0, y0, z0), (x0 + 3.0, y1, z0 + 3.0), m["frame"], g),
              bx("lip_r", (x1 - 3.0, y0, z0), (x1, y1, z0 + 3.0), m["frame"], g),
              bx("post_l", (x0, y0, z1 - 2.5), (x0 + 2.5, y1, z1), m["frame"], g),
              bx("post_r", (x1 - 2.5, y0, z1 - 2.5), (x1, y1, z1), m["frame"], g)]
    join(parts, "cabinet_mesh")
    return g


def phe(m, parent):
    """The plate heat exchanger: plates stacked along x between a fixed and a moving frame plate."""
    x0, x1, y0, y1, z0, z1 = PHE
    g = empty("phe", parent)
    pitch = (x1 - x0 - 6.0) / N_PLATES
    plates = []
    for i in range(N_PLATES):
        xa = x0 + 3.0 + pitch * i
        plates.append(bx(f"pl{i}", (xa, y0 + 2.0, z0 + 2.0), (xa + pitch * 0.45, y1 - 2.0, z1 - 2.0),
                         m["plate_a"] if i % 2 else m["plate_b"], g))
    join(plates, "phe_plates")
    fr = [bx("phe_fix", (x0, y0 - 3.0, z0 - 3.0), (x0 + 3.0, y1 + 3.0, z1 + 3.0), m["pheframe"], g),
          bx("phe_mov", (x1 - 3.0, y0 - 3.0, z0 - 3.0), (x1, y1 + 3.0, z1 + 3.0), m["pheframe"], g),
          bx("phe_rail", (x0, y1 + 3.0, (z0 + z1) / 2 - 1.5), (x1 + 4.0, y1 + 6.0, (z0 + z1) / 2 + 1.5), m["steel"], g)]
    join(fr, "phe_frame")
    bolts = []
    for yy in (y0 - 1.0, y1 + 1.0):
        for zz in (z0 - 1.0, z1 + 1.0):
            bolts.append(tube(f"tie{yy}{zz}", (x0 - 3.0, yy, zz), (x1 + 3.0, yy, zz), 0.7, m["bolt"], g, 10))
            bolts.append(ball(f"nut{yy}{zz}", (x1 + 3.0, yy, zz), 1.3, m["bolt"], g, 8))
    join(bolts, "phe_bolts")
    ports = [tube("port_fi", (x0 - 4.0, 160.0, -78.0), (x0, 160.0, -78.0), 3.2, m["steel"], g, 16),
             tube("port_fo", (x0 - 4.0, 126.0, -52.0), (x0, 126.0, -52.0), 3.2, m["steel"], g, 16),
             tube("port_si", (x1, 126.0, -52.0), (x1 + 4.0, 126.0, -52.0), 3.2, m["steel"], g, 16),
             tube("port_so", (x1, 160.0, -78.0), (x1 + 4.0, 160.0, -78.0), 3.2, m["steel"], g, 16)]
    join(ports, "phe_ports")
    return g


def pump(m, parent, name, cut_open=False):
    """A close-coupled centrifugal pump: a motor behind, a volute in front, axis along z."""
    x = PUMPS[name]
    g = empty(f"pump_{name}", parent)
    mo = [tube(f"motor_{name}", (x, PUMP_Y, PUMP_Z - 40.0), (x, PUMP_Y, PUMP_Z - 8.0), 8.0, m["motor"], g, 24)]
    for k in range(8):
        a = 2 * math.pi * k / 8
        mo.append(tube(f"fin_{name}{k}", (x + 8.4 * math.cos(a), PUMP_Y + 8.4 * math.sin(a), PUMP_Z - 38.0),
                       (x + 8.4 * math.cos(a), PUMP_Y + 8.4 * math.sin(a), PUMP_Z - 10.0), 0.8, m["motor"], g, 6))
    join(mo, f"motor_{name}_mesh")
    vo = tube(f"volute_{name}", (x, PUMP_Y, PUMP_Z - 8.0), (x, PUMP_Y, PUMP_Z + 4.0), 9.5, m["pump"], g, 32)
    if cut_open:
        cut(vo, PUMP_Z - 2.0)
    bx(f"pbase_{name}", (x - 9.0, 8.0, PUMP_Z - 42.0), (x + 9.0, PUMP_Y - 8.0, PUMP_Z + 4.0), m["frame"], g)
    # VFD box on the motor
    bx(f"vfd_{name}", (x - 5.0, PUMP_Y + 8.0, PUMP_Z - 34.0), (x + 5.0, PUMP_Y + 14.0, PUMP_Z - 18.0), m["panel_lt"], g)
    led = ball(f"pled_{name}", (x, PUMP_Y + 14.4, PUMP_Z - 20.0), 1.0, m["led_g" if name == "A" else "led_a"], g, 8)
    imp = O.pivot(f"imp_{name}", (x, PUMP_Y, PUMP_Z - 3.0), g)
    bl = [disc(f"hub_{name}", (0, 0, 0), 2.0, 2.0, m["impeller"], imp, 16)]
    bl[0].rotation_euler = (math.pi / 2, 0, 0)
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = bx(f"blade_{name}{k}", (-0.6, 1.5, -2.0), (0.6, 7.5, 1.5), m["impeller"], imp)
        b.rotation_mode = "XYZ"
        b.rotation_euler = (0.0, -a, 0.0)
        bl.append(b)
    return {"g": g, "led": led, "imp": imp, "top": (x, PUMP_Y + 15.0, PUMP_Z - 20.0), "volute": (x, PUMP_Y, PUMP_Z + 4.0)}


def spin(imp, b0, b1, rps=0.6):
    """Spin an impeller about the poly z axis (Blender -Y) from beat b0 to b1."""
    n = (b1 - b0) * 8
    for i in range(n + 1):
        f = F(b0, 0) + round((F(b1, 0) - F(b0, 0)) * i / n) - (1 if i == n else 0)
        key(imp, f, "rotation_euler", (0.0, 2 * math.pi * rps * (f - F(b0, 0)) / 24.0, 0.0), linear=True)


def filt(m, parent):
    x, y0, y1, z, r = FILT
    g = empty("filter", parent)
    can = tube("filter_can", (x, y0, z), (x, y1, z), r, m["filter"], g, 32)
    cut(can, z)
    core = tube("filter_core", (x, y0 + 4.0, z), (x, y1 - 4.0, z), r * 0.62, m["mesh"], g, 24)
    cut(core, z)
    pleats = []
    for k in range(10):
        yy = y0 + 6.0 + (y1 - y0 - 12.0) * k / 9
        pleats.append(tube(f"pleat{k}", (x - r * 0.62, yy, z - 0.2), (x + r * 0.62, yy, z - 0.2), 0.25, m["frame"], g, 6))
    join(pleats, "filter_pleats")
    bx("filter_cap", (x - r - 1.0, y1, z - r - 1.0), (x + r + 1.0, y1 + 3.0, z), m["steel"], g)
    gauge = ball("dp_gauge", (x + r + 2.0, y1 - 4.0, z + 1.0), 1.8, m["plc"], g, 12)
    return {"g": g, "top": (x, y1 + 3.0, z), "mid": (x, (y0 + y1) / 2, z), "gauge": gauge}


def reservoir(m, parent):
    x, y0, y1, z, r = RES
    g = empty("reservoir", parent)
    tank = tube("res_tank", (x, y0, z), (x, y1, z), r, m["tank"], g, 32)
    level = tube("res_level", (x, y0 + 1.0, z), (x, y0 + (y1 - y0) * 0.6, z), r * 0.92, m["fluid"], g, 24)
    sight = bx("res_sight", (x + r - 0.2, y0 + 4.0, z - 1.0), (x + r + 0.6, y1 - 4.0, z + 1.0), m["frame"], g)
    return {"g": g, "top": (x, y1, z), "level": level, "sight": sight}


def valve(m, parent):
    x, y, z = VALVE
    g = empty("valve", parent)
    bx("valve_body", (x - 4.0, y - 5.0, z - 4.0), (x + 4.0, y + 5.0, z + 4.0), m["valve"], g)
    tube("valve_stem", (x, y, z + 4.0), (x, y, z + 9.0), 0.8, m["steel"], g, 8)
    bx("valve_act", (x - 4.0, y - 4.0, z + 9.0), (x + 4.0, y + 4.0, z + 17.0), m["actuator"], g)
    pos = O.pivot("valve_flag", (x, y, z + 17.5), g)
    bx("valve_flag_m", (-0.5, -0.5, 0.0), (0.5, 3.5, 1.0), m["frame"], pos)
    return {"g": g, "pos": pos, "act": (x, y, z + 17.0)}


def controller(m, parent):
    g = empty("controller", parent)
    bx("plc_box", (-60.0, 176.0, -10.0), (-28.0, 196.0, -3.0), m["plc"], g)
    scr_g = empty("plc_screen_g", g)
    bx("plc_screen", (-56.0, 179.0, -3.0), (-38.0, 193.0, -2.4), m["screen"], scr_g)
    leds = {}
    for i, c in enumerate(("led_g", "led_g", "led_a", "led_r")):
        leds[i] = ball(f"plc_led{i}", (-34.0, 192.0 - 3.5 * i, -2.6), 0.8, m[c], g, 8)
    return {"g": g, "screen": scr_g, "leds": leds, "at": (-44.0, 196.0, -3.0)}


def sensors(m, parent):
    """Temperature (T), pressure (P) and flow (F) points: a stub on the pipe with an LED cap."""
    pts = {
        "T_sup": (-24.0, 186.0, -78.0), "P_sup": (-24.0, 200.0, -78.0), "F_sup": (-24.0, 170.0, -78.0),
        "T_ret": (RES[0], 205.0, RES[3]), "P_ret": (10.0, 222.0, MAN_Z),
        "T_fin": (-66.0, 140.0, -78.0), "T_fout": (-66.0, 100.0, -52.0),
        "P_pump": (-34.0, 56.0, PUMP_Z),
    }
    g = empty("sensors", parent)
    leds = {}
    for k, p in pts.items():
        tube(f"sn_{k}", p, (p[0], p[1], p[2] + 6.0), 1.0, m["steel"], g, 8)
        e = empty(f"snled_{k}_g", g)
        ball(f"snled_{k}", (p[0], p[1], p[2] + 6.6), 1.2, m["led_g"], e, 8)
        leds[k] = e
    # leak rope along the cabinet floor
    rope = bx("leak_rope", (CAB[0] + 3.0, 8.0, -20.0), (CAB[1] - 3.0, 8.6, -18.0), m["led_a"], g)
    return {"g": g, "leds": leds, "pts": pts, "rope": rope}


def rack(m, parent, x_off=0.0, name="rack", trays=True):
    x0, x1, y0, y1, z0, z1 = RACK
    x0 += x_off
    x1 += x_off
    g = empty(name, parent)
    fr = []
    for xx in (x0, x1 - 3.0):
        for zz in (z0, z1 - 3.0):
            fr.append(bx(f"{name}_post{xx}{zz}", (xx, y0, zz), (xx + 3.0, y1, zz + 3.0), m["frame"], g))
    fr.append(bx(f"{name}_top", (x0, y1 - 3.0, z0), (x1, y1, z1), m["frame"], g))
    join(fr, f"{name}_frame")
    out = {"g": g, "gpu_glow": empty(f"{name}_gpuglow", g)}
    if not trays:
        return out
    tr, cp, gp, glow = [], [], [], []
    for k, y in enumerate(TRAY_Y):
        tr.append(bx(f"{name}_tray{k}", (x0 + 3.0, y, z0 + 6.0), (x1 - 3.0, y + 2.0, z1 - 4.0), m["tray"], g))
        tr.append(bx(f"{name}_pcb{k}", (x0 + 5.0, y + 2.0, z0 + 10.0), (x1 - 12.0, y + 2.6, z1 - 6.0), m["pcb"], g))
        tr.append(bx(f"{name}_bezel{k}", (x0 + 3.0, y, z1 - 4.0), (x1 - 3.0, y + 9.0, z1 - 3.0), m["panel"], g))
        for cx, cz in ((24.0, -30.0), (24.0, -60.0), (40.0, -30.0), (40.0, -62.0)):
            cxx = cx + x_off
            gp.append(bx(f"{name}_gpu{k}{cx}{cz}", (cxx - 5.0, y + 2.6, cz - 5.0), (cxx + 5.0, y + 3.6, cz + 5.0), m["gpu"], g))
            glow.append(bx(f"{name}_glow{k}{cx}{cz}", (cxx - 3.5, y + 2.6, cz - 3.5), (cxx + 3.5, y + 3.7, cz + 3.5), m["gpu_hot"], out["gpu_glow"]))
            cp.append(bx(f"{name}_cp{k}{cx}{cz}", (cxx - 4.5, y + 3.6, cz - 4.5), (cxx + 4.5, y + 6.0, cz + 4.5), m["copper"], g))
    join(tr, f"{name}_trays")
    join(gp, f"{name}_gpus")
    join(cp, f"{name}_coldplates")
    join(glow, f"{name}_glow_mesh")
    return out


def manifolds(m, parent):
    g = empty("manifolds", parent)
    pipe("man_sup", [(MAN_SUP_X, 18.0, MAN_Z), (MAN_SUP_X, 214.0, MAN_Z)], m["pipe_sup"], g, 2.2)
    pipe("man_ret", [(MAN_RET_X, 18.0, MAN_Z), (MAN_RET_X, 222.0, MAN_Z)], m["pipe_ret"], g, 2.2)
    hoses, qds = [], []
    for k in range(8):
        pts = p_tray(k)
        hoses.append(polyline(f"hose{k}", pts[1:7], R_HOSE, m["hose"], g))
        qds.append(ball(f"qd_s{k}", pts[1], 1.5, m["qd"], g, 10))
        qds.append(ball(f"qd_r{k}", pts[6], 1.5, m["qd"], g, 10))
        hoses.append(tube(f"tap_s{k}", pts[0], pts[1], 1.0, m["pipe_sup"], g, 8))
        hoses.append(tube(f"tap_r{k}", pts[6], pts[7], 1.0, m["pipe_ret"], g, 8))
    join(hoses, "hoses")
    join(qds, "qds")
    return {"g": g, "qd": p_tray(3)[1], "sup": (MAN_SUP_X, 120.0, MAN_Z), "ret": (MAN_RET_X, 150.0, MAN_Z)}


def plumbing(m, parent):
    g = empty("plumbing", parent)
    pipe("fac_in", p_fac_in(), m["pipe_fac"], g, 3.0)
    pipe("fac_out", p_fac_out(), m["pipe_fac"], g, 3.0)
    pipe("sec_ret", p_sec_ret(), m["pipe_ret"], g)
    for n in PUMPS:
        pipe(f"sec_pump{n}", p_sec_pump(n)[3:9], m["pipe_ret"], g, 2.2)
    pipe("suction", p_sec_pump("A")[:4], m["pipe_ret"], g)
    pipe("disch", p_sec_pump("A")[8:], m["pipe_ret"], g)
    pipe("sec_filt", p_sec_filter()[2:], m["pipe_sup"], g)
    pipe("sec_sup", p_sec_sup()[:5], m["pipe_sup"], g)
    # floor penetrations
    for x, z in ((-66.0, -78.0), (-66.0, -52.0)):
        disc(f"flange{z}", (x, 0.5, z), 4.6, 1.2, m["steel"], g, 24)
    return g


def inrack(m, parent):
    """An in-rack CDU: a 4U box at the bottom of the rack, lid off, with a small brazed-plate
    exchanger, two pump cartridges and its own little reservoir."""
    g = empty("inrack", parent)
    x0, x1 = RACK[0] + 3.0, RACK[1] - 3.0
    y0, y1 = 4.0, 22.0
    parts = [bx("ir_base", (x0, y0, -104.0), (x1, y0 + 1.5, -4.0), m["panel"], g),
             bx("ir_back", (x0, y0, -104.0), (x1, y1, -102.0), m["panel"], g),
             bx("ir_face", (x0, y0, -4.0), (x1, y0 + 4.0, -3.0), m["panel_lt"], g)]
    join(parts, "ir_case")
    pl = [bx(f"ir_pl{i}", (18.0 + 1.1 * i, y0 + 2.0, -70.0), (18.6 + 1.1 * i, y1 - 2.0, -40.0),
             m["plate_a"] if i % 2 else m["copper"], g) for i in range(14)]
    join(pl, "ir_bphe")
    for i, x in enumerate((44.0, 56.0)):
        tube(f"ir_pump{i}", (x, 12.0, -60.0), (x, 12.0, -30.0), 4.5, m["pump"], g, 20)
    tube("ir_res", (60.0, 8.0, -88.0), (60.0, 20.0, -88.0), 5.0, m["tank"], g, 20)
    e = empty("ir_led_g", g)
    ball("ir_led", (64.0, y0 + 2.5, -2.8), 0.8, m["led_g"], e, 8)
    return {"g": g, "led": e, "at": (40.0, y1, -20.0)}


def p_inrack_fac():
    """Facility water (or a TCS branch) into the in-rack CDU's exchanger and out."""
    return [(30.0, -30.0, -96.0), (30.0, 12.0, -96.0), (24.0, 12.0, -70.0), (24.0, 12.0, -40.0),
            (30.0, 12.0, -20.0), (30.0, -30.0, -20.0)]


def p_inrack_sec():
    return [(MAN_RET_X, TRAY_Y[0], MAN_Z), (MAN_RET_X, 14.0, MAN_Z), (56.0, 14.0, -60.0), (44.0, 14.0, -40.0),
            (20.0, 16.0, -55.0), (MAN_SUP_X, 16.0, MAN_Z), (MAN_SUP_X, TRAY_Y[0], MAN_Z)]


def row(m, parent, n=3):
    """More racks down the row to the right, each with its trays and a supply/return pair off a
    header running over the row from the CDU."""
    g = empty("row", parent)
    racks = []
    for i in range(n):
        xo = 66.0 * (i + 1)
        r = rack(m, g, xo, f"rk{i}")
        racks.append(r)
        pipe(f"rk{i}_s", [(MAN_SUP_X + xo, 214.0, MAN_Z), (MAN_SUP_X + xo, 30.0, MAN_Z)], m["pipe_sup"], g, 2.0)
        pipe(f"rk{i}_r", [(MAN_RET_X + xo, 222.0, MAN_Z), (MAN_RET_X + xo, 30.0, MAN_Z)], m["pipe_ret"], g, 2.0)
    pipe("hdr_s", [(MAN_SUP_X, 214.0, MAN_Z), (MAN_SUP_X + 66.0 * n, 214.0, MAN_Z)], m["pipe_sup"], g, 2.6)
    pipe("hdr_r", [(MAN_RET_X, 222.0, MAN_Z), (MAN_RET_X + 66.0 * n, 222.0, MAN_Z)], m["pipe_ret"], g, 2.6)
    return {"g": g, "racks": racks}


def p_row_sup(i):
    xo = 66.0 * (i + 1)
    return [(MAN_SUP_X, 214.0, MAN_Z), (MAN_SUP_X + xo, 214.0, MAN_Z), (MAN_SUP_X + xo, 40.0, MAN_Z)]


def p_row_ret(i):
    xo = 66.0 * (i + 1)
    return [(MAN_RET_X + xo, 40.0, MAN_Z), (MAN_RET_X + xo, 222.0, MAN_Z), (MAN_RET_X, 222.0, MAN_Z)]


def scene(m, root, row_racks=False, in_rack=False):
    """Everything on the page. Returns handles for animation and tags."""
    s = {}
    floor(m, root)
    cabinet(m, root)
    s["phe"] = phe(m, root)
    s["pumps"] = {n: pump(m, root, n, cut_open=(n == "A")) for n in PUMPS}
    s["filter"] = filt(m, root)
    s["res"] = reservoir(m, root)
    s["valve"] = valve(m, root)
    s["ctrl"] = controller(m, root)
    s["sens"] = sensors(m, root)
    s["plumb"] = plumbing(m, root)
    s["rack"] = rack(m, root)
    s["man"] = manifolds(m, root)
    if in_rack:
        s["inrack"] = inrack(m, root)
    if row_racks:
        s["row"] = row(m, root)
    return s


# ---- animation helpers ----------------------------------------------------------------------


def secondary(root, m, beats, u0=0.0, u1=0.85, n=5, pump_name="A"):
    """The whole secondary loop for `beats`: return in, through the pump and filter, up the PHE,
    out as cool supply and through every tray."""
    run(root, "s_ret", p_sec_ret(), n, 2.2, m["b_ret"], beats, u0, u1, 70)
    run(root, f"s_pump{pump_name}", p_sec_pump(pump_name), n, 2.0, m["b_ret"], beats, u0 + 0.05, u1, 80)
    run(root, "s_filt", p_sec_filter(), n, 2.0, m["b_ret"], beats, u0 + 0.1, u1, 50)
    run(root, "s_phe", p_sec_phe(), n, 1.8, m["b_sup"], beats, u0 + 0.12, u1, 50)
    run(root, "s_sup", p_sec_sup(), n, 2.2, m["b_sup"], beats, u0 + 0.15, u1, 70)
    trays(root, m, beats, u0 + 0.2, u1)


def trays(root, m, beats, u0, u1, ks=range(8)):
    for k in ks:
        pts = p_tray(k)
        run(root, f"t_in{k}", pts[:3], 2, 1.5, m["b_sup"], beats, u0 + 0.01 * k, u1, 30)
        run(root, f"t_out{k}", pts[3:], 2, 1.5, m["b_ret"], beats, u0 + 0.06 + 0.01 * k, u1, 36)
        run(root, f"t_up{k}", p_man_ret(k), 1, 1.3, m["b_ret"], beats, u0 + 0.1 + 0.01 * k, u1, 40)


def facility(root, m, beats, u0=0.0, u1=0.85, n=5):
    run(root, "f_in", p_fac_in(), n, 2.4, m["b_fac"], beats, u0, u1, 70)
    run(root, "f_phe", p_fac_phe(), n, 1.8, m["b_fac"], beats, u0 + 0.1, u1, 50)
    run(root, "f_out", p_fac_out(), n, 2.4, m["b_facw"], beats, u0 + 0.2, u1, 70)


def gpu_heat(root, m, beats, ks=(1, 4, 7)):
    for k in ks:
        for cx in (24.0, 40.0):
            rise(root, f"gh{k}{cx}", (cx, TRAY_Y[k] + 6.0, -30.0), 2, 0.8, m["heat"], beats, 0.05, 0.8, 12.0, 50, (3.0, 3.0))


def phe_transfer(root, m, beats, n=10):
    """Heat hopping across the plates: tiny orange beads jumping from a secondary gap to the next
    facility gap."""
    x0, x1, y0, y1 = PHE[0], PHE[1], PHE[2], PHE[3]
    pitch = (x1 - x0 - 6.0) / N_PLATES
    for k in range(n):
        i = 2 * (k % (N_PLATES // 2))
        xa = x0 + 3.0 + pitch * (i + 0.7)
        y = y0 + 6.0 + (y1 - y0 - 12.0) * ((k * 7) % n) / max(1, n - 1)
        run(root, f"hx{k}", [(xa, y, -41.0), (xa + pitch, y + 1.0, -41.0)], 1, 1.1, m["heat"], beats,
            0.02 + 0.07 * k, 0.9, 18)


def leds_on(s, beats):
    """Sensors blinking (staggered) through `beats`."""
    for i, e in enumerate(s["sens"]["leds"].values()):
        iv = []
        for b in beats:
            for j in range(8):
                if (j + i) % 2 == 0:
                    iv.append((F(b, j / 8), F(b, (j + 0.5) / 8)))
        show(e, iv)


def pulses(root, m, s, beats, u0=0.05, u1=0.85):
    """Signals from every sensor to the controller (yellow beads)."""
    at = s["ctrl"]["at"]
    for k, p in s["sens"]["pts"].items():
        q = (p[0], p[1], p[2] + 7.0)
        run(root, f"sig_{k}", [q, (q[0], 204.0, q[2]), (at[0], 204.0, at[2]), at], 1, 0.9, m["sig"], beats, u0, u1, 40)
