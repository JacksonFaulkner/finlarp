"""Honeywell: Aerospace Technologies grows into nearly half of revenue and the largest share of
segment profit while Industrial Automation shrinks in both, and in the latest quarter Industrial
Automation keeps falling as Process Automation grows."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "HON"
NAMES = {"Process Automation and Technology": "Process Automation and Tech."}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    # the quarterly revenue and margin series carry restated / discontinued-ops quarters (Q3 halves),
    # so the story uses annual revenue
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Aerospace", "Industrial Automation"])),
        oi and story.towers("Segment profit", oi, tags=[share(oi, "Aerospace", u=0.55),
                                                        growth(oi, "Industrial Automation", u=0.8)]),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Process Automation", u=0.55), growth(seg_q, "Industrial Automation", u=0.8)]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
    ]
    return [story.scene(d.name("financials"), beats)]
