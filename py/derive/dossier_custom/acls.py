"""Axcelis: annual revenue falls two years running as new-system sales shrink, while aftermarket
grows, up about a third on its year-ago quarter; in the latest quarter Asia Pacific grows while
North America shrinks by more than half, and operating margin slides from the low 20s to single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_peak_to_last, growth, seg_tags, shaped, short, tagged)

TICKER = "ACLS"
SHORT = {"New Systems Revenue": "New systems", "After Market": "Aftermarket"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    qgeo = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["New Systems", "After Market"]), SHORT)),
        qprod and story.towers("Revenue by type, same quarter a year apart", qprod,
                               tags=short([growth(qprod, "After Market")], SHORT)),
        qgeo and story.towers("Revenue by region, same quarter a year apart", qgeo,
                              tags=[growth(qgeo, "North America", u=0.6), growth(qgeo, "Asia Pacific", u=0.85)]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
