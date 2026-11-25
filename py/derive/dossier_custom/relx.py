"""RELX: Risk is the largest and growing segment while print shrinks, electronic revenue takes a
larger share, and operating margin widens every year. Figures are GBP (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "RELX"
NAMES = {"Scientific Technical and Medical": "Scientific, Technical and Medical",
         "Print and Print Related": "Print and related"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("SegmentsAxis",)), NAMES)
    fmt = shaped(d.history(("ProductsAndServicesAxis",)))
    unit = (seg or fmt or {}).get("unit", "GBP M")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Risk", "Print"])),
        fmt and story.towers("Revenue share by format", fmt, pct=True, tags=pct_tags(fmt, ["Electronic", "Print"])),
        story.bars("Annual revenue", unit, d.points("Annual revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
