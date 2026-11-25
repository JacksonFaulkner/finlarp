"""Spend guard for every paid Databento call: a daily budget, a rate limit and a kill switch.

Every `timeseries.get_range` in the repo goes through `get_range` here. Before the request it
prices the call with `metadata.get_cost` (free), then, under a lock shared by every process:

  - refuses if the kill switch is on;
  - refuses and TRIPS the kill switch if today's spend plus this call would pass the cap
    ($5 a day, ET date; FL_DATABENTO_DAILY_CAP overrides);
  - waits for a slot if more than RATE_PER_MIN paid calls went out in the last minute;
  - books the cost before calling, so concurrent callers can't overshoot together.

The kill switch is sticky: it stays on across days and restarts until someone looks at what
happened and clears it.

    uv run python -m sources.databento_guard            today's spend, cap, kill state
    uv run python -m sources.databento_guard --reset    clear the kill switch

Costs are Databento's pay-as-you-go list prices, so the ledger can only overstate the bill.
State lives in data/databento_spend.json.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from zoneinfo import ZoneInfo

from databento.common.error import BentoClientError, BentoServerError

from sources import universe

LEDGER = universe.DATA_ROOT / "databento_spend.json"
DEFAULT_CAP = 5.0
RATE_PER_MIN = 60
DAYS_KEPT = 30
ET = ZoneInfo("America/New_York")

_thread_lock = threading.Lock()


class DatabentoKilled(RuntimeError):
    """A paid Databento call was refused: the kill switch is on, or would have been tripped."""


def cap() -> float:
    try:
        return float(os.environ.get("FL_DATABENTO_DAILY_CAP", DEFAULT_CAP))
    except ValueError:
        return DEFAULT_CAP


def today() -> str:
    return datetime.now(ET).date().isoformat()


@contextmanager
def _ledger(path: Path | None = None) -> Generator[dict[str, Any]]:
    """The ledger, locked against other threads and processes; written back on exit."""
    path = path or LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock, open(path.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            state: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
        except json.JSONDecodeError:
            # A ledger we can't read must not reset the budget to zero: stop instead.
            state = {"killed": {"at": datetime.now(ET).isoformat(), "reason": f"unreadable ledger {path}"}}
        state.setdefault("days", {})
        state.setdefault("recent", [])
        try:
            yield state
        finally:
            # Written even when the body raises: a refusal must persist the kill switch.
            days = state["days"]
            for old in sorted(days)[:-DAYS_KEPT]:
                del days[old]
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=1))
            tmp.replace(path)


def _day(state: dict[str, Any]) -> dict[str, Any]:
    return state["days"].setdefault(today(), {"spent": 0.0, "calls": 0, "refused": 0})


def charge(cost: float, what: str, path: Path | None = None, now: float | None = None) -> None:
    """Books `cost` against today's budget, or raises DatabentoKilled (tripping the switch when
    the cap is what stops it). Waits while the per-minute rate limit is full."""
    while True:
        with _ledger(path) as state:
            day = _day(state)
            if state.get("killed"):
                day["refused"] += 1
                k = state["killed"]
                raise DatabentoKilled(f"Databento kill switch is on since {k['at']}: {k['reason']} (clear: python -m sources.databento_guard --reset)")
            limit = cap()
            if day["spent"] + cost > limit:
                day["refused"] += 1
                reason = f"{what} would cost ${cost:.4f} with ${day['spent']:.4f} already spent today, over the ${limit:.2f} daily cap"
                state["killed"] = {"at": datetime.now(ET).isoformat(timespec="seconds"), "reason": reason}
                raise DatabentoKilled(f"Databento kill switch tripped: {reason}")
            t = time.time() if now is None else now
            state["recent"] = [x for x in state["recent"] if t - x < 60]
            if len(state["recent"]) < RATE_PER_MIN:
                state["recent"].append(t)
                day["spent"] = round(day["spent"] + cost, 6)
                day["calls"] += 1
                return
            wait = 60 - (t - min(state["recent"]))
        time.sleep(max(wait, 0.05))


def refund(cost: float, path: Path | None = None) -> None:
    """Takes back a booking whose request failed before Databento served anything."""
    with _ledger(path) as state:
        day = _day(state)
        day["spent"] = max(0.0, round(day["spent"] - cost, 6))
        day["calls"] = max(0, day["calls"] - 1)


def remaining(path: Path | None = None) -> float:
    """What is left of today's budget (0 while the kill switch is on)."""
    with _ledger(path) as state:
        if state.get("killed"):
            return 0.0
        return max(0.0, cap() - _day(state)["spent"])


def get_range(client: Any, *, cost: float | None = None, **kw: Any) -> Any:
    """`client.timeseries.get_range(**kw)` behind the guard. `cost` skips the pricing call when
    the caller already priced exactly this request."""
    if cost is None:
        price_kw = {k: kw[k] for k in ("dataset", "symbols", "schema", "start", "end", "stype_in") if k in kw}
        cost = float(client.metadata.get_cost(**price_kw))
    what = f"{kw.get('dataset')} {kw.get('schema')} {kw.get('start')}..{kw.get('end')}"
    charge(cost, what)
    try:
        return client.timeseries.get_range(**kw)
    except (BentoClientError, BentoServerError):
        # Databento answered with an error, so it sent no data and bills nothing. Any other
        # failure (a dropped download) keeps its booking: the guard may overstate, never under.
        refund(cost)
        raise


def status(path: Path | None = None) -> dict[str, Any]:
    with _ledger(path) as state:
        day = dict(_day(state))
        return {"date": today(), "cap": cap(), **day, "killed": state.get("killed")}


def reset(path: Path | None = None) -> None:
    with _ledger(path) as state:
        state.pop("killed", None)


def main() -> None:
    ap = argparse.ArgumentParser(description="Databento spend guard")
    ap.add_argument("--reset", action="store_true", help="clear the kill switch")
    args = ap.parse_args()
    if args.reset:
        reset()
        print("kill switch cleared")
    s = status()
    print(f"{s['date']}: ${s['spent']:.4f} of ${s['cap']:.2f} in {s['calls']} calls, {s['refused']} refused")
    print(f"kill switch: {'ON since ' + s['killed']['at'] + ': ' + s['killed']['reason'] if s['killed'] else 'off'}")


if __name__ == "__main__":
    main()
