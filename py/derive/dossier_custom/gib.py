"""CGI: revenue grows in every segment in FY2025, the United Kingdom and Australia most, managed IT
and business process services stay the larger half, and annual revenue rises each year from FY2021.
Figures are C$."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, short, without

TICKER = "GIB"
UNIT = "C$M"  # the Financials tab's series are the filer's C$ figures


def specs(d: Data) -> list[dict]:
    seg = shaped(without(d.history(("SegmentsAxis",)), "Geography Eliminations"))
    prod = shaped(d.history(("ProductsAndServicesAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["United Kingdom", "US Federal"]),
                                                               {"United Kingdom and Australia": "UK and Australia"})),
        prod and story.towers("Revenue by service type", prod, tags=short(seg_tags(prod, ["Managed IT"]),
                                                                    {"Managed IT and Business Process Services": "Managed IT and BPS"})),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Net margin", "%", d.points("Net margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
