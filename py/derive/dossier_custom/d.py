"""Dominion Energy: the Virginia utility is most of revenue and does the growing, it jumps again in
the latest quarter against a year earlier, and quarterly revenue reaches a new high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "D"
SHORT = {"Dominion Energy Virginia": "Virginia"}

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
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=_short([growth(seg, "Dominion Energy Virginia", u=0.55),
                                          share(seg, "Dominion Energy Virginia", u=0.8)], SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=_short(seg_tags(seg_q, ["Dominion Energy Virginia"]), SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
