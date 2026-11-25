"""Braze: subscription revenue keeps compounding and professional services more than doubles
in the latest quarter, gross margin slips a few points, and the operating loss margin narrows
as free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_peak_to_last, bars_swing, growth, seg_tags, shaped, short,
                                         tagged)

TICKER = "BRZE"
NAMES = {"Subscription Revenue": "Subscription", "Professional Services Revenue": "Professional services"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product / service", prod, tags=seg_tags(prod, ["Subscription"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Professional", u=0.8), growth(prod_q, "Subscription", u=0.5)],
                                           {"Professional services": "Services"})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
