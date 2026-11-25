"""TRM_EPC_CONTRACTOR: one firm engineers, buys and builds a data center's power and cooling block.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_epc_contractor.py

A data center site seen from above the fence line: a site office with the design drawings, a
laydown yard where long-lead gear (transformers, switchgear, chillers) arrives by truck, a tower
crane over a half-built hall, and a schedule board (Gantt bars) on the office wall.

Beats:
  0 site      the whole job: office, laydown yard, crane, hall
  1 engineer  the design is drawn first: glowing layout lines on the empty slab
  2 procure   trucks bring transformer, switchgear and chiller; lead-time bars fill on the board
  3 build     crane sets gear, walls and racks go up, power and water flow in
  4 slip      one transformer is late: its bar runs red, the racks behind it stay dark
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from sand_overview import P, key  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, present  # noqa: E402

SLUG = "TRM_EPC_CONTRACTOR"
BEATS = [
    ("An EPC contractor engineers, buys and builds the whole job",
     "EPC stands for engineering, procurement and construction. One firm signs a contract to design the plant, order the "
     "equipment and run the crews that install it, usually for a fixed price or a guaranteed finish date. The owner gets "
     "one party to hold accountable instead of juggling dozens of trades."),
    ("Engineering comes first: the layout is drawn before steel goes up",
     "Engineers size the substation, switchgear, generators, chillers and piping, then lay every room, duct and cable "
     "tray out on drawings. On a data center the design is driven by the IT load in megawatts and the rack density, "
     "which sets how much power and cooling each hall needs."),
    ("Procurement: long-lead gear is ordered years ahead",
     "Large power transformers now take two to four years to arrive, and big switchgear and chillers well over a year. "
     "The EPC firm places those orders early, often before the design is final, and tracks every crate to the laydown "
     "yard. Whoever has secured factory slots can promise earlier dates."),
    ("Construction: crews set the gear and tie power and water in",
     "Cranes lift transformers and chillers onto pads, electricians pull cable and land it in switchgear, pipefitters "
     "join the chilled-water loops, and the hall is commissioned system by system. A large AI campus can have thousands "
     "of workers on site, and electrical and mechanical work is most of the cost."),
    ("One late part slips the date the capacity comes online",
     "If a transformer arrives late, everything it feeds waits: racks sit dark and the owner's revenue start slides. On "
     "a fixed-price job the contractor eats overruns, so margins depend on execution. Backlog at these firms has surged "
     "with AI builds. Related: Quanta Services (PWR), EMCOR (EME), Comfort Systems USA (FIX), Sterling Infrastructure (STRL)."),
]

# layout (units ~0.5 m). Hall x HX0..HX1, z HZ0..HZ1; laydown yard on the right; office on the left
HX0, HX1, HZ0, HZ1, HY = -60.0, 110.0, -140.0, -30.0, 30.0
YARD = (135.0, 235.0)
OFF = (-150.0, -90.0)


def mats(m):
    m["ground"] = mat("epc_ground", (0.36, 0.30, 0.22), rough=0.95)
    m["gravel"] = mat("epc_gravel", (0.45, 0.44, 0.40), rough=0.95)
    m["concrete"] = mat("epc_conc", (0.58, 0.58, 0.56), rough=0.9)
    m["crane"] = mat("epc_crane", (0.95, 0.72, 0.10), metal=0.3, rough=0.45)
    m["truck"] = mat("epc_truck", (0.75, 0.18, 0.15), metal=0.4, rough=0.4)
    m["crate"] = mat("epc_crate", (0.62, 0.46, 0.28), rough=0.8)
    m["xfmr"] = mat("epc_xfmr", (0.42, 0.50, 0.40), metal=0.4, rough=0.5)
    m["chiller"] = mat("epc_chiller", (0.78, 0.80, 0.82), metal=0.5, rough=0.4)
    m["rack"] = mat("epc_rack", (0.08, 0.08, 0.10), metal=0.5, rough=0.45)
    m["board"] = mat("epc_board", (0.12, 0.13, 0.16), rough=0.6)
    m["office"] = mat("epc_office", (0.85, 0.85, 0.82), rough=0.7)
    m["plan"] = mat("epc_plan", (0.40, 0.75, 1.0), emit=(0.35, 0.70, 1.0), strength=3.0)
    m["bar_ok"] = mat("epc_bar_ok", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=2.5)
    m["bar_late"] = mat("epc_bar_late", (1.0, 0.25, 0.15), emit=(1.0, 0.25, 0.15), strength=3.0)
    m["hv"] = mat("epc_hv", (1.0, 0.85, 0.40), emit=(1.0, 0.80, 0.30), strength=4.0)
    m["cold_b"] = mat("epc_cold", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0)
    m["led_g"] = mat("epc_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["weld"] = mat("epc_weld", (1.0, 0.85, 0.5), emit=(1.0, 0.8, 0.45), strength=5.0)


def slide(g, moves):
    """Key group `g` through [(frame, (dx, dy, dz)), ...] offsets."""
    for f, d in moves:
        key(g, f, "location", P(*d), linear=False)


def transformer(m, g, name, c, s=1.0):
    x, y, z = c
    bx(f"{name}_tank", (x - 10 * s, y, z - 8 * s), (x + 10 * s, y + 16 * s, z + 8 * s), m["xfmr"], g)
    for j in range(7):
        zz = z - 7 * s + j * 2.3 * s
        bx(f"{name}_fin{j}", (x + 10 * s, y + 1.5 * s, zz - 0.35 * s), (x + 15 * s, y + 13 * s, zz + 0.35 * s), m["xfmr"], g)
    for j in range(3):
        D.tube(f"{name}_bu{j}", (x - 6 * s + j * 6 * s, y + 16 * s, z), (x - 6 * s + j * 6 * s, y + 23 * s, z), 1.1 * s, m["white"], g, 10)


def switchgear(m, g, name, c):
    x, y, z = c
    for k in range(5):
        x0 = x - 15 + k * 6
        bx(f"{name}_c{k}", (x0, y, z - 5), (x0 + 5.6, y + 14, z + 5), m["dark"], g)
        bx(f"{name}_d{k}", (x0 + 0.6, y + 1, z + 5), (x0 + 5.0, y + 13, z + 5.3), m["steel"], g)
        bx(f"{name}_h{k}", (x0 + 3.8, y + 6, z + 5.3), (x0 + 4.4, y + 8, z + 5.7), m["dark"], g)


def chiller(m, g, name, c):
    x, y, z = c
    bx(f"{name}_b", (x - 16, y, z - 8), (x + 16, y + 10, z + 8), m["chiller"], g)
    for j in range(3):
        cx = x - 10 + j * 10
        D.tube(f"{name}_r{j}", (cx, y + 10, z), (cx, y + 11.5, z), 4.2, m["grid"], g, 18)


def truck(m, root, name, cargo, c):
    """A flatbed truck at c carrying `cargo(g, top)`. Returns the group (move it with slide)."""
    g = empty(name, root)
    x, y, z = c
    bx(f"{name}_cab", (x + 22, y + 2, z - 6), (x + 32, y + 14, z + 6), m["truck"], g)
    bx(f"{name}_win", (x + 31.9, y + 8, z - 5), (x + 32.3, y + 12.5, z + 5), m["glass"] if "glass" in m else m["steel"], g)
    bx(f"{name}_bed", (x - 22, y + 3, z - 6), (x + 22, y + 5, z + 6), m["steel"], g)
    for wx in (-16, -8, 14, 27):
        for side in (-1, 1):
            D.tube(f"{name}_w{wx}{side}", (x + wx, y + 2.6, z + side * 6.2), (x + wx, y + 2.6, z + side * 7.6), 2.6, m["rubber"], g, 12)
    cargo(g, (x, y + 5, z))
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    site = empty("site", root)
    # ground, road, gravel yard, slab
    gr = [bx("ground", (-230.0, -3.0, -220.0), (300.0, -1.5, 30.0), m["ground"], site),
          bx("road", (-230.0, -1.5, -14.0), (300.0, -1.0, 2.0), m["concrete"], site),
          bx("yard", (YARD[0], -1.5, -140.0), (YARD[1], -1.0, -30.0), m["gravel"], site),
          bx("slab", (HX0, -1.5, HZ0), (HX1, 0.0, HZ1), m["concrete"], site)]
    for k in range(14):
        x = -225.0 + k * 38.0
        gr.append(bx(f"fence{k}", (x, -1.0, -18.0), (x + 0.6, 8.0, -17.4), m["steel"], site))
    gr.append(bx("fence_w", (-225.0, 6.5, -18.0), (290.0, 7.0, -17.6), m["steel"], site))
    D.join(gr, "ground_m")

    # site office with the schedule board on its front
    of = [bx("office", (OFF[0], -1.0, -80.0), (OFF[1], 22.0, -40.0), m["office"], site),
          bx("office_roof", (OFF[0] - 2, 22.0, -82.0), (OFF[1] + 2, 23.5, -38.0), m["dark"], site),
          bx("board", (OFF[0] + 4, 4.0, -39.8), (OFF[1] - 4, 20.0, -39.4), m["board"], site)]
    D.join(of, "office_m")
    # Gantt: 4 rows (design, transformer, switchgear, chiller) + 1 build row
    bars = {}
    bx0, bx1 = OFF[0] + 7, OFF[1] - 7
    rows = [("eng", 0.0, 0.30), ("xfmr", 0.10, 0.80), ("swg", 0.12, 0.55), ("chl", 0.15, 0.60), ("bld", 0.45, 0.95)]
    for r, (nm, a, b) in enumerate(rows):
        y = 17.0 - r * 2.8
        g = empty(f"bar_{nm}", root)
        bx(f"barb_{nm}", (bx0 + (bx1 - bx0) * a, y, -39.3), (bx0 + (bx1 - bx0) * b, y + 1.6, -39.0), m["bar_ok"], g)
        bars[nm] = g
    late = empty("bar_late", root)
    bx("barl", (bx0 + (bx1 - bx0) * 0.80, 17.0 - 2.8, -39.3), (bx1 + 4.0, 17.0 - 2.8 + 1.6, -39.0), m["bar_late"], late)
    bx("barl2", (bx0 + (bx1 - bx0) * 0.95, 17.0 - 4 * 2.8, -39.3), (bx1 + 6.0, 17.0 - 4 * 2.8 + 1.6, -39.0), m["bar_late"], late)
    show(bars["eng"], [(F(1, 0.3), F(5, 0))])
    for nm in ("xfmr", "swg", "chl"):
        show(bars[nm], [(F(2, 0.25), F(5, 0))])
    show(bars["bld"], [(F(3, 0.2), F(5, 0))])
    show(late, [(F(4, 0.2), F(5, 0))])

    # engineering: glowing layout lines on the slab (rooms, pads, rack rows)
    plan = empty("plan", root)
    pl = []
    lines = [((HX0 + 4, HZ1 - 4), (HX1 - 4, HZ1 - 4)), ((HX0 + 4, HZ0 + 4), (HX1 - 4, HZ0 + 4)),
             ((HX0 + 4, HZ0 + 4), (HX0 + 4, HZ1 - 4)), ((HX1 - 4, HZ0 + 4), (HX1 - 4, HZ1 - 4)),
             ((60.0, HZ0 + 4), (60.0, HZ1 - 4))]
    for r in range(4):
        z = -50.0 - r * 22.0
        lines.append(((HX0 + 10, z), (50.0, z)))
        lines.append(((HX0 + 10, z - 8), (50.0, z - 8)))
    for k, ((xa, za), (xb, zb)) in enumerate(lines):
        pl.append(bx(f"pl{k}", (min(xa, xb) - 0.35, 0.05, min(za, zb) - 0.35), (max(xa, xb) + 0.35, 0.35, max(za, zb) + 0.35), m["plan"], plan))
    for k in range(3):
        x0 = 66.0 + k * 14.0
        for (a, b) in (((x0, -128.0), (x0 + 10, -128.0)), ((x0, -110.0), (x0 + 10, -110.0)),
                       ((x0, -128.0), (x0, -110.0)), ((x0 + 10, -128.0), (x0 + 10, -110.0))):
            pl.append(bx(f"pp{k}_{a}_{b}", (min(a[0], b[0]) - 0.3, 0.05, min(a[1], b[1]) - 0.3),
                         (max(a[0], b[0]) + 0.3, 0.35, max(a[1], b[1]) + 0.3), m["plan"], plan))
    D.join(pl, "plan_m")
    show(plan, [(F(1, 0.1), F(3, 0.35))])

    # the hall: walls rise in beat 3 (present = slide up from below the slab)
    walls = empty("walls", root)
    wl = [bx("wall_b", (HX0, 0.0, HZ0), (HX1, HY, HZ0 + 2.5), m["concrete"], walls),
          bx("wall_l", (HX0, 0.0, HZ0), (HX0 + 2.5, HY, HZ1), m["concrete"], walls),
          bx("wall_m", (58.0, 0.0, HZ0), (60.5, HY, HZ1), m["concrete"], walls)]
    for k in range(9):
        x = HX0 + 2 + k * (HX1 - HX0 - 4) / 8
        wl.append(bx(f"col{k}", (x - 1.0, 0.0, HZ1 - 2.0), (x + 1.0, HY, HZ1), m["steel"], walls))
        wl.append(bx(f"tru{k}", (x - 0.7, HY, HZ0), (x + 0.7, HY + 2.0, HZ1), m["steel"], walls))
    D.join(wl, "walls_m")
    slide(walls, [(0, (0, -HY - 3, 0)), (F(3, 0.05), (0, -HY - 3, 0)), (F(3, 0.45), (0, 0, 0))])

    # racks: 4 rows; first two light when power arrives, last two stay dark in beat 4
    racks = empty("racks", root)
    rk = []
    leds = [empty(f"led{k}", root) for k in range(4)]
    for r in range(4):
        z = -50.0 - r * 22.0
        for i in range(14):
            x = HX0 + 10 + i * 4.3
            rk.append(bx(f"rk{r}_{i}", (x, 0.0, z - 8), (x + 3.8, 20.0, z), m["rack"], racks))
            for j in range(3):
                bx(f"rl{r}_{i}_{j}", (x + 0.6, 4 + j * 5.5, z + 0.01), (x + 3.2, 4.8 + j * 5.5, z + 0.3), m["led_g"], leds[r])
    D.join(rk, "racks_m")
    slide(racks, [(0, (0, -25, 0)), (F(3, 0.4), (0, -25, 0)), (F(3, 0.7), (0, 0, 0))])
    for r, g in enumerate(leds):
        D.join(list(g.children), f"ledm{r}")
        iv = [(F(3, 0.8), F(4, 0))]
        if r < 2:
            iv.append((F(4, 0.0), F(5, 0)))
        show(g, iv)
    # dark racks warning in beat 4: red strip on the floor in front of rows 3-4
    dark = empty("dark", root)
    for r in (2, 3):
        z = -50.0 - r * 22.0
        bx(f"dk{r}", (HX0 + 10, 0.1, z + 0.5), (HX0 + 70, 0.5, z + 1.5), m["bar_late"], dark)
    show(dark, [(F(4, 0.3), F(5, 0))])

    # the gear: three groups that ride in on trucks to the yard (beat 2), then the crane sets them
    # onto pads inside the plant room (beat 3). The late transformer arrives only in beat 4's end.
    road_z = -6.0
    gear = {}
    specs = [("xfmr", lambda g, t: transformer(m, g, "tx", t, 0.9), 150.0),
             ("swg", lambda g, t: switchgear(m, g, "sg", t), 185.0),
             ("chl", lambda g, t: chiller(m, g, "ch", t), 220.0)]
    for k, (nm, cargo, yx) in enumerate(specs):
        tk = truck(m, root, f"trk_{nm}", cargo, (yx, 0.0, road_z))
        f_in = F(2, 0.15 + 0.15 * k)
        f_park = F(2, 0.45 + 0.12 * k)
        slide(tk, [(0, (-420, 0, 0)), (f_in, (-420, 0, 0)), (f_park, (0, 0, -60.0 - k * 6)),
                   (F(3, 0.0), (0, 0, -60.0 - k * 6)), (F(3, 0.01), (600, 0, 0))])
        gear[nm] = tk
    # pads in the plant room with the set gear (appear in beat 3 after the lift)
    set_g = empty("set_gear", root)
    transformer(m, set_g, "txs", (71.0, 0.0, -119.0), 0.45)
    switchgear(m, set_g, "sgs", (88.0, 0.0, -50.0))
    chiller(m, set_g, "chs", (95.0, 0.0, -119.0))
    show(set_g, [(F(3, 0.35), F(5, 0))])

    # tower crane: mast, jib that slews, hook with a load
    cr = empty("crane", root)
    cx, cz = 120.0, -85.0
    mast = []
    for k in range(12):
        y = k * 6.0
        mast.append(bx(f"cm{k}", (cx - 2.5, y, cz - 2.5), (cx + 2.5, y + 5.4, cz + 2.5), m["crane"], cr))
    D.join(mast, "crane_mast")
    jib = empty("jib", cr, P(cx, 74.0, cz))
    bx("jib_a", (-90.0, 0.0, -1.5), (30.0, 4.0, 1.5), m["crane"], jib)
    bx("jib_cw", (18.0, -3.0, -3.0), (30.0, 1.0, 3.0), m["concrete"], jib)
    bx("jib_cab", (-3.0, -6.0, -3.0), (3.0, 0.0, 3.0), m["truck"], jib)
    D.tube("hook_line", (-60.0, 0.0, 0.0), (-60.0, -45.0, 0.0), 0.25, m["dark"], jib, 6)
    bx("hook_load", (-66.0, -52.0, -5.0), (-54.0, -45.0, 5.0), m["crate"], jib)
    import math as _m
    from sand_overview import _interp
    for f, a in ((0, 0.0), (F(3, 0.0), 0.0), (F(3, 0.3), 0.9), (F(3, 0.6), -0.4), (F(3, 0.95), 0.6), (F(4, 0.4), 0.0)):
        _interp("BEZIER")
        jib.rotation_euler = (0.0, 0.0, a)
        jib.keyframe_insert("rotation_euler", frame=f)

    # welding sparks / activity in beat 3
    for k, x in enumerate((-20.0, 20.0, 50.0)):
        sp = empty(f"spark{k}", root)
        D.bead(f"spark{k}_b", (x, HY, HZ1 - 1.0), 1.4, m["weld"], sp)
        blink(sp, 3, [k, k + 3, k + 5], n=8, on=0.4, u0=0.3)

    # power and water flow into the hall in beat 3 (rows 1-2 only in beat 4)
    for r in range(4):
        z = -50.0 - r * 22.0 + 2.0
        bl = [3] if r >= 2 else [3, 4]
        run(root, f"pw{r}", [(71.0, 10.0, -110.0), (56.0, 24.0, -110.0), (56.0, 24.0, z), (HX0 + 10, 24.0, z)], 4, 1.2,
            m["hv"], bl, 0.55, 0.9, 40)
    run(root, "cw", [(95.0, 11.0, -110.0), (95.0, 27.0, -100.0), (HX0 + 6, 27.0, -100.0)], 5, 1.2, m["cold_b"], [3, 4], 0.6, 0.9, 40)
    rise(root, "dust", (20.0, 1.0, -85.0), 10, 1.0, m["dim_glow"], [3], 0.0, 0.5, 20.0, 40, (60.0, 30.0))
    # the late transformer: crate waiting at the far yard corner, flashing
    lt = empty("late_crate", root)
    bx("lt_b", (215.0, 0.0, -130.0), (235.0, 18.0, -112.0), m["crate"], lt)
    bx("lt_x", (214.5, 8.0, -131.0), (235.5, 10.0, -111.0), m["bar_late"], lt)
    show(lt, [(F(4, 0.1), F(5, 0))])

    tags = {
        0: [("site office: design + schedule", (OFF[0] + 30, 24.0, -60.0)), ("laydown yard", (185.0, 2.0, -110.0)),
            ("tower crane", (cx, 78.0, cz)), ("hall slab", (20.0, 1.0, -85.0))],
        1: [("layout drawn on the slab", (0.0, 1.0, -70.0)), ("gear pads sized in MW", (80.0, 1.0, -119.0)),
            ("rack rows set by density", (0.0, 1.0, -110.0))],
        2: [("transformer: 2-4 yr lead", (150.0, 20.0, -66.0)), ("switchgear: 1+ yr", (185.0, 16.0, -72.0)),
            ("chillers", (220.0, 14.0, -78.0)), ("lead-time bars", (OFF[0] + 30, 18.0, -39.0))],
        3: [("crane sets the gear", (cx - 40, 40.0, cz)), ("walls and racks go up", (0.0, HY, -60.0)),
            ("power + chilled water tie-in", (56.0, 25.0, -90.0))],
        4: [("transformer late", (225.0, 20.0, -121.0)), ("schedule slips", (OFF[0] + 30, 12.0, -39.0)),
            ("racks wait dark", (0.0, 21.0, -100.0)), ("PWR EME FIX STRL", (20.0, HY + 4, -60.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((40.0, 10.0, -80.0), 380.0, 0.30, 0.55, pad=1.0),
        frame((25.0, 0.0, -85.0), 190.0, 0.15, 0.95),
        [(0.0, frame((170.0, 10.0, -60.0), 200.0, 0.45, 0.60)), (0.6, frame((60.0, 15.0, -60.0), 300.0, 0.0, 0.40))],
        frame((40.0, 20.0, -85.0), 260.0, 0.35, 0.50),
        [(0.0, frame((-60.0, 12.0, -60.0), 160.0, -0.15, 0.25)), (0.5, frame((60.0, 10.0, -85.0), 360.0, 0.20, 0.50, pad=1.0))],
    ], root)


if __name__ == "__main__":
    build()
