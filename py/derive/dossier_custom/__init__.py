"""Custom diagram stories for single tickers, written in template panels (tpl_kit.py).

The generic compositions (dossier_diagrams.COMPOSITIONS) give every ticker the same three
beats. A custom module tells one company's story instead: which segment exploded, which region
shrank, where margins went. It is still all templates, so there is no Blender code per ticker,
and still all sourced: every number comes from `Data` (SEC XBRL via the dossier's own tab
builders and the segment facts), never typed into the module.

A module here defines

    TICKER = "NVDA"
    def specs(d: Data) -> list[dict]     # one spec per dossier tab, name = d.name("<tab id>")

and wins over the generic composition for the tabs it covers. Beats may carry `tags`
(custom callouts, see tpl_kit.py) and `auto_tags: false` to replace the default ones.
"""
from __future__ import annotations

import importlib
import re
import pkgutil
from functools import cache

from derive.dossier import _member


# XBRL unit -> the panels' money unit (millions); tpl_kit.fmt prints the prefix before the number
CURRENCY = {"USD": "$M", "TWD": "NT$M", "EUR": "EUR M", "JPY": "JPY M", "KRW": "KRW M", "CNY": "CNY M",
            "GBP": "GBP M", "CAD": "C$M", "HKD": "HK$M"}


def iso(unit: str | None) -> str:
    """The ISO currency in an XBRL unit id: "usd", "iso4217:TWD", "U_USD", "UNIT_STANDARD_EUR_ab12"."""
    u = (unit or "USD").upper()
    m = re.search(r"(?:^|[:_])([A-Z]{3})(?:_|$)", u)
    code = m.group(1) if m else "USD"  # opaque ids ("U002") are the filer's own label for USD
    return "USD" if code in ("STANDARD", "UNIT") else code


def _q(xs) -> str:
    return ", ".join(f"'{x}'" for x in xs)  # constants from code, not user input


class Data:
    """One ticker's sourced numbers, shaped for panels. Values in $M."""

    def __init__(self, ticker: str, con, F, financials: dict | None):
        self.t, self.con, self.F = ticker, con, F
        self.blocks = (financials or {}).get("blocks") or []

    def name(self, tab: str) -> str:
        from derive.dossier_diagrams import scene_name
        return scene_name(self.t, tab)

    # ---- the Financials tab's own blocks ----

    def block(self, prefix: str) -> dict | None:
        return next((b for b in self.blocks if (b.get("title") or "").startswith(prefix)), None)

    def points(self, prefix: str) -> list[list]:
        b = self.block(prefix) or {}
        return [[p["x"], p["y"]] for p in b.get("points") or [] if p.get("y") is not None]

    # ---- segment facts over time ----

    def history(self, axes: tuple[str, ...], cadence: str = "annual", n: int = 5, oi: bool = False) -> dict | None:
        """Revenue by member of the first axis in `axes` with data, per period (oldest first):
        {"periods": [...], "series": [[label, [v per period]]], "srcs": [...]}. The member set is
        the non-overlapping split of the latest period (see dossier_diagrams.partition), held for
        every period so the towers compare like with like. `oi`: segment operating income for the
        same members instead of revenue (members with no OI fact are left out; losses are kept as
        negatives in `series` and towers draw them as 0)."""
        from derive.dossier_diagrams import partition
        from sources import sec_segments

        days = "> 300" if cadence == "annual" else "BETWEEN 80 AND 100"
        for axis in axes:
            rows = self.con.execute(f"""
                SELECT member, period_end, value, accn, concept, unit
                FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
                WHERE ticker = ? AND axis IN ({_q([axis, 'srt:' + axis, 'us-gaap:' + axis])})
                  AND period_start IS NOT NULL AND date_diff('day', period_start, period_end) {days}
                  AND concept {"" if oi else "NOT"} ILIKE '%OperatingIncome%'
                QUALIFY row_number() OVER (PARTITION BY member, period_end
                                           ORDER BY filing_date DESC NULLS LAST, value DESC) = 1
                ORDER BY period_end""", [self.t]).fetchall()
            if not rows:
                continue
            ends = sorted({r[1] for r in rows})
            if cadence == "quarterly" and n == 2:
                # "same quarter a year apart": the latest quarter and the one ~365 days before it
                # (10-Qs also carry the prior quarter, so the last two ends can be adjacent)
                prior = [pe for pe in ends if abs((ends[-1] - pe).days - 364) <= 21]
                ends = [prior[-1], ends[-1]] if prior else ends[-2:]
            else:
                ends = ends[-n:]
            if oi:
                rev = self.history((axis,), cadence, n)
                order = [nm for nm, _ in (rev or {}).get("series", [])]  # revenue order = same colours
                members = sorted((m for m in dict.fromkeys(r[0] for r in rows if r[1] == ends[-1])
                                  if _member(m, axis) in order), key=lambda m: order.index(_member(m, axis)))
            else:
                last = {m: v for m, pe, v, *_ in rows if pe == ends[-1]}
                total = self.points("Annual revenue" if cadence == "annual" else "Quarterly revenue")
                keep = partition([[m, v / 1e6] for m, v in last.items()], [total[-1][1]] if total else [])
                members = [m for m, _ in keep]
            if len(members) < 2 or len(ends) < 2:
                continue
            vals = {(m, pe): v for m, pe, v, *_ in rows}
            # a 52/53-week year that ends in the first days of January belongs to the year before
            label = ((lambda pe: f"FY{pe.year - (1 if pe.month == 1 and pe.day <= 10 else 0)}")
                     if cadence == "annual" else (lambda pe: f"{pe:%b %y}"))
            srcs = sorted({f"{self.F.form(a)} {a} {c}" for m, pe, _, a, c, _u in rows if m in members and pe in ends})
            units = [iso(r[5]) for r in rows if r[1] in ends]
            cur = max(set(units), key=units.count) if units else "USD"
            return {"axis": axis, "periods": [label(pe) for pe in ends], "unit": CURRENCY.get(cur, f"{cur} M"),
                    "series": [[_member(m, axis), [round((vals.get((m, pe)) or 0) / 1e6, 1) for pe in ends]]
                               for m in members],
                    "srcs": srcs}
        return None


@cache
def modules() -> dict:
    """TICKER -> module, for every module in this package."""
    out = {}
    for m in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{m.name}")
        if getattr(mod, "TICKER", None) and getattr(mod, "specs", None):
            out[mod.TICKER] = mod
    return out


def specs(ticker: str, con, F, financials: dict | None) -> list[dict]:
    mod = modules().get(ticker.upper())
    return [s for s in mod.specs(Data(ticker.upper(), con, F, financials)) if s] if mod else []
