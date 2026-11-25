"""EPAM: revenue returns to growth in FY2025 led by Europe and financial services clients, fixed
price work takes a growing share from time-and-materials, quarterly revenue flattens around $1.4B,
and operating margin settles near 10% after a 15% quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, pct_tags, seg_tags, shaped, tagged

TICKER = "EPAM"
NAMES = {"Business Information": "Business Information and Media",
         "Consumer Goods Retail": "Consumer Goods, Retail and Travel",
         "Time and Materials": "Time and materials", "Fixed Price": "Fixed price"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    ind = shaped(d.history(("EquitySecuritiesByIndustryAxis",)), NAMES)
    price = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",)), NAMES)
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Europe", "Americas"])),
        ind and story.towers("Revenue by client industry", ind, tags=seg_tags(ind, ["Financial Services"])),
        price and story.towers("Revenue share by pricing basis", price, pct=True,
                               tags=pct_tags(price, ["Fixed price"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
