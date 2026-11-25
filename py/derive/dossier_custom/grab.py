"""Grab: deliveries, mobility and financial services all grow, financial services fastest, Malaysia
overtakes the other markets, annual revenue climbs every year, and operating margin goes from deep
losses to slightly positive in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, tagged

TICKER = "GRAB"
GEO = {"MY": "Malaysia", "SG": "Singapore", "ID": "Indonesia", "PH": "Philippines", "TH": "Thailand",
       "VN": "Vietnam"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductsAndServicesAxis",)))
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by business", prod, tags=seg_tags(prod, ["Financial Services", "Deliveries"])),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["Malaysia", "Indonesia"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
