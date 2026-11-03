"""Step 4: where does sentiment become linearly readable, and which heads attend to negation?

(a) Linear probe on the <s> (CLS) hidden state at every layer (0 = embeddings, 12 = last).
    Probe trained on a random TRAIN subset, scored on TEST.
(b) Attention from <s> to negation tokens, per head, on TEST tweets containing negation.
    Ratio > 1 means the head over-attends to negation relative to its share of tokens.
"""

import random
import re

import numpy as np
import torch
from common import RESULTS, device, load_model, load_split, preprocess, save_json
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler

NEG_TOKENS = {"not", "no", "never", "nothing", "nobody", "none", "nor", "nt", "'t"}
NEG_RX = re.compile(r"\b(not|no|never|nothing|nobody|none|nor)\b|n't", re.I)
N_TRAIN = 4000
BS = 64

tok, model = load_model()
dev = device()
train_texts, train_y = load_split("train")
test_texts, test_y = load_split("test")

rng = random.Random(0)
idx = rng.sample(range(len(train_texts)), N_TRAIN)
train_texts = [train_texts[i] for i in idx]
train_y = train_y[idx]


@torch.inference_mode()
def cls_states(texts: list[str]) -> np.ndarray:
    """Shape (n, 13, 768): CLS hidden state at each layer."""
    out = np.zeros((len(texts), model.config.num_hidden_layers + 1, model.config.hidden_size), dtype=np.float32)
    proc = [preprocess(t) for t in texts]
    for s in range(0, len(proc), BS):
        enc = tok(proc[s : s + BS], padding=True, truncation=True, max_length=128, return_tensors="pt").to(dev)
        hs = model(**enc, output_hidden_states=True).hidden_states
        stacked = torch.stack([h[:, 0, :] for h in hs], dim=1)
        out[s : s + BS] = stacked.float().cpu().numpy()
    return out


print("extracting CLS states (train subset + test)...")
Xtr = cls_states(train_texts)
Xte = cls_states(test_texts)

probe = {}
for layer in range(Xtr.shape[1]):
    scaler = StandardScaler().fit(Xtr[:, layer])
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(scaler.transform(Xtr[:, layer]), train_y)
    pred = clf.predict(scaler.transform(Xte[:, layer]))
    probe[layer] = float(f1_score(test_y, pred, average="macro"))
    print(f"  layer {layer:>2}: probe macro-F1 {probe[layer]:.4f}")
best_layer = max(probe, key=probe.get)
print(f"best probe layer: {best_layer} ({probe[best_layer]:.4f})")

# (b) negation attention ----------------------------------------------------
neg_idx = [i for i, t in enumerate(test_texts) if NEG_RX.search(t)]
print(f"\nnegation tweets in test: {len(neg_idx)}")
L, H = model.config.num_hidden_layers, model.config.num_attention_heads
mass_sum = np.zeros((L, H))
base_sum = np.zeros((L, H))
count = 0


@torch.inference_mode()
def attn_batch(texts: list[str]):
    proc = [preprocess(t) for t in texts]
    enc = tok(proc, padding=True, truncation=True, max_length=128, return_tensors="pt").to(dev)
    out = model(**enc, output_attentions=True)
    return enc["input_ids"].cpu(), enc["attention_mask"].cpu(), [a.float().cpu() for a in out.attentions]


for s in range(0, len(neg_idx), BS):
    batch_ids = neg_idx[s : s + BS]
    batch_texts = [test_texts[i] for i in batch_ids]
    ids, mask, atts = attn_batch(batch_texts)
    for b in range(len(batch_texts)):
        toks = tok.convert_ids_to_tokens(ids[b].tolist())
        valid = mask[b].bool()
        neg_pos = [j for j, t in enumerate(toks) if valid[j] and t.lstrip("Ġ").lower() in NEG_TOKENS]
        if not neg_pos:
            continue
        n_valid = int(valid.sum())
        share = len(neg_pos) / n_valid  # chance-level attention to negation tokens
        for layer in range(L):
            a = atts[layer][b, :, 0, :]  # (H, T) attention from <s>
            mass = a[:, neg_pos].sum(-1).numpy()
            mass_sum[layer] += mass
            base_sum[layer] += share
        count += 1

ratio = mass_sum / np.maximum(base_sum, 1e-9)
flat = [(float(ratio[l, h]), l, h) for l in range(L) for h in range(H)]
flat.sort(reverse=True)
print(f"\nover-attention ratio (attention to negation / chance), over {count} tweets with negation tokens")
print("top 10 heads (ratio, layer, head):")
for r, l, h in flat[:10]:
    print(f"  L{l:>2}.H{h:<2}  {r:.2f}")
print("bottom 3 heads:")
for r, l, h in flat[-3:]:
    print(f"  L{l:>2}.H{h:<2}  {r:.2f}")

save_json("step4_probe", {"probe_macro_f1_by_layer": probe, "best_layer": best_layer, "n_train": N_TRAIN})
save_json("step4_negation_heads", {
    "n_tweets": count,
    "ratio_by_layer_head": ratio.tolist(),
    "top10": [{"ratio": r, "layer": l, "head": h} for r, l, h in flat[:10]],
})
print("wrote results to", RESULTS)
