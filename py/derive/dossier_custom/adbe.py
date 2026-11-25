"""Adobe: subscriptions grow to nearly all revenue while product and services shrink, Digital Media
leads the segments, gross margin sits near 89%, and free cash flow rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "ADBE"
NAMES = {"Subscription Revenue": "Subscription", "Service Other": "Services and other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Digital Media", "Digital Experience"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Subscription"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
