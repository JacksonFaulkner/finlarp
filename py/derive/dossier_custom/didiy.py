"""DiDi: annual revenue dips in FY2022 and then climbs past its FY2021 level, while the operating margin
climbs from a deep loss in FY2021 to just above break-even in FY2024 and free cash flow turns positive
in FY2023. Figures are CNY (20-F); the filing has no segment breakdown in XBRL."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, tagged

TICKER = "DIDIY"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's RMB figures


def specs(d: Data) -> list[dict]:
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
        tagged(story.bars("Free cash flow, annual", UNIT, fcf), bars_swing(fcf, UNIT)),
    ]
    return [story.scene(d.name("financials"), beats)]
