"""NXP: distributors carry a steady ~$7B while direct sales shrink, Germany's share falls as China's
rises, sales through intermediaries jump in the latest quarter, and gross margin edges up toward 58%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "NXPI"
GEO = {"DE": "Germany", "CN": "China", "JP": "Japan", "KR": "Korea", "TW": "Taiwan", "SG": "Singapore",
       "NL": "Netherlands", "Other Countries": "Other countries"}


def specs(d: Data) -> list[dict]:
    ch = shaped(d.history(("ContractWithCustomerSalesChannelAxis",)))
    ch_q = shaped(d.history(("ContractWithCustomerSalesChannelAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        ch and story.towers("Revenue by sales channel", ch, tags=seg_tags(ch, ["Distributors", "Direct"])),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["Germany", "China"])),
        ch_q and story.towers("Sales channel, same quarter a year apart", ch_q, tags=[growth(ch_q, "Through")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
