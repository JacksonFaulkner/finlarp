"""onsemi: revenue falls in every segment and end market from FY2023 to FY2025, automotive most, and
operating margin drops to a deep loss in Q1'25; the latest quarter is up on a year earlier, led by
Power Solutions."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "ON"
NAMES = {"Automative": "Automotive"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    mkt = shaped(d.history(("SubsegmentsAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Power Solutions", "Analog Mixed"])),
        mkt and story.towers("Revenue by end market", mkt, tags=[growth(mkt, "Automotive")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Power Solutions")]),
    ]
    return [story.scene(d.name("financials"), beats)]
