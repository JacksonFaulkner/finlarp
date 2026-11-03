"""Client for the shared weight-edit server. Standard library only: loads no model, no torch.

  python3 py/ml/sentiment/wsp_client.py ping
  python3 py/ml/sentiment/wsp_client.py stats --shard K
  python3 py/ml/sentiment/wsp_client.py eval  --shard K --edits FILE
  python3 py/ml/sentiment/wsp_client.py status
(start is run by the orchestrator only: wsp_client.py start --minutes N)
"""

import argparse
import json
import socket
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WSP = ROOT / "data/ml/sentiment/wsp"
DEADLINE = WSP / "deadline.txt"
START = WSP / "start.txt"
STOP = WSP / "STOP"
PROGRESS = WSP / "progress.jsonl"
HOST, PORT = "127.0.0.1", 8765


def call(req):
    try:
        with socket.create_connection((HOST, PORT), timeout=900) as s:
            s.sendall((json.dumps(req) + "\n").encode())
            line = s.makefile().readline()
    except (ConnectionRefusedError, OSError) as ex:
        raise SystemExit(f"server not reachable on {HOST}:{PORT} ({ex}). Is wsp_server.py running?")
    return json.loads(line)


def cmd_ping(_):
    print(json.dumps(call({"op": "ping"})))


def cmd_stats(args):
    resp = call({"op": "stats", "shard": args.shard})
    print(resp.get("text", json.dumps(resp)))


def cmd_eval(args):
    text = Path(args.edits).read_text()
    resp = call({"op": "eval", "shard": args.shard, "edits": text})
    print(json.dumps(resp))


def cmd_status(_):
    recs = [json.loads(l) for l in PROGRESS.read_text().splitlines() if l.strip()] if PROGRESS.exists() else []
    dl = DEADLINE.read_text().strip() if DEADLINE.exists() else "unset"
    print(f"now {datetime.now():%H:%M:%S}   deadline {dl}   STOP {'yes' if STOP.exists() else 'no'}")
    print(f"evals so far: {len(recs)}")
    print(f"{'shard':>5} {'evals':>6} {'best delta':>11} {'best val F1':>12} {'last eval':>10}")
    for k in range(15):
        mine = [r for r in recs if r["shard"] == k]
        if not mine:
            print(f"{k:>5} {0:>6} {'-':>11} {'-':>12} {'-':>10}")
            continue
        best = max(mine, key=lambda r: r["delta"])
        print(f"{k:>5} {len(mine):>6} {best['delta']:>+11.4f} {best['val_macro_f1']:>12.4f} {mine[-1]['ts'][11:]:>10}")


def cmd_start(args):
    WSP.mkdir(parents=True, exist_ok=True)
    t0 = datetime.now()
    end = t0 + timedelta(minutes=args.minutes)
    DEADLINE.write_text(end.isoformat(timespec="seconds"))
    START.write_text(t0.isoformat(timespec="seconds"))
    if STOP.exists():
        STOP.unlink()
    PROGRESS.write_text("")
    print("deadline", end.strftime("%H:%M:%S"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ping").set_defaults(fn=cmd_ping)
    p = sub.add_parser("stats")
    p.add_argument("--shard", type=int, required=True)
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("eval")
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--edits", required=True)
    p.set_defaults(fn=cmd_eval)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("start")
    p.add_argument("--minutes", type=float, required=True)
    p.set_defaults(fn=cmd_start)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
