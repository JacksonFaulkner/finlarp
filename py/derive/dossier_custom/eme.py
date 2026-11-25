"""EMCOR: revenue climbs every year since FY2021, operating margin roughly doubles as gross margin
rises, and free cash flow grows about fourfold. (No segment split in the XBRL facts.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago

TICKER = "EME"


def _first_last(points: list[list], unit: str, u: float = 0.75) -> dict | None:
    """'<first> a -> <last> b' on the latest bar (whole-span change, % points or money)."""
    if len(points) < 2:
        return None
    (pa, a), (pb, b) = points[0], points[-1]
    if unit == "%":
        return {"i": -1, "u": u, "text": f"{pa} {a:.1f}% -> {pb} {b:.1f}%"}
    ch = f" ({b / a:.1f}x)" if a > 0 and b / a >= 2 else (f" ({(b / a - 1) * 100:+.0f}%)" if a > 0 else "")
    return {"i": -1, "u": u, "text": f"{pa} -> {pb}{ch}"}


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, annual")
    fcf = d.points("Free cash flow, annual")
    q = d.points("Quarterly revenue")
    beats = [
        story.bars("Annual revenue", "$M", rev),
        story.bars("Operating margin, annual", "%", om, tags=[t for t in [_first_last(om, "%")] if t]),
        story.bars("Gross margin, annual", "%", gm, tags=[t for t in [_first_last(gm, "%")] if t]),
        story.bars("Free cash flow, annual", "$M", fcf),
        story.bars("Quarterly revenue", "$M", q, tags=[t for t in [bars_year_ago(q)] if t]),
    ]
    for b in beats:
        if b and b.get("tags"):
            b["auto_tags"] = False
    return [story.scene(d.name("financials"), beats)]
