"""Meta: the Family of Apps is nearly all revenue and earns the profit, Reality Labs loses more each
year, and operating margin falls by half within 2026."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, series_bars, shaped

TICKER = "META"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    rl = series_bars("Reality Labs operating income", oi, "Reality Labs")
    if rl:
        loss = -sum(v for _, v in rl["points"] if v < 0)
        rl["tags"] = [{"i": -1, "text": f"{len(rl['points'])}-year loss ${loss / 1e3:.1f}B", "u": 0.75}]
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Family of Apps"])),
        series_bars("Family of Apps operating income", oi, "Family of Apps"),
        rl,
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
