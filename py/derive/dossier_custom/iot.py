"""Samsara: subscription revenue carries the growth, outside-US revenue grows faster than the US,
and operating margin climbs from double-digit losses to around breakeven while free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, short

TICKER = "IOT"
NAMES = {"Non Us": "Non-US", "Product and Service Other": "Other"}


def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def _m(v: float) -> str:
    a = abs(v)
    return ("-" if v < 0 else "") + (f"${a / 1e3:.1f}B" if a >= 1e3 else f"${a:,.0f}M")


def _swing_money(pts: list[list], u: float = 0.75) -> dict | None:
    """Low -> latest for a money series that may go negative."""
    if len(pts) < 2:
        return None
    lo = min(range(len(pts)), key=lambda i: pts[i][1])
    if lo == len(pts) - 1:
        return None
    return {"i": -1, "u": u, "text": f"{pts[lo][0]} {_m(pts[lo][1])} -> {pts[-1][0]} {_m(pts[-1][1])}"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=short(seg_tags(prod, ["Subscription"]), {"Subscription and Circulation": "Subscription"})),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "US", u=0.55), growth(geo_q, "Non-US", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), _swing_money(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
