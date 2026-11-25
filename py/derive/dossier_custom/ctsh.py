"""Cognizant: revenue grows in every industry segment, Products and Resources fastest, while segment
operating income is lower in FY2025 than FY2023, and quarterly operating margin moves up from the
mid-14s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, short, total_swing

TICKER = "CTSH"
NAMES = {"Productsand Resources": "Products and Resources", "Communications": "Communications, Media and Technology"}
SHORT = {"Communications, Media and Technology": "CMT"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    beats = [
        seg and story.towers("Revenue by industry segment", seg,
                             tags=short(seg_tags(seg, ["Products and Resources", "Health Sciences"]), SHORT)),
        oi and story.towers("Segment operating income", oi, tags=[total_swing(oi)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
