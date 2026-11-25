"""ASML: EUV (NXE) and ArF immersion carry system sales while the new High-NA EXE line starts
shipping, China swings from about a quarter of revenue to over a third and partly back, and free cash flow
recovers after a FY2023 low. Figures are EUR (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "ASML"
UNIT = "EUR M"  # the Financials tab's series are the 20-F's EUR figures
NAMES = {"Arf Immersion": "ArF immersion", "Arf Dry": "ArF dry", "Krf": "KrF", "Iline": "i-line"}
GEO = {"CN": "China", "TW": "Taiwan", "KR": "Korea", "US": "US", "JP": "Japan"}


def _pct_swing(hist: dict, prefix: str, u: float) -> dict | None:
    """'<name> peak n% (<period>)' on the period where that series' share of the tower is highest."""
    k = next((j for j, (n, _) in enumerate(hist["series"]) if n.startswith(prefix)), None)
    if k is None:
        return None
    tot = [sum(vs[i] for _, vs in hist["series"]) or 1 for i in range(len(hist["periods"]))]
    sh = [v / t * 100 for v, t in zip(hist["series"][k][1], tot)]
    i = max(range(len(sh)), key=sh.__getitem__)
    return {"i": i, "s": k, "u": u, "text": f"{hist['series'][k][0]} peak {sh[i]:.0f}% ({hist['periods'][i]})"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["NXE", "EXE"])),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=[_pct_swing(geo, "China", 0.5), *pct_tags(geo, ["China"])]),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Free cash flow", UNIT, d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
