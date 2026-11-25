"""Datadog: North America grows faster than international, quarterly revenue passes $1B, operating
margin hovers around zero, and free cash flow rises every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "DDOG"
AX = ("StatementGeographicalAxis",)


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(AX))
    geo_q = shaped(d.history(AX, cadence="quarterly", n=2))
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["North America", "International"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "North America", u=0.6),
                                                                        growth(geo_q, "International", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
