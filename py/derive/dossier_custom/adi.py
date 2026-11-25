"""Analog Devices: Industrial drops sharply in FY2024 and recovers part of it, the latest quarter shows
Industrial and Communications far above a year earlier, China's share rises, and gross and operating
margins widen quarter after quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "ADI"
GEO = {"CN": "China", "JP": "Japan", "US": "US", "Rest of North and South America": "Rest of Americas"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    mkt_q = shaped(d.history(("RevenueFromContractWithCustomerEndMarketAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by end market", seg, tags=seg_tags(seg, ["Industrial", "Automotive"])),
        mkt_q and story.towers("Same quarter a year apart", mkt_q,
                               tags=[growth(mkt_q, "Industrial"), growth(mkt_q, "Communications", u=0.8)]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
