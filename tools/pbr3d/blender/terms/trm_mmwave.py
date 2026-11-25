"""TRM_MMWAVE: the Terms-tab overview for millimetre wave, on the telecom-radio kit.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_mmwave.py

Writes assets/term_TRM_MMWAVE.glb. Captions live in specs/terms/TRM_MMWAVE.json.

A street with small cells on the lamp poles. A mmWave antenna-in-package module sits on the
bench, cut open. The 24-100 GHz waves run short and fast, and a building in the way blocks them.

Beats:
  0 street    small cells on the lamp posts, dense along the block
  1 module    the antenna-in-package, cut open: patch array over the RFIC
  2 waves     short, wide-band waves from a small cell to a phone
  3 blocked   a wall or a building cuts the path; the phone needs a nearer cell
  4 dense     many small sites, each covering a few hundred metres (est.)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402
import kit_radio as K  # noqa: E402

SLUG = "TRM_MMWAVE"
BEATS = [
    ("Small cells on the lamp posts, many per block",
     "Millimetre-wave networks put small radios on street furniture: lamp posts, poles and building faces. Each is a "
     "box about the size of a shoebox, and a dense city needs many of them close together."),
    ("Inside the module: a patch array printed on a laminate",
     "The radio is an antenna-in-package: a grid of tiny patch antennas printed on a laminate, sitting right on top of "
     "the beamformer chip. Short traces keep the loss low at these frequencies."),
    ("24 to 100 GHz: a wide channel, but a short reach",
     "At these frequencies the wavelength is a few millimetres. Channels are wide, so peak throughput is high, but the "
     "waves die out over short distances. A single cell covers a short stretch of street."),
    ("A wall or a building blocks the path; a nearer cell takes over",
     "Walls, glass, foliage and even people block or absorb these waves. When the path is cut, the network hands the "
     "phone to a cell with a clear line, which is why the sites sit so close together."),
    ("Dense sites on every block: many small cells, not a few towers",
     "The model is many small sites, not a few tall towers. Each cell carries a few hundred metres of street (est.), so "
     "carriers need far more sites per square kilometre. Qualcomm (QCOM), Skyworks (SWKS), Qorvo (QRVO) and Verizon (VZ) "
     "are named in this build-out."),
]

POLES = [(-60.0, 0.0, 30.0), (-20.0, 0.0, 30.0), (20.0, 0.0, 30.0), (60.0, 0.0, 30.0)]
PHONE = (-12.0, 1.0, 90.0)
WALL = (-40.0, 0.0, 60.0)
BX = 200.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.radio_materials(m)
    K.ground(m, root, "street", -160.0, 160.0, -40.0, 160.0)
    K.building(m, root, "bldL", -160.0, -90.0, 90.0, 60.0, 130.0)
    K.building(m, root, "bldR", 90.0, 160.0, 75.0, 60.0, 130.0)
    cells = [K.small_cell(m, root, f"cell{i}", p, s=1.4) for i, p in enumerate(POLES)]
    K.phone(m, root, "phone", PHONE, s=1.6)
    # a wall between the cell and the phone, for beat 3
    K.building(m, root, "wall", -40.0, 0.0, 26.0, 45.0, 50.0, floors=2)

    mod = K.aip(m, root, "aip", (BX, 6.0, 0.0), s=2.6, n=4)
    show(mod["group"], [(F(1, 0.0), F(2, 0))])

    # beat 2: a wave from the cell to the phone, short and wide
    wave = K.beam_paths(cells[1]["front"], PHONE, n=3, spread=5.0)
    for k, r in enumerate(wave):
        run(root, f"w{k}", r, 3, 1.4, m["radio_mmw"], [2], 0.1, 0.8, 30)
    # beat 3: the cell behind the wall tries; the path breaks at the wall
    blocked = K.beam_paths(cells[2]["front"], PHONE, n=2, spread=4.0)
    for k, r in enumerate(blocked):
        run(root, f"blk{k}", r, 3, 1.4, m["radio_hot"], [3], 0.1, 0.5, 30)
    # beat 4: a clear cell takes over; the nearer cells fan out
    for i, c in enumerate(cells):
        for k, r in enumerate(K.beam_paths(c["front"], PHONE, n=1)):
            run(root, f"d{i}_{k}", r, 2, 1.4, m["radio_mmw"], [4], 0.05 * i, 0.6, 30)

    C.tags(root, {
        0: [("small cells on lamp posts", cells[0]["top"]), ("many per block", cells[3]["top"])],
        1: [("patch array on a laminate", mod["patches"][1]), ("RFIC underneath", mod["top"])],
        2: [("24-100 GHz: wide channel", PHONE), ("short reach", cells[1]["front"])],
        3: [("wall blocks the path", WALL), ("hand over to a nearer cell", cells[2]["front"])],
        4: [("dense sites, not a few towers", cells[0]["top"]), ("many small cells", cells[3]["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 30.0, 60.0), 300.0, 0.15, 0.18, pad=1.0),
        frame((BX, 8.0, 0.0), 110.0, 0.25, 0.22, pad=1.0),
        frame((0.0, 25.0, 60.0), 240.0, 0.10, 0.20, pad=1.0),
        frame((-20.0, 25.0, 60.0), 240.0, -0.10, 0.20, pad=1.0),
        frame((0.0, 30.0, 60.0), 320.0, 0.20, 0.25, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
