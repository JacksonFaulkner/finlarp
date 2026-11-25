"""Entergy: Entergy Louisiana is the largest operating utility, revenue swings with the seasons,
operating margin drifts lower, and free cash flow stays negative year after year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, shaped, share

TICKER = "ETR"


def specs(d: Data) -> list[dict]:
    # the annual legal-entity split misses Entergy Louisiana; the quarterly one carries it
    ent_q = shaped(d.history(("LegalEntityAxis",), cadence="quarterly", n=2))
    fcf = story.bars("Free cash flow", "$M", d.points("Free cash flow, annual"))
    if fcf:
        pts = fcf["points"]
        neg = sum(1 for _, v in pts if v < 0)
        if neg >= 2:
            fcf["tags"] = [{"i": -1, "u": 0.8, "text": f"negative in {neg} of {len(pts)} years"}]
    beats = [
        ent_q and story.towers("Revenue by utility, same quarter a year apart", ent_q,
                               tags=[share(ent_q, "Entergy Louisiana", u=0.55), growth(ent_q, "Entergy Mississippi", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
