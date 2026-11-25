"""Okta: subscriptions are nearly all revenue and keep growing, quarterly revenue rises every
quarter, the operating margin turns from a loss to double digits, and free cash flow climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, share

TICKER = "OKTA"
NAMES = {"Subscription and Circulation": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=[*seg_tags(prod, ["Subscription"]), share(prod, "Subscription", u=0.4)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
