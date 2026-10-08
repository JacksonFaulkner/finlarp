"""The ai_stocks.json universe, resolved to SEC CIKs.

cik_aliases.json maps a ticker to predecessor CIKs whose filings are the
same business under an older registrant (MRVL's pre-2021 history lives
under the Bermuda parent, 1058057). `ciks(ticker)` returns current first.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from core import db
from sources import sec_http

ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_PATH = ROOT / "data" / "ai_stocks.json"
ALIASES_PATH = ROOT / "data" / "cik_aliases.json"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
DATA_ROOT = db.DB_PATH.parent / "finlarp"

_cik_map: dict[str, int] | None = None


def data_dir(source: str) -> Path:
    """~/.local/share/nvim/finlarp/<source>/ — one dir per puller."""
    d = DATA_ROOT / source
    d.mkdir(parents=True, exist_ok=True)
    return d


def submissions(cik: int, max_age_s: float = 86400) -> dict:
    """data.sec.gov submissions JSON with `filings.recent` merged with any
    overflow pages into one columnar dict, disk-cached for max_age_s.
    Shared by pullers so each company's index is fetched once a day."""
    path = data_dir("submissions") / f"{cik}.json"
    if path.exists() and time.time() - path.stat().st_mtime < max_age_s:
        return json.loads(path.read_text())
    resp = sec_http.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    resp.raise_for_status()
    sub = resp.json()
    recent = sub["filings"]["recent"]
    for page in sub["filings"].get("files", []):
        extra = sec_http.get(f"https://data.sec.gov/submissions/{page['name']}").json()
        for k in recent:
            recent[k] = recent[k] + extra.get(k, [])
    sub["filings"]["files"] = []
    tmp = path.with_suffix(f".{os.getpid()}.part")
    tmp.write_text(json.dumps(sub))
    tmp.rename(path)
    return sub


def _cik_lookup() -> dict[str, int]:
    global _cik_map
    if _cik_map is None:
        resp = sec_http.get(TICKERS_URL)
        resp.raise_for_status()
        _cik_map = {v["ticker"].upper(): v["cik_str"] for v in resp.json().values()}
    return _cik_map


def aliases() -> dict[str, list[int]]:
    if not ALIASES_PATH.exists():
        return {}
    return {k: v for k, v in json.loads(ALIASES_PATH.read_text()).items() if not k.startswith("_")}


def ciks(ticker: str) -> list[int]:
    """Current CIK first, then predecessors. Empty for non-SEC filers
    (foreign listings, unsponsored OTC ADRs)."""
    cur = _cik_lookup().get(ticker.upper())
    out = [cur] if cur else []
    return out + [c for c in aliases().get(ticker.upper(), []) if c not in out]


def stocks() -> list[dict]:
    """Universe entries with `cik` (current or None) and `ciks` (all)."""
    out = []
    for s in json.loads(UNIVERSE_PATH.read_text())["stocks"]:
        cs = ciks(s["ticker"])
        out.append(s | {"cik": cs[0] if cs else None, "ciks": cs})
    return out


if __name__ == "__main__":
    ss = stocks()
    missing = [s["ticker"] for s in ss if s["cik"] is None]
    print(f"{len(ss)} stocks, {len(ss) - len(missing)} with CIK, {len(missing)} without:")
    print(" ".join(missing))
