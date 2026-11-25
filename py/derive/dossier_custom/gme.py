"""GameStop: hardware and software sales shrink while collectibles grow, Canada and Europe fall away,
segment operating income turns from a loss to a profit carried by the United States, and quarterly
operating margin climbs from below zero to about 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, tagged, total_swing, yoy

TICKER = "GME"
NAMES = {"Videogamehardwareaccessories": "Hardware and Accessories", "Pre Owned": "Pre-Owned and Refurbished"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Collectibles", "Software"])),
        geo and story.towers("Revenue by segment", geo, tags=seg_tags(geo, ["Europe", "Canada"])),
        oi and story.towers("Segment operating income (losses drawn as 0)", oi,
                            tags=[total_swing(oi), growth(oi, "United States", u=0.5)]),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[yoy(prod_q, "Collectibles", u=0.55), yoy(prod_q, "Video Games", u=0.85)]),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
