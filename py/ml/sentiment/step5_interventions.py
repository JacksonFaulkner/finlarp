"""Step 5: interventions on the weights, selected on VALIDATION, scored once on TEST.

(a) Head ablation sweep: zero one attention head's output (144 heads), measure val macro-F1 delta.
(b) Direction projection (blog Exp 8 analog): for layers 8-11, remove a unit direction u from the
    MLP output projection, W_out <- (I - u u^T) W_out. The direction comes from TRAIN-subset CLS states:
      - neu_vs_polar: neutral vs (negative+positive). Targets the dominant error (neutral confusion).
      - pos_vs_neg:   positive vs negative. Control; expected to hurt.
    Only the best validation config is scored on test. If it wins on validation, it is saved as a
    new checkpoint.
"""

import random

import numpy as np
import torch
from common import OUT, cached_logits, load_model, load_split, metrics, predict_logits, preprocess, save_json

HEAD_DIM = 64
MIN_GAIN = 0.005  # validation macro-F1 gain required before touching test

tok, model = load_model()
dev = next(model.parameters()).device
layers = model.roberta.encoder.layer
L, H = len(layers), model.config.num_attention_heads

val_texts, val_y = load_split("validation")
test_texts, test_y = load_split("test")
base_val_logits, _ = cached_logits("base", model, tok, "validation")
base_val = metrics(val_y, base_val_logits.argmax(1))["macro_f1"]
print(f"baseline val macro-F1 {base_val:.4f}")


def val_f1() -> float:
    return metrics(val_y, predict_logits(model, tok, val_texts).argmax(1))["macro_f1"]


# (a) head ablation sweep ---------------------------------------------------
def zero_head_pre_hook(h: int):
    def hook(mod, args):
        x = args[0].clone()
        x[..., h * HEAD_DIM : (h + 1) * HEAD_DIM] = 0.0
        return (x,)

    return hook


sweep = {}
for l in range(L):
    for h in range(H):
        handle = layers[l].attention.output.dense.register_forward_pre_hook(zero_head_pre_hook(h))
        try:
            sweep[f"L{l}.H{h}"] = val_f1() - base_val
        finally:
            handle.remove()
    print(f"  layer {l:>2} done; worst so far {min(sweep.values()):+.4f}, best {max(sweep.values()):+.4f}", flush=True)

ranked = sorted(sweep.items(), key=lambda kv: kv[1])
print("\nmost harmful heads when ablated (val delta):")
for k, v in ranked[:5]:
    print(f"  {k:<8} {v:+.4f}")
print("most helpful heads when ablated (val delta):")
for k, v in ranked[-5:][::-1]:
    print(f"  {k:<8} {v:+.4f}")

head_result = {"val_delta_by_head": sweep, "candidate": None}
best_head, best_head_gain = ranked[-1]
if best_head_gain >= MIN_GAIN:
    l, h = (int(x) for x in best_head[1:].split(".H"))
    handle = layers[l].attention.output.dense.register_forward_pre_hook(zero_head_pre_hook(h))
    try:
        test_ablate = metrics(test_y, predict_logits(model, tok, test_texts).argmax(1))["macro_f1"]
    finally:
        handle.remove()
    head_result["candidate"] = {"head": best_head, "val_gain": best_head_gain, "test_macro_f1": test_ablate}
    print(f"\ncandidate head {best_head}: val gain {best_head_gain:+.4f} -> test macro-F1 {test_ablate:.4f}")
else:
    print(f"\nno head ablation clears the {MIN_GAIN} validation gain bar (best {best_head} {best_head_gain:+.4f})")

# (b) direction projection on MLP output ------------------------------------
print("\ncomputing directions from train subset (CLS states)...")
train_texts, train_y = load_split("train")
idx = random.Random(0).sample(range(len(train_texts)), 4000)
tr_texts = [train_texts[i] for i in idx]
tr_y = train_y[idx]

hs_all = []
with torch.inference_mode():
    for s in range(0, len(tr_texts), 64):
        enc = tok([preprocess(t) for t in tr_texts[s : s + 64]], padding=True, truncation=True,
                  max_length=128, return_tensors="pt").to(dev)
        hs = model(**enc, output_hidden_states=True).hidden_states
        hs_all.append(torch.stack([h[:, 0, :] for h in hs], dim=1).float().cpu())
hs_all = torch.cat(hs_all).numpy()  # (n, 13, 768); index l+1 is the output of block l

directions = {}
for l in range(8, 12):
    h_l = hs_all[:, l + 1, :]
    d_neu = h_l[tr_y == 1].mean(0) - h_l[tr_y != 1].mean(0)
    d_pn = h_l[tr_y == 2].mean(0) - h_l[tr_y == 0].mean(0)
    directions[(l, "neu_vs_polar")] = d_neu / np.linalg.norm(d_neu)
    directions[(l, "pos_vs_neg")] = d_pn / np.linalg.norm(d_pn)

proj_val = {}
best_proj = (-1.0, None)
for (l, name), u in directions.items():
    W = layers[l].output.dense.weight  # (768, 3072): MLP output projection
    W0 = W.detach().clone()
    u_t = torch.tensor(u, dtype=W.dtype, device=dev)
    P = torch.eye(u_t.numel(), dtype=W.dtype, device=dev) - torch.outer(u_t, u_t)
    with torch.no_grad():
        W.copy_(P @ W0)
    try:
        d = val_f1() - base_val
    finally:
        with torch.no_grad():
            W.copy_(W0)
    proj_val[f"L{l}.{name}"] = d
    print(f"  L{l} {name:<12} val delta {d:+.4f}")
    if d > best_proj[0]:
        best_proj = (d, (l, name, u))

result = {"baseline_val_macro_f1": base_val, "head_ablation": head_result, "projection_val_delta": proj_val}
if best_proj[0] >= MIN_GAIN:
    d, (l, name, u) = best_proj
    W = layers[l].output.dense.weight
    u_t = torch.tensor(u, dtype=W.dtype, device=dev)
    P = torch.eye(u_t.numel(), dtype=W.dtype, device=dev) - torch.outer(u_t, u_t)
    with torch.no_grad():
        W.copy_(P @ W.detach().clone())
    test_proj = metrics(test_y, predict_logits(model, tok, test_texts).argmax(1))
    base_test = metrics(test_y, cached_logits("base", model, tok, "test")[0].argmax(1))
    print(f"\nchosen projection L{l} {name}: val gain {d:+.4f}")
    print(f"test macro-F1 base {base_test['macro_f1']:.4f} -> edited {test_proj['macro_f1']:.4f} "
          f"(delta {test_proj['macro_f1'] - base_test['macro_f1']:+.4f})")
    result["projection_candidate"] = {"layer": l, "direction": name, "val_gain": d,
                                      "test_base": base_test, "test_edited": test_proj}
    out_dir = OUT / f"edited_L{l}_{name}"
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    print("saved edited checkpoint to", out_dir)
else:
    print(f"\nno projection clears the {MIN_GAIN} validation gain bar (best {best_proj[0]:+.4f})")

save_json("step5_interventions", result)
print("wrote step5_interventions.json")
