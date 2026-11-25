"""Synopsys: Design Automation jumps in FY2025 while Design IP revenue and operating income fall,
technology services more than double in a year, and operating margin sits in single digits for four quarters."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "SNPS"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Design Automation", "Design IP"])),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Design Automation", "Design IP"])),
        prod_q and story.towers("Same quarter a year apart, by type", prod_q, tags=[growth(prod_q, "Technology")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
