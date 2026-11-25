"""FormFactor: probe cards carry the growth, the DRAM product group and Taiwan lead the latest quarter's
year-over-year gain, quarterly revenue climbs from its early-2025 low, and gross margin jumps past
50% in the latest quarter (operating margin confirms it). The annual product-group split has a
missing Systems year, so the segment split is used for annual towers."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "FORM"
NAMES = {"Foundry Logic Product Group": "Foundry & Logic", "DRAM Product Group": "DRAM",
         "Systems Product Group": "Systems", "Flash Product Group": "Flash"}
GEO = {"TW": "Taiwan", "KR": "South Korea", "CN": "China", "JP": "Japan", "MY": "Malaysia", "SG": "Singapore"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Probe Cards", "Systems"])),
        prod_q and story.towers("Product groups, same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "DRAM", u=0.55), growth(prod_q, "Foundry", u=0.8)]),
        geo_q and story.towers("Region, same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "Taiwan", u=0.55), growth(geo_q, "South Korea", u=0.8)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Gross margin", "%", gm), bars_year_ago(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
