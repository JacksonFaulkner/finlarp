"""TRM_GPU_CLUSTER: the Terms-tab overview for a GPU cluster.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gpu_cluster.py

Writes assets/term_TRM_GPU_CLUSTER.glb and specs/terms/TRM_GPU_CLUSTER.json. Units cm; racks come
from trm_rack_density's kit.

A hall of four rows of NVL72-class racks (the nearest rack cut open), a spine-switch column at the
rows' left ends, overhead fibre trays from every rack to the spines, a storage row, and a yard of
transformers outside the hall wall.

Beats:
  0 rack     one rack: 72 GPUs on copper NVLink act as one big GPU
  1 network  every tray's NICs -> leaf switch -> fibre trays -> spine: the scale-out network
  2 hall     the whole hall pulses in step: an all-reduce every training step
  3 power    megawatts: transformers feed the hall; GPU count and MW go together
  4 failure  a rack fails; the job falls back to its last checkpoint on storage
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink  # noqa: E402
import trm_rack_density as K  # noqa: E402

SLUG = "TRM_GPU_CLUSTER"
BEATS = [
    ("The building block: a rack of GPUs wired as one",
     "A GPU cluster is many GPU servers networked so they can train or serve one model together. It starts with "
     "the rack: in an Nvidia NVL72, 72 GPUs share copper NVLink through nine switch trays, so any GPU can read any "
     "other's memory at about 1.8 TB/s. Inside that domain the rack behaves like one giant GPU."),
    ("Racks join through a second network: InfiniBand or Ethernet",
     "Each compute tray also has network cards (NICs), one per GPU, wired by fibre to leaf switches and from there "
     "to spine switches. This scale-out fabric is slower per GPU than NVLink but reaches every rack in the building. "
     "Big clusters use hundreds of thousands of optical links, which is why switch and optics makers ride AI build-outs."),
    ("Training steps sync the whole hall at once",
     "In training, each GPU works on its slice of the batch, then all of them swap gradients (an all-reduce) before "
     "the next step. The slowest link sets the pace, so the network is designed for every GPU to talk at full speed "
     "at the same moment. The largest training clusters now link 100,000 or more GPUs across several buildings."),
    ("Size is measured in megawatts as much as GPUs",
     "This hall's 32 racks would draw about 4 MW for the IT gear alone, plus cooling. A 100,000-GPU cluster needs "
     "well over 100 MW, as much as a small city, so builders quote clusters in megawatts and gigawatts and pick "
     "sites by how fast the grid can deliver power."),
    ("At this scale something is always failing",
     "With tens of thousands of GPUs, optics and cables, a part fails every few hours. A training job saves "
     "checkpoints to storage and, when a rack drops out, swaps in a spare and restarts from the last one, so "
     "reliability tooling matters as much as raw speed. Related: Nvidia (NVDA), Arista (ANET), Broadcom (AVGO), "
     "CoreWeave (CRWV), Meta (META)."),
]

NR, NC = 4, 7  # rows, racks per row
PX, PZ = 72.0, 280.0  # rack pitch along x, row pitch along z
SPX = -120.0  # spine column x
STOR_Z = PZ  # storage row in front of row 0
TY = 238.0  # fibre tray height
YARD_X = NC * PX + 160.0


def rack_x(c):
    return c * PX


def row_z(r):
    return -r * PZ


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    K.floor(m, root, -220, YARD_X - 40, -NR * PZ, STOR_Z + 140)
    bx("wall", (YARD_X - 50, -12, -NR * PZ), (YARD_X - 40, 300, STOR_Z + 140), m["concrete"], root)
    bx("yard", (YARD_X - 40, -14, -NR * PZ), (YARD_X + 360, -8, STOR_Z + 140), m["concrete"], root)

    leds, gpus = [], []
    cut_rack = None
    for r in range(NR):
        for c in range(NC):
            cut = r == 0 and c == NC - 1
            _, p, g = K.rack_ai(m, root, f"r{r}_{c}", (rack_x(c), row_z(r)), 1, cut=cut, liquid=True)
            leds.append(g["leds"])
            gpus.append(g["gpus"])
            if cut:
                cut_rack = p
        # spine/leaf network rack at each row's left end
        K.rack_ent(m, root, f"sp{r}", (SPX, row_z(r)), 1, "net")
        # overhead fibre tray along the row, with drops into every rack
        bx(f"tray{r}", (SPX - 20, TY, row_z(r) - 12), (rack_x(NC - 1) + 30, TY + 4, row_z(r) + 12), m["yellow"], root)
        for c in range(NC):
            D.polyline(f"drop{r}_{c}", [(rack_x(c), TY, row_z(r)), (rack_x(c), K.RH, row_z(r) - 10)], 1.0, m["yellow"], root)
    bx("tray_x", (SPX - 12, TY + 4, row_z(NR - 1) - 12), (SPX + 12, TY + 8, STOR_Z + 12), m["yellow"], root)
    # storage row
    for c in range(4):
        K.rack_ent(m, root, f"st{c}", (rack_x(c), STOR_Z), 1, "disk")
    bx("tray_s", (SPX - 20, TY, STOR_Z - 12), (rack_x(3) + 30, TY + 4, STOR_Z + 12), m["yellow"], root)

    # beat 0: NVLink on the cut rack
    xs = K.RW + 1.5
    x0 = rack_x(NC - 1)
    for k in range(8):
        yc = K.slot_y(5 + k if k < 4 else 23 + k)
        ys = K.slot_y(15 + k)
        run(root, f"nvl{k}", [(x0 + xs, yc + 2, 10), (x0 + xs + 3, (yc + ys) / 2, -20), (x0 + xs, ys + 2, -50)], 3, 1.0, m["nvl"], [0], 0.1 + 0.05 * k, 0.8, 30)
    show(gpus[NC - 1], [(F(0, 0.2), F(1, 0))])

    # beat 1-2: data beads rack -> tray -> spine, and spine -> other rows
    for r in range(NR):
        for c in range(0, NC, 2):
            path = [(rack_x(c), K.RH, row_z(r) - 10), (rack_x(c), TY + 6, row_z(r)), (SPX, TY + 6, row_z(r)), (SPX, K.RH, row_z(r))]
            run(root, f"d{r}_{c}", path, 3, 1.8, m["data"], [1] if r == 0 else [2], 0.05 + 0.04 * c, 0.75, 50)
        run(root, f"x{r}", [(SPX, TY + 10, row_z(r)), (SPX, TY + 10, row_z((r + 1) % NR))], 3, 1.8, m["data"], [2], 0.1, 0.8, 40)
        run(root, f"x1_{r}", [(SPX, TY + 10, row_z(r)), (SPX, TY + 10, row_z(r) + 60)], 2, 1.8, m["data"], [1], 0.2, 0.8, 30)
    # beat 2: every rack's LEDs pulse together (sync steps)
    for k, g in enumerate(leds):
        blink(g, 2, [0, 2, 4, 6], n=8, on=0.5)

    # beat 3: transformer yard feeding the hall
    for k in range(3):
        z = -60 - k * 300
        x = YARD_X + 120
        bx(f"xf{k}", (x - 60, -8, z - 50), (x + 60, 160, z + 50), m["mold"], root)
        for j in range(8):
            bx(f"xf{k}_fin{j}", (x + 60, 10, z - 45 + j * 12), (x + 72, 140, z - 41 + j * 12), m["frame2"], root)
        for j in range(3):
            D.tube(f"xf{k}_bush{j}", (x - 30 + j * 30, 160, z), (x - 30 + j * 30, 200, z), 5.0, m["white"], root, 12)
        path = [(x, 200, z), (x, 280, z), (YARD_X - 45, 280, z), (YARD_X - 45, 255, z), (SPX - 20, 255, z)]
        D.polyline(f"feed{k}", path[1:], 3.0, m["busway"], root)
        run(root, f"pw{k}", path, 12, 2.6, m["kw"], [3], 0.0, 0.8, 70)
    rise(root, "hall_heat", (rack_x(3), K.RH + 6, row_z(1)), 10, 3.0, m["heat"], 3, 0.1, 0.9, 50.0, 60, (220.0, 300.0))

    # beat 4: one rack fails (red), checkpoint flows from storage back to a spare
    fail = empty("fail", root)
    fr = (rack_x(3), row_z(1))
    bx("fail_f", (fr[0] - K.RW - 1, 0, fr[1] + K.RD + 1), (fr[0] + K.RW + 1, K.RH + 2, fr[1] + K.RD + 2.5), m["led_r"], fail)
    blink(fail, 4, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.5, u0=0.0, u1=0.5)
    spare = (rack_x(5), row_z(1))
    path = [(rack_x(1), K.RH, STOR_Z), (rack_x(1), TY + 6, STOR_Z), (SPX, TY + 10, STOR_Z), (SPX, TY + 10, row_z(1)), (spare[0], TY + 6, row_z(1)), (spare[0], K.RH, row_z(1))]
    run(root, "ckpt", path, 14, 2.2, m["cold_b"], [4], 0.45, 0.9, 50)

    cx = (rack_x(0) + rack_x(NC - 1)) / 2
    C.tags(root, {
        0: [("one NVL72 rack: 72 GPUs", cut_rack["top"]), ("NVLink switch trays", cut_rack["switch"]),
            ("compute trays: 4 GPUs each", cut_rack["compute"])],
        1: [("NIC per GPU -> fibre", (rack_x(2), K.RH, row_z(0))), ("overhead fibre tray", (rack_x(4), TY + 4, row_z(0))),
            ("leaf / spine switches", (SPX, K.RH + 4, row_z(0)))],
        2: [("all-reduce every step", (cx, TY + 8, row_z(1))), ("32 racks = 2,304 GPUs", (cx, K.RH, row_z(3))),
            ("storage row", (rack_x(1), K.RH, STOR_Z))],
        3: [("transformer yard", (YARD_X + 120, 200, -360)), ("~4 MW IT load here", (cx, K.RH + 40, row_z(1))),
            ("100k GPUs: >100 MW", (YARD_X + 120, 160, -660))],
        4: [("rack fails", (fr[0], K.RH + 4, fr[1])), ("checkpoint from storage", (rack_x(1), K.RH, STOR_Z)),
            ("spare takes over", (spare[0], K.RH + 4, spare[1])), ("NVDA ANET AVGO CRWV META", (cx, K.RH + 60, row_z(3)))],
    })
    C.done(SLUG, BEATS, [
        frame((x0, 100.0, 0.0), 180.0, 0.40, 0.12),
        frame((150.0, 170.0, 0.0), 420.0, 0.30, 0.35),
        frame((180.0, 60.0, -400.0), 1100.0, 0.55, 0.65, pad=1.0),
        frame((420.0, 60.0, -400.0), 1300.0, 1.05, 0.55, pad=1.0),
        frame((180.0, 100.0, -50.0), 800.0, 0.20, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
