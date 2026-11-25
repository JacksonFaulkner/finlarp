"""TRM_RETIMER: the Terms-tab overview for a retimer, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_retimer.py

Writes assets/term_TRM_RETIMER.glb and specs/terms/TRM_RETIMER.json.

The GPU board with a long PCIe/Ethernet trace from the package to a far connector. Without help
the signal fades along the copper; a retimer chip halfway along catches it, recovers the clock and
data, and sends a fresh copy. On the bench the retimer die is cut open (CDR, equalizer, TX), and two
eye diagrams compare the signal before and after.

Beats:
  0 loss      a long board trace: the signal fades with distance
  1 retimer   a chip in the middle catches the weak signal and resends it clean
  2 inside    receive, equalize, recover the clock, retransmit
  3 eyes      a nearly closed eye in, a wide-open eye out
  4 count     several per server, more each generation
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, show, empty  # noqa: E402
from power_vrm_detail import run, frame, bx, polyline, blink, mat, present  # noqa: E402

import term_common as C  # noqa: E402
import kit_link as K  # noqa: E402

SLUG = "TRM_RETIMER"
BEATS = [
    ("At 32-64 GT/s, a signal only survives a few inches of board copper",
     "Copper traces lose more signal the longer they are and the higher the frequency. A PCIe Gen5 lane "
     "loses about 36 dB end to end before the receiver gives up, and Gen6 has even less margin. In a big AI "
     "server the GPU, CPU, NIC and SSD sit too far apart, so the bits reach the end as mush."),
    ("A retimer sits halfway and sends a fresh copy",
     "A retimer is a small chip placed in the middle of the link. It fully receives the weak signal, decides "
     "each bit, and retransmits it at full strength with a clean clock. Each side now only has to cover half "
     "the distance, so the loss budget resets."),
    ("Inside: equalize, recover the clock, decide, retransmit",
     "Every lane has its own receiver with an equalizer that undoes the channel's blur, a clock-data recovery "
     "(CDR) loop that locks onto the incoming bits, and a transmitter. Because it takes part in link training "
     "like a real endpoint, it also resets jitter. A simple redriver only amplifies, noise and all."),
    ("A nearly closed eye in, a wide-open eye out",
     "Engineers judge a link by its eye diagram: many bits overlaid. A tall, wide opening means the receiver "
     "can tell ones from zeros easily. At the far end of a long trace the eye has almost collapsed; after the "
     "retimer it is wide open again."),
    ("More lanes and faster speeds mean more retimers per server",
     "AI servers use retimers between CPUs, GPUs, NICs and SSDs and on riser cards, often several per "
     "accelerator, and each speed step shortens reach further. That makes it a fast-growing attach product. "
     "Related: Astera Labs (ALAB), Broadcom (AVGO), Marvell (MRVL), Credo (CRDO)."),
]

Y = 0.6
LINK_Z = -120.0
P0 = (-40.0, Y, -50.0)  # trace leaves the package
RT = (60.0, 0.0, LINK_Z)  # retimer on the board
END_X = 142.0  # far connector
DIE = (156.0, 246.0, -40.0)  # cut-open die on the bench (x0, x1, z0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    m["eye_dim"] = mat("t_eye_dim", (1.0, 0.35, 0.2), emit=(1.0, 0.35, 0.2), strength=2.0)
    b = C.base(m, root)
    pk = b["pk"]

    # the long link: package -> down -> along to the far connector (diff pair, 2 lanes)
    for k, dz in enumerate((-4.0, 4.0)):
        path = [(P0[0], Y, P0[2]), (P0[0], Y, LINK_Z + dz), (END_X, Y, LINK_Z + dz)]
        for s in (-0.8, 0.8):
            polyline(f"tr{k}{s}", [(x, y, z + s) for x, y, z in path], 0.35, m["copper"], root)
    bx("conn", (END_X, 0.0, LINK_Z - 12.0), (END_X + 6.0, 8.0, LINK_Z + 12.0), m["lnk_pkg"], root)
    rtg = empty("rtg", root)
    rt = K.retimer(m, rtg, "rt", RT, w=22.0, d=22.0, h=3.0)
    present(rtg, [(F(1, 0.0), F(5, 0))])

    first = [(P0[0], 1.4, P0[2]), (P0[0], 1.4, LINK_Z - 4.0), (RT[0] - 12.0, 1.4, LINK_Z - 4.0)]
    second = [(RT[0] + 12.0, 1.4, LINK_Z - 4.0), (END_X, 1.4, LINK_Z - 4.0)]
    whole = first + second
    # beat 0: bright at the start, dim the rest of the way (fading signal)
    run(root, "b0h", first[:2], 6, 1.0, m["bit"], 0, 0.0, 0.5, 30)
    run(root, "b0l", [first[1], whole[-1]], 6, 0.7, m["dim_glow"], 0, 0.15, 0.85, 60)
    # beats 1, 4: weak arrives at the retimer, clean leaves it
    run(root, "b1a", first, 8, 0.7, m["dim_glow"], [1, 4], 0.0, 0.7, 55)
    run(root, "b1b", second, 8, 1.0, m["sig"], [1, 4], 0.2, 0.95, 35)

    # bench: the cut-open retimer die
    die, pts = K.lane_die(m, root, "die", DIE[0], DIE[1], DIE[2], lanes=8)
    show(die, [(F(2, 0.0), F(3, 0))])
    mg = empty("magg", root)
    C.magnify(m, mg, (RT[0], 3.0, RT[2]), pts["top"])
    present(mg, [(F(2, 0.0), F(3, 0))])
    run(root, "d_in", [pts["par"], pts["cdr"]], 6, 0.6, m["dim_glow"], 2, 0.0, 0.5, 40)
    run(root, "d_mid", [pts["cdr"], pts["ser"]], 6, 0.6, m["bit"], 2, 0.2, 0.7, 30)
    run(root, "d_out", [pts["ser"], pts["out"]], 6, 0.7, m["sig"], 2, 0.35, 0.9, 30)

    # beat 3: eye diagrams before / after, on the bench
    eyes = empty("eyes", root)
    ex, ey, ez = 180.0, 30.0, -60.0
    pnl = empty("pnl", eyes)
    bx("pnl_b", (ex - 26.0, ey - 14.0, ez - 1.5), (ex + 66.0, ey + 14.0, ez - 0.5), m["lnk_panel"], pnl)
    w, h = 36.0, 4.0  # closed eye: flat, tangled
    for j, o in enumerate((-1.2, 0.0, 1.0, 1.8)):
        top = [(ex - w / 2, ey + o, ez), (ex - w / 4, ey + h / 2 - o * 0.6, ez), (ex + w / 4, ey + h / 2 + o * 0.5, ez), (ex + w / 2, ey - o, ez)]
        bot = [(x, 2 * ey - y, z) for x, y, z in top]
        polyline(f"ce_t{j}", top, 0.2, m["eye_dim"], eyes)
        polyline(f"ce_b{j}", bot, 0.2, m["eye_dim"], eyes)
    K.eye(m, eyes, "oe", (ex + 40.0, ey, ez + 0.1), 36.0, 22.0)
    show(eyes, [(F(3, 0.0), F(4, 0))])

    # beat 4: more retimers on the board, blinking
    for i, c in enumerate(((100.0, 0.0, -170.0), (-120.0, 0.0, -170.0), (150.0, 0.0, -170.0))):
        g = empty(f"xr{i}", root)
        K.retimer(m, g, f"xr{i}r", c, w=16.0, d=16.0, h=2.6)
        present(g, [(F(4, 0.0), F(5, 0))])
        lg = empty(f"xl{i}", root)
        bx(f"xl{i}b", (c[0] - 3, 3.0, c[2] - 3), (c[0] + 3, 3.6, c[2] + 3), m["sig"], lg)
        blink(lg, 4, [i], n=3, on=0.8)

    C.tags(root, {
        0: [("GPU package", pk["top"]), ("long board trace", (40.0, 2.0, LINK_Z - 4.0)),
            ("signal fades", (110.0, 2.0, LINK_Z)), ("far connector", (END_X + 3.0, 9.0, LINK_Z))],
        1: [("retimer", rt["top"]), ("weak in", (0.0, 2.0, LINK_Z - 4.0)), ("fresh copy out", (110.0, 2.0, LINK_Z - 4.0))],
        2: [("RX + equalizer", pts["par"]), ("clock recovery (CDR)", pts["cdr"]), ("retransmit", pts["out"])],
        3: [("before: eye nearly shut", (ex, ey + 15.0, ez)), ("after: eye wide open", (ex + 40.0, ey + 15.0, ez))],
        4: [("retimer per link", (100.0, 3.0, -170.0)), ("riser + NIC links", (-120.0, 3.0, -170.0)),
            ("more each generation", rt["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((50.0, 0.0, -90.0), 260.0, 0.30, 0.70, pad=1.0),
        frame((60.0, 0.0, LINK_Z), 140.0, 0.25, 0.55),
        frame(((DIE[0] + DIE[1]) / 2, 10.0, DIE[2] / 2), 150.0, 0.22, 0.25),
        frame((ex + 20.0, ey, ez), 100.0, 0.05, 0.05),
        frame((20.0, 0.0, -140.0), 340.0, 0.30, 0.70, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
