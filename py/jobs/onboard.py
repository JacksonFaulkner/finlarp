"""Onboard tickers: add to the universe (if new), run every puller for just
those tickers, build the dossier, and report what is missing and what was slow.

    uv run python py/jobs/onboard.py AAPL SKHY            # already in the universe
    uv run python py/jobs/onboard.py NEWCO --sub cybersecurity   # add first, then onboard
    uv run python py/jobs/onboard.py AAPL --skip patents,bars    # skip steps
    uv run python py/jobs/onboard.py AAPL --force         # redo steps that skip when already done
    uv run python py/jobs/onboard.py AAPL --json          # machine-readable report (nvim)

Steps run in dependency order; one failing step never stops the rest. The report
(also written to <DATA_ROOT>/debug/onboard_<ts>.json) lists, per step, seconds,
status and a one-line detail, then the slowest steps and what each ticker lacks.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import time
import traceback
from datetime import datetime

import duckdb  # type: ignore[import-not-found]

from core import db
from core.schemas.universe import Stock
from sources import universe, yahoo, yahoo_profile

D = universe.DATA_ROOT
DEBUG_DIR = D / "debug"


def _quiet(fn, *a, **kw):
    """Call fn with its stdout captured (pullers print progress per ticker)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn(*a, **kw)
    return out, buf.getvalue()


def _tail(text: str, n: int = 1) -> str:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return " | ".join(lines[-n:])[:160]


def add_to_universe(ticker: str, sub: str) -> str:
    res = yahoo_profile.fetch(yahoo.new_session(), ticker, "quoteType,price,assetProfile")
    if not res:
        raise ValueError(f"{ticker}: Yahoo has no such symbol")
    q = res.get("quoteType", {})
    if q.get("quoteType") != "EQUITY":
        raise ValueError(f"{ticker}: not an equity ({q.get('quoteType')})")
    name = q.get("longName") or q.get("shortName") or ticker
    db.upsert_stock(Stock(
        ticker=ticker, name=name, region="US", subs={sub: 1.0}, eligible=True,
        status="listed_exchange_verified_yahoo", category_confidence="low",
        rationale=f"Added {datetime.now():%Y-%m-%d} via onboard.py. AI materiality not yet verified.",
        source_url=f"https://finance.yahoo.com/quote/{ticker}/", reviewed_on=f"{datetime.now():%Y-%m-%d}"))
    return f"added to {sub}: {name}"


# ---- steps: each takes (tickers, ctx) and returns a detail string ---------------


def s_universe(ts, ctx):
    have = {s["ticker"] for s in universe.rows()}
    new = [t for t in ts if t not in have]
    if new and not ctx.get("sub"):
        raise ValueError(f"{new} not in the universe: pass --sub <sub_sector>")
    msgs = [add_to_universe(t, ctx["sub"]) for t in new]
    ctx["cik"] = {t: (universe.ciks(t) or [None])[0] for t in ts}
    nocik = [t for t, c in ctx["cik"].items() if not c]
    return "; ".join(msgs + ([f"no CIK (non-SEC filer): {nocik}"] if nocik else [])) or "already in universe"


def s_profile(ts, ctx):
    r = yahoo_profile.update(ts)
    return f"{r['fetched']} fetched, missing {r['missing']}"


def s_financials(ts, ctx):
    from sources import sec_financials
    r, _ = _quiet(sec_financials.ingest, ts)
    return json.dumps(r, default=str)[:160]


def s_events(ts, ctx):
    from sources import sec_events
    _, out = _quiet(sec_events.ingest, tickers=ts)  # only these tickers, then rebuilds the parquet
    return _tail(out)


def s_filing_text(ts, ctx):
    from sources import sec_filing_text
    r, out = _quiet(sec_filing_text.ingest, ts)
    if not r.get("ok"):  # nothing new parsed: skip the ~25s global rebuild
        return f"{json.dumps(r, default=str)[:90]}; build skipped"
    b, _ = _quiet(sec_filing_text.build)
    return f"{json.dumps(r, default=str)[:90]}; build {json.dumps(b, default=str)[:60]}"


def s_segments(ts, ctx):
    from sources import sec_segments
    _, out = _quiet(sec_segments.ingest, ts)
    return _tail(out, 2) or "no output"


def s_earnings(ts, ctx):
    from sources import sec_earnings
    r, _ = _quiet(sec_earnings.ingest, ts)
    return json.dumps(r, default=str)[:160]


def s_insiders(ts, ctx):
    from sources import sec_insiders
    with_cik = [t for t in ts if ctx["cik"].get(t)]
    if not with_cik:
        return "skipped: no CIK"
    r = sec_insiders.backfill(with_cik)
    return f"{sum(r.values())} rows over {len(r)} quarters"


def s_13f(ts, ctx):
    from sources import sec_13f
    r, _ = _quiet(sec_13f.build_cusip_map)
    got = duckdb.sql(f"SELECT ticker, method FROM '{sec_13f.DATA_DIR}/cusip_map.parquet'").fetchall()
    have = {t for t, _ in got}
    return f"map methods {r}; unmapped: {[t for t in ts if t not in have]}"


def s_patents(ts, ctx):
    from sources import patents, patents_ai
    q = f"SELECT ticker FROM '{D}/patents/patent_ticker.parquet' WHERE ticker IN ({','.join(repr(t) for t in ts)})"
    have = {r[0] for r in duckdb.sql(q).fetchall()}
    if set(ts) <= have and not ctx.get("force"):  # matching is a ~15s global rebuild
        return "skipped: already matched"
    _quiet(patents.build)
    _quiet(patents_ai.build)
    n = duckdb.sql(f"SELECT ticker, count(*) FROM '{D}/patents/patent_ticker.parquet' WHERE ticker IN "
                   f"({','.join(repr(t) for t in ts)}) GROUP BY 1").fetchall()
    return f"patent rows {dict(n) or 'none matched (add patent_aliases.json?)'}"


def s_tweets(ts, ctx):
    from sources import tweets
    r, _ = _quiet(tweets.ingest)
    return json.dumps(r, default=str)[:120]


def s_bars(ts, ctx):
    from sources import databento_bars
    tables = ["bars_1d"] + (["bars_1m", "quotes_1m"] if ctx.get("all_bars") else [])
    _, out = _quiet(databento_bars.pull, tables, ctx.get("max_cost", 5.0), False)
    return _tail(out, 2)


def s_dossier(ts, ctx):
    from derive import dossier
    out = []
    for t in ts:
        d = dossier.build(t)
        db.put_cached_dossier(t, d)
        bad = [f"{h['section']}:{h['status']}" for h in d["health"] if h["status"] != "ok"]
        ctx.setdefault("health", {})[t] = bad
        out.append(f"{t} {len(d['sections'])} sections" + (f" [{', '.join(bad)}]" if bad else ""))
    return "; ".join(out)


STEPS = [
    ("universe", s_universe), ("profile", s_profile), ("financials", s_financials), ("events", s_events),
    ("filing_text", s_filing_text), ("segments", s_segments), ("earnings", s_earnings),
    ("insiders", s_insiders), ("13f", s_13f), ("patents", s_patents), ("tweets", s_tweets),
    ("bars", s_bars), ("dossier", s_dossier),
]


def run(tickers: list[str], sub: str | None = None, skip: set[str] | frozenset[str] = frozenset(), all_bars: bool = False,
        max_cost: float = 5.0, force: bool = False, log=print) -> dict:
    ts = [t.upper() for t in tickers]
    ctx = {"sub": sub, "all_bars": all_bars, "max_cost": max_cost, "force": force}
    report = {"tickers": ts, "started": datetime.now().isoformat(timespec="seconds"), "steps": []}
    for name, fn in STEPS:
        if name in skip:
            report["steps"].append({"step": name, "status": "skipped", "secs": 0, "detail": ""})
            continue
        log(f"… {name}")
        t0 = time.time()
        try:
            detail, status = fn(ts, ctx), "ok"
        except SystemExit as e:  # some pullers exit() on a refusal (cost cap, dead crumb)
            detail, status = str(e), "failed"
        except Exception as e:  # noqa: BLE001 — keep onboarding the rest
            detail, status = f"{type(e).__name__}: {e}", "failed"
            report.setdefault("tracebacks", {})[name] = traceback.format_exc()
        if name == "universe" and status == "failed":
            report["steps"].append({"step": name, "status": status, "secs": round(time.time() - t0, 1), "detail": detail})
            break  # nothing else makes sense without universe rows
        report["steps"].append({"step": name, "status": status, "secs": round(time.time() - t0, 1), "detail": detail})
    report["health"] = ctx.get("health", {})
    report["total_secs"] = round(sum(s["secs"] for s in report["steps"]), 1)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    (DEBUG_DIR / f"onboard_{datetime.now():%Y%m%d_%H%M%S}.json").write_text(json.dumps(report, indent=1, default=str))
    return report


def print_report(r: dict) -> None:
    print(f"\nonboard {' '.join(r['tickers'])}  ({r['total_secs']}s)")
    for s in r["steps"]:
        mark = {"ok": "✓", "failed": "✗", "skipped": "-"}[s["status"]]
        print(f"  {mark} {s['step']:12} {s['secs']:7.1f}s  {s['detail']}")
    slow = sorted((s for s in r["steps"] if s["status"] == "ok"), key=lambda s: -s["secs"])[:3]
    if slow:
        print("slowest: " + ", ".join(f"{s['step']} {s['secs']:.0f}s" for s in slow))
    for t, bad in r.get("health", {}).items():
        print(f"  {t}: " + (", ".join(bad) if bad else "all dossier sections populated"))


def main(argv: list[str]) -> None:
    def opt(name):
        return next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a == name), None)

    if "--list-subs" in argv:  # for the nvim sub-sector picker
        print(json.dumps([sub for subs in db.taxonomy().values() for sub in subs]))
        return
    values = {opt("--sub"), opt("--skip"), opt("--max-cost")}
    tickers = [a for a in argv if not a.startswith("--") and a not in values]
    if not tickers:
        sys.exit(__doc__)
    rep = run(tickers, sub=opt("--sub"), skip=set((opt("--skip") or "").split(",")) - {""},
              all_bars="--all-bars" in argv, force="--force" in argv, max_cost=float(opt("--max-cost") or 5.0),
              log=(lambda m: None) if "--json" in argv else (lambda m: print(m, file=sys.stderr, flush=True)))
    print(json.dumps(rep, default=str) if "--json" in argv else "", end="" if "--json" in argv else "")
    if "--json" not in argv:
        print_report(rep)


if __name__ == "__main__":
    main(sys.argv[1:])
