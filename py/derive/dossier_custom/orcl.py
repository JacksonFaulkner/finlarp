"""Oracle: Cloud Infrastructure revenue more than doubles in two years and again year on year by
August 2026 while license and support stay flat, the operating margin edges up, and free cash flow
turns deeply negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, series_bars, shaped

TICKER = "ORCL"


def _usd(hist: dict | None) -> dict | None:
    """Oracle's segment facts carry the unit as "U_USD", which Data.history does not map; it is USD."""
    if hist and hist.get("unit", "").startswith("U_USD"):
        return {**hist, "unit": "$M"}
    return hist


def specs(d: Data) -> list[dict]:
    seg = _usd(shaped(d.history(("StatementBusinessSegmentsAxis",))))
    prod = _usd(d.history(("ProductOrServiceAxis",)))
    prod_q = _usd(shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2)))
    oci = series_bars("Cloud Infrastructure revenue", prod, "Cloud Infrastructure")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Cloud and Software"])),
        oci,
        prod_q and story.towers("Cloud and license lines, same quarter a year apart", prod_q,
                                tags=seg_tags(prod_q, ["Cloud Infrastructure", "Cloud Applications"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", fcf),
    ]
    return [story.scene(d.name("financials"), beats)]
