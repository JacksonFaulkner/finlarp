"""SS&C: software-enabled services carry the growth and most of revenue, revenue rises every year and
quarter with a steady operating margin, and annual free cash flow climbs from its FY2022 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, shaped, share, short, tagged, yoy

TICKER = "SSNC"
NAMES = {"Software Enabled": "Software-enabled services", "Maintenance and Term": "Maintenance and term licenses"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short([yoy(prod, "Software-enabled", u=0.55),
                                                                  share(prod, "Software-enabled", u=0.8)],
                                                                 {"Software-enabled services": "Software-enabled"})),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
