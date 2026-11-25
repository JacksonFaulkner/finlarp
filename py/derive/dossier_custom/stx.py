"""Seagate: sales to OEMs double in two years, the US becomes the largest region, operating margin
climbs from the high teens past 40%, and free cash flow jumps in FY2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "STX"
GEO = {"SG": "Singapore", "NL": "Netherlands"}


def specs(d: Data) -> list[dict]:
    chan = shaped(d.history(("ContractWithCustomerSalesChannelAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        chan and story.towers("Revenue by sales channel", chan, tags=seg_tags(chan, ["OEMs", "Distributors"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["US", "Singapore"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
