"""NetApp: all-flash arrays grow while hybrid flash shrinks, all-flash jumps in the latest quarter
against a year earlier, and operating margin rises into the mid-20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "NTAP"
NAMES = {"All- Flash": "All-flash", "Hybrid- Flash": "Hybrid flash and other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["All-flash", "Hybrid"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "All-flash")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
