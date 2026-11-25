"""Paycom: recurring revenue is nearly all of revenue and keeps growing while interest on client
funds falls back after FY2024, and quarterly operating margin swings between the low 20s and mid 30s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, seg_tags, share, shaped, tagged, yoy

TICKER = "PAYC"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=[*seg_tags(prod, ["Recurring"]), share(prod, "Recurring", u=0.85)]),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[yoy(prod_q, "Recurring", u=0.55), yoy(prod_q, "Interest", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
