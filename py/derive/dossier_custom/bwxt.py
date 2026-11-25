"""BWX Technologies: Commercial Operations grows far faster than Government Operations from FY2023 to
FY2025, Canada's share of revenue climbs, quarterly revenue rises year over year, and operating margin
drifts down from the mid-teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, pct_tags, seg_tags, shaped, tagged

TICKER = "BWXT"
GEO = {"CA": "Canada", "Other Geographic": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=seg_tags(seg, ["Commercial Operations", "Government Operations"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Canada", "US"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
