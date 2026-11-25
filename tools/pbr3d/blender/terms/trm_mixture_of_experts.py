"""TRM_MIXTURE_OF_EXPERTS: the Terms-tab overview for mixture of experts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_mixture_of_experts.py

A router gate reads each token and sends it to a few of the expert blocks; the rest stay dark. The
eight experts sit on eight GPUs, so the chosen experts' traffic crosses the GPU fabric (arcs).

Beats:
  0 router   tokens reach the router gate
  1 pick     the router sends each token to two experts
  2 compute  only the chosen experts light and run; their outputs return to the router
  3 spread   each expert lives on its own GPU; token traffic crosses the fabric between them
  4 memory   every expert's weights stay resident, so memory grows while compute per token stays small
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, run, rise, present  # noqa: E402

import term_common as C  # noqa: E402
import kit_model as K  # noqa: E402

SLUG = "TRM_MIXTURE_OF_EXPERTS"
BEATS = [
    ("A router sends each token to a few experts, not all of them",
     "A mixture-of-experts (MoE) model replaces one big feed-forward block with many smaller expert networks and a router. "
     "For every token the router reads its state and picks a handful of experts to run. Only those do any work, "
     "so compute per token stays low even when the model holds far more weights than a dense model of the same speed."),
    ("The router scores every expert and picks the top few",
     "The router is a small learned layer that outputs one score per expert. The highest-scoring experts (typically two "
     "in a larger group) receive the token, and their outputs are mixed back together using the router's weights. "
     "The same router runs on every layer, so different tokens take different routes."),
    ("Only the chosen experts compute; their outputs return to the router",
     "The chosen experts light up and process the token, while the rest sit idle. Each chosen expert sends its result back "
     "to the router, which combines them into one vector for the next layer. Per token, the work done is a small slice of "
     "what the full parameter count would need."),
    ("Each expert lives on its own GPU, so tokens cross the network",
     "Experts are split across GPUs, and a token routed to a remote expert has to travel over the GPU-to-GPU link (NVLink "
     "in NVIDIA systems). That all-to-all traffic is the trade-off: more bandwidth between accelerators is what keeps "
     "the experts busy. Networking silicon from Broadcom (AVGO) sits on that path."),
    ("More experts means more memory held, even though compute stays small",
     "All experts' weights must sit in GPU memory for the router to reach them, so MoE models need large HBM pools even "
     "though each token uses only a few experts. That favours memory-rich GPUs, such as NVIDIA (NVDA) accelerators with "
     "high-bandwidth memory from Micron (MU)."),
]

ROW_X0, ROW_X1, N_EXP = -40.0, 140.0, 8
ZC = -85.0  # the GPU row and the experts that sit on it
ROUTER = (-96.0, 0.0, ZC)
TOKS = [(-172.0, 0.0, ZC), (-154.0, 0.0, ZC), (-136.0, 0.0, ZC)]
CHOSEN = (1, 5)
LATER = (2, 6)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    D.bx("plinth", (-185.0, -4.0, -110.0), (160.0, 0.0, -60.0), m["dark"], root)

    gpu, gtops = K.gpu_tray(m, root, "gpu", ROW_X0, ROW_X1, ZC - 15.0, ZC + 15.0, N_EXP)
    ex, lids, etops = K.expert_row(m, root, "exp", ROW_X0, ROW_X1, ZC, N_EXP, y0=6.2, w=12.0, h=16.0, d=12.0)
    rt, rtop = K.router(m, root, "router", (ROUTER[0], 0.0, ZC), w=20.0, h=24.0, d=14.0)
    tok, ttops = K.token_row(m, root, "tok", [t[0] for t in TOKS], ZC, size=10.0)

    # beat 0: the token stream waits at the gate; the gate slot glows
    present(tok, [(F(0, 0.0), F(5, 0))])
    for k in range(3):
        run(root, f"in{k}", [(TOKS[k][0], 10.0, ZC), (ROUTER[0] - 12.0, 20.0, ZC), (ROUTER[0], rtop[1] + 2.0, ZC)],
            2, 1.2, m["mdl_token"], 0, 0.1 * k, 0.1 * k + 0.2, 36)

    # beat 1-2: the two chosen experts light; beads go out to them and the outputs come back
    for i in CHOSEN:
        show(lids[i], [(F(1, 0.2), F(3, 0)), (F(4, 0.8), F(5, 0))])
        src, dst = rtop, etops[i]
        mid = ((src[0] + dst[0]) / 2, 70.0, ZC)
        run(root, f"go{i}", [src, mid, dst], 3, 1.2, m["mdl_token"], [1, 2], 0.2, 0.5, 40)
        run(root, f"back{i}", [dst, mid, src], 2, 1.0, m["mdl_expert_on"], [2], 0.5, 0.8, 40)
        rise(root, f"heat{i}", (dst[0], dst[1] + 1.0, dst[2]), 4, 1.0, m["heat"], 2, 0.4, 0.9, 16.0, 40, (4.0, 3.0))

    # beat 3: the GPUs hold the experts, and the fabric carries traffic between them
    fab = K.fabric(m, root, "fab", gtops, h=30.0)
    show(fab, [(F(3, 0.1), F(4, 0))])
    for k, (a, b) in enumerate(((0, 5), (2, 7), (4, 1))):
        mid = ((gtops[a][0] + gtops[b][0]) / 2, 60.0, ZC)
        run(root, f"fab{k}", [gtops[a], mid, gtops[b]], 3, 1.1, m["mdl_link"], 3, 0.1 + 0.2 * k, 0.4 + 0.2 * k, 40)

    # beat 4: the experts stay resident in memory; only two compute, and the GPUs run warm
    for i in LATER:
        show(lids[i], [(F(4, 0.2), F(5, 0))])
    for j, t in enumerate(gtops):
        rise(root, f"hot{j}", (t[0], t[1] + 1.0, t[2]), 3, 1.1, m["heat"], 4, 0.0, 0.6, 22.0, 50, (4.0, 4.0))

    tags = {
        0: [("token stream in", ttops[0]), ("router gate", rtop), ("only the top few run", (ROUTER[0] + 30.0, 40.0, ZC))],
        1: [("router scores experts", rtop), ("two experts chosen", etops[CHOSEN[0]]), ("the rest stay dark", etops[3])],
        2: [("chosen experts compute", etops[CHOSEN[1]]), ("outputs return to router", rtop)],
        3: [("one expert per GPU", gtops[3]), ("token traffic on NVLink", (60.0, 60.0, ZC))],
        4: [("all weights held in HBM", gtops[6]), ("compute per token stays low", rtop)],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-10.0, 20.0, -70.0), 260.0, 0.30, 0.40, pad=1.0),
        frame((-30.0, 30.0, ZC), 170.0, 0.20, 0.40),
        frame((30.0, 25.0, ZC), 210.0, 0.25, 0.35),
        frame((40.0, 20.0, ZC), 230.0, 0.30, 0.35, pad=1.05),
        frame((20.0, 30.0, -70.0), 260.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
