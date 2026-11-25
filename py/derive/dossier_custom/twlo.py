"""Twilio: messaging is the largest product and adds the most revenue, quarterly revenue climbs,
gross margin edges down while the operating margin turns from break-even to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "TWLO"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Messaging", "Programmable Voice"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
