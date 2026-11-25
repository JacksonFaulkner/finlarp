"""Unity: Create Solutions shrinks after FY2023 and Greater China grows its share of revenue; in the
latest quarter Grow Solutions is well above a year earlier, and the operating loss narrows sharply
after a deep Q1'26 trough (gross margin fell the same quarter)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, pct_tags, seg_tags, shaped, short, tagged

TICKER = "U"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by solution", prod, tags=seg_tags(prod, ["Create", "Grow"])),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["Greater China", "Asia Pacific excluding"]),
                                        {"Asia Pacific excluding Greater China": "APAC ex-China"})),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Grow")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
