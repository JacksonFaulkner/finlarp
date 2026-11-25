"""American Electric Power: the vertically integrated utilities grow most in dollars and generation
and marketing fastest, AEP Transmission and Indiana Michigan Power lead the subsidiaries, and the
annual operating margin rises to the mid-20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "AEP"
NAMES = {"Transmission and Distribution Companies": "Transmission and distribution cos.",
         "Vertically Integrated Utilities": "Vertically integrated", "AEP Transmission Company": "AEP Transmission Co.",
         "Indiana Michigan Power": "Indiana Michigan Power", "Southwestern Electric Power": "Southwestern Electric Power",
         "Public Service Company of Oklahoma": "Public Service Co. of Oklahoma", "Ohio Power Company": "Ohio Power"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    ent = shaped(d.history(("LegalEntityAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Vertically integrated", "Generation and Marketing"])),
        ent and story.towers("Revenue by operating company", ent,
                             tags=seg_tags(ent, ["AEP Transmission", "Indiana Michigan"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
