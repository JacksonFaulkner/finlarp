"""BILL: spend and expense interchange is the fastest-growing revenue line while interest on customer
funds shrinks, revenue grows every year, the operating loss narrows towards breakeven and free cash
flow turns from a burn into a steady inflow."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, pct_tags, seg_tags, shaped, short, tagged

TICKER = "BILL"
NAMES = {"Accounts Payable and Accounts Receivable": "AP and AR",
         "Spend and Expense Interchange": "Spend and expense interchange",
         "Interest on Funds Held": "Interest on customer funds",
         "Embedded and Other": "Embedded and other"}
SHORT = {"Spend and expense interchange": "Interchange", "Interest on customer funds": "Interest"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product", prod,
                              tags=short(seg_tags(prod, ["Spend", "Interest"]), SHORT)),
        prod and story.towers("Revenue share by product", prod, pct=True,
                              tags=short(pct_tags(prod, ["Spend"]), SHORT)),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
