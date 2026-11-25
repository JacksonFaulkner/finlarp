"""Kratos: Government Solutions drives the growth and jumps again in the latest quarter, revenue hits a
new high, but operating margin stays in the low single digits and dips below zero, and free cash flow
turns deeply negative in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "KTOS"
NAMES = {"Kratos Government Solutions": "Government Solutions"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Government", "Unmanned"])),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Government"), growth(seg_q, "Unmanned", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
