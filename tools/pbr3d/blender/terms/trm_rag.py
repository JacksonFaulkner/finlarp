"""TRM_RAG: the Terms-tab overview for retrieval-augmented generation.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rag.py

Documents are split into chunks and indexed; a query finds its closest chunks; those chunks go
into the prompt, and the model answers from them.

Beats:
  0 chunk    documents are split into chunks
  1 index    each chunk is embedded and stored in the index
  2 query    the question's vector finds the closest chunks
  3 prompt   the matches are placed into the prompt
  4 answer   the model answers from the retrieved text
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

SLUG = "TRM_RAG"
BEATS = [
    ("Documents are cut into chunks the search can point at",
     "Retrieval-augmented generation (RAG) starts with the company's own documents: manuals, contracts, filings, tickets. "
     "The system splits each one into chunks, passages small enough to hand back to a model whole."),
    ("Each chunk is embedded as a vector and stored in an index",
     "An embedding model turns every chunk into a vector, a list of numbers that places it in meaning-space. The vectors "
     "go into a search index, so related passages end up near each other."),
    ("A question is embedded, and the closest chunks light up",
     "The user's question is embedded the same way. The index returns the chunks whose vectors sit closest to it, usually "
     "a handful. Retrieval quality often limits answer quality more than the model does."),
    ("The retrieved chunks are placed into the prompt",
     "The matched chunks are pasted into the model's prompt beside the question. The model now answers from current or "
     "private material it was never trained on, rather than from memory alone."),
    ("The answer cites the sources it was given",
     "The model writes an answer grounded in those passages, often with citations back to the source chunks. RAG is used "
     "for enterprise search, support and research assistants. Data-platform vendors such as Snowflake (SNOW), MongoDB "
     "(MDB), Elastic (ESTC) and Palantir (PLTR) sell into that stack."),
]

DOC_X = [-150.0, -120.0, -90.0]
INDEX_C = (-30.0, 0.0, -10.0)
PROMPT = ((60.0, 0.0, -60.0), (140.0, 36.0, -30.0))
LLM = ((60.0, 0.0, 20.0), (140.0, 30.0, 60.0))


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    D.bx("plinth", (-175.0, -4.0, -90.0), (170.0, 0.0, 80.0), m["dark"], root)

    docs = []
    for i, x in enumerate(DOC_X):
        g, top = K.doc_stack(m, root, f"doc{i}", (x, 0.0, 30.0), n=5, w=22.0, h=1.4, d=26.0)
        docs.append((g, top))
    chunks, cc = K.chunk_grid(m, root, "chunks", (-120.0, 0.0, -10.0), cols=3, rows=3, s=8.0, gap=4.0)
    idx, idx_hi, idx_tops = K.bar_chart(m, root, "idx", -50.0, -30.0, [6, 9, 4, 12, 7, 10, 5], step=12.0, w=8.0, hi=3)
    qbox = K.panel(m, root, "query", (-10.0, 0.0, 40.0), (14.0, 14.0, 60.0), mt=m["mdl_token"])
    pr = K.panel(m, root, "prompt", PROMPT[0], PROMPT[1], mt=m["mdl_cell"])
    llm_g, llm_tops = K.gpu_tray(m, root, "llm", LLM[0][0], LLM[1][0], LLM[0][2], LLM[1][2], n=4)

    # beat 0: documents split into chunks
    for g, _ in docs:
        present(g, [(F(0, 0.0), F(1, 0))])
    show(chunks, [(F(0, 0.5), F(5, 0))])
    # beat 1: each chunk is embedded; beads go into the index bars
    show(idx, [(F(1, 0.2), F(5, 0))])
    for k, c in enumerate(cc[:6]):
        run(root, f"emb{k}", [(c[0], 10.0, c[2]), (-50.0, 28.0, -30.0), idx_tops[k % len(idx_tops)]], 2, 1.0,
            m["mdl_token"], 1, 0.1 * k, 0.1 * k + 0.4, 36)
    # beat 2: the query beads hit the index; the closest chunks light
    show(idx_hi, [(F(2, 0.35), F(5, 0))])
    run(root, "q", [(4.0, 8.0, 50.0), (-10.0, 28.0, 0.0), idx_tops[3]], 3, 1.2, m["mdl_hit"], 2, 0.2, 0.6, 36)
    for k in (0, 4):
        run(root, f"hit{k}", [cc[k], (-60.0, 30.0, -20.0), idx_tops[3]], 2, 1.0, m["mdl_hit"], 2, 0.4, 0.7, 36)
    # beat 3: matched chunks are copied into the prompt
    show(pr, [(F(3, 0.0), F(5, 0))])
    for k in (0, 4, 6):
        run(root, f"pin{k}", [cc[k], (30.0, 30.0, -30.0), (PROMPT[0][0] + 40.0, 10.0, -45.0)], 2, 1.0,
            m["mdl_hit"], 3, 0.1 * k / 6, 0.3, 36)
    # beat 4: the model answers; output beads leave the GPU tray
    for j, t in enumerate(llm_tops):
        run(root, f"ans{j}", [(t[0], t[1] + 2.0, t[2]), (t[0] + 10.0, 40.0, t[2]), (PROMPT[0][0] + 40.0, 40.0, -10.0)], 2,
            1.1, m["mdl_token"], 4, 0.1 * j, 0.1 * j + 0.3, 40)

    tags = {
        0: [("documents", docs[1][1]), ("chunks: passages", cc[4])],
        1: [("embedding per chunk", idx_tops[3]), ("stored in the index", (-50.0, 40.0, -30.0))],
        2: [("question embedded", (4.0, 14.0, 50.0)), ("closest chunks light", idx_tops[3])],
        3: [("matches into the prompt", (PROMPT[0][0] + 40.0, 30.0, -45.0))],
        4: [("answer cites sources", (PROMPT[0][0] + 40.0, 40.0, -10.0)), ("SNOW MDB ESTC PLTR", llm_tops[1])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-90.0, 10.0, 0.0), 220.0, 0.25, 0.35),
        frame((-60.0, 12.0, -10.0), 240.0, 0.22, 0.35),
        frame((-30.0, 14.0, -10.0), 220.0, 0.30, 0.35),
        frame((60.0, 20.0, -20.0), 220.0, 0.30, 0.35),
        frame((60.0, 20.0, 20.0), 260.0, 0.25, 0.35, pad=1.05),
    ], root)


if __name__ == "__main__":
    build()
