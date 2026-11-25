"""Bilibili: advertising and mobile games grow fastest, revenue rises every year, gross margin
nearly doubles and the operating margin turns positive in FY2025, and free cash flow swings from
a large burn to a large inflow. Figures are CNY (20-F); the quarterly blocks hold one point per
year, so quarterly beats are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, seg_tags, shaped, short, tagged

TICKER = "BILI"
UNIT = "CNY M"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Advertising", "Mobile Game"]),
                                                                   {"Mobile Game Services": "Mobile games"})),
        tagged(story.bars("Annual revenue", UNIT, rev), bars_first_to_last(rev, UNIT)),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", UNIT, fcf), bars_swing(fcf, UNIT)),
    ]
    return [story.scene(d.name("financials"), beats)]
