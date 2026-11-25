"""The Trade Desk: non-US revenue grows faster than the US over FY2023-FY2025, but the latest
quarter is up only slightly on a year earlier and its operating margin is lower; free cash flow
keeps rising every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, seg_tags, shaped, tagged

TICKER = "TTD"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Non-US", "US"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
