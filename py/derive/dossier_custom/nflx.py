"""Netflix: one streaming segment; revenue outside the US is the larger part and grows at the same
pace as the US, operating margin widens from FY2022 on, and free cash flow turns from negative to
billions."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, share

TICKER = "NFLX"


def _us_split(d: Data) -> dict | None:
    """US revenue (the 10-K's only geographic member) and the rest of annual revenue, per fiscal year."""
    from sources import sec_segments

    rows = d.con.execute(f"""
        SELECT year(period_end) AS y, value, accn, concept
        FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
        WHERE ticker = ? AND axis IN ('StatementGeographicalAxis', 'srt:StatementGeographicalAxis',
                                      'us-gaap:StatementGeographicalAxis')
          AND member = 'US' AND period_start IS NOT NULL AND date_diff('day', period_start, period_end) > 300
        QUALIFY row_number() OVER (PARTITION BY period_end ORDER BY filing_date DESC NULLS LAST) = 1
        ORDER BY period_end""", [d.t]).fetchall()
    total = {p: v for p, v in d.points("Annual revenue")}
    keep = [(f"FY{y}", v / 1e6, a, c) for y, v, a, c in rows if f"FY{y}" in total][-5:]
    if len(keep) < 2:
        return None
    return {"periods": [p for p, *_ in keep], "unit": "$M",
            "series": [["US", [round(v, 1) for _, v, *_ in keep]],
                       ["Outside the US", [round(total[p] - v, 1) for p, v, *_ in keep]]],
            "srcs": sorted({f"{d.F.form(a)} {a} {c}" for *_, a, c in keep})}


def specs(d: Data) -> list[dict]:
    geo = _us_split(d)
    beats = [
        geo and story.towers("Revenue, US and outside the US", geo, tags=[share(geo, "Outside", u=0.55), growth(geo, "US", u=0.7)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
