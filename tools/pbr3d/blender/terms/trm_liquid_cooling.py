"""TRM_LIQUID_COOLING: a direct-to-chip liquid-cooled rack, its CDU and an immersion tank.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_liquid_cooling.py

No GPU board base: the subject is the rack-level plumbing. Units are centimetres. Left to right:
the CDU (front cut away: pump, motor, plate heat exchanger, reservoir, facility pipes up to the
ceiling), the rack (rear supply and return manifolds, quick disconnects on every tray), one compute
tray pulled out onto a bench with two GPU cold plates and a CPU plate, a cold plate drawn ~6x size
and cut open over its die, and an immersion tank. Blue = cool coolant, amber = warm.

Beats:
  0 rack     a 100+ kW rack, heat rising, liquid lines on every tray
  1 plate    the cold plate cut open: coolant through microchannels over the die
  2 loop     tray -> rear manifold -> CDU and back
  3 cdu      pump + plate heat exchanger hand the heat to facility water
  4 market   immersion as the other route; who sells it
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, polyline  # noqa: E402

SLUG = "TRM_LIQUID_COOLING"
BEATS = [
    ("An AI rack now makes more heat than air can carry",
     "A rack of current Nvidia GPUs draws 120 kW or more, against 10 to 20 kW for a classic server rack. Every watt "
     "ends up as heat, and blowing enough air through a rack that dense would take hurricane fans. So each compute "
     "tray now has liquid lines plugged into it, and the heat leaves in water instead of air."),
    ("A cold plate sits on each chip with coolant in tiny channels",
     "Direct-to-chip cooling bolts a copper cold plate onto each GPU and CPU. Inside, coolant (water with glycol) "
     "flows through fins a fraction of a millimetre apart, right above the die, so heat crosses only a thin layer of "
     "thermal paste and copper. Roughly 80 percent or more of a tray's heat leaves this way; fans handle the rest."),
    ("Trays plug into manifolds that run down the back of the rack",
     "Each tray's hoses end in dripless quick disconnects that click onto a supply and a return manifold at the rack's "
     "rear. Cool liquid goes in at maybe 25 to 40 C and comes out 10 C or so warmer. The rack loop is a closed, "
     "clean circuit with filtered, treated coolant."),
    ("The CDU pumps the loop and hands the heat to facility water",
     "A coolant distribution unit (CDU) holds the pumps, a reservoir, filters and a plate heat exchanger. Warm rack "
     "coolant passes on one side of the thin steel plates, facility water on the other, so the two never mix. The "
     "facility water carries the heat to dry coolers or chillers. One large CDU can serve several megawatts."),
    ("Immersion is the other route; the plumbing is a fast-growing market",
     "Immersion cooling drops whole servers into a tank of dielectric fluid that cannot short anything, and pulls "
     "the heat out of the fluid. It is used less than cold plates but avoids fans entirely. Suppliers of CDUs, "
     "manifolds and plates: Vertiv (VRT), Schneider Electric, nVent (NVT), Modine (MOD), CoolIT, Boyd, and server "
     "makers like Super Micro (SMCI) that ship racks with the loop installed."),
]

RX0, RX1, RZ0 = -60.0, 0.0, -120.0  # rack x, back z (front at z = 0)
RH = 210.0
CDU = (-180.0, -100.0, -120.0, 200.0)  # x0, x1, z0, h
TB = (25.0, 135.0, -90.0, 80.0)  # tray on the bench: x0, x1, z0, top y of bench
GP = (165.0, 255.0, 70.0)  # giant cold plate x0, x1, base y
TK = (285.0, 395.0, -110.0, -20.0)  # immersion tank x0, x1, z0, z1


def mats(m):
    m["skin"] = mat("lc_skin", (0.78, 0.80, 0.82), metal=0.5, rough=0.4)
    m["rack"] = mat("lc_rack", (0.08, 0.08, 0.10), metal=0.4, rough=0.5)
    m["tray"] = mat("lc_tray", (0.30, 0.31, 0.35), metal=0.6, rough=0.4)
    m["floor"] = mat("lc_floor", (0.40, 0.41, 0.43), rough=0.8)
    m["pipe_s"] = mat("lc_pipe_s", (0.20, 0.38, 0.70), metal=0.5, rough=0.35)
    m["pipe_r"] = mat("lc_pipe_r", (0.62, 0.34, 0.20), metal=0.5, rough=0.35)
    m["hose"] = mat("lc_hose", (0.10, 0.10, 0.11), rough=0.8)
    m["motor"] = mat("lc_motor", (0.15, 0.30, 0.22), metal=0.4, rough=0.45)
    m["fluid"] = mat("lc_fluid", (0.55, 0.75, 0.95), rough=0.1, alpha=0.35)
    m["c_cool"] = mat("lc_g_cool", (0.30, 0.65, 1.0), emit=(0.25, 0.62, 1.0), strength=4.0)
    m["c_warm"] = mat("lc_g_warm", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)
    m["led"] = mat("lc_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["die_g"] = mat("lc_die_g", (0.9, 0.35, 0.12), emit=(1.0, 0.35, 0.10), strength=2.0)
    m["chan_g"] = mat("lc_chan_g", (0.3, 0.6, 1.0), emit=(0.25, 0.6, 1.0), strength=1.8)


def build_rack(m, root):
    g = empty("rack", root)
    for px in (RX0, RX1 - 4.0):
        for pz in (RZ0, -4.0):
            bx(f"rk_p{px:.0f}{pz:.0f}", (px, 0.0, pz), (px + 4.0, RH, pz + 4.0), m["rack"], g)
    bx("rk_top", (RX0, RH - 4.0, RZ0), (RX1, RH, 0.0), m["rack"], g)
    bx("rk_side", (RX0 - 1.0, 0.0, RZ0), (RX0, RH, 0.0), m["rack"], g)
    trays, qds = [], []
    leds = empty("rk_leds", root)
    for k in range(18):
        y = 10.0 + k * 10.8
        trays.append(bx(f"rk_t{k}", (RX0 + 4.0, y, RZ0 + 14.0), (RX1 - 4.0, y + 7.0, -4.0), m["tray"], g))
        bx(f"rk_l{k}", (RX0 + 8.0, y + 2.0, -3.8), (RX0 + 12.0, y + 3.5, -3.5), m["led"], leds)
        for dx, mt in ((-18.0, "pipe_s"), (-8.0, "pipe_r")):  # QD pair at the tray's back
            qds.append(tube(f"rk_qd{k}{dx:.0f}", (dx, y + 3.5, RZ0 + 14.0), (dx, y + 3.5, RZ0 + 7.0), 1.4, m[mt], g, 8))
    D.join(trays, "rk_trays")
    D.join(qds, "rk_qds")
    for dx, mt in ((-18.0, "pipe_s"), (-8.0, "pipe_r")):
        bx(f"rk_man{dx:.0f}", (dx - 2.5, 6.0, RZ0 + 3.0), (dx + 2.5, RH - 6.0, RZ0 + 7.0), m[mt], g)
    return leds


def build_cdu(m, root):
    x0, x1, z0, h = CDU
    g = empty("cdu", root)
    bx("cdu_back", (x0, 0.0, z0), (x1, h, z0 + 3.0), m["skin"], g)
    bx("cdu_l", (x0, 0.0, z0), (x0 + 3.0, h, 0.0), m["skin"], g)
    bx("cdu_r", (x1 - 3.0, 0.0, z0), (x1, h, 0.0), m["skin"], g)
    bx("cdu_top", (x0, h - 3.0, z0), (x1, h, 0.0), m["skin"], g)
    bx("cdu_base", (x0, 0.0, z0), (x1, 6.0, 0.0), m["rack"], g)
    bx("cdu_screen", (x0 + 20.0, 170.0, -3.0), (x0 + 60.0, 190.0, -1.0), m["screen"], g)
    # pump + motor
    tube("pump_v", (x0 + 25.0, 6.0, -60.0), (x0 + 25.0, 30.0, -60.0), 11.0, m["steel"], g, 24)
    tube("pump_m", (x0 + 25.0, 30.0, -60.0), (x0 + 25.0, 58.0, -60.0), 9.0, m["motor"], g, 24)
    # reservoir
    tube("res", (x0 + 58.0, 6.0, -80.0), (x0 + 58.0, 60.0, -80.0), 12.0, m["steel"], g, 24)
    # plate heat exchanger: frame plates + 24 thin plates
    bx("phx_f0", (x0 + 10.0, 80.0, -90.0), (x0 + 70.0, 84.0, -30.0), m["dark"], g)
    bx("phx_f1", (x0 + 10.0, 136.0, -90.0), (x0 + 70.0, 140.0, -30.0), m["dark"], g)
    pl = []
    for k in range(24):
        y = 86.0 + 2.1 * k
        pl.append(bx(f"phx_p{k}", (x0 + 12.0, y, -88.0), (x0 + 68.0, y + 1.0, -32.0), m["steel"], g))
    D.join(pl, "phx_plates")
    for xb in (x0 + 12.0, x0 + 66.0):
        tube(f"phx_bolt{xb:.0f}", (xb, 78.0, -32.0), (xb, 142.0, -32.0), 1.0, m["dark"], g, 8)
    hot = empty("phx_glow", root)
    for k in range(0, 24, 2):
        y = 86.0 + 2.1 * k
        bx(f"phx_g{k}", (x0 + 14.0, y + 1.0, -31.8), (x0 + 66.0, y + 1.6, -31.5), m["c_warm" if k % 4 else "c_cool"], hot)
    show(hot, [])
    return hot


def build_tray(m, root):
    """A compute tray on a bench: two GPU modules + a CPU, each under a cold plate, hoses to the QDs."""
    x0, x1, z0, ty = TB
    g = empty("tray", root)
    for xl in (x0 + 4.0, x1 - 8.0):
        for zl in (z0 + 4.0, -8.0):
            bx(f"bench_leg{xl:.0f}{zl:.0f}", (xl, 0.0, zl), (xl + 4.0, ty, zl + 4.0), m["rack"], g)
    bx("bench_top", (x0, ty - 3.0, z0), (x1, ty, 0.0), m["dark"], g)
    bx("tray_pan", (x0 + 8.0, ty, z0 + 8.0), (x1 - 8.0, ty + 1.0, -6.0), m["tray"], g)
    bx("tray_pcb", (x0 + 12.0, ty + 1.0, z0 + 12.0), (x1 - 12.0, ty + 2.0, -10.0), m["mask"], g)
    plates = []
    for k, (cx, cz, s) in enumerate(((x0 + 35.0, -55.0, 11.0), (x0 + 75.0, -55.0, 11.0), (x0 + 55.0, -25.0, 8.0))):
        bx(f"tr_pkg{k}", (cx - s - 2, ty + 2.0, cz - s - 2), (cx + s + 2, ty + 3.0, cz + s + 2), m["substrate"], g)
        plates.append(bx(f"tr_cp{k}", (cx - s, ty + 3.0, cz - s), (cx + s, ty + 7.0, cz + s), m["copper"], g))
    D.join(plates, "tr_plates")
    # hoses: supply from rear QD over plate 0 -> plate 1 -> plate 2 -> return QD
    yh = ty + 9.0
    hose = [(x0 + 20.0, yh, z0 + 8.0), (x0 + 35.0, yh, -55.0), (x0 + 75.0, yh, -55.0), (x0 + 55.0, yh, -25.0),
            (x0 + 90.0, yh, -25.0), (x0 + 90.0, yh, z0 + 8.0)]
    polyline("tr_hose", hose, 1.2, m["hose"], g)
    for xq, mt in ((x0 + 20.0, "pipe_s"), (x0 + 90.0, "pipe_r")):
        tube(f"tr_qd{xq:.0f}", (xq, yh, z0 + 8.0), (xq, yh, z0 + 2.0), 2.0, m[mt], g, 10)
    return hose


def build_plate(m, root):
    """One cold plate ~6x size, cut at z = 0: die, TIM, copper base, skived fins, lid, ports."""
    x0, x1, y0 = GP
    g = empty("gplate", root)
    zb = -50.0
    bx("gp_stand", ((x0 + x1) / 2 - 6.0, 0.0, zb / 2 - 6.0), ((x0 + x1) / 2 + 6.0, y0 - 8.0, zb / 2 + 6.0), m["rack"], g)
    bx("gp_sub", (x0, y0 - 8.0, zb), (x1, y0 - 2.0, 0.0), m["substrate"], g)
    bx("gp_die", (x0 + 20.0, y0 - 2.0, zb + 10.0), (x1 - 20.0, y0 + 2.0, 0.0), m["die"], g)
    die_g = empty("gp_dieg", root)
    bx("gp_dieglow", (x0 + 21.0, y0 - 1.0, -0.4), (x1 - 21.0, y0 + 1.6, 0.1), m["die_g"], die_g)
    show(die_g, [])
    bx("gp_tim", (x0 + 20.0, y0 + 2.0, zb + 10.0), (x1 - 20.0, y0 + 3.0, 0.0), m["ink"], g)
    bx("gp_base", (x0, y0 + 3.0, zb), (x1, y0 + 9.0, 0.0), m["copper"], g)
    fins = []
    n = 22
    for k in range(n):
        x = x0 + 6.0 + (x1 - x0 - 12.0) * k / (n - 1)
        fins.append(bx(f"gp_f{k}", (x - 0.6, y0 + 9.0, zb + 4.0), (x + 0.6, y0 + 24.0, -1.0), m["copper"], g))
    D.join(fins, "gp_fins")
    chan = empty("gp_chan", root)
    for k in range(n - 1):
        x = x0 + 6.0 + (x1 - x0 - 12.0) * (k + 0.5) / (n - 1)
        bx(f"gp_c{k}", (x - 0.8, y0 + 10.0, -1.2), (x + 0.8, y0 + 23.0, -0.6), m["chan_g"], chan)
    show(chan, [])
    bx("gp_lid", (x0, y0 + 24.0, zb), (x1, y0 + 30.0, 0.0), m["copper"], g)
    bx("gp_lidback", (x0, y0 + 9.0, zb), (x1, y0 + 24.0, zb + 4.0), m["copper"], g)
    for k, (xp, mt) in enumerate(((x0 + 15.0, "pipe_s"), (x1 - 15.0, "pipe_r"))):
        tube(f"gp_port{k}", (xp, y0 + 30.0, -25.0), (xp, y0 + 44.0, -25.0), 4.0, m[mt], g, 16)
    yi = y0 + 37.0
    flow = [(x0 + 15.0, y0 + 44.0, -25.0), (x0 + 15.0, y0 + 26.0, -12.0), (x0 + 12.0, y0 + 16.0, -2.0),
            ((x0 + x1) / 2, y0 + 12.0, -2.0), (x1 - 12.0, y0 + 16.0, -2.0), (x1 - 15.0, y0 + 26.0, -12.0), (x1 - 15.0, y0 + 44.0, -25.0)]
    return {"die_g": die_g, "chan": chan, "flow": flow, "top": ((x0 + x1) / 2, y0 + 30.0, -25.0), "yi": yi}


def build_tank(m, root):
    x0, x1, z0, z1 = TK
    g = empty("tank", root)
    bx("tk_base", (x0, 0.0, z0), (x1, 8.0, z1), m["rack"], g)
    bx("tk_back", (x0, 8.0, z0), (x1, 100.0, z0 + 3.0), m["skin"], g)
    bx("tk_l", (x0, 8.0, z0), (x0 + 3.0, 100.0, z1), m["skin"], g)
    bx("tk_r", (x1 - 3.0, 8.0, z0), (x1, 100.0, z1), m["skin"], g)
    bx("tk_fluid", (x0 + 3.0, 8.0, z0 + 3.0), (x1 - 3.0, 86.0, z1), m["fluid"], g)
    blades = []
    for k in range(9):
        x = x0 + 12.0 + 10.5 * k
        blades.append(bx(f"tk_b{k}", (x, 14.0, z0 + 10.0), (x + 3.0, 92.0, z1 - 10.0), m["mask"], g))
        bx(f"tk_h{k}", (x - 0.5, 92.0, z0 + 10.0), (x + 3.5, 96.0, z1 - 10.0), m["tray"], g)
    D.join(blades, "tk_blades")
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-220.0, -4.0, -160.0), (420.0, 0.0, 30.0), m["floor"], root)
    leds = build_rack(m, root)
    phx = build_cdu(m, root)
    hose = build_tray(m, root)
    gp = build_plate(m, root)
    build_tank(m, root)
    # magnifier from tray plate 0 to the giant plate
    C.magnify(m, root, (TB[0] + 35.0, TB[3] + 7.0, -55.0), (GP[0] - 2.0, GP[2] + 15.0, -25.0), r=4.0)
    # rack loop piping: CDU -> under floor-level header -> rack manifolds
    x0c, x1c = CDU[0], CDU[1]
    sup = [(x0c + 25.0, 18.0, -60.0), (x0c + 25.0, 18.0, -110.0), (x1c, 14.0, -110.0), (-18.0, 14.0, -110.0),
           (-18.0, 14.0, RZ0 + 5.0), (-18.0, 190.0, RZ0 + 5.0)]
    ret = [(-8.0, 190.0, RZ0 + 5.0), (-8.0, 200.0, RZ0 + 5.0), (-8.0, 215.0, -100.0), (x1c - 10.0, 215.0, -100.0),
           (x1c - 10.0, 120.0, -60.0), (x0c + 70.0, 120.0, -60.0)]
    polyline("loop_sup", sup[1:5], 3.0, m["pipe_s"], root)
    polyline("loop_ret", ret[1:5], 3.0, m["pipe_r"], root)
    fac_in = [(x0c + 10.0, 300.0, -40.0), (x0c + 10.0, 135.0, -40.0), (x0c + 20.0, 135.0, -40.0)]
    fac_out = [(x0c + 20.0, 90.0, -40.0), (x0c + 2.0, 90.0, -40.0), (x0c + 2.0, 300.0, -40.0)]
    polyline("fac_in", fac_in[:2], 4.0, m["pipe_s"], root)
    polyline("fac_out", fac_out[1:], 4.0, m["pipe_r"], root)

    all_b = [0, 1, 2, 3, 4]
    for k in range(5):
        blink(leds, k, [0, 2, 4, 6], n=8, on=0.7)
    rise(root, "rk_heat", ((RX0 + RX1) / 2, RH + 4.0, -60.0), 8, 3.0, m["heat"], [0], 0.0, 0.85, 60.0, 50, (20.0, 40.0))
    # beat 0 + 2: tray hose flow
    run(root, "hose_c", hose[:3], 5, 1.6, m["c_cool"], [0, 2], 0.0, 0.7, 40)
    run(root, "hose_w", hose[2:], 5, 1.6, m["c_warm"], [0, 2], 0.2, 0.85, 40)
    # beat 1: giant plate
    show(gp["die_g"], [(F(1, 0), F(2, 0))])
    show(gp["chan"], [(F(1, 0.2), F(2, 0))])
    run(root, "gp_flow", gp["flow"][:4], 6, 1.8, m["c_cool"], [1], 0.05, 0.6, 40)
    run(root, "gp_flow2", gp["flow"][3:], 6, 1.8, m["c_warm"], [1], 0.25, 0.8, 40)
    rise(root, "gp_heat", ((GP[0] + GP[1]) / 2, GP[2] + 2.0, -1.0), 6, 1.2, m["heat"], [1], 0.0, 0.8, 8.0, 30, (25.0, 0.0))
    # beat 2-4: rack loop
    run(root, "loop_c", sup, 12, 3.6, m["c_cool"], [2, 3, 4], 0.0, 0.7, 70)
    run(root, "loop_w", ret, 12, 3.6, m["c_warm"], [2, 3, 4], 0.1, 0.8, 70)
    # beat 3: facility water through the PHX
    show(phx, [(F(3, 0.1), F(4, 0))])
    run(root, "fac_c", fac_in, 7, 4.0, m["c_cool"], [3, 4], 0.0, 0.7, 50)
    run(root, "fac_w", fac_out, 7, 4.0, m["c_warm"], [3, 4], 0.15, 0.8, 50)
    # beat 4: immersion tank bubbles of warm fluid rising
    rise(root, "tk_heat", ((TK[0] + TK[1]) / 2, 20.0, (TK[2] + TK[3]) / 2), 10, 1.8, m["c_warm"], [4], 0.0, 0.85, 60.0, 45, (45.0, 25.0))
    _ = all_b

    tags = {
        0: [("AI rack: 120+ kW", (-30.0, RH + 10.0, -60.0)), ("compute tray, lid off", (TB[0] + 55.0, TB[3] + 12.0, -25.0)),
            ("liquid lines on every tray", (TB[0] + 90.0, TB[3] + 9.0, TB[2] + 8.0))],
        1: [("cold plate, cut open", gp["top"]), ("microchannel fins", (GP[0] + 45.0, GP[2] + 18.0, 0.0)),
            ("GPU die under thin paste", (GP[0] + 45.0, GP[2], 0.0)), ("in cool, out warm", (GP[1] - 15.0, GP[2] + 44.0, -25.0))],
        2: [("rear supply manifold", (-18.0, 100.0, RZ0 + 5.0)), ("return manifold", (-8.0, 160.0, RZ0 + 5.0)),
            ("dripless quick disconnects", (TB[0] + 20.0, TB[3] + 9.0, TB[2] + 2.0))],
        3: [("CDU: pumps + reservoir", (CDU[0] + 25.0, 58.0, -60.0)), ("plate heat exchanger", (CDU[0] + 40.0, 140.0, -40.0)),
            ("facility water in / out", (CDU[0] + 6.0, 250.0, -40.0))],
        4: [("immersion: servers in fluid", ((TK[0] + TK[1]) / 2, 100.0, TK[2] + 10.0)), ("VRT, NVT, MOD, Schneider", (CDU[0] + 40.0, CDU[3], -60.0)),
            ("SMCI ships racks plumbed", (-30.0, RH + 10.0, -60.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-10.0, 100.0, -60.0), 330.0, 0.30, 0.30),
        frame(((GP[0] + GP[1]) / 2, GP[2] + 15.0, -15.0), 110.0, 0.15, 0.25),
        frame((-30.0, 100.0, -100.0), 280.0, 2.3, 0.30),
        frame((CDU[0] + 40.0, 120.0, -60.0), 230.0, -0.30, 0.20),
        frame((100.0, 110.0, -60.0), 620.0, 0.15, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
