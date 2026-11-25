"""Arista: the Americas carry most of the revenue and growth while EMEA picks up in the latest year,
quarterly revenue climbs every quarter, and operating margin holds in the 40s as gross margin eases."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "ANET"


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Americas", "EMEA"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Americas"), growth(geo_q, "EMEA", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
