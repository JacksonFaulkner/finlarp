"""Coinbase: the largest revenue line (tagged bank servicing) jumps in FY2024 and stalls in FY2025,
stablecoin revenue roughly doubles in two years, bank servicing falls against the same quarter a year
earlier, and quarterly revenue slides from its peak as the operating margin turns negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, short

TICKER = "COIN"
NAMES = {"Subscription and Circulation Stablecoin": "Stablecoin subscription and circulation",
         "Subscription and Circulation Blockchain": "Blockchain subscription and circulation",
         "Subscription and Circulation Other": "Other subscription and circulation",
         "Bank Servicing Institutional": "Bank servicing, institutional",
         "Bank Servicing Other": "Bank servicing, other", "Bank Servicing": "Bank servicing",
         "Other Revenue": "Other revenue"}
SHORT = {"Stablecoin subscription and circulation": "Stablecoin", "Bank servicing, institutional": "Institutional"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Stablecoin", "Bank servicing"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Bank servicing"), growth(prod_q, "Bank servicing, inst", u=0.4)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
