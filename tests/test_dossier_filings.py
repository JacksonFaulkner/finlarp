"""Dossier Filings tab: pure text logic on synthetic inputs (no parquet on disk needed)."""
from derive.dossier import Filings
from derive.dossier_tabs import filings as tab


def _filings(by_accn: dict, cik: int | None = 123) -> Filings:
    F = Filings.__new__(Filings)
    F.by_accn = by_accn
    F.cik = cik
    return F


def test_doc_uses_filing_cik_and_falls_back_to_current_cik():
    F = _filings({"0000123-26-000001": (999, "a.htm", "10-K", "2026-01-01")}, cik=123)
    assert tab._doc(F, "0000123-26-000001", "a.htm") == \
        "https://www.sec.gov/Archives/edgar/data/999/000012326000001/a.htm"
    assert tab._doc(F, "0000777-26-000002", "ex21.htm") == \
        "https://www.sec.gov/Archives/edgar/data/123/000077726000002/ex21.htm"
    assert tab._doc(_filings({}, cik=None), "0000777-26-000002", "x.htm") is None


def test_body_skips_headings_and_mda_preamble():
    text = "\n".join([
        "Item 7. Management's Discussion",
        "The following discussion of our financial condition and results of operations should be read in conjunction "
        "with the financial statements and related notes included in this Annual Report on Form 10-K.",
        "•a bullet that is long enough to count as a paragraph of text here for the test",
        "Revenue grew because demand for data center products increased across every end market we serve.",
    ])
    assert tab._body(text).startswith("Revenue grew because")


def test_body_returns_none_without_a_long_paragraph():
    assert tab._body("Competition\nShort line.") is None


def test_opening_sentence_does_not_split_on_abbreviation_inc():
    p = "Marvell Technology, Inc., together with its subsidiaries, is a supplier. We make chips."
    assert tab._opening(p) == "Marvell Technology, Inc., together with its subsidiaries, is a supplier."


def test_excerpt_keeps_short_text_and_cuts_long_text_at_a_sentence():
    assert tab._excerpt("Short text.") == "Short text."
    long = ("First sentence is here and it is reasonably long to start. " * 3 + "x" * 600)
    out = tab._excerpt(long, limit=200)
    assert out.endswith("…") and len(out) <= 205 and out.startswith("First sentence")


def test_going_concern_negated_sentence_is_not_a_warning(monkeypatch):
    neg = "We have concluded that no substantial doubt exists about our ability to continue as a going concern."
    monkeypatch.setattr(tab, "_section_text", lambda con, t, accn, sec: f"Intro line.\n{neg}")
    row, block = tab._going_concern(None, "OKLO", _filings({}), "10-K", "2026-03-01", "acc", "https://x")
    assert block is None
    assert row["value"] == "no doubt language found"
    assert row["src"]["inputs"][0]["url"] == "https://x"


def test_going_concern_warning_becomes_text_block(monkeypatch):
    warn = "The Chapter 11 Cases raise substantial doubt regarding our ability to continue as a going concern."
    monkeypatch.setattr(tab, "_section_text", lambda con, t, accn, sec: f"Other.\n•{warn}" if sec == "risk_factors" else "")
    row, block = tab._going_concern(None, "WOLF", _filings({}), "10-K", "2026-03-01", "acc", "https://x")
    assert row is None
    assert block["type"] == "text" and "Chapter 11" in block["text"]
    assert block["src"]["url"].startswith("https://x#:~:text=The%20Chapter%2011")


def test_exhibit21_junk_filter_drops_headers_and_bare_jurisdictions():
    assert tab._EX21_JUNK.search("Subsidiaries of the Registrant")
    assert tab._EX21_JUNK.search("Taiwan")
    assert tab._EX21_JUNK.search("As of January 31, 2026")
    assert not tab._EX21_JUNK.search("Marvell Technology Japan K.K.")

