"""Cerebras: services revenue roughly quadruples year on year while product revenue falls, US revenue
nearly triples, one named customer (OpenAI) is a large share of the latest quarter, and free cash flow
stays deeply negative. Only four quarters of financials are on file."""
from __future__ import annotations

from derive.dossier import _member
from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, shaped

TICKER = "CBRS"
NAMES = {"Other Geographic": "Other"}
CUSTOMER = {"Open AI": "OpenAI"}  # spelling of the counterparty member name


def _top_customer(d: Data, rev: list[list]) -> dict | None:
    """'<customer> $xM, n% of <quarter> revenue' from the latest quarterly CounterpartyNameAxis fact."""
    from sources import sec_segments
    if not rev:
        return None
    row = d.con.execute(f"""
        SELECT member, value FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
        WHERE ticker = ? AND axis ILIKE '%CounterpartyNameAxis' AND concept ILIKE 'Revenue%'
          AND date_diff('day', period_start, period_end) BETWEEN 80 AND 100
        ORDER BY period_end DESC, filing_date DESC NULLS LAST, value DESC LIMIT 1""", [d.t]).fetchone()
    if not row:
        return None
    v = row[1] / 1e6
    name = _member(row[0], "CounterpartyNameAxis")
    return {"i": -1, "u": 0.85,
            "text": f"{CUSTOMER.get(name, name)} ${v:,.1f}M, {v / rev[-1][1] * 100:.0f}% of {rev[-1][0]}"}


def _year_apart(rev: list[list]) -> dict | None:
    """'<latest> vs <same month a year earlier>: +n%' for 'YYYY-MM' labelled quarters."""
    if not rev:
        return None
    lab, b = rev[-1]
    prior = f"{int(lab[:4]) - 1}{lab[4:]}"
    a = next((v for p, v in rev if p == prior), None)
    if not a or a <= 0:
        return None
    return {"i": -1, "u": 0.6, "text": f"{lab} vs {prior}: {(b / a - 1) * 100:+.0f}%"}


def specs(d: Data) -> list[dict]:
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    qb = story.bars("Quarterly revenue", "$M", q)
    tags = [t for t in (_year_apart(q), _top_customer(d, q)) if t]
    if qb and tags:
        qb["tags"], qb["auto_tags"] = tags, False
    # margins left out: Q2 2026 operating margin -265% and Q2 2025 net margin +300% on four quarters
    beats = [
        prod_q and story.towers("Same quarter a year apart: product vs service", prod_q,
                                tags=[growth(prod_q, "Service", u=0.6), growth(prod_q, "Product", u=0.85)]),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "US", u=0.6), growth(geo_q, "EMEA", u=0.85)]),
        qb,
        story.bars("Free cash flow, quarterly", "$M", d.points("Free cash flow, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
