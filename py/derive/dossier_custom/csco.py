"""Cisco: security jumps in FY2025 and networking rebounds in FY2026, every region grows, and
operating margin widens from the high teens to about 25% while gross margin stays flat."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "CSCO"
NAMES = {"Europe Middle East and Africa": "EMEA", "Asia Pacific Japan and China": "APJC"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    reg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["Networking", "Security"])),
        reg and story.towers("Revenue by region (segments)", reg, tags=seg_tags(reg, ["Americas"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
