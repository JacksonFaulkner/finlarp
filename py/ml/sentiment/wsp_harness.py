"""Weight-space edit harness, one shard per agent. Scores edits on VALIDATION only.

Subcommands:
  start  --minutes N   set the deadline (now + N min), clear STOP, reset progress log
  shards               write the 15-way split of the base weights (shards.json)
  stats  --shard K     per-tensor summary for shard K (read-only)
  eval   --shard K --edits FILE
                       apply the edits (only tensors inside shard K) to base in memory,
                       score macro-F1 on the 2000 validation tweets, log the result
  status               progress table for all shards, plus time left

Edit language (same as the paper's Exp 4):
  name[idx] = value        name[idx] = [v, v, ...]   name[idx] += / -= / *= value
  ZERO name                # comment
  idx: ints, a:b (half-open), ':' or empty; comma-separated. Row ranges of split tensors
       must sit inside the shard's row range.
Unreadable or out-of-shard statements are skipped and reported; the rest still apply.

Guards: refuses to run after the deadline, if STOP exists, or on test-set data (never loaded here).
"""

import argparse
import fcntl
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import torch
from common import MODEL_DIR, OUT, cached_logits, load_model, load_split, metrics, predict_logits

WSP = OUT / "wsp"
LOCKS = WSP / "locks"
SHARDS = WSP / "shards.json"
PROGRESS = WSP / "progress.jsonl"
DEADLINE = WSP / "deadline.txt"
START = WSP / "start.txt"
STOP = WSP / "STOP"
N_SHARDS = 15
MAX_CONCURRENT = 3
MAX_ABS = 1e6
for _d in (WSP, LOCKS):
    _d.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now()


# ---- shards ----------------------------------------------------------------------
def cmd_shards(_):
    sd = torch.load(MODEL_DIR / "pytorch_model.bin", map_location="cpu", weights_only=True)
    pieces = []
    for name, t in sd.items():
        if not t.is_floating_point():
            continue
        if name == "roberta.embeddings.word_embeddings.weight":
            rows = t.shape[0]
            step = (rows + 4) // 5
            for r0 in range(0, rows, step):
                r1 = min(rows, r0 + step)
                pieces.append({"name": name, "r0": r0, "r1": r1, "numel": (r1 - r0) * t.shape[1]})
        else:
            pieces.append({"name": name, "r0": None, "r1": None, "numel": t.numel()})
    pieces.sort(key=lambda p: -p["numel"])
    shards = [{"shard": k, "numel": 0, "entries": []} for k in range(N_SHARDS)]
    for p in pieces:
        k = min(shards, key=lambda s: s["numel"])
        k["entries"].append(p)
        k["numel"] += p["numel"]
    SHARDS.write_text(json.dumps(shards, indent=2))
    for s in shards:
        print(f"shard {s['shard']:>2}: {s['numel']:>11,} weights in {len(s['entries'])} pieces")
    print("wrote", SHARDS)


def load_shard(k):
    shards = json.loads(SHARDS.read_text())
    return shards[k]


# ---- stats -------------------------------------------------------------------------
def cmd_stats(args):
    sys.exit("use py/ml/sentiment/wsp_client.py stats (shared server; no per-call model loads)")
    shard = load_shard(args.shard)
    _, model = load_model()
    sd = dict(model.named_parameters())
    print(f"shard {args.shard}: {shard['numel']:,} weights, {len(shard['entries'])} pieces")
    print(f"{'tensor':<62}{'rows':>14}{'numel':>12}{'L2':>10}{'mean|w|':>10}")
    with torch.no_grad():
        for e in shard["entries"]:
            t = sd[e["name"]]
            if e["r0"] is not None:
                t = t[e["r0"] : e["r1"]]
                rows = f"{e['r0']}:{e['r1']}"
            else:
                rows = "all"
            tag = e["name"].replace("roberta.encoder.layer.", "L").replace("roberta.", "")
            print(f"{tag:<62}{rows:>14}{t.numel():>12,}{float(t.norm()):>10.2f}{float(t.abs().mean()):>10.4f}")
    print("\nEdit only these tensors (row ranges for split ones):")
    for e in shard["entries"]:
        print(f"  {e['name']}" + (f"[{e['r0']}:{e['r1']}]" if e["r0"] is not None else ""))


# ---- edit parser ----------------------------------------------------------------------
STMT = re.compile(r"^(\S+?)\s*\[(.*)\]\s*(=|\+=|-=|\*=)\s*(.+)$")


def parse_index(s):
    parts = []
    for p in s.split(","):
        p = p.strip()
        if p in ("", ":"):
            parts.append(slice(None))
        elif ":" in p:
            a, b = p.split(":", 1)
            parts.append(slice(int(a) if a.strip() else None, int(b) if b.strip() else None))
        else:
            parts.append(int(p))
    return tuple(parts)


def apply_edits(model, shard, text):
    sd = dict(model.named_parameters())
    names = {e["name"]: e for e in shard["entries"]}
    applied, skipped = 0, []

    def check_range(name, key):
        e = names.get(name)
        if e is None:
            raise ValueError(f"{name} not in this shard")
        if e["r0"] is None:
            return
        first = key[0] if key else slice(None)
        if isinstance(first, int):
            ok = e["r0"] <= first < e["r1"]
        else:
            ok = first.start is not None and first.stop is not None and first.start >= e["r0"] and first.stop <= e["r1"]
        if not ok:
            raise ValueError(f"rows outside shard range {e['r0']}:{e['r1']}")

    with torch.no_grad():
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                if line.startswith("ZERO "):
                    name = line[5:].strip()
                    if name not in names or names[name]["r0"] is not None:
                        raise ValueError("ZERO only for whole tensors inside this shard")
                    sd[name].zero_()
                else:
                    m = STMT.match(line)
                    if not m:
                        raise ValueError("unreadable statement")
                    name, idx, op, val = m.groups()
                    key = parse_index(idx)
                    check_range(name, key)
                    t = sd[name]
                    if val.strip().startswith("["):
                        if op != "=":
                            raise ValueError("list values only with =")
                        v = torch.tensor(json.loads(val), dtype=t.dtype, device=t.device)
                        if float(v.abs().max()) > MAX_ABS:
                            raise ValueError("value above 1e6")
                        t[key] = v
                    else:
                        v = float(val)
                        if abs(v) > MAX_ABS:
                            raise ValueError("value above 1e6")
                        if op == "=":
                            t[key] = v
                        else:
                            cur = t[key]
                            t[key] = cur + v if op == "+=" else cur - v if op == "-=" else cur * v
                applied += 1
            except Exception as ex:  # noqa: BLE001 - report and skip, as the paper's harness does
                skipped.append({"line": lineno, "why": str(ex)[:100]})
    return applied, skipped


# ---- guards and locks --------------------------------------------------------------
def guard():
    if STOP.exists():
        sys.exit("STOP file present: no evals run")
    if not DEADLINE.exists():
        sys.exit("no deadline set (run: start --minutes N)")
    dl = datetime.fromisoformat(DEADLINE.read_text().strip())
    if now() > dl:
        sys.exit(f"deadline {dl:%H:%M:%S} passed")


def acquire_slot():
    while True:
        for i in range(MAX_CONCURRENT):
            f = open(LOCKS / f"slot{i}.lock", "w")
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return f
            except BlockingIOError:
                f.close()
        time.sleep(0.5)


# ---- eval --------------------------------------------------------------------------
def cmd_eval(args):
    sys.exit("use py/ml/sentiment/wsp_client.py eval (shared server; no per-call model loads)")
    guard()
    shard = load_shard(args.shard)
    text = Path(args.edits).read_text()
    slot = acquire_slot()
    try:
        guard()
        tok, model = load_model()
        val_texts, val_y = load_split("validation")
        base_logits, _ = cached_logits("base", model, tok, "validation")
        base_f1 = metrics(val_y, base_logits.argmax(1))["macro_f1"]
        applied, skipped = apply_edits(model, shard, text)
        model.eval()
        f1 = metrics(val_y, predict_logits(model, tok, val_texts).argmax(1))["macro_f1"]
    finally:
        slot.close()
    rec = {
        "ts": now().isoformat(timespec="seconds"),
        "shard": args.shard,
        "edits": str(args.edits),
        "edits_sha": hashlib.sha1(text.encode()).hexdigest()[:10],
        "applied": applied,
        "skipped": len(skipped),
        "val_macro_f1": round(f1, 4),
        "base_val_macro_f1": round(base_f1, 4),
        "delta": round(f1 - base_f1, 4),
    }
    with open(PROGRESS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    for s in skipped[:5]:
        print("  skipped line", s["line"], "-", s["why"])


# ---- start and status ----------------------------------------------------------------
def cmd_start(args):
    t0 = now()
    DEADLINE.write_text((t0 + timedelta(minutes=args.minutes)).isoformat(timespec="seconds"))
    START.write_text(t0.isoformat(timespec="seconds"))
    if STOP.exists():
        STOP.unlink()
    PROGRESS.write_text("")
    print("deadline", (t0 + timedelta(minutes=args.minutes)).strftime("%H:%M:%S"))


def cmd_status(_):
    recs = [json.loads(l) for l in PROGRESS.read_text().splitlines() if l.strip()] if PROGRESS.exists() else []
    print(f"now {now():%H:%M:%S}   deadline {DEADLINE.read_text().strip() if DEADLINE.exists() else 'unset'}"
          f"   STOP {'yes' if STOP.exists() else 'no'}")
    print(f"evals so far: {len(recs)}")
    print(f"{'shard':>5} {'evals':>6} {'best delta':>11} {'best val F1':>12} {'last eval':>10}  best edits")
    for k in range(N_SHARDS):
        mine = [r for r in recs if r["shard"] == k]
        if not mine:
            print(f"{k:>5} {0:>6} {'-':>11} {'-':>12} {'-':>10}")
            continue
        best = max(mine, key=lambda r: r["delta"])
        print(f"{k:>5} {len(mine):>6} {best['delta']:>+11.4f} {best['val_macro_f1']:>12.4f} "
              f"{mine[-1]['ts'][11:]:>10}  {best['edits']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("shards").set_defaults(fn=cmd_shards)
    p = sub.add_parser("start")
    p.add_argument("--minutes", type=float, required=True)
    p.set_defaults(fn=cmd_start)
    p = sub.add_parser("stats")
    p.add_argument("--shard", type=int, required=True)
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("eval")
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--edits", required=True)
    p.set_defaults(fn=cmd_eval)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
