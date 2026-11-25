"""Emerson: Software and Control jumps in FY2024 and takes a larger share next to Intelligent
Devices, keeps growing faster in the latest quarter, and free cash flow rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "EMR"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue by business group", prod, tags=seg_tags(prod, ["Software", "Intelligent"])),
        prod and story.towers("Revenue share by business group", prod, pct=True, tags=pct_tags(prod, ["Software"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Software", u=0.55), growth(prod_q, "Intelligent", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Free cash flow, quarterly", "$M", d.points("Free cash flow, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
