"""POC: score the base sentiment model on a 300-tweet recent-tweet set.

Reference labels are two independent sources:
  - claude: hand-labelled blind (texts + tickers only), labels_claude_part{1,2}.txt, with a confidence tag.
  - pipeline: finlarp tweet_sentiment stance, bucketed (<= -1 neg, >= 1 pos, else neu).
Also reports model vs the two references and the agreement between the two references.
"""

import json
from collections import Counter

import numpy as np
from common import LABELS, OUT, load_model, metrics, predict_logits, save_json
from sklearn.metrics import cohen_kappa_score

POC = OUT / "poc"
MAP = {"neg": 0, "neu": 1, "pos": 2}

blind = [json.loads(line) for line in open(POC / "blind_300.jsonl")]
assert [b["idx"] for b in blind] == list(range(300)), "blind idx must be 0..299"

claude = {}
for part in ("part1", "part2"):
    for line in open(POC / f"labels_claude_{part}.txt"):
        idx, lab, conf = line.split()
        assert int(idx) not in claude, f"duplicate label for idx {idx}"
        claude[int(idx)] = (MAP[lab], conf)
assert sorted(claude) == list(range(300)), f"missing labels: {sorted(set(range(300)) - set(claude))}"

key = {(k["id"], k["ticker"]): k for k in map(json.loads, open(POC / "key_300.jsonl"))}
pipe = np.array([
    0 if key[(b["id"], b["ticker"])]["stance"] <= -1 else 2 if key[(b["id"], b["ticker"])]["stance"] >= 1 else 1
    for b in blind
])
y_claude = np.array([claude[i][0] for i in range(300)])
conf = np.array([claude[i][1] for i in range(300)])

print("reference label counts")
print("  claude  :", dict(Counter(LABELS[v] for v in y_claude)))
print("  pipeline:", dict(Counter(LABELS[v] for v in pipe)))
print(f"  claude confidence: {dict(Counter(conf))}")

agree = float((y_claude == pipe).mean())
kappa = float(cohen_kappa_score(y_claude, pipe))
print(f"\nclaude vs pipeline: agreement {agree:.3f}  kappa {kappa:.3f}")

tok, model = load_model()
logits = predict_logits(model, tok, [b["text"] for b in blind])
pred = logits.argmax(1)

m_claude = metrics(y_claude, pred)
m_pipe = metrics(pipe, pred)
m_hi = metrics(y_claude[conf == "high"], pred[conf == "high"])
print(f"\nmodel vs claude   : macro-F1 {m_claude['macro_f1']:.4f}  acc {m_claude['accuracy']:.4f}")
print(f"model vs pipeline : macro-F1 {m_pipe['macro_f1']:.4f}  acc {m_pipe['accuracy']:.4f}")
print(f"model vs claude (high-conf only, n={int((conf == 'high').sum())}): macro-F1 {m_hi['macro_f1']:.4f}")

print("\nmodel vs claude confusion (rows=claude neg/neu/pos, cols=model):")
for row in m_claude["confusion"]:
    print("  ", row)

# Dump rows where model disagrees with my label, for review.
disagree = [
    {"idx": i, "ticker": blind[i]["ticker"], "text": blind[i]["text"],
     "claude": LABELS[y_claude[i]], "conf": conf[i], "pipeline": LABELS[pipe[i]], "model": LABELS[pred[i]]}
    for i in range(300) if pred[i] != y_claude[i]
]
with open(POC / "model_vs_claude_disagreements.jsonl", "w") as f:
    for r in disagree:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\nwrote {len(disagree)} disagreements to {POC / 'model_vs_claude_disagreements.jsonl'}")

save_json("poc_recent300", {
    "n": 300,
    "reference_agreement_claude_vs_pipeline": agree,
    "reference_kappa": kappa,
    "model_vs_claude": m_claude,
    "model_vs_claude_high_conf": m_hi,
    "model_vs_pipeline": m_pipe,
})
