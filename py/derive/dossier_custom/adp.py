"""ADP: every revenue line grows, interest on client funds fastest, revenue peaks each fiscal Q3,
and net margin edges up year after year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "ADP"
NAMES = {"Interest on Funds Held for Clients": "Interest on client funds",
         "PEO Zero Margin Benefits Pass Throughs": "PEO zero-margin pass-throughs"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    beats = [
        prod and story.towers("Revenue by line", prod, tags=seg_tags(prod, ["Interest on client", "HCM"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Net margin, annual", "%", d.points("Net margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
