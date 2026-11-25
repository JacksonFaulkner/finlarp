"""Sterling Infrastructure: E-Infrastructure Solutions grows into most of revenue and operating income,
nearly triples against the same quarter a year earlier, quarterly revenue roughly doubles in a year,
and operating margin rises into the high teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, share, shaped, short, tagged

TICKER = "STRL"
NAMES = {"E Infrastructure": "E-Infrastructure Solutions"}
SHORT = {"E-Infrastructure Solutions": "E-Infrastructure", "Transportation Solutions": "Transportation"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["E-Infrastructure", "Transportation"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "E-Infrastructure")], SHORT)),
        oi and story.towers("Segment operating income", oi, tags=short([share(oi, "E-Infrastructure")], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
