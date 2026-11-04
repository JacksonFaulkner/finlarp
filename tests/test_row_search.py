from datetime import date

import duckdb
import pytest

from derive.row_search import Col, Dataset, Searcher, fmt, parse


def test_filters_fields_phrases_and_words_split():
    q = parse('t:nvda,amd since:2026 until:2026-06 code:S,P "chief executive" -director huang mgr:x',
              {"code": ("r.code", "eq")})
    assert q["tickers"] == ["NVDA", "AMD"]
    assert q["since"] == "2026-01-01" and q["until"] == "2026-06-01"
    assert q["fields"] == {"code": ["S", "P"]}
    assert q["phrases"] == ["chief executive"]
    assert q["exclude"] == ["director"]
    # an unknown field stays a word rather than silently filtering
    assert q["words"] == ["huang", "mgr:x"]


def test_formatting():
    assert fmt(3_012_345.0, "money") == "$3.0M"
    assert fmt(-2.5e9, "money") == "-$2.5B"
    assert fmt(13_500.0, "num") == "13.5K"
    assert fmt(85.0, "num") == "85"
    assert fmt(223.05, "price") == "223.05"
    assert fmt(date(2026, 9, 23), "date") == "2026-09-23"
    assert fmt(True, "bool") == "yes" and fmt(False, "bool") == ""
    assert fmt(None, "money") == ""


@pytest.fixture()
def toy():
    con = duckdb.connect()
    con.execute("""CREATE TABLE t AS SELECT * FROM (VALUES
        ('NVDA', DATE '2026-09-23', 'S', 'Teter Timothy', 3.0e6, NULL),
        ('NVDA', DATE '2026-03-01', 'P', 'Huang Jen-Hsun', 1.0e6, NULL),
        ('AMD',  DATE '2026-10-01', 'S', 'Su Lisa', 5.0e6, NULL)
    ) v(ticker, filed, code, owner, value, accn)""")
    s = Searcher(con)
    s.sets = {"toy": Dataset("toy", "Toy", "t r",
                             [Col("r.filed", "filed", "date"), Col("r.ticker", "ticker"),
                              Col("r.owner", "owner"), Col("r.value", "value", "money")],
                             "r.filed", ["r.owner"], fields={"code": ("r.code", "eq")})}
    return s


def test_query_filters_and_orders_newest_first(toy):
    out = toy.query("toy", "", 10)
    assert [r["cells"][1] for r in out["rows"]] == ["AMD", "NVDA", "NVDA"]
    assert [r["cells"][2] for r in toy.query("toy", "t:NVDA code:s", 10)["rows"]] == ["Teter Timothy"]
    assert [r["cells"][2] for r in toy.query("toy", "since:2026-06 -su", 10)["rows"]] == ["Teter Timothy"]
    assert [r["cells"][2] for r in toy.query("toy", "huang", 10)["rows"]] == ["Huang Jen-Hsun"]


def test_more_flag_and_detail(toy):
    out = toy.query("toy", "", 2)
    assert out["more"] is True and len(out["rows"]) == 2
    assert ["owner", "Su Lisa"] in out["rows"][0]["detail"]
    assert out["rows"][0]["url"] is None


def test_unknown_dataset_names_the_choices(toy):
    with pytest.raises(KeyError, match="toy"):
        toy.query("nope")
