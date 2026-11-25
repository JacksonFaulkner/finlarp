"""Nova: revenue rebounds from its FY2023 dip to a new high, with product and service both growing,
operating margin holds in the high 20s, and free cash flow more than doubles from its FY2022 low. Annual data
only (20-F filer)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, seg_tags, shaped, tagged

TICKER = "NVMI"


def _from_low(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    i = min(range(len(pts)), key=lambda j: pts[j][1])
    if i == len(pts) - 1 or pts[i][1] <= 0:
        return None
    (pa, a), (pb, b) = pts[i], pts[-1]
    ch = f"{b / a:.1f}x" if b / a >= 2 else f"{(b / a - 1) * 100:+.0f}%"
    return {"i": -1, "u": u, "text": f"{pa} -> {pb}: {ch}"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Product", "Service"])),
        tagged(story.bars("Annual revenue", "$M", rev), _from_low(rev)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _from_low(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
