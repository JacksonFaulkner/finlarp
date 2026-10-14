"""Form 4s straight from EDGAR, for the weeks the quarterly bulk file hasn't been published yet.

sec_insiders loads SEC's Insider Transactions Data Sets, which land after a quarter ends. This
pulls each universe company's recent Form 4 / 4/A filings (from the submissions index), parses the
non-derivative table of the XML, and writes transactions/live_form4.parquet in the same schema, so
insiders.tx_sql() and every view built on it pick the rows up. When the bulk quarter arrives its
rows win the 4/A dedup in tx_sql; delete live_form4.parquet then, or just rerun (it rebuilds).

Derivative tables (options, RSUs) are skipped: only P (open-market buy) and S carry signal.

    uv run python -m sources.sec_form4_live pull [--since 2026-10-01] [--max-age 3600]
    uv run python -m sources.sec_form4_live buys [--since 2026-10-01] [--min-value 25000]
"""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import duckdb

from sources import sec_http, universe
from sources.sec_insiders import TX_DIR, _PLAN_RE, _dir

CACHE = universe.data_dir("insiders") / "live_form4.ndjson"
OUT = TX_DIR / "live_form4.parquet"
FORMS = {"4", "4/A"}

_SCHEMA = """
    ticker VARCHAR, issuer_cik INTEGER, accn VARCHAR, form VARCHAR, filed DATE, period DATE,
    owner_cik BIGINT, owner_name VARCHAR, relationship VARCHAR, officer_title VARCHAR,
    n_owners BIGINT, owner_names VARCHAR, kind VARCHAR, security_title VARCHAR, trans_date DATE,
    code VARCHAR, shares DOUBLE, price DOUBLE, value DOUBLE, acquired_disposed VARCHAR,
    shares_owned_after DOUBLE, direct_indirect VARCHAR, nature VARCHAR, is_10b5_1 BOOLEAN,
    plan_src VARCHAR
"""


def _text(el: ET.Element | None, path: str) -> str | None:
    if el is None:
        return None
    t = el.findtext(path)
    return t.strip() if t and t.strip() else None


def _num(s: str | None) -> float | None:
    try:
        return float(s) if s is not None else None
    except ValueError:
        return None


def parse(xml: str, ticker: str, accn: str, form: str, filed: str) -> list[dict]:
    """Non-derivative transaction rows of one Form 4 document, owner-deduplicated like the bulk set."""
    root = ET.fromstring(xml)
    owners = []
    for o in root.findall("reportingOwner"):
        rel = o.find("reportingOwnerRelationship")
        flags = [name for tag, name in (("isDirector", "Director"), ("isOfficer", "Officer"),
                                        ("isTenPercentOwner", "TenPercentOwner"), ("isOther", "Other"))
                 if (_text(rel, tag) or "").lower() in ("1", "true")]
        owners.append({
            "cik": int(_text(o, "reportingOwnerId/rptOwnerCik") or 0) or None,
            "name": _text(o, "reportingOwnerId/rptOwnerName"),
            "relationship": ", ".join(flags) or None,
            "title": _text(rel, "officerTitle"),
        })
    if not owners:
        return []
    owners.sort(key=lambda o: o["cik"] or 0)
    lead = owners[0]
    notes = {n.get("id"): n.text or "" for n in root.findall("footnotes/footnote")}
    remarks_plan = bool(re.search(_PLAN_RE, _text(root, "remarks") or "", re.I))
    flag_plan = (_text(root, "aff10b5One") or "").lower() in ("1", "true")
    issuer_cik = int(_text(root, "issuer/issuerCik") or 0) or None
    period = _text(root, "periodOfReport")
    rows = []
    for t in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        ids = {f.get("id") for f in t.iter("footnoteId")}
        fn_plan = remarks_plan or any(re.search(_PLAN_RE, notes.get(i, ""), re.I) for i in ids)
        shares = _num(_text(t, "transactionAmounts/transactionShares/value"))
        price = _num(_text(t, "transactionAmounts/transactionPricePerShare/value"))
        rows.append({
            "ticker": ticker, "issuer_cik": issuer_cik, "accn": accn, "form": form, "filed": filed,
            "period": period, "owner_cik": lead["cik"], "owner_name": lead["name"],
            "relationship": lead["relationship"], "officer_title": lead["title"],
            "n_owners": len(owners), "owner_names": "; ".join(o["name"] or "" for o in owners),
            "kind": "nonderiv", "security_title": _text(t, "securityTitle/value"),
            "trans_date": _text(t, "transactionDate/value"), "code": _text(t, "transactionCoding/transactionCode"),
            "shares": shares, "price": price,
            "value": shares * price if shares is not None and price is not None else None,
            "acquired_disposed": _text(t, "transactionAmounts/transactionAcquiredDisposedCode/value"),
            "shares_owned_after": _num(_text(t, "postTransactionAmounts/sharesOwnedFollowingTransaction/value")),
            "direct_indirect": _text(t, "ownershipNature/directOrIndirectOwnership/value"),
            "nature": _text(t, "ownershipNature/natureOfOwnership/value"),
            "is_10b5_1": flag_plan or fn_plan,
            "plan_src": "both" if flag_plan and fn_plan else "flag" if flag_plan else "footnote" if fn_plan else None,
        })
    return rows


def _cached() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["accn"]] = rec["rows"]
    return out


def _candidates(since: str, max_age_s: float) -> list[dict]:
    """Form 4 / 4/A filings by universe issuers filed on or after `since`, from the submissions index."""
    seen: dict[str, dict] = {}
    stocks = universe.stocks()
    for k, s in enumerate(stocks, 1):
        for cik in s["ciks"][:1]:  # predecessors stopped filing as the current issuer long ago
            rec = universe.submissions(cik, max_age_s)["filings"]["recent"]
            for form, filed, accn, doc in zip(rec["form"], rec["filingDate"], rec["accessionNumber"],
                                              rec["primaryDocument"]):
                if form in FORMS and filed >= since and accn not in seen:
                    seen[accn] = {"ticker": s["ticker"], "cik": cik, "form": form, "filed": filed,
                                  "accn": accn, "doc": re.sub(r"^xsl[^/]*/", "", doc)}
        if k % 50 == 0:
            print(f"  index {k}/{len(stocks)}", flush=True)
    return sorted(seen.values(), key=lambda c: c["filed"])


def pull(since: str, max_age_s: float = 3600) -> dict:
    cache = _cached()
    todo = [c for c in _candidates(since, max_age_s) if c["accn"] not in cache]
    print(f"{len(todo)} new Form 4 filings to fetch", flush=True)
    failed = 0
    with open(CACHE, "a") as f:
        for k, c in enumerate(todo, 1):
            url = f"https://www.sec.gov/Archives/edgar/data/{c['cik']}/{c['accn'].replace('-', '')}/{c['doc']}"
            try:
                resp = sec_http.get(url)
                resp.raise_for_status()
                rows = parse(resp.text, c["ticker"], c["accn"], c["form"], c["filed"])
            except Exception as e:  # one bad filing shouldn't sink the run; it is retried next time
                print(f"  skip {c['ticker']} {c['accn']}: {type(e).__name__} {e}", flush=True)
                failed += 1
                continue
            f.write(json.dumps({"accn": c["accn"], "rows": rows}) + "\n")
            f.flush()
            if k % 100 == 0:
                print(f"  fetched {k}/{len(todo)}", flush=True)
    return {"fetched": len(todo) - failed, "failed": failed, "written": write_parquet()}


def write_parquet() -> int:
    rows = [r for rs in _cached().values() for r in rs]
    _dir(TX_DIR)
    if not rows:
        OUT.unlink(missing_ok=True)
        return 0
    tmp_json = CACHE.with_suffix(".rows.json")
    tmp_json.write_text(json.dumps(rows))
    part = OUT.with_suffix(".part")
    con = duckdb.connect()
    try:
        con.execute(f"""
            COPY (
                SELECT ticker, issuer_cik, accn, form, filed::DATE filed, period::DATE period, owner_cik,
                       owner_name, relationship, officer_title, n_owners, owner_names, kind, security_title,
                       trans_date::DATE trans_date, code, shares, price, value, acquired_disposed,
                       shares_owned_after, direct_indirect, nature, is_10b5_1, plan_src
                FROM read_json('{tmp_json}', columns={{{", ".join(_cols())}}})
                ORDER BY ticker, trans_date, accn
            ) TO '{part}' (FORMAT parquet, COMPRESSION zstd)
        """)
    finally:
        con.close()
        tmp_json.unlink(missing_ok=True)
    part.rename(OUT)
    return len(rows)


def _cols() -> list[str]:
    out = []
    for piece in _SCHEMA.replace("\n", " ").split(","):
        name, typ = piece.split()
        out.append(f"'{name}': '{'VARCHAR' if typ in ('DATE',) else typ}'")
    return out


def buys(since: str, min_value: float) -> list[dict]:
    from sources.sec_insiders import _rows, tx_sql
    return _rows(f"""
        SELECT ticker, owner_name, coalesce(officer_title, relationship) AS role, trans_date, filed,
               shares, price, round(value) AS value, is_10b5_1
        FROM {tx_sql()}
        WHERE kind = 'nonderiv' AND code = 'P' AND trans_date >= $since AND coalesce(value, 0) >= $v
          AND NOT regexp_matches(security_title, 'prefer|note|warrant|debenture', 'i')
        ORDER BY value DESC
    """, {"since": since, "v": min_value})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("cmd", choices=["pull", "buys"])
    ap.add_argument("--since", default=str(date.today() - timedelta(days=21)))
    ap.add_argument("--max-age", type=float, default=3600, help="submissions index cache, seconds")
    ap.add_argument("--min-value", type=float, default=25_000)
    a = ap.parse_args()
    if a.cmd == "pull":
        print(json.dumps(pull(a.since, a.max_age)))
    else:
        for r in buys(a.since, a.min_value):
            print(f"{r['trans_date']} {r['ticker']:<6} ${r['value'] / 1e6:>7.2f}M @ {r['price'] or 0:>8.2f} "
                  f"{'10b5-1 ' if r['is_10b5_1'] else ''}{r['owner_name']} ({r['role']})")
