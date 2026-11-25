"""Summarise an FL_PROFILE log (tui/src/app.rs: one JSON line per frame that answers a key).

    FL_PROFILE=1 fl intraday          then press keys; the log is $TMPDIR/fl_profile.jsonl
    uv run python py/tools/fl_profile.py [file] [--key i] [--last N]

Per key: how many frames, then the median and the worst of every stage, in ms:
handle (key -> draw start), render (screen draw incl. image encode), draw (+ diff + write),
term (terminal finishing the frame), total (key -> terminal done), and KB sent.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path

STAGES = ("handle", "render", "draw", "term", "total")


def load(path: Path, last: int | None) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return rows[-last:] if last else rows


def summarise(rows: list[dict]) -> str:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["key"]].append(r)
    head = f"{'key':<8}{'n':>4}  " + "  ".join(f"{s:>15}" for s in STAGES) + f"  {'KB':>8}"
    lines = [head, f"{'':<14}" + "  ".join(f"{'median / max':>15}" for _ in STAGES)]
    for key, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        cells = []
        for s in STAGES:
            vals = [r[s] for r in rs if r.get(s) is not None]
            cells.append(f"{statistics.median(vals):7.1f} /{max(vals):6.1f}" if vals else f"{'—':>15}")
        kb = statistics.median(r["bytes"] for r in rs) / 1024
        lines.append(f"{key:<8}{len(rs):>4}  " + "  ".join(cells) + f"  {kb:>8.0f}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", default=os.path.join(tempfile.gettempdir(), "fl_profile.jsonl"))
    ap.add_argument("--key", help="only frames answering this key")
    ap.add_argument("--last", type=int, help="only the last N frames")
    args = ap.parse_args()
    rows = load(Path(args.file), args.last)
    if args.key:
        rows = [r for r in rows if r["key"] == args.key]
    print(summarise(rows) if rows else "no frames logged")


if __name__ == "__main__":
    main()
