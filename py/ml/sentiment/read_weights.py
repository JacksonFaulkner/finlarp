"""Read the weights directly: structure, norms, classifier head, and what the silver fine-tune changed.

No forward passes. Reads tensors from disk only.
  base:  data/models/cardiffnlp-twitter-roberta-base-sentiment/pytorch_model.bin
  tuned: data/ml/sentiment/silver_v1/model.safetensors
"""

import torch
from common import MODEL_DIR, OUT
from safetensors.torch import load_file

LABELS = ["negative", "neutral", "positive"]
base = torch.load(MODEL_DIR / "pytorch_model.bin", map_location="cpu", weights_only=True)
tuned = load_file(OUT / "silver_v1" / "model.safetensors")

print(f"base tensors: {len(base)}  tuned tensors: {len(tuned)}")
print(f"base params: {sum(t.numel() for t in base.values()):,}")
missing = set(base) ^ set(tuned)
print(f"key mismatch between base and tuned: {sorted(missing)[:5]} ({len(missing)})")

# 1. Structure by component -----------------------------------------------------
print("\n== structure (base) ==")
groups = {}
for k, t in base.items():
    g = k.split(".")[1] if k.startswith("roberta.encoder") else k.split(".")[0] + "." + k.split(".")[1]
    groups.setdefault(g, [0, 0.0])
    groups[g][0] += t.numel()
    groups[g][1] += float(t.float().norm() ** 2)
for g, (n, sq) in sorted(groups.items(), key=lambda kv: -kv[1][0])[:12]:
    print(f"  {g:<28} {n:>12,} params   L2 {sq ** 0.5:10.2f}")

# 2. Per-layer weight norms ------------------------------------------------------
print("\n== per-layer L2 of attention and MLP weights (base) ==")
print(f"  {'layer':>5} {'Q':>8} {'K':>8} {'V':>8} {'O':>8} {'MLP_in':>8} {'MLP_out':>8}")
for l in range(12):
    p = f"roberta.encoder.layer.{l}."
    row = [
        base[p + "attention.self.query.weight"].norm(),
        base[p + "attention.self.key.weight"].norm(),
        base[p + "attention.self.value.weight"].norm(),
        base[p + "attention.output.dense.weight"].norm(),
        base[p + "intermediate.dense.weight"].norm(),
        base[p + "output.dense.weight"].norm(),
    ]
    print(f"  {l:>5} " + " ".join(f"{float(x):8.2f}" for x in row))

# 3. Classifier head: the only part that maps the sentence to a label ------------
print("\n== classifier head (base) ==")
W = base["classifier.out_proj.weight"]  # (3, 768)
b = base["classifier.out_proj.bias"]
print(f"  out_proj weight {tuple(W.shape)}  bias {[round(float(x), 4) for x in b]}")
for i, name in enumerate(LABELS):
    print(f"  row {i} ({name:<8}) L2 {float(W[i].norm()):.3f}")
cos = torch.nn.functional.cosine_similarity
print(f"  cos(neg,neu) {float(cos(W[0], W[1], dim=0)):+.3f}  "
      f"cos(neu,pos) {float(cos(W[1], W[2], dim=0)):+.3f}  "
      f"cos(neg,pos) {float(cos(W[0], W[2], dim=0)):+.3f}")
d = W[2] - W[0]  # direction that pushes toward positive over negative
top = torch.topk(d.abs(), 8)
print("  hidden dims that most separate pos from neg (dim: pos-neg weight):")
print("   ", ", ".join(f"{int(i)}: {float(d[i]):+.3f}" for i in top.indices))

dense = base["classifier.dense.weight"]
print(f"  classifier.dense {tuple(dense.shape)} L2 {float(dense.norm()):.2f}")

# 4. What silver fine-tune changed, relative to base --------------------------------
print("\n== change from base to silver_v1 (relative ||delta|| / ||base||) ==")
rows = []
for k in base:
    if k in tuned and base[k].shape == tuned[k].shape and base[k].is_floating_point():
        db = base[k].float()
        delta = tuned[k].float() - db
        rel = float(delta.norm() / (db.norm() + 1e-12))
        rows.append((rel, k))
rows.sort(reverse=True)
print("  most changed tensors:")
for rel, k in rows[:10]:
    print(f"    {rel:8.4f}  {k}")
print("  least changed tensors:")
for rel, k in rows[-5:]:
    print(f"    {rel:8.6f}  {k}")

by_layer = {}
for rel, k in rows:
    if k.startswith("roberta.encoder.layer."):
        l = int(k.split(".")[3])
        by_layer.setdefault(l, []).append(rel)
print("  mean relative change per encoder layer:")
print("   ", ", ".join(f"L{l}:{sum(v) / len(v):.4f}" for l, v in sorted(by_layer.items())))
print("\n  classifier head rel change:",
      {k.split('.', 1)[1]: round(rel, 4) for rel, k in rows if k.startswith("classifier.")})
