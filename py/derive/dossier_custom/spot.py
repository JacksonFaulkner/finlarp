"""Spotify: Premium carries the growth while ad-supported revenue stalls, and the margins turn: the
operating margin goes from a loss to double digits and free cash flow multiplies. Figures are EUR (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "SPOT"
UNIT = "EUR M"  # the Financials tab's series are the 20-F's EUR figures


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("SegmentsAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Premium", "Ad Supported"])),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Gross margin, annual", "%", d.points("Gross margin, annual")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow, annual", UNIT, d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
