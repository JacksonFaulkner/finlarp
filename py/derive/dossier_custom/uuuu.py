"""Energy Fuels: uranium is the main revenue line and heavy mineral sands come and go, every segment
loses money and the combined segment loss nearly triples in FY2025, and free cash flow burn deepens.
Operating margin is left out: at -60% to -1,100% on small revenue it swamps the frame."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, growth, seg_tags, shaped, tagged

TICKER = "UUUU"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    loss = None
    if oi:  # towers cannot draw losses: the segments' combined operating income as bars
        tot = [[p, round(sum(vs[i] for _, vs in oi["series"]), 1)] for i, p in enumerate(oi["periods"])]
        loss = {"panel": "bars", "title": "Segment operating income, all segments", "unit": oi["unit"],
                "points": tot, "srcs": oi["srcs"]}
        loss = tagged(loss, bars_first_to_last(tot, oi["unit"]))
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Uranium", "Heavy Mineral"])),
        seg_q and story.towers("Same quarter a year apart, by segment", seg_q, tags=[growth(seg_q, "Uranium")]),
        loss,
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
