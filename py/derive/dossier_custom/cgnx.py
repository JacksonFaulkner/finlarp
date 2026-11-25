"""Cognex: revenue climbs back from its FY2023 low led by the Americas and Europe, China grows fastest
in the latest quarter against a year earlier, and quarterly operating margin rises from about 12% to
about 29% as gross margin moves above 70%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, tagged

TICKER = "CGNX"
GEO = {"CN": "China"}


def _from_low(pts: list[list], u: float = 0.75) -> dict | None:
    """'<low period> $a -> <last> $b (+n%)' from the series' low to its latest point."""
    if len(pts) < 2:
        return None
    i = min(range(len(pts)), key=lambda j: pts[j][1])
    if i == len(pts) - 1 or pts[i][1] <= 0:
        return None
    (pa, a), (pb, b) = pts[i], pts[-1]
    return {"i": -1, "u": u, "text": f"{pa} {story.money(a)} -> {pb} {story.money(b)} ({(b / a - 1) * 100:+.0f}%)"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Americas", "Europe"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=seg_tags(geo_q, ["China", "Americas"])),
        tagged(story.bars("Annual revenue", "$M", rev), _from_low(rev)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin", "%", gm), bars_year_ago(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
