"""Caterpillar: Power and Energy grows into the largest segment while Construction Industries
shrinks, North America drives a jump in revenue by mid-2026, and the operating margin returns to
about 21% after a dip."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "CAT"
NAMES = {"Power Energy": "Power and Energy"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Power and Energy", "Construction"])),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["Power and Energy"])),
        geo_q and story.towers("By region, same quarter a year apart", geo_q, tags=[growth(geo_q, "North America")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
