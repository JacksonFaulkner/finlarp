"""Doximity: subscriptions are nearly all revenue and keep growing, quarterly revenue peaks each
fiscal Q3, free cash flow rises every year, and both gross and operating margin step down in the
latest two quarters."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_year_ago, growth, shaped,
                                         share, tagged)

TICKER = "DOCS"
NAMES = {"Service Other": "Service and other"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=[growth(prod, "Subscription", u=0.55), share(prod, "Subscription", u=0.8)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_peak_to_last(om, "%")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
