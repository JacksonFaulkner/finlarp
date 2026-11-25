"""Energy Transfer: annual revenue is flat by segment through FY2025, then in 2026 quarterly revenue
jumps as the Sunoco LP and crude oil segments more than double against the same quarter a year
earlier, while the operating margin stays near 10-12%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, shaped

TICKER = "ET"
NAMES = {"Crudeoiltransportationandservices": "Crude oil transportation",
         "NG Landrefinedproducts": "NGL and refined products"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    qb = story.bars("Quarterly revenue", "$M", q)
    if qb:
        lo = q[-5] if len(q) >= 5 else q[0]  # the same quarter a year earlier
        qb["tags"], qb["auto_tags"] = [{"i": -1, "u": 0.8, "text": f"{lo[0]} ${lo[1] / 1e3:.1f}B -> {q[-1][0]} "
                                        f"${q[-1][1] / 1e3:.1f}B ({q[-1][1] / lo[1]:.1f}x)"}], False
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[growth(seg, "Investment in Sunoco")]),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Investment in Sunoco", u=0.55), growth(seg_q, "Crude oil", u=0.75)]),
        qb,
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
