"""F5: product revenue rebounds in FY2025 and keeps growing year on year while service grows
slowly, EMEA rises and Asia Pacific falls in the latest quarter, and free cash flow climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "FFIV"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue: product vs service", prod, tags=seg_tags(prod, ["Product", "Service"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Product", u=0.6), growth(prod_q, "Service", u=0.85)]),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "EMEA", u=0.6), growth(geo_q, "Asia Pacific", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
