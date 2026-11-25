"""TRM_INFERENCE: the Terms-tab overview for inference, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_inference.py

The shared GPU board (term_common.base) carries the accelerator that serves requests. On the
bench, the GPU's compute die is drawn huge with its grid of matrix units, one HBM stack stands
beside it, and a token tape above shows the prompt going in and the answer coming out one token
at a time.

Beats:
  0 board     the trained model's weights sit in HBM beside the GPU
  1 prefill   the prompt arrives; every matrix unit lights at once
  2 decode    one token per pass; each pass streams all the weights out of HBM
  3 batching  many users' requests share each pass
  4 cost      every request costs compute; usage scales the bill
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, present  # noqa: E402

import term_common as C  # noqa: E402

SLUG = "TRM_INFERENCE"
BEATS = [
    ("Inference runs a model that is already trained",
     "Training is finished: the model is now a fixed file of weights, billions of numbers, loaded into the high-bandwidth "
     "memory (HBM) stacks beside the GPU. Inference means using those weights to answer requests: text, images, "
     "predictions. Nothing is learned while it runs."),
    ("The prompt goes in all at once: every matrix unit lights",
     "First the GPU reads the whole prompt in one pass, called prefill. All its tokens are multiplied through every layer "
     "in parallel, so the matrix units on the die are busy and the chip is compute-bound. This sets how long you wait "
     "for the first word."),
    ("Then one token per pass, and each pass reads every weight",
     "The answer comes out one token at a time (decode). To make each new token the GPU has to pull essentially all the "
     "weights out of HBM again, so speed is set by memory bandwidth more than raw compute. A 70B-parameter model at "
     "8 bits moves ~70 GB per token, which is why HBM capacity and bandwidth matter so much."),
    ("Batching many users into each pass keeps the chip busy",
     "Since every pass reads the weights anyway, servers stack dozens or hundreds of users' requests into one batch and "
     "share that read. Requests arrive over the network card, wait briefly to be grouped, and stream back token by token. "
     "Cost per token falls as batches and utilisation rise."),
    ("Every request costs compute, so inference grows with usage",
     "Training is a one-off bill; inference is paid on every query, forever, so its spend scales with users and with "
     "longer answers and reasoning. Cost and energy per token are the competitive metric, driving GPUs, custom "
     "accelerators, HBM and networking: NVIDIA (NVDA), AMD (AMD), Broadcom (AVGO), Marvell (MRVL)."),
]

# bench part: the giant die, one HBM stack, the token tape
DX0, DX1, DZ0 = 158.0, 218.0, -56.0
DY0, DY1 = 0.6, 6.0
NC, NR = 8, 6  # matrix-unit grid (x by z)
HX0, HX1, HZ0, HZ1 = 225.0, 246.0, -42.0, -14.0
TAPE_Y, TAPE_Z = 46.0, -28.0
TOK = 7.0  # token cube size
N_PROMPT, N_OUT = 5, 8


def mats(m):
    m["tok"] = D.mat("inf_tok", (0.85, 0.86, 0.90), rough=0.5)
    m["tok_in"] = D.mat("inf_tok_in", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["tok_out"] = D.mat("inf_tok_out", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.50), strength=2.5)
    m["mac"] = D.mat("inf_mac", (0.30, 0.32, 0.40), metal=0.5, rough=0.3)
    m["mac_on"] = D.mat("inf_mac_on", (0.40, 0.85, 1.0), emit=(0.40, 0.85, 1.0), strength=3.0)
    m["wt"] = D.mat("inf_wt", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)


def cube(name, c, s, mt, parent):
    x, y, z = c
    return bx(name, (x - s / 2, y - s / 2, z - s / 2), (x + s / 2, y + s / 2, z + s / 2), mt, parent)


def giant(m, root):
    g = empty("gdie", root)
    # substrate, interposer and the die with its grid of matrix units
    bx("g_sub", (DX0 - 4.0, 0.0, DZ0 - 4.0), (HX1 + 2.0, 0.6, 0.0), m["substrate"], g)
    bx("g_die", (DX0, DY0, DZ0), (DX1, DY1, 0.0), m["silicon"], g)
    cw, cd = (DX1 - DX0 - 6.0) / NC, (-DZ0 - 6.0) / NR
    cells, on_all, cols = [], empty("mac_all", root), [empty(f"mac_c{i}", root) for i in range(NC)]
    for i in range(NC):
        for j in range(NR):
            x0 = DX0 + 3.0 + i * cw + 0.6
            z0 = DZ0 + 3.0 + j * cd + 0.6
            lo, hi = (x0, DY1, z0), (x0 + cw - 1.2, DY1 + 1.0, z0 + cd - 1.2)
            cells.append(bx(f"g_mac{i}_{j}", lo, hi, m["mac"], g))
            bx(f"g_on{i}_{j}", (lo[0] + 0.3, DY1 + 1.0, lo[2] + 0.3), (hi[0] - 0.3, DY1 + 1.3, hi[2] - 0.3), m["mac_on"], on_all)
            bx(f"g_onc{i}_{j}", (lo[0] + 0.3, DY1 + 1.0, lo[2] + 0.3), (hi[0] - 0.3, DY1 + 1.3, hi[2] - 0.3), m["mac_on"], cols[i])
    D.join(cells, "g_macs")
    # cut face of the die: metal stack lines
    for k in range(5):
        y = DY0 + 1.0 + k * 0.9
        bx(f"g_bel{k}", (DX0 + 0.5, y, -0.4), (DX1 - 0.5, y + 0.3, 0.05), m["copper"], g)
    # HBM stack: base logic die + 8 DRAM layers, cut open at the front
    bx("h_base", (HX0, 0.6, HZ0), (HX1, 3.0, HZ1), m["silicon"], g)
    for n in range(8):
        y = 3.0 + n * 3.2
        bx(f"h_d{n}", (HX0, y + 0.5, HZ0), (HX1, y + 3.2, HZ1), m["hbm_dram"], g)
        bx(f"h_g{n}", (HX0 + 0.4, y, HZ0 + 0.4), (HX1 - 0.4, y + 0.5, HZ1 - 0.4), m["mold"], g)
    for k in range(4):  # through-silicon vias
        x = HX0 + 4.0 + k * 4.4
        D.tube(f"h_tsv{k}", (x, 0.6, HZ1 - 2.0), (x, 28.6, HZ1 - 2.0), 0.35, m["copper"], g, 8)
    # weight glow inside the stack (shown when weights stream out)
    wglow = empty("h_wglow", root)
    for n in range(8):
        y = 3.0 + n * 3.2
        bx(f"h_wg{n}", (HX0 + 1.0, y + 1.2, HZ1 - 0.2), (HX1 - 1.0, y + 2.4, HZ1 + 0.05), m["wt"], wglow)
    show(wglow, [])
    return {"on_all": on_all, "cols": cols, "wglow": wglow,
            "die": ((DX0 + DX1) / 2, DY1 + 1.0, DZ0 / 2), "hbm": ((HX0 + HX1) / 2, 28.6, (HZ0 + HZ1) / 2),
            "face": ((DX0 + DX1) / 2, DY0 + 2.0, 0.0)}


def tape(m, root, z, name, n_in, n_out, beats_out, u0, u1, prompt_beats, lift=0.0):
    """A row of token cubes: n_in prompt tokens, then n_out answer tokens appearing one by one."""
    y = TAPE_Y + lift
    x0 = DX0 + 2.0
    pg = empty(f"{name}_p", root)
    for k in range(n_in):
        cube(f"{name}_p{k}", (x0 + k * (TOK + 1.5), y, z), TOK, m["tok_in"], pg)
    present(pg, prompt_beats)
    outs = []
    for k in range(n_out):
        o = empty(f"{name}_o{k}", root)
        cube(f"{name}_o{k}c", (x0 + (n_in + k) * (TOK + 1.5), y, z), TOK, m["tok_out"], o)
        iv = []
        for b, end in beats_out:
            iv.append((F(b, u0 + (u1 - u0) * k / n_out), end))
        present(o, iv)
        outs.append(o)
    return outs


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, die_glow, glow_top = b["pk"], b["die_glow"], b["glow"]
    gp = giant(m, root)
    C.magnify(m, root, pk["top"], (DX0 - 2.0, 10.0, -28.0), r=6.0)

    # beat 0: weights resting in HBM (board HBM stacks marked)
    show(gp["wglow"], [(F(0, 0.3), F(1, 0)), (F(2, 0), F(3, 0))])

    # beat 1: prefill. prompt tokens drop into the die; every unit lights
    present(gp["on_all"], [(F(1, 0.35), F(2, 0)), (F(4, 0.2), F(5, 0))])
    for k in range(N_PROMPT):
        x = DX0 + 2.0 + k * (TOK + 1.5)
        run(root, f"pf{k}", [(x, TAPE_Y - 4.0, TAPE_Z), (x + 6.0, 20.0, TAPE_Z + 4.0), (x + 10.0, DY1 + 2.0, -20.0)],
            3, 1.4, m["tok_in"], 1, 0.1 + 0.03 * k, 0.4, 30)

    # beat 2: decode. weights stream HBM -> die each pass, a column of units sweeps, a token appears
    for k in range(4):
        y = 6.0 + k * 6.0
        run(root, f"wt{k}", [(HX0 - 1.0, y, -20.0), (DX1 + 2.0, max(y - 6.0, DY1 + 2.0), -24.0), ((DX0 + DX1) / 2, DY1 + 2.0, -24.0)],
            8, 1.1, m["wt"], [2, 3], 0.0, 0.9, 22)
    for i, col in enumerate(gp["cols"]):
        blink(col, 2, [i], n=NC, on=0.9, u0=0.05, u1=0.95)
    tape(m, root, TAPE_Z, "tp", N_PROMPT, N_OUT, [(2, F(3, 0))], 0.1, 0.95, [(F(1, 0), F(3, 0))])
    for k in range(N_OUT):  # each new token rises out of the die to the tape
        x = DX0 + 2.0 + (N_PROMPT + k) * (TOK + 1.5)
        run(root, f"up{k}", [((DX0 + DX1) / 2, DY1 + 2.0, -20.0), (min(x, 240.0), TAPE_Y - 4.0, TAPE_Z)],
            1, 1.6, m["tok_out"], 2, 0.1 + 0.85 * k / N_OUT - 0.08, 1.0, 10)

    # beat 3: batching. several users' tapes grow together; requests come in over the board edge
    for r in range(4):
        z = TAPE_Z - 10.0 + r * 12.0
        tape(m, root, z, f"bt{r}", 3, 6, [(3, F(4, 0))], 0.15 + 0.02 * r, 0.95, [(F(3, 0), F(4, 0))], lift=r * 1.0)
    for side in range(3):
        z = -40.0 - side * 30.0
        run(root, f"req{side}", [(-300.0, 3.0, z), (-150.0, 3.0, z), (-50.0, 8.0, -20.0), (0.0, D.DIE_Y[1] + 2.0, -17.0)],
            6, 1.6, m["tok_in"], [3, 4], 0.0, 0.7, 50)
    present(gp["on_all"], [(F(1, 0.35), F(2, 0)), (F(3, 0.1), F(5, 0))])
    show(die_glow, [(F(1, 0.4), F(2, 0)), (F(3, 0.1), F(5, 0))])

    # beat 4: cost. heat and power on every pass
    rise(root, "die_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 6, 1.2, m["heat"], [3, 4], 0.1, 0.9, 30.0, 60, (14.0, 10.0))
    rise(root, "g_heat", ((DX0 + DX1) / 2, DY1 + 2.0, -28.0), 6, 1.2, m["heat"], 4, 0.1, 0.9, 30.0, 60, (20.0, 14.0))
    for side in (-1, 1):
        run(root, f"pwr{side}", D.front_path(side), 6, 1.2, m["amp"], 4, 0.1, 0.9, 70)
    for k, g_ in enumerate(glow_top):
        blink(g_, 4, [k, k + 4], n=8, on=0.6)

    tags = {
        0: [("GPU package", pk["top"]), ("weights loaded in HBM", pk["hbm"]),
            ("compute die, ~40x size", gp["die"]), ("one HBM stack", gp["hbm"])],
        1: [("prompt tokens", (DX0 + 20.0, TAPE_Y + 6.0, TAPE_Z)), ("all units busy: prefill", gp["die"]),
            ("compute-bound", gp["face"])],
        2: [("weights stream out each pass", gp["hbm"]), ("one token per pass", (DX0 + 70.0, TAPE_Y + 6.0, TAPE_Z)),
            ("bandwidth-bound: decode", gp["face"])],
        3: [("4 users, one batch", (DX0 + 40.0, TAPE_Y + 10.0, TAPE_Z + 26.0)), ("requests from the network", (-60.0, 8.0, -20.0)),
            ("shared weight read", gp["hbm"])],
        4: [("every query costs watts", pk["top"]), ("cost per token = the metric", gp["die"]),
            ("NVDA AMD AVGO MRVL", (DX0 + 40.0, TAPE_Y + 10.0, TAPE_Z))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((60.0, 10.0, -60.0), 330.0, 0.30, 0.55, pad=1.0),
        frame((200.0, 22.0, -28.0), 100.0, 0.25, 0.35),
        frame((205.0, 22.0, -26.0), 100.0, 0.10, 0.25),
        frame((100.0, 15.0, -50.0), 300.0, 0.25, 0.45),
        frame((40.0, 10.0, -80.0), 400.0, 0.20, 0.55, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
