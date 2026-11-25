"""Tesla: car sales shrink two years running while energy storage more than doubles, revenue is
flat by quarter, and operating margin thins."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "TSLA"
NAMES = {"Energy Generation and Storage Sales": "Energy storage sales",
         "Energy Generation and Storage Leasing": "Energy leasing", "Automotive Regulatory": "Regulatory credits"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    beats = [
        prod and story.towers("Revenue by line", prod, tags=seg_tags(prod, ["Automotive Sales", "Energy storage"])),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["Energy"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
