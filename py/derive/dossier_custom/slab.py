"""Silicon Labs: revenue falls by almost half from FY2022 to FY2024 and then rebounds, both product
lines recover, Taiwan grows fastest in the latest quarter, gross margin climbs and operating losses
narrow. Net margin is left out (its FY2021 value is near 300%)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, seg_tags, shaped, tagged

TICKER = "SLAB"
NAMES = {"Industrial": "Industrial & Commercial", "Home": "Home & Life", "TW": "Taiwan", "CN": "China",
         "Rest of World": "Rest of world"}


def _fall(pts: list[list], u: float = 0.75) -> dict | None:
    """'<peak> -> <low>: -n%' for the drop before the rebound."""
    if len(pts) < 3:
        return None
    hi = max(range(len(pts)), key=lambda i: pts[i][1])
    lo = min(range(hi, len(pts)), key=lambda i: pts[i][1])
    if lo == hi or pts[hi][1] <= 0:
        return None
    return {"i": lo, "u": u, "text": f"{pts[hi][0]} -> {pts[lo][0]}: {(pts[lo][1] / pts[hi][1] - 1) * 100:+.0f}%"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), _fall(rev)),
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["Industrial", "Home"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "Taiwan"), growth(geo_q, "China", u=0.85)]),
        tagged(story.bars("Gross margin", "%", gm), bars_first_to_last(gm, "%")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
