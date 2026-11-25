"""TE Connectivity: Industrial Solutions catches up with Transportation in revenue and grows its
operating income fastest, China becomes the largest region, and operating margin climbs toward 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "TEL"
GEO = {"CN": "China", "US": "US", "CH": "Switzerland", "DE": "Germany"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Industrial", "Transportation"])),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Industrial", u=0.6)]),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["China", "Switzerland"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
