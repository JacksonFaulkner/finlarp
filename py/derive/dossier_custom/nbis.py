"""Nebius Group: since FY2023 (earlier XBRL history is the predecessor, Yandex) the Nebius AI cloud
segment grows from almost nothing to nearly all revenue, and the US becomes the largest region.
Only the periods the segment history covers are shown."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "NBIS"
NAMES = {"Triple Ten": "TripleTen", "GB": "United Kingdom", "Segment Geographical Area Other": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    keep = set(seg["periods"]) if seg else set()  # the current business only, not the predecessor's years
    rev = [p for p in d.points("Annual revenue") if p[0] in keep]
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Nebius", "TripleTen"])),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["Nebius"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "United Kingdom"])),
        story.bars("Annual revenue", "$M", rev),
    ]
    return [story.scene(d.name("financials"), beats)]
