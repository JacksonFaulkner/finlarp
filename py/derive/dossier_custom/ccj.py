"""Cameco: uranium is the main consolidated segment and grows, its equity-accounted Westinghouse share
grows faster, revenue more than doubles over five years, and margins climb from breakeven. Figures
are C$ (40-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, seg_tags, shaped, without

TICKER = "CCJ"
UNIT = "C$M"  # the Financials tab's series are the 40-F's C$ figures
SHORT = {"Westinghouse Electric Corporation": "Westinghouse"}


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(without(d.history(("SegmentsAxis",)), "Adjustments"))
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    beats = [
        seg and story.towers("Segment revenue (Westinghouse equity-accounted)", seg,
                             tags=story.short(seg_tags(seg, ["Uranium", "Westinghouse"]), SHORT)),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        _tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm, "%")),
        _tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        story.bars("Free cash flow, annual", UNIT, d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
