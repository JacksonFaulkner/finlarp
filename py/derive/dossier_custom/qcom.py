"""Qualcomm: chips (QCT) carry all of the growth while licensing (QTL) stays flat, then the latest
quarters slip: revenue and QCT fall below a year earlier and operating margin roughly halves from
its peak."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "QCOM"
NAMES = {"Qct": "QCT", "Qtl": "QTL", "Qsi": "QSI"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["QCT", "QTL"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "QCT")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
