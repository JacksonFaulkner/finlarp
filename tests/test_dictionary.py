from core.schemas import dictionary
from core.schemas.views import VIEW_MODELS


def test_sweep_includes_views():
    keys = dictionary.sweep()
    assert "views.TradingDay" in keys and "views.BarN" in keys


def test_all_view_fields_described():
    missing = [f"{n}.{f}" for n, m in VIEW_MODELS.items() for f, fi in m.model_fields.items() if not fi.description]
    assert not missing


def test_sweep_stats_consistent():
    st = dictionary.sweep_stats()
    assert st["described"] <= st["fields"]
    assert st["models"] == len(dictionary.sweep())
    assert 0 <= st["pct_described"] <= 100
    assert sum(len(m["fields"]) for m in dictionary.sweep().values()) == st["fields"]


def test_coverage_flags(monkeypatch):
    cols = {"trading_days": ["et_date", "n_symbols", "median_close_minute", "is_half_day", "bogus_col"],
            "nomodel": ["a"]}
    cov = dictionary.coverage(cols)
    td = cov["trading_days"]
    assert "bogus_col" in td["undocumented"]
    assert "is_thin_day" in td["stale_in_model"]
    assert "et_date" in td["documented"]
    assert cov["nomodel"] == {"model": None, "undocumented": ["a"]}


def test_comment_fallback():
    f = dictionary.sweep()["canslim.EarningsQuarter"]["fields"]["quarter_end"]
    assert f["source"] == "comment" and "YYYY" in f["description"]


def test_view_notes():
    assert dictionary.view_notes("trading_days")["is_half_day"]
    assert dictionary.view_notes("nope") == {}
