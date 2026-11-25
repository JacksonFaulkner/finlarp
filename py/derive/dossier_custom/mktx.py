"""MarketAxess: commissions are most of revenue, the UK and other non-US regions take a growing
share while US revenue flattens in FY2025, and the operating margin drifts down year after year
even as revenue grows."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, pct_tags, shaped, share, tagged, yoy

TICKER = "MKTX"
NAMES = {"GB": "UK"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=[share(prod, "Commission", u=0.6), yoy(prod, "Technology", u=0.9)]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["US", "UK"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_peak_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
