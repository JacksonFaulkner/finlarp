"""Final check of the weight-edit candidates on the TEST set. Run once; not used for selection.

Candidates were chosen on VALIDATION before this script was written:
  A  best single shard edit by validation delta: shard 13 (last-layer LayerNorm gain x0.3)
  B  the four top per-shard edits applied together: shards 13, 6, 11, 7

Each candidate starts from a freshly loaded base model. Output: validation and test macro-F1.
"""

import json
from pathlib import Path

import numpy as np
from common import OUT, cached_logits, load_model, load_split, metrics, predict_logits
from wsp_harness import apply_edits

AG = OUT / "wsp" / "agents"
SHARDS = json.loads((OUT / "wsp" / "shards.json").read_text())

import sys

RUN = sys.argv[1] if len(sys.argv) > 1 else "haiku"
if RUN == "haiku":
    AG = OUT / "wsp" / "agents_haiku"
    CANDIDATES = {
        "A_shard13_LN_x0.3": [(13, AG / "shard_13/e5.txt")],
        "B_combined_13_6_11_7": [
            (13, AG / "shard_13/e5.txt"),
            (6, AG / "shard_6/e11.txt"),
            (11, AG / "shard_11/e4.txt"),
            (7, AG / "shard_7/e5.txt"),
        ],
    }
else:  # opus run, candidates fixed on validation before any test eval
    CANDIDATES = {
        "A_shard7_head_bias": [(7, AG / "shard_7/d1.txt")],
        "B_shard5_L8_value_x1.25": [(5, AG / "shard_5/e7.txt")],
        "C_combined_7_9_5_2": [
            (7, AG / "shard_7/d1.txt"),
            (9, AG / "shard_9/combo.txt"),
            (5, AG / "shard_5/e7.txt"),
            (2, AG / "shard_2/up3.txt"),
        ],
    }

test_texts, test_y = load_split("test")
val_texts, val_y = load_split("validation")
results = {}

for name, parts in CANDIDATES.items():
    tok, model = load_model()
    entries = []
    text = []
    for k, path in parts:
        entries += SHARDS[k]["entries"]
        text.append(path.read_text())
    merged = {"entries": entries}
    applied, skipped = apply_edits(model, merged, "\n".join(text))
    model.eval()
    val_f1 = metrics(val_y, predict_logits(model, tok, val_texts).argmax(1))["macro_f1"]
    test_m = metrics(test_y, predict_logits(model, tok, test_texts).argmax(1))
    results[name] = {
        "applied": applied,
        "skipped": skipped,
        "val_macro_f1": val_f1,
        "test_macro_f1": test_m["macro_f1"],
        "test_accuracy": test_m["accuracy"],
        "test_confusion": test_m["confusion"],
    }
    print(f"{name}: applied {applied}, skipped {len(skipped)}  "
          f"val {val_f1:.4f}  test macro-F1 {test_m['macro_f1']:.4f}  acc {test_m['accuracy']:.4f}", flush=True)
    del model

base_test_logits, _ = cached_logits("base", *load_model(), "test")
base_test = metrics(test_y, base_test_logits.argmax(1))
results["base"] = {"test_macro_f1": base_test["macro_f1"], "test_accuracy": base_test["accuracy"],
                   "test_confusion": base_test["confusion"]}
print(f"base: test macro-F1 {base_test['macro_f1']:.4f}  acc {base_test['accuracy']:.4f}")
for name in CANDIDATES:
    d = results[name]["test_macro_f1"] - base_test["macro_f1"]
    print(f"{name}: test delta vs base {d:+.4f}")

out = OUT / "results" / f"wsp_final_test_{RUN}.json"
out.write_text(json.dumps(results, indent=2))
print("wrote", out)
