"""HubSpot: subscription revenue grows about 20% a year, Europe grows faster than the Americas, and the
quarterly operating margin turns from losses to a profit in the second half of 2025 while free cash flow
more than triples since FY2021."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, tagged, yoy

TICKER = "HUBS"
NAMES = {"Subscription and Circulation": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Subscription"])),
        geo and story.towers("Revenue by region", geo, tags=[growth(geo, "Europe", u=0.55), yoy(geo, "Americas", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
