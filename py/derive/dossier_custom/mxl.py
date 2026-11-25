"""MaxLinear: revenue falls by two thirds from FY2022 to FY2024, then infrastructure products drive
the rebound, more than tripling in a year, and the quarterly operating margin climbs from deep losses
to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, shaped, tagged

TICKER = "MXL"
NAMES = {"Industrialandmultimarket": "Industrial and Multi Market"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, quarterly")
    hi = max(range(len(rev)), key=lambda i: rev[i][1]) if rev else None
    lo = min(range(len(rev)), key=lambda i: rev[i][1]) if rev else None
    fall = rev and hi < lo and {"i": lo, "u": 0.75, "text": f"{rev[hi][0]} {story.money(rev[hi][1])} -> "
                                                       f"{rev[lo][0]} {story.money(rev[lo][1])}"}
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), fall),
        prod and story.towers("Revenue by product line", prod,
                              tags=[_last_step(prod, "Broadband", u=0.55), _last_step(prod, "Infrastructure", u=0.8)]),
        prod_q and story.towers("Same quarter a year apart, by product line", prod_q,
                                tags=[growth(prod_q, "Infrastructure", u=0.6)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]


def _last_step(hist: dict | None, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> <a> -> <b>: +n%' over the last two periods only."""
    k = next((k for k, (n, _) in enumerate((hist or {}).get("series", [])) if n.startswith(prefix)), None)
    if k is None or len(hist["periods"]) < 2:
        return None
    name, vs = hist["series"][k]
    a, b = vs[-2], vs[-1]
    if a <= 0:
        return None
    ch = f"{b / a:.1f}x" if b / a >= 2 else f"{(b / a - 1) * 100:+.0f}%"
    p = hist["periods"]
    return {"i": -1, "s": k, "u": u, "text": f"{name} {p[-2]} -> {p[-1]}: {ch}"}
