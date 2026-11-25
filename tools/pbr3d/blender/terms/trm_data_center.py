"""TRM_DATA_CENTER: a cut-away AI data hall with its power, cooling and fiber.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_data_center.py

A data hall with its front wall and roof cut away: six rows of racks in hot/cold aisle pairs,
overhead fiber trays and coolant headers, an electrical room (UPS + batteries) at the right end,
a substation fed by a high-voltage line, a chiller yard and generator yard behind, and a fiber
meet-me room on the left. `hall()` is reused by trm_hyperscaler.py.

Beats:
  0 hall      the whole campus, cut open
  1 power     grid -> substation -> transformers -> UPS -> busways -> racks (MW)
  2 compute   racks blink, heat rises out of the hot aisles
  3 cooling   chilled water out to the CDUs and racks, warm water back, chiller fans spin
  4 fiber     fiber enters the meet-me room and fans out to every row; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from sand_overview import P  # noqa: E402
from power_vrm_detail import frame, run, rise  # noqa: E402

SLUG = "TRM_DATA_CENTER"
BEATS = [
    ("A data center is a building of servers plus power, cooling and fiber",
     "Inside the hall, servers sit in rows of racks. Around it sits the plant that keeps them alive: a substation and "
     "backup generators for power, chillers for cooling, and fiber links to the outside world. The building is "
     "mostly that plant; the racks take up a surprisingly small share of the site."),
    ("Capacity is counted in megawatts, and the grid sets the limit",
     "Power arrives at high voltage, is stepped down by transformers, passes through UPS batteries that bridge the "
     "seconds before diesel generators start, and runs along busways to every rack. Sites are sized by IT load: a "
     "classic hall is 5-30 MW, while new AI campuses plan for hundreds of MW to over a gigawatt. Getting a grid "
     "connection now takes years, so power is the main bottleneck."),
    ("AI racks pack far more power into the same floor",
     "A traditional cloud rack draws 5-15 kW. A rack of current Nvidia GPUs draws 100-150 kW, and designs for 2027 "
     "aim at several hundred. Nearly every watt in becomes heat out, which is pushed out of the back of each rack "
     "into a closed hot aisle."),
    ("Cooling carries that heat out: air for old halls, liquid for AI",
     "Chillers outside make cold water. Coolant distribution units (CDUs) at the rows pass it to cold plates on the "
     "chips, and the warm water returns to be cooled again. Air alone cannot remove 100+ kW from one rack, so AI "
     "halls are being built or refitted for direct liquid cooling."),
    ("Fiber ties the hall to the internet and the racks to each other",
     "Carrier fiber enters a meet-me room, where networks cross-connect, then runs in overhead trays to every row. "
     "Inside an AI cluster far more fiber links GPU to GPU than goes to the outside. Related: Equinix (EQIX) and "
     "Digital Realty (DLR) rent space, Vertiv (VRT) sells power and cooling gear, Nvidia (NVDA) the GPUs, and "
     "Microsoft (MSFT) is among the largest builders."),
]

# layout (units ~ 0.5 m): hall x HX0..HX1, z HZ0..0 (front cut), walls up to HY
HX0, HX1, HZ0, HY = -155.0, 115.0, -155.0, 34.0
ROWS = [(-20.0, -40.0), (-65.0, -85.0), (-110.0, -130.0)]  # rack row pairs (z centres)
RX0, RX1, RW, RD, RH = -140.0, 66.0, 6.0, 10.0, 22.0
ELEC = (80.0, 110.0)  # electrical room x span


def mats(m):
    m["concrete"] = mat("dc_concrete", (0.55, 0.55, 0.53), rough=0.9)
    m["ground"] = mat("dc_ground", (0.24, 0.28, 0.22), rough=0.95)
    m["gravel"] = mat("dc_gravel", (0.40, 0.39, 0.36), rough=0.95)
    m["rack"] = mat("dc_rack", (0.08, 0.08, 0.10), metal=0.5, rough=0.45)
    m["rack_door"] = mat("dc_rack_door", (0.16, 0.17, 0.20), metal=0.6, rough=0.4)
    m["tray"] = mat("dc_tray", (0.95, 0.78, 0.15), rough=0.5)
    m["pipe_c"] = mat("dc_pipe_c", (0.25, 0.45, 0.80), metal=0.6, rough=0.35)
    m["pipe_h"] = mat("dc_pipe_h", (0.80, 0.35, 0.20), metal=0.6, rough=0.35)
    m["xfmr"] = mat("dc_xfmr", (0.42, 0.50, 0.40), metal=0.4, rough=0.5)
    m["gen"] = mat("dc_gen", (0.85, 0.75, 0.30), metal=0.3, rough=0.5)
    m["chiller"] = mat("dc_chiller", (0.78, 0.80, 0.82), metal=0.5, rough=0.4)
    m["batt"] = mat("dc_batt", (0.18, 0.22, 0.30), metal=0.3, rough=0.5)
    m["led_g"] = mat("dc_led_g", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.5)
    m["led_b"] = mat("dc_led_b", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=3.5)
    m["hv"] = mat("dc_hv", (1.0, 0.85, 0.40), emit=(1.0, 0.80, 0.30), strength=5.0)
    m["cold_b"] = mat("dc_cold_b", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0)
    m["warm_b"] = mat("dc_warm_b", (1.0, 0.50, 0.20), emit=(1.0, 0.45, 0.15), strength=4.0)
    m["heat_b"] = mat("dc_heat_b", (1.0, 0.40, 0.15), emit=(1.0, 0.35, 0.10), strength=3.0)
    m["fib_b"] = mat("dc_fib_b", (0.40, 1.0, 0.60), emit=(0.35, 1.0, 0.55), strength=4.5)


def rack_xs():
    xs, x = [], RX0
    while x + RW <= RX1:
        xs.append(x)
        x += RW + 0.6
    return xs


def hall(m, root, ox=0.0, oz=0.0, name="h", leds=True):
    """The cut-open hall at offset (ox, oz). Returns points and the LED blink groups."""
    g = empty(name, root)
    o = lambda x, y, z: (x + ox, y, z + oz)  # noqa: E731
    B = lambda n, a, b, mt, par=g: bx(f"{name}_{n}", o(*a), o(*b), m[mt], par)  # noqa: E731
    parts = []
    parts.append(B("slab", (HX0, -1.5, HZ0), (HX1, 0.0, 0.0), "concrete"))
    parts.append(B("wall_b", (HX0, 0.0, HZ0), (HX1, HY, HZ0 + 3.0), "concrete"))
    parts.append(B("wall_l", (HX0, 0.0, HZ0), (HX0 + 3.0, HY, 0.0), "concrete"))
    parts.append(B("wall_r", (HX1 - 3.0, 0.0, HZ0), (HX1, HY, 0.0), "concrete"))
    parts.append(B("curb", (HX0, 0.0, -3.0), (HX1, 3.0, 0.0), "concrete"))
    parts.append(B("wall_e", (ELEC[0] - 2.0, 0.0, HZ0), (ELEC[0], HY, -6.0), "concrete"))
    D.join(parts, f"{name}_shell")
    # roof trusses (the roof itself is cut away)
    tr = []
    for k in range(10):
        x = HX0 + 3.0 + (HX1 - HX0 - 6.0) * k / 9
        tr.append(B(f"tr{k}", (x - 0.8, HY, HZ0), (x + 0.8, HY + 2.0, 0.0), "steel"))
    tr.append(B("tr_b", (HX0, HY, HZ0), (HX1, HY + 2.0, HZ0 + 3.0), "steel"))
    D.join(tr, f"{name}_truss")
    # racks
    xs = rack_xs()
    racks, doors = [], []
    led_groups = [empty(f"{name}_led{k}", g) for k in range(4)]
    led_parts = [[] for _ in range(4)]
    for r, (za, zb) in enumerate(ROWS):
        for zc, face in ((za, 1.0), (zb, -1.0)):
            for i, x in enumerate(xs):
                racks.append(B(f"r{r}_{zc:.0f}_{i}", (x, 0.0, zc - RD / 2), (x + RW, RH, zc + RD / 2), "rack"))
                zf = zc + face * RD / 2
                doors.append(B(f"d{r}_{zc:.0f}_{i}", (x + 0.4, 1.0, zf), (x + RW - 0.4, RH - 1.0, zf + face * 0.3), "rack_door"))
                if leds:
                    k = (i * 3 + r + (1 if face > 0 else 2)) % 4
                    for j in range(3):
                        y = 5.0 + j * 6.0
                        led_parts[k].append(bx(f"{name}_l{r}_{zc:.0f}_{i}_{j}", o(x + 1.0, y, zf + face * 0.3),
                                               o(x + RW - 1.0, y + 0.8, zf + face * 0.6), m["led_g" if j else "led_b"], led_groups[k]))
            # hot-aisle containment roof between the pair
        hz = (za + zb) / 2
        racks.append(B(f"cont{r}", (RX0, RH, hz - 5.0), (xs[-1] + RW, RH + 0.6, hz + 5.0), "steel"))
        for x in (RX0 - 0.6, xs[-1] + RW):
            racks.append(B(f"door{r}_{x:.0f}", (x, 0.0, hz - 5.0), (x + 0.6, RH, hz + 5.0), "rack_door"))
    D.join(racks, f"{name}_racks")
    D.join(doors, f"{name}_doors")
    for k in range(4):
        if led_parts[k]:
            D.join(led_parts[k], f"{name}_ledm{k}")
        show(led_groups[k], [])
    # CDUs at the left end of each pair, overhead coolant headers above each hot aisle
    cool = []
    for r, (za, zb) in enumerate(ROWS):
        hz = (za + zb) / 2
        cool.append(B(f"cdu{r}", (RX0 - 12.0, 0.0, hz - 7.0), (RX0 - 3.0, 20.0, hz + 7.0), "chiller"))
        cool.append(bx(f"{name}_ps{r}", o(RX0 - 8.0, 28.0, hz - 2.0), o(RX1, 29.6, hz - 0.4), m["pipe_c"], g))
        cool.append(bx(f"{name}_pr{r}", o(RX0 - 8.0, 28.0, hz + 0.4), o(RX1, 29.6, hz + 2.0), m["pipe_h"], g))
        cool.append(bx(f"{name}_pd{r}", o(RX0 - 8.0, 20.0, hz - 2.0), o(RX0 - 6.4, 28.0, hz + 2.0), m["pipe_c"], g))
        # fiber trays above the cold aisles (in front of each pair)
        cool.append(bx(f"{name}_ft{r}", o(RX0, 26.0, za + 7.0), o(RX1, 27.0, za + 11.0), m["tray"], g))
    # main headers along the back wall to the chiller yard
    cool.append(bx(f"{name}_hc", o(RX0 - 10.0, 30.0, HZ0 + 4.0), o(RX0 - 7.0, 31.6, -5.0), m["pipe_c"], g))
    cool.append(bx(f"{name}_hh", o(RX0 - 6.0, 32.0, HZ0 + 4.0), o(RX0 - 3.0, 33.6, -5.0), m["pipe_h"], g))
    cool.append(bx(f"{name}_fb", o(HX0 + 3.0, 26.0, -14.0), o(RX0, 27.0, -10.0), m["tray"], g))
    cool.append(bx(f"{name}_fs", o(RX0 - 1.0, 26.0, -130.0), o(RX0 + 2.0, 27.0, -10.0), m["tray"], g))
    D.join(cool, f"{name}_mep")
    # electrical room: UPS cabinets and battery strings, busways out over the rows
    el = []
    for k in range(4):
        z0 = -20.0 - 30.0 * k
        el.append(B(f"ups{k}", (ELEC[0] + 4.0, 0.0, z0 - 10.0), (ELEC[0] + 14.0, 20.0, z0), "dark"))
        for j in range(5):
            el.append(B(f"bt{k}_{j}", (ELEC[0] + 17.0, 0.0, z0 - 10.0 + j * 2.0), (ELEC[0] + 26.0, 16.0, z0 - 8.6 + j * 2.0), "batt"))
    for r, (za, zb) in enumerate(ROWS):
        for zc in (za, zb):
            el.append(B(f"bw{r}_{zc:.0f}", (RX0, 24.0, zc - 1.0), (ELEC[0], 25.4, zc + 1.0), "copper"))
    D.join(el, f"{name}_elec")
    pts = {
        "racks": o(-40.0, RH + 1.0, ROWS[0][0]),
        "row": o(-80.0, RH, ROWS[1][0]),
        "aisle": [o(-40.0, RH, (za + zb) / 2) for za, zb in ROWS],
        "ups": o(ELEC[0] + 10.0, 20.0, -20.0),
        "batt": o(ELEC[0] + 22.0, 16.0, -50.0),
        "cdu": o(RX0 - 7.0, 20.0, -30.0),
        "trays": o(-60.0, 27.0, ROWS[0][0] + 9.0),
        "hc": o(RX0 - 8.5, 31.0, HZ0 + 5.0),
        "hh": o(RX0 - 4.5, 33.0, HZ0 + 5.0),
        "o": o,
    }
    return pts, led_groups


def fan(m, root, name, c, r):
    g = empty(name, root, P(*c))
    bl = []
    for k in range(3):
        import math
        a = k * 2.0944
        ca, sa = math.cos(a), math.sin(a)
        bl.append(D.tube(f"{name}_b{k}", (0.0, 0.5, 0.0), (ca * r, 0.5, sa * r), r * 0.18, m["dark"], g, 6))
    D.join(bl, f"{name}_m")
    return g


def site(m, root):
    """Everything outside the hall. Returns points and moving parts."""
    g = empty("site", root)
    gr = [bx("ground", (-300.0, -3.0, -260.0), (330.0, -1.5, 40.0), m["ground"], g),
          bx("yard_s", (125.0, -1.5, -150.0), (250.0, -1.0, -20.0), m["gravel"], g),
          bx("yard_c", (-150.0, -1.5, -235.0), (115.0, -1.0, -165.0), m["gravel"], g)]
    D.join(gr, "ground_m")
    # substation: incoming HV line on pylons, transformers with fins and bushings, switchgear
    s = []
    for k, x in enumerate((320.0, 280.0)):
        s.append(bx(f"py{k}", (x - 1.5, 0.0, -90.0), (x + 1.5, 70.0, -87.0), m["steel"], g))
        s.append(bx(f"pyx{k}", (x - 10.0, 64.0, -90.0), (x + 10.0, 66.0, -87.0), m["steel"], g))
    for k in range(3):
        z = -84.0 + k * 0.0
        x0 = 230.0
        s.append(D.tube(f"hvl{k}", (322.0, 64.0, -88.5 + (k - 1) * 0.0), (x0, 40.0, -70.0 - k * 18.0), 0.4, m["alu"], g, 6))
    for k in range(3):
        zc = -70.0 - k * 18.0
        s.append(bx(f"gan{k}", (226.0, 0.0, zc - 1.0), (230.0, 40.0, zc + 1.0), m["steel"], g))
    for k in range(2):
        zc = -60.0 - k * 50.0
        s.append(bx(f"xf{k}", (165.0, 0.0, zc - 12.0), (195.0, 22.0, zc + 12.0), m["xfmr"], g))
        for j in range(8):
            z = zc - 10.0 + j * 2.8
            s.append(bx(f"xff{k}_{j}", (195.0, 2.0, z - 0.4), (201.0, 18.0, z + 0.4), m["xfmr"], g))
        for j in range(3):
            s.append(D.tube(f"xfb{k}_{j}", (172.0 + j * 8.0, 22.0, zc), (172.0 + j * 8.0, 30.0, zc), 1.2, m["white"], g, 10))
    s.append(bx("swg", (130.0, 0.0, -140.0), (148.0, 20.0, -30.0), m["dark"], g))
    D.join(s, "substation")
    # chiller yard behind the hall
    ch, fans = [], []
    for k in range(5):
        x0 = -140.0 + k * 40.0
        ch.append(bx(f"ch{k}", (x0, 0.0, -230.0), (x0 + 32.0, 14.0, -175.0), m["chiller"], g))
        for j in range(2):
            c = (x0 + 16.0, 14.2, -216.0 + j * 27.0)
            ch.append(D.tube(f"chr{k}_{j}", (c[0], 14.0, c[2]), (c[0], 16.0, c[2]), 10.0, m["grid"], g, 20))
            fans.append(fan(m, g, f"chf{k}_{j}", (c[0], 16.2, c[2]), 9.0))
    ch.append(bx("chp_c", (-150.0, 30.0, -200.0), (60.0, 31.6, -198.0), m["pipe_c"], g))
    ch.append(bx("chp_h", (-150.0, 32.0, -196.0), (60.0, 33.6, -194.0), m["pipe_h"], g))
    ch.append(bx("chp_cz", (-147.0, 30.0, -200.0), (-144.0, 31.6, -150.0), m["pipe_c"], g))
    ch.append(bx("chp_hz", (-143.0, 32.0, -200.0), (-140.0, 33.6, -150.0), m["pipe_h"], g))
    for k in range(5):
        x = -124.0 + k * 40.0
        ch.append(bx(f"chv{k}", (x - 0.8, 14.0, -199.0), (x + 0.8, 32.0, -197.0), m["pipe_c"], g))
    D.join(ch, "chillers")
    # generator yard
    gn = []
    for k in range(5):
        x0 = 120.0 + k * 26.0
        gn.append(bx(f"gn{k}", (x0, 0.0, -230.0), (x0 + 20.0, 16.0, -180.0), m["gen"], g))
        gn.append(D.tube(f"gns{k}", (x0 + 10.0, 16.0, -220.0), (x0 + 10.0, 30.0, -220.0), 1.6, m["dark"], g, 10))
    D.join(gn, "generators")
    # meet-me room annex on the left with fiber conduit from the street
    mm = [bx("mmr", (-200.0, -1.5, -60.0), (-158.0, 0.0, -6.0), m["concrete"], g),
          bx("mmr_w", (-200.0, 0.0, -60.0), (-158.0, 22.0, -57.0), m["concrete"], g),
          bx("mmr_wl", (-200.0, 0.0, -60.0), (-197.0, 22.0, -6.0), m["concrete"], g)]
    for k in range(4):
        x = -192.0 + k * 9.0
        mm.append(bx(f"mmr_r{k}", (x, 0.0, -50.0), (x + 6.0, 18.0, -40.0), m["rack"], g))
        mm.append(bx(f"mmr_p{k}", (x + 0.5, 4.0, -40.0), (x + 5.5, 16.0, -39.6), m["tray"], g))
    mm.append(bx("conduit", (-300.0, -1.2, -32.0), (-200.0, -0.4, -28.0), m["tray"], g))
    mm.append(bx("mmr_t", (-190.0, 20.0, -14.0), (-155.0, 21.0, -10.0), m["tray"], g))
    D.join(mm, "mmr_m")
    return {"sub": (180.0, 30.0, -60.0), "pylon": (280.0, 66.0, -88.0), "swg": (139.0, 20.0, -85.0),
            "chill": (-60.0, 16.0, -200.0), "gen": (170.0, 30.0, -220.0), "mmr": (-180.0, 18.0, -45.0),
            "street": (-290.0, 0.0, -30.0), "fans": fans}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    h, leds = hall(m, root)
    s = site(m, root)

    # beat 1: power path, grid to racks
    hvp = [(322.0, 64.0, -88.0), (230.0, 40.0, -70.0), (195.0, 24.0, -60.0), (148.0, 18.0, -60.0),
           (ELEC[0] + 9.0, 20.0, -50.0), (ELEC[0] + 2.0, 24.5, -40.0)]
    run(root, "pw_hv", hvp, 9, 2.2, m["hv"], [1], 0.0, 0.5, 60)
    for r, (za, zb) in enumerate(ROWS):
        for zc in (za, zb):
            run(root, f"pw_bw{r}_{zc:.0f}", [(ELEC[0], 25.8, zc), (RX0, 25.8, zc)], 4, 1.3, m["hv"], [1], 0.35, 0.85, 50)
    run(root, "pw_gen", [(170.0, 16.0, -180.0), (148.0, 18.0, -140.0), (148.0, 18.0, -90.0)], 4, 1.6, m["warn"], [1], 0.55, 0.9, 30)

    # beat 2: racks busy, heat up out of the hot aisles
    for r, a in enumerate(h["aisle"]):
        rise(root, f"heat{r}", a, 10, 1.4, m["heat_b"], [2], 0.0, 0.8, 18.0, 50, (90.0, 3.0))

    # beat 3: cooling loop
    for r, (za, zb) in enumerate(ROWS):
        hz = (za + zb) / 2
        sup = [(-145.5, 31.0, -196.0), (-145.5, 31.0, hz - 1.2), (RX0 - 7.2, 29.0, hz - 1.2), (RX1 - 4.0, 29.0, hz - 1.2)]
        ret = [(RX1 - 4.0, 29.0, hz + 1.2), (RX0 - 7.0, 29.0, hz + 1.2), (-141.5, 33.0, hz + 1.2), (-141.5, 33.0, -196.0)]
        run(root, f"cs{r}", sup, 6, 1.4, m["cold_b"], [3], 0.0, 0.6, 70)
        run(root, f"cr{r}", ret, 6, 1.4, m["warm_b"], [3], 0.25, 0.85, 70)
    run(root, "cy_c", [(60.0, 31.0, -199.0), (-145.5, 31.0, -199.0)], 6, 1.4, m["cold_b"], [3], 0.0, 0.5, 60)
    run(root, "cy_h", [(-141.5, 33.0, -195.0), (60.0, 33.0, -195.0)], 6, 1.4, m["warm_b"], [3], 0.3, 0.8, 60)
    for f in s["fans"]:
        C.spin(f, [3], turns=4.0)

    # beat 4: fiber in from the street, through the meet-me room, out along the trays
    run(root, "fb_in", [s["street"], (-200.0, -0.5, -30.0), (-185.0, 18.0, -40.0), (-185.0, 21.5, -12.0),
                        (HX0 + 3.0, 27.5, -12.0), (RX0 + 0.5, 27.5, -12.0)], 8, 1.3, m["fib_b"], [4], 0.0, 0.45, 50)
    for r, (za, zb) in enumerate(ROWS):
        run(root, f"fb{r}", [(RX0 + 0.5, 27.5, -12.0), (RX0 + 0.5, 27.5, za + 9.0), (RX1, 27.5, za + 9.0)], 5, 1.2,
            m["fib_b"], [4], 0.3 + 0.08 * r, 0.9, 50)
    # LED groups: blink in beat 2, steady glow in 3-4
    for k, gl in enumerate(leds):
        iv = []
        w = 1.0 / 8
        for sl in (k, k + 4):
            iv.append((F(2, w * sl), F(2, w * sl + w * 0.7)))
        iv.append((F(3, 0.0), F(5, 0.0)) if k < 2 else (F(4, 0.0), F(5, 0.0)))
        show(gl, iv)

    tags = {
        0: [("data hall: rows of racks", h["racks"]), ("substation", s["sub"]), ("chiller yard", s["chill"]),
            ("backup generators", s["gen"]), ("fiber meet-me room", s["mmr"])],
        1: [("high-voltage grid feed", s["pylon"]), ("transformers step down", s["sub"]),
            ("UPS + batteries", h["ups"]), ("busways to every rack", (0.0, 26.0, ROWS[0][0])),
            ("diesel backup", s["gen"])],
        2: [("AI rack: 100-150 kW", h["racks"]), ("cloud rack: 5-15 kW", h["row"]),
            ("hot aisle: heat out", h["aisle"][1])],
        3: [("chillers make cold water", s["chill"]), ("CDU per row", h["cdu"]),
            ("cold supply", h["hc"]), ("warm return", (RX1 - 4.0, 30.0, -97.0))],
        4: [("carrier fiber in", s["street"]), ("cross-connects", s["mmr"]), ("overhead fiber trays", h["trays"]),
            ("EQIX, DLR rent the space", (-40.0, 34.0, -60.0)), ("VRT power + cooling", s["chill"])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((20.0, 10.0, -110.0), 430.0, 0.35, 0.50, pad=1.0),
        [(0.0, frame((200.0, 20.0, -80.0), 220.0, 0.55, 0.35)), (0.5, frame((40.0, 15.0, -70.0), 260.0, 0.25, 0.55))],
        frame((-30.0, 12.0, -50.0), 150.0, 0.30, 0.30),
        [(0.0, frame((-90.0, 15.0, -150.0), 260.0, -0.35, 0.50)), (0.55, frame((-100.0, 20.0, -70.0), 180.0, -0.15, 0.45))],
        frame((-120.0, 15.0, -60.0), 340.0, -0.30, 0.50),
    ], root)


if __name__ == "__main__":
    build()
