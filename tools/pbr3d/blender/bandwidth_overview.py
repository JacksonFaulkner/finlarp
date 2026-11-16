"""The BANDWIDTH overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md): a processor with its memory controller, DDR channels to DIMMs, data dots
on the lanes, an HBM stack beside the processor, a gauge of GB/s, and the memory wall bars. The
parts are in bandwidth_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bandwidth_overview.py

It writes:
  blender/bandwidth_overview.blend   open it in Blender to edit by hand
  assets/bandwidth_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/bandwidth/overview.rs).

Beats (match the BANDWIDTH overview page):
  0 pin        one data pin at 3200 MT/s; the gauge reads a sliver
  1 channel    the pin becomes a 64-pin ribbon; the gauge climbs to one channel, 25.6 GB/s
  2 channels   three more channels and DIMMs; four channels, 102.4 GB/s peak
  3 holes      pink markers where the lanes carry no data
  4 turnaround reads run one way, writes come back in orange
  5 HBM        a stack of dies on an interposer, 1024 short wires; the gauge reaches 819 GB/s
  6 wall       compute bars rise far above the DRAM bandwidth bar
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, empty, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import bandwidth_kit as K  # noqa: E402
from bandwidth_kit import OFF, PORT_X  # noqa: E402

BEATS = 7
CH_Y = [1050.0, 780.0, 510.0, 240.0]  # channel heights, top first
GAUGE_X, GAUGE_H = 2100.0, 1500.0  # the gauge is full height at HBM's 819 GB/s
HBM_X0, HBM_X1 = -2900.0, -2300.0

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((150.0, 950.0, 0.0), 7800.0, 0.10, 0.10),
    ((150.0, 950.0, 0.0), 7800.0, 0.08, 0.10),
    ((150.0, 700.0, 0.0), 8000.0, 0.10, 0.12),
    ((150.0, 700.0, 0.0), 8000.0, 0.08, 0.12),
    ((150.0, 700.0, 0.0), 8000.0, 0.06, 0.12),
    ((-2150.0, 150.0, -450.0), 3200.0, 0.30, 0.14),
    ((-700.0, 500.0, 0.0), 5000.0, 0.10, 0.12),
]

# gauge fraction of full height (1500 mm = 819 GB/s): 0.4, 25.6, 102.4, 819 GB/s
GAUGE = [
    (F(0, 0.2), 0.0005),
    (F(1, 0.2), 0.0313),
    (F(2, 0.2), 0.125),
    (F(5, 0.2), 1.0),
    (F(6, 0.1), 0.0005),
]


def build():
    m, root = start("overview", BEATS, page="bandwidth")
    K.mats(m)
    K.processor(root, m)
    label("memory controller", (PORT_X - 40.0, 1330.0, -300.0), root, beat(0) + beat(1) + beat(2) + beat(3) + beat(4))

    # channel 1 is one pin in beat 0, then a 64-pin ribbon; channels 2-4 arrive in beat 2
    y0 = CH_Y[0]
    pin = empty("ch0_pin", root)
    tube("ch0_pin_m", (PORT_X, y0, -40), (K.DIMM_X0, y0, -40), 16.0, m["copper"], pin, verts=10)
    show(pin, [(0, F(1, 0))])
    show(K.lanes(root, "ch0_lanes", PORT_X, K.DIMM_X0, y0, m, n=8), [(F(1, 0), F(6, 0))])
    show(K.dimm(root, "ch0", y0, m), [(0, F(6, 0))])
    K.dots(root, "ch0_pin_dots", (PORT_X + 40, y0, -40), (K.DIMM_X0 - 20, y0, -40), 3, m["read"], 0, 0.05, 0.7, 80, size=26)
    label("one pin: 3200 MT/s", (-300.0, y0 + 110.0, -40), root, beat(0))
    label("64 data pins: 25.6 GB/s", (-300.0, y0 + 190.0, -40), root, beat(1))
    for c in range(4):
        yc = CH_Y[c]
        if c:
            show(K.lanes(root, f"ch{c}_lanes", PORT_X, K.DIMM_X0, yc, m, n=8), [(F(2, 0), F(6, 0))])
            show(K.dimm(root, f"ch{c}", yc, m), [(F(2, 0), F(6, 0))])
        for b in (1, 2) if c == 0 else (2,):
            for i, y in enumerate(K.lane_ys(yc)):
                K.dots(root, f"ch{c}_b{b}_d{i}", (PORT_X + 40, y, -40), (K.DIMM_X0 - 20, y, -40), 2, m["read"], b, 0.05, 0.6, 90, size=8)
    label("four channels: 102.4 GB/s peak", (-300.0, 1420.0, -40), root, beat(2))

    # beat 3: pink markers where the lanes carry no data, between the dots
    gaps = empty("gaps", root)
    for c in range(4):
        for x in (-500.0, 100.0, 700.0):
            box(f"gap{c}_{int(x)}", (x - 60, CH_Y[c] - 40, -20), (x + 60, CH_Y[c] + 40, 30), m["gap"], gaps)
    show(gaps, [(F(3, 0), F(4, 0))])
    for c in range(4):
        for i, y in enumerate(K.lane_ys(CH_Y[c])[::2]):
            K.dots(root, f"ch{c}_b3_d{i}", (PORT_X + 40, y, -40), (K.DIMM_X0 - 20, y, -40), 2, m["read"], 3, 0.05, 0.6, 90, size=8)
    label("pink: a slot with no data", (-300.0, 1420.0, -40), root, beat(3))

    # beat 4: reads run in, writes come back in orange over the same lanes
    for c in range(4):
        for i, y in enumerate(K.lane_ys(CH_Y[c])[::2]):
            K.dots(root, f"ch{c}_b4_w{i}", (K.DIMM_X0 - 20, y, -40), (PORT_X + 40, y, -40), 2, m["write"], 4, 0.45, 0.9, 90, size=8)
            K.dots(root, f"ch{c}_b4_r{i}", (PORT_X + 40, y, -40), (K.DIMM_X0 - 20, y, -40), 2, m["read"], 4, 0.02, 0.4, 90, size=8)
    label("orange: writes return on the same lanes", (-300.0, 1420.0, -40), root, beat(4))

    # beat 5: HBM beside the processor, 1024 pins as a dense comb of short wires
    show(K.hbm(root, m, HBM_X0, HBM_X1, -200.0, -700.0, -350.0), [(F(5, 0), F(6, 0))])
    show(K.hbm_comb(root, "hbm_comb", HBM_X1, PORT_X - 600.0, -150.0, -500.0, 12, 26.0, m), [(F(5, 0), F(6, 0))])
    for i in range(3):
        y = -150.0 + 26.0 * (i * 4)
        K.dots(root, f"hbm_d{i}", (HBM_X1 + 20, y, -500.0), (PORT_X - 620.0, y, -500.0), 2, m["read"], 5, 0.1, 0.6, 60, size=8)
    label("HBM3: 1024 pins, 819 GB/s", (HBM_X0 + 300.0, 270.0, -380.0), root, beat(5))

    # the gauge, in GB/s of full height (819)
    K.bar(root, "gauge_track", GAUGE_X, -150.0, 300.0, 120.0, GAUGE_H, m["grey"], [])
    K.bar(root, "gauge", GAUGE_X, -150.0, 240.0, 150.0, GAUGE_H, m["cyan"], GAUGE)
    label("GB/s of peak", (GAUGE_X - 180.0, GAUGE_H + 80.0, -150.0), root, beat(0) + beat(1) + beat(2) + beat(3) + beat(4) + beat(5))

    # beat 6: the memory wall; bar heights are illustrative, not to scale
    wall = empty("wall_bars", root)
    show(wall, beat(6))
    K.bar(wall, "wall_compute", -900.0, -150.0, 300.0, 120.0, 1300.0, m["pink_bar"],
          [(0, OFF), (F(6, 0.2), OFF), (F(6, 0.7), 1.0)], y0=-200.0)
    K.bar(wall, "wall_dram", -300.0, -150.0, 300.0, 120.0, 1300.0, m["cyan"],
          [(0, OFF), (F(6, 0.3), OFF), (F(6, 0.8), 0.35)], y0=-200.0)
    label("compute: 3.0x every 2 years", (-900.0, 1200.0, -150.0), root, beat(6))
    label("DRAM bandwidth: 1.6x", (-300.0, 240.0, -150.0), root, beat(6))

    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="bandwidth")
