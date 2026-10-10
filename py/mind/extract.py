"""Pull linkable world entities out of free text."""
from __future__ import annotations

import re
from functools import lru_cache

from sources import universe

_PATENT = re.compile(r"\b(?:US\s?)?(\d{1,2}[,]?\d{3}[,]?\d{3})\b")
_ACCN = re.compile(r"\b\d{10}-\d{2}-\d{6}\b")
_CASHTAG = re.compile(r"\$([A-Za-z]{1,5})\b")
_CAPS = re.compile(r"\b[A-Z]{2,5}\b")
# Common words that collide with tickers; only match when written as $TICKER.
_AMBIGUOUS = {"AI", "IT", "ON", "ALL", "ARE", "FOR", "NOW", "ONE", "CAN", "SO", "UP", "OR", "AN", "BE", "BY", "PEG", "CEO", "CFO", "EPS", "IPO", "GAAP"}


@lru_cache(maxsize=1)
def _tickers() -> frozenset[str]:
    return frozenset(s["ticker"].upper() for s in universe.rows())


def entities(text: str) -> list[str]:
    known = _tickers()
    out: list[str] = []
    for m in _CASHTAG.findall(text):
        if m.upper() in known:
            out.append(f"ticker:{m.upper()}")
    for m in _CAPS.findall(text):
        if m in known and m not in _AMBIGUOUS:
            out.append(f"ticker:{m}")
    for m in _ACCN.findall(text):
        out.append(f"filing:{m}")
    for m in _PATENT.findall(text):
        out.append(f"patent:{m.replace(',', '')}")
    return list(dict.fromkeys(out))
