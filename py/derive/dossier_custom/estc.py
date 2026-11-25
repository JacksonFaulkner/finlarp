"""Elastic: SaaS annual-commitment revenue grows about 1.8x in two years toward the size of
self-managed subscriptions, non-US revenue grows faster than US, annual operating margin narrows from
about -20% to about -2%, and free cash flow rises from near zero to over $300M."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "ESTC"
NAMES = {"Saa S Self Managed Annual": "SaaS Self Managed Annual", "Saa S Self Managed Monthly": "SaaS Self Managed Monthly",
         "Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["SaaS Self Managed Annual", "Self Managed Sub"]),
                                                           {"SaaS Self Managed Annual": "SaaS annual", "Self Managed Subscription": "Self-managed"})),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "Non-US", u=0.6), growth(geo_q, "US", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
