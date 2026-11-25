"""Pegasystems: Pega Cloud, already the largest line, grows by half while maintenance shrinks and
consulting falls in the latest quarter; quarterly revenue and operating margin swing with license timing, and on a full-year basis the
operating margin goes from a loss to a profit as free cash flow climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, seg_tags, shaped, tagged

TICKER = "PEGA"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Pega Cloud", "Maintenance"])),
        qprod and story.towers("Revenue by type, same quarter a year apart", qprod,
                               tags=[growth(qprod, "Pega Cloud", u=0.6), growth(qprod, "Consulting", u=0.85)]),
        story.bars("Quarterly revenue", "$M", q),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
