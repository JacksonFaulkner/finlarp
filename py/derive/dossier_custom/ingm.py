"""Ingram Micro: FY2025 revenue growth comes mostly from client and endpoint solutions, Asia Pacific
grows fastest in the latest quarter, gross margin edges down on a thin base, and annual free cash
flow swings from a burn to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, growth, seg_tags, shaped, short, tagged

TICKER = "INGM"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by solution", prod,
                              tags=short(seg_tags(prod, ["Client and Endpoint", "Advanced Solutions"]),
                                         {"Client and Endpoint Solutions": "Client/endpoint"})),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "Asia Pacific", u=0.55), growth(geo_q, "North America", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
