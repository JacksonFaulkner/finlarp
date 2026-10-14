"""Pull the newer end of every stored handle: for each raw file, fetch everything after its newest stored
tweet (X's since_time operator) and merge it in (deduped by id). The scheduled counterpart of fill_tweets, which fills the older end.

    uv run python -m jobs.pull_recent_tweets --dry-run              # plan and cost estimate
    uv run python -m jobs.pull_recent_tweets --max-cost 1           # every handle, Apify hard cap $1 per run
    uv run python -m jobs.pull_recent_tweets dylan522p --max-cost 0.2

All handles share runs of --batch-size (one `from:` search term each), so a pull every half hour pays
the per-run platform overhead once, not once per handle. Apify bills per tweet returned, so starting
each search one second after the newest stored tweet means a run pays only for new tweets. Each handle's cap is its posting rate over
the window plus slack, so one noisy account can't eat the run.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from jobs.fill_tweets import COST_PER_TWEET
from jobs.pull_tweets import ACTOR, save
from sources import apify, tweets


def plan(slack: float, min_cap: int, max_cap: int) -> list[dict]:
    """Per handle: newest stored tweet, the window to ask for, and a cap from its posting rate."""
    now = datetime.now(timezone.utc)
    out = []
    for f in sorted(tweets.RAW.glob("*.jsonl")):
        stamps = [parsedate_to_datetime(json.loads(line)["createdAt"]).astimezone(timezone.utc)
                  for line in f.read_text().splitlines() if line.strip()]
        if not stamps:
            continue
        first, last = min(stamps), max(stamps)
        rate = len(stamps) / max((last - first).total_seconds() / 86400, 1)  # tweets per day
        since = int(last.timestamp()) + 1
        days = max((now - last).total_seconds() / 86400, 0.1)
        out.append({"handle": f.stem, "last": last, "since": since, "rate": rate,
                    "cap": min(max_cap, max(min_cap, math.ceil(rate * (days + 1) * slack)))})
    return out


def run_batch(batch: list[dict], until: date, max_cost: float) -> dict[str, int]:
    terms = [f"from:{g['handle']} since_time:{g['since']} until:{until}" for g in batch]
    run = apify.start_run(ACTOR, {"mode": "search", "searchTerms": terms, "maxItems": sum(g["cap"] for g in batch)},
                          max_cost_usd=max_cost)
    while run["status"] in ("READY", "RUNNING"):
        run = apify.wait_run(run["id"], wait_secs=60)
    print(f"  run {run['id']} {run['status']}, usage ${run.get('usageTotalUsd')}", flush=True)
    items, offset = [], 0
    while True:
        page = apify.dataset_items(run["defaultDatasetId"], limit=1000, offset=offset)
        items += page
        if len(page) < 1000:
            break
        offset += 1000
    by: dict[str, list[dict]] = {}
    for it in items:
        by.setdefault(((it.get("author") or {}).get("username") or "").lower(), []).append(it)
    for g in batch:
        if rows := by.get(g["handle"]):
            save(g["handle"], rows)
    return {g["handle"]: len(by.get(g["handle"], [])) for g in batch}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("handles", nargs="*", help="only these handles (default: every stored one)")
    ap.add_argument("--slack", type=float, default=1.5, help="multiplier on the projected new volume")
    ap.add_argument("--min-cap", type=int, default=20)
    ap.add_argument("--max-cap", type=int, default=400, help="per handle per run")
    ap.add_argument("--batch-size", type=int, default=40)
    ap.add_argument("--max-cost", type=float, default=1.0, help="Apify hard spend cap per run, USD")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    todo = plan(a.slack, a.min_cap, a.max_cap)
    if a.handles:
        want = {h.lstrip("@").lower() for h in a.handles}
        todo = [g for g in todo if g["handle"] in want]
    total = sum(g["cap"] for g in todo)
    print(f"{len(todo)} handles, up to {total} tweets, at most ${total * COST_PER_TWEET:.2f} at ${COST_PER_TWEET}/tweet")
    if a.dry_run:
        for g in todo:
            print(f"  {g['handle']:<18} last {g['last']:%m-%d %H:%M}Z  ~{g['rate']:.1f}/day  cap {g['cap']}")
        return
    until = datetime.now(timezone.utc).date() + timedelta(days=1)
    got: dict[str, int] = {}
    for i in range(0, len(todo), a.batch_size):
        got |= run_batch(todo[i:i + a.batch_size], until, a.max_cost)
    print(f"fetched {sum(got.values())} tweets from {sum(1 for n in got.values() if n)} handles")


if __name__ == "__main__":
    main()
