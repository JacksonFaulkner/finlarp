"""Celestica: the CCS segment roughly doubles in two years and again year over year in the latest
quarter while ATS stays flat, CCS earns most of the segment profit, and operating margin widens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, share

TICKER = "CLS"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["CCS", "ATS"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "CCS")]),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["CCS"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "CCS"), growth(oi, "CCS", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
