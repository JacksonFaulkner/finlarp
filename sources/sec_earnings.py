"""Earnings press releases — the EX-99.1 furnished with 8-K item 2.02
("Results of Operations"). XBRL has the reported numbers; the release is
where forward guidance lives.

Per universe company: the last 4 item-2.02 8-Ks filed in the past ~18
months (all CIKs, current + predecessors). Foreign filers furnish results
on 6-K with no item codes, so when a company has no 2.02s we scan its
recent 6-Ks and keep those whose exhibit description or opening text looks
like a results release (form='6-K', method prefixed 'guess_').

The filing's -index.htm gives each document's Type (EX-99.1) in the same
single request index.json would cost. The exhibit is converted to text
(block tags -> lines, table rows -> ' | ' joined cells) and the HTML is
dropped. One zstd Parquet per ticker under earnings/releases/; state.json
remembers every accession fetched or rejected so reruns only pull new ones.

Extraction is rules only (see `extract`): guidance sentences/rows and
headline revenue / GAAP / non-GAAP EPS. `stats` reports hit rates.

    SEC_RPS=1.4 uv run python sources/sec_earnings.py ingest [TICKER...]
    uv run python sources/sec_earnings.py show MRVL
    uv run python sources/sec_earnings.py stats
    uv run python sources/sec_earnings.py reextract   # after tuning rules
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

import duckdb

from sources import sec_http, universe

N_RELEASES = 4
LOOKBACK_DAYS = 550
MAX_6K_SCAN = 25           # 6-Ks examined per company (after the size filter)
MIN_6K_BYTES = 60_000      # whole-submission size; notices/AGM/buyback 6-Ks are smaller
MAX_DOC_BYTES = 2_500_000  # full statutory reports, not press releases
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

DIR = universe.data_dir("earnings")
REL_DIR = DIR / "releases"
REL_DIR.mkdir(exist_ok=True)
STATE_PATH = DIR / "state.json"

COLS = {
    "ticker": "VARCHAR", "cik": "BIGINT", "accn": "VARCHAR", "form": "VARCHAR", "filed": "DATE",
    "doc_name": "VARCHAR", "method": "VARCHAR", "text": "VARCHAR", "words": "INTEGER",
    "guidance": "VARCHAR[]", "headline": "VARCHAR",
}

# ---------------------------------------------------------------- HTML -> text

_BLOCK = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "table",
          "center", "blockquote", "hr", "section", "article", "title", "pre", "font_block"}
_SKIP = {"script", "style", "head", "ix:header", "xml"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []      # finished lines
        self.buf: list[str] = []      # current line
        self.skip = 0
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.depth = 0                # table nesting

    def _flush(self):
        line = " ".join("".join(self.buf).split())
        self.buf = []
        self.out.append(line)

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self.skip += 1
        elif tag == "table":
            self._flush()
            self.depth += 1
        elif tag == "tr" and self.depth:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag in _BLOCK and self.cell is None:
            self._flush()
        elif tag in ("br", "p", "div") and self.cell is not None:
            self.cell.append(" ")

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self._flush()

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            cells = _merge_cells(self.row)
            if cells:
                self.out.append(" | ".join(cells))
            self.row = None
            self.cell = None
        elif tag == "table":
            self.depth = max(0, self.depth - 1)
            self.out.append("")
        elif tag in _BLOCK and self.cell is None:
            self._flush()

    def handle_data(self, data):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        else:
            self.buf.append(data)


def _merge_cells(cells: list[str]) -> list[str]:
    """Drop empty cells; glue '$' onto the next cell and ')' / '%' onto the
    previous one, the way EDGAR tables split '$ (1.2 )%'."""
    out: list[str] = []
    pending = ""
    for c in cells:
        c = c.replace("​", "").strip()
        if not c:
            continue
        if c in ("$", "(", "$(", "($"):
            pending += c
            continue
        if out and re.fullmatch(r"\)?%?\)?|pts?\.?|bps", c) and c:
            out[-1] += c
            continue
        out.append(pending + c)
        pending = ""
    return out


def html_to_text(raw: str) -> str:
    p = _Text()
    p.feed(raw)
    p.close()
    p._flush()
    lines, blank = [], False
    for ln in p.out:
        ln = ln.replace("\xa0", " ").strip()
        if not ln:
            blank = bool(lines)
            continue
        if blank:
            lines.append("")
            blank = False
        lines.append(ln)
    return "\n".join(lines)


# ------------------------------------------------------------ filing indexes

_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)


def filing_docs(cik: int, accn: str) -> list[dict]:
    """[{seq, desc, name, url, type, size}] from the first ('Document Format
    Files') table of the filing's -index.htm."""
    url = f"{ARCHIVES}/{cik}/{accn.replace('-', '')}/{accn}-index.htm"
    resp = sec_http.get(url)
    if resp.status_code != 200:
        return []
    body = resp.text
    start = body.find('class="tableFile"')
    end = body.find("</table>", start)
    docs = []
    for row in _ROW.findall(body[start:end] if start >= 0 else ""):
        tds = _TD.findall(row)
        if len(tds) < 5:
            continue
        href = re.search(r'href="([^"]+)"', tds[2])
        if not href:
            continue
        path = href.group(1).replace("/ix?doc=", "")
        clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
        size = clean(tds[4])
        docs.append({"desc": clean(tds[1]), "name": path.rsplit("/", 1)[-1],
                     "url": "https://www.sec.gov" + path, "type": clean(tds[3]).upper(),
                     "size": int(size) if size.isdigit() else 0})
    return docs


def _is_htm(d: dict) -> bool:
    return d["name"].lower().endswith((".htm", ".html", ".txt"))


def pick_exhibit(docs: list[dict]) -> tuple[dict | None, str]:
    """EX-99.1 first, then the largest EX-99*, then anything named like ex99."""
    htm = [d for d in docs if _is_htm(d)]
    for d in htm:
        if re.fullmatch(r"EX-99\.0?1", d["type"]):
            return d, "ex99.1"
    ex99 = [d for d in htm if d["type"].startswith("EX-99")]
    if ex99:
        return max(ex99, key=lambda d: d["size"]), "largest_ex99"
    named = [d for d in htm if re.search(r"ex-?99|exhibit-?99", d["name"], re.I)]
    if named:
        return max(named, key=lambda d: d["size"]), "named_ex99"
    return None, "no_exhibit"


_RESULTS_DESC = re.compile(r"result|earning|quarter|interim|financial (statements|highlights|report)|"
                           r"\b[1-4]Q\b|\bQ[1-4]\b|half[- ]year|annual report", re.I)
_RESULTS_HEAD = re.compile(r"\b(results|earnings|net income|net profit|EPS)\b", re.I)
_PERIOD_HEAD = re.compile(r"\b(quarter|half[- ]year|first half|second half|fiscal|months ended|year ended|Q[1-4])\b", re.I)


# ---------------------------------------------------------------- extraction

_BOILER = re.compile(r"forward[- ]looking|Private Securities Litigation|risks and uncertainties|safe harbor|"
                     r"undue reliance|actual results (may|could)|no obligation to update|fair value|"
                     r"weighted[- ]average|included separately|expected to be made|reflect only", re.I)
_FWD = re.compile(r"\b(outlook|guidance|guides?|expects?|expected|expecting|anticipates?|anticipated|forecasts?|"
                  r"projects (that|to)|projected to|estimates (that|to)|plus or minus|is targeting|we target|"
                  r"reaffirm\w*|(rais|narrow|updat)(es|ed|ing) (its |our |the )?(\w+ )?(full[- ]year|annual|fiscal|"
                  r"20\d\d|outlook|guidance))\b|\+/-|±", re.I)
_QTR_FISCAL = re.compile(r"for the (first|second|third|fourth) (fiscal )?quarter of (fiscal|20\d\d)", re.I)
_AMOUNT = re.compile(r"\$\s?\(?\d|\d(\.\d+)?\s?%|\d(\.\d+)?\s*(to|-|–|—|and)\s*\$?\d")
_HEADING = re.compile(r"^[\W\d]*((business|financial|fiscal|quarterly|annual|full[- ]year|current|updated|"
                      r"\w+ quarter)\s+)*(outlook|guidance)\b", re.I)
_SECTION_END = re.compile(r"^(about |conference call|webcast|forward[- ]looking|non-gaap|use of non|"
                          r"investor|contact|safe harbor|cautionary|note regarding|\w*\s?highlights|"
                          r"supplemental|reconciliation)", re.I)
_PAST = re.compile(r"\b(was|were|has been|had been|grew|increased|decreased|declined|reported|totaled|applied)\b", re.I)
# "revenue was $2.7B, above the midpoint of guidance" — a result, not guidance
_RETRO = re.compile(r"\b(was|were)\b.{0,250}?\b(guidance|outlook|expectations?|expected)\b|"
                    r"\b(above|below|exceed\w*|midpoint|mid-point|high end|low end|top end) of (our |the |its )?"
                    r"(\S+ )?(guidance|outlook|expectations|range)", re.I)
_SENT = re.compile(r"(?<=[.;!?])\s+(?=[A-Z(\"“])")


def _units(text: str) -> list[tuple[str, str]]:
    """(kind, unit) — table rows whole, prose split into sentences."""
    out = []
    for ln in text.split("\n"):
        if not ln:
            out.append(("blank", ""))
        elif " | " in ln:
            out.append(("row", ln))
        else:
            out.extend(("prose", s) for s in _SENT.split(ln))
    return out


def extract_guidance(text: str) -> list[str]:
    """Verbatim guidance units. Two passes: (a) any sentence/row with a
    forward word ('expects', 'outlook', ...) or 'for the Nth quarter of
    fiscal' plus a $ / % / range, minus safe-harbor boilerplate; (b) every
    numeric line under an 'Outlook'/'Guidance' heading until the next
    section. Retrospective mentions ('above the midpoint of guidance')
    slip through — that's for an LLM pass."""
    units = _units(text)
    keep: dict[int, str] = {}
    for i, (kind, u) in enumerate(units):
        if kind == "blank" or len(u) > 1500 or _BOILER.search(u):
            continue
        if not _AMOUNT.search(u) or (kind == "prose" and _RETRO.search(u)):
            continue
        if _FWD.search(u) or (_QTR_FISCAL.search(u) and not _PAST.search(u)):
            keep[i] = u
    # heading-scoped capture
    i = 0
    while i < len(units):
        kind, u = units[i]
        if kind == "prose" and len(u) < 90 and _HEADING.match(u) and not _BOILER.search(u):
            taken, j = 0, i + 1
            while j < len(units) and taken < 30:
                k2, u2 = units[j]
                if k2 != "blank" and (_SECTION_END.match(u2) or _BOILER.search(u2)):
                    break
                # a short digit-free line after we've captured something = next heading
                if taken and k2 == "prose" and len(u2) < 60 and not re.search(r"\d|[.:;]$", u2):
                    break
                if k2 != "blank" and _AMOUNT.search(u2) and len(u2) < 1500:
                    keep.setdefault(j, u2)
                    taken += 1
                j += 1
            i = j
        i += 1
    seen, out = set(), []
    for i in sorted(keep):
        k = keep[i]
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


_NUM = re.compile(r"(?<![A-Za-z])((?:NT|US|HK|NZ|A|C|S|R)?[$€£¥])\s?(\(?)\s?(\d[\d,]*(?:\.\d+)?)\s?(\)?)\s*(billion|million|thousand|bn|mn|[BMK]\b)?", re.I)


_RESPECTIVELY = re.compile(r"\bGAAP and non-GAAP [^.]{0,60}?(?:per (?:diluted )?share|EPS)[^.$]{0,40}?"
                           r"\$\s?(\(?\d+\.\d+\)?)\s*and\s*\$\s?(\(?\d+\.\d+\)?),? respectively", re.I)


def extract_headline(text: str) -> dict:
    """First revenue, GAAP EPS and non-GAAP EPS $ figures in the release's
    prose (tables only as fallback). Each value is labelled by the ~100
    chars since the previous $ figure. conf: high = explicit GAAP/non-GAAP
    label in window; med = inferred; low = from a table row."""
    out: dict[str, dict] = {}
    units = [(k, u) for k, u in _units(text[:20000]) if k != "blank"]
    for k, u in units:
        m = _RESPECTIVELY.search(u) if k == "prose" else None
        if m and not _BOILER.search(u):
            for key, grp in (("eps_gaap", 1), ("eps_nongaap", 2)):
                v = m.group(grp)
                out[key] = {"value": -float(v.strip("()")) if v.startswith("(") else float(v),
                            "conf": "high", "snippet": u[:400]}
            break
    for pass_kind in ("prose", "row"):
        for kind, u in units:
            if kind != pass_kind or _BOILER.search(u):
                continue
            if kind == "prose" and re.search(r"\b(expects?|outlook|guidance|anticipat)", u, re.I):
                continue
            last = 0
            for m in _NUM.finditer(u):
                win = u[max(last, m.start() - 110):m.start()]
                post = u[m.end():m.end() + 30]
                last = m.end()
                ccy, neg, num, close, unit = m.groups()
                val = float(num.replace(",", "")) * (-1 if neg and close else 1)
                unit = (unit or "").lower()
                snip = u if len(u) < 400 else u[max(0, m.start() - 200):m.end() + 100]
                # label from the sentence so far: "Non-GAAP net income was $X, or $Y per share"
                label = re.search(r"non-?gaap|adjusted|core\b|pro forma", u[max(0, m.start() - 160):m.start()]
                                  if kind == "prose" else win, re.I)
                per_share = r"per (diluted |basic )?(ordinary )?share|\bEPS\b|per ADS"
                if re.search(per_share, win, re.I) or (not unit and re.match(r"\s*" + per_share, post, re.I)):
                    if "range" in win.lower() or re.search(r"shares? outstanding|dividend", win, re.I):
                        continue
                    key = "eps_nongaap" if label else "eps_gaap"
                    conf = "low" if kind == "row" else (
                        "high" if (label or re.search(r"\bGAAP\b", u[max(0, m.start() - 160):m.start()])) else "med")
                    if key not in out and val < 1000 and not (label and re.search(r"\bGAAP and non-GAAP\b", win, re.I)):
                        out[key] = {"value": val, "ccy": ccy or "$", "conf": conf, "snippet": snip}
                elif re.match(r"\s*(of |in )?(total |net |quarterly )*(revenues?|sales)\b", post, re.I) or (
                        re.search(r"\b(total |net |quarterly )?(revenues?|net sales|sales)\b", win, re.I)
                        and not re.search(r"per share|margin|cost of|income|backlog|segment|\bEPS\b", win[-60:], re.I)
                        and not re.match(r"\s*(of |in )?(net income|net profit|net loss|operating|gross|free cash|"
                                         r"cash|EBITDA|income)", post, re.I)):
                    if "revenue" not in out and (unit or kind == "row"):
                        conf = "low" if kind == "row" else ("high" if re.search(r"quarter|three months|Q[1-4]", u) else "med")
                        out["revenue"] = {"value": val, "unit": unit or "table", "ccy": ccy or "$", "conf": conf, "snippet": snip}
        if len(out) == 3:
            break
    return out


def extract(text: str) -> tuple[list[str], str]:
    return extract_guidance(text), json.dumps(extract_headline(text))


# ------------------------------------------------------------------- storage

def _state() -> dict:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}


def _save_state(st: dict) -> None:
    tmp = STATE_PATH.with_suffix(f".{os.getpid()}.part")
    tmp.write_text(json.dumps(st, indent=0))
    tmp.rename(STATE_PATH)


def _cols_sql() -> str:
    return "{" + ", ".join(f"'{k}': '{v}'" for k, v in COLS.items()) + "}"


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    con = duckdb.connect()
    try:
        cur = con.execute(f"SELECT * FROM read_parquet('{path}')")
        names = [d[0] for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        con.close()


def _write_rows(path: Path, rows: list[dict]) -> None:
    nd = path.with_suffix(".ndjson")
    with open(nd, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    part = path.with_suffix(".part")
    con = duckdb.connect()
    try:
        con.execute(f"""COPY (SELECT * FROM read_json('{nd}', format='newline_delimited', columns={_cols_sql()})
                        ORDER BY filed DESC) TO '{part}' (FORMAT parquet, COMPRESSION zstd)""")
    finally:
        con.close()
        nd.unlink(missing_ok=True)
    part.rename(path)


# -------------------------------------------------------------------- ingest

def candidates(ciks: list[int]) -> tuple[list[tuple], list[tuple]]:
    """(item-2.02 8-Ks, 6-Ks) within the lookback, newest first, as
    (cik, accn, form, filed, primary_doc_desc)."""
    cutoff = (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    eightk, sixk = [], []
    for cik in ciks:
        r = universe.submissions(cik)["filings"]["recent"]
        for i, form in enumerate(r["form"]):
            if r["filingDate"][i] < cutoff:
                continue
            row = (cik, r["accessionNumber"][i], form, r["filingDate"][i], r["primaryDocDescription"][i])
            if form == "8-K" and "2.02" in (r["items"][i] or "").split(","):
                eightk.append(row)
            elif form == "6-K" and (r["size"][i] or 0) >= MIN_6K_BYTES:
                sixk.append(row)
    key = lambda x: (x[3], x[1])
    return sorted(eightk, key=key, reverse=True), sorted(sixk, key=key, reverse=True)


def _fetch_text(doc: dict) -> str | None:
    resp = sec_http.get(doc["url"])
    if resp.status_code != 200:
        return None
    raw = resp.content.decode("utf-8", errors="replace") if resp.encoding is None else resp.text
    return html_to_text(raw) if not doc["name"].lower().endswith(".txt") else raw


def ingest_company(stock: dict, st: dict) -> dict:
    """Fetch any new releases for one company. Updates st[ticker] in place:
    {'seen': {accn: status}, 'reason': str|None}."""
    t = stock["ticker"]
    cs = st.setdefault(t, {"seen": {}, "reason": None})
    seen = cs["seen"]
    if not stock["ciks"]:
        cs["reason"] = "no_cik"
        return cs
    eightk, sixk = candidates(stock["ciks"])
    new_rows = []

    def make_row(cik, accn, form, filed, doc, method, text):
        g, h = extract(text)
        return {"ticker": t, "cik": cik, "accn": accn, "form": form, "filed": filed, "doc_name": doc["name"],
                "method": method, "text": text, "words": len(text.split()), "guidance": g, "headline": h}

    if eightk:
        # walk past 2.02s with no usable exhibit (results in the 8-K body,
        # pre-announcements) until N_RELEASES press releases are stored
        got = 0
        for cik, accn, form, filed, _ in eightk:
            if got >= N_RELEASES:
                break
            if accn in seen:
                got += seen[accn] == "ok"
                continue
            doc, method = pick_exhibit(filing_docs(cik, accn))
            text = _fetch_text(doc) if doc else None
            if not text or len(text.split()) < 50:
                seen[accn] = method if not doc else "empty_exhibit"
                continue
            new_rows.append(make_row(cik, accn, form, filed, doc, method, text))
            seen[accn] = "ok"
            got += 1
        cs["reason"] = None if any(v == "ok" for v in seen.values()) else "exhibit_not_found"
    elif sixk:
        hits = 0
        for cik, accn, form, filed, pdesc in sixk[:MAX_6K_SCAN]:
            if hits >= N_RELEASES:
                break
            if accn in seen:
                hits += seen[accn] == "ok"
                continue
            docs = filing_docs(cik, accn)
            htm = [d for d in docs if _is_htm(d) and d["size"] <= MAX_DOC_BYTES and not d["name"].endswith(".txt")]
            desc_hit = [d for d in htm if _RESULTS_DESC.search(d["desc"])]
            if desc_hit:
                doc = max(desc_hit, key=lambda d: d["size"])
                method = "guess_6k_desc"
            else:
                doc, _ = pick_exhibit(htm)
                doc = doc or (max(htm, key=lambda d: d["size"]) if htm else None)
                method = "guess_6k_text"
            text = _fetch_text(doc) if doc else None
            head = (text or "")[:2500]
            ok = bool(text) and len(text.split()) >= 150 and (
                method == "guess_6k_desc" or (_RESULTS_HEAD.search(head) and _PERIOD_HEAD.search(head)))
            if ok and not _AMOUNT.search(text[:20000]):
                ok = False
            if not ok:
                seen[accn] = "not_results"
                continue
            new_rows.append(make_row(cik, accn, form, filed, doc, method, text))
            seen[accn] = "ok"
            hits += 1
        cs["reason"] = None if any(v == "ok" for v in seen.values()) else "6k_no_results_found"
    else:
        cs["reason"] = "no_2.02_or_6k"
    if new_rows:
        path = REL_DIR / f"{t}.parquet"
        rows = {r["accn"]: r for r in _read_rows(path)}
        rows.update({r["accn"]: r for r in new_rows})
        _write_rows(path, list(rows.values()))
    return cs


def ingest(tickers: list[str] | None = None) -> dict:
    st = _state()
    stocks = universe.stocks()
    if tickers:
        want = {x.upper() for x in tickers}
        stocks = [s for s in stocks if s["ticker"] in want]
    t0 = time.time()
    for n, s in enumerate(stocks, 1):
        try:
            cs = ingest_company(s, st)
        except Exception as e:  # keep going; recorded for the report
            cs = st.setdefault(s["ticker"], {"seen": {}, "reason": None})
            cs["reason"] = f"error: {type(e).__name__}: {e}"[:200]
        _save_state(st)
        ok = sum(1 for v in cs["seen"].values() if v == "ok")
        print(f"[{n}/{len(stocks)} {time.time() - t0:5.0f}s] {s['ticker']:8} ok={ok} {cs['reason'] or ''}", flush=True)
    return stats()


def reextract() -> int:
    n = 0
    for path in REL_DIR.glob("*.parquet"):
        rows = _read_rows(path)
        for r in rows:
            r["guidance"], r["headline"] = extract(r["text"])
        _write_rows(path, rows)
        n += len(rows)
    return n


def _glob() -> str:
    return f"read_parquet('{REL_DIR}/*.parquet')"


def stats() -> dict:
    st = _state()
    reasons: dict[str, int] = {}
    for v in st.values():
        if v["reason"]:
            r = "error" if v["reason"].startswith("error") else v["reason"]
            reasons[r] = reasons.get(r, 0) + 1
    con = duckdb.connect()
    try:
        q = con.execute(f"""
            WITH r AS (SELECT *, headline::JSON h FROM {_glob()})
            SELECT count(*), count(DISTINCT ticker),
                   count(*) FILTER (WHERE len(guidance) > 0),
                   count(DISTINCT ticker) FILTER (WHERE len(guidance) > 0),
                   count(*) FILTER (WHERE len(list_filter(guidance, g -> regexp_matches(g,
                       '(?i)(revenue|sales|per share|EPS)'))) > 0),
                   count(DISTINCT ticker) FILTER (WHERE len(list_filter(guidance, g -> regexp_matches(g,
                       '(?i)(revenue|sales|per share|EPS)'))) > 0),
                   count(*) FILTER (WHERE (h->'revenue') IS NOT NULL),
                   count(*) FILTER (WHERE (h->'eps_gaap') IS NOT NULL),
                   count(*) FILTER (WHERE (h->'eps_nongaap') IS NOT NULL),
                   count(*) FILTER (WHERE (h->>'$.revenue.conf') = 'high'),
                   count(*) FILTER (WHERE form = '6-K'), count(DISTINCT ticker) FILTER (WHERE form = '6-K'),
                   median(words)::INT, median(len(guidance))::INT
            FROM r
        """).fetchone()
        by_method = dict(con.execute(f"SELECT method, count(*) FROM {_glob()} GROUP BY 1 ORDER BY 2 DESC").fetchall())
    finally:
        con.close()
    size = sum(p.stat().st_size for p in REL_DIR.glob("*.parquet"))
    keys = ["releases", "companies", "rel_with_guidance", "cos_with_guidance", "rel_guidance_rev_or_eps",
            "cos_guidance_rev_or_eps", "rel_revenue", "rel_eps_gaap",
            "rel_eps_nongaap", "rel_revenue_high_conf", "rel_6k", "cos_6k", "median_words", "median_guidance_units"]
    return dict(zip(keys, q)) | {"by_method": by_method, "misses": reasons, "universe": len(st),
                                  "disk_mb": round(size / 1e6, 2)}


def latest(ticker: str) -> dict | None:
    con = duckdb.connect()
    try:
        path = REL_DIR / f"{ticker.upper()}.parquet"
        if not path.exists():
            return None
        cur = con.execute(f"SELECT * FROM read_parquet('{path}') ORDER BY filed DESC LIMIT 1")
        names = [d[0] for d in cur.description]
        return dict(zip(names, cur.fetchone()))
    finally:
        con.close()


def show(ticker: str) -> None:
    r = latest(ticker)
    if not r:
        print(f"{ticker}: no release stored ({_state().get(ticker.upper(), {}).get('reason')})")
        return
    print(f"{r['ticker']}  {r['form']}  filed {r['filed']}  {r['accn']}  {r['doc_name']} ({r['method']}, {r['words']} words)")
    for k, v in json.loads(r["headline"]).items():
        print(f"  {k:12} {v.get('ccy', '$'):>3} {v['value']:>12,} {v.get('unit', ''):8} [{v['conf']}]  {v['snippet'][:110]}")
    print(f"\nguidance ({len(r['guidance'])}):")
    for g in r["guidance"]:
        print(f"  - {g}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "ingest":
        print(json.dumps(ingest(sys.argv[2:] or None), indent=2))
    elif cmd == "show":
        for t in sys.argv[2:]:
            show(t)
    elif cmd == "reextract":
        print(reextract(), "rows re-extracted")
        print(json.dumps(stats(), indent=2))
    else:
        print(json.dumps(stats(), indent=2))
