"""Ouster: revenue grows every year to FY2025, led by Asia Pacific and the Americas while EMEA shrinks,
a royalty line appears in FY2025 and lifts one quarter to a small operating profit, and the operating
loss narrows from -98% of revenue to under -40% while cash still burns."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_total, seg_tags, shaped, tagged

TICKER = "OUST"


def _royalty_tag(om: list[list], prod_q: dict | None) -> dict | None:
    """Tag the operating-margin bar of the quarter whose royalty spiked (calendar fiscal year)."""
    k = story.find(prod_q, "Royalty") if prod_q else None
    if k is None or not om:
        return None
    vs = prod_q["series"][k][1]
    j = max(range(len(vs)), key=lambda i: vs[i])
    mon, yy = prod_q["periods"][j].split()
    q = {"Mar": 1, "Jun": 2, "Sep": 3, "Dec": 4}.get(mon)
    i = next((i for i, (p, _) in enumerate(om) if p == f"Q{q}'{yy}"), None)
    if i is None or vs[j] <= 0:
        return None
    return {"i": i, "u": 0.6, "text": f"{om[i][0]} {om[i][1]:.1f}%, {story.money(vs[j])} royalty"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = d.history(("ProductOrServiceAxis",), cadence="quarterly", n=8)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Asia Pacific", "EMEA"])),
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Product", "Royalty"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), _royalty_tag(om, prod_q),
               bars_first_to_last(om, "%", u=0.85)),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
