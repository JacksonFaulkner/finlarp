"""Varonis: SaaS goes from a small slice to about three quarters of revenue in three years (nearly all
of the latest quarter) as subscription and
maintenance fade, revenue keeps growing, gross margin steps down through the shift, and operating
losses persist while free cash flow grows."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_year_ago, growth, pct_tags,
                                         shaped, short, tagged)

TICKER = "VRNS"
NAMES = {"Software As A Service": "SaaS"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue share by type", prod, pct=True,
                              tags=short(pct_tags(prod, ["SaaS", "Subscription"]),
                                         {"Subscription and Circulation": "Subscription"})),
        qprod and story.towers("Revenue by type, same quarter a year apart", qprod, tags=[growth(qprod, "SaaS")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        story.bars("Operating margin, quarterly", "%", om),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
