"""Lam Research: systems and customer support both grow, Taiwan's share of revenue nearly doubles
while China's falls, Korea doubles in a year in the latest quarter, and operating margin climbs to
the top of the run."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "LRCX"
NAMES = {"System": "Systems", "Customer Supportand Other": "Customer support and other"}
GEO = {"CN": "China", "TW": "Taiwan", "KR": "Korea", "JP": "Japan", "South East Asia": "Southeast Asia"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Systems", "Customer support"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan", "China"])),
        geo_q and story.towers("By region, same quarter a year apart", geo_q, tags=[growth(geo_q, "Korea")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
