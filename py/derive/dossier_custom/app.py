"""AppLovin: revenue outside the US more than triples in two years and keeps pace with the US,
quarterly revenue more than doubles over two years, and operating margin climbs past 75%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "APP"
GEO = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Non-US", "US"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Non-US", u=0.55), growth(geo_q, "US", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Net margin", "%", d.points("Net margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
