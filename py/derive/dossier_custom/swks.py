"""Skyworks: annual revenue shrinks every year after FY2022 with the US its dominant market, operating
margin falls from the 30s to the low teens, and quarterly free cash flow turns negative in 2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, bars_year_ago, growth, shaped, share, tagged

TICKER = "SWKS"
GEO = {"TW": "Taiwan", "CN": "China", "KR": "Korea"}


def _peak_to_last(pts: list[list], unit: str, u: float = 0.75) -> dict | None:
    """'<peak period> <v> -> <last period> <v>' (private: the shared bars_swing goes low -> latest)."""
    if len(pts) < 2:
        return None
    hi = max(range(len(pts)), key=lambda i: pts[i][1])
    if hi == len(pts) - 1:
        return None
    f = (lambda v: f"{v:.1f}%") if unit == "%" else (lambda v: _money(v, unit))  # noqa: E731
    return {"i": -1, "u": u, "text": f"{pts[hi][0]} {f(pts[hi][1])} -> {pts[-1][0]} {f(pts[-1][1])}"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    omq = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=[share(geo, "US", u=0.6), growth(geo, "China", u=0.8)]),
        tagged(story.bars("Annual revenue", "$M", rev), _peak_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), _peak_to_last(om, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", omq), bars_year_ago(omq, "%")),
        tagged(story.bars("Free cash flow, quarterly", "$M", fcf), _peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
