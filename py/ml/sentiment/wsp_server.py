"""Shared model server for the weight-edit agents. Holds ONE copy of the model.

Start (once):  uv run --group ml python py/ml/sentiment/wsp_server.py
Clients:       python3 py/ml/sentiment/wsp_client.py {ping|stats|eval|status|start}

Each eval: applies the edits to the in-memory model, scores VALIDATION macro-F1, then restores
the shard's original weights. Requests run one at a time under a lock, so edits never overlap.
Enforces the deadline and the STOP file. Never loads the test set.
"""

import hashlib
import json
import socketserver
import threading
from datetime import datetime

import torch
from common import cached_logits, load_model, load_split, metrics, predict_logits
from wsp_harness import DEADLINE, PROGRESS, STOP, apply_edits, load_shard, now

HOST, PORT = "127.0.0.1", 8765
LOCK = threading.Lock()
STATE = {}


def check_open():
    if STOP.exists():
        return "STOP file present: no evals run"
    if not DEADLINE.exists():
        return "no deadline set (run: wsp_client.py start --minutes N)"
    dl = datetime.fromisoformat(DEADLINE.read_text().strip())
    if now() > dl:
        return f"deadline {dl:%H:%M:%S} passed"
    return None


def do_eval(shard_k, edits_text):
    err = check_open()
    if err:
        return {"error": err}
    shard = load_shard(shard_k)
    model, tok = STATE["model"], STATE["tok"]
    with LOCK:
        err = check_open()
        if err:
            return {"error": err}
        params = dict(model.named_parameters())
        snap = []
        for e in shard["entries"]:
            t = params[e["name"]]
            if e["r0"] is None:
                snap.append((t, None, t.detach().clone()))
            else:
                sl = slice(e["r0"], e["r1"])
                snap.append((t, sl, t[sl].detach().clone()))
        try:
            applied, skipped = apply_edits(model, shard, edits_text)
            model.eval()
            pred = predict_logits(model, tok, STATE["val_texts"]).argmax(1)
            f1 = metrics(STATE["val_y"], pred)["macro_f1"]
        finally:
            with torch.no_grad():
                for t, sl, saved in snap:
                    if sl is None:
                        t.copy_(saved)
                    else:
                        t[sl].copy_(saved)
    base = STATE["base_f1"]
    rec = {
        "ts": now().isoformat(timespec="seconds"),
        "shard": shard_k,
        "edits_sha": hashlib.sha1(edits_text.encode()).hexdigest()[:10],
        "applied": applied,
        "skipped": len(skipped),
        "val_macro_f1": round(f1, 4),
        "base_val_macro_f1": round(base, 4),
        "delta": round(f1 - base, 4),
    }
    with open(PROGRESS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    rec["skipped_detail"] = skipped[:5]
    return rec


def do_stats(shard_k):
    shard = load_shard(shard_k)
    model = STATE["model"]
    lines = [f"shard {shard_k}: {shard['numel']:,} weights, {len(shard['entries'])} pieces",
             f"{'tensor':<62}{'rows':>14}{'numel':>12}{'L2':>10}{'mean|w|':>10}"]
    with LOCK, torch.no_grad():
        params = dict(model.named_parameters())
        for e in shard["entries"]:
            t = params[e["name"]]
            if e["r0"] is not None:
                t = t[e["r0"] : e["r1"]]
                rows = f"{e['r0']}:{e['r1']}"
            else:
                rows = "all"
            tag = e["name"].replace("roberta.encoder.layer.", "L").replace("roberta.", "")
            lines.append(f"{tag:<62}{rows:>14}{t.numel():>12,}{float(t.norm()):>10.2f}{float(t.abs().mean()):>10.4f}")
    lines.append("")
    lines.append("Edit only these tensors (row ranges for split ones):")
    for e in shard["entries"]:
        lines.append(f"  {e['name']}" + (f"[{e['r0']}:{e['r1']}]" if e["r0"] is not None else ""))
    return {"text": "\n".join(lines)}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            req = json.loads(self.rfile.readline().decode())
            op = req.get("op")
            if op == "ping":
                resp = {"ok": True, "base_val_macro_f1": round(STATE["base_f1"], 4)}
            elif op == "eval":
                resp = do_eval(int(req["shard"]), req["edits"])
            elif op == "stats":
                resp = do_stats(int(req["shard"]))
            else:
                resp = {"error": f"unknown op {op!r}"}
        except Exception as ex:  # noqa: BLE001 - report to client, keep server alive
            resp = {"error": f"{type(ex).__name__}: {str(ex)[:200]}"}
        self.wfile.write((json.dumps(resp) + "\n").encode())


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    tok, model = load_model()
    val_texts, val_y = load_split("validation")
    base_logits, _ = cached_logits("base", model, tok, "validation")
    STATE.update(tok=tok, model=model, val_texts=val_texts, val_y=val_y,
                 base_f1=metrics(val_y, base_logits.argmax(1))["macro_f1"])
    print(f"ready on {HOST}:{PORT}  base val macro-F1 {STATE['base_f1']:.4f}", flush=True)
    with Server((HOST, PORT), Handler) as srv:
        srv.serve_forever()


if __name__ == "__main__":
    main()
