"""Silicon Motion: almost all revenue is mobile storage; sales shift toward China (now over half)
while Singapore, Korea and the US shrink, annual revenue recovers from the FY2023 drop, and operating
margin stays far below its FY2021 level. (20-F filer: annual data only.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, growth, pct_tags, shaped, tagged

TICKER = "SIMO"
GEO = {"CN": "China", "JP": "Japan", "SG": "Singapore", "TW": "Taiwan", "KR": "South Korea",
       "US": "United States", "Other Countries": "Other countries"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    beats = [
        geo and story.towers("Revenue by country", geo,
                             tags=[growth(geo, "China", u=0.55), growth(geo, "Singapore", u=0.85)]),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["China"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_swing(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
