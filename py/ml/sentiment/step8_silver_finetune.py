"""Step 8: fine-tune on silver labels, evaluate on the 300 hand-labelled recent tweets.

Training data: finlarp tweet_sentiment stance, bucketed (<= -1 neg, >= 1 pos, 0 neu), filtered to
votes >= 2 and agreement >= 0.67. All 300 POC tweet ids are excluded from training.
Silver labels are LLM-produced stance toward a ticker, not generic tweet tone. Neg labels also
include quoted analysts/people (view_holder != author), so they are noisier than the rest.

Progress: logged to the console AND to data/ml/sentiment/logs/silver_v1_<timestamp>.log.
Follow a run with:  tail -f <that log path>

Eval: POC 300 after every epoch (informational only; the reported model is the final epoch,
fixed in advance, so nothing is picked on the eval set). tweet_eval test once at the end, to
check whether recent-tweet tuning hurts the old benchmark.
"""

import json
import logging
import random
import sys
import time
from datetime import datetime

import duckdb
import numpy as np
import torch
from common import (
    LABELS,
    OUT,
    cached_logits,
    device,
    load_model,
    load_split,
    metrics,
    predict_logits,
    preprocess,
    save_json,
)
from transformers import get_linear_schedule_with_warmup

RUN = "silver_v1"
EPOCHS = 3
LR = 1e-5
BS = 16
SEED = 0
LOG_EVERY = 10
MAX_LEN = 128
MAP = {"neg": 0, "neu": 1, "pos": 2}
SCRATCH_TRAIN = "/Users/jacksonfaulkner/code/github_repos/finlarp/data/scratch/silver_train_v1.parquet"
POC = OUT / "poc"

# ---- logging -------------------------------------------------------------------
LOG_DIR = OUT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_path = LOG_DIR / f"{RUN}_{datetime.now():%Y%m%d_%H%M%S}.log"
logger = logging.getLogger(RUN)
logger.setLevel(logging.INFO)
logger.propagate = False
_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(_fmt)
_file = logging.FileHandler(log_path, mode="w")
_file.setFormatter(_fmt)
logger.addHandler(_console)
logger.addHandler(_file)
logger.info("log file: %s", log_path)
logger.info("config: epochs=%d lr=%g bs=%d seed=%d max_len=%d", EPOCHS, LR, BS, SEED, MAX_LEN)


# ---- data -----------------------------------------------------------------------
def load_poc():
    blind = [json.loads(line) for line in open(POC / "blind_300.jsonl")]
    claude = {}
    for part in ("part1", "part2"):
        for line in open(POC / f"labels_claude_{part}.txt"):
            idx, lab, _conf = line.split()
            claude[int(idx)] = MAP[lab]
    texts = [b["text"] for b in blind]
    ids = {b["id"] for b in blind}
    y = np.array([claude[i] for i in range(len(blind))])
    return texts, y, ids


def load_train(poc_ids):
    rows = duckdb.connect().execute(
        f"SELECT id, text, lab FROM read_parquet('{SCRATCH_TRAIN}') ORDER BY lab, id"
    ).fetchall()
    logger.info("train rows read: %d (multi-ticker tweets repeat)", len(rows))
    seen, texts, labels = set(), [], []
    for tid, text, lab in rows:
        if tid in seen:
            continue
        seen.add(tid)
        texts.append(text)
        labels.append(MAP[lab])
    overlap = seen & poc_ids
    assert not overlap, f"POC leakage into training: {len(overlap)} ids"
    counts = {k: labels.count(v) for k, v in MAP.items()}
    logger.info("train tweets after dedupe: %d  class counts %s  (POC overlap: 0)", len(texts), counts)
    return texts, np.array(labels)


# ---- eval -----------------------------------------------------------------------
def eval_poc(model, tok, poc_texts, poc_y, tag):
    logits = predict_logits(model, tok, poc_texts)
    m = metrics(poc_y, logits.argmax(1))
    logger.info("[%s] POC300 macro-F1 %.4f  acc %.4f  confusion(neg/neu/pos rows) %s",
                tag, m["macro_f1"], m["accuracy"], m["confusion"])
    return m


# ---- main -----------------------------------------------------------------------
def main():
    torch.manual_seed(SEED)
    random.seed(SEED)
    dev = device()
    logger.info("device: %s", dev)

    poc_texts, poc_y, poc_ids = load_poc()
    logger.info("POC eval: %d tweets, class counts %s", len(poc_texts),
                {k: int((poc_y == v).sum()) for k, v in MAP.items()})
    train_texts, train_y = load_train(poc_ids)

    tok, model = load_model()
    logger.info("loaded base checkpoint")
    results = {"config": {"epochs": EPOCHS, "lr": LR, "bs": BS, "seed": SEED},
               "train_n": len(train_texts), "poc_by_epoch": {}}

    results["base_poc"] = eval_poc(model, tok, poc_texts, poc_y, "base")
    base_test_logits, test_y = cached_logits("base", model, tok, "test")
    results["base_test_macro_f1"] = metrics(test_y, base_test_logits.argmax(1))["macro_f1"]
    logger.info("[base] tweet_eval test macro-F1 %.4f", results["base_test_macro_f1"])

    model.train()
    proc = [preprocess(t) for t in train_texts]
    steps_per_epoch = (len(proc) + BS - 1) // BS
    total_steps = EPOCHS * steps_per_epoch
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total_steps), total_steps)
    loss_fn = torch.nn.CrossEntropyLoss()
    logger.info("training: %d steps/epoch, %d total", steps_per_epoch, total_steps)

    step = 0
    t0 = time.time()
    for epoch in range(1, EPOCHS + 1):
        order = np.random.default_rng(SEED + epoch).permutation(len(proc))
        window_loss, window_n, window_t = 0.0, 0, time.time()
        for s in range(0, len(order), BS):
            idx = order[s : s + BS]
            enc = tok([proc[i] for i in idx], padding=True, truncation=True,
                      max_length=MAX_LEN, return_tensors="pt").to(dev)
            labels = torch.tensor(train_y[idx], device=dev)
            loss = loss_fn(model(**enc).logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            step += 1
            window_loss += loss.item() * len(idx)
            window_n += len(idx)

            if step % LOG_EVERY == 0 or step == total_steps:
                elapsed = time.time() - t0
                rate = step / elapsed
                eta = (total_steps - step) / rate if rate > 0 else float("nan")
                ex_per_s = window_n / max(time.time() - window_t, 1e-9)
                logger.info(
                    "epoch %d/%d step %d/%d (%.1f%%)  loss %.4f  lr %.2e  %.1f ex/s  elapsed %.0fs  eta %.0fs",
                    epoch, EPOCHS, step, total_steps, 100 * step / total_steps,
                    window_loss / window_n, sched.get_last_lr()[0], ex_per_s, elapsed, eta,
                )
                window_loss, window_n, window_t = 0.0, 0, time.time()

        model.eval()
        m = eval_poc(model, tok, poc_texts, poc_y, f"epoch {epoch}")
        results["poc_by_epoch"][epoch] = m
        model.train()
        logger.info("epoch %d done in %.0fs total", epoch, time.time() - t0)

    model.eval()
    results["final_poc"] = results["poc_by_epoch"][EPOCHS]
    test_logits = predict_logits(model, tok, load_split("test")[0])
    results["final_test_macro_f1"] = metrics(test_y, test_logits.argmax(1))["macro_f1"]
    logger.info("[final] tweet_eval test macro-F1 %.4f (base %.4f, delta %+.4f)",
                results["final_test_macro_f1"], results["base_test_macro_f1"],
                results["final_test_macro_f1"] - results["base_test_macro_f1"])

    out_dir = OUT / RUN
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    logger.info("saved fine-tuned checkpoint to %s", out_dir)
    path = save_json(RUN, results)
    logger.info("wrote results to %s", path)
    logger.info("DONE. base POC %.4f -> final POC %.4f | test %.4f -> %.4f",
                results["base_poc"]["macro_f1"], results["final_poc"]["macro_f1"],
                results["base_test_macro_f1"], results["final_test_macro_f1"])


if __name__ == "__main__":
    main()
