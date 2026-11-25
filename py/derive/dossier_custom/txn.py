"""Texas Instruments: Analog is most of revenue, segment operating income jumps in the latest
quarter against the same quarter a year earlier, and gross and operating margins rise through 2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "TXN"


def _year_apart(h: dict | None) -> dict | None:
    """The latest quarter and the same quarter a year earlier, from a quarterly history."""
    if not h:
        return None
    mon, yy = h["periods"][-1].split()
    prev = f"{mon} {int(yy) - 1:02d}"
    if prev not in h["periods"]:
        return None
    i = h["periods"].index(prev)
    return {**h, "periods": [prev, h["periods"][-1]], "series": [[n, [vs[i], vs[-1]]] for n, vs in h["series"]]}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi_q = _year_apart(shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=8, oi=True)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Analog", "Embedded"])),
        oi_q and story.towers("Operating income, same quarter a year apart", oi_q,
                              tags=seg_tags(oi_q, ["Analog", "Embedded"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
