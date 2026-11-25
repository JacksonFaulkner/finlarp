"""TRM_TRAINING: the Terms-tab overview for training, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_training.py

Training does not live on one board, so the scene is a slice of a training cluster: four racks
cut open at the front, each with eight trays of four GPUs and a top-of-rack switch, a spine switch
above tying the racks together, and a storage array feeding data. On the bench to the right, one
GPU's copy of the model is drawn as a stack of layers, with a loss curve behind it.

Beats:
  0 cluster   thousands of GPUs, wired into one machine
  1 data      batches of training text stream from storage to every GPU
  2 learn     forward pass up the layers, error back down, weights nudged
  3 sync      every step the GPUs average their gradients over the network
  4 months    repeat for weeks; the loss falls; heat and power the whole time
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink  # noqa: E402

import term_common as C  # noqa: E402

SLUG = "TRM_TRAINING"
BEATS = [
    ("Training builds a model on thousands of GPUs wired as one machine",
     "A large model is trained on a cluster: racks of GPU trays, each tray holding several accelerators, joined by "
     "switches into one fabric. Frontier runs use tens of thousands of GPUs at once, and the whole cluster works on a "
     "single model for weeks or months."),
    ("Batches of training data stream to every GPU",
     "The training set (trillions of tokens of text, code, images) sits on storage and is cut into batches. Each step, "
     "every GPU gets its own slice of the batch. Feeding them fast enough takes high-throughput storage and networking, "
     "or expensive GPUs sit idle."),
    ("Forward through the layers, error back down, weights nudged",
     "Each GPU runs its slice forward through the model's layers to make predictions, measures how wrong they were (the "
     "loss), then runs backward to work out how every weight should change: the gradient. That costs roughly three "
     "times the compute of the forward pass, which is why training needs so many FLOPs."),
    ("Every step, all GPUs average their gradients over the network",
     "Each GPU saw different data, so before updating, the cluster sums and averages gradients across every GPU (an "
     "all-reduce), through the top-of-rack and spine switches. This happens every step, thousands of times an hour, so "
     "the network's bandwidth and latency set how well the cluster scales."),
    ("Repeat for weeks until the loss stops falling",
     "Millions of steps later the loss curve flattens and the weights are frozen and shipped for inference. A frontier "
     "run can burn tens of megawatts for months. This workload drove the first wave of AI data-center spending: NVIDIA "
     "(NVDA), Microsoft (MSFT), Meta (META), Arista Networks (ANET)."),
]

NR, NT, NG = 4, 8, 4  # racks, trays per rack, GPUs per tray
RW, RD, RH = 70.0, 60.0, 170.0
RX = [-230.0 + i * 92.0 for i in range(NR)]  # rack left x
TRAY_H, TRAY_Y0 = 12.0, 12.0
TOR_Y = TRAY_Y0 + NT * (TRAY_H + 4.0) + 4.0
SPINE_Y = 230.0
ST = (-330.0, -270.0)  # storage x
BX0, BX1 = 170.0, 250.0  # bench
NL = 6
LY0, LH = 8.0, 14.0


def mats(m):
    m["rack"] = D.mat("trn_rack", (0.10, 0.10, 0.12), metal=0.6, rough=0.45)
    m["tray"] = D.mat("trn_tray", (0.35, 0.37, 0.42), metal=0.8, rough=0.35)
    m["gpu"] = D.mat("trn_gpu", (0.16, 0.17, 0.20), metal=0.5, rough=0.4)
    m["data"] = D.mat("trn_data", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=4.0)
    m["fwd"] = D.mat("trn_fwd", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.50), strength=3.0)
    m["bwd"] = D.mat("trn_bwd", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=3.0)
    m["grad"] = D.mat("trn_grad", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=5.0)
    m["led"] = D.mat("trn_led", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.50), strength=4.0)
    m["cable"] = D.mat("trn_cable", (0.15, 0.35, 0.75), rough=0.5)
    m["layer"] = D.mat("trn_layer", (0.30, 0.32, 0.40), metal=0.4, rough=0.35)
    m["panel"] = D.mat("trn_panel", (0.05, 0.06, 0.08), rough=0.4)


def tray_y(j):
    return TRAY_Y0 + j * (TRAY_H + 4.0)


def gpu_c(i, j, k):
    x0 = RX[i] + 6.0 + k * (RW - 12.0) / NG
    return (x0 + (RW - 12.0) / NG / 2, tray_y(j) + TRAY_H * 0.5, -8.0)


def cluster(m, root):
    g = empty("cluster", root)
    bx("floor", (-360.0, -4.0, -120.0), (270.0, 0.0, 20.0), m["dark"], g)
    for t in range(14):  # floor tiles
        x = -360.0 + t * 45.0
        bx(f"tile{t}", (x, 0.0, -120.0), (x + 0.6, 0.1, 20.0), m["grid"], g)
    leds, glows = [], [empty(f"gglow{k}", root) for k in range(4)]
    for i, x0 in enumerate(RX):
        x1 = x0 + RW
        # frame: back, sides, top (front open, cut at z = 0)
        bx(f"r{i}_back", (x0, 0.0, -RD), (x1, RH, -RD + 2.0), m["rack"], g)
        for sx in (x0, x1 - 3.0):
            bx(f"r{i}_side{sx:.0f}", (sx, 0.0, -RD), (sx + 3.0, RH, 0.0), m["rack"], g)
        bx(f"r{i}_top", (x0, RH - 3.0, -RD), (x1, RH, 0.0), m["rack"], g)
        for j in range(NT):
            y = tray_y(j)
            bx(f"r{i}t{j}", (x0 + 3.0, y, -RD + 4.0), (x1 - 3.0, y + 2.0, 0.0), m["tray"], g)
            for k in range(NG):
                cx, cy, _ = gpu_c(i, j, k)
                w = (RW - 12.0) / NG - 3.0
                bx(f"r{i}t{j}g{k}", (cx - w / 2, y + 2.0, -40.0), (cx + w / 2, y + 7.0, -4.0), m["gpu"], g)
                bx(f"r{i}t{j}h{k}", (cx - w / 2 + 1.0, y + 7.0, -38.0), (cx + w / 2 - 1.0, y + 10.0, -6.0), m["cold"], g)
                bx(f"r{i}t{j}w{k}", (cx - w / 2 + 1.5, y + 2.5, -4.0), (cx + w / 2 - 1.5, y + 6.5, -3.6), m["die_hot"], glows[(i + j + k) % 4])
            leds.append(bx(f"r{i}t{j}led", (x1 - 8.0, y + 2.0, -1.0), (x1 - 6.0, y + 4.0, 0.0), m["led"], g))
        # top-of-rack switch with ports
        bx(f"r{i}_tor", (x0 + 3.0, TOR_Y, -RD + 4.0), (x1 - 3.0, TOR_Y + 8.0, 0.0), m["dark"], g)
        for p in range(10):
            px = x0 + 7.0 + p * 5.6
            bx(f"r{i}_port{p}", (px, TOR_Y + 2.0, -0.5), (px + 3.6, TOR_Y + 5.0, 0.05), m["plastic"], g)
        # cables tray -> ToR along the right post
        D.polyline(f"r{i}_up", [(x1 - 10.0, tray_y(0) + 4.0, -2.0), (x1 - 10.0, TOR_Y, -2.0)], 0.8, m["cable"], g)
        # uplinks ToR -> spine
        cx = (x0 + x1) / 2
        D.polyline(f"r{i}_upl", [(cx, RH, -30.0), (cx, SPINE_Y - 10.0, -30.0), (-60.0 + (i - 1.5) * 20.0, SPINE_Y, -30.0)], 1.0, m["cable"], g)
    D.join(leds, "leds")
    # spine switch chassis
    bx("spine", (-110.0, SPINE_Y, -50.0), (0.0, SPINE_Y + 22.0, -10.0), m["dark"], g)
    for p in range(16):
        px = -106.0 + p * 6.6
        bx(f"sp_port{p}", (px, SPINE_Y + 6.0, -10.5), (px + 4.0, SPINE_Y + 10.0, -9.9), m["plastic"], g)
        bx(f"sp_led{p}", (px, SPINE_Y + 14.0, -10.3), (px + 1.5, SPINE_Y + 15.5, -9.9), m["led"], g)
    # storage array: drive sleds
    bx("st_body", (ST[0], 0.0, -RD), (ST[1], 120.0, 0.0), m["rack"], g)
    for j in range(10):
        y = 6.0 + j * 11.0
        for k in range(4):
            x = ST[0] + 4.0 + k * 13.5
            bx(f"st_d{j}_{k}", (x, y, -50.0), (x + 12.0, y + 9.0, 0.0), m["tray"], g)
            bx(f"st_l{j}_{k}", (x + 9.0, y + 6.0, 0.0), (x + 11.0, y + 8.0, 0.4), m["data"], g)
    D.polyline("st_link", [((ST[0] + ST[1]) / 2, 120.0, -30.0), ((ST[0] + ST[1]) / 2, SPINE_Y + 11.0, -30.0), (-110.0, SPINE_Y + 11.0, -30.0)], 1.0, m["cable"], g)
    for g_ in glows:
        show(g_, [])
    return glows


def bench(m, root):
    """One GPU's copy of the model: a stack of layers, glow groups for forward and backward."""
    g = empty("bench", root)
    bx("b_base", (BX0 - 4.0, 0.0, -50.0), (BX1 + 4.0, 4.0, 0.0), m["gpu"], g)
    fwd, bwd = [], []
    for k in range(NL):
        y = LY0 + k * LH
        bx(f"b_l{k}", (BX0, y, -40.0), (BX1, y + LH * 0.55, 0.0), m["layer"], g)
        # weight grid on the cut face
        for i in range(10):
            x = BX0 + 3.0 + i * (BX1 - BX0 - 6.0) / 10
            bx(f"b_w{k}_{i}", (x, y + 1.5, -0.3), (x + 4.5, y + LH * 0.55 - 1.5, 0.05), m["copper"], g)
        f_, b_ = empty(f"b_f{k}", root), empty(f"b_b{k}", root)
        bx(f"b_fg{k}", (BX0 + 1.0, y + LH * 0.55, -38.0), (BX1 - 1.0, y + LH * 0.55 + 0.6, -2.0), m["fwd"], f_)
        bx(f"b_bg{k}", (BX0 + 1.0, y + LH * 0.55, -38.0), (BX1 - 1.0, y + LH * 0.55 + 0.6, -2.0), m["bwd"], b_)
        for k2 in range(2):  # posts between layers
            x = BX0 + 6.0 + k2 * (BX1 - BX0 - 12.0)
            D.tube(f"b_post{k}_{k2}", (x, y, -36.0), (x, y + LH, -36.0), 0.6, m["alu"], g, 8)
        fwd.append(f_)
        bwd.append(b_)
    # loss curve panel behind the stack
    bx("loss_panel", (BX0 - 10.0, 100.0, -62.0), (BX1 + 10.0, 160.0, -60.0), m["panel"], g)
    bx("loss_ax", (BX0 - 4.0, 106.0, -59.8), (BX0 - 3.0, 154.0, -59.4), m["ink"], g)
    bx("loss_ay", (BX0 - 4.0, 106.0, -59.8), (BX1 + 4.0, 107.0, -59.4), m["ink"], g)
    curve = empty("loss", root)
    pts = C.wave_pts(BX0, BX1, 110.0, -59.0, 40.0, 1, n=40, fn=lambda u: 0.08 + 0.92 / (1 + 9 * u) + 0.03 * ((u * 37) % 1 - 0.5))
    D.polyline("loss_line", pts, 0.6, m["fwd"], curve)
    show(curve, [])
    return fwd, bwd, curve


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    glows = cluster(m, root)
    fwd, bwd, curve = bench(m, root)
    rack_c = [(x + RW / 2, RH / 2, -10.0) for x in RX]

    # beat 0: GPUs glow in turns, then stay lit from beat 1 on
    for k, g_ in enumerate(glows):
        show(g_, [(F(0, k / 8), F(0, k / 8 + 0.07)), (F(0, (k + 4) / 8), F(0, (k + 4) / 8 + 0.07)), (F(1, 0.0), F(5, 0))])

    # beat 1: data from storage via the spine down into every rack and tray
    sc = (ST[0] + ST[1]) / 2
    for i, x0 in enumerate(RX):
        cx, x1 = x0 + RW / 2, x0 + RW
        path = [(sc, 120.0, -28.0), (sc, SPINE_Y + 13.0, -28.0), (-55.0, SPINE_Y + 13.0, -28.0),
                (-60.0 + (i - 1.5) * 20.0, SPINE_Y - 2.0, -28.0), (cx, SPINE_Y - 12.0, -28.0), (cx, RH + 2.0, -28.0),
                (x1 - 10.0, TOR_Y + 4.0, 1.0), (x1 - 10.0, tray_y(0) + 4.0, 1.0)]
        run(root, f"data{i}", path, 6, 2.2, m["data"], 1, 0.0, 0.6, 70)
        for j in (1, 4, 7):  # into trays
            y = tray_y(j) + 5.0
            run(root, f"dt{i}_{j}", [(x1 - 10.0, y, 1.0), (x0 + 6.0, y, 1.0)], 3, 1.4, m["data"], 1, 0.45, 0.85, 30)

    # beat 2: forward up the stack, backward down (again in beat 4)
    for k in range(NL):
        iv_f, iv_b = [], []
        for bb in (2, 4):
            w = 1.0 / (2 * NL)
            iv_f.append((F(bb, k * w), F(bb, (k + 1) * w)))
            iv_b.append((F(bb, (2 * NL - 1 - k) * w), F(bb, (2 * NL - k) * w)))
        show(fwd[k], iv_f)
        show(bwd[k], iv_b)
    run(root, "fw_up", [((BX0 + BX1) / 2, LY0, 1.5), ((BX0 + BX1) / 2, LY0 + NL * LH, 1.5)], 1, 2.4, m["fwd"], 2, 0.0, 0.0, F(2, 0.5) - F(2, 0))
    run(root, "bw_dn", [((BX0 + BX1) / 2 + 10.0, LY0 + NL * LH, 1.5), ((BX0 + BX1) / 2 + 10.0, LY0, 1.5)], 1, 2.4, m["bwd"], 2, 0.5, 0.5, F(2, 0.5) - F(2, 0))
    C.magnify(m, root, (gpu_c(3, 7, 3)[0], tray_y(7) + 10.0, -20.0), (BX0 - 4.0, 50.0, -20.0), r=5.0)

    # beat 3: all-reduce. gradients go up from every rack to the spine and back down to the others
    for i, x0 in enumerate(RX):
        cx = x0 + RW / 2
        sx = -60.0 + (i - 1.5) * 20.0
        up = [(cx, TOR_Y + 4.0, 1.0), (cx, RH + 2.0, -28.0), (cx, SPINE_Y - 12.0, -28.0), (sx, SPINE_Y - 1.0, -28.0)]
        run(root, f"gu{i}", up, 5, 2.0, m["grad"], [3, 4], 0.0, 0.45, 40)
        run(root, f"gd{i}", list(reversed(up)), 5, 2.0, m["grad"], [3, 4], 0.45, 0.9, 40)
        for j in (0, 3, 6):
            y = tray_y(j) + 5.0
            run(root, f"gt{i}_{j}", [(x0 + 6.0, y, 1.0), (x0 + RW - 10.0, y, 1.0), (x0 + RW - 10.0, TOR_Y + 2.0, 1.0)],
                2, 1.4, m["grad"], 3, 0.0, 0.3, 30)

    # beat 4: loss curve, heat over every rack
    show(curve, [(F(4, 0.0), F(5, 0))])
    for i, c in enumerate(rack_c):
        rise(root, f"heat{i}", (c[0], RH + 1.0, -30.0), 5, 2.0, m["heat"], 4, 0.0, 0.9, 40.0, 60, (25.0, 20.0))

    tags = {
        0: [("rack: 8 trays x 4 GPUs", (RX[0] + RW / 2, RH, -10.0)), ("spine switch", (-55.0, SPINE_Y + 22.0, -30.0)),
            ("top-of-rack switch", (RX[2] + RW / 2, TOR_Y + 8.0, -5.0)), ("storage: the dataset", (sc, 120.0, -20.0))],
        1: [("token batches from storage", (sc, 120.0, -20.0)), ("a slice to every GPU", rack_c[1])],
        2: [("one GPU's model copy", ((BX0 + BX1) / 2, LY0 + NL * LH, -20.0)), ("forward: predict", (BX1, LY0 + 2 * LH, 0.0)),
            ("backward: gradients", (BX1, LY0 + 4 * LH, 0.0))],
        3: [("all-reduce every step", (-55.0, SPINE_Y + 22.0, -30.0)), ("gradients averaged", rack_c[2]),
            ("network sets scaling", (RX[3] + RW / 2, TOR_Y + 8.0, -5.0))],
        4: [("loss falls over weeks", (BX0 + 20.0, 150.0, -60.0)), ("tens of MW for months", rack_c[0]),
            ("NVDA MSFT META ANET", ((BX0 + BX1) / 2, LY0 + NL * LH, -20.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-60.0, 120.0, -30.0), 420.0, 0.25, 0.25, pad=1.0),
        frame((-130.0, 140.0, -30.0), 300.0, 0.15, 0.20),
        frame(((BX0 + BX1) / 2, 50.0, -20.0), 110.0, -0.20, 0.25),
        frame((-60.0, 150.0, -30.0), 320.0, 0.10, 0.25),
        frame((-20.0, 110.0, -30.0), 560.0, -0.10, 0.25, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
