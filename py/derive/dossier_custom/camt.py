"""Camtek: China is the largest region and grows most in FY2025 while Korea swings up in FY2024 and
back down in FY2025; product sales carry nearly all revenue and free cash flow more than doubles
over five years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, seg_tags, shaped, tagged

TICKER = "CAMT"
NAMES = {"CN": "China", "KR": "Korea"}

# The Financials quarterly blocks hold one Q2 point per year ending in 2021 (not a quarterly
# series), so quarterly revenue and the margins are left out.


def _step(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> <last period> +n% to $b': the last step of a series (vs the period before)."""
    k = next((j for j, (n, _) in enumerate(hist["series"]) if n.startswith(prefix)), None)
    if k is None:
        return None
    name, vs = hist["series"][k]
    a, b = vs[-2], vs[-1]
    if a <= 0:
        return None
    return {"i": -1, "s": k, "u": u,
            "text": f"{name} {hist['periods'][-1]} {(b / a - 1) * 100:+.0f}% to {story.money(b)}"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=[_step(geo, "China", 0.55), _step(geo, "Korea", 0.8)]),
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Sales of Products", "Service"])),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
