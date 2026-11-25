"""Netskope: revenue grows about 1.7x in two years, nearly all of it through indirect channels, with
EMEA roughly doubling; gross margin climbs into the low 70s apart from one quarter, when operating
margin also plunges to its low, and annual free cash flow turns slightly positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, share, tagged

TICKER = "NTSK"


def _low(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    i = min(range(len(pts)), key=lambda j: pts[j][1])
    return {"i": i, "u": u, "text": f"Low {pts[i][0]} {pts[i][1]:.1f}%"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA", "Americas"])),
        prod and story.towers("Revenue by channel", prod, tags=[share(prod, "Indirect")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin", "%", gm), bars_year_ago(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), _low(om)),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
