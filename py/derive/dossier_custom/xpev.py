"""XPeng: vehicle revenue nearly doubles in FY2025, gross margin recovers from its FY2023 low,
the operating loss shrinks to a few percent of revenue, and free cash flow turns positive.
Figures are CNY (20-F); there is no quarterly data, so quarterly beats are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, shaped, tagged, yoy

TICKER = "XPEV"
UNIT = "CNY M"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=[growth(prod, "Vehicle", u=0.55), yoy(prod, "Services", u=0.8)]),
        tagged(story.bars("Annual revenue", UNIT, rev), bars_first_to_last(rev, UNIT)),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", UNIT, fcf), bars_swing(fcf, UNIT)),
    ]
    return [story.scene(d.name("financials"), beats)]
