"""PDD Holdings: transaction services revenue doubles in a year and draws level with online marketing,
revenue multiplies over five years, and operating margin peaks then falls back. Figures are RMB (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, shaped

TICKER = "PDD"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's RMB figures


def _multiple(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> k.kx, <first> -> <last>' (the money tag with CNY on both ends is too long to fit)."""
    k = next((j for j, (n, _) in enumerate(hist["series"]) if n.startswith(prefix)), None)
    if k is None or hist["series"][k][1][0] <= 0:
        return None
    name, vs = hist["series"][k]
    return {"i": -1, "s": k, "u": u, "text": f"{name} {vs[-1] / vs[0]:.1f}x, {hist['periods'][0]} -> {hist['periods'][-1]}"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), {"Online Marketing Services and Others": "Online marketing and other"})
    beats = [
        prod and story.towers("Revenue by service", prod, tags=[_multiple(prod, "Transaction")]),
        prod and story.towers("Revenue share by service", prod, pct=True, tags=[{**t, "text": t["text"].split(" (")[0] + " of revenue"} for t in pct_tags(prod, ["Transaction"])]),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
