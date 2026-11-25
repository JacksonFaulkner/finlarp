"""TRM_GDDR: the Terms-tab overview for GDDR graphics memory, on a graphics card.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gddr.py

Writes assets/term_TRM_GDDR.glb. Captions live in specs/terms/TRM_GDDR.json.

A graphics card with the GPU die in the middle and eight GDDR chips soldered around it, each on its
own short 32-bit channel. On the bench: a PAM3 eye (three voltage levels) and bandwidth bars for a
DDR5 channel, a GDDR7 card and an HBM3E GPU.

Beats:
  0 card     GPU die ringed by eight GDDR chips
  1 channels each chip has its own 32-bit channel; beads stream to the die
  2 per-pin  GDDR7 runs ~32 Gb/s per pin using three signal levels (PAM3)
  3 compare  bandwidth bars: DDR5 channel vs GDDR7 card vs HBM3E GPU
  4 market   who makes and buys it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import trm_ddr_sdram as S  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty  # noqa: E402
from power_vrm_detail import bx, frame, polyline, present, run, rise  # noqa: E402

SLUG = "TRM_GDDR"
BEATS = [
    ("GDDR chips ring the GPU on a graphics card",
     "Gaming and workstation GPUs, and some AI inference cards, use GDDR: DRAM chips soldered to the card in a ring "
     "around the GPU package. A typical card has 8 to 16 of them, each 2 to 3 GB, kept within a few centimetres of "
     "the die so the traces stay short."),
    ("Every chip gets its own narrow 32-bit channel",
     "Unlike a DIMM, where many chips share one bus, each GDDR chip talks to the GPU over its own 32-bit link. "
     "Twelve chips give a 384-bit bus. More chips means more bandwidth, which is why bus width is quoted on every "
     "card's spec sheet."),
    ("It wins on speed per pin, not on width",
     "GDDR7 signals at about 28-32 Gb/s per pin, four to five times DDR5. It gets there with PAM3 signalling: three "
     "voltage levels carry 1.5 bits per symbol instead of one. Each pin is pushed hard, which costs power and needs "
     "careful board design."),
    ("Bandwidth sits between DDR and HBM, at a much lower cost",
     "A DDR5 channel moves about 50 GB/s. A 384-bit GDDR7 card moves around 1.5 TB/s. An HBM3E GPU moves 8 TB/s "
     "using thousands of slow pins on stacked dies, but HBM needs costly 3D stacking and an interposer. GDDR uses "
     "plain packages on a normal board."),
    ("Three memory makers supply it, GPU vendors buy it",
     "Samsung, SK hynix and Micron make GDDR, and NVIDIA and AMD design their consumer GPUs around it. Cheaper "
     "inference cards such as NVIDIA's RTX Pro line keep GDDR to save HBM supply for training GPUs. Related: "
     "NVIDIA (NVDA), Micron (MU), Samsung (005930.KS), AMD (AMD)."),
]

GPU = (0.0, 0.0, -50.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    C.pcb(m, root, "card", -110.0, 180.0, -120.0, 20.0, mask="dark")
    # bracket and PCIe fingers
    bx("bracket", (-114.0, -10.0, -120.0), (-110.0, 30.0, 20.0), m["steel"], root)
    bx("pcie", (-60.0, -1.6, 20.0), (40.0, -0.4, 26.0), m["gold"], root)
    x, _, z = GPU
    bx("gpu_sub", (x - 28, 0.0, z - 28), (x + 28, 2.0, z + 28), m["substrate"], root)
    bx("gpu_die", (x - 15, 2.0, z - 15), (x + 15, 3.4, z + 15), m["die"], root)
    rise(root, "gpu_heat", (x, 4.0, z), 8, 0.9, m["h_amber"], [1, 2], h=24.0, spread=(10.0, 10.0))
    # VRM row
    for k in range(8):
        bx(f"ind{k}", (-95.0, 0.0, -105.0 + k * 13), (-85.0, 6.0, -95.0 + k * 13), m["ferrite"], root)
    chips, paths = [], []
    spots = [(-48, -50), (48, -50), (-48, -86), (48, -86), (-48, -14), (48, -14), (0, -98), (0, -2)]
    for k, (cx, cz) in enumerate(spots):
        c = (float(cx), 0.0, float(cz))
        top = C.chip(m, root, f"gddr{k}", c, 14.0, 12.0, h=1.4, pins=0, body="mold")
        chips.append(top)
        # 32-bit channel: a bundle of four traces to the die edge
        ex = max(-15.0, min(15.0, cx * 0.4))
        ez = z + max(-15.0, min(15.0, (cz - z) * 0.4))
        for j in range(4):
            o = (j - 1.5) * 1.2
            dz = o if abs(cx) > 0 else 0.0
            dx = o if cx == 0 else 0.0
            C.trace(m, root, f"ch{k}{j}", [(cx + dx, 0.0, cz + dz), (ex + dx, 0.0, ez + dz)], w=0.5)
        paths.append([(c[0], 2.0, c[2]), (ex, 2.5, ez)])
    for k, p in enumerate(paths):
        run(root, f"bd{k}", p, 10, 1.6, m["sig"], [1, 2], 0.0, 0.85, 25)

    # bench: PAM3 eye, three levels
    eye = empty("eye", root)
    bx("eye_plate", (68.0, 8.0, -21.0), (168.0, 38.0, -20.4), m["dark"], eye)
    for k, lv in enumerate((13.0, 23.0, 33.0)):
        bx(f"eye_lv{k}", (70.0, lv - 0.2, -20.3), (166.0, lv + 0.2, -20.2), m["dim_glow"], eye)
    import random
    rnd = random.Random(3)
    pts = [(70.0, 23.0, -20.0)]
    for i in range(1, 17):
        pts += [(70.0 + i * 6.0 - 1.5, pts[-1][1], -20.0), (70.0 + i * 6.0, rnd.choice((13.0, 23.0, 33.0)), -20.0)]
    polyline("eye_wave", pts, 0.35, m["sig"], eye)
    present(eye, [(F(2, 0), F(3, 0))])
    run(root, "eyebead", pts, 2, 1.0, m["bit"], 2, 0.05, 0.4, 70)

    # bench: bandwidth bars (log-ish heights)
    tops = [S.bar(m, root, "bw0", 90.0, -70.0, 14.0, 4.0, "steel", 3, 5),
            S.bar(m, root, "bw1", 118.0, -70.0, 14.0, 24.0, "copper", 3, 5),
            S.bar(m, root, "bw2", 146.0, -70.0, 14.0, 48.0, "gold", 3, 5)]

    C.tags(root, {
        0: [("GPU die", (x, 3.4, z)), ("GDDR chips soldered around it", chips[1]), ("VRM feeds the GPU", (-90.0, 6.0, -60.0))],
        1: [("one chip: own 32-bit channel", chips[0]), ("12 chips = 384-bit bus", chips[3]), ("short traces to the die", paths[5][1])],
        2: [("PAM3: three voltage levels", (70.0, 33.0, -20.0)), ("~32 Gb/s per pin (GDDR7)", (150.0, 38.0, -20.0)),
            ("1.5 bits per symbol", (118.0, 13.0, -20.0))],
        3: [("DDR5 channel ~50 GB/s", tops[0]), ("GDDR7 card ~1.5 TB/s", tops[1]), ("HBM3E GPU ~8 TB/s", tops[2])],
        4: [("Samsung, SK hynix, Micron make it", chips[4]), ("NVIDIA, AMD design around it", (x, 3.4, z))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 4.0, -50.0), 190.0, 0.30, 0.70),
        frame((0.0, 4.0, -50.0), 120.0, 0.20, 0.85),
        frame((118.0, 23.0, -20.0), 110.0, 0.05, 0.15),
        frame((118.0, 20.0, -70.0), 90.0, 0.25, 0.30),
        frame((20.0, 4.0, -50.0), 260.0, 0.30, 0.55),
    ], root)


if __name__ == "__main__":
    build()
