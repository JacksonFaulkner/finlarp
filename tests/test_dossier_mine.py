"""Dossier tab Mine: pure block builders on synthetic rows, plus one end-to-end run on tmp files."""
import json
from datetime import date, datetime

import duckdb
import pytest

from derive import dossier
from derive.dossier_tabs import mine
from mind import store as mind_store


def _all_internal(block) -> bool:
    items = {"kv": "rows", "table": "rows"}.get(block["type"], "rows")
    return all(r["src"].get("internal") and r["src"].get("url") is None for r in block[items])


def test_position_block_none_without_quantity():
    assert mine.position_block(None) is None
    assert mine.position_block({"qty": 0.0, "cost_basis": 0.0}) is None


def test_position_block_kv_is_internal_and_has_no_account_fields():
    p = {"symbol": "XYZ", "qty": 10.0, "avg_cost": 50.0, "cost_basis": 500.0, "n_lots": 2,
         "first_entry_date": date(2026, 1, 5), "last_entry_date": date(2026, 2, 1), "last_price": 60.0,
         "market_value": 600.0, "unrealized_pnl": 100, "qty_matches_broker": True,
         "as_of": datetime(2026, 10, 28, 12, 0)}
    b = mine.position_block(p)
    assert b["type"] == "kv"
    labels = [r["label"] for r in b["rows"]]
    assert "Quantity" in labels and "Unrealized P&L" in labels
    pnl = next(r for r in b["rows"] if r["label"] == "Unrealized P&L")
    assert pnl["value"].startswith("+$100 (+20.0%)")
    assert _all_internal(b)
    assert "acct" not in json.dumps(b)


def test_round_trip_block_sorted_newest_exit_first_with_unmatched_row():
    trips = [
        {"lot_id": "XYZ-1", "qty": 5, "matched": True, "entry_date": date(2026, 1, 2), "exit_date": date(2026, 3, 1),
         "entry_price": 10.0, "exit_price": 12.0, "pnl": 10.0, "ret": 0.2, "hold_days": 58.0},
        {"lot_id": "XYZ-2", "qty": 3, "matched": False, "entry_date": None, "exit_date": date(2026, 5, 1),
         "entry_price": None, "exit_price": 9.0, "pnl": None, "ret": None, "hold_days": None},
    ]
    b = mine.round_trip_block(trips)
    assert b["type"] == "table" and b["cols"][0] == "exit"
    assert [r["cells"][0] for r in b["rows"]] == ["2026-05-01", "2026-03-01"]
    assert b["rows"][0]["cells"][1] == "no matched buy"
    assert b["rows"][1]["cells"][5].startswith("+$10 (+20.0%)")
    assert b["rows"][1]["cells"][6] == "58d"
    assert _all_internal(b)


def test_round_trip_block_none_when_empty():
    assert mine.round_trip_block([]) is None


def test_dividend_block_total_in_title():
    cash = [{"kind": "dividend", "et_date": date(2026, 2, 10), "amount": 1.5},
            {"kind": "dividend", "et_date": date(2026, 5, 10), "amount": 2.0}]
    b = mine.dividend_block(cash)
    assert "2 payments" in b["title"] and "$3.50" in b["title"]
    assert b["rows"][0]["cells"][0] == "2026-05-10"
    assert _all_internal(b)
    assert mine.dividend_block([]) is None


def test_notes_blocks_counts_follow_ups_and_themes():
    notes = [
        {"id": "n2", "ts": datetime(2026, 10, 1, 9, 0), "structured": {"follow_ups": ["  check capex  ", ""]}},
        {"id": "n1", "ts": datetime(2026, 1, 1, 9, 0), "structured": None},
    ]
    blocks = mine.notes_blocks(notes, [("capex", 2)], "MRVL")
    kv = blocks[0]
    assert kv["rows"][0]["value"] == "2"
    assert kv["rows"][1]["value"] == "2026-10-01"
    follow = next(b for b in blocks if b.get("title") == "Follow-ups")
    assert follow["rows"] == [{"cells": ["2026-10-01", "check capex"], "new": follow["rows"][0]["new"],
                               "src": {"label": "note n2 · follow-up", "url": None, "internal": True}}]
    themes = next(b for b in blocks if b.get("title") == "Note themes")
    assert themes["rows"][0]["cells"] == ["capex", "2"]
    assert all(_all_internal(b) for b in blocks)


def test_notes_blocks_empty():
    assert mine.notes_blocks([], [], "MRVL") == []


def test_godel_block_only_done_items_naming_ticker():
    items = [
        {"id": "a1", "status": "done", "commands": [
            {"key": "MRVL US EQ FA 2025Q4", "cmd": "FA", "name": "Financials", "tickers": ["MRVL"],
             "period": "Q4", "year": 2025},
            {"key": "NVDA US EQ DES", "cmd": "DES", "name": "Description", "tickers": ["NVDA"],
             "period": None, "year": None}]},
        {"id": "b2", "status": "cooking", "commands": [
            {"key": "MRVL US EQ N", "cmd": "N", "name": "News", "tickers": ["MRVL"], "period": None, "year": None}]},
    ]
    b = mine.godel_block(items, "MRVL")
    assert [r["cells"][0] for r in b["rows"]] == ["MRVL US EQ FA 2025Q4"]
    assert b["rows"][0]["cells"][2] == "2025 Q4"
    assert _all_internal(b)
    assert mine.godel_block(items, "AMD") is None
    assert mine.godel_block(None, "MRVL") is None


def test_watchlist_block_missing_file_and_membership():
    assert mine.watchlist_block("MRVL", None) is None
    b = mine.watchlist_block("MRVL", ["MRVL  # core", "NVDA"])
    assert b["rows"][0]["value"] == "yes"
    assert mine.watchlist_block("AMD", ["MRVL"])["rows"][0]["value"] == "no"


@pytest.fixture
def tmp_mine(tmp_path, monkeypatch):
    acct = tmp_path / "account"
    acct.mkdir()
    con = duckdb.connect()
    con.execute(f"""COPY (SELECT 'XYZ' AS symbol, 'h1' AS acct, DATE '2026-03-01' AS exit_date,
                        DATE '2026-01-02' AS entry_date, 5.0 AS qty, true AS matched, 10.0 AS entry_price,
                        12.0 AS exit_price, 10.0 AS pnl, 0.2 AS ret, 58.0 AS hold_days, 'L1' AS lot_id)
                 TO '{acct / 'round_trips.parquet'}' (FORMAT PARQUET)""")
    con.close()
    monkeypatch.setattr(mine, "ACCOUNT", acct)
    monkeypatch.setattr(mine, "GODEL_ITEMS", tmp_path / "godel" / "items.json")
    monkeypatch.setattr(mine, "WATCHLIST", tmp_path / "watchlist.txt")
    # store.py runs ALTER TABLE answers before CREATE TABLE answers, so a brand-new file needs answers made first
    monkeypatch.setattr(mind_store, "MIND_PATH", tmp_path / "mind.duckdb")
    pre = duckdb.connect(str(tmp_path / "mind.duckdb"))
    pre.execute("CREATE TABLE answers (note_id VARCHAR PRIMARY KEY, ts TIMESTAMP DEFAULT now(), body VARCHAR, "
                "model VARCHAR, error VARCHAR)")
    pre.close()
    mind_store.connect().close()  # creates the rest of the schema
    return tmp_path


def test_section_end_to_end_on_tmp_files(tmp_mine):
    con = duckdb.connect()
    s = mine.section("XYZ", con, None, None)
    assert s["id"] == "mine" and s["title"] == "Mine"
    assert [b["type"] for b in s["blocks"]] == ["table"]
    assert dossier.validate({"sections": [s]}) == []
    assert "acct" not in json.dumps(s)


def test_section_with_notes_and_godel(tmp_mine):
    mind_store.add_note("why", anchor_entity="ticker:XYZ")
    nid = mind_store.add_note("another", mentions=["ticker:XYZ"])
    mind_store.save_answer(nid, {"summary": "s", "follow_ups": ["next?"], "themes": ["Capex"]}, "m")
    (tmp_mine / "godel").mkdir()
    (tmp_mine / "godel" / "items.json").write_text(json.dumps([{"id": "g1", "status": "done", "commands": [
        {"key": "XYZ US EQ DES", "cmd": "DES", "name": "Description", "tickers": ["XYZ"], "period": None,
         "year": None}]}]))
    (tmp_mine / "watchlist.txt").write_text("XYZ\n")
    con = duckdb.connect()
    s = mine.section("XYZ", con, None, None)
    titles = [b.get("title") or b.get("type") for b in s["blocks"]]
    assert "kv" in titles and "Follow-ups" in titles and "Note themes" in titles
    assert "Godel commands for this ticker" in titles and "kv" in titles
    assert dossier.validate({"sections": [s]}) == []


def test_section_none_when_nothing_for_ticker(tmp_mine):
    con = duckdb.connect()
    assert mine.section("NOPE", con, None, None) is None
