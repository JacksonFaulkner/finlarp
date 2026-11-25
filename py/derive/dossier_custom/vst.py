"""Vistra: Retail grows into the largest segment, retail energy sales in the Northeast/Midwest more
than double, and the annual operating margin swings from losses to a 2024 peak before falling back
as free cash flow shrinks from its 2023 high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, without

TICKER = "VST"
NAMES = {"Retail Energy Charge in ERCOT": "Retail, ERCOT",
         "Retail Energy Charge in Northeast": "Retail, Northeast/Midwest",
         "Wholesale Generation Revenue from ERCOT": "Wholesale, ERCOT",
         "Revenue from Other Wholesale": "Other wholesale contracts"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    # hedging, amortization and intersegment lines are contra/negative adjustments, left out
    src = shaped(without(d.history(("ProductOrServiceAxis",)), "Hedging", "Intangible", "Intersegment"), NAMES)
    beats = [
        seg and story.towers("Revenue by segment (before eliminations)", seg, tags=seg_tags(seg, ["Retail", "Texas"])),
        src and story.towers("Revenue by source (before hedging)", src,
                             tags=seg_tags(src, ["Retail, Northeast", "Retail, ERCOT"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
