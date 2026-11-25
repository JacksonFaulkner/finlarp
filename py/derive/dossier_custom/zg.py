"""Zillow: rentals and mortgages grow far faster than the residential core, mortgages rise about three
quarters in the latest quarter against a year earlier, operating losses narrow toward breakeven, and gross margin
slides every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "ZG"
NAMES = {"Residential": "Residential", "Rental": "Rentals", "Mortgage": "Mortgages",
         "Display Advertising": "Display advertising and other"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, annual")
    beats = [
        prod and story.towers("Revenue by business", prod, tags=seg_tags(prod, ["Rentals", "Mortgages"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Mortgages"), growth(prod_q, "Rentals", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_first_to_last(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
