"""SailPoint: SaaS nearly doubles in two years and becomes most of revenue while maintenance and other
lines shrink; operating losses persist (a deep one in Q1 FY2026, when gross margin also dipped), and
free cash flow turns positive in FY2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, seg_tags, shaped, tagged

TICKER = "SAIL"
NAMES = {"Software As A Service": "SaaS", "Term Subscriptions": "Term subscriptions",
         "Product and Service Other": "Other products and services", "Other Subscription": "Other subscriptions"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, quarterly")
    gm = dict(d.points("Gross margin, quarterly"))
    lo = min(om, key=lambda p: p[1]) if om else None
    lo_tag = lo and {"i": om.index(lo), "u": 0.7,
                     "text": f"{lo[0]} {lo[1]:.0f}%" + (f" (gross {gm[lo[0]]:.0f}%)" if lo[0] in gm else "")}
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["SaaS", "Maintenance"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["SaaS"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "SaaS")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), lo_tag),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
