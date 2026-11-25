"""Pinterest: revenue outside the US and Canada grows fastest, so Europe and Rest of World take a
larger share, quarterly revenue peaks each fourth quarter, and operating margin is only solidly
positive in those fourth quarters."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, pct_tags, seg_tags, shaped, short, tagged, yoy

TICKER = "PINS"
SHORT = {"United States and Canada": "US and Canada"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Rest of World", "Europe"])),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["United States", "Rest of World"]), SHORT)),
        geo_q and story.towers("Same quarter a year apart", geo_q,
                               tags=short([yoy(geo_q, "Rest of World", u=0.55), yoy(geo_q, "United States", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
