from derive.filing_search import parse, sec_url


def test_filters_and_words_are_split():
    q = parse('t:intc,mu form:10-q item:5.02 signal:high since:2026 "chief executive" -guidance officer')
    assert q["tickers"] == ["INTC", "MU"]
    assert q["forms"] == ["10-Q"]
    assert q["items"] == ["5.02"]
    assert q["signal"] == "high"
    assert q["since"] == "2026-01-01"
    assert q["phrases"] == ["chief executive"]
    assert q["exclude"] == ["guidance"]
    assert q["words"] == ["officer"]


def test_until_and_month_precision():
    assert parse("until:2026-06")["until"] == "2026-06-01"
    assert parse("since:2026-03-15")["since"] == "2026-03-15"


def test_unknown_signal_is_ignored():
    assert parse("signal:loud")["signal"] is None


def test_index_url_from_cik_and_accession():
    assert sec_url(50863, "0000050863-26-000100") == (
        "https://www.sec.gov/Archives/edgar/data/50863/000005086326000100/0000050863-26-000100-index.htm"
    )
