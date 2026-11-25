"""Lyft: revenue is almost all US, but non-US revenue jumps in FY2025. The Financials revenue
series run below the segment totals (a partial revenue concept) and quarterly net margin reads over
100%, so revenue and margin beats are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, shaped

TICKER = "LYFT"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    beats = [
        geo and story.towers("Revenue by region", geo,
                             tags=[growth(geo, "US", u=0.55), _last_step(geo, "Non-US", u=0.85)]),
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
