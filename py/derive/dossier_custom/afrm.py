"""Affirm: revenue by region grows mostly in the US, network revenue rises each year with the
virtual card growing faster than the merchant network, and annual free cash flow swings from
negative to positive. (The Financials tab's revenue line covers only part of revenue, so its
quarterly revenue and margin series are left out.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import drop, seg_tags, shaped

TICKER = "AFRM"
NAMES = {"CA": "Canada"}

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
    geo = shaped(drop(d.history(("StatementGeographicalAxis",)), "Other Geographical"), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Canada"])),
        prod and story.towers("Network revenue by type", prod, tags=seg_tags(prod, ["Merchant", "Virtual Card"])),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), _swing_money(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
