"""Nasdaq: all three segments grow with Financial Technology up fastest, revenue outside the US gains
share, Capital Access Platforms earns the most operating income, and operating margin rises to ~30%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, share

TICKER = "NDAQ"
GEO = {"Non Us": "Non-US"}

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
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Financial Technology", "Market Services"])),
        geo and story.towers("Revenue share, US vs non-US", geo, pct=True, tags=pct_tags(geo, ["Non-US"])),
        oi_q and story.towers("Segment operating income, same quarter a year apart", oi_q,
                              tags=_short([share(oi_q, "Capital Access", u=0.6), growth(oi_q, "Financial Technology", u=0.8)],
                                                {"Capital Access Platforms": "Capital Access"})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
