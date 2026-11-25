"""Bitdeer: self-mining grows to most of revenue in FY2025 while hosting and subscription lines shrink.
The Financials blocks stop at FY2024 (and the geographic facts cover only part of revenue), so the
story uses the product split alone; margins are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "BTDR"
NAMES = {"AI Cloud": "AI cloud services", "Cloud Hosting": "Other", "Other Revenues": "Other",
         "Electricity Subscription": "Subscriptions", "Hash Rate Subscription": "Subscriptions"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductsAndServicesAxis",)), NAMES)
    beats = [
        prod and story.towers("Revenue by product / service", prod,
                              tags=seg_tags(prod, ["Self Mining", "General Hosting"])),
        prod and story.towers("Revenue share by product / service", prod, pct=True,
                              tags=pct_tags(prod, ["Self Mining", "Subscriptions"])),
    ]
    return [story.scene(d.name("financials"), beats)]
