"""Tetra Tech: International and State and Local clients grow while Federal Government revenue
falls by about a quarter year over year in the latest quarter, both segments lift operating income,
and the operating margin recovers from a dip in early FY2025 to around 12%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, growth, seg_tags, shaped, tagged, yoy

TICKER = "TTEK"


def specs(d: Data) -> list[dict]:
    cust = shaped(d.history(("MajorCustomersAxis",)))
    cust_q = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        cust and story.towers("Revenue by client type", cust,
                              tags=seg_tags(cust, ["International", "State and Local"])),
        cust_q and story.towers("By client type, same quarter a year apart", cust_q,
                                tags=[growth(cust_q, "Federal", u=0.55), growth(cust_q, "International", u=0.8)]),
        oi and story.towers("Operating income by segment", oi, tags=[yoy(oi, "Government", u=0.55), yoy(oi, "Commercial", u=0.8)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
