"""TRM_FOUNDRY: a contract chip factory, drawn as a fab floor that serves many designers.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_foundry.py

Four customer design studios on the left send layouts in. In the middle a lithography scanner
stands cut open: light from a glowing reticle runs down a lens column onto a wafer on its stage,
and the wafer's die fields light one after another. A row of process tools (deposit, etch, CMP,
implant) sits behind, joined by an overhead rail that carries FOUP wafer pods. On the right,
finished wafers stack up and leave for packaging.

Beats:
  0 floor     many studios, one fab
  1 expose    reticle -> lens -> wafer, die fields light one by one
  2 loop      FOUPs ride the overhead rail tool to tool, hundreds of steps
  3 queue     every customer wants the newest node; the line runs full
  4 ship      wafers leave for packaging; who the foundries are
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from sand_overview import fly  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_FOUNDRY"
BEATS = [
    ("A foundry builds chips that other companies design",
     "A foundry is a chip factory for hire. Companies like Nvidia, AMD, Apple and Broadcom design chips but own no "
     "fabs; they send finished layouts to a foundry, which turns them into wafers. One fab serves hundreds of "
     "customers, so a single $20B+ building is shared instead of every designer paying for its own."),
    ("Lithography prints each layer: light through a mask onto the wafer",
     "The scanner shines extreme-ultraviolet (or deep-UV) light through a reticle (the mask holding one layer of the "
     "customer's design), shrinks it through a lens column and exposes the wafer one die field at a time. A "
     "leading-edge chip needs 60-plus mask layers, and each EUV scanner costs over $150M."),
    ("Wafers ride pods between hundreds of tools for about three months",
     "Between exposures, wafers travel in sealed pods (FOUPs) on an overhead rail to deposition, etch, polishing and "
     "implant tools, then back to litho. A modern chip takes over a thousand process steps and roughly 3-4 months "
     "from bare wafer to finished. Yield, the share of good dies, is what the foundry is really selling."),
    ("Leading-edge capacity is scarce, and AI chips queue for it",
     "Only a few fabs on Earth can make 3 nm and 2 nm chips, and nearly all of them belong to TSMC. Every AI "
     "accelerator, phone chip and server CPU wants the same newest node, so the line runs full and customers book "
     "capacity years ahead and prepay. That pricing power is why TSMC earns gross margins near 60%."),
    ("Finished wafers go to packaging; TSMC leads, others chase",
     "Finished wafers are tested and shipped to packaging (TSMC's own CoWoS lines or OSATs) where dies become chips. "
     "TSMC (TSM) has about two thirds of foundry revenue and almost all leading-edge AI work. Samsung, Intel Foundry "
     "(INTC), GlobalFoundries (GFS), UMC (UMC) and SMIC mostly compete on older, cheaper nodes."),
]

FLOOR = (-230.0, 230.0, -200.0, 40.0)
STUDIOS = [("NVDA", -120.0), ("AMD", -80.0), ("AVGO", -40.0), ("AAPL", 0.0)]
SX = -200.0  # studio column x
SC = (0.0, -80.0)  # scanner centre x, z
TOOLS = [("depo", -110.0), ("etch", -60.0), ("CMP", 60.0), ("implant", 110.0)]
TZ = -165.0  # tool row z
RAIL_Y = 88.0
WC = (0.0, 14.0, -80.0)  # wafer centre on the stage
OUT = (185.0, -60.0)


def mats(m):
    m["code"] = mat("fd_code", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=2.5)
    m["euv"] = mat("fd_euv", (0.75, 0.45, 1.0), emit=(0.70, 0.40, 1.0), strength=3.0)
    m["exp"] = mat("fd_exp", (0.80, 0.55, 1.0), emit=(0.75, 0.50, 1.0), strength=1.0)
    m["wafer"] = mat("fd_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["foup"] = mat("fd_foup", (0.85, 0.86, 0.88), rough=0.45)
    m["tool"] = mat("fd_tool", (0.80, 0.82, 0.84), metal=0.2, rough=0.5)
    m["glass"] = mat("fd_glass", (0.35, 0.45, 0.55), metal=0.0, rough=0.1)
    m["full"] = mat("fd_full", (1.0, 0.35, 0.15), emit=(1.0, 0.30, 0.10), strength=2.5)


def studios(m, root):
    pts = {}
    for name, z in STUDIOS:
        g = empty(f"st_{name}", root)
        bx(f"st_{name}_desk", (SX - 14.0, 0.0, z - 14.0), (SX + 14.0, 8.0, z + 14.0), m["dark"], g)
        bx(f"st_{name}_bz", (SX - 11.0, 8.0, z - 6.0), (SX + 11.0, 26.0, z - 4.0), m["plastic"], g)
        bx(f"st_{name}_sc", (SX - 10.0, 9.0, z - 4.0), (SX + 10.0, 25.0, z - 3.8), m["screen"], g)
        for r in range(5):  # layout lines on the screen
            w = 6.0 + 2.5 * ((r * 3 + len(name)) % 4)
            bx(f"st_{name}_l{r}", (SX - 8.0, 22.5 - 3.0 * r, z - 3.7), (SX - 8.0 + w, 23.5 - 3.0 * r, z - 3.6), m["code"], g)
        bx(f"st_{name}_kb", (SX - 8.0, 8.0, z + 2.0), (SX + 8.0, 9.0, z + 8.0), m["plastic"], g)
        pts[name] = (SX, 27.0, z - 4.0)
    return pts


def scanner(m, root):
    """The cut-open scanner: base, wafer stage, wafer with die grid, lens column, reticle stage.
    Returns die-exposure groups, beam group and points."""
    x, z = SC
    g = empty("scan", root)
    bx("sc_base", (x - 50.0, 0.0, z - 45.0), (x + 50.0, 6.0, z + 45.0), m["dark"], g)
    bx("sc_stage", (x - 34.0, 6.0, z - 34.0), (x + 34.0, 12.0, z + 34.0), m["alu"], g)
    for s in (-1, 1):  # stage rails
        bx(f"sc_rail{s}", (x - 46.0, 6.0, z + s * 38.0 - 2.0), (x + 46.0, 9.0, z + s * 38.0 + 2.0), m["cold"], g)
    D.tube("sc_wafer", (x, 12.0, z), (x, 13.4, z), 28.0, m["wafer"], g, 64)
    # back frame and a cut-away housing (back wall + one side) so the inside stays visible
    bx("sc_back", (x - 50.0, 6.0, z - 45.0), (x + 50.0, 110.0, z - 41.0), m["tool"], g)
    bx("sc_side", (x - 50.0, 6.0, z - 41.0), (x - 46.0, 110.0, z + 45.0), m["tool"], g)
    bx("sc_roof", (x - 50.0, 106.0, z - 41.0), (x + 50.0, 110.0, z - 10.0), m["tool"], g)
    # lens column: stacked lens elements in a barrel
    for k in range(7):
        y = 30.0 + 6.0 * k
        r = 10.0 + 3.0 * abs(k - 3) * -0.6 + 4.0
        D.tube(f"sc_lens{k}", (x, y, z), (x, y + 1.6, z), r, m["glass"], g, 32)
        D.tube(f"sc_ring{k}", (x, y + 1.6, z), (x, y + 4.0, z), r + 2.0, m["alu"], g, 32)
    bx("sc_col_arm", (x - 4.0, 30.0, z - 41.0), (x + 4.0, 72.0, z - 16.0), m["alu"], g)
    # reticle stage on top
    bx("sc_rstage", (x - 30.0, 80.0, z - 20.0), (x + 30.0, 84.0, z + 20.0), m["alu"], g)
    bx("sc_ret", (x - 16.0, 84.0, z - 16.0), (x + 16.0, 85.0, z + 16.0), m["quartz_c"], g)
    ret = empty("sc_ret_pat", root)
    for i in range(6):
        bx(f"sc_rp{i}", (x - 14.0 + 5.0 * i, 85.0, z - 14.0), (x - 12.0 + 5.0 * i, 85.4, z + 14.0), m["euv"], ret)
    # light source box feeding in from the back
    bx("sc_src", (x + 10.0, 92.0, z - 40.0), (x + 40.0, 104.0, z - 20.0), m["dark"], g)
    # die grid on the wafer + their exposure glows, lit one by one
    dies, glows = [], []
    order = []
    for j in range(-4, 5):
        row = list(range(-4, 5)) if j % 2 == 0 else list(range(4, -5, -1))
        for i in row:
            if (5.6 * i) ** 2 + (5.6 * j) ** 2 < 24.0 ** 2:
                order.append((i, j))
    for n, (i, j) in enumerate(order):
        cx, cz = x + 5.6 * i, z + 5.6 * j
        dies.append(bx(f"sc_d{i}_{j}", (cx - 2.5, 13.4, cz - 2.5), (cx + 2.5, 13.7, cz + 2.5), m["die"], g))
        e = empty(f"sc_x{n}", root)
        bx(f"sc_xb{n}", (cx - 2.4, 13.7, cz - 2.4), (cx + 2.4, 14.0, cz + 2.4), m["exp"], e)
        glows.append((e, (cx, cz)))
    D.join(dies, "sc_dies")
    # beam segments: reticle -> lens, lens -> wafer (a thin column, retargeted per die via groups)
    beam = empty("sc_beam", root)
    D.tube("sc_b1", (x, 80.0, z), (x, 72.0, z), 6.0, m["euv"], beam, 16)
    D.tube("sc_b2", (x, 30.0, z), (x, 14.0, z), 1.6, m["euv"], beam, 12)
    pts = {"scan": (x, 110.0, z - 20.0), "ret": (x + 16.0, 85.0, z), "lens": (x + 14.0, 50.0, z),
           "wafer": (x + 20.0, 14.0, z + 20.0), "stage": (x + 34.0, 10.0, z + 30.0)}
    return ret, glows, beam, pts


def tools(m, root):
    leds = [empty(f"tl_led{k}", root) for k in range(3)]
    pts = {}
    for k, (name, x) in enumerate(TOOLS):
        g = empty(f"tl_{name}", root)
        bx(f"tl_{name}_b", (x - 20.0, 0.0, TZ - 20.0), (x + 20.0, 60.0, TZ + 20.0), m["tool"], g)
        bx(f"tl_{name}_door", (x - 14.0, 10.0, TZ + 20.0), (x + 14.0, 40.0, TZ + 20.6), m["glass"], g)
        bx(f"tl_{name}_port", (x - 10.0, 60.0, TZ - 6.0), (x + 10.0, 62.0, TZ + 6.0), m["dark"], g)
        D.tube(f"tl_{name}_lift", (x, 62.0, TZ), (x, RAIL_Y - 4.0, TZ), 0.6, m["alu"], g, 8)
        for j in range(3):
            bx(f"tl_{name}_l{j}", (x + 10.0 + 2.5 * j, 50.0, TZ + 20.6), (x + 12.0 + 2.5 * j, 52.0, TZ + 21.0), m["sig"], leds[(k + j) % 3])
        pts[name] = (x, 62.0, TZ + 20.0)
    for l in leds:
        show(l, [])
    # overhead rail: a loop over the tools and the scanner
    rail = [(-180.0, RAIL_Y, TZ), (180.0, RAIL_Y, TZ), (180.0, RAIL_Y, -20.0), (-180.0, RAIL_Y, -20.0), (-180.0, RAIL_Y, TZ)]
    for k in range(4):
        D.polyline(f"rail{k}", [rail[k], rail[k + 1]], 1.2, m["alu"], root)
    for x in (-180.0, -60.0, 60.0, 180.0):
        for zz in (TZ, -20.0):
            D.tube(f"hang{x:.0f}{zz:.0f}", (x, RAIL_Y, zz), (x, RAIL_Y + 30.0, zz), 0.8, m["alu"], root, 8)
    return leds, rail, pts


def foup(m, parent, name, c):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_b", (x - 5.0, y - 9.0, z - 5.0), (x + 5.0, y - 1.0, z + 5.0), m["foup"], g)
    bx(f"{name}_h", (x - 2.0, y - 1.0, z - 2.0), (x + 2.0, y, z + 2.0), m["dark"], g)
    bx(f"{name}_w", (x - 4.0, y - 8.0, z + 5.0), (x + 4.0, y - 2.0, z + 5.2), m["wafer"], g)
    return g


def output(m, root):
    x, z = OUT
    g = empty("out", root)
    bx("out_tbl", (x - 22.0, 0.0, z - 22.0), (x + 22.0, 10.0, z + 22.0), m["dark"], g)
    for k in range(10):
        D.tube(f"out_w{k}", (x, 10.0 + 1.6 * k, z), (x, 11.0 + 1.6 * k, z), 15.0, m["wafer"], g, 48)
    show(g, [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))])
    return {"out": (x, 27.0, z)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    x0, x1, z0, z1 = FLOOR
    bx("floor", (x0, -3.0, z0), (x1, 0.0, z1), m["grid"], root)
    for i in range(12):  # raised-floor tile seams
        xx = x0 + (x1 - x0) * (i + 0.5) / 12
        bx(f"seam{i}", (xx - 0.3, 0.0, z0), (xx + 0.3, 0.1, z1), m["dark"], root)
    sp = studios(m, root)
    ret, glows, beam, cp = scanner(m, root)
    leds, rail, tp = tools(m, root)
    op = output(m, root)

    # beat 0: every studio sends its layout into the scanner
    for k, (name, z) in enumerate(STUDIOS):
        run(root, f"lay{k}", [sp[name], (SX + 60.0, 50.0, z), (SC[0] - 30.0, 95.0, SC[1]), (SC[0], 86.0, SC[1])],
            3, 1.2, m["code"], [0, 3], 0.05 + 0.15 * k, 0.4 + 0.15 * k, 45)
    show(ret, [(F(0, 0.5), F(5, 0))])
    for l in leds:
        blink(l, 0, [0, 2, 4, 6], n=8, on=0.6)

    # beat 1: light runs reticle -> lens -> wafer; each die field lights and stays lit
    show(beam, [(F(1, 0.05), F(1, 0.95)), (F(3, 0.0), F(4, 0))])
    run(root, "photon", [(SC[0] + 25.0, 98.0, SC[1] - 30.0), (SC[0], 86.0, SC[1]), (SC[0], 50.0, SC[1]), (SC[0], 14.5, SC[1])],
        10, 0.9, m["euv"], 1, 0.0, 0.85, 30)
    n = len(glows)
    for k, (e, _) in enumerate(glows):
        show(e, [(F(1, 0.08 + 0.85 * k / n), F(2, 0)), (F(3, 0.85 * k / n), F(4, 0))])

    # beat 2: FOUPs ride the rail loop, dropping to tools
    loop = rail
    for k in range(5):
        g = foup(m, root, f"foup{k}", loop[0])
        path = [tuple(p[i] - loop[0][i] for i in range(3)) for p in loop]
        f0 = F(2, 0.02 + 0.16 * k)
        fly(g, path, f0, f0 + 90, steps=20)
        show(g, [(F(2, 0.0), F(3, 0))])
    for l in leds:
        blink(l, 2, [1, 3, 5, 7], n=8, on=0.7)
        blink(l, 3, [0, 2, 4, 6], n=8, on=0.7)

    # beat 3: the queue. wafer pods from every customer lined up waiting; the line runs full
    q = empty("queue", root)
    for k in range(9):
        zz = -10.0 + 0.0 * k
        xx = -150.0 + 15.0 * k
        D.tube(f"q_w{k}", (xx, 0.0, 22.0), (xx, 1.2, 22.0), 6.0, m["wafer"], q, 32)
        foup(m, q, f"q_f{k}", (xx, 12.0, 22.0))
    show(q, [(F(3, 0.1), F(4, 0))])
    meter = empty("meter", root)
    bx("m_frame", (60.0, 0.0, 18.0), (64.0, 62.0, 26.0), m["dark"], meter)
    show(meter, [(F(3, 0.0), F(4, 0))])
    for k in range(10):
        e = empty(f"m_bar{k}", root)
        bx(f"m_b{k}", (64.0, 2.0 + 6.0 * k, 19.0), (74.0, 6.5 + 6.0 * k, 25.0), m["full" if k >= 7 else "sig"], e)
        show(e, [(F(3, 0.1 + 0.06 * k), F(4, 0))])
    rise(root, "scan_heat", (SC[0], 108.0, SC[1] - 30.0), 6, 1.0, m["heat"], 3, 0.1, 0.8, 22.0, 50, (20.0, 8.0))

    # beat 4: wafers leave for packaging
    run(root, "ship", [(SC[0] + 30.0, 16.0, SC[1] + 20.0), (120.0, 30.0, -60.0), (OUT[0], 30.0, OUT[1])], 6, 1.6, m["v12"], 4, 0.0, 0.5, 40)
    run(root, "pkg", [(OUT[0], 30.0, OUT[1]), (OUT[0] + 40.0, 30.0, OUT[1] + 40.0), (240.0, 20.0, 30.0)], 5, 1.4, m["v12"], 4, 0.4, 0.85, 35)

    C.tags(root, {
        0: [("design studios (fabless)", sp["AMD"]), ("litho scanner, cut open", cp["scan"]),
            ("process tools", tp["etch"]), ("one fab, many customers", (SC[0] + 60.0, 70.0, -20.0))],
        1: [("reticle: one layer's mask", cp["ret"]), ("lens shrinks the image 4x", cp["lens"]),
            ("die fields exposed one by one", cp["wafer"])],
        2: [("FOUP pods on overhead rail", (120.0, RAIL_Y, -20.0)), ("deposit / etch / CMP", tp["CMP"]),
            ("1000+ steps, ~3 months", tp["depo"])],
        3: [("every customer wants 3/2 nm", (-90.0, 20.0, 22.0)), ("line runs at ~100%", (69.0, 64.0, 22.0)),
            ("book capacity years ahead", sp["NVDA"])],
        4: [("finished wafers", op["out"]), ("-> packaging (CoWoS, OSAT)", (225.0, 22.0, 20.0)),
            ("TSM ~2/3 of foundry revenue", cp["scan"]), ("GFS, UMC, INTC chase", tp["implant"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 40.0, -80.0), 440.0, 0.25, 0.42, pad=1.0),
        [(0.0, frame((SC[0], 50.0, SC[1]), 120.0, 0.35, 0.25)), (0.6, frame((SC[0], 14.0, SC[1]), 70.0, 0.30, 0.65))],
        frame((0.0, 60.0, -100.0), 380.0, 0.15, 0.30, pad=1.0),
        frame((-30.0, 30.0, -20.0), 300.0, 0.10, 0.35),
        frame((80.0, 30.0, -60.0), 330.0, -0.30, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
