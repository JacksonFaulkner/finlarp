"""Dossier tab: Mine. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Personal and local-only: this ticker's position, FIFO round trips, dividends, notes (mind.duckdb), Godel commands
already generated for it, and watchlist membership when data/watchlist.txt exists. Every value is internal
(src(..., internal=True)); no account ids, account numbers or account-level totals are written.

Reads the derived account parquet (derive/account.py) and the mind/godel files directly, never the broker.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from derive.dossier import _is_new, _money, _pct, src
from mind import store as mind_store
from sources import universe

ACCOUNT = universe.DATA_ROOT / "account"
GODEL_ITEMS = universe.DATA_ROOT / "godel" / "items.json"  # not universe.data_dir(): that mkdirs on read
WATCHLIST = Path(__file__).resolve().parents[3] / "data" / "watchlist.txt"  # same file jobs/refresh.py reads
EPS = 1e-9


# ---- small formatters ------------------------------------------------------

def _day(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _qty(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}" if abs(v - round(v)) < 1e-6 else f"{v:,.4f}".rstrip("0").rstrip(".")


def _usd(v: float | None) -> str:
    return "—" if v is None else f"${v:,.2f}"


def _signed(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{'+' if v >= 0 else '-'}{_money(abs(v))}"


def _own(label: str) -> dict:
    return src(label, None, internal=True)


# ---- pure block builders (take plain rows, return a block or None) ----------

def position_block(p: dict | None) -> dict | None:
    """p: one row of account positions for t (qty, avg_cost, cost_basis, last_price, market_value, ...)."""
    if not p or abs(p.get("qty") or 0) < EPS:
        return None
    cost = p.get("cost_basis")
    pnl = p.get("unrealized_pnl")
    pnl_pct = (pnl / cost * 100) if (pnl is not None and cost) else None
    first, last = _day(p.get("first_entry_date")), _day(p.get("last_entry_date"))
    match = p.get("qty_matches_broker")
    rows = [
        {"label": "Quantity", "value": _qty(p["qty"]), "src": _own("Position · quantity")},
        {"label": "Average cost", "value": _usd(p.get("avg_cost")), "src": _own("Position · avg cost")},
        {"label": "Cost basis", "value": _money(cost), "src": _own("Position · cost basis")},
        {"label": "Last price", "value": _usd(p.get("last_price")), "src": _own("Position · last price")},
        {"label": "Market value", "value": _money(p.get("market_value")), "src": _own("Position · market value")},
        {"label": "Unrealized P&L", "value": f"{_signed(pnl)} ({_pct(pnl_pct)})" if pnl is not None else "—",
         "src": _own("Position · unrealized P&L (broker total gain)")},
        {"label": "Lots", "value": f"{p.get('n_lots') or 0} (first {first or '—'}, last {last or '—'})",
         "new": _is_new(last), "src": _own("Position · FIFO lots")},
        {"label": "Matches broker quantity", "value": "unknown" if match is None else ("yes" if match else "no"),
         "src": _own("Position · reconciliation")},
    ]
    if p.get("as_of"):
        rows.append({"label": "Priced as of", "value": str(_day(p["as_of"]) or p["as_of"]), "src": _own("Position · as_of")})
    return {"type": "kv", "rows": rows}


def round_trip_block(trips: list[dict]) -> dict | None:
    """trips: rows of account round trips for t (lot_id, qty, matched, entry/exit dates and prices, pnl, ret, hold_days)."""
    if not trips:
        return None
    rows = []
    for r in sorted(trips, key=lambda r: (_day(r.get("exit_date")) or date.min, r.get("lot_id") or ""), reverse=True):
        ex = _day(r.get("exit_date"))
        en = _day(r.get("entry_date"))
        pnl, ret, hold = r.get("pnl"), r.get("ret"), r.get("hold_days")
        pnl_s = "—" if pnl is None else _signed(pnl) + ("" if ret is None else f" ({_pct(ret * 100)})")
        rows.append({
            "cells": [str(ex) if ex else "—", str(en) if en else "no matched buy", _qty(r.get("qty")),
                      _usd(r.get("entry_price")), _usd(r.get("exit_price")), pnl_s,
                      "—" if hold is None else f"{hold:.0f}d"],
            "new": _is_new(ex),
            "src": _own(f"Round trip {r.get('lot_id') or ''} (FIFO)"),
        })
    return {"type": "table", "title": f"Round trips, {len(rows)} lots (FIFO)",
            "cols": ["exit", "entry", "qty", "buy", "sell", "P&L", "hold"], "rows": rows}


def dividend_block(cash: list[dict]) -> dict | None:
    """cash: rows of account cash for t with kind == dividend (et_date, amount)."""
    divs = [c for c in cash or [] if (c.get("kind") == "dividend") and c.get("amount") is not None]
    if not divs:
        return None
    divs.sort(key=lambda c: _day(c.get("et_date")) or date.min, reverse=True)
    total = sum(c["amount"] for c in divs)
    rows = [{"cells": [str(_day(c.get("et_date")) or "—"), _usd(c["amount"])],
             "new": _is_new(_day(c.get("et_date"))), "src": _own("Dividend, cash ledger")} for c in divs]
    return {"type": "table", "title": f"Dividends, {len(rows)} payments, total {_usd(total)}",
            "cols": ["paid", "amount"], "rows": rows}


def notes_blocks(notes: list[dict], themes: list[tuple[str, int]], t: str) -> list[dict]:
    """notes: [{id, ts, structured: dict|None}] for ticker t, newest first. themes: [(theme, note count)]."""
    if not notes:
        return []
    last = _day(notes[0].get("ts"))
    out = [{"type": "kv", "rows": [
        {"label": "Notes", "value": str(len(notes)), "src": _own(f"mind.duckdb · notes on ticker:{t}")},
        {"label": "Last note", "value": str(last) if last else "—", "new": _is_new(last),
         "src": _own(f"mind.duckdb · last note on ticker:{t}")},
    ]}]
    follow = []
    for n in notes:
        for q in (n.get("structured") or {}).get("follow_ups") or []:
            if isinstance(q, str) and q.strip():
                d = _day(n.get("ts"))
                follow.append({"cells": [str(d) if d else "—", q.strip()], "new": _is_new(d),
                               "src": _own(f"note {n['id']} · follow-up")})
    if follow:
        out.append({"type": "table", "title": "Follow-ups", "cols": ["note", "follow-up"], "rows": follow})
    if themes:
        out.append({"type": "table", "title": "Note themes", "cols": ["theme", "notes"],
                    "rows": [{"cells": [th, str(n)], "src": _own(f"mind.duckdb · themes on ticker:{t}")}
                             for th, n in themes]})
    return out


def godel_block(items: list[dict], t: str) -> dict | None:
    """items: godel items.json rows. Lists the generated commands (status done) that name ticker t."""
    rows = []
    for it in items or []:
        if it.get("status") != "done":
            continue
        for c in it.get("commands") or []:
            if t in [x.upper() for x in c.get("tickers") or []]:
                when = " ".join(str(x) for x in (c.get("year"), c.get("period")) if x) or "—"
                rows.append({"cells": [c.get("key") or "—", c.get("name") or c.get("cmd") or "—", when],
                             "src": _own(f"godel item {it.get('id')} · {c.get('key')}")})
    if not rows:
        return None
    return {"type": "table", "title": "Godel commands for this ticker", "cols": ["key", "command", "period"],
            "rows": rows}


def watchlist_block(t: str, lines: list[str] | None) -> dict | None:
    """lines: contents of data/watchlist.txt, or None when the file does not exist (then no block)."""
    if lines is None:
        return None
    tickers = {ln.split("#")[0].strip().upper() for ln in lines} - {""}
    return {"type": "kv", "rows": [{"label": "Watchlist", "value": "yes" if t in tickers else "no",
                                    "src": _own("data/watchlist.txt")}]}


# ---- readers ---------------------------------------------------------------

def _account_rows(con, name: str, t: str) -> list[dict]:
    p = ACCOUNT / f"{name}.parquet"
    if not p.exists():
        return []
    cur = con.execute(f"SELECT * FROM '{p}' WHERE symbol = ?", [t])
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _mind(t: str) -> tuple[list[dict], list[tuple[str, int]]]:
    if not mind_store.MIND_PATH.exists():
        return [], []
    eid = f"ticker:{t}"
    con = mind_store.connect(read_only=True)
    try:
        notes = con.execute("""
            SELECT DISTINCT n.id, n.ts, a.structured
            FROM notes n JOIN note_links l ON l.note_id = n.id
            LEFT JOIN answers a ON a.note_id = n.id
            WHERE l.entity_id = ? ORDER BY n.ts DESC""", [eid]).fetchall()
        themes = con.execute("""
            SELECT nt.theme, count(DISTINCT nt.note_id) FROM note_themes nt
            JOIN note_links l ON l.note_id = nt.note_id
            WHERE l.entity_id = ? GROUP BY nt.theme ORDER BY 2 DESC, 1""", [eid]).fetchall()
    finally:
        con.close()
    rows = [{"id": i, "ts": ts, "structured": json.loads(s) if s else None} for i, ts, s in notes]
    return rows, [(th, int(n)) for th, n in themes]


def _godel_items() -> list[dict] | None:
    if not GODEL_ITEMS.exists():
        return None
    return json.loads(GODEL_ITEMS.read_text())


def _watchlist_lines() -> list[str] | None:
    return WATCHLIST.read_text().splitlines() if WATCHLIST.exists() else None


def section(t: str, con, F, prof: dict | None) -> dict | None:
    t = t.upper()
    blocks: list[dict] = []

    positions = _account_rows(con, "positions", t)
    blocks.append(position_block(positions[0] if positions else None))
    blocks.append(round_trip_block(_account_rows(con, "round_trips", t)))
    blocks.append(dividend_block(_account_rows(con, "cash", t)))

    notes, themes = _mind(t)
    blocks.extend(notes_blocks(notes, themes, t))

    items = _godel_items()
    blocks.append(godel_block(items, t) if items else None)
    lines = _watchlist_lines()
    blocks.append(watchlist_block(t, lines))

    blocks = [b for b in blocks if b]
    if not blocks:
        return None
    return {"id": "mine", "title": "Mine", "blocks": blocks}
