"""Galaxy Digital: digital asset sales are nearly all of its revenue, so quarterly revenue swings
with trading volume; beside them, fee revenue roughly triples and blockchain rewards grow while
proprietary mining shrinks, a Data Centers segment shows its first revenue in FY2025, and annual
free cash flow is negative every year and deepest in FY2025. No gross or operating margin is
reported in the Financials data."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, drop, growth, seg_tags, shaped, tagged, total_of

TICKER = "GLXY"


def _share1(hist: dict | None, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> n.n% of revenue' for the latest period, one decimal (the share rounds to 100%)."""
    k = next((k for k, (n, _) in enumerate((hist or {}).get("series", [])) if n.startswith(prefix)), None)
    if k is None or not total_of(hist):
        return None
    name, vs = hist["series"][k]
    return {"i": -1, "s": k, "u": u, "text": f"{name} {vs[-1] / total_of(hist) * 100:.1f}% of revenue"}


def specs(d: Data) -> list[dict]:
    seg_q = drop(shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)), "Digital Assets")
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    rest = drop(prod, "Digital Assets Sales")
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    low = fcf and min(fcf, key=lambda p: p[1])
    beats = [
        prod and story.towers("Revenue by type", prod, tags=[_share1(prod, "Digital Assets Sales")]),
        rest and story.towers("Revenue besides digital asset sales", rest,
                              tags=seg_tags(rest, ["Fee", "Proprietary Mining"])),
        seg_q and story.towers("Smaller segments, same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Data Centers")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf),
               low and {"i": fcf.index(low), "u": 0.75, "text": f"{low[0]} {story.money(low[1])}"}),
    ]
    return [story.scene(d.name("financials"), beats)]
