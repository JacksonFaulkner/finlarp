"""Palantir: government and commercial both grow fast, commercial roughly doubles in a year by
mid-2026, quarterly revenue more than doubles in two years, and operating margin climbs from the
mid teens to the high 40s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "PLTR"
NAMES = {"Government": "Government", "Commercial": "Commercial"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Government", "Commercial"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Commercial", "Government"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
