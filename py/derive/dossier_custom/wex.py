"""WEX: Mobility is the largest segment and leads a year-on-year jump in the latest quarter, finance
fees grow fastest among revenue types, non-US revenue shrinks while the US grows, and free cash flow
falls by more than half from its FY2023 high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, seg_tags, shaped, short, tagged

TICKER = "WEX"
NAMES = {"Non Us": "Non-US"}

# The Financials "Quarterly revenue" block (~$0.45B a quarter) is well under the segment totals
# (~$0.66B in Jun 25), so it and the margins computed from it are left out.


def _total_tag(hist: dict, u: float = 0.85) -> dict:
    a, b = story.total_of(hist, 0), story.total_of(hist)
    k = max(range(len(hist["series"])), key=lambda j: hist["series"][j][1][-1])
    return {"i": -1, "s": k, "u": u, "text": f"Total {story.money(a)} -> {story.money(b)} ({(b / a - 1) * 100:+.0f}%)"}


def specs(d: Data) -> list[dict]:
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg_q and story.towers("Revenue by segment, same quarter a year apart", seg_q,
                               tags=[*seg_tags(seg_q, ["Mobility"]), _total_tag(seg_q)]),
        prod_q and story.towers("Revenue by type, same quarter a year apart", prod_q,
                                tags=short(seg_tags(prod_q, ["Finance Fee", "Payment Processing"]),
                                           {"Finance Fee Revenue": "Finance fees",
                                            "Payment Processing Revenue": "Payment processing"})),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Non-US", "US"])),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
