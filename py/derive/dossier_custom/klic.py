"""Kulicke & Soffa: annual revenue halves from FY2022 to FY2025, then quarterly revenue more than
doubles off its low, led by ball bonding equipment, and the quarterly operating margin climbs from a
loss to a solid profit."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_peak_to_last, bars_swing, drop, growth, seg_tags, shaped,
                                         short, tagged)

TICKER = "KLIC"
NAMES = {"Aftermarket Productsand Services": "Aftermarket products and services",
         "Ball Bonding": "Ball bonding equipment", "Wedge Bonding": "Wedge bonding equipment",
         "Advanced Solutions": "Advanced solutions", "All Others": "All others"}
GEO = {"CN": "China", "US": "United States", "TW": "Taiwan", "MY": "Malaysia", "KR": "South Korea",
       "HK": "Hong Kong", "PH": "Philippines", "JP": "Japan", "All Other": "Other"}
SHORT = {"Ball bonding equipment": "Ball bonding", "Advanced solutions": "Advanced"}


def specs(d: Data) -> list[dict]:
    seg = shaped(drop(d.history(("StatementBusinessSegmentsAxis",)), "Unallocated Corporate Expenses"), NAMES)
    seg_q = shaped(drop(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2),
                        "Unallocated Corporate Expenses"), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    # The quarterly operating margin reads +52% then -52% in Q1/Q2 FY2025 (an implausible split of the
    # half-year), so the beat starts after those two quarters.
    om = d.points("Operating margin, quarterly")
    om = om[next((i for i, (p, _) in enumerate(om) if p == "Q3'25"), 0):]
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Ball", "Wedge"]), SHORT)),
        geo and story.towers("Revenue by country", geo, tags=[growth(geo, "China")]),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=short([growth(seg_q, "Ball", u=0.6), growth(seg_q, "Advanced", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
