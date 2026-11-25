"""SAP: revenue grows in every region, fastest in EMEA outside the home country, and the annual
operating margin recovers from its FY2024 low to the highest of the run. Figures are EUR (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "SAP"
UNIT = "EUR M"  # the 20-F's figures; the segment facts carry an IFRS unit id, not a plain EUR
GEO = {"Europe Middle East and Africa excluding Germany": "EMEA excl. Germany",
       "Country of Domicile": "Country of domicile", "Asia Pacific excluding Japan": "Asia Pacific excl. Japan",
       "Americas excluding United States": "Americas excl. US", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    if geo:
        geo = {**geo, "unit": UNIT}
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA excl", "US"])),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
