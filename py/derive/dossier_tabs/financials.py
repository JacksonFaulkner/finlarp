"""Dossier tab: Financials. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Revenue (KV, quarterly and annual series, segment revenue bars) as before, then:
segment operating income and margin, margin and FCF series, and four tables of
XBRL line items: quarterly and annual P&L and cash flow (last 8 quarters / 5
fiscal years), quarter-end balance sheet with per-share and capital return, and
the annual balance sheet with ROE and ROIC.

Every table cell is a fact link (inline XBRL viewer) or part of a derived value.
A table row carries one src: the fact itself when only one cell is populated,
otherwise derived() whose inputs are the populated cells' sources.
"""
from __future__ import annotations

from derive.dossier import Filings, _is_new, _member, _money, _pct, derived, src
from sources import sec_financials, sec_segments

# name -> XBRL concept priority, first concept with a value wins per period.
CONCEPTS: dict[str, list[str]] = {
    "revenue": sec_financials.METRICS["revenue"],
    "gross_profit": sec_financials.METRICS["gross_profit"],
    "operating_income": sec_financials.METRICS["operating_income"],
    "net_income": sec_financials.METRICS["net_income"],
    "eps": sec_financials.METRICS["eps_diluted"],
    "rnd": sec_financials.METRICS["rnd"],
    "sga": ["us-gaap:SellingGeneralAndAdministrativeExpense"],
    "da": ["us-gaap:DepreciationDepletionAndAmortization", "us-gaap:DepreciationAmortizationAndAccretionNet",
           "us-gaap:DepreciationAndAmortization", "us-gaap:Depreciation"],
    "interest": ["us-gaap:InterestExpense", "us-gaap:InterestExpenseNonoperating", "us-gaap:InterestExpenseDebt"],
    "pretax": ["us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
               "ifrs-full:ProfitLossBeforeTax"],
    "tax": ["us-gaap:IncomeTaxExpenseBenefit", "ifrs-full:IncomeTaxExpenseContinuingOperations"],
    "ocf": sec_financials.METRICS["operating_cash_flow"],
    "capex": sec_financials.METRICS["capex"],
    "cash": sec_financials.METRICS["cash"],
    "ltd": sec_financials.METRICS["long_term_debt"],
    "current_ltd": ["us-gaap:LongTermDebtCurrent", "ifrs-full:CurrentPortionOfNoncurrentBorrowings"],
    "short_borrow": ["us-gaap:ShortTermBorrowings", "ifrs-full:CurrentBorrowings"],
    "assets": sec_financials.METRICS["total_assets"],
    "assets_current": ["us-gaap:AssetsCurrent", "ifrs-full:CurrentAssets"],
    "equity": sec_financials.METRICS["equity"],
    "liabilities": ["us-gaap:Liabilities", "ifrs-full:Liabilities"],
    "liab_current": ["us-gaap:LiabilitiesCurrent", "ifrs-full:CurrentLiabilities"],
    "inventory": ["us-gaap:InventoryNet", "ifrs-full:Inventories"],
    "receivables": ["us-gaap:AccountsReceivableNetCurrent", "us-gaap:AccountsReceivableNet",
                    "ifrs-full:TradeAndOtherCurrentReceivables"],
    "payables": ["us-gaap:AccountsPayableCurrent", "ifrs-full:TradeAndOtherCurrentPayables"],
    "lease_total": ["us-gaap:OperatingLeaseLiability"],
    "lease_current": ["us-gaap:OperatingLeaseLiabilityCurrent"],
    "lease_noncurrent": ["us-gaap:OperatingLeaseLiabilityNoncurrent"],
    "deferred_rev": ["us-gaap:DeferredRevenue", "us-gaap:DeferredRevenueCurrent", "ifrs-full:ContractLiabilities"],
    "rpo": ["us-gaap:RevenueRemainingPerformanceObligation"],
    "shares_out": sec_financials.METRICS["shares_outstanding"],
    "dil_shares": sec_financials.METRICS["diluted_shares"],
    "buyback": ["us-gaap:PaymentsForRepurchaseOfCommonStock", "us-gaap:StockRepurchasedDuringPeriodValue"],
    "buyback_sh": ["us-gaap:StockRepurchasedDuringPeriodShares"],
    "sbc": ["us-gaap:ShareBasedCompensation", "us-gaap:AllocatedShareBasedCompensationExpense"],
    "stock_issued": ["us-gaap:StockIssuedDuringPeriodValueNewIssues", "us-gaap:ProceedsFromIssuanceOfCommonStock"],
    "dividends": ["us-gaap:PaymentsOfDividends", "us-gaap:PaymentsOfDividendsCommonStock",
                  "us-gaap:DividendsCommonStockCash"],
    "dps": ["us-gaap:CommonStockDividendsPerShareCashPaid", "us-gaap:CommonStockDividendsPerShareDeclared"],
}
KIND = {"eps": "eps", "dps": "eps", "shares_out": "sh", "dil_shares": "sh", "buyback_sh": "sh"}
# Per-share and weighted-average values: a quarter cannot be taken as YTD minus YTD.
NON_ADDITIVE = {"eps", "dps", "dil_shares"}


# ---- formatting and combinators --------------------------------------------

def _fmt(v: float | None, kind: str = "m") -> str:
    if v is None:
        return "—"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "x":
        return f"{v:.2f}x"
    if kind == "eps":
        return f"{v:,.2f}"
    return f"{v / 1e6:,.1f}"  # $M or millions of shares


def _later(*xs):
    vals = [x for x in xs if x]
    return max(vals) if vals else None


def _sub(x, y):
    return x - y


def _div(x, y):
    return x / y if y else None


def _sum(parts: list[dict | None], label: str) -> dict | None:
    parts = [p for p in parts if p]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return {"v": sum(p["v"] for p in parts),
            "src": derived(label, " + ".join(_fmt(p["v"]) for p in parts), [p["src"] for p in parts]),
            "filed": _later(*(p["filed"] for p in parts))}


def _bin(a: dict | None, b: dict | None, fn, sym: str, label: str, ka: str = "m", kb: str = "m") -> dict | None:
    if not a or not b:
        return None
    v = fn(a["v"], b["v"])
    if v is None:
        return None
    return {"v": v, "src": derived(label, f"{_fmt(a['v'], ka)} {sym} {_fmt(b['v'], kb)}", [a["src"], b["src"]]),
            "filed": _later(a["filed"], b["filed"])}


# ---- data access -----------------------------------------------------------

class _Store:
    """Lazy per-ticker series: rows(name, cad) -> {end | fy: row}, pt(name, cad, key) -> point."""

    def __init__(self, t: str, F: Filings):
        self.t, self.F = t, F
        self._rows: dict[tuple[str, str], dict] = {}
        self._qmap: dict[str, dict] = {}  # quarter end -> revenue quarter, for fiscal labels on instants

    def seed(self, name: str, quarterly: list[dict], annual: list[dict]) -> None:
        self._rows[(name, "q")] = {r["end"]: r for r in quarterly}
        self._rows[(name, "a")] = {r["fy"]: r for r in annual}
        if name == "revenue":
            self._qmap = {r["end"]: r for r in quarterly}

    def rows(self, name: str, cad: str) -> dict:
        key = (name, cad)
        if key not in self._rows:
            if cad == "q":
                ser = sec_financials.quarterly_series(self.t, CONCEPTS[name])
                for r in ser:  # instant concepts come back without fiscal labels
                    q = self._qmap.get(r["end"])
                    if q and not r.get("fq"):
                        r["fy"], r["fq"] = q["fy"], q["fq"]
                self._rows[key] = {r["end"]: r for r in ser}
            else:
                self._rows[key] = {r["fy"]: r for r in sec_financials.annual_series(self.t, CONCEPTS[name])}
        return self._rows[key]

    def pt(self, name: str, cad: str, k) -> dict | None:
        r = self.rows(name, cad).get(k)
        if not r or r.get("val") is None:
            return None
        if cad == "q" and r.get("derived") and name in NON_ADDITIVE:
            return None
        return {"v": r["val"], "src": self._src(name, r, cad), "filed": r.get("filed"), "concept": r.get("concept")}

    def latest(self, name: str, cad: str = "q") -> dict | None:
        for k in sorted(self.rows(name, cad), reverse=True):
            p = self.pt(name, cad, k)
            if p:
                return p
        return None

    def _src(self, name: str, r: dict, cad: str) -> dict:
        if cad == "a":
            per = f"FY{r['fy']}"
        elif r.get("fq"):
            per = f"Q{r['fq']} FY{r['fy']}"
        else:
            per = f"quarter ending {r['end']}"
        if cad == "q" and r.get("derived") and r.get("derived_from"):
            parts = r["derived_from"]
            inputs = [self._fact(p, f"{p['start']}..{p['end']}") for p in parts]
            formula = " − ".join(f"[{p['start']}..{p['end']}] {_fmt(p['val'], KIND.get(name, 'm'))}" for p in parts)
            return derived(f"{per} derived: no discrete quarterly fact filed", formula, inputs)
        return self._fact(r, per)

    def _fact(self, r: dict, per: str) -> dict:
        return src(f"{self.F.form(r['accn'])} filed {r['filed']} · {r['concept']} · {per}",
                   self.F.doc_url(r["accn"], inline_xbrl=True))


class _View:
    """One cadence ("q" or "a") of the store, with the derived line items."""

    def __init__(self, st: _Store, cad: str):
        self.st, self.cad = st, cad

    def pt(self, name: str, k) -> dict | None:
        return self.st.pt(name, self.cad, k)

    def ratio(self, num: str, den: str, k, label: str) -> dict | None:
        return _bin(self.pt(num, k), self.pt(den, k), _div, "/", label, KIND.get(num, "m"), KIND.get(den, "m"))

    def fcf(self, k) -> dict | None:
        return _bin(self.pt("ocf", k), self.pt("capex", k), _sub, "−", "Free cash flow = operating cash flow − capex")

    def total_debt(self, k) -> dict | None:
        ltd, cur, stb = self.pt("ltd", k), self.pt("current_ltd", k), self.pt("short_borrow", k)
        parts = [ltd]
        # a LongTermDebt (total, incl. current portion) already contains the current portion
        if cur and not (ltd and ltd.get("concept") == "LongTermDebt"):
            parts.append(cur)
        parts.append(stb)
        return _sum(parts, "Total debt = long-term debt + current portion (unless total) + short-term borrowings")

    def net_debt(self, k) -> dict | None:
        return _bin(self.total_debt(k), self.pt("cash", k), _sub, "−", "Net debt = total debt − cash")

    def lease(self, k) -> dict | None:
        total = self.pt("lease_total", k)
        if total:
            return total
        cur, nc = self.pt("lease_current", k), self.pt("lease_noncurrent", k)
        return _sum([cur, nc], "Operating lease liability = current + noncurrent") if cur and nc else None

    def roe(self, fy: int) -> dict | None:
        ni, eq, eqp = self.pt("net_income", fy), self.pt("equity", fy), self.pt("equity", fy - 1)
        if not ni or not eq:
            return None
        if eqp:
            den = (eq["v"] + eqp["v"]) / 2
            formula = f"{_fmt(ni['v'])} / avg({_fmt(eqp['v'])}, {_fmt(eq['v'])}) ($M)"
            inputs = [ni["src"], eqp["src"], eq["src"]]
        else:
            den = eq["v"]
            formula = f"{_fmt(ni['v'])} / {_fmt(eq['v'])} ($M, ending equity)"
            inputs = [ni["src"], eq["src"]]
        if den <= 0:
            return None
        return {"v": ni["v"] / den, "src": derived("ROE = net income / average equity", formula, inputs),
                "filed": _later(ni["filed"], eq["filed"])}

    def roic(self, fy: int) -> dict | None:
        oi, pre, tax = self.pt("operating_income", fy), self.pt("pretax", fy), self.pt("tax", fy)
        eq, cash, debt = self.pt("equity", fy), self.pt("cash", fy), self.total_debt(fy)
        if not (oi and pre and tax and eq and cash) or not pre["v"]:
            return None
        rate = tax["v"] / pre["v"]
        if not 0 <= rate < 1:
            return None
        nopat = oi["v"] * (1 - rate)
        debt_v = debt["v"] if debt else 0.0
        ic = eq["v"] + debt_v - cash["v"]
        if ic <= 0:
            return None
        formula = (f"NOPAT / invested capital; NOPAT = operating income × (1 − tax / pretax) = "
                   f"{_fmt(oi['v'])} × (1 − {_fmt(tax['v'])} / {_fmt(pre['v'])}); "
                   f"invested capital = equity + total debt − cash = {_fmt(eq['v'])} + {_fmt(debt_v)} − {_fmt(cash['v'])} ($M)")
        inputs = [oi["src"], tax["src"], pre["src"], eq["src"], cash["src"]] + ([debt["src"]] if debt else [])
        return {"v": nopat / ic, "src": derived("ROIC = NOPAT / invested capital", formula, inputs),
                "filed": _later(oi["filed"], eq["filed"], cash["filed"])}


# ---- row specs -------------------------------------------------------------

def _pl_spec(v: _View) -> list[tuple]:
    p = v.pt
    return [
        ("Revenue ($M)", "m", lambda k: p("revenue", k)),
        ("Gross profit ($M)", "m", lambda k: p("gross_profit", k)),
        ("Gross margin (%)", "pct", lambda k: v.ratio("gross_profit", "revenue", k, "Gross margin = gross profit / revenue")),
        ("Operating income ($M)", "m", lambda k: p("operating_income", k)),
        ("Operating margin (%)", "pct", lambda k: v.ratio("operating_income", "revenue", k, "Operating margin = operating income / revenue")),
        ("Net income ($M)", "m", lambda k: p("net_income", k)),
        ("Net margin (%)", "pct", lambda k: v.ratio("net_income", "revenue", k, "Net margin = net income / revenue")),
        ("EPS diluted ($)", "eps", lambda k: p("eps", k)),
        ("R&D ($M)", "m", lambda k: p("rnd", k)),
        ("SG&A ($M)", "m", lambda k: p("sga", k)),
        ("D&A ($M)", "m", lambda k: p("da", k)),
        ("Interest expense ($M)", "m", lambda k: p("interest", k)),
        ("Pretax income ($M)", "m", lambda k: p("pretax", k)),
        ("Income tax ($M)", "m", lambda k: p("tax", k)),
        ("Operating cash flow ($M)", "m", lambda k: p("ocf", k)),
        ("Capex ($M)", "m", lambda k: p("capex", k)),
        ("Free cash flow ($M)", "m", lambda k: v.fcf(k)),
    ]


def _bs_spec(v: _View) -> list[tuple]:
    p = v.pt
    return [
        ("Cash ($M)", "m", lambda k: p("cash", k)),
        ("Long-term debt ($M)", "m", lambda k: p("ltd", k)),
        ("Current debt ($M)", "m", lambda k: _sum([p("current_ltd", k), p("short_borrow", k)],
                                                 "Current debt = current LTD + short-term borrowings")),
        ("Net debt ($M, negative = net cash)", "m", lambda k: v.net_debt(k)),
        ("Total assets ($M)", "m", lambda k: p("assets", k)),
        ("Equity ($M)", "m", lambda k: p("equity", k)),
        ("Total liabilities ($M)", "m", lambda k: p("liabilities", k)),
        ("Working capital ($M)", "m", lambda k: _bin(p("assets_current", k), p("liab_current", k), _sub, "−",
                                                     "Working capital = current assets − current liabilities")),
        ("Current ratio (x)", "x", lambda k: _bin(p("assets_current", k), p("liab_current", k), _div, "/",
                                                 "Current ratio = current assets / current liabilities")),
        ("Inventory ($M)", "m", lambda k: p("inventory", k)),
        ("Receivables ($M)", "m", lambda k: p("receivables", k)),
        ("Payables ($M)", "m", lambda k: p("payables", k)),
        ("Operating lease liability ($M)", "m", lambda k: v.lease(k)),
        ("Deferred revenue ($M)", "m", lambda k: p("deferred_rev", k)),
        ("Remaining performance obligations ($M)", "m", lambda k: p("rpo", k)),
        ("Shares outstanding (M, undimensioned XBRL)", "sh", lambda k: p("shares_out", k)),
        ("Diluted shares, weighted (M)", "sh", lambda k: p("dil_shares", k)),
        ("Buybacks, cash ($M)", "m", lambda k: p("buyback", k)),
        ("Buyback shares (M)", "sh", lambda k: p("buyback_sh", k)),
        ("Stock-based comp ($M)", "m", lambda k: p("sbc", k)),
        ("Stock issued ($M)", "m", lambda k: p("stock_issued", k)),
        ("Dividends paid ($M)", "m", lambda k: p("dividends", k)),
        ("DPS cash paid ($)", "eps", lambda k: p("dps", k)),
    ]


def _table(title: str, cols: list[tuple], spec: list[tuple]) -> dict | None:
    rows = []
    for label, kind, fn in spec:
        pts = [fn(k) for k, _ in cols]
        present = [p for p in pts if p]
        if not present:
            continue
        srcs = [p["src"] for p in present]
        row_src = srcs[0] if len(srcs) == 1 else derived(
            f"{label}: {len(srcs)} periods", "each cell is that period's value; see inputs", srcs)
        latest = max(present, key=lambda p: p.get("filed") or "")
        rows.append({"cells": [label] + [_fmt(p["v"], kind) if p else "—" for p in pts],
                     "new": _is_new(latest.get("filed")), "src": row_src})
    if not rows:
        return None
    return {"type": "table", "title": title, "cols": ["metric"] + [h for _, h in cols], "rows": rows}


def _series(title: str, unit: str, cols: list[tuple], fn, scale: float) -> dict | None:
    pts = []
    for k, h in cols:
        p = fn(k)
        if p:
            pts.append({"x": h, "y": round(p["v"] * scale, 1), "src": p["src"]})
    return {"type": "series", "title": title, "unit": unit, "points": pts} if pts else None


# ---- section ---------------------------------------------------------------

def _segments(t: str, F: Filings, con) -> dict | None:
    """Segment operating income for the latest annual period, with segment revenue where tagged."""
    oi_c = sorted(sec_segments.OPINC)
    rev_c = sorted(sec_segments.REVENUE)
    axes = sorted(sec_segments.SEGMENT_AXES)
    q = lambda xs: ", ".join(f"'{x}'" for x in xs)  # constants from code, not user input
    rows = con.execute(f"""
        WITH s AS (SELECT *, CASE WHEN concept IN ({q(oi_c)}) THEN 'oi' ELSE 'rev' END AS kind
                   FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
                   WHERE ticker = ? AND axis IN ({q(axes)}) AND concept IN ({q(oi_c + rev_c)})
                     AND period_start IS NOT NULL AND date_diff('day', period_start, period_end) > 300),
             last AS (SELECT max(period_end) AS pe FROM s WHERE kind = 'oi')
        SELECT axis, member, kind, concept, period_end, value, accn, form, filing_date FROM s
        WHERE period_end = (SELECT pe FROM last)
        QUALIFY row_number() OVER (PARTITION BY kind, axis, member
                                   ORDER BY filing_date DESC NULLS LAST, value DESC) = 1""", [t]).fetchall()
    if not rows:
        return None
    oi, rev, pe = {}, {}, None
    for axis, member, kind, concept, period_end, val, accn, form, filed in rows:
        item = {"v": val, "concept": concept, "axis": axis, "member": member, "accn": accn, "form": form,
                "filed": str(filed) if filed else None,
                "src": src(f"{form} · {concept} · {axis}={member}", F.doc_url(accn, inline_xbrl=True))}
        (oi if kind == "oi" else rev)[(axis, member)] = item
        if kind == "oi":
            pe = period_end
    out = []
    for key in sorted(oi, key=lambda k: -oi[k]["v"]):
        o, r = oi[key], rev.get(key)
        margin = _bin(o, r, _div, "/", f"{_member(key[1], key[0])} operating margin = OI / revenue")
        out.append({"cells": [_member(key[1], key[0]), _fmt(o["v"]), _fmt(r["v"]) if r else "—",
                              _fmt(margin["v"], "pct") if margin else "—"],
                    "new": _is_new(o["filed"]), "src": margin["src"] if margin else o["src"]})
    return {"type": "table", "title": f"Segment operating income and margin (FY ending {pe})",
            "cols": ["segment", "operating income ($M)", "revenue ($M)", "margin"], "rows": out}


def section(t: str, con, F, prof: dict | None) -> dict | None:
    rq = sec_financials.quarterly_series(t, CONCEPTS["revenue"])
    ra = sec_financials.annual_series(t, CONCEPTS["revenue"])
    if not rq and not ra:
        return None
    st = _Store(t, F)
    st.seed("revenue", rq, ra)
    qcols = [(r["end"], f"Q{r['fq']}'{str(r['fy'])[2:]}" if r.get("fq") else str(r["end"])[:7]) for r in rq[-8:]]
    acols = [(r["fy"], f"FY{r['fy']}") for r in ra[-5:]]
    qv, av = _View(st, "q"), _View(st, "a")
    blocks: list[dict] = []

    # revenue KV and series (as in sec_revenue_)
    kv = []
    if rq:
        q = rq[-1]
        q_label = f"Q{q['fq']} FY{q['fy']}" if q.get("fq") else f"quarter ending {q['end']}"
        kv.append({"label": f"Latest {q_label}", "value": _money(q["val"]), "src": st._src("revenue", q, "q")})
        prev = next((x for x in rq if q.get("fy") and x.get("fy") == q["fy"] - 1 and x.get("fq") == q.get("fq")), None)
        if prev and prev["val"]:
            kv.append({"label": "  YoY", "value": _pct((q["val"] / prev["val"] - 1) * 100), "src": derived(
                "YoY growth", f"{q['val'] / 1e6:,.1f} / {prev['val'] / 1e6:,.1f} − 1",
                [st._src("revenue", q, "q"), st._src("revenue", prev, "q")])})
    if len(ra) >= 2 and ra[-2]["val"]:
        a, b = ra[-1], ra[-2]
        kv.append({"label": f"FY{a['fy']}", "value": _money(a["val"]), "src": st._fact(a, f"FY{a['fy']}")})
        kv.append({"label": "  YoY", "value": _pct((a["val"] / b["val"] - 1) * 100), "src": derived(
            "YoY growth", f"{a['val'] / 1e6:,.1f} / {b['val'] / 1e6:,.1f} − 1",
            [st._fact(a, f"FY{a['fy']}"), st._fact(b, f"FY{b['fy']}")])})
    if kv:
        blocks.append({"type": "kv", "rows": kv})
    q_pts = [{"x": h, "y": round(r["val"] / 1e6, 1), "src": st._src("revenue", r, "q")}
             for (_, h), r in zip(qcols, rq[-8:])]
    a_pts = [{"x": f"FY{a['fy']}", "y": round(a["val"] / 1e6, 1), "src": st._fact(a, f"FY{a['fy']}")} for a in ra[-5:]]
    for title, pts in (("Quarterly revenue", q_pts), ("Annual revenue", a_pts)):
        if pts:
            blocks.append({"type": "series", "title": title, "unit": "$M", "points": pts})

    for tag, cols, view in (("quarterly", qcols, qv), ("annual", acols, av)):
        blocks += [b for b in (
            _series(f"Gross margin, {tag}", "%", cols,
                    lambda k, v=view: v.ratio("gross_profit", "revenue", k, "Gross margin = gross profit / revenue"), 100),
            _series(f"Operating margin, {tag}", "%", cols,
                    lambda k, v=view: v.ratio("operating_income", "revenue", k, "Operating margin = operating income / revenue"), 100),
            _series(f"Net margin, {tag}", "%", cols,
                    lambda k, v=view: v.ratio("net_income", "revenue", k, "Net margin = net income / revenue"), 100),
            _series(f"Free cash flow, {tag}", "$M", cols, lambda k, v=view: v.fcf(k), 1e-6),
        ) if b]

    # segment revenue bars (as in sec_revenue_)
    seg = con.execute(f"""
        WITH s AS (SELECT * FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
                   WHERE ticker = ? AND axis <> '' AND period_start IS NOT NULL
                     AND date_diff('day', period_start, period_end) > 300
                     AND concept NOT ILIKE '%OperatingIncome%'),
             latest AS (SELECT axis, max(period_end) pe FROM s GROUP BY 1)
        SELECT s.axis, s.member, s.period_end, s.value, s.accn, s.concept FROM s JOIN latest l
          ON s.axis = l.axis AND s.period_end = l.pe
        QUALIFY row_number() OVER (PARTITION BY s.axis, s.member ORDER BY s.value DESC) = 1
        ORDER BY s.axis, s.value DESC""", [t]).fetchall()
    by_axis: dict[str, list] = {}
    for axis, member, pe, val, accn, concept in seg:
        by_axis.setdefault(axis, []).append((member, pe, val, accn, concept))
    for axis, items in by_axis.items():
        if len(items) < 2 or axis == "StatementBusinessSegmentsAxis":
            continue
        blocks.append({"type": "bars", "title": f"{_member(axis)} (FY ending {items[0][1]})", "unit": "$M", "items": [
            {"label": _member(m, axis), "value": round(v / 1e6, 1),
             "src": src(f"{F.form(a)} · {c} · {axis}={m}", F.doc_url(a, inline_xbrl=True))}
            for m, _, v, a, c in items[:8]]})

    seg_oi = _segments(t, F, con)
    if seg_oi:
        blocks.append(seg_oi)

    sh = st.latest("shares_out")
    if sh:
        blocks.append({"type": "kv", "rows": [{"label": "Shares outstanding (M, undimensioned XBRL)",
                                               "value": _fmt(sh["v"], "sh") + "M", "new": _is_new(sh["filed"]),
                                               "src": sh["src"]}]})

    for title, cols, spec in (
        ("Quarterly P&L and cash flow", qcols, _pl_spec(qv)),
        ("Annual P&L and cash flow", acols, _pl_spec(av)),
        ("Quarter-end balance sheet, per-share and capital return", qcols, _bs_spec(qv)),
        ("Annual balance sheet, per-share, capital return and returns", acols,
         _bs_spec(av) + [("ROE (%)", "pct", lambda k: av.roe(k)), ("ROIC (%)", "pct", lambda k: av.roic(k))]),
    ):
        if cols:
            tbl = _table(title, cols, spec)
            if tbl:
                blocks.append(tbl)

    if not blocks:
        return None
    return {"id": "financials", "title": "Financials", "blocks": blocks}
