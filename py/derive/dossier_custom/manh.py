"""Manhattan Associates: cloud subscriptions are the growth line while maintenance and services shrink
in FY2025; annual operating margin rises, but the quarterly margin slips back through 2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, pct_tags, seg_tags, shaped, tagged

TICKER = "MANH"
NAMES = {"Service Other": "Services", "License and Maintenance": "License"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Cloud", "Maintenance"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Cloud"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Cloud")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
        story.bars("Free cash flow, annual", "$M", fcf),
    ]
    return [story.scene(d.name("financials"), beats)]
