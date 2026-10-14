"""Fill the older end of capped tweet pulls: for every stored handle whose earliest tweet is later than
--since, fetch [since, earliest day] and merge it into that handle's raw file (deduped by id).

    uv run python -m jobs.fill_tweets --dry-run                     # show the plan and cost estimate
    uv run python -m jobs.fill_tweets --limit 2 --max-cost 1        # first batch: 2 smallest gaps
    uv run python -m jobs.fill_tweets --batch-size 8 --max-cost 3   # all gaps, 8 handles per Apify run

Several handles share one Apify run (one `from:` search term each), which avoids the per-run platform
overhead of the one-handle-per-run pull_tweets job. --max-cost is Apify's hard spend cap per run.
Each handle's cap is its projected missing volume plus slack, so a quiet account does not eat the budget.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from jobs.pull_tweets import ACTOR, save
from sources import apify, tweets

COST_PER_TWEET = 0.00025  # upper end of what we have observed (row price plus platform usage)


def gaps(since: date, until_day: date, slack: float, min_cap: int) -> list[dict]:
    """Per handle: earliest stored tweet and a cap sized from its posting rate so far."""
    out = []
    for f in sorted(tweets.RAW.glob("*.jsonl")):
        stamps = []
        for line in f.read_text().splitlines():
            if line.strip():
                stamps.append(parsedate_to_datetime(json.loads(line)["createdAt"]).astimezone(timezone.utc))
        if not stamps:
            continue
        first, last = min(stamps), max(stamps)
        if first.date() <= since + timedelta(days=2):
            continue  # already reaches the window start
        span = max((last - first).days, 1)
        rate = len(stamps) / span
        missing = rate * ((first.date() - since).days)
        out.append({"handle": f.stem, "have": len(stamps), "first": first.date(), "rate": rate,
                    "cap": max(min_cap, math.ceil(missing * slack)), "until": first.date() + timedelta(days=1)})
    return sorted(out, key=lambda g: g["cap"])


def run_batch(batch: list[dict], since: date, max_cost: float) -> dict[str, int]:
    terms = [f"from:{g['handle']} since:{since} until:{g['until']}" for g in batch]
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
    by: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        by[((it.get("author") or {}).get("username") or "").lower()].append(it)
    got = {}
    for g in batch:
        rows = by.get(g["handle"], [])
        if rows:
            save(g["handle"], rows)
        got[g["handle"]] = len(rows)
    return got


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("handles", nargs="*", help="only these handles (default: every short one)")
    ap.add_argument("--since", type=date.fromisoformat, default=date(2026, 9, 1))
    ap.add_argument("--slack", type=float, default=1.2, help="multiplier on the projected missing volume")
    ap.add_argument("--min-cap", type=int, default=60)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--limit", type=int, help="only the N smallest gaps (a cheap first test)")
    ap.add_argument("--max-cost", type=float, default=3.0, help="Apify hard spend cap per run, USD")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    plan = gaps(a.since, datetime.now(timezone.utc).date(), a.slack, a.min_cap)
    if a.handles:
        want = {h.lstrip("@").lower() for h in a.handles}
        plan = [g for g in plan if g["handle"] in want]
    if a.limit:
        plan = plan[: a.limit]
    total = sum(g["cap"] for g in plan)
    print(f"{len(plan)} handles, up to {total} tweets, about ${total * COST_PER_TWEET:.2f} at ${COST_PER_TWEET}/tweet")
    for g in plan:
        print(f"  {g['handle']:<18} have {g['have']:>4} from {g['first']}  ~{g['rate']:.0f}/day  cap {g['cap']}")
    if a.dry_run:
        return
    for i in range(0, len(plan), a.batch_size):
        batch = plan[i:i + a.batch_size]
        print(f"batch {i // a.batch_size + 1}: {[g['handle'] for g in batch]}", flush=True)
        got = run_batch(batch, a.since, a.max_cost)
        for g in batch:
            print(f"  {g['handle']:<18} got {got[g['handle']]:>5} of cap {g['cap']}", flush=True)


if __name__ == "__main__":
    main()
