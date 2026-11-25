"""STMicroelectronics: revenue peaks in FY2023 and falls two years running, EMEA shrinks most,
Power and Discrete swings to an operating loss, and the annual operating margin nearly vanishes."""
from __future__ import annotations

from derive.dossier import _member
from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "STM"
NAMES = {"Analog Products MEMS": "Analog, MEMS and Sensors", "R F Optical": "RF and Optical Communications",
         "RF Optical": "RF and Optical Communications"}
AXIS = "StatementBusinessSegmentsAxis"


def _segment_oi(d: Data, n: int = 3) -> dict | None:
    """Annual segment operating income by member. Data.history(oi=True) needs segment revenue for
    the same members, which STM's 20-F does not tag, so read the OI facts directly."""
    from sources import sec_segments
    rows = d.con.execute(f"""
        SELECT member, period_end, value, accn, concept
        FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
        WHERE ticker = ? AND axis IN ('{AXIS}', 'srt:{AXIS}', 'us-gaap:{AXIS}')
          AND period_start IS NOT NULL AND date_diff('day', period_start, period_end) > 300
          AND concept ILIKE '%OperatingIncome%'
        QUALIFY row_number() OVER (PARTITION BY member, period_end ORDER BY filing_date DESC NULLS LAST) = 1
        ORDER BY period_end""", [d.t]).fetchall()
    ends = sorted({r[1] for r in rows})[-n:]
    if len(ends) < 2:
        return None
    vals = {(m, pe): v for m, pe, v, *_ in rows}
    last = sorted({m for m, pe, *_ in rows if pe == ends[-1]}, key=lambda m: -(vals.get((m, ends[0])) or 0))
    return {"axis": AXIS, "periods": [f"FY{pe.year}" for pe in ends], "unit": "$M",
            "series": [[_member(m, AXIS), [round((vals.get((m, pe)) or 0) / 1e6, 1) for pe in ends]] for m in last],
            "srcs": sorted({f"{d.F.form(a)} {a} {c}" for m, pe, _, a, c in rows if pe in ends})}


def _loss_tag(hist: dict | None) -> list[dict]:
    """The segments whose latest operating income is a loss (towers draw losses as 0)."""
    if not hist:
        return []
    return [{"i": -1, "s": k, "u": 0.75,
             "text": f"{nm.removesuffix(' Products')} loss {story._money(-vs[-1], hist['unit'])} in {hist['periods'][-1]}"}
            for k, (nm, vs) in enumerate(hist["series"]) if vs[-1] < 0][:1]


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    oi = shaped(_segment_oi(d), NAMES)
    beats = [
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA", "Asia"])),
        oi and story.towers("Segment operating income", oi, tags=_loss_tag(oi)),
        story.bars("Gross margin, annual", "%", d.points("Gross margin, annual")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
