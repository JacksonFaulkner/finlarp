"""Atlassian: cloud revenue grows to most of the business as server revenue goes to zero, gross margin
rises to the mid-80s, and operating margin turns positive in the latest quarter after a run of losses."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "TEAM"
SHORT = {"Cloud Deployment Services": "Cloud", "Server Deployment": "Server"}

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
    dep = shaped(d.history(("ProductOrServiceAxis",)))
    beats = [
        dep and story.towers("Revenue by deployment", dep, tags=_short(seg_tags(dep, ["Cloud", "Server"]), SHORT)),
        dep and story.towers("Revenue share by deployment", dep, pct=True, tags=_short(pct_tags(dep, ["Cloud"]), SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
