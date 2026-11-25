"""Applied Optoelectronics: CATV sales roughly quadruple in FY2025 and data center sales more than
double in a year, revenue shifts between Taiwan and China, yet operating margin stays negative every
quarter and free cash flow burns deeper each year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, growth, seg_tags, shaped, tagged

TICKER = "AAOI"
NAMES = {"Ftth and Other": "FTTH and other", "Product and Service Other": "Other"}
GEO = {"CN": "China", "TW": "Taiwan", "US": "United States"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by market", prod, tags=seg_tags(prod, ["CATV", "Data Center"])),
        prod_q and story.towers("Same quarter a year apart, by market", prod_q,
                                tags=[growth(prod_q, "Data Center", u=0.55), growth(prod_q, "CATV", u=0.85)]),
        geo_q and story.towers("Same quarter a year apart, by country", geo_q,
                               tags=[growth(geo_q, "Taiwan", u=0.55), growth(geo_q, "China", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_first_to_last(q, "$M")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
