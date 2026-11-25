"""Hims & Hers: revenue grows more than 8x from FY2021 to FY2025, sales outside the US jump from a sliver
to about a sixth of the latest quarter, and gross margin slides from the high 70s to the mid 60s as
the quarterly operating margin turns negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, growth, shaped, tagged

TICKER = "HIMS"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        geo and story.towers("Revenue by region", geo, tags=[growth(geo, "US", u=0.55), growth(geo, "Non-US", u=0.85)]),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "US", u=0.55), growth(geo_q, "Non-US", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]

