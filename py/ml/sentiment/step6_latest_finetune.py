"""Step 6: (a) compare the -latest checkpoint, (b) fine-tune control on tweet_eval train.

(a) Same test set for both checkpoints. Caveat: tweet_eval test is older than the -latest
    training tweets, so this comparison is biased toward the base checkpoint. It is still the
    only labelled test set here.
(b) Fine-tune the base checkpoint 1 epoch on tweet_eval TRAIN (lr 1e-5). Control: the base
    checkpoint was already fine-tuned on this split, so only a small change is expected.
    Real drift gains need recent labelled tweets, which we do not have yet.
"""

import random

import numpy as np
import torch
from common import LABELS, MODEL_DIR, cached_logits, device, load_model, load_split, metrics, preprocess, save_json
from transformers import get_linear_schedule_with_warmup

LATEST = MODEL_DIR.parent / "cardiffnlp-twitter-roberta-base-sentiment-latest"
EPOCHS = 1
LR = 1e-5
BS = 32
SEED = 0

# (a) -latest vs base ----------------------------------------------------------
tok, model = load_model()
base_test_logits, test_y = cached_logits("base", model, tok, "test")
base_val_logits, val_y = cached_logits("base", model, tok, "validation")
del model

tok_l, model_l = load_model(LATEST)
latest_test_logits, _ = cached_logits("latest", model_l, tok_l, "test")
latest_val_logits, _ = cached_logits("latest", model_l, tok_l, "validation")
del model_l

res = {
    "base": {"validation": metrics(val_y, base_val_logits.argmax(1)), "test": metrics(test_y, base_test_logits.argmax(1))},
    "latest": {"validation": metrics(val_y, latest_val_logits.argmax(1)), "test": metrics(test_y, latest_test_logits.argmax(1))},
}
print("(a) checkpoint comparison")
for name in ("base", "latest"):
    for split in ("validation", "test"):
        m = res[name][split]
        print(f"  {name:<7}{split:<11} macro-F1 {m['macro_f1']:.4f}  acc {m['accuracy']:.4f}")
agree = float((base_test_logits.argmax(1) == latest_test_logits.argmax(1)).mean())
print(f"  test prediction agreement base vs latest: {agree:.3f}")
res["test_agreement"] = agree

# (b) fine-tune control -----------------------------------------------------------
print("\n(b) fine-tune control: base + 1 epoch on tweet_eval train")
random.seed(SEED)
torch.manual_seed(SEED)
dev = device()
tok, model = load_model()
model.train()
train_texts, train_y = load_split("train")
proc = [preprocess(t) for t in train_texts]
opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
steps = EPOCHS * ((len(proc) + BS - 1) // BS)
sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
loss_fn = torch.nn.CrossEntropyLoss()
order = np.random.default_rng(SEED).permutation(len(proc))
running, n_seen = 0.0, 0
for epoch in range(EPOCHS):
    for s in range(0, len(order), BS):
        idx = order[s : s + BS]
        enc = tok([proc[i] for i in idx], padding=True, truncation=True, max_length=128, return_tensors="pt").to(dev)
        labels = torch.tensor(train_y[idx], device=dev)
        loss = loss_fn(model(**enc).logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        running += loss.item() * len(idx)
        n_seen += len(idx)
        if (s // BS) % 200 == 0:
            print(f"  step {s // BS:>5}/{steps // EPOCHS}  running loss {running / n_seen:.4f}", flush=True)
model.eval()
ft_val_logits, _ = cached_logits("ft_ctrl", model, tok, "validation")
ft_test_logits, _ = cached_logits("ft_ctrl", model, tok, "test")
res["finetune_control"] = {
    "validation": metrics(val_y, ft_val_logits.argmax(1)),
    "test": metrics(test_y, ft_test_logits.argmax(1)),
    "hyper": {"epochs": EPOCHS, "lr": LR, "bs": BS},
}
print(f"  ft-control validation macro-F1 {res['finetune_control']['validation']['macro_f1']:.4f}")
print(f"  ft-control test       macro-F1 {res['finetune_control']['test']['macro_f1']:.4f} "
      f"(base {res['base']['test']['macro_f1']:.4f})")
print("wrote", save_json("step6_latest_finetune", res))
