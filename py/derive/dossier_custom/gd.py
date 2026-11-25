"""General Dynamics: Aerospace and Marine Systems drive the growth, Aerospace earns the most
operating income, non-US commercial sales rise fastest among customers, and revenue climbs each year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "GD"
CUST = {"U. S. Government Department of War": "U.S. Department of War",
        "U. S. Government Non Department of War": "U.S. Government, other",
        "U. S. Government Foreign Military Sales": "U.S. Foreign Military Sales",
        "U. S. Commercial": "U.S. commercial", "Non U. S. Commercial": "Non-U.S. commercial",
        "Non US Government": "Non-U.S. government"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    cust = shaped(d.history(("MajorCustomersAxis",)), CUST)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Aerospace", "Marine"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Aerospace"), growth(oi, "Marine", u=0.85)]),
        cust and story.towers("Revenue by customer", cust,
                              tags=[growth(cust, "Non-U.S. commercial", u=0.55), growth(cust, "U.S. Department", u=0.8)]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
    ]
    return [story.scene(d.name("financials"), beats)]
