"""TRM_HYPERSCALER: a fleet of owned campuses linked by private fiber, and the capex that flows
out of them to the AI supply chain.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hyperscaler.py

One campus is the cut-open hall from trm_data_center.py; eleven more campuses sit round it in
four colour-coded fleets (AWS, Azure, GCP, Meta) joined by a backbone ring. In front stand three
supplier plinths (GPUs, network, power + cooling) that capex beads flow to.

Beats:
  0 fleet     many campuses, four owners
  1 backbone  private fiber between regions, traffic beads
  2 inside    zoom into one campus: rows of AI racks busy
  3 capex     money flows from every campus to the suppliers
  4 demand    supplier plinths glow; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, rise  # noqa: E402
import trm_data_center as DC  # noqa: E402

SLUG = "TRM_HYPERSCALER"
BEATS = [
    ("A hyperscaler runs computing across dozens of its own giant campuses",
     "Amazon (AWS), Microsoft (Azure), Google (GCP) and Meta each own and operate fleets of data centers around the "
     "world, grouped into regions. They design their own servers, racks and often chips, and buy at a scale no one "
     "else does. Oracle and a few newer GPU clouds are trying to join that tier."),
    ("Regions are tied together by private fiber backbones",
     "Each hyperscaler lays or leases its own long-haul and subsea fiber, so traffic between its regions never touches "
     "the public internet. That backbone lets them spread a service, or a training job's data, across many sites "
     "and fail over when one goes down."),
    ("Each campus is a cluster of halls full of AI racks",
     "Zoom into one site and it is a data center like any other, only larger and more uniform: hundreds of MW, "
     "identical rows of racks, and increasingly liquid-cooled GPU or custom-chip (TPU, Trainium, Maia, MTIA) "
     "systems. They buy for themselves and rent the capacity to cloud customers."),
    ("Their capex, hundreds of billions a year, is the AI build-out",
     "Combined capital spending by the big four runs at several hundred billion dollars a year and is still rising. "
     "Roughly half goes to servers and chips, the rest to buildings, power, cooling and network. That spending is "
     "the main source of demand for nearly every AI hardware supplier."),
    ("Suppliers name them as top customers, so their guidance moves the chain",
     "Nvidia, Broadcom, Arista, Vertiv and others list hyperscalers among their largest customers. When one raises "
     "or trims its capex guidance on an earnings call, the whole AI supply chain reprices. Related: Amazon (AMZN), "
     "Microsoft (MSFT), Alphabet (GOOGL), Meta (META), Oracle (ORCL)."),
]

FLEETS = [  # owner, colour, campus positions (x, z)
    ("AWS", (1.0, 0.62, 0.18), [(-700.0, -250.0), (-620.0, 150.0), (-430.0, -520.0)]),
    ("Azure", (0.30, 0.65, 1.0), [(560.0, -300.0), (700.0, 100.0), (420.0, -600.0)]),
    ("GCP", (0.35, 1.0, 0.55), [(-150.0, -720.0), (150.0, -760.0)]),
    ("Meta", (0.85, 0.45, 1.0), [(-380.0, 330.0), (380.0, 330.0), (0.0, -500.0)]),
]
SUP = [("GPUs + accelerators", -260.0), ("network + optics", 0.0), ("power + cooling", 260.0)]
SZ = 560.0  # supplier plinths z


def campus(m, root, name, x, z, own):
    g = empty(name, root)
    parts = [bx(f"{name}_pad", (x - 110.0, -1.5, z - 90.0), (x + 110.0, -0.5, z + 90.0), m["gravel"], g)]
    for k in range(3):
        x0 = x - 100.0 + k * 70.0
        parts.append(bx(f"{name}_h{k}", (x0, 0.0, z - 70.0), (x0 + 60.0, 22.0, z + 30.0), m["concrete"], g))
        for j in range(4):
            parts.append(bx(f"{name}_c{k}_{j}", (x0 + 4.0 + j * 14.0, 22.0, z - 60.0), (x0 + 14.0 + j * 14.0, 27.0, z - 40.0), m["chiller"], g))
    parts.append(bx(f"{name}_sub", (x - 100.0, 0.0, z + 45.0), (x - 50.0, 14.0, z + 80.0), m["xfmr"], g))
    D.join(parts, f"{name}_m")
    roof = empty(f"{name}_roof", root)
    rp = [bx(f"{name}_r{k}", (x - 98.0 + k * 70.0, 22.1, z - 30.0), (x - 42.0 + k * 70.0, 22.6, z + 26.0), m[own], roof)
          for k in range(3)]
    D.join(rp, f"{name}_rm")
    return g, roof


def build():
    m, root = C.setup(SLUG, len(BEATS))
    DC.mats(m)
    for own, c, _ in FLEETS:
        m[own] = mat(f"hs_{own}", c, emit=c, strength=2.5)
    m["usd"] = mat("hs_usd", (0.55, 1.0, 0.45), emit=(0.5, 1.0, 0.4), strength=4.0)
    bx("ground", (-900.0, -3.0, -900.0), (900.0, -1.5, 700.0), m["ground"], root)
    h, leds = DC.hall(m, root)  # the zoom-in campus at the centre (AWS-coloured roofs off: open)
    sites = []
    roofs = []
    for own, _, pos in FLEETS:
        for k, (x, z) in enumerate(pos):
            _, rf = campus(m, root, f"cp_{own}{k}", x, z, own)
            roofs.append(rf)
            sites.append((own, (x, 30.0, z)))
    for rf in roofs:
        show(rf, [(F(0, 0.15), F(5, 0))])
    # backbone ring through every campus (sorted by angle about the centre)
    ring = sorted([p for _, p in sites] + [(-10.0, 30.0, -70.0)], key=lambda p: math.atan2(p[2] + 200.0, p[0]))
    loop = ring + [ring[0]]
    seg = []
    for k in range(len(loop) - 1):
        a, b = loop[k], loop[k + 1]
        seg.append(D.tube(f"bb{k}", (a[0], 2.0, a[2]), (b[0], 2.0, b[2]), 2.2, m["tray"], root, 8))
    D.join(seg, "backbone")
    pth = [(p[0], 5.0, p[2]) for p in loop]
    run(root, "bb_a", pth, 14, 6.0, m["fib_b"], [1], 0.0, 0.5, 160)
    run(root, "bb_b", list(reversed(pth)), 14, 6.0, m["e_blue"], [1], 0.1, 0.6, 160)

    # beat 2: inside the hall
    show(leds[0], [(F(2, 0.1), F(2, 0.5)), (F(3, 0), F(5, 0))])
    show(leds[1], [(F(2, 0.3), F(2, 0.8)), (F(3, 0), F(5, 0))])
    show(leds[2], [(F(2, 0.0), F(2, 0.35)), (F(2, 0.6), F(5, 0))])
    show(leds[3], [(F(2, 0.45), F(2, 1.0))])
    for r, a in enumerate(h["aisle"]):
        rise(root, f"heat{r}", a, 8, 1.4, m["heat_b"], [2], 0.0, 0.8, 18.0, 50, (90.0, 3.0))

    # suppliers: plinths with a GPU board, a switch with optics, a transformer + CDU
    sp = []
    for name, x in SUP:
        sp.append(bx(f"pl_{x:.0f}", (x - 90.0, 0.0, SZ - 60.0), (x + 90.0, 12.0, SZ + 60.0), m["dark"], root))
    gx = SUP[0][1]
    sp.append(bx("gpu_b", (gx - 70.0, 12.0, SZ - 40.0), (gx + 70.0, 15.0, SZ + 40.0), m["mask"], root))
    for k in range(4):
        cx = gx - 48.0 + k * 32.0
        sp.append(bx(f"gpu_p{k}", (cx - 12.0, 15.0, SZ - 14.0), (cx + 12.0, 18.0, SZ + 14.0), m["substrate"], root))
        sp.append(bx(f"gpu_d{k}", (cx - 7.0, 18.0, SZ - 8.0), (cx + 7.0, 20.0, SZ + 8.0), m["die"], root))
        for j in (-1, 1):
            sp.append(bx(f"gpu_h{k}{j}", (cx - 7.0, 18.0, SZ + j * 9.0 - 1.5 * (1 - j)), (cx + 7.0, 21.0, SZ + j * 12.0), m["hbm"], root))
    nx = SUP[1][1]
    sp.append(bx("sw", (nx - 70.0, 12.0, SZ - 40.0), (nx + 70.0, 34.0, SZ + 40.0), m["rack"], root))
    for k in range(16):
        x = nx - 64.0 + k * 8.2
        sp.append(bx(f"opt{k}", (x, 16.0, SZ + 40.0), (x + 6.0, 22.0, SZ + 52.0), m["alu"], root))
        sp.append(bx(f"opt2{k}", (x, 24.0, SZ + 40.0), (x + 6.0, 30.0, SZ + 52.0), m["alu"], root))
    px = SUP[2][1]
    sp.append(bx("tx", (px - 70.0, 12.0, SZ - 30.0), (px - 10.0, 52.0, SZ + 30.0), m["xfmr"], root))
    for j in range(8):
        z = SZ - 26.0 + j * 7.4
        sp.append(bx(f"txf{j}", (px - 10.0, 16.0, z - 1.0), (px - 2.0, 48.0, z + 1.0), m["xfmr"], root))
    sp.append(bx("cdu", (px + 10.0, 12.0, SZ - 30.0), (px + 70.0, 62.0, SZ + 30.0), m["chiller"], root))
    for k in range(3):
        sp.append(D.tube(f"tb{k}", (px - 55.0 + k * 20.0, 52.0, SZ), (px - 55.0 + k * 20.0, 64.0, SZ), 2.5, m["white"], root, 10))
    D.join(sp, "suppliers")
    glow = []
    for i, (name, x) in enumerate(SUP):
        g = empty(f"sup_glow{i}", root)
        bx(f"sg{i}", (x - 92.0, 11.0, SZ + 60.0), (x + 92.0, 12.5, SZ + 62.0), m["usd"], g)
        glow.append(g)
        show(g, [(F(3, 0.5), F(5, 0))])

    # beat 3: capex beads from every campus to the suppliers (about half to the GPUs)
    for k, (own, p) in enumerate(sites):
        tgt = SUP[0][1] if k % 2 == 0 else SUP[1 + (k // 2) % 2][1]
        run(root, f"usd{k}", [(p[0], 40.0, p[2]), ((p[0] + tgt) / 2, 140.0, (p[2] + SZ) / 2), (tgt, 30.0, SZ)],
            5, 7.0, m["usd"], [3, 4], 0.0, 0.7, 90)

    tags = {
        0: [("AWS campuses", sites[0][1]), ("Azure", sites[3][1]), ("Google Cloud", sites[6][1]),
            ("Meta (own use)", sites[8][1]), ("each: 100s of MW", h["racks"])],
        1: [("private fiber backbone", (-560.0, 5.0, -50.0)), ("region to region", (630.0, 5.0, -100.0)),
            ("no public internet hop", (0.0, 5.0, -640.0))],
        2: [("rows of identical AI racks", h["racks"]), ("liquid-cooled GPU / TPU", h["cdu"]),
            ("rented out as cloud", h["ups"])],
        3: [("capex: $100s of billions / yr", (0.0, 140.0, 250.0)), ("~half to chips + servers", (SUP[0][1], 22.0, SZ)),
            ("network + optics", (SUP[1][1], 36.0, SZ)), ("power + cooling + buildings", (SUP[2][1], 64.0, SZ))],
        4: [("NVDA, AVGO: top customers", (SUP[0][1], 22.0, SZ)), ("ANET, optics makers", (SUP[1][1], 36.0, SZ)),
            ("VRT power + cooling", (SUP[2][1], 64.0, SZ)), ("AMZN MSFT GOOGL META ORCL", (0.0, 30.0, -300.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 0.0, -180.0), 1500.0, 0.0, 0.85, pad=1.0),
        frame((0.0, 0.0, -180.0), 1450.0, 0.30, 0.70, pad=1.0),
        [(0.0, frame((-20.0, 10.0, -80.0), 320.0, 0.25, 0.55)), (0.45, frame((-30.0, 12.0, -50.0), 160.0, 0.30, 0.32))],
        frame((0.0, 30.0, 100.0), 1300.0, 0.0, 0.55, pad=1.0),
        frame((0.0, 30.0, SZ - 120.0), 640.0, 0.15, 0.50),
    ], root)


if __name__ == "__main__":
    build()
