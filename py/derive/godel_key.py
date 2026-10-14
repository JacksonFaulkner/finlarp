"""Natural-language question -> the ten Godel commands most worth running, as structured output from an OpenAI model.

    uv run python derive/godel_key.py add "aapl q4 performance 2023"   # queue a question; the `godel` TUI screen shows it
    uv run python derive/godel_key.py ask "aapl q4 performance 2023"   # just print the ranked commands as JSON

The reply contract is the pydantic models below (the JSON Schema sent to the Responses API is generated from them, so
the field descriptions are the instructions). A Godel key reads  `AAPL US EQ FA 2023Q4`: tickers, country, asset class,
command, optional period.

`add` persists to <data_dir>/godel/items.json, which the TUI (tui/src/screens/godel.rs) reads and polls: a row appears
as status "cooking" at once and flips to "done" (with its ten commands) or "error". The TUI also writes that file
(seen flags, deletes), so every write here re-reads it first and replaces only the one item.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from enum import StrEnum

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from core.schemas.sentiment import strict_schema
from sources import keys, sec_financials, universe

MODEL = os.environ.get("GODEL_MODEL", os.environ.get("SENTIMENT_MODEL", "gpt-6-luna"))
EFFORT = os.environ.get("GODEL_EFFORT", "none")
URL = "https://api.openai.com/v1/responses"
N_COMMANDS = 10
ITEMS = universe.data_dir("godel") / "items.json"


class Command(StrEnum):
    DES = "DES"
    FA = "FA"
    GR = "GR"
    EVT = "EVT"
    HDS = "HDS"
    CF = "CF"
    N = "N"
    HP = "HP"
    HMS = "HMS"
    EQS = "EQS"


NAMES = {
    "DES": "Description", "FA": "Financials", "GR": "Ratio Analysis", "EVT": "Company Events", "HDS": "Holders",
    "CF": "Filings", "N": "News", "HP": "Historical Prices", "HMS": "Historical Multiple Security", "EQS": "Equity Screener",
}


class Period(StrEnum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    FY = "FY"


# Which periods each command can really take. FA/GR read XBRL, so a quarter must exist in the filer's data (20-F filers
# such as TSM and NBIS have none: FY only). CF is a filing (10-K = FY, 10-Q = Q1-Q3, so never Q4); HDS is a 13F quarter.
# Commands that map to no period reject one outright.
_Q = {"Q1", "Q2", "Q3", "Q4"}
ALLOWED_PERIODS: dict[str, set[str]] = {
    "FA": _Q | {"FY"}, "GR": _Q | {"FY"}, "CF": {"Q1", "Q2", "Q3", "FY"}, "HDS": _Q,
    "DES": set(), "EVT": set(), "N": set(), "HP": set(), "HMS": set(), "EQS": set(),
}
YEAR_COMMANDS = {"FA", "GR", "CF", "HDS", "EVT", "HP", "HMS"}  # DES and EQS are always "latest"
NEEDS_TICKER = set(NAMES) - {"EQS"}


class GodelCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cmd: Command = Field(description=(
        "DES company description and profile. FA financial statements from XBRL (revenue, margins, EPS, cash flow). "
        "GR ratio analysis (margins, ROIC, leverage, derived formulas). EVT company events, 8-Ks, earnings dates, catalysts. "
        "HDS holders: 13F institutions and Form 4 insiders. CF filings: 10-K/20-F/10-Q text, risk factors, MD&A. "
        "N news and tweet stance. HP historical prices and returns. HMS several tickers compared and rebased on one chart. "
        "EQS screen the stock universe by a financial or sector condition"))
    tickers: list[str] = Field(max_length=6, description=(
        "Upper-case ticker symbols this command runs on, taken from the question. Empty only for EQS or when the question "
        "names no company"))
    period: Period | None = Field(description=(
        "Fiscal period the question asks about, or null for the latest. Only FA and GR take Q1-Q4 or FY; CF takes Q1-Q3 "
        "(10-Q) or FY (10-K) and never Q4; HDS takes Q1-Q4 (13F quarter). Always null for DES, EVT, N, HP, HMS and EQS"))
    year: int | None = Field(description=(
        "Four-digit year the question asks about, or null for the latest. Always null for DES and EQS"))
    why: str = Field(max_length=90, description="At most 12 words on what this command shows that answers the question")


class GodelReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commands: list[GodelCommand] = Field(min_length=N_COMMANDS, max_length=N_COMMANDS, description=(
        f"Exactly {N_COMMANDS} commands ranked by how directly they answer the question, best first. The same command may "
        "appear again only with different tickers, period or year (for example FA for Q3 and for Q4). Fill remaining "
        "slots with the most useful neighbouring commands for the same company"))


SYSTEM = """You turn a finance research question into Godel keys, terminal commands over a local SEC and market dataset of
about 430 AI-exposed US stocks. Return the ten commands most worth running, best answer first. Take tickers only from the
question (map company names to their US ticker); never invent a period or year the question does not imply. Follow each
field's description exactly."""

SCHEMA = strict_schema(GodelReply)


def key_string(c: GodelCommand | dict, country: str = "US", asset: str = "EQ") -> str:
    """`AAPL,MSFT US EQ HMS 2023Q4` — tickers, country, asset class, command, then year+period when present."""
    d = c.model_dump(mode="json") if isinstance(c, GodelCommand) else c
    parts = [",".join(d["tickers"]) or "-", country, asset, d["cmd"]]
    when = f"{d.get('year') or ''}{d.get('period') or ''}"
    if when:
        parts.append(when)
    return " ".join(parts)


def _texts(d: dict) -> list[str]:
    if d.get("status") == "incomplete":
        return []
    return [part["text"] for item in d.get("output", []) if item.get("type") == "message"
            for part in item.get("content", []) if part.get("type") == "output_text"]


def _parse(text: str) -> GodelReply | None:
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return GodelReply.model_validate(obj)
    except (ValueError, ValidationError):
        return None


_coverage: dict[str, tuple[set[tuple[int, int]], set[int]]] = {}


def coverage(ticker: str) -> tuple[set[tuple[int, int]], set[int]]:
    """({(fiscal year, quarter 1-4)}, {fiscal years}) with XBRL revenue for this ticker; both empty without data."""
    if ticker not in _coverage:
        try:
            q = {(r["fy"], r["fq"]) for r in sec_financials.quarterly_series(ticker, "revenue") if r.get("fy") and r.get("fq")}
            a = {r["fy"] for r in sec_financials.annual_series(ticker, "revenue") if r.get("fy")}
        except Exception:  # unknown ticker or unreadable cache: treat as no data, never fail the whole question
            q, a = set(), set()
        _coverage[ticker] = (q, a)
    return _coverage[ticker]


def normalize(c: dict) -> dict | None:
    """Drop what the command cannot take and what the data does not have. None = the command is unusable as asked
    (a ticker-bound command with no ticker). Mutates nothing; returns a copy."""
    c = {**c, "tickers": [t.upper().lstrip("$") for t in c["tickers"]]}
    asked = (c["period"], c["year"])
    cmd = c["cmd"]
    if cmd in NEEDS_TICKER and not c["tickers"]:
        return None
    if cmd not in YEAR_COMMANDS:
        c["year"] = None
    if c["period"] not in ALLOWED_PERIODS[cmd]:
        c["period"] = None
    if cmd in ("FA", "GR") and c["period"] and c["tickers"]:
        quarters, years = coverage(c["tickers"][0])
        want = c["year"]
        if c["period"] == "FY":
            if years and want not in years:
                c["year"] = None
        else:
            n = int(c["period"][1])
            have = (want, n) in quarters if want else any(fq == n for _, fq in quarters)
            if not have:  # the quarter is not in the filer's data: fall back to the fiscal year, else to the latest
                c["period"] = "FY" if years and (want is None or want in years) else None
                if c["period"] is None:
                    c["year"] = None
    if asked[0] and (c["period"], c["year"]) != asked:  # the model's explanation described the period it asked for
        c["why"] = f"{asked[0]} not available here" + (f"; showing {c['period']}" if c["period"] else "; showing latest")
    return c


DEFAULT_ORDER = ("DES", "FA", "GR", "EVT", "HDS", "CF", "N", "HP", "HMS", "EQS")


def finalize(raw: list[dict]) -> list[dict]:
    """Normalize, drop duplicate keys, and top up to ten with the standard commands for the lead ticker."""
    out, seen = [], set()
    for c in raw:
        n = normalize(c)
        if n and (k := key_string(n)) not in seen:
            seen.add(k)
            out.append({**n, "key": k, "name": NAMES[n["cmd"]]})
    lead = next((c["tickers"] for c in out if c["tickers"]), [])
    for cmd in DEFAULT_ORDER:
        if len(out) >= N_COMMANDS:
            break
        if cmd != "EQS" and not lead:
            continue
        n = {"cmd": cmd, "tickers": [] if cmd == "EQS" else lead[:1], "period": None, "year": None, "why": "standard follow-up"}
        if (k := key_string(n)) not in seen:
            seen.add(k)
            out.append({**n, "key": k, "name": NAMES[cmd]})
    return out[:N_COMMANDS]


def ask(query: str, retries: int = 3) -> list[dict]:
    """The ten ranked commands for `query`, each {key, cmd, name, tickers, period, year, why}. Raises RuntimeError on failure."""
    body = {
        "model": MODEL, "instructions": SYSTEM, "reasoning": {"effort": EFFORT},
        "input": [{"role": "user", "content": query}],
        "text": {"format": {"type": "json_schema", "name": "godel_keys", "strict": True, "schema": SCHEMA}},
    }
    auth = {"Authorization": f"Bearer {keys.require('OPENAI_API_KEY')}"}
    for _ in range(retries):
        try:
            r = requests.post(URL, json=body, timeout=60, headers=auth)
        except requests.RequestException:
            continue
        if r.status_code in (429, 500, 502, 503):
            continue
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code}: {r.json().get('error', {}).get('message', r.text)[:300]}")
        reply = next((p for t in _texts(r.json()) if (p := _parse(t))), None)
        if reply:
            return finalize([c.model_dump(mode="json") for c in reply.commands])
    raise RuntimeError("no valid reply after retries")


def _load() -> list[dict]:
    try:
        return json.loads(ITEMS.read_text())
    except (FileNotFoundError, ValueError):
        return []


def _save(items: list[dict]) -> None:
    tmp = ITEMS.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False))
    tmp.replace(ITEMS)  # atomic, so the TUI never reads half a file


def _put(item: dict) -> None:
    """Insert (newest first) or replace the item with this id, leaving every other item as the TUI last wrote it."""
    items = _load()
    for i, old in enumerate(items):
        if old["id"] == item["id"]:
            items[i] = {**item, "seen": old.get("seen", False)}
            break
    else:
        items.insert(0, item)
    _save(items)


def add(query: str) -> dict:
    item = {"id": uuid.uuid4().hex[:8], "query": query, "ts": time.strftime("%H:%M:%S"), "status": "cooking",
            "seen": False, "commands": []}
    _put(item)
    try:
        item.update(status="done", commands=ask(query))
    except (RuntimeError, SystemExit) as e:
        item.update(status="error", error=str(e)[:300])
    _put(item)
    return item


def main(argv: list[str]) -> int:
    mode, query = (argv[0], " ".join(argv[1:])) if argv and argv[0] in ("add", "ask") else ("ask", " ".join(argv))
    query = query.strip().lstrip(">").strip()
    if not query:
        print("usage: godel_key.py [add|ask] <question>", file=sys.stderr)
        return 2
    if mode == "add":
        item = add(query)
        if item["status"] == "error":
            print(item["error"], file=sys.stderr)
            return 1
        print(json.dumps(item))
        return 0
    try:
        print(json.dumps({"commands": ask(query)}))
    except (RuntimeError, SystemExit) as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
