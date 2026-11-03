"""Step 3: error analysis on the TEST split, by tweet slice, plus example dumps.

Slices are regex/heuristic tags on the raw tweet text. Small slices are flagged (n < 100).
"""

import json
import re

import numpy as np
from common import LABELS, RESULTS, cached_logits, load_model, load_split, metrics, save_json

SLICES = {
    "negation": re.compile(r"\b(not|no|never|nothing|nobody|none|nor)\b|n't", re.I),
    "contrast": re.compile(r"\b(but|however|although|though|yet)\b", re.I),
    "question": re.compile(r"\?"),
    "exclaim": re.compile(r"!"),
    "hashtag": re.compile(r"#\w+"),
    "mention": re.compile(r"@\w+"),
    "url": re.compile(r"https?://|\bhttp\b"),
    "emoji": re.compile("[\U0001F300-\U0001FAFF☀-➿]"),
    "all_caps_word": re.compile(r"\b[A-Z]{3,}\b"),
}

tok, model = load_model()
texts, _ = load_split("test")
logits, y = cached_logits("base", model, tok, "test")
pred = logits.argmax(1)
n = len(texts)
words = np.array([len(t.split()) for t in texts])


def slice_report(mask: np.ndarray) -> dict:
    if mask.sum() == 0:
        return {"n": 0}
    m = metrics(y[mask], pred[mask])
    return {"n": int(mask.sum()), "macro_f1": m["macro_f1"], "accuracy": m["accuracy"], "flag": "small" if mask.sum() < 100 else ""}


report = {"overall": slice_report(np.ones(n, dtype=bool))}
report["slices"] = {}
for name, rx in SLICES.items():
    mask = np.array([bool(rx.search(t)) for t in texts])
    report["slices"][name] = slice_report(mask)
    report["slices"][name]["without_macro_f1"] = metrics(y[~mask], pred[~mask])["macro_f1"]

report["slices"]["no_letters_or_digits"] = slice_report(np.array([not re.search(r"[A-Za-z0-9]", t) for t in texts]))
report["slices"]["short_<=4_words"] = slice_report(words <= 4)
report["slices"]["long_>=25_words"] = slice_report(words >= 25)

print(f"overall test macro-F1 {report['overall']['macro_f1']:.4f}  n={n}\n")
print(f"{'slice':<22}{'n':>6}{'macroF1':>9}{'acc':>7}{'F1 w/o':>9}")
for name, r in report["slices"].items():
    if r["n"] == 0:
        continue
    flag = " *" if r["flag"] else ""
    print(f"{name:<22}{r['n']:>6}{r['macro_f1']:>9.4f}{r['accuracy']:>7.3f}{r.get('without_macro_f1', float('nan')):>9.4f}{flag}")
print("  (* = n < 100, treat as noisy)")

# Confusion-pair counts and example dumps.
pairs = {}
for t, yt, yp in zip(texts, y, pred):
    if yt != yp:
        pairs.setdefault((LABELS[yt], LABELS[yp]), []).append(t)
print("\nmisclassification pairs (true -> pred):")
for (a, b), items in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
    print(f"  {a:>9} -> {b:<9} {len(items)}")
    with open(RESULTS / f"step3_examples_{a}_to_{b}.jsonl", "w") as f:
        for t in items[:50]:
            f.write(json.dumps({"text": t}) + "\n")

report["confusion_pairs"] = {f"{a}->{b}": len(v) for (a, b), v in pairs.items()}
print("wrote", save_json("step3_errors", report))
