"""Flex: Cloud Power Infrastructure doubles from FY2024 to FY2026 while Integrated Technology
Solutions shrinks, revenue recognized over time rises to about a third, and gross margin edges up
from a thin base."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, short

TICKER = "FLEX"
NAMES = {"Integrated Technology Solutions": "Integrated Technology Solutions",
         "Regulated Manufacturing Solutions": "Regulated Manufacturing Solutions",
         "Cloud Power Infrastructure": "Cloud Power Infrastructure"}
SHORT = {"Integrated Technology Solutions": "ITS", "Regulated Manufacturing Solutions": "RMS",
         "Cloud Power Infrastructure": "CPI"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    timing = shaped(d.history(("TimingOfTransferOfGoodOrServiceAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short(seg_tags(seg, ["Cloud Power", "Integrated Technology"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Cloud Power")], SHORT)),
        timing and story.towers("Revenue share by timing of recognition", timing, pct=True,
                                tags=pct_tags(timing, ["Over time"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
