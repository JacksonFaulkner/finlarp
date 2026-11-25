"""Paychex: Management Solutions jumps in FY2026 and carries the revenue step, while PEO and insurance
grows faster in the latest quarter; operating margin eases from its FY2024 high and free cash flow rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "PAYX"
NAMES = {"Peo and Insurance": "PEO and Insurance Solutions"}
SHORT = {"PEO and Insurance Solutions": "PEO & Insurance", "Management Solutions": "Management"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by service line", prod,
                              tags=story.short(seg_tags(prod, ["Management Solutions", "PEO and Insurance"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=story.short([growth(prod_q, "Management Solutions", u=0.6), growth(prod_q, "PEO", u=0.85)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
