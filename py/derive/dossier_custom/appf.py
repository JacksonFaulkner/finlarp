"""AppFolio: value added services grow faster than subscriptions and make up most of revenue,
quarterly revenue climbs every quarter but one, and the annual operating margin swings from a loss
in FY2022 to the high teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, seg_tags, shaped, tagged

TICKER = "APPF"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    om_a = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by service", prod,
                              tags=seg_tags(prod, ["Value Added", "Subscription"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om_a), bars_swing(om_a, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om_q), bars_swing(om_q, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
