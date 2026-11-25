"""Arm: royalties and licensing both grow, Japan's share of revenue jumps while the US share falls,
related-party revenue roughly doubles in two years, and quarterly revenue rises at a ~97% gross margin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "ARM"
GEO = {"CN": "China", "JP": "Japan", "TW": "Taiwan", "KR": "Korea", "Other Countries": "Other"}
REL = {"Nonrelated Party": "Non-related parties", "Related Party": "Related parties"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), {"License and Other": "License and other"})
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rel = shaped(d.history(("RelatedPartyTransactionsByRelatedPartyAxis",)), REL)
    q = story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue"))
    gm = d.points("Gross margin, quarterly")
    if q and gm:
        q["tags"] = [{"i": 1, "u": 0.85, "text": f"gross margin {min(v for _, v in gm):.0f}-{max(v for _, v in gm):.0f}%"
                                                 " every quarter"}]
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Royalty", "License"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Japan", "US"])),
        rel and story.towers("Revenue from related parties", rel, tags=[growth(rel, "Related")]),
        q,
    ]
    return [story.scene(d.name("financials"), beats)]
