"""PSEG: the regulated utility (PSE&G) grows every year while PSEG Power & Other swings, falling hard in
the latest quarter, and operating margin moves from a FY2021 loss to the mid-20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped

TICKER = "PEG"
NAMES = {"Public Service Electricand Gas": "Public Service Electric and Gas", "PSEG Power Other": "PSEG Power & Other"}
SHORT = {"Public Service Electric and Gas": "PSE&G"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, annual")
    omb = story.bars("Operating margin, annual", "%", om)
    if omb and (t := bars_swing(om, "%")):
        omb["tags"], omb["auto_tags"] = [t], False
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=story.short(seg_tags(seg, ["Public Service", "PSEG Power"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=story.short([growth(seg_q, "PSEG Power", u=0.6),
                                                 growth(seg_q, "Public Service", u=0.85)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        omb,
    ]
    return [story.scene(d.name("financials"), beats)]
