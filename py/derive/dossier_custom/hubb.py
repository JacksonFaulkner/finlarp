"""Hubbell: Utility Solutions is the larger segment and grows revenue faster over three years, while
Electrical grows operating income faster and leads the same quarter a year apart; operating margin
moves around 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped

TICKER = "HUBB"

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Utility", "Electrical"])),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Utility", "Electrical"])),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Electrical", u=0.8), growth(seg_q, "Utility", u=0.5)]),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
