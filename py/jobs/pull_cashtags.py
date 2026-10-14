"""Pull $CASHTAG tweets (anyone, not just followed accounts) around chosen windows, for bot analysis.

    uv run python -m jobs.pull_cashtags --dry-run
    uv run python -m jobs.pull_cashtags                    # the built-in plan: spike windows + a recent baseline
    uv run python -m jobs.pull_cashtags QUBT --spike-cap 300

Raw JSONL (full author object: account age, followers, following, statuses) goes to cashtags/<TICKER>_<since>.jsonl,
deduped by id, kept apart from the followed-accounts tweet store so it does not flood the `tweets` view.
`until` is exclusive. Apify bills per delivered tweet, so every window has a cap.
"""

from __future__ import annotations

import argparse
import json

from jobs.pull_tweets import ACTOR
from sources import apify, universe

OUT = universe.data_dir("cashtags")

# ticker -> [(since, until, label)]: the biggest unexplained spike days (day before .. day after) and a recent baseline
PLAN = {
    "QUBT": [("2024-11-12", "2024-11-16", "spike"), ("2026-09-27", "2026-10-12", "recent")],
    "RGTI": [("2024-11-22", "2024-11-27", "spike"), ("2026-09-27", "2026-10-12", "recent")],
    "RCAT": [("2024-11-19", "2024-11-22", "spike"), ("2026-09-27", "2026-10-12", "recent")],
    "BBAI": [("2024-08-20", "2024-08-23", "spike"), ("2026-09-27", "2026-10-12", "recent")],
    "SERV": [("2024-07-18", "2024-07-23", "spike"), ("2026-09-27", "2026-10-12", "recent")],
    "RXRX": [("2026-09-29", "2026-10-10", "spike"), ("2025-10-14", "2025-10-17", "spike")],
}


def pull(ticker: str, since: str, until: str, cap: int) -> int:
    items = apify.run_actor(
        ACTOR, {"mode": "search", "searchTerms": [f"${ticker} since:{since} until:{until}"], "maxItems": cap}, timeout=280)
    f = OUT / f"{ticker}_{since}.jsonl"
    seen = {}
    if f.exists():
        seen = {str(json.loads(line)["id"]): json.loads(line) for line in f.read_text().splitlines() if line.strip()}
    n0 = len(seen)
    seen.update({str(r["id"]): r for r in items if r.get("id")})
    f.write_text("".join(json.dumps(r) + "\n" for r in seen.values()))
    return len(seen) - n0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--spike-cap", type=int, default=600)
    ap.add_argument("--recent-cap", type=int, default=400)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    plan = {t: w for t, w in PLAN.items() if not a.tickers or t in {x.upper() for x in a.tickers}}
    jobs = [(t, s, u, a.recent_cap if lab == "recent" else a.spike_cap, lab) for t, ws in plan.items() for s, u, lab in ws]
    print(f"{len(jobs)} windows, up to {sum(j[3] for j in jobs)} tweets (about ${sum(j[3] for j in jobs) * 0.00025:.2f})")
    for t, s, u, cap, lab in jobs:
        print(f"  ${t:<5} {s}..{u} {lab:<6} cap {cap}")
        if not a.dry_run:
            print(f"    -> {pull(t, s, u, cap)} new tweets", flush=True)


if __name__ == "__main__":
    main()
