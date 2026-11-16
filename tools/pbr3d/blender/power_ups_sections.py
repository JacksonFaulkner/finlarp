"""The UPS node's nine numbered sections (POWER tab), in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_UPS.txt;
the tenth heading (Sources) is text only. Three beats each, one beat is 8 s.

Run from the repo root, one section per run:

    blender -b --factory-startup --python tools/pbr3d/blender/power_ups_sections.py -- <n>

Writes blender/power_ups_section_<n>.blend and assets/power_ups_section_<n>.glb. Every section is built
on the cut-open site of power_ups_detail.plant (utility pole, generator, transfer switch, rectifier,
DC link, inverter, static bypass, Li-ion cabinets, racks); close-ups (a cut-open lithium-ion cell, a
VRLA block, gensets on their pads) stand on a bench to the right of the racks, at x >= BX.

  1 what happens     normal flow; the utility fails and the batteries carry; the generator takes over
  2 the parts        rectifier / DC link / inverter; Li-ion cabinets; generator and transfer switch
  3 a power cut      utility drops + inverter on battery; start signal, ~10 s; transfer, recharge, back
  4 double conv.     dirty in, clean out; 3-5% lost as heat; eco mode through the static bypass
  5 batteries        a Li-ion cell cut open; Li-ion vs lead-acid; runtime: minutes, not hours
  6 generators       the genset cut open; start within 10 s; a row of sets with fuel on site
  7 AI loads         GPU racks swing; the swings travel upstream; in-rack batteries smooth them
  8 who makes it     UPS makers; generator makers; battery makers
  9 chokepoints      generator lead times and permits; losses scale; spiky loads
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, ball, label, beat, show, key, P  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import power_ups_detail as D  # noqa: E402
from power_ups_detail import frame, camera_path, flow, rise, soc, engine_run, drops_flow, cable, cable_obj, arch  # noqa: E402

PAGE = "power_ups"
BEATS = 3
BX = 700.0  # the bench, right of the racks
G = D.GX0


def setup(name):
    _, root = start(name, beats=BEATS, page=PAGE)
    m = D.materials()
    return m, root


def after(b, u):
    return [(F(b, u), F(BEATS, 0))]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, items):
    for b, lst in items.items():
        for text, p in lst:
            label(text, p, root, beat(b))


def normal(S, root, m, beats, rect=True):
    """The everyday flow in the given beats: utility through the double conversion to the racks."""
    P_ = S["paths"]
    r = [(b, 0.0, 0.85) for b in beats]
    flow(root, "n_util", P_["util"], m["ac"], r, n=9)
    if rect:
        flow(root, "n_rect", P_["rect"], m["dc"], r, n=6)
    flow(root, "n_inv", P_["inv"], m["ac"], r, n=10)


def site(m, root, blade="u"):
    S = D.plant(m, root)
    at = S["ats"]
    if blade == "u":
        show(at["blade_g"], [])
    return S


# poses the sections share
WIDE = frame((-720.0, 170.0, -40.0), 1900.0, 0.30, 0.36, pad=0.86)
UPSROW = frame((-560.0, 220.0, -80.0), 1150.0, 0.28, 0.28, pad=0.95)
CONV = frame((-620.0, 115.0, -30.0), 380.0, 0.26, 0.16)
BATTS = frame((-242.0, 120.0, -20.0), 330.0, 0.32, 0.18)
GENSET = frame((G + 290.0, 180.0, 0.0), 620.0, 0.26, 0.20)
GEN_ATS = frame((-1160.0, 200.0, -20.0), 1080.0, 0.26, 0.24, pad=0.95)
RACKS = frame((83.0, 140.0, -30.0), 330.0, 0.30, 0.20)


# ---- 1 what happens ------------------------------------------------------------------------------


def sec1(m, root):
    S = site(m, root)
    at, gp, P_ = S["ats"], S["gen"], S["paths"]
    show(at["blade_u"], span(0, 0, 2, 0.3))
    show(at["blade_g"], after(2, 0.3))
    show(S["dead"], after(1, 0.12))
    show(at["led_u"], span(0, 0, 1, 0.12))
    show(at["led_g"], after(2, 0.15))
    normal(S, root, m, [0])
    flow(root, "inv12", P_["inv"], m["ac"], [(1, 0.0, 0.85), (2, 0.0, 0.85)], n=10)
    flow(root, "util1", P_["util"], m["ac"], [(1, 0.0, 0.03)], n=3)
    drops_flow(root, S, m["ac"], [(0, 0, 0.85), (1, 0, 0.85), (2, 0, 0.85)])
    flow(root, "chg", P_["charge"], m["dc"], [(0, 0.0, 0.85), (2, 0.4, 0.9)], n=6)
    flow(root, "dis", P_["discharge"], m["bat"], [(1, 0.12, 0.9), (2, 0.0, 0.3)], n=7)
    engine_run(gp, F(1, 0.55), F(3, 0))
    rise(root, "smoke", gp["stack"], m["smoke"], [(1, 0.6, 0.95), (2, 0.0, 0.9)], n=10, size=8.0, height=140, spread=(20, 10))
    flow(root, "gen", P_["gen"], m["gen"], [(2, 0.3, 0.9)], n=8)
    flow(root, "rect2", P_["rect"], m["dc"], [(2, 0.36, 0.9)], n=6)
    soc(S["bats"], [(0, 1.0), (F(1, 0.12), 1.0), (F(2, 0.3), 0.45), (F(3, 0), 0.8)])
    C, dl, iv, rk = S["C"], S["dcl"], S["inv"], S["racks"]
    tags(root, {
        0: [("utility in", C["util_drop"][4]), ("RECTIFIER: AC to DC", S["rect"]["top"]), ("INVERTER: clean AC", iv["top"]),
            ("Li-ion batteries kept charged", S["bats"][1]["top"]), ("racks", rk["top"])],
        1: [("utility fails", C["util_drop"][5]), ("batteries feed the DC", C["dc_batt"][7]), ("inverter: no break at all", iv["top"]),
            ("racks keep running", rk["top"])],
        2: [("GENERATOR starts", gp["alt"]), ("TRANSFER SWITCH moves", at["top"]), ("generator power in", C["gen_out"][7]),
            ("batteries recharge", S["bats"][0]["top"])],
    })
    camera_path(root, [WIDE, UPSROW, frame((-930.0, 200.0, -40.0), 1450.0, 0.28, 0.30, pad=0.92)])


# ---- 2 the parts ---------------------------------------------------------------------------------


def sec2(m, root):
    S = site(m, root)
    at, gp, P_ = S["ats"], S["gen"], S["paths"]
    show(at["blade_u"], span(0, 0, 2, 0.3))
    show(at["blade_g"], after(2, 0.3))
    show(S["dead"], after(2, 0.0))
    normal(S, root, m, [0, 1])
    flow(root, "inv2", P_["inv"], m["ac"], [(2, 0.0, 0.85)], n=10)
    flow(root, "chg", P_["charge"], m["dc"], [(1, 0.0, 0.85)], n=6)
    soc(S["bats"], [(0, 0.6), (F(1, 0.05), 0.6), (F(1, 0.85), 1.0), (F(3, 0), 1.0)])
    engine_run(gp, F(2, 0.0), F(3, 0))
    rise(root, "smoke", gp["stack"], m["smoke"], [(2, 0.0, 0.9)], n=8, size=8.0, height=140, spread=(20, 10))
    flow(root, "gen", P_["gen"], m["gen"], [(2, 0.3, 0.9)], n=8)
    flow(root, "rect2", P_["rect"], m["dc"], [(2, 0.36, 0.9)], n=6)
    rc, dl, iv, bt, C = S["rect"], S["dcl"], S["inv"], S["bats"], S["C"]
    for nm, x in (("rect", rc), ("inv", iv)):
        rise(root, f"heat_{nm}", x["heat"][1], m["heat"], [(0, 0.1, 0.85)], n=6, size=4.0, height=90, spread=(70, 20))
    tags(root, {
        0: [("RECTIFIER: AC to DC", rc["top"]), ("DC link", dl["top"]), ("INVERTER: DC to AC", iv["top"]),
            ("EFFICIENCY: a few % as heat", rc["heat"][1])],
        1: [("LITHIUM-ION cabinets", bt[1]["top"]), ("RUNTIME: minutes", bt[2]["mod"]), ("DC link charges them", C["dc_batt"][7])],
        2: [("GENERATOR: diesel + alternator", gp["alt"]), ("about 2-3 MW per unit", gp["panel"]), ("TRANSFER SWITCH", at["top"])],
    })
    camera_path(root, [frame((-620.0, 125.0, -30.0), 400.0, 0.26, 0.16), BATTS, GEN_ATS])


# ---- 3 a power cut, in order ------------------------------------------------------------------------


def sec3(m, root):
    S = site(m, root)
    at, gp, P_ = S["ats"], S["gen"], S["paths"]
    show(at["blade_u"], [(0, F(2, 0.12)), (F(2, 0.62), F(3, 0))])
    show(at["blade_g"], span(2, 0.12, 2, 0.62))
    show(S["dead"], span(0, 0.15, 2, 0.55))
    show(at["led_u"], [(0, F(0, 0.15)), (F(2, 0.55), F(3, 0))])
    show(at["led_g"], span(1, 0.8, 3, 0))
    sp = empty("s3_spark", root)
    ball("s3_spark_b", (at["pv"][0] - 20, 110.0, -18.0), 7.0, m["spark"], sp, 12)
    show(sp, [(F(2, 0.10), F(2, 0.15)), (F(2, 0.60), F(2, 0.65))])
    flow(root, "util0", P_["util"], m["ac"], [(0, 0.0, 0.1), (2, 0.62, 0.9)], n=6)
    flow(root, "inv", P_["inv"], m["ac"], [(0, 0, 0.85), (1, 0, 0.85), (2, 0, 0.85)], n=10)
    drops_flow(root, S, m["ac"], [(0, 0, 0.85), (2, 0, 0.85)])
    flow(root, "dis", P_["discharge"], m["bat"], [(0, 0.15, 0.9), (1, 0.0, 0.9), (2, 0.0, 0.1)], n=7)
    flow(root, "gen", P_["gen"], m["gen"], [(2, 0.12, 0.5)], n=7)
    flow(root, "chg", P_["charge"], m["dc"], [(2, 0.18, 0.85)], n=6)
    flow(root, "rect", P_["rect"], m["dc"], [(2, 0.16, 0.85)], n=6)
    # the start signal: a control cable from the switch's controller to the genset's panel
    ctl = cable("s3_ctl", arch((at["ctl"][0], D.H + 2, -50.0), (gp["panel"][0] + 10, 290.0, -20.0), (0, 120, -30), 18), 1.6, m["cable"], root)
    flow(root, "sig", ctl, m["signal"], [(1, 0.0, 0.2)], n=5, size=4.0, speed=22)
    engine_run(gp, F(1, 0.3), F(3, 0))
    rise(root, "smoke", gp["stack"], m["smoke"], [(1, 0.32, 0.95), (2, 0.0, 0.9)], n=10, size=8.0, height=140, spread=(20, 10))
    soc(S["bats"], [(0, 1.0), (F(0, 0.15), 1.0), (F(2, 0.12), 0.5), (F(3, 0), 0.85)])
    C, iv = S["C"], S["inv"]
    tags(root, {
        0: [("1 the utility feed drops", C["util_drop"][5]), ("2 inverter runs on battery DC", iv["top"]),
            ("no interruption", S["racks"]["top"])],
        1: [("3 start signal", ctl[9]), ("4 at voltage and speed in ~10 s", gp["alt"]), ("engine fires", gp["piston"])],
        2: [("5 TRANSFER SWITCH: to generators", at["top"]), ("6 batteries recharge", C["dc_batt"][7]),
            ("utility back: load moves back", C["util_drop"][4])],
    })
    camera_path(root, [UPSROW, frame((-1200.0, 210.0, -30.0), 900.0, 0.26, 0.24), frame((-1000.0, 210.0, -40.0), 1250.0, 0.28, 0.28, pad=0.95)])


# ---- 4 why double conversion ---------------------------------------------------------------------------


def wave(m, root, x0, x1, y, z, mt, name, dirty=False, cycles=3):
    pts = []
    n = 60
    for i in range(n + 1):
        u = i / n
        a = 22 * math.sin(2 * math.pi * cycles * u)
        if dirty:
            if 0.30 < u < 0.48:
                a *= 0.45  # a sag
            if abs(u - 0.68) < 0.02:
                a += 30  # a spike
            if u > 0.86:
                a = 0.0  # the outage
        pts.append((x0 + (x1 - x0) * u, y + a, z))
    return cable_obj(name, pts, 1.8, mt, root, 6)


def sec4(m, root):
    S = site(m, root)
    P_, rc, iv, ss = S["paths"], S["rect"], S["inv"], S["ss"]
    normal(S, root, m, [0, 1])
    drops_flow(root, S, m["ac"], [(0, 0, 0.85), (1, 0, 0.85), (2, 0, 0.85)])
    w = empty("s4_waves", root)
    wave(m, w, -905.0, -775.0, 330.0, -20.0, m["wave_dirty"], "s4_dirty", dirty=True)
    wave(m, w, -575.0, -455.0, 330.0, -20.0, m["wave_clean"], "s4_clean")
    show(w, beat(0))
    for nm, x in (("rect", rc), ("inv", iv)):
        for k, h in enumerate(x["heat"]):
            rise(root, f"heat_{nm}{k}", h, m["heat"], [(1, 0.05, 0.85)], n=9, size=5.0, height=110, spread=(80, 20), seed=k + 2)
    show(ss["glow"], beat(2))
    flow(root, "eco_u", P_["util_bypass"], m["ac"], [(2, 0.0, 0.85)], n=8)
    flow(root, "eco_b", P_["bypass"], m["ac"], [(2, 0.0, 0.85)], n=9)
    C = S["C"]
    tags(root, {
        0: [("utility: sags, spikes, outage", (-840.0, 360.0, -20.0)), ("every watt rectified", rc["top"]),
            ("and inverted again", iv["top"]), ("clean AC to the racks", (-515.0, 360.0, -20.0))],
        1: [("two conversions lose 3-5%", rc["heat"][1]), ("as heat off the heatsinks", iv["hs"]), ("heat that must be cooled", iv["heat"][1])],
        2: [("eco mode: static bypass on", ss["scr"]), ("utility goes around", C["bypass"][9]), ("conversion skipped", rc["top"])],
    })
    camera_path(root, [frame((-680.0, 200.0, -30.0), 560.0, 0.26, 0.18), CONV, frame((-620.0, 220.0, -60.0), 560.0, 0.24, 0.24)])


# ---- 5 batteries and runtime ------------------------------------------------------------------------------


def sec5(m, root):
    S = site(m, root)
    P_ = S["paths"]
    # beat 0: four prismatic cells on the bench, the front one cut open
    box("s5_bench", (BX - 20, 0, -120), (BX + 160, 40, 20), m["cab_dark"], root)
    cells = [D.li_cell(m, root, (BX + 10 + 34 * k, 40.0, 0.0), 6.0, f"s5_cell{k}") for k in range(4)]
    c0 = cells[0]
    # beat 1: a Li-ion cabinet and a lead-acid cabinet holding the same energy, and a VRLA block cut open
    LX = BX + 260
    li = D.li_cabinet(m, root, LX, LX + 76, "s5_li")
    D.vrla_cabinet(m, root, LX + 100, LX + 230, "s5_vrla")
    D.vrla_cabinet(m, root, LX + 236, LX + 366, "s5_vrla2")
    vb = D.vrla_block(m, root, (LX + 380, 0.0, 0.0), 4.0, "s5_block")
    soc([li], [(0, 1.0), (F(3, 0), 1.0)])
    # beat 2: runtime: the site's cabinets drain; carrying hours would need rows more
    ghost = empty("s5_ghost", root)
    for r_, z in enumerate((-100.0, -190.0, -280.0)):
        for k, (a, b) in enumerate(D.BATT_X):
            box(f"s5_g{r_}{k}", (a, 0, z - 80), (b, D.H, z), m["ghost"], ghost)
    show(ghost, after(2, 0.45))
    flow(root, "dis", P_["discharge"], m["bat"], [(2, 0.0, 0.9)], n=7)
    flow(root, "inv", P_["inv"], m["ac"], [(2, 0.0, 0.9)], n=10)
    show(S["dead"], beat(2))
    soc(S["bats"], [(0, 1.0), (F(2, 0.0), 1.0), (F(2, 0.95), 0.15), (F(3, 0), 0.15)])
    tags(root, {
        0: [("LITHIUM-ION cell, cut open", (BX + 60, 98.0, -40.0)), ("graphite anode", c0["anode"]), ("separator", c0["sep"]),
            ("oxide cathode on Al foil", c0["cathode"])],
        1: [("Li-ion: smaller, lighter", li["top"]), ("lead-acid (VRLA), same energy", (LX + 233, D.H, -40.0)),
            ("lead plates in each cell", vb["plates"]), ("Li-ion lasts longer", li["mod"])],
        2: [("RUNTIME: minutes", S["bats"][1]["mod"]), ("enough to start the generators", S["C"]["dc_batt"][8]),
            ("hours: far more cabinets", (-242.0, D.H, -230.0))],
    })
    camera_path(root, [frame((BX + 70, 70.0, -20.0), 150.0, 0.28, 0.18),
                       frame((LX + 250, 110.0, -30.0), 540.0, 0.24, 0.18),
                       frame((-250.0, 140.0, -120.0), 520.0, 0.36, 0.34)])


# ---- 6 generators -----------------------------------------------------------------------------------------


def gen_row(m, root, zs, name):
    row = []
    for k, z in enumerate(zs):
        box(f"{name}_pad{k}", (G - 30, 0, z - 110), (G + D.GEN_L + 30, 3, z + 110), m["concrete"], root)
        row.append(D.generator(m, root, G, f"{name}{k}", cut_open=False, zc=z))
    return row


def sec6(m, root):
    S = site(m, root)
    gp, P_, at = S["gen"], S["paths"], S["ats"]
    box("s6_yard", (G - 60, -6, -900), (G + D.GEN_L + 60, -0.4, -120), m["floor"], root)
    row = gen_row(m, root, (-260.0, -500.0, -740.0), "s6_gs")
    engine_run(gp, F(1, 0.1), F(3, 0))
    rise(root, "smoke", gp["stack"], m["smoke"], [(1, 0.12, 0.9), (2, 0.0, 0.9)], n=10, size=8.0, height=140, spread=(20, 10))
    for k, g in enumerate(row):
        rise(root, f"smk{k}", g["stack"], m["smoke"], [(2, 0.05 + 0.1 * k, 0.9)], n=5, size=8.0, height=120, spread=(20, 10), seed=k)
    flow(root, "gen", P_["gen"], m["gen"], [(1, 0.8, 0.95), (2, 0.0, 0.9)], n=8)
    show(at["blade_u"], span(0, 0, 1, 0.78))
    show(at["blade_g"], after(1, 0.78))
    show(S["dead"], after(1, 0.0))
    tags(root, {
        0: [("diesel engine: six cylinders", gp["engine"]), ("alternator: stator + rotor", gp["alt"]), ("radiator and fan", gp["radiator"]),
            ("fuel tank in the base", gp["tank"])],
        1: [("pistons firing", gp["piston"]), ("NFPA 110 Type 10: within 10 s", gp["panel"]), ("power out to the switch", S["C"]["gen_out"][6])],
        2: [("a row of gensets outside", row[1]["top"]), ("about 2-3 MW each", row[0]["c"]), ("fuel on site: a day or more", row[2]["top"])],
    })
    camera_path(root, [frame((G + 290.0, 170.0, 0.0), 600.0, 0.24, 0.16), GENSET,
                       frame((G + 300.0, 170.0, -380.0), 1000.0, 0.55, 0.32, pad=0.95)])


# ---- 7 AI loads are spiky -------------------------------------------------------------------------------------


SPIKES = [(0.00, 1), (0.10, 0), (0.18, 1), (0.30, 0), (0.36, 1), (0.50, 0), (0.56, 1), (0.70, 0), (0.78, 1), (0.92, 0)]


def gpu_pulse(S, b, smooth=False):
    """GPU lights on (busy) and off (idle) together, in step with SPIKES, during beat b."""
    return [(F(b, u), F(b, SPIKES[i + 1][0] if i + 1 < len(SPIKES) else 1.0)) for i, (u, on) in enumerate(SPIKES) if on]


def trace(m, root, x0, x1, y, z, b, name, flat=False):
    """A power trace over the racks, drawn left to right through beat b: square steps, or flat."""
    g = empty(name, root)
    pts = []
    for i, (u, on) in enumerate(SPIKES):
        u1 = SPIKES[i + 1][0] if i + 1 < len(SPIKES) else 1.0
        h = (40.0 if on else 0.0) if not flat else 22.0
        pts += [(x0 + (x1 - x0) * u, y + h, z), (x0 + (x1 - x0) * u1, y + h, z)]
    segs = []
    for k in range(len(pts) - 1):
        if math.dist(pts[k], pts[k + 1]) < 1e-3:  # a flat trace repeats its joints: nothing to draw
            continue
        e = empty(f"{name}_s{k}", g)
        cable_obj(f"{name}_c{k}", [pts[k], pts[k + 1]], 2.0, m["wave_dirty" if not flat else "wave_clean"], e, 6)
        show(e, [(F(b, 0.9 * k / (len(pts) - 1)), F(b + 1, 0))])
        segs.append(e)
    return pts


def sec7(m, root):
    S = site(m, root)
    rk, P_, gp = S["racks"], S["paths"], S["gen"]
    for k, g in enumerate(rk["leds"]):
        show(g, gpu_pulse(S, 0) + gpu_pulse(S, 1) + [(F(2, 0), F(3, 0))])
    x0, x1 = D.RACK_X0, rk["x1"]
    trace(m, root, x0, x1, 290.0, -20.0, 0, "s7_tr0")
    trace(m, root, -560.0, -300.0, 330.0, -20.0, 1, "s7_tr1")
    trace(m, root, x0, x1, 290.0, -20.0, 2, "s7_tr2", flat=True)
    # bursts: power rushes in when the GPUs step up together
    bursts = [(b, u, u + 0.06) for b in (0, 1) for u, on in SPIKES if on]
    flow(root, "burst", P_["inv"], m["ac"], bursts, n=4, size=6.0, speed=16)
    drops_flow(root, S, m["ac"], bursts)
    flow(root, "rect", P_["rect"], m["dc"], [(1, u, u + 0.06) for u, on in SPIKES if on], n=3)
    flow(root, "util", P_["util"], m["ac"], [(1, u, u + 0.06) for u, on in SPIKES if on], n=3)
    # beat 2: in-rack battery shelves soak up the swings; steady flow upstream
    bbu = empty("s7_bbu", root)
    for r in range(D.NRACK):
        rx = x0 + r * (D.RACK_W + 2)
        box(f"s7_bbu{r}", (rx + 3, 8, -20), (rx + D.RACK_W - 3, 26, 0.5), m["batt_cab"], bbu)
        box(f"s7_bbu{r}_l", (rx + 8, 14, 0.5), (rx + D.RACK_W - 8, 19, 1.2), m["bat"], bbu)
    show(bbu, beat(2))
    flow(root, "steady", P_["inv"], m["ac"], [(2, 0.0, 0.85)], n=10)
    drops_flow(root, S, m["ac"], [(2, 0.0, 0.85)], name="sdrop")
    tags(root, {
        0: [("GPUs: full power, then idle", rk["top"]), ("ms swings, all in step", (x0 + 130.0, 340.0, -20.0)),
            ("training steps sync up", rk["c"])],
        1: [("swings reach the UPS", S["inv"]["top"]), ("and the generators, the grid", S["C"]["util_drop"][4]),
            ("rapid swings: stress", (-430.0, 380.0, -20.0))],
        2: [("batteries / capacitors in the rack", (x0 + 30.0, 20.0, 0.0)), ("swings smoothed", (x0 + 130.0, 320.0, -20.0)),
            ("steady draw upstream", rk["in"])],
    })
    camera_path(root, [frame((90.0, 180.0, -30.0), 380.0, 0.30, 0.20), frame((-300.0, 230.0, -50.0), 780.0, 0.26, 0.24),
                       frame((90.0, 150.0, -30.0), 380.0, 0.30, 0.18)])


# ---- 8 who makes it --------------------------------------------------------------------------------------------


def sec8(m, root):
    S = site(m, root)
    normal(S, root, m, [0])
    drops_flow(root, S, m["ac"], [(0, 0, 0.85)])
    box("s8_yard", (G - 60, -6, -900), (G + D.GEN_L + 60, -0.4, -120), m["floor"], root)
    row = gen_row(m, root, (-260.0, -500.0, -740.0), "s8_gs")
    box("s8_bench", (BX - 20, 0, -120), (BX + 160, 40, 20), m["cab_dark"], root)
    cells = [D.li_cell(m, root, (BX + 10 + 34 * k, 40.0, 0.0), 6.0, f"s8_cell{k}") for k in range(4)]
    gp = S["gen"]
    tags(root, {
        0: [("Vertiv (VRT)", S["rect"]["top"]), ("Schneider Electric", S["dcl"]["top"]), ("Eaton (ETN)", S["inv"]["top"]),
            ("ABB", S["ss"]["top"])],
        1: [("Caterpillar (CAT)", gp["stack"]), ("Cummins (CMI)", row[0]["top"]), ("Rolls-Royce (mtu)", row[1]["top"]),
            ("Kohler", row[2]["top"])],
        2: [("Samsung SDI", cells[0]["pos"]), ("LG", cells[1]["pos"]), ("CATL", cells[2]["pos"]), ("and others", cells[3]["pos"])],
    })
    camera_path(root, [frame((-640.0, 160.0, -30.0), 560.0, 0.26, 0.20),
                       frame((G + 300.0, 170.0, -380.0), 1000.0, 0.55, 0.32, pad=0.95),
                       frame((BX + 70, 80.0, -20.0), 170.0, 0.28, 0.24)])


# ---- 9 chokepoints and risks -----------------------------------------------------------------------------------


def truck(m, root, x, z, name):
    g = empty(name, root)
    box(f"{name}_bed", (x, 30, z - 100), (x + 640, 42, z + 100), m["skid"], g)
    box(f"{name}_cab", (x + 640, 20, z - 100), (x + 760, 220, z + 100), m["truck"], g)
    box(f"{name}_win", (x + 700, 150, z + 100), (x + 750, 205, z + 101), m["glass"], g)
    for k, xx in enumerate((x + 60, x + 140, x + 560, x + 700)):
        for zz in (z - 90, z + 90):
            D.rod(f"{name}_w{k}{zz}", (xx, 20, zz - 12), (xx, 20, zz + 12), 20.0, m["tyre"], g, False, 16)
    gs = D.generator(m, g, x + 40, f"{name}_gs", cut_open=False, zc=z)
    import bpy
    bpy.data.objects[f"{name}_gs"].location.z += 42.0
    gs["top"] = (gs["top"][0], gs["top"][1] + 42.0, gs["top"][2])
    return g, gs


def sec9(m, root):
    S = site(m, root)
    # beat 0: on the bench, pads waiting for gensets; one arrives on a truck; air permits for diesel
    QX = BX + 100
    for k, z in enumerate((0.0, -260.0, -520.0)):
        box(f"s9_pad{k}", (QX - 30, 0, z - 110), (QX + D.GEN_L + 30, 3, z + 110), m["concrete"], root)
    box("s9_lot", (QX - 300, -6, -700), (QX + 1500, 0, 160), m["floor"], root)
    g1 = D.generator(m, root, QX, "s9_gs", cut_open=False, zc=-520.0)
    rise(root, "s9_smoke", g1["stack"], m["smoke"], [(0, 0.05, 0.9)], n=8, size=9.0, height=140, spread=(20, 10))
    tg, tgs = truck(m, root, QX + 900, 0.0, "s9_truck")
    key(tg, F(0, 0.0), "location", P(700, 0, 0), linear=True)
    key(tg, F(0, 0.7), "location", P(0, 0, 0), linear=True)
    # beat 1: losses scale: the conversion cabinets and more of them, all shedding heat
    CX = BX + 1800
    box("s9_hall", (CX - 60, -6, -200), (CX + 700, 0, 60), m["floor"], root)
    cvs = [(CX + k * 130, CX + 120 + k * 130) for k in range(5)]
    for k, (a, b) in enumerate(cvs):
        D.converter(m, root, a, b, f"s9_cv{k}", "inv" if k % 2 else "rect")
    for x in cvs:
        rise(root, f"s9_heat{x[0]:.0f}", ((x[0] + x[1]) / 2, 200.0, -35.0), m["heat"], [(1, 0.05, 0.85)], n=6, size=5.0,
             height=110, spread=(80, 20), seed=int(abs(x[0])) % 7)
    # beat 2: spiky racks stress the UPS
    rk, iv = S["racks"], S["inv"]
    for g in rk["leds"]:
        show(g, [(0, F(2, 0))] + gpu_pulse(S, 2))
    trace(m, root, D.RACK_X0, rk["x1"], 290.0, -20.0, 2, "s9_tr")
    bursts = [(2, u, u + 0.06) for u, on in SPIKES if on]
    flow(root, "s9_burst", S["paths"]["inv"], m["ac"], bursts, n=4, size=6.0, speed=16)
    warn = empty("s9_warn", root)
    ball("s9_warn_b", (iv["top"][0], D.H + 12, -20.0), 8.0, m["fault"], warn, 12)
    show(warn, [(F(2, u), F(2, u + 0.05)) for u, on in SPIKES if on])
    tags(root, {
        0: [("waiting on generator lead times", (QX + 280.0, 10.0, -260.0)), ("diesel exhaust: air permits", g1["stack"]),
            ("genset on its way", tgs["top"])],
        1: [("losses scale with every MW", (CX + 320.0, 260.0, -35.0)), ("each converter sheds heat", (CX + 60.0, 200.0, -35.0)),
            ("more MW, more converters", (CX + 580.0, 200.0, -35.0))],
        2: [("spiky AI loads", (D.RACK_X0 + 130.0, 340.0, -20.0)), ("UPS not designed for this", iv["top"]), ("GPU racks", rk["c"])],
    })
    camera_path(root, [frame((QX + 450.0, 150.0, -260.0), 1250.0, 0.45, 0.34, pad=0.92),
                       frame((CX + 320.0, 150.0, -30.0), 700.0, 0.28, 0.20, pad=0.95),
                       frame((-200.0, 200.0, -40.0), 620.0, 0.28, 0.22)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = setup(f"section_{n}")
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
