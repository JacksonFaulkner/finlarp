"""Pull a handle's tweets for a date window via Apify (xquik x-tweet-scraper).

    uv run jobs/pull_tweets.py aleabitoreddit dylan522p --since 2026-09-01 --until 2026-11-01

--until is exclusive (X search semantics). Output: JSONL, one tweet per line, deduped by id.
Apify bills per result, so --max-items caps the spend.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

from sources import apify

ACTOR = "wAusCMrm284Voaw86"
OUT_ROOT = Path(os.path.expanduser("~/.local/share/nvim/finlarp/tweets"))


def pull(handle: str, since: str, until: str, max_items: int) -> list[dict]:
    handle = handle.lstrip("@")
    return apify.run_actor(
        ACTOR,
        {
            "mode": "search",
            "searchTerms": [f"from:{handle} since:{since} until:{until}"],
            "maxItems": max_items,
        },
        timeout=300,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("handles", nargs="+")
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    ap.add_argument("--max-items", type=int, default=3000)
    a = ap.parse_args()

    seen_handles: set[str] = set()
    for h in a.handles:
        h = h.lstrip("@")
        if h.lower() in seen_handles:
            continue
        seen_handles.add(h.lower())
        try:
            save(h, pull(h, a.since, a.until, a.max_items))
        except requests.HTTPError as e:
            print(f"{h}: {e}")
            if e.response is not None and e.response.status_code == 402:
                raise SystemExit("402 payment required: stopping")


def save(handle: str, items: list[dict]) -> None:
    out = OUT_ROOT / f"{handle.lower()}.jsonl"
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    seen: dict[str, dict] = {}
    if out.exists():
        for line in out.read_text().splitlines():
            row = json.loads(line)
            seen[str(row.get("id"))] = row
    new = 0
    for row in items:
        k = str(row.get("id"))
        new += k not in seen
        seen[k] = row
    out.write_text("".join(json.dumps(r) + "\n" for r in seen.values()))
    print(f"{handle}: {len(items)} fetched, {new} new, {len(seen)} total -> {out}")


if __name__ == "__main__":
    main()
