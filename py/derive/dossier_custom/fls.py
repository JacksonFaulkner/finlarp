"""Flowserve: aftermarket outgrows original equipment and original equipment falls year over year
in the latest quarter, FPD segment operating income rises by about 70% in two years, gross margin
widens each year, and the operating margin rebounds after a late-2025 dip."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, seg_tags, shaped, tagged

TICKER = "FLS"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Aftermarket", "Original"])),
        prod_q and story.towers("By type, same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Original", u=0.55), growth(prod_q, "Aftermarket", u=0.8)]),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["FPD", "FCD"])),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_first_to_last(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
