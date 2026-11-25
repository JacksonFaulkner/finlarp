"""TRM_ACTIVE_OPTICAL_CABLE: the Terms-tab overview for the active optical cable (AOC).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_active_optical_cable.py

Writes assets/term_TRM_ACTIVE_OPTICAL_CABLE.glb. Captions live in specs/terms/TRM_ACTIVE_OPTICAL_CABLE.json.

Beats:
  0 row      a GPU server and a leaf switch, joined by an AOC
  1 inside   one end cut open: edge fingers, driver/TIA chip, VCSEL + photodiode arrays, bonded fibre ribbon
  2 flow     electrical bits -> driver -> VCSEL light -> fibre -> photodiode -> TIA -> bits
  3 reach    copper DAC ~3 m, AEC ~7 m, AOC tens of metres
  4 trade    sealed unit vs separate transceivers; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, mat, show  # noqa: E402
from power_vrm_detail import bx, frame, polyline, rise, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_ACTIVE_OPTICAL_CABLE"
BEATS = [
    ("An AOC is a fibre cable with the optics built into both plugs",
     "An active optical cable plugs into a port like a copper cable, but inside each plug is a small transceiver that "
     "turns electrical signals into light and back. The fibre between the plugs is permanently attached. In AI rows "
     "they commonly join GPU servers to leaf switches a few racks away."),
    ("Each plug holds a laser driver, lasers, photodiodes and an amplifier",
     "Cut open, the plug has a small circuit board with gold edge fingers for the port, a driver chip that switches "
     "an array of tiny lasers (VCSELs for multimode fibre), a row of photodiodes for the return path, and a "
     "transimpedance amplifier (TIA) that turns their weak current into voltage. The fibre ribbon is glued to the "
     "optics at the factory, so there is no connector to clean or misalign."),
    ("Bits become light at one end and bits again at the other",
     "The host's SerDes drives electrical lanes into the plug. The driver flashes the lasers, the light crosses the "
     "fibre with almost no loss over tens of metres, and the far plug's photodiodes and TIA rebuild the electrical "
     "signal. Each direction has its own fibres, so an 800G AOC runs eight lanes each way."),
    ("Fibre reaches much farther than copper at today's speeds",
     "At 100-200 Gb/s per lane a passive copper cable (DAC) works only to about 2-3 m, and an active electrical cable "
     "(AEC) with retimers stretches that to about 7 m. An AOC reaches 30-100 m, enough to cross a row. It is also "
     "thinner and lighter, which matters when thousands of cables run through one rack."),
    ("Sealed and simple, but the whole cable is one part",
     "Because the vendor tunes the two ends and the fibre together, AOCs are cheap per link and plug-and-play. The "
     "tradeoff: a dead laser means replacing the whole cable, and the length is fixed. Longer or structured runs use "
     "separate transceivers and patch fibre instead. Coherent (COHR), Nvidia (NVDA), Amphenol (APH) and Credo (CRDO) "
     "sell into this market."),
]

PX0, PX1 = -40.0, 40.0  # the big cut-open plug, centred on the bench
PY = 0.0


def plug(m, parent, name, x0, x1, z0, z1, y=0.0, cut=True):
    """A QSFP/OSFP-style shell: metal case, pull tab, boot; open top when cut."""
    g = empty(name, parent)
    h = (z1 - z0) * 0.45
    bx(f"{name}_b", (x0, y, z0), (x1, y + 1.0, z1), m["steel"], g)
    bx(f"{name}_s0", (x0, y, z0), (x1, y + h, z0 + 1.0), m["steel"], g)
    bx(f"{name}_s1", (x0, y, z1 - 1.0), (x1, y + h, z1), m["steel"], g)
    bx(f"{name}_e", (x1 - 1.0, y, z0), (x1, y + h, z1), m["steel"], g)
    if not cut:
        bx(f"{name}_t", (x0, y + h - 1.0, z0), (x1, y + h, z1), m["steel"], g)
    return g, h


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    m["cable"] = mat("aoc_cable", (0.95, 0.55, 0.15), rough=0.5)  # aqua/orange jacket: orange for multimode
    m["vcsel"] = mat("aoc_vcsel", (0.9, 0.2, 0.9), emit=(0.85, 0.25, 1.0), strength=3.5)
    m["cu"] = mat("aoc_cu", (0.85, 0.50, 0.30), metal=0.9, rough=0.3)
    m["rack"] = mat("aoc_rack", (0.12, 0.13, 0.15), metal=0.4, rough=0.5)

    # ---- beat 0: the row --------------------------------------------------------------------
    row = empty("row", root)
    RZ = -80.0
    for k, (rx, kind) in enumerate(((-120.0, "gpu"), (-80.0, "gpu"), (80.0, "sw"))):
        bx(f"rk{k}", (rx - 16.0, 0.0, RZ - 20.0), (rx + 16.0, 90.0, RZ), m["rack"], row)
        for j in range(8):
            y = 6.0 + 10.0 * j
            mt = m["ph_front"] if kind == "gpu" else m["ph_case"]
            bx(f"rk{k}u{j}", (rx - 14.0, y, RZ), (rx + 14.0, y + 8.0, RZ + 0.6), mt, row)
            bx(f"rk{k}l{j}", (rx + 10.0, y + 3.0, RZ + 0.6), (rx + 12.0, y + 5.0, RZ + 0.9), m["ph_green"], row)
    K.switch_panel(m, row, "leaf", 66.0, 94.0, 60.0, 72.0, RZ + 0.8, cols=8, rows=2)
    cables = []
    for k, (sx, sy) in enumerate(((-110.0, 26.0), (-110.0, 46.0), (-70.0, 36.0), (-70.0, 56.0))):
        ex = 70.0 + 3.5 * k
        pts = [(sx, sy, RZ + 1.0), (sx, sy, RZ + 6.0), (sx, 96.0, RZ + 6.0), (ex, 96.0, RZ + 6.0), (ex, 64.0, RZ + 3.0)]
        polyline(f"aoc{k}", pts, 0.9, m["cable"], row)
        cables.append(pts)
    run(row, "rowb", cables[0], 6, 1.6, m["vcsel"], [0], 0.0, 0.6, 60)
    run(row, "rowb2", cables[3][::-1], 6, 1.6, m["ph_cyan"], [0], 0.1, 0.7, 60)
    show(row, [(F(0, 0), F(1, 0))])

    # ---- beats 1-2: the big cut-open plug -----------------------------------------------------
    big = empty("big", root)
    _, h = plug(m, big, "shell", PX0, PX1, -14.0, 14.0, PY)
    bx("pcb", (PX0 - 6.0, PY + 1.0, -11.0), (PX1 - 6.0, PY + 2.4, 11.0), m["ph_pcb"], big)
    for k in range(10):  # edge fingers poking out the port end
        z = -9.0 + 2.0 * k
        bx(f"fing{k}", (PX0 - 6.0, PY + 2.4, z - 0.6), (PX0 + 2.0, PY + 2.6, z + 0.6), m["ph_gold"], big)
    C.chip(m, big, "drv", (-8.0, PY + 2.4, -5.0), 10.0, 7.0, h=1.4, pins=6)
    C.chip(m, big, "tia", (-8.0, PY + 2.4, 5.0), 10.0, 7.0, h=1.4, pins=6)
    C.chip(m, big, "mcu", (-24.0, PY + 2.4, 6.0), 5.0, 5.0, h=1.0, pins=4)
    bx("optb", (6.0, PY + 2.4, -9.0), (16.0, PY + 4.0, 9.0), m["ceramic"], big)
    vcsels, pds = [], []
    for k in range(4):
        z = -7.5 + 1.6 * k
        v = bx(f"vc{k}", (13.0, PY + 4.0, z - 0.5), (14.5, PY + 4.8, z + 0.5), m["ph_si"], big)
        p = bx(f"pd{k}", (13.0, PY + 4.0, z + 9.0 - 0.5), (14.5, PY + 4.8, z + 9.0 + 0.5), m["ph_dsp"], big)
        vcsels.append((14.5, PY + 4.4, z))
        pds.append((14.5, PY + 4.4, z + 9.0))
    vglow = empty("vglow", big)
    for k, (x, y, z) in enumerate(vcsels):
        bx(f"vg{k}", (x - 0.4, y + 0.4, z - 0.35), (x + 0.2, y + 0.7, z + 0.35), m["vcsel"], vglow)
    show(vglow, [(F(2, 0), F(3, 0))])
    bx("lens", (17.0, PY + 3.0, -9.0), (20.0, PY + 7.0, 9.0), m["quartz_c"], big)  # lens/mirror block
    # fibre ribbon bonded and leaving through the boot
    for k in range(8):
        z = -7.5 + 1.6 * (k % 4) + (9.0 if k >= 4 else 0.0)
        K.fiber(m, big, f"rib{k}", [(20.0, PY + 5.0, z), (34.0, PY + 5.0, z * 0.3), (PX1 + 2.0, PY + 5.0, z * 0.12)], r=0.35)
    polyline("boot", [(PX1, PY + 5.0, 0.0), (PX1 + 14.0, PY + 5.0, 0.0)], 3.2, m["rubber"], big)
    polyline("jacket", [(PX1 + 14.0, PY + 5.0, 0.0), (90.0, PY + 5.0, 0.0), (130.0, PY + 5.0, -10.0)], 1.8, m["cable"], big)
    # traces from fingers to the chips
    for k in range(4):
        z = -9.0 + 2.0 * k
        C.trace(m, big, f"tr{k}", [(PX0 + 2.0, PY + 2.45, z), (-14.0, PY + 2.45, -5.0 + (k - 1.5) * 1.2)], w=0.35)
        C.trace(m, big, f"tr2{k}", [(-3.0, PY + 2.45, -5.0 + (k - 1.5) * 1.2), (13.0, PY + 2.45, vcsels[k][2])], w=0.3)
    show(big, [(F(1, 0), F(3, 0)), (F(4, 0), F(5, 0))])

    # beat 2: the far plug (closed) at the other end of the jacket
    far = empty("far", root)
    plug(m, far, "farp", 130.0, 170.0, -24.0, 4.0, PY, cut=False)
    show(far, [(F(2, 0), F(3, 0))])

    # beat 2 flows
    for k in range(4):
        z = -9.0 + 2.0 * k
        run(root, f"ein{k}", [(PX0 - 6.0, PY + 2.8, z), (-14.0, PY + 2.8, -5.0 + (k - 1.5) * 1.2)], 3, 0.5, m["h_amber"], [2], 0.0 + 0.02 * k, 0.6, 25)
        run(root, f"lt{k}", [vcsels[k], (20.0, PY + 5.0, vcsels[k][2]), (34.0, PY + 5.0, vcsels[k][2] * 0.3), (PX1 + 2.0, PY + 5.0, 0.0),
                             (90.0, PY + 5.0, 0.0), (130.0, PY + 5.0, -10.0)], 3, 0.9, m["vcsel"], [2], 0.15 + 0.02 * k, 0.7, 50)
        run(root, f"rt{k}", [(130.0, PY + 5.0, -10.0), (90.0, PY + 5.0, 0.0), (PX1 + 2.0, PY + 5.0, 0.0), (34.0, PY + 5.0, pds[k][2] * 0.3),
                             (20.0, PY + 5.0, pds[k][2]), pds[k]], 3, 0.9, m["ph_cyan"], [2], 0.1 + 0.02 * k, 0.65, 50)
    rise(root, "drvh", (-8.0, PY + 4.0, -5.0), 4, 0.35, m["h_amber"], [2], 0.1, 0.8, h=8.0, life=40)

    # ---- beat 3: reach bars -------------------------------------------------------------------
    reach = empty("reach", root)
    for k, (lab, length, mt, r) in enumerate((("dac", 9.0, "cu", 1.4), ("aec", 21.0, "rubber", 1.4), ("aoc", 150.0, "cable", 1.0))):
        z = -20.0 + 20.0 * k
        polyline(f"r_{lab}", [(-75.0, 30.0, z), (-75.0 + length, 30.0, z)], r, m[mt], reach)
        bx(f"r_{lab}_p0", (-80.0, 27.0, z - 3.0), (-75.0, 33.0, z + 3.0), m["steel"], reach)
        bx(f"r_{lab}_p1", (-75.0 + length, 27.0, z - 3.0), (-70.0 + length, 33.0, z + 3.0), m["steel"], reach)
    for j in range(6):  # metre ticks every 20 m (scale 1.5 units/m... schematic)
        bx(f"tick{j}", (-75.0 + 30.0 * j - 0.3, 26.0, -28.0), (-75.0 + 30.0 * j + 0.3, 34.0, -27.0), m["white"], reach)
    run(reach, "rb", [(-75.0, 30.0, 20.0), (75.0, 30.0, 20.0)], 6, 0.9, m["vcsel"], [3], 0.0, 0.7, 50)
    show(reach, [(F(3, 0), F(4, 0))])

    tags = {
        0: [("GPU servers", (-100.0, 92.0, RZ - 10.0)), ("leaf switch", (80.0, 74.0, RZ)),
            ("AOCs: plugs + fibre in one", (0.0, 98.0, RZ + 6.0))],
        1: [("gold edge fingers", (PX0 - 2.0, PY + 3.0, -9.0)), ("laser driver", (-8.0, PY + 4.5, -5.0)),
            ("TIA (receive amp)", (-8.0, PY + 4.5, 5.0)), ("VCSEL + photodiode rows", (14.0, PY + 5.0, 0.0)),
            ("fibre bonded at factory", (34.0, PY + 6.0, 0.0))],
        2: [("SerDes lanes in", (PX0 - 4.0, PY + 3.0, -6.0)), ("lasers flash the bits", (14.0, PY + 5.5, -6.0)),
            ("return light to PDs", (60.0, PY + 7.0, 0.0)), ("far plug", (150.0, 14.0, -10.0))],
        3: [("copper DAC ~2-3 m", (-70.0, 34.0, -20.0)), ("AEC ~7 m", (-55.0, 34.0, 0.0)),
            ("AOC 30-100 m", (40.0, 34.0, 20.0))],
        4: [("dead laser = new cable", (14.0, PY + 5.5, -6.0)), ("fixed length, plug-and-play", (60.0, PY + 7.0, 0.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-15.0, 50.0, RZ), 260.0, 0.15, 0.20),
        frame((-4.0, PY + 3.0, 0.0), 95.0, 0.35, 0.65),
        [(0.0, frame((0.0, PY + 3.0, 0.0), 100.0, 0.30, 0.55)), (0.5, frame((55.0, PY + 3.0, -5.0), 180.0, 0.05, 0.60))],
        frame((0.0, 30.0, 0.0), 170.0, 0.0, 0.45),
        frame((20.0, PY + 3.0, 0.0), 140.0, -0.30, 0.50),
    ], root)


if __name__ == "__main__":
    build()
