"""JOYY: revenue edges down every year, developed countries grow to well over half of it while the
United Arab Emirates and China shrink, and FY2024's operating loss gives way to a small profit."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_low, pct_tags, seg_tags, shaped, short, tagged

TICKER = "JOYY"
GEO = {"AE": "United Arab Emirates", "CN": "China", "Developed Countries": "Developed countries",
       "Southeast Asia and Other": "Southeast Asia and other"}
SHORT = {"United Arab Emirates": "UAE", "Developed countries": "Developed"}


def specs(d: Data) -> list[dict]:
    # 20-F filer: annual figures only. Net margin (98.8% in FY2025) is left out.
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    beats = [
        geo and story.towers("Revenue by region", geo,
                             tags=short(seg_tags(geo, ["Developed", "United Arab"]), SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["Developed", "China"]), SHORT)),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_low(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
