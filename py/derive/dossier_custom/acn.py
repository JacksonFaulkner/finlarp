"""Accenture: managed services overtakes consulting as the larger half of revenue, EMEA's operating
income grows while Asia Pacific's barely moves, and quarterly revenue stays near flat with operating
margin in the teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "ACN"
NAMES = {"Managed Services Revenue": "Managed Services", "Consulting Revenue": "Consulting"}
INDUSTRY = {"Communications Media and Technology": "Communications, Media and Technology",
            "Health and Public Service": "Health and Public Service"}


def specs(d: Data) -> list[dict]:
    kind = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    ind = shaped(d.history(("EquitySecuritiesByIndustryAxis",)), INDUSTRY)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        kind and story.towers("Revenue by type of work", kind, tags=seg_tags(kind, ["Managed", "Consulting"])),
        ind and story.towers("Revenue by industry group", ind, tags=seg_tags(ind, ["Financial", "Communications"])),
        oi and story.towers("Operating income by geographic segment", oi, tags=seg_tags(oi, ["EMEA", "Asia Pacific"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
