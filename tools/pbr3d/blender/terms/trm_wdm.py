"""TRM_WDM: the Terms-tab overview for wavelength division multiplexing.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_wdm.py

Writes assets/term_TRM_WDM.glb. Captions live in specs/terms/TRM_WDM.json.

Beats:
  0 link       two switches joined by one fibre trunk
  1 one colour one channel: one wavelength carries one stream down the fibre
  2 mux        four lasers, four colours, combined by an arrayed-waveguide mux into one fibre
  3 demux      the far-end demux splits the colours to their receivers; dense WDM packs many more
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import bx, frame, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_WDM"
BEATS = [
    ("Two switches share one fibre, and the fibre carries many colours",
     "Wavelength division multiplexing (WDM) sends several signals down one fibre at once, each on its own colour of "
     "laser light. Here two switches are linked by a single fibre pair. Nothing new is laid: the same glass carries more "
     "data because it carries more colours."),
    ("One colour is one channel",
     "Each wavelength is a separate channel with its own laser and receiver. A single colour on the fibre carries one "
     "stream of bits, and the fibre itself does not care how many colours share it."),
    ("A multiplexer combines the colours into one fibre",
     "At the sending end, an arrayed-waveguide multiplexer folds the separate colours into one beam. Coarse WDM uses a "
     "few widely spaced colours for short links such as FR4 transceivers. The multiplexer is the part that makes one "
     "fibre carry four streams."),
    ("A demultiplexer splits them again; dense WDM packs dozens",
     "At the far end, a demultiplexer sends each colour to its own receiver. Dense WDM (DWDM) packs dozens of closely "
     "spaced channels for long-haul and metro networks, which multiplies the capacity of the fibre already in the "
     "ground. Ciena (CIEN), Coherent (COHR), Lumentum (LITE) and Nokia (NOK) sell the gear."),
]

TRUNK_Y = 6.0
LANE_Z = (-9.0, -3.0, 3.0, 9.0)
MUX_X, DEMUX_X = -50.0, 50.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    cols = ["ph_red", "ph_amber", "ph_green", "ph_cyan"]

    # beat 0: the switches at each end, in context
    ctx = empty("ctx", root)
    swa = K.switch_panel(m, ctx, "swA", -150.0, -120.0, 0.0, 18.0, -26.0, cols=4, rows=2)
    swb = K.switch_panel(m, ctx, "swB", 120.0, 150.0, 0.0, 18.0, -26.0, cols=4, rows=2)
    show(ctx, [(F(0, 0), F(1, 0))])

    # the link: lasers, mux, trunk, demux, receivers
    link = empty("link", root)
    lasers = []
    for k, zk in enumerate(LANE_Z):
        lasers.append(K.laser(m, link, f"las{k}", (-80.0, 2.5, zk), cols[k], size=2.5))
    mux = K.awg(m, link, "mux", (MUX_X, TRUNK_Y - 3.0, 0.0), 10.0, 26.0, 6.0, len(LANE_Z))
    demux = K.awg(m, link, "demux", (DEMUX_X, TRUNK_Y - 3.0, 0.0), 10.0, 26.0, 6.0, len(LANE_Z))
    lanes_in, lanes_out = [], []
    for k, zk in enumerate(LANE_Z):
        p_in = (-80.0 + 3.0, 4.0, zk)
        lanes_in.append([p_in, (-65.0, TRUNK_Y, zk * 0.4), (MUX_X - 5.0, TRUNK_Y, zk * 0.4), (MUX_X - 5.0, TRUNK_Y, 0.0)])
        p_out = (80.0 - 3.0, 4.0, zk)
        lanes_out.append([(DEMUX_X + 5.0, TRUNK_Y, 0.0), (DEMUX_X + 5.0, TRUNK_Y, zk * 0.4), (65.0, TRUNK_Y, zk * 0.4), p_out])
        K.wg(m, link, f"wgin{k}", lanes_in[k], 0.6)
        K.wg(m, link, f"wgout{k}", lanes_out[k], 0.6)
        bx(f"rx{k}", (76.0, 0.0, zk - 2.5), (84.0, 5.0, zk + 2.5), m["ph_dsp"], link)
    trunk = K.fiber(m, link, "trunk", [(MUX_X + 9.0, TRUNK_Y, 0.0), (0.0, TRUNK_Y, 0.0), (DEMUX_X - 9.0, TRUNK_Y, 0.0)], r=0.7)
    show(link, [(F(1, 0), F(4, 0))])

    # beat 1: one colour down the trunk
    run(root, "one", [(MUX_X + 9.0, TRUNK_Y, 0.0), (DEMUX_X - 9.0, TRUNK_Y, 0.0)], 6, 2.0, m["ph_c4"], [1], 0.0, 0.6, 40)

    # beats 2-3: four colours through the mux, down the trunk, out through the demux
    for k in range(len(LANE_Z)):
        path = lanes_in[k] + [(0.0, TRUNK_Y, 0.0)] + lanes_out[k]
        run(root, f"ch{k}", path, 4, 2.0, m[cols[k]], [2, 3], 0.0, 0.7, 45)

    tags = {
        0: [("switch: 800G ports", (-135.0, 22.0, -26.0)), ("one fibre trunk", (0.0, 9.0, 0.0)),
            ("switch: 800G ports", (135.0, 22.0, -26.0))],
        1: [("one colour = one channel", (0.0, 9.0, 0.0)), ("fibre carries the bits", (MUX_X, 10.0, 0.0)),
            ("separate laser per colour", (-80.0, 10.0, 0.0))],
        2: [("lasers: one colour each", (-80.0, 10.0, -9.0)), ("mux folds colours in", mux["in"]),
            ("one fibre out: 4 streams", (0.0, 12.0, 0.0))],
        3: [("demux splits them", demux["in"]), ("receivers per colour", (80.0, 10.0, 0.0)),
            ("DWDM: dozens of colours", (0.0, 18.0, -30.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 6.0, -10.0), 320.0, 0.30, 0.35, pad=1.0),
        frame((0.0, 6.0, 0.0), 170.0, 0.20, 0.30),
        frame((-40.0, 6.0, 0.0), 170.0, 0.10, 0.35),
        frame((20.0, 6.0, 0.0), 230.0, -0.10, 0.35),
    ], root)


if __name__ == "__main__":
    build()
