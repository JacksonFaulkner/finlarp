"""Cirrus Logic: mixed-signal products grow faster than audio, India and Vietnam take share from
China, quarterly revenue peaks every fiscal Q2-Q3, and free cash flow climbs to a high in FY2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, pct_tags, seg_tags, shaped, short, tagged

TICKER = "CRUS"
NAMES = {"CN": "China", "IN": "India", "HK": "Hong Kong", "VN": "Vietnam", "KR": "South Korea"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product line", prod,
                              tags=short(seg_tags(prod, ["High Performance", "Audio"]),
                                         {"High Performance Mixed Signal Products": "Mixed signal", "Audio Products": "Audio"})),
        geo and story.towers("Revenue share by ship-to location", geo, pct=True, tags=pct_tags(geo, ["India", "China"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        story.bars("Operating margin, annual", "%", om),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
