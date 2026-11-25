"""Calix: software and service revenue grows every year while appliance sales dip in FY2024 and recover;
quarterly revenue rises in every quarter shown, the quarterly operating margin goes from a loss to a
profit, and free cash flow more than doubles in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, money, pct_tags, seg_tags, shaped, tagged

TICKER = "CALX"


def _fcf_step(fcf: list[list]) -> dict | None:
    """'<prev> $a -> <last> $b (k.kx)' for the last year-over-year step."""
    if len(fcf) < 2 or fcf[-2][1] <= 0:
        return None
    (pa, a), (pb, b) = fcf[-2], fcf[-1]
    return {"i": -1, "u": 0.75, "text": f"{pa} {money(a)} -> {pb} {money(b)} ({b / a:.1f}x)"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Software", "Appliance"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Software"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_first_to_last(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _fcf_step(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
