"""Johnson Controls: the Americas grow while APAC shrinks, service takes a larger share of revenue,
the Americas lead the latest year-on-year quarter, and gross margin edges up each year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "JCI"
NAMES = {"Productsand Systems": "Products and systems"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Americas", "APAC"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Service"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Americas")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin, annual", "%", d.points("Gross margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
