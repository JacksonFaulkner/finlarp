"""Western Digital: the cloud business more than doubles in two years and is nearly all revenue,
China's share of revenue grows, gross margin rises from the 30s to the high 50s, and free cash flow
turns from negative to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "WDC"
GEO = {"CN": "China", "HK": "Hong Kong"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by end market", prod, tags=seg_tags(prod, ["Cloud"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Cloud")]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
