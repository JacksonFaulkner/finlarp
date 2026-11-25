"""Global Payments: quarterly revenue jumps by about two thirds from Q1'26, the new Enterprise and
Platforms segments grow several-fold on a year earlier, and operating margin and free cash flow dip
in Q1'26 before recovering."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "GPN"
NAMES = {"Small and Medium Sized Businesses": "Small and medium businesses"}


def specs(d: Data) -> list[dict]:
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, quarterly")
    beats = [
        seg_q and story.towers("Segment revenue, same quarter a year apart", seg_q,
                               tags=seg_tags(seg_q, ["Enterprise", "Platforms"])),
        oi_q and story.towers("Segment operating income, a year apart", oi_q,
                              tags=short([growth(oi_q, "Enterprise", u=0.6), growth(oi_q, "Small", u=0.8)],
                                         {"Small and medium businesses": "SMB"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, quarterly", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
