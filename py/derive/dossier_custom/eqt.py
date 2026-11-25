"""EQT: a Transmission segment appears in FY2024 and grows into a real share of operating income beside
upstream gas, annual revenue sits below its FY2022 peak, the latest quarter is down on a year earlier, and
quarterly operating margin recovers from a loss."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, share

TICKER = "EQT"


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Segment revenue (before eliminations)", seg,
                             tags=seg_tags(seg, ["Upstream", "Transmission"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Transmission")]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
