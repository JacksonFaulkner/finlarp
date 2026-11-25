"""TRM_LARGE_LANGUAGE_MODEL: the Terms-tab overview for large language models.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_large_language_model.py

An LLM is software, so the scene draws its working parts physically: a row of token blocks at the
bottom, each lifted into a column of numbers (its embedding), a tower of transformer layers above
(attention arcs linking each token to earlier ones, then a feed-forward block), a bar chart of
next-token probabilities on top, and the chosen token dropping back onto the end of the row. To the
right, an 8-GPU tray holds the model's weights sliced across its HBM.

Beats:
  0 tokens     text cut into tokens, each turned into a vector
  1 layers     dozens of transformer layers; attention looks back at earlier tokens
  2 next       the top scores every possible next token; one is picked and appended
  3 weights    billions of parameters, sliced across many GPUs' HBM
  4 scale      trained on trillions of tokens; products and companies
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, present  # noqa: E402

import term_common as C  # noqa: E402

SLUG = "TRM_LARGE_LANGUAGE_MODEL"
BEATS = [
    ("Text is cut into tokens, and each token becomes a vector",
     "A large language model (LLM) never sees letters. Text is split into tokens (whole words or word pieces, about "
     "3/4 of a word each on average) and every token is looked up in a table that turns it into a long list of numbers, "
     "its embedding, a few thousand numbers wide."),
    ("Dozens of transformer layers; attention links each token to earlier ones",
     "The vectors pass up through a stack of transformer layers, often 30 to 120 of them. In each, attention lets every "
     "token pull in information from the tokens before it (which word 'it' refers to, say), then a feed-forward block "
     "transforms each one. The layers' weights are the parameters."),
    ("The top scores every possible next token; one is picked and appended",
     "At the top, the model outputs a probability for every token in its vocabulary (often 100,000+). One is chosen, "
     "added to the end of the text, and the whole stack runs again for the next. That one-token-at-a-time loop is all "
     "a chat answer is."),
    ("Billions to trillions of parameters, sliced across many GPUs",
     "Models range from a few billion parameters to over a trillion. At 2 bytes each, a 400B model is ~800 GB, far more "
     "than one GPU's HBM, so the weights are split across 8 or more GPUs linked by fast interconnect, which pass "
     "activations between them every layer."),
    ("Trained on trillions of tokens, served to millions of users",
     "Learning those weights takes months of training on tens of thousands of GPUs; serving them takes large inference "
     "fleets. LLMs underpin chat assistants, coding tools and enterprise AI, and drive demand for GPUs, HBM and "
     "networking: Microsoft (MSFT), Alphabet (GOOGL), Meta (META), NVIDIA (NVDA)."),
]

NTOK = 6
TX = [-75.0 + i * 30.0 for i in range(NTOK)]  # token x
TZ = -10.0
TOK = 12.0
EMB_Y0, EMB_N = 12.0, 6
NL = 5
L_Y0, L_H = 50.0, 26.0
TOP_Y = L_Y0 + NL * L_H + 6.0
NEW_X = TX[-1] + 30.0
GX0, GX1 = 150.0, 270.0  # GPU tray


def mats(m):
    m["tok"] = D.mat("llm_tok", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["tok_new"] = D.mat("llm_new", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.50), strength=3.0)
    m["vec"] = D.mat("llm_vec", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=2.5)
    m["att"] = D.mat("llm_att", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)
    m["slab"] = D.mat("llm_slab", (0.28, 0.30, 0.38), metal=0.4, rough=0.35)
    m["ffn"] = D.mat("llm_ffn", (0.22, 0.36, 0.40), metal=0.4, rough=0.35)
    m["bar"] = D.mat("llm_bar", (0.55, 0.58, 0.66), metal=0.3, rough=0.4)
    m["node_on"] = D.mat("llm_node_on", (0.40, 0.85, 1.0), emit=(0.40, 0.85, 1.0), strength=3.0)


def cube(name, c, s, mt, parent):
    x, y, z = c
    return bx(name, (x - s / 2, y - s / 2, z - s / 2), (x + s / 2, y + s / 2, z + s / 2), mt, parent)


def tower(m, root):
    g = empty("tower", root)
    bx("plinth", (-100.0, -4.0, -50.0), (125.0, 0.0, 20.0), m["dark"], g)
    toks = empty("toks", root)
    for i, x in enumerate(TX):
        cube(f"tok{i}", (x, TOK / 2 + 0.5, TZ), TOK, m["tok"], toks)
    vecs = empty("vecs", root)
    for i, x in enumerate(TX):
        for n in range(EMB_N):
            h = 2.0 + 2.5 * ((i * 7 + n * 3) % 5) / 4
            y = TOK + 6.0 + n * 5.0
            bx(f"v{i}_{n}", (x - h / 2 - 1.0, y, TZ - 2.0), (x + h / 2 + 1.0, y + 3.5, TZ + 2.0), m["vec"], vecs)
    nodes_on, att = [], []
    for k in range(NL):
        y = L_Y0 + k * L_H
        bx(f"L{k}_att", (-95.0, y, -40.0), (95.0, y + 3.0, 10.0), m["slab"], g)
        bx(f"L{k}_ffn", (-95.0, y + 12.0, -40.0), (95.0, y + 18.0, 10.0), m["ffn"], g)
        for c in range(12):  # neuron grid on the ffn cut face
            x = -90.0 + c * 15.4
            bx(f"L{k}_n{c}", (x, y + 13.5, 9.8), (x + 9.0, y + 16.5, 10.2), m["copper"], g)
        for side in (-95.0, 91.0):
            bx(f"L{k}_p{side:.0f}", (side, y + 3.0, -38.0), (side + 4.0, y + 12.0, -34.0), m["alu"], g)
        on = empty(f"L{k}_on", root)
        for i, x in enumerate(TX):
            bx(f"L{k}_t{i}", (x - 4.0, y + 3.0, TZ - 4.0), (x + 4.0, y + 4.2, TZ + 4.0), m["node_on"], on)
            bx(f"L{k}_tf{i}", (x - 4.0, y + 18.0, TZ - 4.0), (x + 4.0, y + 19.2, TZ + 4.0), m["node_on"], on)
        nodes_on.append(on)
        a = empty(f"L{k}_arcs", root)
        last = TX[-1]
        for i, x in enumerate(TX[:-1]):
            D.polyline(f"L{k}_a{i}", D.arc((last, y + 4.2, TZ), (x, y + 4.2, TZ), 6.0 + 1.2 * (NTOK - i)), 0.35, m["att"], a)
        att.append(a)
    # vertical rails linking tokens up the stack
    for i, x in enumerate(TX):
        D.tube(f"rail{i}", (x, TOK + 40.0, TZ - 6.0), (x, TOP_Y, TZ - 6.0), 0.4, m["alu"], g, 8)
    # probability bars on top
    bars_hi = empty("bar_hi", root)
    heights = [4, 7, 3, 12, 5, 30, 6, 9, 3, 5, 8, 4]
    for c, h in enumerate(heights):
        x = -88.0 + c * 15.4
        bx(f"bar{c}", (x, TOP_Y, -16.0), (x + 9.0, TOP_Y + h, -4.0), m["bar"], g)
        if h == 30:
            bx("bar_win", (x - 0.4, TOP_Y, -4.0), (x + 9.4, TOP_Y + h + 0.4, -3.6), m["tok_new"], bars_hi)
            win = (x + 4.5, TOP_Y + h, -10.0)
    bx("bar_base", (-95.0, TOP_Y - 2.0, -40.0), (95.0, TOP_Y, 10.0), m["slab"], g)
    for o in nodes_on + att + [bars_hi]:
        show(o, [])
    return {"toks": toks, "vecs": vecs, "on": nodes_on, "att": att, "hi": bars_hi, "win": win}


def gpu_tray(m, root):
    g = empty("tray", root)
    bx("tr_pcb", (GX0, 0.0, -80.0), (GX1, 2.0, 0.0), m["mask"], g)
    bx("tr_fr4", (GX0, -3.0, -80.0), (GX1, 0.0, 0.0), m["fr4"], g)
    slices, pts = empty("w_slices", root), []
    for r in range(2):
        for c in range(4):
            x0 = GX0 + 6.0 + c * 28.5
            z0 = -74.0 + r * 38.0
            bx(f"gp{r}{c}_sub", (x0, 2.0, z0), (x0 + 24.0, 4.0, z0 + 32.0), m["substrate"], g)
            bx(f"gp{r}{c}_die", (x0 + 7.0, 4.0, z0 + 6.0), (x0 + 17.0, 7.0, z0 + 26.0), m["die"], g)
            for s in range(2):
                hx = x0 + 1.5 + s * 17.5
                for n in range(6):
                    bx(f"gp{r}{c}_h{s}{n}", (hx, 4.0 + n * 1.2, z0 + 8.0), (hx + 5.0, 5.0 + n * 1.2, z0 + 24.0), m["hbm_dram" if n % 2 else "hbm"], g)
                bx(f"gp{r}{c}_w{s}", (hx + 0.5, 11.5, z0 + 9.0), (hx + 4.5, 12.3, z0 + 23.0), m["att"], slices)
            pts.append((x0 + 12.0, 8.0, z0 + 16.0))
    # NVLink-style switch chips between the rows
    for c in range(2):
        bx(f"nvs{c}", (GX0 + 30.0 + c * 50.0, 2.0, -42.0), (GX0 + 46.0 + c * 50.0, 5.0, -36.0), m["dark"], g)
    show(slices, [])
    return slices, pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    t = tower(m, root)
    slices, gpts = gpu_tray(m, root)

    # beat 0: tokens, then each rises into its vector
    show(t["vecs"], [(F(0, 0.35), F(5, 0))])
    for i, x in enumerate(TX):
        run(root, f"emb{i}", [(x, TOK + 1.0, TZ + 7.0), (x, TOK + 6.0 + EMB_N * 5.0, TZ + 7.0)], 3, 1.2, m["vec"], 0, 0.1, 0.5, 30)

    # beat 1: layers light bottom to top; attention arcs fire in each
    for k in range(NL):
        w = 1.0 / NL
        show(t["att"][k], [(F(1, k * w), F(1, (k + 1) * w)), (F(2, k * w * 0.5), F(2, (k + 1) * w * 0.5)), (F(4, 0.0), F(5, 0))])
        show(t["on"][k], [(F(1, k * w), F(2, 0)), (F(2, 0.0), F(3, 0)), (F(4, 0.0), F(5, 0))])
    for i, x in enumerate(TX):
        run(root, f"up{i}", [(x, L_Y0, TZ + 6.0), (x, TOP_Y, TZ + 6.0)], 2, 1.4, m["node_on"], [1, 2], 0.0, 0.5, 90)

    # beat 2: the winning bar lights, the new token drops to the end of the row
    show(t["hi"], [(F(2, 0.45), F(3, 0)), (F(4, 0), F(5, 0))])
    run(root, "newtok", [t["win"], (NEW_X, TOP_Y + 10.0, TZ), (NEW_X, TOK / 2 + 0.5, TZ)], 1, 4.0, m["tok_new"], 2, 0.55, 0.55, 40)
    nt = empty("newtok_cube", root)
    cube("newtok_c", (NEW_X, TOK / 2 + 0.5, TZ), TOK, m["tok_new"], nt)
    present(nt, [(F(2, 0.55) + 40, F(5, 0))])

    # beat 3: weights slice from the tower onto the GPUs' HBM
    show(slices, [(F(3, 0.3), F(5, 0))])
    for k in range(NL):
        y = L_Y0 + k * L_H + 15.0
        for j in (k % 8, (k + 3) % 8):
            run(root, f"w{k}_{j}", [(95.0, y, -10.0), (130.0, y + 10.0, -20.0), (gpts[j][0], gpts[j][1] + 10.0, gpts[j][2])],
                3, 1.6, m["att"], 3, 0.05 + 0.1 * k, 0.6 + 0.07 * k, 40)
    run(root, "act", [gpts[0], gpts[1], gpts[2], gpts[3], gpts[7], gpts[6], gpts[5], gpts[4]], 4, 1.4, m["node_on"], [3, 4], 0.3, 0.9, 50)

    # beat 4: everything running; GPUs warm
    for j, p in enumerate(gpts):
        if j % 2 == 0:
            rise(root, f"heat{j}", (p[0], 12.0, p[2]), 3, 1.4, m["heat"], 4, 0.0, 0.8, 25.0, 50, (6.0, 6.0))

    tags = {
        0: [("tokens: word pieces", (TX[0], TOK, TZ)), ("embedding: a vector each", (TX[3], TOK + 30.0, TZ)),
            ("transformer stack", (90.0, L_Y0 + 2 * L_H, 0.0))],
        1: [("attention looks back", (TX[2], L_Y0 + 2 * L_H + 12.0, TZ)), ("feed-forward block", (60.0, L_Y0 + 3 * L_H + 16.0, 10.0)),
            ("30-120 layers in real models", (-90.0, L_Y0 + 4 * L_H + 10.0, 0.0))],
        2: [("probability per token", (-60.0, TOP_Y + 12.0, -10.0)), ("most likely one picked", t["win"]),
            ("appended, then run again", (NEW_X, TOK, TZ))],
        3: [("weights sliced across 8 GPUs", ((GX0 + GX1) / 2, 12.0, -40.0)), ("each slice in HBM", gpts[4]),
            ("billions to 1T+ params", (90.0, L_Y0 + 2 * L_H, 0.0))],
        4: [("chat, code, enterprise AI", (0.0, TOP_Y + 30.0, -10.0)), ("MSFT GOOGL META NVDA", ((GX0 + GX1) / 2, 12.0, -40.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 40.0, -10.0), 200.0, 0.25, 0.25),
        frame((0.0, 110.0, -10.0), 220.0, 0.30, 0.20),
        frame((10.0, 170.0, -10.0), 210.0, 0.20, 0.30),
        frame((140.0, 70.0, -30.0), 300.0, 0.35, 0.40),
        frame((80.0, 90.0, -30.0), 380.0, 0.25, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
