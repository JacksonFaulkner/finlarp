#!/usr/bin/env python3
"""Print runs from observe.py logs as a table, to compare machines and commits.

    python3 tools/pbr3d/runs.py                       # tools/pbr3d/runs.jsonl
    python3 tools/pbr3d/runs.py worker.jsonl local.jsonl --label bake:logic_die_overview

Columns: when (UTC), where, label, wall_s, user_s, exit, git sha (* = dirty tree), cpus, os/arch,
and the first output's short sha256. Sorted by label, then time.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(paths):
    rows = []
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def main(argv):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("logs", nargs="*", default=[os.path.join(HERE, "runs.jsonl")])
    ap.add_argument("--label", help="only labels containing this text")
    args = ap.parse_args(argv)

    rows = load(args.logs)
    if args.label:
        rows = [r for r in rows if args.label in r["label"]]
    rows.sort(key=lambda r: (r["label"], r["started"]))
    if not rows:
        print("no runs")
        return 0

    head = f"{'when (UTC)':<19} {'where':<7} {'label':<30} {'wall_s':>8} {'user_s':>8} {'exit':>4} {'git':<14} {'cpus':>4} {'os/arch':<16} {'out sha':<12}"
    print(head)
    print("-" * len(head))
    for r in rows:
        git = r.get("git") or {}
        sha = (git.get("sha") or "?") + ("*" if git.get("dirty") else "")
        host = r.get("host") or {}
        osarch = f"{host.get('os', '?')}/{host.get('arch', '?')}"
        outs = [o for o in r.get("outputs", []) if "sha256" in o]
        out_sha = outs[0]["sha256"][:10] if outs else "-"
        print(
            f"{r['started'][:19]:<19} {r.get('where', '?'):<7} {r['label']:<30} "
            f"{r['wall_s']:>8.2f} {r.get('user_s', 0):>8.2f} {r['exit']:>4} {sha:<14} "
            f"{str(host.get('cpus', '?')):>4} {osarch:<16} {out_sha:<12}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
