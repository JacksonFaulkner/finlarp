"""Lattice Semiconductor: China rises to about half of revenue, its quarterly sales double in a year,
annual revenue and margin drop after FY2023, and quarterly revenue and operating margin recover."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, pct_tags, shaped, tagged

TICKER = "LSCC"
GEO = {"CN": "China", "JP": "Japan", "MY": "Malaysia"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "Japan"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "China")]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
