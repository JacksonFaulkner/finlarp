"""Southern Company: Georgia Power carries most of the revenue growth, revenue swings with the seasons,
and free cash flow is negative in most recent years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "SO"


def specs(d: Data) -> list[dict]:
    ent = shaped(d.history(("LegalEntityAxis",)))
    fcf = story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual"))
    if fcf:
        neg = sum(1 for _, v in fcf["points"] if v < 0)
        fcf["tags"] = [{"i": len(fcf["points"]) // 2, "u": 0.75, "text": f"Negative in {neg} of {len(fcf['points'])} years"}]
    beats = [
        ent and story.towers("Revenue by operating company", ent, tags=seg_tags(ent, ["Georgia Power", "Alabama Power"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
