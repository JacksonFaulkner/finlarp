"""Arrow Electronics: Global Components revenue and operating income drop in FY2024 then recover,
components lead the latest quarter's year-over-year jump, quarterly revenue climbs to about $10B,
and the thin operating margin widens from the low 2s to near 4%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped, tagged, yoy

TICKER = "ARW"
NAMES = {"Global Ecs": "Global ECS"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Global Components", "Global ECS"])),
        oi and story.towers("Segment operating income", oi, tags=[growth(oi, "Global Components")]),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[yoy(seg_q, "Global Components", u=0.55), yoy(seg_q, "Global ECS", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
