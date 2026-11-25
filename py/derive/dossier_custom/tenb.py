"""Tenable: subscriptions are nearly all revenue and keep growing while license and maintenance
shrinks, EMEA grows fastest, and free cash flow climbs every year while the GAAP operating margin
only just turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, seg_tags, shaped, short, tagged

TICKER = "TENB"
NAMES = {"Service Other": "Other services"}
SHORT = {"Subscription and Circulation": "Subscription", "License and Maintenance": "License"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    fcf = d.points("Free cash flow, annual")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product / service", prod,
                              tags=short(seg_tags(prod, ["Subscription", "License"]), SHORT)),
        geo and story.towers("Revenue by region", geo, tags=[growth(geo, "EMEA", u=0.55), growth(geo, "Americas", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
