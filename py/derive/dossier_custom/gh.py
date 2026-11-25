"""Guardant Health: screening revenue appears and multiplies, oncology keeps growing, quarterly revenue
climbs every quarter, and operating losses narrow but stay deep while free cash flow stays negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped

TICKER = "GH"

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
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Oncology", "Screening"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Screening", u=0.85), growth(prod_q, "Oncology", u=0.45)]),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), _swing_money(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
