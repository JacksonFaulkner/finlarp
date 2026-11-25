"""Himax: revenue shrinks every year from FY2021, driver ICs decline while non-driver products grow,
large-size display revenue roughly halves, China stays most of sales, and operating margin falls from
35% to single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, pct_tags, seg_tags, shaped, tagged

TICKER = "HIMX"
NAMES = {"Non Driver IC": "Non-driver IC"}
APPS = {"Small and Medium Sized Applications": "Small and medium-size", "Non Driver Products": "Non-driver",
        "Large Size Applications": "Large-size"}
GEO = {"CN": "China", "TW": "Taiwan", "KR": "South Korea", "JP": "Japan", "MX": "Mexico"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductsAndServicesAxis",)), NAMES)
    apps = shaped(d.history(("ApplicationsAxis",)), APPS)
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Driver IC", "Non-driver"])),
        apps and story.towers("Revenue by application", apps, tags=seg_tags(apps, ["Large-size"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
