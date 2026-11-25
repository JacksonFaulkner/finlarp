"""TRM_SERDES: the Terms-tab overview for SerDes, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_serdes.py

Writes assets/term_TRM_SERDES.glb. Captions live in specs/terms/TRM_SERDES.json (same beat count).

A row of SerDes macros sits on the GPU board beside the package: each lane takes the chip's wide
parallel bus and serializes it onto one fast differential pair. The big macro on the bench is cut
open: the RX columns with their clock-data recovery (CDR), the equalizer, the serializer tree and the
TX driver. Parallel bits go in, a serial stream comes out, and the lane speed sets the bandwidth.

Beats:
  0 board     the GPU with a row of SerDes macros along its edge
  1 inside    one macro cut open: RX columns, CDR, serializer, TX driver
  2 serialize parallel bits enter on the bus, one bit at a time leaves on the fast lane
  3 channel   the lossy board trace softens the edges; the receiver equalizer restores them
  4 speed     bandwidth per lane doubles each generation: 56G, 112G, 224G
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, show  # noqa: E402
from power_vrm_detail import run, frame  # noqa: E402

import term_common as C  # noqa: E402
import kit_link as K  # noqa: E402

SLUG = "TRM_SERDES"
BEATS = [
    ("A SerDes row runs along the edge of every AI chip",
     "A SerDes (serializer/deserializer) is the circuit at the edge of a chip that turns wide, slow parallel data into "
     "one very fast serial lane, and back again. A GPU, switch ASIC or NIC is ringed with dozens of them. Each lane "
     "carries a pair of wires, so a chip's total bandwidth is simply lane count times lane speed."),
    ("Inside one macro: receive columns, clock recovery, a serializer and a driver",
     "Each receive column samples its incoming bit with a clock recovered from the data itself (CDR). The equalizer "
     "rebuilds the edges that the channel blurred. A serializer tree multiplexes many slow bits into one stream, and "
     "the TX driver pushes that stream onto the copper. Getting this right at tens of gigabits is the hard part."),
    ("Parallel bits in, one serial stream out",
     "The chip hands over a wide bus of slow bits. The serializer folds them into one lane running many times faster, "
     "one bit after another. The receiver on the far end does the reverse, so the bus on each side never has to run "
     "at the lane rate."),
    ("The board trace blurs the edges; the equalizer sharpens them",
     "Copper loses signal with length and frequency, so a fast edge arrives rounded and smeared. The equalizer boosts the "
     "high frequencies in the receiver to undo that, which is why each generation needs more of it and more power per bit."),
    ("Lane speed sets the bandwidth: 56G, 112G, now 224G",
     "Per-lane rates have doubled from 56G to 112G and now 224G. Designing low-power SerDes at those speeds is hard, so it "
     "is a key differentiator and licensable IP. Related: Broadcom (AVGO), Marvell (MRVL), Credo (CRDO), Alphawave (AWE), "
     "Synopsys (SNPS), Cadence (CDNS)."),
]

LANE_X = (68.0, 140.0)  # the SerDes row on the board, beside the package
LANE_Z = -30.0
DIE_X0, DIE_X1, DIE_Z0 = 152.0, 246.0, -40.0  # the cut-open macro on the bench


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root)
    pk = b["pk"]
    ring, tops = K.lane_ring(m, root, "ring", LANE_X, LANE_Z, n=8)
    die, pts = K.lane_die(m, root, "die", DIE_X0, DIE_X1, DIE_Z0, lanes=8)
    C.magnify(m, root, (LANE_X[1] - 6.0, 2.6, LANE_Z), pts["top"])
    bars = K.speed_bars(m, root, "bars", (-150.0, 0.0, LANE_Z), rates=(56, 112, 224), x_gap=16.0, scale=0.18)

    show(die, [(F(1, 0.0), F(5, 0))])
    show(bars["group"], [(F(4, 0.0), F(5, 0))])

    # beat 2: parallel bits enter, serial bits leave
    par_path = [pts["par"], pts["cdr"], pts["ser"]]
    run(root, "pbit", par_path, 8, 0.7, m["bit"], 2, 0.1, 0.9, 50)
    ser_path = [pts["ser"], pts["out"], (DIE_X1 + 6.0, pts["out"][1], DIE_Z0 / 2)]
    run(root, "sbit", ser_path, 8, 0.55, m["sig"], 2, 0.2, 0.95, 40)
    # beat 3: the board trace out to the ring is lossy; the equalizer restores the signal
    board_path = [(LANE_X[1], 2.0, LANE_Z), (LANE_X[1] - 36.0, 2.0, LANE_Z), (LANE_X[0], 2.0, LANE_Z)]
    run(root, "lossy", board_path, 6, 0.7, m["dim_glow"], 3, 0.1, 0.9, 70)
    run(root, "eq", [(LANE_X[0] - 2.0, 2.0, LANE_Z), (LANE_X[0] - 40.0, 2.0, LANE_Z)], 6, 0.7, m["sig"], 3, 0.5, 0.95, 60)
    # beat 4: lanes light up on the bench, and the bar heights say the speed
    for k, t in enumerate(tops):
        run(root, f"lane{k}", [t, (t[0] + 4.0, t[1] + 6.0, t[2])], 1, 0.6, m["sig"], 4, 0.05 * k, 0.4, 30)

    C.tags(root, {
        0: [("SerDes row on the GPU board", (LANE_X[0] + 36.0, 4.0, LANE_Z)), ("GPU package", pk["top"]),
            ("lanes x speed = bandwidth", (LANE_X[0] + 36.0, 4.0, LANE_Z - 16.0))],
        1: [("RX column + CDR per lane", pts["cdr"]), ("equalizer", (DIE_X0 + 20.0, 6.0, DIE_Z0 / 2)),
            ("serializer tree", pts["ser"]), ("TX driver", pts["out"])],
        2: [("parallel bus in", pts["par"]), ("serial lane out", pts["out"]), ("one bit at a time", pts["ser"])],
        3: [("board trace: edges blur", (LANE_X[1] - 36.0, 4.0, LANE_Z)), ("equalizer sharpens", (LANE_X[0] - 20.0, 4.0, LANE_Z))],
        4: [("56G", (-142.0, 40.0, LANE_Z)), ("112G", (-126.0, 60.0, LANE_Z)), ("224G", (-110.0, 90.0, LANE_Z))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((DIE_X0 + DIE_X1) / 2, 10.0, DIE_Z0 / 2), 150.0, 0.22, 0.20),
        frame((DIE_X0 + 30.0, 12.0, DIE_Z0 / 2), 60.0, 0.10, 0.10),
        frame((-40.0, 4.0, -40.0), 200.0, 0.25, 0.55),
        frame((-40.0, 40.0, -40.0), 260.0, 0.20, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
