"""Cohu: annual revenue falls by more than half from FY2021 to FY2024 and operating margin turns to a
loss; since then quarterly revenue climbs, systems revenue nearly doubles in the latest quarter, and the
quarterly operating margin recovers to about break-even."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_swing, growth, last_step,
                                         shaped, tagged)

TICKER = "COHU"
GEO = {"Rest of the World": "Rest of world", "PH": "Philippines", "TW": "Taiwan", "CN": "China", "MY": "Malaysia",
       "SG": "Singapore"}


def specs(d: Data) -> list[dict]:
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        geo and story.towers("Revenue by region", geo, tags=[last_step(geo, "Taiwan")]),
        qprod and story.towers("Revenue by type, same quarter a year apart", qprod, tags=[growth(qprod, "Systems")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_first_to_last(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
