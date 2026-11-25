"""Rambus: annual revenue more than doubles from FY2021 as the operating margin climbs from single
digits to the mid-30s; in the latest quarter against a year earlier product revenue leads the growth,
China roughly doubles and Korea, still the largest region, shrinks. Segment data is quarterly only."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, seg_tags, shaped, tagged

TICKER = "RMBS"
NAMES = {"Contractandother": "Contract and other revenue", "KR": "Korea", "SG": "Singapore", "CN": "China"}


def specs(d: Data) -> list[dict]:
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        prod_q and story.towers("Revenue by type, same quarter a year apart", prod_q,
                                tags=seg_tags(prod_q, ["Product", "Royalty"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=seg_tags(geo_q, ["China", "Korea"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
