"""Moody's: Moody's Investors Service grows faster than Moody's Analytics and becomes the larger
segment, transaction revenue takes a bigger share, and the quarterly operating margin rises into
the mid-40s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "MCO"
NAMES = {"Moodys Investors": "Moody's Investors Service", "Moodys Analytics": "Moody's Analytics",
         "Recurring": "Recurring", "Transaction": "Transaction"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    kind = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Moody's Investors", "Moody's Analytics"])),
        kind and story.towers("Recurring vs transaction revenue share", kind, pct=True, tags=pct_tags(kind, ["Transaction"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
