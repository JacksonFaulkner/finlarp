"""Pentair: Pool overtakes Flow as the largest segment and earns the most operating income while
Water Solutions shrinks; Pool then falls against a year earlier in the latest quarter, and annual
gross and operating margins climb from FY2022."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_swing, bars_year_ago, growth, seg_tags, shaped,
                                         share, tagged)

TICKER = "PNR"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Pool", "Water Solutions"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Pool", u=0.55), growth(oi, "Flow", u=0.85)]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Pool", "Water Solutions"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%") or bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
