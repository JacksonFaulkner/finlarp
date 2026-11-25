"""DoubleVerify: revenue grows every year with all three reported lines rising and Supply Side the
fastest, but operating margin slips from its FY2023 high while free cash flow keeps climbing."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, seg_tags, shaped, tagged

TICKER = "DV"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("MajorCustomersAxis",)))
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by line", seg, tags=seg_tags(seg, ["Supply Side", "Activation"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_peak_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
