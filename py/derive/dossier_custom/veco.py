"""Veeco: in FY2025 data storage revenue falls by more than half and US and China sales drop while
Asia Pacific outside China grows; quarterly gross and operating margins slide into a small operating
loss, then the latest quarter's revenue jumps with data storage and the US rebounding."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_peak_to_last, bars_swing, bars_year_ago, growth, last_step, shaped,
                                         tagged)

TICKER = "VECO"
GEO = {"Asia Pacific excluding China": "Asia Pacific ex China", "CN": "China", "Rest of World": "Rest of world"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    qgeo = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by market", prod,
                              tags=[last_step(prod, "Data Storage", u=0.6), last_step(prod, "Semiconductor", u=0.85)]),
        geo and story.towers("Revenue by region", geo,
                             tags=[last_step(geo, "Asia Pacific", u=0.6), last_step(geo, "China", u=0.85)]),
        qgeo and story.towers("Revenue by region, same quarter a year apart", qgeo, tags=[growth(qgeo, "US")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
