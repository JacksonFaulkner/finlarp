"""AAON: the BASX line takes over growth, more than tripling in the latest quarter on a year
earlier, coil products more than double over FY2023-FY2025, quarterly revenue doubles, and gross
margin slides as the mix shifts."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_year_ago, seg_tags, shaped, tagged

TICKER = "AAON"
NAMES = {"Bas X": "BASX"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["AAON Coil", "BASX"])),
        prod_q and story.towers("Product lines, same quarter a year apart", prod_q,
                                tags=seg_tags(prod_q, ["BASX", "AAON"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
