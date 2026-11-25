"""TRM_HAMR: a hard drive opened up (spinning platter, actuator arm, head), the head and the platter's
recording layer cut open huge on the bench: a laser and gold antenna heat a spot of FePt grains so the
write pole can flip them. Then a drive shelf for capacity.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hamr.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import blink, frame, rise, run  # noqa: E402
from sand_overview import disc, pivot, rel, tube  # noqa: E402

SLUG = "TRM_HAMR"
BEATS = [
    ("A hard drive writes bits as tiny magnetized patches on a spinning platter",
     "Inside a drive, glass or aluminium platters spin at 7,200 rpm while an arm swings a head a few nanometres above "
     "the surface. Each bit is a patch of magnetic grains pointing up or down. More bits per platter means more "
     "terabytes per drive without adding platters."),
    ("Smaller bits need tougher grains, which a normal head cannot flip",
     "To shrink a bit you shrink the grains, but small grains lose their magnetism to room-temperature jiggling unless "
     "the material is very stubborn (high coercivity, like iron-platinum). The write pole's field is too weak to flip "
     "such stubborn grains cold."),
    ("HAMR: a laser heats a nanometre spot for about a nanosecond, then the pole writes it",
     "A laser diode on the slider sends light down a waveguide to a gold near-field transducer, which focuses it to a "
     "spot tens of nanometres wide. The spot heats past about 400 C, the grains soften, the pole flips them, and they "
     "cool locked in place within a nanosecond as the platter moves on."),
    ("Result: smaller grains and denser tracks than conventional recording",
     "With grains that stay stable at small sizes, HAMR raises areal density well past conventional perpendicular "
     "recording (PMR). Drives of 30-36 TB ship today with roadmaps toward 50 TB and beyond, at the same 3.5-inch size."),
    ("Bulk storage for AI data lakes: Seagate (STX), Western Digital (WDC), Toshiba (6502.T)",
     "Training sets, checkpoints and logs mostly live on hard drives because they are still several times cheaper per "
     "terabyte than flash. Seagate (STX) ships HAMR first as Mozaic; Western Digital (WDC) and Toshiba (6502.T) are "
     "bringing their own HAMR drives."),
]

PC = (-40.0, 2.0, -95.0)  # platter centre
PR = 72.0
HEAD = (2.0, 4.6, -40.0)
APIV = (48.0, 4.0, -22.0)
# bench
BX0, BX1 = 152.0, 246.0
MY = (0.0, 4.0, 5.5, 8.5, 9.0)  # glass, soft underlayer, grains, carbon top
NFT_X = 206.0


def mats(m):
    m["up"] = mat("hamr_up", (0.22, 0.38, 0.70), metal=0.3, rough=0.4)
    m["dn"] = mat("hamr_dn", (0.66, 0.30, 0.24), metal=0.3, rough=0.4)
    m["up_g"] = mat("hamr_up_g", (0.35, 0.60, 1.0), emit=(0.30, 0.55, 1.0), strength=2.5)
    m["dn_g"] = mat("hamr_dn_g", (1.0, 0.45, 0.30), emit=(1.0, 0.40, 0.25), strength=2.5)
    m["platter"] = mat("hamr_platter", (0.78, 0.80, 0.84), metal=0.95, rough=0.12)
    m["laser"] = mat("hamr_laser", (1.0, 0.25, 0.20), emit=(1.0, 0.18, 0.12), strength=4.0)
    m["hot"] = mat("hamr_hot", (1.0, 0.85, 0.40), emit=(1.0, 0.75, 0.30), strength=5.0)


def drive(m, root):
    """The opened drive: casting, spinning platter with tracks, actuator, voice coil."""
    g = empty("hdd", root)
    bx("cast_floor", (-125.0, -6.0, -178.0), (70.0, -1.0, 0.0), m["alu"], g)
    for k, (lo, hi) in enumerate([((-125.0, -6.0, -178.0), (-119.0, 8.0, 0.0)), ((64.0, -6.0, -178.0), (70.0, 8.0, 0.0)),
                                  ((-125.0, -6.0, -178.0), (70.0, 8.0, -172.0))]):
        bx(f"cast_wall{k}", lo, hi, m["alu"], g)
    for k, c in enumerate([(-112.0, 8.0, -165.0), (57.0, 8.0, -165.0), (-112.0, 8.0, -8.0), (57.0, 8.0, -8.0)]):
        disc(f"screw{k}", c, 2.2, 0.8, m["steel"], g, 16)
    # platter, spinning about its own pivot; tracks and bits ride on it
    piv = pivot("platter_piv", PC, g)
    disc("platter", (0.0, 0.0, 0.0), PR, 1.4, m["platter"], piv, 128)
    disc("hub", (0.0, 1.4, 0.0), 13.0, 2.4, m["steel"], piv, 48)
    disc("clamp", (0.0, 2.8, 0.0), 9.0, 0.8, m["alu"], piv, 48)
    for k in range(6):
        a = k * math.pi / 3
        disc(f"clamp_s{k}", (6.0 * math.cos(a), 3.3, 6.0 * math.sin(a)), 0.9, 0.4, m["dark"], piv, 10)
    for t, r in enumerate((26.0, 38.0, 50.0, 62.0)):
        pts = [(r * math.cos(2 * math.pi * j / 96), 0.75, r * math.sin(2 * math.pi * j / 96)) for j in range(97)]
        D.polyline(f"track{t}", pts, 0.18, m["dark"], piv)
    r = 50.0
    for j in range(48):
        a = 2 * math.pi * j / 48
        x, z = r * math.cos(a), r * math.sin(a)
        mt = m["up_g"] if (j * 7) % 3 else m["dn_g"]
        bx(f"bit{j}", (x - 1.0, 0.75, z - 1.0), (x + 1.0, 1.0, z + 1.0), mt, piv)
    # actuator: pivot bearing, arm, suspension, slider; voice coil behind
    disc("act_bear", APIV, 7.0, 6.0, m["steel"], g, 32)
    D.wire("arm", [APIV, (28.0, 5.0, -30.0), HEAD], 2.2, m["alu"], g)
    bx("slider", (HEAD[0] - 2.5, 3.6, HEAD[2] - 2.0), (HEAD[0] + 2.5, 4.4, HEAD[2] + 2.0), m["aln"], g)
    bx("coil", (52.0, 2.0, -48.0), (64.0, 6.0, -6.0), m["copper"], g)
    bx("magnet", (50.0, 7.0, -50.0), (64.0, 9.0, -4.0), m["moly"], g)
    D.wire("flex", [(46.0, 6.0, -10.0), (30.0, 6.0, -6.0), (0.0, 1.0, -6.0)], 0.8, m["copper"], g)
    C.chip(m, g, "preamp", (-10.0, 0.5, -10.0), 8.0, 6.0, 1.2, pins=4)
    return piv


def bench(m, root):
    """The head and the recording layer cut open on the bench."""
    g = empty("bench", root)
    C.xsec(m, g, "media", BX0, BX1, -40.0, [(MY[0], MY[1], "quartz_c"), (MY[1], MY[2], "moly")])
    bx("carbon", (BX0, MY[3], -40.0), (BX1, MY[4], 0.0), m["dark"], g)
    grains = []
    x = BX0
    k = 0
    while x < BX1 - 1.0:
        w = 1.6 + 0.5 * ((k * 5) % 3) / 2
        mt = m["up"] if (k * 7 + k // 3) % 3 else m["dn"]
        bx(f"gr{k}", (x, MY[2], -40.0), (x + w, MY[3], 0.0), mt, g)
        grains.append(x + w / 2)
        x += w + 0.5
        k += 1
    # conventional media below: fat grains
    C.xsec(m, g, "pmr", BX0, BX1, -20.0, [(-22.0, -18.0, "quartz_c"), (-18.0, -16.5, "moly")])
    x, k = BX0, 0
    while x < BX1 - 1.0:
        bx(f"pg{k}", (x, -16.5, -20.0), (min(x + 5.0, BX1), -13.5, 0.0), m["up"] if k % 3 else m["dn"], g)
        x += 5.7
        k += 1
    # slider: ceramic body, write pole with coil, laser diode on top, waveguide, gold NFT
    bx("sl_body", (176.0, 11.5, -36.0), (236.0, 28.0, 0.0), m["aln"], g)
    bx("sl_abs", (176.0, 11.2, -36.0), (236.0, 11.5, 0.0), m["dark"], g)
    bx("pole", (200.0, 10.4, -12.0), (203.0, 24.0, 0.0), m["nickel"], g)
    bx("yoke", (190.0, 21.0, -12.0), (203.0, 24.0, 0.0), m["nickel"], g)
    bx("ret", (190.0, 11.0, -12.0), (193.0, 24.0, 0.0), m["nickel"], g)
    for j in range(4):
        y = 13.5 + 2.0 * j
        tube(f"coil{j}", (193.5, y, 0.3), (199.5, y, 0.3), 0.6, m["copper"], g)
    bx("reader", (184.0, 10.6, -8.0), (185.2, 16.0, 0.0), m["moly"], g)
    bx("laser", (205.0, 28.0, -10.0), (215.0, 33.0, 0.0), m["gan"], g)
    las_on = empty("las_on", g)
    bx("laser_facet", (205.5, 27.6, -6.0), (208.0, 28.2, 0.4), m["laser"], las_on)
    bx("wg", (205.8, 11.0, -3.0), (207.4, 28.0, 0.0), m["quartz_c"], g)
    bx("nft", (205.6, 10.0, -4.0), (207.6, 11.2, 0.2), m["gold"], g)
    disc("nft_disc", (206.6, 11.6, -1.5), 2.4, 0.6, m["gold"], g, 24)
    hot = empty("hot", g)
    bx("hot_spot", (NFT_X - 1.4, MY[2] - 0.2, -3.0), (NFT_X + 1.6, MY[4] + 0.2, 0.4), m["hot"], hot)
    # written trail: grains to the left of the head re-lit in their new direction one by one
    trail = []
    for j, gx in enumerate([gx for gx in grains if 188.0 < gx < NFT_X - 1.0][::-1]):
        tg = empty(f"tr{j}", g)
        bx(f"tr{j}_b", (gx - 0.8, MY[2], -3.0), (gx + 0.8, MY[3], 0.3), m["up_g"] if j % 3 else m["dn_g"], tg)
        trail.append(tg)
    return {"las_on": las_on, "hot": hot, "trail": trail, "grains": grains}


def shelf(m, root):
    """A JBOD shelf of drives behind the opened drive, LEDs blinking."""
    g = empty("shelf", root)
    x0, x1, z0, z1 = -125.0, 70.0, -290.0, -205.0
    bx("sh_case", (x0, -6.0, z0), (x1, 0.0, z1), m["steel"], g)
    leds = []
    for r in range(3):
        for c in range(8):
            xa = x0 + 6.0 + c * 23.5
            za = z0 + 6.0 + r * 26.0
            bx(f"dr{r}{c}", (xa, 0.0, za), (xa + 20.0, 14.0, za + 22.0), m["alu"], g)
            bx(f"drl{r}{c}", (xa + 1.0, 14.0, za + 1.0), (xa + 19.0, 14.5, za + 21.0), m["dark"], g)
            led = empty(f"led{r}{c}", g)
            bx(f"led{r}{c}_b", (xa + 16.0, 14.5, za + 18.0), (xa + 18.0, 15.2, za + 20.0), m["sig"], led)
            leds.append(led)
    return leds, ((x0 + x1) / 2, 15.0, (z0 + z1) / 2)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    piv = drive(m, root)
    b = bench(m, root)
    leds, sh = shelf(m, root)
    C.magnify(m, root, (HEAD[0], 4.4, HEAD[2]), (176.0, 20.0, -18.0), r=3.0)

    C.spin(piv, [0, 1, 3, 4], turns=1.5)
    # beat 0: head reads (beads from the preamp up the flex)
    run(root, "read", [(HEAD[0], 5.0, HEAD[2]), (28.0, 6.0, -30.0), (46.0, 7.0, -10.0), (0.0, 2.0, -6.0), (-10.0, 2.0, -10.0)],
        8, 0.8, m["e_blue"], 0, 0.1, 0.85, 40)
    # beat 1: pole field tries the stubborn grains cold, nothing flips
    field = [(201.5, 24.0, 0.6), (201.5, 12.0, 0.6), (201.5, 9.0, 0.6), (196.0, 7.0, 0.6), (191.5, 9.0, 0.6), (191.5, 22.0, 0.6)]
    run(root, "field1", field, 8, 0.6, m["e_blue"], [1, 2], 0.05, 0.8, 30)
    tag_x = empty("nope", root)
    bx("nope_b", (199.0, MY[3] + 0.2, -2.0), (204.0, MY[3] + 0.8, 0.5), m["warn"], tag_x)
    blink(tag_x, 1, [1, 3, 5, 7], n=8, on=0.6)
    # beat 2: laser on, photons down the waveguide, the spot glows, then grains flip one by one
    show(b["las_on"], [(F(2, 0.0), F(4, 0))])
    run(root, "photon", [(210.0, 30.5, 0.6), (206.6, 27.5, 0.6), (206.6, 12.0, 0.6), (206.6, 10.0, 0.6)],
        12, 0.55, m["laser"], [2, 3], 0.0, 0.85, 18)
    blink(b["hot"], 2, [0, 1, 2, 3, 4, 5, 6, 7], n=16, on=0.6)
    rise(root, "heat", (NFT_X, MY[4], -1.0), 6, 0.45, m["h_amber"], 2, 0.1, 0.85, 8.0, 24, (1.5, 1.0))
    n = len(b["trail"])
    for j, tg in enumerate(b["trail"]):
        show(tg, [(F(2, 0.15 + 0.7 * j / max(1, n)), F(5, 0))])
    # beat 4: shelf LEDs
    for k, led in enumerate(leds):
        blink(led, 4, [k % 8, (k * 3 + 1) % 8], n=8, on=0.5)

    bc = (199.0, 12.0, -20.0)
    C.tags(root, {
        0: [("platter, 7,200 rpm", (PC[0] - 40.0, 3.0, PC[2] + 30.0)), ("arm + head", (28.0, 6.0, -30.0)),
            ("bits: grains up or down", (PC[0] + 50.0, 3.0, PC[2])), ("head cut open on the bench", (206.0, 34.0, -18.0))],
        1: [("write pole", (201.5, 24.0, 0.0)), ("FePt grains: stubborn", (225.0, 7.0, 0.0)),
            ("field too weak cold", (196.0, 8.0, 0.0))],
        2: [("laser diode", (210.0, 33.0, -5.0)), ("waveguide", (206.6, 20.0, 0.0)),
            ("gold near-field antenna", (206.6, 10.5, 0.0)), ("~400 C spot, ~1 ns", (NFT_X, MY[4], 0.0))],
        3: [("HAMR: small grains", (230.0, MY[3], 0.0)), ("PMR: big grains", (230.0, -13.5, 0.0)),
            ("30-36 TB per drive", (PC[0], 4.0, PC[2]))],
        4: [("drive shelf for data lakes", sh), ("STX Mozaic HAMR", (PC[0], 4.0, PC[2])),
            ("WDC, Toshiba 6502.T", (sh[0] + 60.0, 15.0, sh[2]))],
    })
    C.done(SLUG, BEATS, [
        frame((-30.0, 0.0, -90.0), 210.0, 0.30, 0.75, pad=1.0),
        frame(bc, 80.0, 0.15, 0.20),
        [(0.0, frame((206.0, 18.0, -10.0), 50.0, 0.20, 0.20)), (0.7, frame((200.0, 12.0, -10.0), 70.0, 0.10, 0.25))],
        frame((199.0, 0.0, -15.0), 105.0, -0.15, 0.15),
        frame((-30.0, 0.0, -150.0), 300.0, 0.25, 0.80, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
