"""DigitalOcean: customers spending over $1M a year triple their revenue in two years and Scalers+
(over $100K a year) grows fastest of the spend tiers, the operating margin rises from losses to the high
teens, and gross margin slips back in 2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "DOCN"
AXIS = "MajorCustomersAxis"
# The axis mixes three overlapping splits; each list below is one split that sums to revenue.
TIERS = [("LearnersTestersAndOtherMember", "Learners and testers"), ("BuildersMember", "Builders"),
         ("ScalersMember", "Scalers"), ("ScalersPlusMember", "Scalers+")]
ARR = [("CustomerWithAnnualRunRateAbove6000AndUnder100000Member", "ARR $6K-$100K"),
       ("CustomerWithAnnualRunRateAbove100000AndUnder500000Member", "ARR $100K-$500K"),
       ("CustomerWithAnnualRunRateAbove500000AndUnder1000000Member", "ARR $500K-$1M"),
       ("CustomerWithAnnualRunRateAbove1000000Member", "ARR over $1M")]


def _split(d: Data, members: list[tuple[str, str]], n: int = 3) -> dict | None:
    """Annual revenue for an exact member set of AXIS (private: d.history picks its own partition)."""
    from sources import sec_segments
    rows = d.con.execute(f"""
        SELECT regexp_replace(member, '^[a-z\\-]+:', '') m, period_end, value, accn, concept
        FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
        WHERE ticker = ? AND regexp_replace(axis, '^[a-z\\-]+:', '') = ?
          AND period_start IS NOT NULL AND date_diff('day', period_start, period_end) > 300
          AND concept NOT ILIKE '%OperatingIncome%'
        QUALIFY row_number() OVER (PARTITION BY member, period_end ORDER BY filing_date DESC NULLS LAST, value DESC) = 1
        ORDER BY period_end""", [d.t, AXIS]).fetchall()
    want = dict(members)
    rows = [r for r in rows if r[0] in want]
    ends = sorted({r[1] for r in rows if all((m, r[1]) in {(x[0], x[1]) for x in rows} for m in want)})[-n:]
    if len(ends) < 2:
        return None
    vals = {(r[0], r[1]): r[2] for r in rows}
    return {"axis": AXIS, "periods": [f"FY{pe.year}" for pe in ends], "unit": "$M",
            "series": [[nm, [round(vals[(m, pe)] / 1e6, 1) for pe in ends]] for m, nm in members],
            "srcs": sorted({f"{d.F.form(r[3])} {r[3]} {r[4]}" for r in rows if r[1] in ends})}


def specs(d: Data) -> list[dict]:
    tiers = shaped(_split(d, TIERS))
    arr = shaped(_split(d, ARR))
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, quarterly")
    beats = [
        tiers and story.towers("Revenue by customer spend tier", tiers, tags=seg_tags(tiers, ["Scalers+"])),
        arr and story.towers("Larger customers' revenue by annual run rate", arr,
                             tags=[growth(arr, "ARR over $1M", u=0.55), growth(arr, "ARR $6K", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
        tagged(story.bars("Gross margin", "%", gm), bars_year_ago(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
