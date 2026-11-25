"""Williams: product sales lead the FY2025 revenue gain, gas and NGL marketing shrinks in the latest
year-on-year quarter, operating margin reaches its high, and quarterly free cash flow turns negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, without

TICKER = "WMB"
NAMES = {"Non Regulated Service Monetary": "Non-reg. service (monetary)",
         "Non Regulated Service Commodity": "Non-reg. service (commodity)",
         "Energy Commodities": "Energy commodities and service"}
SEGS = {"Transmission Power Gulf": "Transmission, Power & Gulf", "Gas NGL Marketing": "Gas & NGL marketing",
        "Northeast GP": "Northeast G&P"}


def specs(d: Data) -> list[dict]:
    # the energy-commodities line goes negative (FY2024), which a stacked tower cannot draw
    prod = shaped(without(d.history(("ProductOrServiceAxis",)), "Energy Commodities"), NAMES)
    # "Reportable Segment Aggregation..." is a subtotal of the segments, not a segment
    seg_q = shaped(without(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), "Reportable"), SEGS)
    fcf = story.bars("Free cash flow, quarterly", "$M", d.points("Free cash flow, quarterly"))
    if fcf and (neg := sum(1 for _, v in fcf["points"] if v < 0)):
        fcf["tags"] = [{"i": len(fcf["points"]) // 2, "u": 0.8, "text": f"below zero in {neg} of the last {len(fcf['points'])} quarters"}]
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Product", "Non-reg. service (m"])),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Gas & NGL", u=0.55), growth(seg_q, "Transmission", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
