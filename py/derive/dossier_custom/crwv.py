"""CoreWeave: revenue multiplies from FY2023 to FY2025, nearly all of it in the US, while quarterly
operating margin slips below zero and free cash flow burns deeper."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, shaped

TICKER = "CRWV"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        geo and story.towers("Revenue by region", geo, tags=[growth(geo, "US")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        geo_q and story.towers("Same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "US", u=0.55), growth(geo_q, "Non-US", u=0.85)]),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
