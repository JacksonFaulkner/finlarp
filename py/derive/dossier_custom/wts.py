"""Watts Water: the Americas segment carries the growth and most of the operating income while Europe
shrinks, HVAC and Gas leads the latest quarter's year-over-year gain, and operating margin moves up
from the mid-teens to about 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, share, shaped, short, tagged, yoy

TICKER = "WTS"
SHORT = {"Asia Pacific Middle East and Africa": "APMEA",
         "Residential and Commercial Flow Control": "Flow Control"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Americas", "Europe"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "Americas")]),
        prod_q and story.towers("Product lines, same quarter a year apart", prod_q,
                                tags=short([yoy(prod_q, "HVAC", u=0.55), yoy(prod_q, "Residential", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
