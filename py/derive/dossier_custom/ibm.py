"""IBM: Software grows into the largest and rising share of revenue while Consulting stays flat,
quarterly revenue peaks each fourth quarter, and gross margin rises year by year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "IBM"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Software", "Consulting"])),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["Software", "Consulting"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
