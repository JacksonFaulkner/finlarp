"""FIS: Banking Solutions is most of revenue and carries the growth; by Q2'26 Banking is far above
the same quarter a year earlier, lifting quarterly revenue, while margins dip in Q1'26 (gross and
operating alike) before recovering."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "FIS"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Banking", "Capital Market"]),
                                                               {"Capital Market Solutions": "Capital Market"})),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Banking")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
