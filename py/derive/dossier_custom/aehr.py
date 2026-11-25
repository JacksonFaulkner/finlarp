"""Aehr Test: contactor sales fall by more than half, Asia Pacific shrinks while the US grows, revenue
slides for two years and operating margin swings from +20% to deep losses before a Q4'26 rebound."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_low, bars_peak_to_last, pct_tags, seg_tags,
                                         shaped, tagged)

TICKER = "AEHR"
GEO = {"Asiia Paciific": "Asia Pacific", "Uniited States": "United States",
       "Europe and Miiddle East": "Europe and Middle East"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    om_a = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Contactors", "Systems"])),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=pct_tags(geo, ["Asia Pacific", "United States"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om_a), bars_first_to_last(om_a, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om_q), bars_low(om_q, "%"),
               {"i": -1, "u": 0.85, "text": f"{om_q[-1][0]} {om_q[-1][1]:.1f}%"} if om_q else None),
    ]
    return [story.scene(d.name("financials"), beats)]
