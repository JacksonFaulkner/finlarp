"""IonQ: revenue triples in FY2025 with quantum hardware and services both growing, sales outside the US
(Switzerland, South Korea) jump in a year, and the cash burn widens as it scales."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, short, tagged

TICKER = "IONQ"
NAMES = {"Platform Consulting": "Platform, consulting and support"}
GEO = {"Non Us": "Other non-US", "CH": "Switzerland", "KR": "South Korea", "US": "United States"}
SHORT = {"Platform, consulting and support": "Services"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    rev = d.points("Annual revenue")
    fcf = d.points("Free cash flow, annual")
    low = min(fcf, key=lambda p: p[1]) if fcf else None
    # (Operating margin is left out: at -400% to -1,000% on small revenue it swamps the frame.)
    beats = [
        prod and story.towers("Revenue by product / service", prod,
                              tags=short(seg_tags(prod, ["Quantum Hardware", "Platform"]), SHORT)),
        geo_q and story.towers("Same quarter a year apart, by country", geo_q,
                               tags=[growth(geo_q, "South Korea", u=0.55), growth(geo_q, "United States", u=0.8)]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_swing(rev, "$M")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        low and tagged(story.bars("Free cash flow, annual", "$M", fcf),
                       {"i": fcf.index(low), "u": 0.75, "text": f"{low[0]} burn {story.money(-low[1])}"}),
    ]
    return [story.scene(d.name("financials"), beats)]
