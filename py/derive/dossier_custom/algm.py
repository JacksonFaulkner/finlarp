"""Allegro MicroSystems: revenue fell in FY2025 and recovered in FY2026, with power ICs rebounding
fastest; Taiwan sales tripled in the latest quarter, quarterly revenue has risen five quarters
running, and the operating margin climbed from a loss to near 10%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, seg_tags, shaped, short, tagged

TICKER = "ALGM"
SHORT = {"Power Integrated Circuits": "Power ICs"}
NAMES = {"CN": "China", "JP": "Japan", "KR": "Korea", "TW": "Taiwan"}


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
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product line", prod,
                              tags=short([_step(prod, "Power", 0.55), _step(prod, "Magnetic", 0.75)], SHORT)),
        prod_q and story.towers("Product lines, same quarter a year apart", prod_q,
                                tags=short(seg_tags(prod_q, ["Power", "Magnetic"]), SHORT)),
        geo_q and story.towers("Revenue by region, same quarter a year apart", geo_q,
                               tags=seg_tags(geo_q, ["Taiwan", "China"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
