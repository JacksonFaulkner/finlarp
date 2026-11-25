"""Exelon: revenue comes from its regulated utilities, Baltimore Gas and Electric and PECO grow while
Commonwealth Edison falls in FY2025, total revenue rises every year, and the operating margin
widens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, short

TICKER = "EXC"
NAMES = {"Commonwealth Edison": "Commonwealth Edison", "Baltimore Gas and Electric": "Baltimore Gas and Electric",
         "Peco Energy": "PECO Energy", "PECO Energy": "PECO Energy", "Potomac Electric Power": "Potomac Electric Power",
         "Delmarva Powerand Light": "Delmarva Power and Light", "Atlantic City Electric": "Atlantic City Electric"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by utility", seg, tags=short(seg_tags(seg, ["Baltimore", "Commonwealth"]), {"Baltimore Gas and Electric": "BGE", "Commonwealth Edison": "ComEd"})),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
