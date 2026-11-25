"""Box: revenue grows steadily every year, gross margin widens by several points, the operating
margin turns from a loss to a profit, and free cash flow rises each year. Box reports no segment
breakdown, so the story is told from the Financials series."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, bars_year_ago, tagged

TICKER = "BOX"


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_first_to_last(gm, "%")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
