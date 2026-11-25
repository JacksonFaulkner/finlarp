"""Veeva: R&D and Quality subscriptions pass Commercial Cloud subscriptions to become the largest
line, revenue rises every quarter, and operating margin moves from the mid-20s to about 30%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "VEEV"
NAMES = {"Subscription Services Veeva Research": "R&D and Quality subscriptions",
         "Subscription Services Veeva Commercial": "Commercial Cloud subscriptions",
         "Professional Services Veeva Research": "R&D and Quality services",
         "Professional Services Veeva Commercial": "Commercial Cloud services"}
SHORT = {"subscriptions": "subs"}

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
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        prod and story.towers("Revenue by product and type", prod,
                              tags=_short(seg_tags(prod, ["R&D and Quality subs", "Commercial Cloud subs"]), SHORT)),
        prod and story.towers("Revenue share", prod, pct=True, tags=_short(pct_tags(prod, ["R&D and Quality subs"]),
                                                                  {**SHORT, f"({prod['periods'][0]} -> {prod['periods'][-1]})": "of revenue"})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
