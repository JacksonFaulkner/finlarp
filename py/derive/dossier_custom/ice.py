"""Intercontinental Exchange: Exchanges stay the bulk of revenue while Mortgage Technology grows
into a third segment and turns its operating loss into a small profit; in the latest quarter cash
equities and options grow while energy futures shrink."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, series_bars, shaped

TICKER = "ICE"
NAMES = {"Cash Equityand Equity Options": "Cash equity and equity options",
         "Fixed Income Data and Analytics": "Fixed income data and analytics",
         "Energy Futures": "Energy futures and options", "Agriculturaland Metals": "Agricultural and metals futures and options"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    mt = series_bars("Mortgage Technology operating income", oi, "Mortgage Technology")
    if mt:
        (pa, a), (pb, b) = mt["points"][0], mt["points"][-1]
        money = lambda v: ("loss " if v < 0 else "") + f"${abs(v):,.0f}M"  # noqa: E731
        mt["tags"], mt["auto_tags"] = [{"i": -1, "u": 0.75, "text": f"{pa} {money(a)} -> {pb} {money(b)}"}], False
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Mortgage Technology", "Exchanges"])),
        mt,
        prod_q and story.towers("By product, same quarter a year apart", prod_q,
                                tags=seg_tags(prod_q, ["Cash equity", "Energy futures"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
