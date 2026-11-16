"""The WAFER overview, authored in Blender and exported for pbr3d, in the SAND template
(docs/diagram-pages.md): a 300 mm polished wafer through its optional layer, inspection, the FOUP
and the fab, with `label:<text>` empties for the tags the TUI pins on. The wafer's parts are in
wafer_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/wafer_overview.py

It writes:
  blender/wafer_overview.blend   open it in Blender to edit by hand
  assets/wafer_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/wafer/overview.rs).

Beats (match the WAFER section 1 flow: polished, optional epi or SOI, inspect, pack, fab):
  0 polished   the blank disc, mirror top face, 775 um on the datasheet (drawn 8x)
  1 epi        an epi layer grows on the top face from CVD gas (SOI is a zoom)
  2 inspect    a scan bar crosses the disc: TTV, SFQR, particles
  3 pack       the disc slides into a FOUP carrier
  4 fab        the wafer comes out on a chuck; litho, etch, deposit and CMP start from its flat face
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, disc, empty, key, label, mat, pivot, rel, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start, stream_of  # noqa: E402
import wafer_kit as K  # noqa: E402
from wafer_kit import END, R, THICK  # noqa: E402

BEATS = 5
FOUP_X = 480.0

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((0.0, 30.0, 0.0), 650.0, 0.60, 0.45),
    ((0.0, 20.0, 0.0), 650.0, 0.80, 0.35),
    ((0.0, 12.0, 0.0), 640.0, 0.30, 1.00),
    ((330.0, 80.0, 0.0), 1300.0, 0.50, 0.35),
    ((0.0, 40.0, -200.0), 1250.0, 0.50, 0.35),
]


def build():
    m, root = start("overview", BEATS, page="wafer")
    K.mats(m)
    m["slurry"] = mat("slurry", (0.95, 0.88, 0.55), emit=(0.95, 0.88, 0.55), strength=1.5)
    m["lamp"] = mat("lamp_on", (1.0, 0.6, 0.2), emit=(1.0, 0.6, 0.2), strength=3.0)
    m["jet"] = mat("gas_jet", (0.9, 0.95, 1.0), emit=(0.9, 0.95, 1.0), strength=3.0)

    holder = K.wafer(root, m, "wafer")
    # beat 0: the disc turns while polish slurry lands on the mirror face
    key(holder, F(0, 0), "rotation_euler", (0.0, 0.0, 0.0))
    key(holder, F(1, 0) - 1, "rotation_euler", (0.0, 1.6, 0.0), linear=True)
    stream_of(root, "slurry", 12, (0.0, 90.0, 0.0), [(0, 0, 0), (60.0, -80.0, 0.0)], 6, m["slurry"], 0, 0.05, 0.7, 40)
    label("polish slurry: silica and KOH", (60, 90, 0), root, [(F(0, 0.1), F(1, 0))])

    # beat 1: CVD gas comes down onto the top face and an epi layer grows (drawn 40x, so it shows)
    layer = empty("epi", holder)
    show(layer, [(F(1, 0), END)])
    grow = pivot("epi_grow", (0, THICK, 0), layer)
    disc("epi_disc", rel((0, THICK, 0), (0, THICK + 5, 0)), R - 1, 10, m["epi"], grow, verts=128)
    scale_keys(grow, [(0, (1, 1, OFF)), (F(1, 0.6), (1, 1, 1)), (END, (1, 1, 1))], until=F(1, 0))
    stream_of(root, "gas", 10, (0.0, 130.0, 0.0), [(0, 0, 0), (0.0, -110.0, 0.0)], 9, m["jet"], 1, 0.05, 0.6, 50)
    label("epi layer: a few um, drawn 40x", (40, 26, 0), root, [(F(1, 0.1), F(2, 0))])

    # the wafer slides into the FOUP in beat 3, then comes out onto a chuck in beat 4
    key(holder, F(3, 0), "location", P(0, 0, 0))
    key(holder, F(3, 0.9), "location", P(FOUP_X, 60, 0), linear=True)
    key(holder, F(4, 0), "location", P(FOUP_X, 60, 0))
    key(holder, F(4, 0.75), "location", P(0, 0, 0), linear=True)

    # beat 2: a scan bar crosses the disc; defect particles light up as it passes them
    scan = empty("scan", root)
    bar = box("scan_bar", (-2, 12, -R - 5), (2, 16, R + 5), m["scan"], scan)
    key(bar, F(2, 0), "location", P(-R - 20, 14, 0), linear=True)
    key(bar, F(3, 0) - 1, "location", P(R + 20, 14, 0), linear=True)
    show(scan, [(F(2, 0), F(3, 0))])
    for k, (u, v) in enumerate(((-0.62, 0.30), (0.12, -0.52), (0.40, 0.58), (-0.18, -0.10), (0.70, -0.30), (-0.48, -0.62))):
        x, z = u * R * 0.9, v * R * 0.9
        f = F(2, (x + R + 20) / (2 * R + 40))
        dot = ball(f"particle{k}", (x, THICK + 3.0, z), 3.5, m["bad"], root, 12)
        show(dot, [(f, f + 26)])
    label("scan bar: TTV, SFQR, particles", (-80, 40, 120), root, [(F(2, 0.1), F(3, 0))])

    # beat 3: the FOUP carrier
    foup = K.foup(root, m, FOUP_X)
    show(foup, [(F(3, 0), F(4, 0))])
    label("25 wafers at 10 mm pitch", (FOUP_X, 350, 0), root, [(F(3, 0.2), F(4, 0))])
    label("775 um +/- 25 um (drawn 8x)", (10, 34, -110), root, [(F(0, 0.2), F(1, 0))])
    label("300 mm prime wafer", (-R * 0.5, 40, 80), root, [(F(0, 0.1), F(1, 0))])

    # beat 4: four tools on the fab side; each lights in turn while a robot carries the wafer over them
    tools = empty("fab_tools", root)
    for k, x in enumerate((-240.0, -80.0, 80.0, 240.0)):
        box(f"tool{k}", (x - 60, 0, -350), (x + 60, 200, -170), m["tool"], tools)
    show(tools, [(F(4, 0), END)])
    for k, x in enumerate((-240.0, -80.0, 80.0, 240.0)):
        lamp = ball(f"lamp{k}", (x, 80.0, -150.0), 16.0, m["lamp"], tools, 12)
        on = F(4, 0.08 + 0.2 * k)
        show(lamp, [(on, on + F(0, 0.16))])
    xfer = empty("transfer", root)
    key(xfer, F(4, 0.15), "location", P(-300, 250, -260))
    key(xfer, F(4, 0.9), "location", P(300, 250, -260), linear=True)
    show(xfer, [(F(4, 0.15), F(4, 0.9))])
    disc("transfer_wafer", (0, 0, 0), R - 1, THICK, m["si"], xfer)
    label("robot carries the wafer tool to tool", (0, 380, -260), root, [(F(4, 0.15), F(4, 0.9))])
    label("litho, etch, deposit, CMP", (0, 230, -260), root, [(F(4, 0.2), END)])

    camera(root, POSES)
    return m, root


if __name__ == "__main__":
    build()
    finish("overview", page="wafer")
