"""Uber: Mobility and Delivery both grow while Freight stays flat, EMEA is the fastest-growing region,
operating margin rises into the teens, and free cash flow goes from negative to billions a year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "UBER"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Mobility", "Delivery"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA"])),
        oi_q and story.towers("Segment operating income, same quarter a year apart", oi_q,
                              tags=[growth(oi_q, "Mobility"), growth(oi_q, "Delivery", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
