"""AXT: the latest quarter's revenue is well over double the same quarter a year earlier, driven by
substrates and by China and Europe, after a weak 2025; gross margin climbs from below zero and the
operating margin turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, tagged

TICKER = "AXTI"
GEO = {"CN": "China", "TW": "Taiwan", "JP": "Japan", "Asia Pacific excluding": "Other Asia Pacific"}


def _m(v: float) -> str:
    return f"-${-v:.1f}M" if v < 0 else f"${v:.1f}M"


def specs(d: Data) -> list[dict]:
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    lo = min(range(len(q)), key=lambda i: q[i][1]) if q else 0
    beats = [
        prod_q and story.towers("Same quarter a year apart, by product", prod_q,
                                tags=seg_tags(prod_q, ["Substrates", "Raw"])),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "China", u=0.6), growth(geo_q, "Europe", u=0.85)]),
        q and tagged(story.bars("Quarterly revenue", "$M", q),
                     {"i": -1, "u": 0.75, "text": f"{q[lo][0]} {_m(q[lo][1])} -> {q[-1][0]} {_m(q[-1][1])}"}),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
