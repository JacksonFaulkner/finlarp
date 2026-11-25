"""Entegris: Taiwan overtakes North America as North America's share of revenue shrinks, non-semi
revenue falls by half, equipment and engineering lead the same quarter a year apart, and gross
margin recovers to a high in the latest quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, seg_tags, shaped, short

TICKER = "ENTG"
NAMES = {"TW": "Taiwan", "CN": "China", "KR": "Korea", "JP": "Japan", "Non Semi": "Non-semi"}

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    gm = d.points("Gross margin, quarterly")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=[{**t, "text": t["text"].split(" (")[0] + " of revenue"}
                                   for t in pct_tags(geo, ["North America", "Taiwan"])]),
        prod and story.towers("Revenue by end market", prod, tags=seg_tags(prod, ["Fabs", "Non-semi"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Equipment", u=0.8)], {"Equipment and Engineering": "Equip. & eng."})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
