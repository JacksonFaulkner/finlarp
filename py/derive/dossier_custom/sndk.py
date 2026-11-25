"""Sandisk: Datacenter goes from a sliver to a quarter of revenue in two years, quarterly revenue
multiplies after mid-2025, gross margin jumps from the 20s to the 80s, and an operating loss quarter
gives way to margins near 80% and positive free cash flow."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "SNDK"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    beats = [
        prod and story.towers("Revenue by end market", prod, tags=seg_tags(prod, ["Datacenter", "Edge"])),
        prod and story.towers("Revenue share by end market", prod, pct=True, tags=pct_tags(prod, ["Datacenter"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
