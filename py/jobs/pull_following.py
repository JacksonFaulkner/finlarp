"""Who do our tracked X accounts follow? Pull each account's following list and rank the overlap.

    uv run python -m jobs.pull_following                      # every handle in the tweet store
    uv run python -m jobs.pull_following dylan522p jukan05 --per-target 500 --max-cost 5
    uv run python -m jobs.pull_following --report             # re-rank the saved pull without spending

Uses Apify xquik/x-follower-scraper (billed per delivered profile, about $0.00015 each). One run in
`merge` mode returns one row per followed profile with `overlapCount` (how many of our accounts follow it)
and `sourceTargets`. Output: following/following.jsonl next to the tweet store. A profile followed by many
of our accounts that we do not store yet is a candidate to add.
"""

from __future__ import annotations

import argparse
import json

import duckdb

from sources import apify, tweets, universe

ACTOR = "AaT0BcKU5GQh97wdt"  # xquik/x-follower-scraper
OUT = universe.data_dir("following") / "following.jsonl"


def tracked_handles() -> list[str]:
    return sorted(f.stem for f in tweets.RAW.glob("*.jsonl"))


def pull(handles: list[str], per_target: int, max_cost: float) -> int:
    run = apify.start_run(ACTOR, {
        "twitterHandles": handles,
        "relation": "following",
        "maxItemsPerTarget": per_target,
        "dedupeMode": "merge",
        "outputMode": "compact",
    }, max_cost_usd=max_cost)
    print(f"run {run['id']} started for {len(handles)} accounts (cap ${max_cost})", flush=True)
    while run["status"] in ("READY", "RUNNING"):
        run = apify.wait_run(run["id"], wait_secs=60)
    print(f"run finished: {run['status']}, cost ${run.get('usageTotalUsd')}")
    rows, offset = [], 0
    while True:
        page = apify.dataset_items(run["defaultDatasetId"], limit=1000, offset=offset)
        rows += page
        if len(page) < 1000:
            break
        offset += 1000
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} rows -> {OUT}")
    return len(rows)


def report(top: int = 60) -> None:
    stored = {h.lower() for h in tracked_handles()}
    con = duckdb.connect()
    cur = con.execute(
        f"SELECT lower(username) h, any_value(name) disp, max(followers) fol, max(overlapCount) overlap, "
        f"any_value(description) bio FROM read_json('{OUT}', format='newline_delimited', ignore_errors=true) "
        f"WHERE overlapCount IS NOT NULL AND lower(username) NOT IN (SELECT unnest($stored)) "
        f"GROUP BY 1 ORDER BY overlap DESC, fol DESC LIMIT {top}", {"stored": sorted(stored)})
    for h, name, fol, ov, bio in cur.fetchall():
        print(f"{ov:>3} {h:<20} {fol or 0:>9,}  {str(name)[:24]:<24} {(bio or '')[:70]!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("handles", nargs="*")
    ap.add_argument("--per-target", type=int, default=500)
    ap.add_argument("--max-cost", type=float, default=5.0, help="hard Apify spend cap for the run, USD")
    ap.add_argument("--report", action="store_true", help="re-rank the saved pull; no spend")
    a = ap.parse_args()
    if not a.report:
        pull([h.lstrip("@") for h in a.handles] or tracked_handles(), a.per_target, a.max_cost)
    report()


if __name__ == "__main__":
    main()
