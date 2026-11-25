"""Bentley Systems: enterprise and term license subscriptions carry the growth while professional
services shrink, term licenses lead the latest quarter's year-over-year gain, and operating margin
peaks in each first quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, seg_tags, shaped, short, tagged, yoy

TICKER = "BSY"
SHORT = {"Enterprise License Subscriptions": "Enterprise License", "Term License Subscriptions": "Term License"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=short(seg_tags(prod, ["Enterprise License", "Term License"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([yoy(prod_q, "Term License", u=0.55), yoy(prod_q, "Enterprise License", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
