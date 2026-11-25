"""Rockwell Automation: revenue falls from its FY2023 peak with Software and Control taking most of
the drop in sales and segment profit, then the latest quarter shows Software and Control growing
again and the operating margin climbing into the low 20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "ROK"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Software and Control", "Lifecycle"])),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Software and Control", "Lifecycle"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Software and Control")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
