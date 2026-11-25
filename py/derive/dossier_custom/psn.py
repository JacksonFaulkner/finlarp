"""Parsons: Federal Solutions revenue falls back in FY2025 after its FY2024 jump while Critical
Infrastructure keeps growing and passes it in the latest quarter; total revenue dips from its
FY2024 peak but the operating margin keeps inching up."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, growth, last_step, shaped, tagged)

TICKER = "PSN"
NAMES = {"Federal Solution": "Federal Solutions"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    qseg = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[growth(seg, "Critical", u=0.6), last_step(seg, "Federal", u=0.85)]),
        qseg and story.towers("Revenue by segment, same quarter a year apart", qseg,
                              tags=[growth(qseg, "Critical", u=0.6), growth(qseg, "Federal", u=0.85)]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        story.bars("Free cash flow, annual", "$M", fcf),
    ]
    return [story.scene(d.name("financials"), beats)]
