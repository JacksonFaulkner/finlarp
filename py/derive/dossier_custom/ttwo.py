"""Take-Two: mobile is the largest line, console revenue jumps in FY2026 while advertising shrinks,
the deep operating losses of FY2024-FY2025 close to near breakeven, and free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped

TICKER = "TTWO"


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by platform", prod, tags=seg_tags(prod, ["Console", "Advertising"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Console", u=0.6), growth(prod_q, "Mobile", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
