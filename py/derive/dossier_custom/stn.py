"""Stantec (C$, annual only): Buildings is the fastest-growing practice, the US grows while Australia
shrinks, revenue rises every year to about C$8.1B, and net margin edges up. Gross margin and free cash
flow stop at FY2023 / FY2022 in the data, so they are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, seg_tags, shaped, tagged

TICKER = "STN"
NAMES = {"Buildings": "Buildings", "Water": "Water", "Environmental": "Environmental",
         "Energy and Resources": "Energy and Resources", "CA": "Canada", "GB": "UK", "AU": "Australia",
         "Other Countries": "Other countries"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("ProductsAndServicesAxis",)), NAMES)
    geo = shaped(d.history(("GeographicalAreasAxis",)), NAMES)
    unit = (seg or geo or {}).get("unit", "C$M")
    rev = d.points("Annual revenue")
    nm = d.points("Net margin, annual")
    beats = [
        seg and story.towers("Revenue by business", seg, tags=seg_tags(seg, ["Buildings", "Infrastructure"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Australia"])),
        tagged(story.bars("Annual revenue", unit, rev), bars_first_to_last(rev, unit)),
        tagged(story.bars("Net margin, annual", "%", nm), bars_first_to_last(nm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
