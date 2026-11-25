"""Natera: revenue paid by insurance carriers more than doubles and grows its share, quarterly revenue
climbs every quarter, operating margin stays negative, and annual free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "NTRA"

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
    pay = shaped(d.history(("MajorCustomersAxis",)))
    fcf = story.bars("Free cash flow", "$M", d.points("Free cash flow, annual"))
    if fcf:
        pts = fcf["points"]
        k = next((i for i in range(1, len(pts)) if pts[i - 1][1] < 0 <= pts[i][1]), None)
        if k is not None:
            fcf["tags"] = [{"i": k, "u": 0.75, "text": f"{pts[k][0]}: first positive year"}]
    beats = [
        pay and story.towers("Revenue by payer", pay, tags=seg_tags(pay, ["Insurance Carriers"])),
        pay and story.towers("Revenue share by payer", pay, pct=True, tags=_short(pct_tags(pay, ["Insurance Carriers"]), {f"({pay['periods'][0]} -> {pay['periods'][-1]})": "of revenue"})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
