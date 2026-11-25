"""Applied Materials: Semiconductor Systems is most of revenue and grows steadily, China's share
swings up and back down over three years while Taiwan's rises, and the latest quarter lifts revenue
and operating margin to the top of the run."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "AMAT"
GEO = {"CN": "China", "TW": "Taiwan", "KR": "Korea", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Semiconductor Systems", "Applied Global"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "Taiwan"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Semiconductor Systems")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
