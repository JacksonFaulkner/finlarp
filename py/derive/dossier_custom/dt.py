"""Dynatrace: revenue more than doubles over five fiscal years with EMEA the fastest-growing region,
operating margin climbs from about 8% to 12%, and free cash flow rises every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, shaped, tagged, yoy

TICKER = "DT"


def _first_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2 or pts[0][1] <= 0:
        return None
    (pa, a), (pb, b) = pts[0], pts[-1]
    ch = f"{b / a:.1f}x" if b / a >= 2 else f"{(b / a - 1) * 100:+.0f}%"
    return {"i": -1, "u": u, "text": f"{pa} -> {pb}: {ch}"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=[yoy(geo, "EMEA", u=0.6), yoy(geo, "North America", u=0.8)]),
        tagged(story.bars("Annual revenue", "$M", rev), _first_to_last(rev)),
        tagged(story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")), bars_year_ago(d.points("Quarterly revenue"))),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _first_to_last(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
