"""Amkor: advanced products are over four fifths of revenue, the US share rises as Japan and EMEA
shrink, quarterly revenue climbs from its Q1 2025 low, mainstream products grow in the latest quarter, and quarterly gross and operating
margins recover from their Q1 2025 lows."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, share, tagged

TICKER = "AMKR"
GEO = {"JP": "Japan", "Asia Pacific excluding Japan": "Asia Pacific excl. Japan"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product type", prod, tags=[share(prod, "Advanced")]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["US", "Japan"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=seg_tags(prod_q, ["Mainstream", "Advanced"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
