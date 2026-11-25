"""Carrier: the Europe segment more than doubles in FY2024 while Transportation shrinks, Americas
earns most of the segment profit, and the quarterly operating margin sinks to low single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, share

TICKER = "CARR"
NAMES = {"Climate Solutions Americas": "Americas", "Climate Solutions Europe": "Europe",
         "Climate Solutions Asia": "Asia Pacific, Middle East & Africa", "Climate Solutions CSAME": "CSAME",
         "Climate Solutions Transportation": "Transportation"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Europe", "Transportation"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "Americas")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
