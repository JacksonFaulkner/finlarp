"""Hesai: lidar products are nearly all revenue and grow fast, China's share rises while North
America's falls from FY2023, and the operating margin turns from a loss to a profit in FY2025.
Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, shaped, short, tagged

TICKER = "HSAI"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's CNY figures
NAMES = {"Revenue from Lidar Products": "Lidar products", "CN": "China"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=[growth(prod, "Lidar")]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=short(pct_tags(geo, ["China", "North America"]), {"North America": "N. America"})),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
