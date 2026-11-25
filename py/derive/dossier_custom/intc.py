"""Intel: client computing stays most of revenue and profit while Datacenter and AI's operating
income more than triples, China's share of revenue falls, and the business runs operating losses
and negative free cash flow before turning back up in mid-2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, shaped, share

TICKER = "INTC"
GEO = {"China including Hong Kong": "China incl. Hong Kong", "SG": "Singapore", "TW": "Taiwan",
       "Other Countries": "Other"}


def _without(hist: dict | None, prefix: str) -> dict | None:
    """`hist` minus one series (Intel Foundry's revenue is mostly sales to Intel's own products)."""
    if not hist:
        return None
    return {**hist, "series": [s for s in hist["series"] if not s[0].startswith(prefix)]}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = _without(shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)), "Intel Foundry")
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[share(seg, "Client Computing", u=0.55), growth(seg, "Datacenter", u=0.7)]),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Datacenter")]),
        seg_q and story.towers("Product segments, same quarter a year apart", seg_q, tags=[growth(seg_q, "Datacenter")]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
