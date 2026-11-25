"""PPL: three regulated utilities (Kentucky, Pennsylvania, Rhode Island) with Rhode Island growing
fastest, residential customers the largest and growing class, revenue up since FY2021, and free
cash flow negative and deepening since FY2022."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, short, without

TICKER = "PPL"
SHORT = {"Rhode Island Regulated": "Rhode Island", "Kentucky Regulated": "Kentucky",
         "Pennsylvania Regulated": "Pennsylvania"}


def _fold(hist: dict | None, prefix: str, name: str) -> dict | None:
    """Sum the series whose names start with `prefix` into one series `name` (kept in place)."""
    if not hist:
        return None
    ser, folded, at = [], None, None
    for n, vs in hist["series"]:
        if n.startswith(prefix):
            folded = vs if folded is None else [round(a + b, 1) for a, b in zip(folded, vs)]
            at = len(ser) if at is None else at
        else:
            ser.append([n, vs])
    if folded is not None:
        ser.insert(at, [name, folded])
    return {**hist, "series": ser}


def specs(d: Data) -> list[dict]:
    seg = shaped(without(d.history(("StatementBusinessSegmentsAxis",)), "Corporate"))
    seg_q = shaped(without(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), "Corporate"))
    cust = shaped(_fold(d.history(("MajorCustomersAxis",)), "Wholesale", "Wholesale"))
    fcf = story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual"))
    beats = [
        seg and story.towers("Revenue by regulated utility", seg, tags=short(seg_tags(seg, ["Rhode Island", "Kentucky"]), SHORT)),
        cust and story.towers("Revenue by customer class", cust, tags=seg_tags(cust, ["Residential", "Commercial"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Pennsylvania")], SHORT)),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
