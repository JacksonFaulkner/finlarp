"""TSMC: high-performance computing (AI accelerators and CPUs) passes smartphones and takes most of
the revenue, one customer grows to about a fifth of it, and margins rise with it. Figures are
NT$ (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import of_total, pct_tags, seg_tags, shaped, total_of

TICKER = "TSM"
UNIT = "NT$M"  # the Financials tab's series are the 20-F's NT$ figures


def specs(d: Data) -> list[dict]:
    mkt = shaped(d.history(("MarketsOfCustomersAxis",)))
    cust = d.history(("MajorCustomersAxis",))
    beats = [
        mkt and story.towers("Revenue by end market", mkt, tags=seg_tags(mkt, ["High Performance", "Smartphone"])),
        mkt and story.towers("Revenue share by end market", mkt, pct=True, tags=pct_tags(mkt, ["High Performance"])),
        cust and mkt and story.towers("Largest customers (named A, B in the 20-F)", cust,
                                      tags=[of_total(cust, "Customer A", total_of(mkt), f"{mkt['periods'][-1]} revenue")]),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
