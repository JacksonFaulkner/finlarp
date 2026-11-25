"""Crown Castle: free cash flow nearly doubles in FY2023 and holds near that level, then the latest two
quarters come in lower. (The Financials tab's revenue and margin series for CCI look broken, so the
story uses cash flow only.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago

TICKER = "CCI"


def specs(d: Data) -> list[dict]:
    q = d.points("Free cash flow, quarterly")
    qb = story.bars("Free cash flow, quarterly", "$M", q)
    if qb and (t := bars_year_ago(q, "$M")):
        qb["tags"] = [t]
        qb["auto_tags"] = False
    beats = [
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
        qb,
    ]
    return [story.scene(d.name("financials"), beats)]
