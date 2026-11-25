"""Wipro: IT services is essentially all revenue, time-and-materials contracts gain share on
fixed-price ones, annual revenue is flat after FY2023, and operating margin recovers in FY2025.
Figures are INR (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, shaped, share, short, tagged

TICKER = "WIT"
NAMES = {"It Product": "IT products", "Timeandmaterials": "Time-and-materials contracts",
         "Fixedprice": "Fixed-price contracts"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("SegmentConsolidationsAxis",)), NAMES)
    con = shaped(d.history(("TypesOfContractsAxis",)), NAMES)
    unit = (seg or con or {}).get("unit", "INR M")  # the 20-F's currency, from the segment facts
    om = d.points("Operating margin, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short([share(seg, "IT Services")], {"of the total": "of revenue"})),
        con and story.towers("Revenue share by contract type", con, pct=True,
                             tags=short(pct_tags(con, ["Time-and", "Fixed"]),
                                        {" contracts": "", f" ({con['periods'][0]} -> {con['periods'][-1]})": ""})),
        story.bars("Annual revenue", unit, d.points("Annual revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        story.bars("Free cash flow, annual", unit, d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
