"""Cloudflare: revenue sold through intermediaries grows fastest and takes a bigger share, while
gross margin slides from the high 70s and the operating loss margin deepens in the latest quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "NET"
AX = ("ContractWithCustomerSalesChannelAxis",)


def _of_revenue(tags: list[dict]) -> list[dict]:
    """pct_tags text without the period range ('<name> a% -> b% of revenue'), to fit the frame."""
    return [{**t, "text": t["text"].split(" (")[0] + " of revenue"} for t in tags]


def specs(d: Data) -> list[dict]:
    ch = shaped(d.history(AX))
    ch_q = shaped(d.history(AX, cadence="quarterly", n=2))
    beats = [
        ch and story.towers("Revenue by sales channel", ch, tags=seg_tags(ch, ["Through intermediary"])),
        ch and story.towers("Revenue share by sales channel", ch, pct=True, tags=_of_revenue(pct_tags(ch, ["Through intermediary"]))),
        ch_q and story.towers("Same quarter a year apart", ch_q, tags=[growth(ch_q, "Through intermediary")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
