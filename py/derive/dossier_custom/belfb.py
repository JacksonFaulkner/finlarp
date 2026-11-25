"""Bel Fuse: after a down FY2024, Power Solutions and Protection leads the FY2025 rebound; in 2026 the
company reports two new segments, both growing on the year-ago quarter; Israel grows from zero to
the largest country line outside North America, and gross margin climbs every year from the mid-20s to near 40%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_year_ago, drop, growth, last_step, shaped,
                                         short, tagged)

TICKER = "BELFB"
NAMES = {"IL": "Israel", "CN": "China", "GB": "United Kingdom", "SK": "Slovakia", "CH": "Switzerland",
         "DE": "Germany", "IN": "India", "MO": "Macao"}
SHORT = {"Power Solutions and Protection": "Power", "Aerospace Defense and Rugged Solutions": "Aerospace/defense",
         "Industrial Technology and Data Solutions": "Industrial/data"}


def specs(d: Data) -> list[dict]:
    seg = shaped(drop(d.history(("StatementBusinessSegmentsAxis",)), "Corporate"))
    qseg = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(drop(d.history(("StatementGeographicalAxis",)), "North America"), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short([last_step(seg, "Power")], SHORT)),
        qseg and story.towers("Revenue by new segment, same quarter a year apart", qseg,
                              tags=short([growth(qseg, "Aerospace", u=0.6), growth(qseg, "Industrial", u=0.85)], SHORT)),
        geo and story.towers("Revenue outside North America by country", geo, tags=[growth(geo, "Israel")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_first_to_last(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
