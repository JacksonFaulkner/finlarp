"""TRM_TOKENS: the Terms-tab overview for tokens.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tokens.py

A document is cut into token cubes, the cubes fill a context window, each one is metered, GPUs
generate them one step at a time, and volume climbs into inference demand.

Beats:
  0 split     a document is cut into token cubes
  1 window    tokens fill the model's context window
  2 meter     every token is metered and billed
  3 generate  GPUs produce output tokens one at a time
  4 demand    token volume climbs, so inference hardware demand climbs with it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, run, present  # noqa: E402

import term_common as C  # noqa: E402
import kit_model as K  # noqa: E402

SLUG = "TRM_TOKENS"
BEATS = [
    ("A token is a chunk of text the model reads as one unit",
     "A language model reads and writes text as tokens: whole words, or pieces of words and punctuation. A page of "
     "ordinary prose becomes a long run of these units before the model does anything else. Counting in tokens is how "
     "model capacity, speed and price are measured."),
    ("Context length is counted in tokens, and the window fills up",
     "A model can only attend to a fixed number of tokens at once, its context window. Prompt, documents and the reply "
     "all share that budget, so a longer context means more memory and more compute for every new token generated."),
    ("Cloud APIs bill per token, both what goes in and what comes out",
     "Providers charge per million input and output tokens, so revenue tracks token volume directly. Output tokens "
     "usually cost more, since each one needs a full pass through the model. Some companies now disclose total tokens "
     "processed as a growth measure."),
    ("GPUs generate output one token at a time",
     "Each reply is produced one token per step. Every step reads the model's weights and the cached context from "
     "GPU memory, which is why inference speed depends on memory bandwidth as much as raw compute."),
    ("More tokens served means more inference hardware",
     "Rising token volume turns into demand for inference capacity: GPUs, the memory they need, and the networking that "
     "connects them. Microsoft (MSFT), Alphabet (GOOGL) and NVIDIA (NVDA) are the names most exposed to that volume."),
]

CTX_Z = -45.0
ROW_Z = -10.0
TXT = [-120.0 + 26.0 * i for i in range(7)]
GPU_Z = (40.0, 66.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    D.bx("plinth", (-170.0, -4.0, -70.0), (170.0, 0.0, 80.0), m["dark"], root)

    _, doc_top = K.doc_stack(m, root, "doc", (-150.0, 0.0, ROW_Z), n=7, w=44.0, h=1.4, d=30.0)
    toks, ttops = K.token_row(m, root, "toks", TXT, ROW_Z, size=10.0)
    _, cells = K.window_strip(m, root, "win", -120.0, 120.0, CTX_Z, h=4.0, cells=20)
    _, bill_hi, btops = K.bar_chart(m, root, "bill", -100.0, 30.0, [3, 4, 5, 4, 6, 9, 14], step=18.0, w=8.0, hi=6)
    _, gtops = K.gpu_tray(m, root, "gpu", -60.0, 120.0, GPU_Z[0], GPU_Z[1], n=4)
    _, otops = K.token_row(m, root, "out", [150.0, 165.0, 180.0], ROW_Z, size=8.0)
    _, gbar_hi, gbtops = K.bar_chart(m, root, "dem", 120.0, 40.0, [5, 8, 11, 15, 22], step=12.0, w=8.0, hi=4)

    # beat 0: the document is cut and the token cubes stand where its text was
    present(toks, [(F(0, 0.3), F(5, 0))])
    run(root, "cut", [doc_top, (-120.0, 40.0, ROW_Z), ttops[0]], 4, 1.0, m["mdl_token"], 0, 0.2, 0.6, 36)

    # beat 1: the context window fills cell by cell
    for i, c in enumerate(cells):
        show(c, [(F(1, 0.05 + 0.04 * i), F(5, 0))])
    run(root, "fill", [ttops[-1], (0.0, 30.0, CTX_Z), (120.0, 6.0, CTX_Z)], 3, 1.0, m["mdl_token"], 1, 0.3, 0.8, 40)

    # beat 2: the bill climbs as tokens are counted; the highlighted bar is the current one
    show(bill_hi, [(F(2, 0.4), F(5, 0))])
    for k, t in enumerate(btops[:3]):
        run(root, f"tick{k}", [ttops[k], (t[0], 25.0, t[2]), t], 2, 1.0, m["mdl_hit"], 2, 0.1 * k, 0.1 * k + 0.4, 36)

    # beat 3: GPUs emit output tokens that step over to the output row
    for j, t in enumerate(gtops):
        run(root, f"emit{j}", [(t[0], t[1] + 2.0, t[2]), (t[0] + 8.0, 30.0, t[2]), otops[j % 3]], 2, 1.2,
            m["mdl_token"], 3, 0.15 * j, 0.15 * j + 0.3, 40)
    run(root, "step", [otops[0], otops[1], otops[2]], 3, 1.2, m["mdl_hit"], 3, 0.5, 0.9, 36)

    # beat 4: demand climbs; the highlighted bar is the latest year
    show(gbar_hi, [(F(4, 0.3), F(5, 0))])

    tags = {
        0: [("text cut into tokens", ttops[2]), ("word pieces, not letters", (-120.0, 40.0, ROW_Z))],
        1: [("context window fills", (0.0, 24.0, CTX_Z)), ("prompt and reply share it", (100.0, 24.0, CTX_Z))],
        2: [("each token metered", btops[3]), ("priced per million", btops[6])],
        3: [("GPUs make one token per step", gtops[1]), ("output row grows", otops[1])],
        4: [("token volume = demand", gbtops[4]), ("MSFT GOOGL NVDA", (120.0, 30.0, 40.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-110.0, 10.0, -20.0), 220.0, 0.25, 0.35),
        frame((0.0, 12.0, -30.0), 260.0, 0.22, 0.30),
        frame((-40.0, 20.0, 20.0), 220.0, 0.30, 0.35),
        frame((30.0, 20.0, 50.0), 220.0, 0.30, 0.35),
        frame((60.0, 20.0, 20.0), 300.0, 0.25, 0.35, pad=1.05),
    ], root)


if __name__ == "__main__":
    build()
