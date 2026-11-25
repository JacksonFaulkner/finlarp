"""Xylem: Water Solutions and Services grows fastest and more than doubles its operating income,
Measurement and Control Solutions falls in the latest quarter versus a year earlier, and gross and
operating margins widen."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, short

TICKER = "XYL"
NAMES = {"Measurementand": "Measurement and Control Solutions"}
SHORT = {"Water Solutions Services": "Water Solutions", "Measurement and Control Solutions": "MCS",
         "Water Infrastructure": "Water Infra."}

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Water Solutions", "Measurement"]), SHORT)),
        oi and story.towers("Operating income by segment", oi, tags=short(seg_tags(oi, ["Water Solutions", "Water Infra"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Measurement")], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
