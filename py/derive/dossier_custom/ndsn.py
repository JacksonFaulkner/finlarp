"""Nordson: Medical Fluid Systems is the growing segment while Industrial Precision slips in FY2025;
in the latest quarter Advanced Technology Systems leads the gain on a year earlier, and the operating
margin holds in the mid-20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "NDSN"
NAMES = {"Industrial Precisions": "Industrial Precision Solutions"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Medical Fluid", "Industrial Precision"]),
                                                               {"Industrial Precision Solutions": "Industrial Precision"})),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Advanced Technology")],
                                                                         {"Advanced Technology Systems": "Advanced Technology"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
