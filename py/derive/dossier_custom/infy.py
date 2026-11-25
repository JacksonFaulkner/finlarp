"""Infosys: Europe supplies the growth while North America, the largest region, stays flat, revenue
growth slows to low single digits after FY2023, and margins step down from FY2021 levels."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, shaped

TICKER = "INFY"
GEO = {"IN": "India"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Europe", "North America"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
