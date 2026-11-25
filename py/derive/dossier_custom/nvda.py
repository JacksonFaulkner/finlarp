"""NVIDIA: compute and networking carry the jump, China shrinks to a single-digit share, hyperscalers
double in a year, and gross margin holds in the mid-70s apart from one quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags

TICKER = "NVDA"


def specs(d: Data) -> list[dict]:
    beats = []
    seg = d.history(("ProductOrServiceAxis",))
    if seg:
        beats.append(story.towers("Revenue by product line", seg, tags=seg_tags(seg, ["Compute", "Networking"])))
    geo = d.history(("StatementGeographicalAxis",))
    if geo:
        beats.append(story.towers("Revenue share by region", geo, pct=True,
                                  tags=pct_tags(geo, ["US", "China including Hong Kong"])))
    q = d.points("Quarterly revenue")
    if q:
        beats.append(story.bars("Quarterly revenue", "$M", q))
    cust = d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2)
    if cust and any(n.startswith("Hyperscale") for n, _ in cust["series"]):
        beats.append(story.towers("Data Center by customer, same quarter a year apart", cust,
                                  tags=[growth(cust, "Hyperscale")]))
    gm = d.points("Gross margin, quarterly")
    if gm:
        beats.append(story.bars("Gross margin", "%", gm))
    return [story.scene(d.name("financials"), beats)] if beats else []
