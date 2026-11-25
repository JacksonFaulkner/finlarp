"""Keysight: the communications group dips and recovers on an annual view, then jumps in the latest
quarter against a year earlier, its operating income nearly doubles, and operating margin climbs
from the mid-teens to about 25%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "KEYS"
SHORT = {"Communications Solutions Group": "Communications", "Electronic Industrial Solutions Group": "Electronic Industrial"}

def _short(tags, names: dict) -> list:
    """`tags` with long series names shortened in the callout text only (the legend keeps the full name)."""
    out = []
    for t in tags if isinstance(tags, list) else [tags]:
        if t:
            for full, short in names.items():
                t["text"] = t["text"].replace(full, short)
            out.append(t)
    return out


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=_short(seg_tags(seg, ["Communications", "Electronic Industrial"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=_short(seg_tags(seg_q, ["Communications", "Electronic Industrial"]), SHORT)),
        oi_q and story.towers("Segment operating income, same quarter a year apart", oi_q,
                              tags=_short(seg_tags(oi_q, ["Communications", "Electronic Industrial"]), SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
