"""UiPath: subscription services grow into the largest line while license revenue stays flat,
operating margin climbs from deep losses to positive in FY2026, and free cash flow turns from burn to
about $350M a year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, pct_tags, seg_tags, shaped, short, tagged

TICKER = "PATH"
SHORT = {"Subscription Services": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Subscription", "License"]), SHORT)),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=short(pct_tags(prod, ["Subscription"]), SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
