"""Dossier tabs, one module each. Every module exposes

    section(t, con, F, prof) -> {"id", "title", "blocks"} | None

where `t` is the ticker, `con` a DuckDB connection, `F` the dossier.Filings for
the ticker and `prof` the profile row (or None). Modules import helpers from
derive.dossier (src, derived, archive, ixbrl, Filings, _money, _pct, _is_new);
dossier.build() imports this package lazily, so no import cycle.

TAB_BUILDERS sets the tab order: (section id, builder).
"""
from derive.dossier_tabs import (earnings, filings, financials, mine, news, ownership, peers, positioning, price,
                                 sentiment, valuation)

TAB_BUILDERS = [
    ("price", price.section),
    ("financials", financials.section),
    ("valuation", valuation.section),
    ("earnings", earnings.section),
    ("filings", filings.section),
    ("ownership", ownership.section),
    ("positioning", positioning.section),
    ("sentiment", sentiment.section),
    ("news", news.section),
    ("peers", peers.section),
    ("mine", mine.section),
]
