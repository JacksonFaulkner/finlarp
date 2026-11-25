"""MasTec: communications and clean energy lead the growth across four segments, clean energy jumps
again in the latest quarter, annual revenue nearly doubles over five years, and net margin stays thin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import drop, growth, seg_tags, shaped, short, yoy

TICKER = "MTZ"
SHORT = {"Clean Energy and Infrastructure": "Clean energy", "Pipeline Infrastructure": "Pipeline"}


def specs(d: Data) -> list[dict]:
    seg = drop(shaped(d.history(("StatementBusinessSegmentsAxis",))), "All Other")
    seg_q = drop(shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)), "All Other")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Communications", "Clean Energy"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=short([growth(seg_q, "Clean Energy"), yoy(seg_q, "Pipeline", u=0.5)], SHORT)),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Net margin", "%", d.points("Net margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
