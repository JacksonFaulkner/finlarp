"""APi Group: Life Safety is the largest line and adds the most revenue, Safety Services earns most of the
segment operating income, and gross margin climbs every year from FY2021."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, share, tagged

TICKER = "APG"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    beats = [
        prod and story.towers("Revenue by service line", prod, tags=seg_tags(prod, ["Life Safety"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Safety Services")]),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Specialty Contracting")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm)),
    ]
    return [story.scene(d.name("financials"), beats)]
