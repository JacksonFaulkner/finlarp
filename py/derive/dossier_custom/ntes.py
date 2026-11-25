"""NetEase: games grow to over four fifths of revenue while innovative businesses shrink, and both
gross and operating margin widen every year. Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "NTES"
NAMES = {"Netease Cloud Music": "NetEase Cloud Music", "Games and Related": "Games",
         "Innovative Businesses": "Innovative businesses"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    unit = (seg or {}).get("unit", "CNY M")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Games", "Innovative"])),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["Games"])),
        story.bars("Annual revenue", unit, d.points("Annual revenue")),
        story.bars("Gross margin, annual", "%", d.points("Gross margin, annual")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
