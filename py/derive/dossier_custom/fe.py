"""FirstEnergy: regulated US electricity is most of revenue, transmission and unregulated revenue grow
faster year on year, revenue rises each year, and free cash flow stays negative since FY2022."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, short

TICKER = "FE"
NAMES = {"Electricity Us Regulated": "Electricity US Regulated",
         "Electric Worldwide Unregulated": "Electric Worldwide Unregulated"}
SHORT = {"Electricity US Regulated": "US regulated", "Electric Worldwide Unregulated": "Unregulated",
         "Electric Transmission": "Transmission"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    fcf = story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual"))
    if fcf:
        neg = [v for _, v in fcf["points"] if v < 0]
        if neg:
            fcf["tags"], fcf["auto_tags"] = [{"i": -1, "u": 0.75, "text": f"{len(neg)} negative years, ${-sum(neg) / 1e3:.1f}B total"}], False
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Electricity US", "Electric Transmission"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Electric Transmission", u=0.6),
                                            growth(prod_q, "Electric Worldwide", u=0.85)], SHORT)),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
