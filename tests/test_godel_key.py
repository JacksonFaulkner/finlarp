from derive import godel_key as gk


def _cmd(cmd="FA", tickers=("AAPL",), period="Q4", year=2023):
    return {"cmd": cmd, "tickers": list(tickers), "period": period, "year": year, "why": "x"}


def test_key_string_full():
    assert gk.key_string(_cmd()) == "AAPL US EQ FA 2023Q4"


def test_key_string_multi_and_no_period():
    assert gk.key_string(_cmd("HMS", ("AAPL", "MSFT"), None, None)) == "AAPL,MSFT US EQ HMS"


def test_key_string_screener_without_ticker():
    assert gk.key_string(_cmd("EQS", (), None, None)) == "- US EQ EQS"


def test_schema_is_strict_and_asks_for_ten():
    props = gk.SCHEMA["properties"]["commands"]
    assert props["minItems"] == props["maxItems"] == 10
    item = props["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {"cmd", "tickers", "period", "year", "why"}
    assert set(item["properties"]["cmd"]["enum"]) == set(gk.NAMES)


def test_parse_rejects_wrong_count_and_ignores_trailing_junk():
    assert gk._parse('{"commands": []}') is None
    ok = '{"commands": [' + ",".join(
        '{"cmd":"DES","tickers":["NVDA"],"period":null,"year":null,"why":"profile"}' for _ in range(10)) + "]} trailing"
    assert len(gk._parse(ok).commands) == 10


def test_add_persists_cooking_then_done(tmp_path, monkeypatch):
    monkeypatch.setattr(gk, "ITEMS", tmp_path / "items.json")
    seen_cooking = []

    def fake_ask(q):
        seen_cooking.append(gk._load()[0]["status"])
        return [{"key": "AAPL US EQ FA", "cmd": "FA", "name": "Financials", "why": "w"}]

    monkeypatch.setattr(gk, "ask", fake_ask)
    item = gk.add("aapl revenue")
    assert seen_cooking == ["cooking"]
    stored = gk._load()
    assert len(stored) == 1 and stored[0]["status"] == "done" and stored[0]["commands"][0]["cmd"] == "FA"
    assert stored[0]["id"] == item["id"]


def test_add_failure_is_recorded_and_keeps_seen_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(gk, "ITEMS", tmp_path / "items.json")

    def boom(q):
        items = gk._load()
        items[0]["seen"] = True  # the TUI marks it while the model is still thinking
        gk._save(items)
        raise RuntimeError("429: slow down")

    monkeypatch.setattr(gk, "ask", boom)
    gk.add("x")
    (it,) = gk._load()
    assert it["status"] == "error" and "429" in it["error"] and it["seen"] is True


def _c(cmd, tickers, period=None, year=None):
    return {"cmd": cmd, "tickers": tickers, "period": period, "year": year, "why": "w"}


def _cov(monkeypatch, quarters, years):
    monkeypatch.setattr(gk, "_coverage", {})
    monkeypatch.setattr(gk, "coverage", lambda t: (quarters, years))


def test_period_dropped_where_command_cannot_take_it(monkeypatch):
    _cov(monkeypatch, set(), set())
    assert gk.normalize(_c("DES", ["AAPL"], "Q4", 2023))["period"] is None
    assert gk.normalize(_c("DES", ["AAPL"], "Q4", 2023))["year"] is None
    assert gk.normalize(_c("N", ["AAPL"], "Q2", 2024))["period"] is None
    assert gk.normalize(_c("CF", ["AAPL"], "Q4", 2023))["period"] is None  # there is no Q4 filing
    assert gk.normalize(_c("CF", ["AAPL"], "Q3", 2023))["period"] == "Q3"
    assert gk.normalize(_c("HDS", ["AAPL"], "Q4", 2023))["period"] == "Q4"


def test_fa_q4_kept_only_when_data_has_it(monkeypatch):
    _cov(monkeypatch, {(2023, 4), (2023, 3)}, {2023})
    assert gk.normalize(_c("FA", ["AAPL"], "Q4", 2023))["period"] == "Q4"
    _cov(monkeypatch, set(), {2022, 2023})  # 20-F filer: annual only
    n = gk.normalize(_c("FA", ["NBIS"], "Q4", 2023))
    assert (n["period"], n["year"]) == ("FY", 2023)
    n = gk.normalize(_c("GR", ["NBIS"], "Q4", 2030))  # not even that year
    assert (n["period"], n["year"]) == (None, None)


def test_ticker_bound_command_without_ticker_is_dropped(monkeypatch):
    _cov(monkeypatch, set(), set())
    assert gk.normalize(_c("FA", [], "FY")) is None
    assert gk.normalize(_c("EQS", [], None))["tickers"] == []


def test_finalize_dedupes_and_tops_up_to_ten(monkeypatch):
    _cov(monkeypatch, set(), {2023})  # NBIS-like: Q4 collapses into FY, and the three Q4 asks into one key
    raw = [_c("FA", ["NBIS"], "Q4", 2023), _c("FA", ["NBIS"], "Q3", 2023), _c("FA", ["NBIS"], "FY", 2023),
           _c("DES", ["NBIS"], "Q4", 2023)]
    out = gk.finalize(raw)
    keys = [c["key"] for c in out]
    assert len(out) == 10 and len(set(keys)) == 10
    assert keys[0] == "NBIS US EQ FA 2023FY" and "NBIS US EQ DES" in keys
    assert not any("Q4" in k for k in keys)


def test_rewritten_period_replaces_stale_explanation(monkeypatch):
    _cov(monkeypatch, set(), {2023})
    n = gk.normalize({**_c("FA", ["NBIS"], "Q4", 2023), "why": "Shows Q4 revenue"})
    assert n["why"] == "Q4 not available here; showing FY"
