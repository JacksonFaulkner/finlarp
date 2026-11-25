"""monday.com: annual revenue roughly quadruples in four years while the operating loss shrinks to
breakeven, net margin turns positive and free cash flow grows from almost nothing."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, tagged

TICKER = "MNDY"


def specs(d: Data) -> list[dict]:
    # monday.com files annual reports only here: no segment facts and no quarterly series.
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    nm = d.points("Net margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Net margin, annual", "%", nm), bars_swing(nm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
