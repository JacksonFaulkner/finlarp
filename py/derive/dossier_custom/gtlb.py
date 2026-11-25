"""GitLab: annual revenue grows nearly 4x in four years with SaaS subscriptions the fastest-growing
line, the annual operating loss narrows from about -51% to about -7%, but gross margin drifts down and
the latest quarter's operating margin falls back to about -20%; annual free cash flow turns clearly
positive in FY2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_swing, bars_year_ago, seg_tags,
                                         shaped, tagged)

TICKER = "GTLB"
NAMES = {"Subscription Software As A Service": "Subscription Software as a Service"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=story.short(
            seg_tags(prod, ["Subscription Software", "Subscription and"]),
            {"Subscription Software as a Service": "SaaS subscription"})),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin", "%", om_q), bars_year_ago(om_q, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
