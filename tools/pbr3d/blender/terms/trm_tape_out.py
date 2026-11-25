"""TRM_TAPE_OUT: the hand-off from design to silicon, as a line on a bench. A design workstation
with the finished layout on its screen (left), a mask shop's rack of photomasks, each a quartz
plate with its chrome pattern (middle), a fab enclosure where a cut-open wafer builds up layer by
layer (right), and a test board where the first chip comes back and powers up (far right).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tape_out.py

Beats:
  0 line     design -> masks -> fab -> silicon, the whole bench
  1 gds      the layout freezes; the GDSII file streams to the mask shop
  2 masks    ~70 masks, written one by one
  3 fab      the wafer climbs through layers for ~3-4 months
  4 back     first silicon on the test board; who announces tape-outs
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_TAPE_OUT"
BEATS = [
    ("Tape-out: the finished chip design leaves for the factory",
     "Tape-out is the moment a chip's design is frozen and handed to the foundry. Everything before it is software "
     "and simulation; everything after is physical: masks, wafers, packaging, test. The name dates from when layouts "
     "were shipped on magnetic tape."),
    ("The final layout is sent as one huge file",
     "The design team signs off on timing, power and the foundry's rule checks, then exports the layout (a GDSII or "
     "OASIS file, often hundreds of gigabytes) describing every polygon on every layer. After this, a bug means a "
     "re-spin: new masks and months of delay."),
    ("The mask shop turns each layer into a photomask",
     "Each layer becomes a photomask: a quartz plate patterned in chrome by an electron-beam writer. A leading-edge "
     "chip needs roughly 60-90 masks, several of them EUV. A full set at 3nm-class nodes costs tens of millions of "
     "dollars, which is why only high-volume chips go to the newest nodes."),
    ("The fab builds the wafer layer by layer for months",
     "Wafers go through more than a thousand process steps: print a layer with its mask, etch, deposit, polish, "
     "repeat. Transistors at the bottom, a dozen-plus copper wiring layers on top. Start to finish takes about 3-4 "
     "months at a leading node, before packaging adds more weeks."),
    ("First silicon comes back and is brought up on a test board",
     "The first parts are mounted on test boards and powered up ('bring-up') to check they work at speed. Companies "
     "announce tape-outs as proof a product is on schedule; revenue typically follows 9-12 months later. NVIDIA (NVDA), "
     "Broadcom (AVGO) and Marvell (MRVL) tape out custom chips; Synopsys (SNPS) and Cadence (CDNS) sell the tools."),
]

WS = (-175.0, -115.0)  # workstation x
MK = (-70.0, 10.0)  # mask rack x
FB = (45.0, 125.0)  # fab enclosure x
TB = (150.0, 220.0)  # test board x
N_MASK = 12


def mats(m):
    m["quartz"] = mat("to_quartz", (0.80, 0.88, 0.95), rough=0.1)
    m["chrome"] = mat("to_chrome", (0.25, 0.26, 0.30), metal=0.95, rough=0.2)
    m["lay"] = mat("to_lay", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["lay2"] = mat("to_lay2", (1.0, 0.45, 0.70), emit=(1.0, 0.40, 0.65), strength=2.5)
    m["data"] = mat("to_data", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=4.0)
    m["ebeam"] = mat("to_ebeam", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=4.0)
    m["wafer"] = mat("to_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["shell"] = mat("to_shell", (0.86, 0.88, 0.90), rough=0.5)
    m["ok"] = mat("to_ok", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=3.0)


def bench(m, root):
    bx("bench", (-200.0, -6.0, -110.0), (240.0, -2.0, 25.0), m["dark"], root)


def workstation(m, root):
    g = empty("ws", root)
    x0, x1 = WS
    xc = (x0 + x1) / 2
    bx("ws_stand", (xc - 3.0, -2.0, -46.0), (xc + 3.0, 10.0, -42.0), m["alu"], g)
    bx("ws_bezel", (x0, 10.0, -48.0), (x1, 56.0, -44.0), m["plastic"], g)
    bx("ws_scr", (x0 + 2.0, 12.0, -44.0), (x1 - 2.0, 54.0, -43.8), m["screen"], g)
    bx("ws_kb", (x0 + 8.0, -2.0, -26.0), (x1 - 8.0, -0.8, -14.0), m["plastic"], g)
    lay = empty("ws_lay", g)
    for r in range(9):  # a layout: cell rows and two metal directions
        y = 15.0 + 4.3 * r
        bx(f"ws_r{r}", (x0 + 5.0, y, -43.7), (x1 - 5.0, y + 1.0, -43.5), m["lay"], lay)
    for c in range(10):
        x = x0 + 7.0 + 5.0 * c
        ya = 16.0 + 3.0 * ((c * 3) % 5)
        bx(f"ws_c{c}", (x, ya, -43.6), (x + 0.9, ya + 20.0, -43.4), m["lay2"], lay)
    lock = empty("ws_lock", root)  # a sign-off bar across the screen top
    bx("ws_lockb", (x0 + 4.0, 50.0, -43.4), (x1 - 4.0, 52.5, -43.2), m["ok"], lock)
    show(lock, [(F(1, 0.2), F(5, 0))])
    return {"scr": (xc, 56.0, -44.0), "lay": (xc + 15.0, 30.0, -43.5), "lock": (xc, 52.0, -43.0)}


def masks(m, root):
    """A rack of photomasks standing on edge, an e-beam writer head over the front one."""
    g = empty("mk", root)
    x0, x1 = MK
    bx("mk_base", (x0, -2.0, -60.0), (x1, 2.0, -6.0), m["alu"], g)
    for s in (-1, 1):
        bx(f"mk_rail{s}", (x0 + 4.0, 2.0, -60.0 if s < 0 else -10.0), (x1 - 4.0, 6.0, -56.0 if s < 0 else -6.0), m["alu"], g)
    glows = []
    pitch = (x1 - x0 - 12.0) / N_MASK
    for k in range(N_MASK):
        x = x0 + 6.0 + pitch * (k + 0.5)
        bx(f"mk_q{k}", (x - 0.8, 2.0, -56.0), (x + 0.8, 44.0, -10.0), m["quartz"], g)
        # chrome pattern: bars on the front face, different per layer
        for j in range(6):
            y = 6.0 + 6.0 * j + (k % 3)
            bx(f"mk_c{k}_{j}", (x - 0.9, y, -50.0 + 3.0 * ((k + j) % 4)), (x + 0.9, y + 2.5, -16.0 - 2.0 * ((k * j) % 3)), m["chrome"], g)
        gl = empty(f"mk_g{k}", root)
        bx(f"mk_gb{k}", (x - 1.0, 44.0, -54.0), (x + 1.0, 45.0, -12.0), m["ebeam"], gl)
        show(gl, [(F(2, 0.05 + 0.07 * k), F(5, 0))])
        glows.append(gl)
    # the e-beam writer column over the rack
    bx("mk_col", (x1 - 18.0, 60.0, -40.0), (x1 - 4.0, 90.0, -26.0), m["dark"], g)
    bx("mk_gun", (x1 - 14.0, 54.0, -36.0), (x1 - 8.0, 60.0, -30.0), m["steel"], g)
    beam = empty("mk_beam", root)
    D.tube("mk_bm", (x1 - 11.0, 54.0, -33.0), (x1 - 11.0, 45.0, -33.0), 0.5, m["ebeam"], beam, 8)
    blink(beam, 2, [0, 2, 4, 6], n=8, on=0.6)
    return {"rack": ((x0 + x1) / 2, 45.0, -10.0), "q": (x0 + 8.0, 30.0, -10.0), "col": (x1 - 11.0, 90.0, -26.0),
            "c": ((x0 + x1) / 2, 25.0, -30.0)}


def fab(m, root):
    """A cleanroom box with the front wall cut away; inside, a big cut wafer whose layers appear."""
    g = empty("fb", root)
    x0, x1 = FB
    xc = (x0 + x1) / 2
    bx("fb_floor", (x0, -2.0, -80.0), (x1, 0.0, 0.0), m["grid"], g)
    bx("fb_back", (x0, 0.0, -80.0), (x1, 70.0, -76.0), m["shell"], g)
    bx("fb_roof", (x0, 70.0, -80.0), (x1, 74.0, -30.0), m["shell"], g)
    for s, x in ((-1, x0), (1, x1)):
        bx(f"fb_side{s}", (x, 0.0, -80.0), (x - s * 4.0, 70.0, 0.0), m["shell"], g)
    for k in range(5):  # ceiling filter units
        bx(f"fb_ffu{k}", (x0 + 6.0 + 14.0 * k, 66.0, -72.0), (x0 + 16.0 + 14.0 * k, 70.0, -36.0), m["alu"], g)
    # the wafer, cut through: substrate then layers that build up
    wx0, wx1 = xc - 32.0, xc + 32.0
    bx("fb_chuck", (wx0 - 2.0, 0.0, -50.0), (wx1 + 2.0, 8.0, -6.0), m["steel"], g)
    bx("fb_sub", (wx0, 8.0, -48.0), (wx1, 16.0, -8.0), m["si"], g)
    mts = ["nplus", "metalg", "oxide", "copper", "oxide", "copper", "oxide", "copper", "oxide", "copper"]
    for k, mt in enumerate(mts):
        lg = empty(f"fb_l{k}", root)
        y0 = 16.0 + 2.4 * k
        bx(f"fb_lb{k}", (wx0, y0, -48.0), (wx1, y0 + 2.4, -8.0), m[mt if mt != "metalg" else "alum"], lg)
        if mt == "copper":
            for j in range(8):  # vias poking through each dielectric
                x = wx0 + 4.0 + 8.0 * j + 2.0 * (k % 2)
                bx(f"fb_v{k}_{j}", (x, y0 - 2.4, -8.6), (x + 1.2, y0, -8.0), m["copper"], lg)
        show(lg, [(F(0, 0), F(1, 0)), (F(3, 0.05 + 0.085 * k), F(5, 0))])
    rise(root, "fb_heat", (xc, 42.0, -28.0), 5, 1.0, m["heat"], 3, 0.1, 0.9, 20.0, 50, (20.0, 10.0))
    C.rings(m, root, "fb_clk", (xc, 52.0, -28.0), 3, n=3, r0=4.0, r1=26.0, mt="h_amber", axis="xz")
    return {"wafer": (wx1, 40.0, -8.0), "sub": (wx0, 12.0, -8.0), "box": (xc, 74.0, -50.0), "c": (xc, 30.0, -30.0)}


def testboard(m, root):
    g = empty("tb", root)
    x0, x1 = TB
    xc = (x0 + x1) / 2
    bx("tb_fr4", (x0, -2.0, -60.0), (x1, 0.0, -6.0), m["fr4"], g)
    bx("tb_mask", (x0, 0.0, -60.0), (x1, 0.4, -6.0), m["mask"], g)
    bx("tb_sock", (xc - 16.0, 0.4, -46.0), (xc + 16.0, 6.0, -18.0), m["plastic"], g)
    bx("tb_sub", (xc - 12.0, 6.0, -42.0), (xc + 12.0, 8.0, -22.0), m["substrate"], g)
    bx("tb_die", (xc - 7.0, 8.0, -38.0), (xc + 7.0, 10.0, -26.0), m["die"], g)
    hot = empty("tb_hot", root)
    bx("tb_dh", (xc - 7.1, 10.0, -38.1), (xc + 7.1, 10.3, -25.9), m["die_hot"], hot)
    show(hot, [(F(4, 0.25), F(5, 0))])
    for k in range(3):
        C.chip(m, g, f"tb_ic{k}", (x0 + 12.0 + 22.0 * k, 0.4, -12.0), 8.0, 5.0, 1.4, pins=4)
    bx("tb_conn", (x1 - 6.0, 0.4, -56.0), (x1, 6.0, -24.0), m["plastic"], g)
    led = empty("tb_led", root)
    bx("tb_l", (x0 + 4.0, 0.4, -54.0), (x0 + 7.0, 2.0, -51.0), m["ok"], led)
    blink(led, 4, [2, 3, 4, 5, 6, 7], n=8, on=0.6)
    for k in range(4):
        run(root, f"tb_p{k}", [(x1 - 4.0, 4.0, -30.0 - 6.0 * k), (xc + 16.0, 4.0, -30.0 - 6.0 * k), (xc + 7.0, 10.0, -32.0)],
            3, 0.8, m["v12"], 4, 0.2 + 0.05 * k, 0.9, 30)
    rise(root, "tb_heat", (xc, 10.0, -32.0), 4, 0.8, m["heat"], 4, 0.4, 0.95, 18.0, 50, (5.0, 4.0))
    return {"die": (xc, 10.0, -26.0), "sock": (xc - 16.0, 6.0, -18.0), "led": (x0 + 5.5, 2.0, -51.0), "c": (xc, 5.0, -32.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bench(m, root)
    ws, mk, fb, tb = workstation(m, root), masks(m, root), fab(m, root), testboard(m, root)
    # flows between stations: data to the mask shop, masks to the fab, chips to the board
    run(root, "gds", [(WS[1] - 4.0, 50.0, -44.0), (-95.0, 70.0, -40.0), (MK[0] + 10.0, 52.0, -33.0)],
        14, 1.0, m["data"], [1], 0.15, 0.9, 40)
    run(root, "gds0", [(WS[1] - 4.0, 50.0, -44.0), (-95.0, 70.0, -40.0), (MK[0] + 10.0, 52.0, -33.0)],
        6, 1.0, m["data"], [0], 0.1, 0.5, 40)
    run(root, "mk2fb", [(MK[1] - 4.0, 30.0, -30.0), (28.0, 60.0, -30.0), (FB[0] + 10.0, 30.0, -28.0)],
        6, 1.0, m["ebeam"], [0, 3], 0.1, 0.5, 40)
    run(root, "fb2tb", [(FB[1] - 6.0, 30.0, -28.0), (138.0, 40.0, -30.0), (TB[0] + 30.0, 12.0, -32.0)],
        5, 1.2, m["v12"], [0, 4], 0.05, 0.3, 35)
    C.tags(root, {
        0: [("design sign-off", ws["scr"]), ("photomask set", mk["rack"]), ("fab: ~3-4 months", fb["box"]),
            ("first silicon", tb["die"])],
        1: [("final layout, frozen", ws["lay"]), ("sign-off checks pass", ws["lock"]),
            ("GDSII file to mask shop", (-95.0, 70.0, -40.0))],
        2: [("~60-90 masks per chip", mk["rack"]), ("chrome on quartz", mk["q"]), ("e-beam writer", mk["col"]),
            ("set costs tens of $M", (MK[0] + 6.0, 2.0, -6.0))],
        3: [("1000+ process steps", fb["wafer"]), ("transistors at the bottom", fb["sub"]),
            ("copper wiring layers above", (FB[1] - 20.0, 38.0, -8.0)), ("months per lot", (sum(FB) / 2, 64.0, -30.0))],
        4: [("bring-up on a test board", tb["led"]), ("powers on, runs at speed", tb["die"]),
            ("NVDA, AVGO, MRVL tape out", (TB[1] - 3.0, 6.0, -40.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 30.0, -40.0), 420.0, 0.15, 0.30, pad=0.85),
        frame((-130.0, 40.0, -40.0), 120.0, 0.20, 0.20),
        frame((-35.0, 40.0, -30.0), 110.0, 0.35, 0.30),
        frame(fb["c"], 110.0, 0.20, 0.25),
        frame(tb["c"], 110.0, 0.25, 0.60),
    ], root)


if __name__ == "__main__":
    build()
