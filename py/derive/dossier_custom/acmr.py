"""ACM Research: cleaning equipment is still the largest line, but ECP, furnace and other tools grow
fastest and more than double in the latest quarter year on year; gross and operating margin dip in
late 2025 and recover in 2026, while free cash flow is negative in four of five years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_low, bars_swing, bars_total, bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "ACMR"
NAMES = {"Total Single Wafer": "Single Wafer and Semi Critical Cleaning Equipment"}
SHORT = {"Single Wafer and Semi Critical Cleaning Equipment": "Cleaning",
         "ECP Front End and Packaging Furnace and Other Technologies": "ECP, furnace, other",
         "Advanced Packaging Exclude ECP Services Spares": "Adv. packaging"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product line", prod,
                              tags=short(seg_tags(prod, ["Single Wafer", "ECP"]), SHORT)),
        qprod and story.towers("Revenue by product line, same quarter a year apart", qprod,
                               tags=short([growth(qprod, "ECP", u=0.6), growth(qprod, "Advanced", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_low(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
