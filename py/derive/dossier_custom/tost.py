"""Toast: technology service revenue grows every year and makes up most of the total, quarterly
revenue keeps climbing, and the operating margin turns from a loss to a profit that widens each
year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, tagged

TICKER = "TOST"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    q = d.points("Quarterly revenue")
    om_a = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Technology Service", "License"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om_a), bars_swing(om_a)),
        tagged(story.bars("Operating margin, quarterly", "%", om_q), bars_year_ago(om_q, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
