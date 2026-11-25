"""Power Integrations: annual revenue falls by a third from FY2021 and stays there, operating margin
shrinks from the mid-20s to low single digits, and Hong Kong / China remains over half of sales while
China's quarterly revenue drops and Singapore's climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, growth, pct_tags, shaped, short,
                                         tagged)

TICKER = "POWI"
GEO = {"Hong Kong China": "Hong Kong / China", "KR": "Korea", "DE": "Germany", "TW": "Taiwan", "IN": "India",
       "Emea Other Than Germany": "EMEA other than Germany", "Other Countries": "Other"}
QGEO = {"CN": "China", "SG": "Singapore"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    qgeo = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), QGEO)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["Hong Kong"]), {"Hong Kong / China": "HK / China"})),
        qgeo and story.towers("Revenue by region, same quarter a year apart", qgeo,
                              tags=[growth(qgeo, "China", u=0.55), growth(qgeo, "Singapore", u=0.85)]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        story.bars("Quarterly revenue", "$M", q),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
