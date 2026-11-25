"""TTM Technologies: data center computing more than doubles in two years beside a growing aerospace
and defense business, data center and networking more than doubles again in the latest quarter
against a year earlier, and quarterly operating margin climbs from about 1% to over 13%, while annual
free cash flow falls from its FY2022 high to about zero."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, bars_year_ago, seg_tags, shaped, short, tagged

TICKER = "TTMI"
SHORT = {"Aerospace and Defense Components": "A&D components", "Data Center Computing": "Data center",
         "Medical Industrial Instrumentation": "Medical/industrial", "Data Center and Networking": "DC & networking"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by end market", prod, tags=short(seg_tags(prod, ["Data Center", "Aerospace"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=short(seg_tags(prod_q, ["Data Center", "Medical"]), SHORT)),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Aerospace", "Commercial"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
