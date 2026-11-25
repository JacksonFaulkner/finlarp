"""MYR Group: transmission and distribution and commercial and industrial split revenue, both
segments' operating income dips in FY2024 and recovers in FY2025, commercial and industrial leads
the latest quarter's growth, and quarterly gross and operating margins widen."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, short, tagged

TICKER = "MYRG"
SHORT = {"Transmission and Distribution": "T&D", "Commercial and Industrial": "C&I"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Commercial"]), SHORT)),
        oi and story.towers("Operating income by segment", oi,
                            tags=short([growth(oi, "Commercial", u=0.55), growth(oi, "Transmission", u=0.8)], SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=short(seg_tags(seg_q, ["Commercial", "Transmission"]), SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
