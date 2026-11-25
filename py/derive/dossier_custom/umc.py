"""UMC: Taiwan and China take a growing share of revenue while the US share shrinks, revenue peaks
in FY2022, and gross and operating margins fall back from that peak. Figures are NT$ (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "UMC"
UNIT = "NT$M"  # the Financials tab's series are the 20-F's NT$ figures
GEO = {"TW": "Taiwan", "US": "US", "China Includes": "China incl. Hong Kong", "KR": "Korea", "Europe": "Europe",
       "JP": "Japan", "All Other": "Other"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    beats = [
        geo and story.towers("Revenue by customer region", geo, tags=seg_tags(geo, ["Taiwan", "US"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan", "US"])),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, annual")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
