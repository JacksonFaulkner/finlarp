"""Centrus: SWU sales carry revenue, Japan becomes a large customer region from FY2024, uranium sales
return in the latest quarter, and operating margin halves from FY2021 with a Q3'25 loss (gross margin
also negative) as quarterly free cash flow turns negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_low, growth, pct_tags, shaped, tagged

TICKER = "LEU"
GEO = {"US": "United States", "JP": "Japan", "NL": "Netherlands", "Other Foreign": "Other foreign"}
NAMES = {"Separative Work Units": "SWU"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om_a = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    fcf_q = d.points("Free cash flow, quarterly")
    beats = [
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["Japan"])),
        prod_q and story.towers("Same quarter a year apart, by product", prod_q,
                                tags=[growth(prod_q, "SWU", u=0.55), growth(prod_q, "Uranium", u=0.85)]),
        story.bars("Quarterly revenue", "$M", q),
        tagged(story.bars("Operating margin, annual", "%", om_a), bars_first_to_last(om_a, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om_q), bars_low(om_q, "%")),
        tagged(story.bars("Free cash flow, quarterly", "$M", fcf_q), story.bars_peak_to_last(fcf_q, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
