"""Jack Henry: revenue grows every year to about $2.5B with Payments, Core and Complementary all
rising, in-house support is the one revenue line that shrinks, annual operating margin recovers from
its FY2024 low, and free cash flow doubles from its FY2023 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, tagged

TICKER = "JKHY"
NAMES = {"Outsourcing Cloud": "Outsourcing and cloud", "In House Support": "In-house support",
         "Product Deliveryand Service": "Product delivery and service"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Payments", "Complementary"])),
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Outsourcing", "In-house"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
