"""Modine: data center cooling sales nearly quadruple in two years and lift Climate Solutions revenue
and operating income, but quarterly gross margin slides from the mid-20s to about 21% and the
operating margin dips with it."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, growth, seg_tags, shaped, tagged

TICKER = "MOD"
NAMES = {"Hvac Technologies": "HVAC Technologies",
         "Commercial Heating Ventilation and Air C": "Commercial HVAC"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by end market", prod,
                              tags=seg_tags(prod, ["Data Centers", "On Highway"])),
        seg_q and story.towers("Same quarter a year apart, by segment", seg_q,
                               tags=[growth(seg_q, "Data Center", u=0.6)]),
        oi and story.towers("Segment operating income", oi, tags=[growth(oi, "Climate Solutions", u=0.6)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
