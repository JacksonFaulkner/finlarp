"""JFrog: cloud SaaS doubles in two years and nearly catches subscriptions, the operating
loss narrows toward single digits over two years, and free cash flow grows every year since FY2022."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, seg_tags, shaped, tagged

TICKER = "FROG"
NAMES = {"Saas": "SaaS"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["SaaS", "Subscription"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["SaaS"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "SaaS")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
