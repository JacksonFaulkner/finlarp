"""Scheduled data refresh: one nightly batch and a short intraday loop.

    uv run python -m jobs.refresh daily                 # after the close: every source, then search + dossiers
    uv run python -m jobs.refresh intraday              # market hours: tweets, sentiment, watchlist news + 8-Ks
    uv run python -m jobs.refresh daily --dry-run       # print the plan
    uv run python -m jobs.refresh daily --only bars,news
    uv run python -m jobs.refresh daily --skip arxiv
    uv run python -m jobs.refresh intraday --force      # run even outside market hours

Steps are grouped in lanes. Lanes run side by side, steps within a lane run in order, so a step can
rely on the one before it. Every SEC puller sits in one lane because SEC's 10 req/s cap is per IP
across all processes. The `final` lane runs after every other lane is done. Each step is its own
process (pullers print and exit freely); one failing step never stops the rest of its lane.

A step whose API key is missing is skipped. Logs go to <DATA_ROOT>/logs/<mode>/<stamp>/<step>.log
(14 days kept), the report to <DATA_ROOT>/debug/refresh_<mode>_<stamp>.json, and a macOS
notification is shown when a step fails. A lock file stops a run from starting while the previous
run of the same mode is still going.

Watchlist (intraday news and 8-Ks): current E*TRADE positions plus data/watchlist.txt (one ticker
per line, # comments), if present.

launchd agents that run these on a schedule: py/jobs/launchd/ (see install.sh there).
"""
from __future__ import annotations

import argparse
import fcntl
import json
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from core import db
from sources import keys, universe

PY = Path(__file__).resolve().parents[1]
ROOT = PY.parent
WATCHLIST = ROOT / "data" / "watchlist.txt"
D = universe.DATA_ROOT
ET = ZoneInfo("America/New_York")
KEEP_LOG_DAYS = 14


def watchlist() -> list[str]:
    syms = {p["symbol"] for p in db.get_cached_positions() or [] if p.get("symbol")}
    if WATCHLIST.exists():
        syms |= {ln.split("#")[0].strip().upper() for ln in WATCHLIST.read_text().splitlines()} - {""}
    have = {s["ticker"] for s in universe.rows()}
    return sorted(syms & have)


def step(lane: str, name: str, script: str, *args: str, needs: str | None = None, timeout_min: int = 120) -> dict:
    """`script` is relative to py/ (a path) or a module (jobs.x)."""
    cmd = [sys.executable, "-m", script] if not script.endswith(".py") else [sys.executable, str(PY / script)]
    return {"lane": lane, "name": name, "cmd": cmd + list(args), "needs": needs, "timeout": timeout_min * 60}


def daily_steps() -> list[dict]:
    return [
        # SEC, one process at a time
        step("sec", "events", "sources/sec_events.py", "ingest", "--refresh", "--max-age", "3600"),
        step("sec", "financials", "sources/sec_financials.py", "ingest", "--new-filings"),
        step("sec", "earnings", "sources/sec_earnings.py", "ingest"),
        step("sec", "segments", "sources/sec_segments.py", "ingest"),
        step("sec", "filing_text", "sources/sec_filing_text.py", "ingest"),  # ingest, then build
        step("sec", "insiders", "sources/sec_insiders.py", "ingest"),  # quarterly sets: no-op until a new one
        step("sec", "13f", "sources/sec_13f.py", "ingest"),
        step("sec", "13f_map", "sources/sec_13f.py", "map"),
        step("sec", "fsds", "sources/edgar_fsds.py", "ingest"),
        # prices and profiles
        step("market", "bars", "sources/databento_bars.py", "pull", "--max-cost", "15", needs="DATABENTO_API_KEY"),
        step("market", "bars_compact", "sources/databento_bars.py", "compact"),
        step("market", "profiles", "sources/yahoo_profile.py"),
        # tweets -> sentiment
        step("tweets", "tweets_pull", "jobs.pull_recent_tweets", "--max-cost", "1", needs="APIFY_TOKEN"),
        step("tweets", "tweets_ingest", "sources/tweets.py", "ingest"),
        step("tweets", "sentiment", "sources/tweet_sentiment.py", "run", "--all", needs="OPENAI_API_KEY"),
        # rate-limited, slow: ~1.5h for the universe at 5 req/min
        step("news", "news", "sources/roic_news.py", "pull", "--universe", "--max-pages", "2", needs="ROIC_TOKEN",
             timeout_min=240),
        step("arxiv", "arxiv", "sources/arxiv.py", "pull", timeout_min=240),
        # after everything above
        step("final", "search", "derive/search.py", "build"),
        step("final", "dossier", "derive/dossier.py", "--all"),
    ]


def intraday_steps() -> list[dict]:
    wl = watchlist()
    out = [
        step("tweets", "tweets_pull", "jobs.pull_recent_tweets", "--max-cost", "0.5", needs="APIFY_TOKEN", timeout_min=20),
        step("tweets", "tweets_ingest", "sources/tweets.py", "ingest"),
        step("tweets", "sentiment", "sources/tweet_sentiment.py", "run", "--all", needs="OPENAI_API_KEY", timeout_min=20),
    ]
    if wl:
        out += [
            step("news", "news", "sources/roic_news.py", "pull", *wl, "--max-pages", "1", needs="ROIC_TOKEN", timeout_min=20),
            step("sec", "events", "sources/sec_events.py", "ingest", *wl, "--refresh", "--max-age", "1200", timeout_min=20),
        ]
    return out


def market_hours(now: datetime) -> bool:
    """Weekdays 08:00-17:00 ET: premarket news through the after-close earnings wave."""
    et = now.astimezone(ET)
    return et.weekday() < 5 and 8 <= et.hour < 17


def run_step(s: dict, log_dir: Path) -> dict:
    t0 = time.time()
    if s["needs"] and not keys.get(s["needs"]):
        return {"step": s["name"], "lane": s["lane"], "status": "skipped", "secs": 0, "detail": f"{s['needs']} not set"}
    log = log_dir / f"{s['name']}.log"
    with log.open("w") as fh:
        fh.write(" ".join(s["cmd"]) + "\n\n")
        fh.flush()
        try:
            rc = subprocess.run(s["cmd"], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=s["timeout"]).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    lines = [ln for ln in log.read_text().splitlines()[2:] if ln.strip()]
    return {"step": s["name"], "lane": s["lane"], "status": "ok" if rc == 0 else "failed",
            "secs": round(time.time() - t0, 1), "detail": (f"exit {rc}: " if rc != 0 else "") + " | ".join(lines[-2:])[:200],
            "log": str(log)}


def run(mode: str, only: set[str], skip: set[str], dry_run: bool, log=print) -> dict:
    steps = [s for s in (daily_steps() if mode == "daily" else intraday_steps())
             if (not only or s["name"] in only) and s["name"] not in skip]
    lanes: dict[str, list[dict]] = {}
    for s in steps:
        lanes.setdefault(s["lane"], []).append(s)
    final = lanes.pop("final", [])
    if dry_run:
        for lane, ss in [*lanes.items(), ("final", final)]:
            for s in ss:
                print(f"  {lane:7} {s['name']:14} {' '.join(Path(c).name if c.startswith('/') else c for c in s['cmd'][1:])[:110]}"
                      + (f"   [needs {s['needs']}{'' if keys.get(s['needs']) else ': NOT SET, will skip'}]" if s["needs"] else ""))
        return {}

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = D / "logs" / mode / stamp
    log_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    lock = threading.Lock()

    def lane_worker(ss: list[dict]) -> None:
        for s in ss:
            log(f"… {s['lane']}/{s['name']}")
            r = run_step(s, log_dir)
            log(f"{'✓' if r['status'] == 'ok' else '-' if r['status'] == 'skipped' else '✗'} {s['lane']}/{s['name']} {r['secs']}s")
            with lock:
                results.append(r)

    t0 = time.time()
    with ThreadPoolExecutor(max(len(lanes), 1)) as pool:
        list(pool.map(lane_worker, lanes.values()))
    lane_worker(final)
    report = {"mode": mode, "started": stamp, "total_secs": round(time.time() - t0, 1), "steps": results}
    (D / "debug").mkdir(parents=True, exist_ok=True)
    (D / "debug" / f"refresh_{mode}_{stamp}.json").write_text(json.dumps(report, indent=1))
    _prune(D / "logs" / mode)
    failed = [r["step"] for r in results if r["status"] == "failed"]
    if failed:
        _notify(f"finlarp {mode} refresh", f"failed: {', '.join(failed)}")
    return report


def _prune(root: Path) -> None:
    cutoff = (datetime.now() - timedelta(days=KEEP_LOG_DAYS)).strftime("%Y%m%d")
    for d in root.iterdir():
        if d.is_dir() and d.name[:8] < cutoff:
            shutil.rmtree(d, ignore_errors=True)


def _notify(title: str, msg: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["osascript", "-e", f"display notification {json.dumps(msg)} with title {json.dumps(title)}"],
                       check=False, capture_output=True)


def print_report(r: dict) -> None:
    print(f"\nrefresh {r['mode']}  ({r['total_secs']}s)")
    for s in r["steps"]:
        mark = {"ok": "✓", "failed": "✗", "skipped": "-"}[s["status"]]
        print(f"  {mark} {s['lane']:7} {s['step']:14} {s['secs']:7.1f}s  {s['detail'][:100]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["daily", "intraday"])
    ap.add_argument("--only", default="", help="comma-separated step names")
    ap.add_argument("--skip", default="", help="comma-separated step names")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="intraday: run outside market hours")
    a = ap.parse_args()
    if a.mode == "intraday" and not (a.force or a.dry_run or market_hours(datetime.now(ET))):
        print("outside market hours (weekdays 08:00-17:00 ET); --force to run anyway")
        return
    split = lambda v: {x.strip() for x in v.split(",") if x.strip()}  # noqa: E731
    (D / "locks").mkdir(parents=True, exist_ok=True)
    with open(D / "locks" / f"refresh_{a.mode}.lock", "w") as lf:
        try:
            fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"a {a.mode} refresh is already running")
            return
        rep = run(a.mode, split(a.only), split(a.skip), a.dry_run,
                  log=lambda m: print(f"{datetime.now():%H:%M:%S} {m}", flush=True))
    if rep:
        print_report(rep)
        sys.exit(1 if any(s["status"] == "failed" for s in rep["steps"]) else 0)


if __name__ == "__main__":
    main()
