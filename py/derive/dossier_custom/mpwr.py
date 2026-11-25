"""Monolithic Power: China is the largest market and keeps growing, Taiwan more than doubles in a
year, quarterly revenue accelerates, and operating margin steps up from the mid-20s to about 31%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "MPWR"
GEO = {"CN": "China", "TW": "Taiwan", "KR": "Korea", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["China", "Taiwan"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Taiwan"), growth(geo_q, "China", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
