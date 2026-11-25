"""Primoris: revenue grows every year to FY2025, led by Energy, and both segments earn more; then the
latest quarter's Energy revenue falls against a year earlier, and quarterly gross and operating
margins slide, the operating margin into a loss."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, growth, seg_tags, shaped, tagged

TICKER = "PRIM"
NAMES = {"U and D": "U&D"}


def specs(d: Data) -> list[dict]:
    # Segment revenue is before intersegment eliminations (about 2% of the total in FY2025).
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Energy", "U&D"])),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Energy", "U&D"])),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Energy", u=0.6), growth(seg_q, "U&D", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
