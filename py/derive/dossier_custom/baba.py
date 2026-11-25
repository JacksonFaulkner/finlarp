"""Alibaba: customer management is the largest revenue line, cloud services grow fastest while
sales of goods shrink, revenue keeps rising, and the operating margin drops in FY2026 after four
years of gains. Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "BABA"
UNIT = "CNY M"  # the 20-F's RMB figures; the segment facts carry a raw unit id
NAMES = {"Customer Management": "Customer management", "Sales of Goods": "Sales of goods",
         "Logistics": "Logistics services", "Cloud": "Cloud services",
         "Membership Fees and Value Added": "Membership and value-added services", "Product and Service Other": "Other"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    if prod:
        prod = {**prod, "unit": UNIT}
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Cloud", "Sales of goods"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Cloud", "Sales of goods"])),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
