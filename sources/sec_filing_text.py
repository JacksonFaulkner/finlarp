"""Annual-report text (10-K / 20-F / 40-F) and Exhibit 21 subsidiaries.

Per universe company, the latest two annual reports: the latest so the
text is current, the prior one so Risk Factors can be diffed year over
year. Only the narrative sections are kept:

    section         10-K    20-F       40-F (best effort, exhibits)
    business        1       4          AIF "Description of the Business"
    risk_factors    1A      3.D        AIF "Risk Factors"
    cybersecurity   1C      16K        -
    mda             7       5          MD&A exhibit
    market_risk     7A      11         -

Item 8 / 18 (financials) is dropped — XBRL has it.

Splitting: the HTML is flattened to block-level lines (div/p/tr/li...),
keeping, per line, the fraction of characters in bold/italic runs. Item
headings are lines that *start* with "Item N" followed by a title (or an
empty remainder, title on the next line). Every item appears at least
twice (table of contents, then body), so for each item we keep the
candidate followed by the most text before the next different item's
heading — the TOC entry is followed by one line, the body by pages.

Staging is one gzip JSON per accession under parsed/ (the resume marker);
`build()` turns those into Parquet and computes the YoY risk diff, which
needs both years:

    filings.parquet       one row per filing: metrics + parse status
    sections.parquet      ticker, cik, accn, form, fiscal_period_end, section, text, words, parse_ok
    subsidiaries.parquet  ticker, accn, subsidiary, jurisdiction (Exhibit 21 / 20-F Exhibit 8)
    risk_diff.parquet     sentences added to (or removed from) Risk Factors vs the prior report

    uv run python sources/sec_filing_text.py ingest [TICKER ...]
    uv run python sources/sec_filing_text.py build
    uv run python sources/sec_filing_text.py show TICKER
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path

import duckdb

from sources import sec_http, universe

ANNUAL_FORMS = ("10-K", "10-KT", "20-F", "40-F")
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
PARSER_VERSION = 2


def _dir(name: str = "") -> Path:
    d = universe.data_dir("filing_text")
    if name:
        d = d / name
        d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------
# HTML -> lines
# --------------------------------------------------------------------------

_BLOCK = {
    "p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table",
    "ul", "ol", "section", "article", "header", "footer", "blockquote", "hr",
    "pre", "center", "dt", "dd", "page", "title",
}
_VOID = {"br", "hr", "img", "input", "meta", "link", "col", "area", "base", "wbr", "param", "source"}
_SKIP = {"script", "style", "ix:header", "head"}
_EMPH_TAGS = {"b", "strong", "i", "em", "u"}
_EMPH_STYLE = re.compile(r"font-weight\s*:\s*(bold|[6-9]00)|font-style\s*:\s*italic|text-decoration\s*:\s*underline", re.I)


class _Flatten(HTMLParser):
    """Block-level lines with the share of characters in emphasised runs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[tuple[str, float]] = []
        self._buf: list[tuple[str, bool]] = []
        self._stack: list[tuple[str, bool]] = []
        self._skip = 0

    def _emph(self) -> bool:
        return any(e for _, e in self._stack)

    def _flush(self) -> None:
        if not self._buf:
            return
        text = "".join(t for t, _ in self._buf)
        norm = " ".join(text.split())
        if norm:
            total = sum(len(t.strip()) for t, _ in self._buf) or 1
            emph = sum(len(t.strip()) for t, e in self._buf if e)
            self.lines.append((norm, emph / total))
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip += 1
            return
        if tag in _BLOCK:
            self._flush()
        if tag in _VOID:
            return
        style = next((v for k, v in attrs if k == "style" and v), "")
        self._stack.append((tag, tag in _EMPH_TAGS or bool(_EMPH_STYLE.search(style))))

    def handle_startendtag(self, tag, attrs):
        if tag in _BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
            return
        if tag in ("td", "th"):
            self._buf.append((" ", False))
        if tag in _BLOCK:
            self._flush()
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        if not self._skip and data:
            self._buf.append((data.replace("\xa0", " "), self._emph()))

    def close(self):
        super().close()
        self._flush()


_JUNK_LINE = re.compile(r"^(?:\d{1,3}|[ivxlc]{1,6}|page \d+|-\s*\d+\s*-|table of contents|index)$", re.I)


def html_lines(html: str) -> list[tuple[str, float]]:
    """Flatten HTML, dropping page numbers and running headers/footers
    (short lines repeated more than 8 times)."""
    if "<" not in html[:2000] and "<html" not in html.lower()[:5000]:
        lines = [(" ".join(l.split()), 0.0) for l in html.splitlines()]
        lines = [l for l in lines if l[0]]
    else:
        p = _Flatten()
        p.feed(html)
        p.close()
        lines = p.lines
    counts = Counter(t for t, _ in lines if len(t) < 90)
    return [(t, e) for t, e in lines if not _JUNK_LINE.match(t) and not (len(t) < 90 and counts[t] > 8)]


def _words(text: str) -> int:
    return len(text.split())


# --------------------------------------------------------------------------
# Section splitting
# --------------------------------------------------------------------------

_ITEM_RE = re.compile(
    r"^\s*(?:part\s+[iv]+\s*[,\-–—.:]?\s*)?items?\s*(\d{1,2}(?:\s?[A-K])?)\b"
    r"(?:\s*(?:,|and|&)\s*\d{1,2}[A-K]?\b)*\s*[\.\:\-–—]?\s*(.*)$",
    re.I,
)
# Titles for the items we keep; other items only need a non-cross-ref remainder.
_TITLES_10K = {
    "1": r"business",
    "1A": r"risk\s+factors",
    "1C": r"cyber\s*security",
    "7": r"management.{0,3}s?\s+discussion",
    "7A": r"quantitative\s+and\s+qualitative",
}
_TITLES_20F = {
    "3": r"key\s+information",
    "4": r"information\s+on\s+the\s+company",
    "5": r"operating\s+and\s+financial\s+review",
    "11": r"quantitative\s+and\s+qualitative",
    "16K": r"cyber\s*security",
}
KEEP_10K = {"1": "business", "1A": "risk_factors", "1C": "cybersecurity", "7": "mda", "7A": "market_risk"}
KEEP_20F = {"4": "business", "5": "mda", "11": "market_risk", "16K": "cybersecurity"}
_XREF_REST = re.compile(r"^(?:[a-z]|[,;(\"“”’'])")  # "Item 7 of Part II", "Item 1A, ..."
_RISK_20F = re.compile(r"^(?:item\s*)?(?:3\s*\.?\s*)?(?:\(?d\)?\s*[\.\-–—:]?\s*)?risks?\s+factors\b\.?\s*(.*)$", re.I)


def _norm_q(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def _item_candidates(lines: list[tuple[str, float]], titles: dict[str, str]) -> list[tuple[int, str]]:
    out = []
    for i, (t, _) in enumerate(lines):
        if len(t) > 400 or not t[:12].lower().lstrip().startswith(("item", "part")):
            continue
        m = _ITEM_RE.match(_norm_q(t))
        if not m:
            continue
        key = re.sub(r"\s", "", m.group(1)).upper()
        rest = m.group(2).strip()
        if not rest and i + 1 < len(lines):
            rest = lines[i + 1][0]
        if key in titles:
            if not re.match(titles[key], rest, re.I):
                continue
        elif rest and _XREF_REST.match(rest):
            continue
        out.append((i, key))
    return out


def _pick_starts(lines: list[tuple[str, float]], cands: list[tuple[int, str]]) -> dict[str, int]:
    """Per item, the candidate followed by the most words before the next
    heading of a different item."""
    cum = [0]
    for t, _ in lines:
        cum.append(cum[-1] + _words(t))
    best: dict[str, tuple[int, int]] = {}
    for j, (i, key) in enumerate(cands):
        nxt = next((i2 for i2, k2 in cands[j + 1:] if k2 != key), len(lines))
        size = cum[nxt] - cum[i + 1]
        if key not in best or size > best[key][1]:
            best[key] = (i, size)
    return {k: v[0] for k, v in best.items()}


def _slice(lines, start: int, end: int) -> str:
    return "\n".join(t for t, _ in lines[start:end])


def _sections_by_item(lines, titles, keep) -> tuple[dict[str, tuple[int, int]], dict[str, int]]:
    cands = _item_candidates(lines, titles)
    starts = _pick_starts(lines, cands)
    order = sorted(starts.values())
    # An item whose body heading was not found keeps its TOC entry; drop it
    # if it sits before an item that precedes it in numbering.
    canon = sorted(starts, key=lambda k: (int(re.match(r"\d+", k).group()), k))
    spans, run_max = {}, -1
    for key in canon:
        s = starts[key]
        e = next((o for o in order if o > s), len(lines))
        if key in keep and s > run_max:
            spans[keep[key]] = (s + 1, e)
        run_max = max(run_max, s)
    return spans, starts


def split_10k(lines):
    spans, _ = _sections_by_item(lines, _TITLES_10K, KEEP_10K)
    return spans


def split_20f(lines):
    spans, starts = _sections_by_item(lines, _TITLES_20F, KEEP_20F)
    if "3" in starts:
        s3 = starts["3"]
        e3 = next((o for o in sorted(starts.values()) if o > s3), len(lines))
        for i in range(s3 + 1, e3):
            t = lines[i][0]
            if len(t) < 200:
                if re.fullmatch(r"(?:3\s*\.?\s*)?\(?D\)?\.?", t) and i + 1 < e3:
                    t = lines[i + 1][0]  # "D." and the title in separate cells
                m = _RISK_20F.match(t)
                if m and not _XREF_REST.match(m.group(1) or "X"):
                    spans["risk_factors"] = (i + 1, e3)
                    break
    return spans


# Generic fallback for reports laid out as an "annual report" with a 20-F /
# 10-K cross-reference index rather than Item headings (ASML, SAP, ...):
# short heading-ish lines with an exact title.
_FALLBACK_TITLES = {
    "risk_factors": r"(?:[\d.]+\s*)?risks?\s+factors",
    "mda": r"(?:[\d.]+\s*)?(?:operating\s+and\s+financial\s+review(?:\s+and\s+prospects)?|management'?s\s+discussion\s+and\s+analysis.*)",
    "business": r"(?:[\d.]+\s*)?(?:business\s+overview|information\s+on\s+the\s+company|(?:description\s+of\s+(?:the\s+|our\s+)?)?business|our\s+business|narrative\s+description\s+of\s+the\s+business)",
    "cybersecurity": r"(?:[\d.]+\s*)?cyber\s*security",
}


def _headingish(t: str, emph: float) -> bool:
    return len(t) <= 100 and (emph >= 0.6 or (t.upper() == t and any(c.isalpha() for c in t)))


def split_fallback(lines, want=("business", "risk_factors", "mda", "cybersecurity")):
    heads = [i for i, (t, e) in enumerate(lines) if _headingish(t, e)]
    cum = [0]
    for t, _ in lines:
        cum.append(cum[-1] + _words(t))
    spans = {}
    for sec in want:
        rx = re.compile(r"^" + _FALLBACK_TITLES[sec] + r"\.?$", re.I)
        best = None
        for j, i in enumerate(heads):
            if not rx.match(_norm_q(lines[i][0])):
                continue
            # end at the next heading of equal-or-stronger "caps" style that
            # is not itself a sub-heading of this section: approximated by
            # the next all-caps heading line (risk sub-headings are sentences).
            e = next((h for h in heads[j + 1:] if lines[h][0].upper() == lines[h][0] and _words(lines[h][0]) <= 8
                      and not rx.match(lines[h][0])), len(lines))
            size = cum[e] - cum[i + 1]
            if best is None or size > best[2]:
                best = (i + 1, e, size)
        if best and best[2] > 200:
            spans[sec] = (best[0], best[1])
    return spans


REQUIRED = {"10-K": ("business", "risk_factors", "mda"), "20-F": ("business", "risk_factors", "mda"),
            "40-F": ("risk_factors",)}
MIN_WORDS = {"business": 400, "risk_factors": 1000, "mda": 800}
_INCORP = re.compile(r"incorporated\s+(?:herein\s+)?by\s+reference|smaller\s+reporting\s+compan", re.I)


def split(lines, form: str) -> tuple[dict[str, tuple[int, int]], str, str | None]:
    """-> ({section: (start, end) line span}, method, failure reason or None)."""
    base = "20-F" if form.startswith("20-F") else "10-K" if form.startswith("10-K") else "40-F"
    spans = split_20f(lines) if base == "20-F" else split_10k(lines) if base == "10-K" else {}
    method = "items"
    required = REQUIRED[base]
    texts = {k: _slice(lines, s, e) for k, (s, e) in spans.items()}

    def bad(ts):
        return [k for k in required if _words(ts.get(k, "")) < MIN_WORDS.get(k, 0)]

    missing = bad(texts)
    if missing:
        fb_spans = split_fallback(lines, tuple(missing))
        fb = {k: _slice(lines, s, e) for k, (s, e) in fb_spans.items()}
        better = {k for k, v in fb.items() if _words(v) > _words(texts.get(k, ""))}
        merged = texts | {k: fb[k] for k in better}
        if len(bad(merged)) < len(missing):
            texts, method = merged, "items+fallback" if spans else "fallback"
            spans = spans | {k: fb_spans[k] for k in better}
            missing = bad(texts)
    reason = None
    if missing:
        if not spans and method == "items":
            reason = "no_item_headings"
        elif sum(_words(t) < 40 for t in texts.values()) >= max(2, len(texts) - 1):
            # every Item heading is followed by a page reference: the 10-K /
            # 20-F is a cross-reference index into an annual-report layout
            reason = "cross_reference_index:" + ",".join(missing)
        else:
            parts = []
            for k in missing:
                t = texts.get(k, "")
                if not t:
                    parts.append(f"missing:{k}")
                elif _INCORP.search(t[:3000]):
                    parts.append(f"by_reference:{k}")
                else:
                    parts.append(f"short:{k}")
            reason = ",".join(parts)
    return {k: spans[k] for k, v in texts.items() if v.strip()}, method, reason


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

_AI = {
    "ai": re.compile(r"\bAI\b"),
    "artificial_intelligence": re.compile(r"\bartificial[\s-]+intelligence\b", re.I),
    "machine_learning": re.compile(r"\bmachine[\s-]+learning\b", re.I),
    "generative": re.compile(r"\bgenerative\b", re.I),
}
_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+(?=[A-Z“\"(])|\n+")
_PATENT = re.compile(
    r"(?:approximately|over|more than|about|nearly|in excess of)?\s*"
    r"\b(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(thousand|million)?\+?\s+"
    r"(?:[\w\-]+\s+){0,7}?patents?\b",
    re.I,
)


_TERMINAL = tuple(".!?:;\"”’)")


def unwrap(text: str) -> str:
    """Re-join hard-wrapped lines (some filings are PDF-converted HTML with
    one <div> per printed line). A line break is kept only after terminal
    punctuation, or after a short line followed by a capital (a heading)."""
    lines = [" ".join(l.split()) for l in text.split("\n")]
    lines = [l for l in lines if l]
    if not lines:
        return ""
    out = [lines[0]]
    for l in lines[1:]:
        prev = out[-1]
        if prev.endswith(_TERMINAL) or (len(prev) < 60 and l[:1].isupper() and not prev[-1:].islower()) \
                or (len(prev) < 60 and l[:1].isupper() and len(prev.split()) <= 8 and prev[:1].isupper()
                    and sum(w[:1].isupper() for w in prev.split()) >= len(prev.split()) / 2):
            out.append(l)
        else:
            out[-1] = prev + " " + l
    return "\n".join(out)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(unwrap(text)) if s and s.strip()]


def ai_counts(text: str) -> dict[str, int]:
    return {k: len(rx.findall(text)) for k, rx in _AI.items()}


def patent_sentences(text: str) -> tuple[list[str], int | None]:
    out, best = [], None
    for s in sentences(text):
        low = s.lower()
        if "patent" not in low or len(s) > 800 or re.search(r"inventor|doctoral|dr\.|professor", low):
            continue
        for m in _PATENT.finditer(s):
            raw = m.group(1).replace(",", "")
            n = float(raw)
            mult = {"thousand": 1e3, "million": 1e6}.get((m.group(2) or "").lower(), 1)
            if mult == 1 and ("." in raw or (1990 <= n <= 2040 and "," not in m.group(1))):
                continue  # years, "Section 1.5"
            n = int(n * mult)
            if n < 2:
                continue
            if s not in out:
                out.append(s)
            best = max(best or 0, n)
    return out[:8], best


def risk_factor_count(lines_slice: list[tuple[str, float]]) -> int:
    """Risk headings are emphasised sentence-length lines (category
    headers like "Risks Related to Our Business" are short, excluded)."""
    n = 0
    for t, e in lines_slice:
        w = _words(t)
        if e >= 0.8 and 8 <= w <= 120 and not t.isupper():
            n += 1
    return n


_NUM = re.compile(r"\d[\d,.]*")


def _norm_sentence(s: str) -> str:
    s = _NUM.sub("#", _norm_q(s).lower())
    return " ".join(re.sub(r"[^a-z#' ]+", " ", s).split())


def _shingles(words: list[str], k: int = 5) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + k]) for i in range(max(1, len(words) - k + 1))}


def risk_diff(cur: str, prev: str, threshold: float = 0.5) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """(added, removed) sentences with novelty = share of the sentence's
    word 5-grams absent from the other year's whole Risk Factors section.
    Numbers are masked so "fiscal 2025" -> "fiscal 2026" is not new."""

    def side(a: str, b: str):
        b_sh: set = set()
        for s in sentences(b):
            b_sh |= _shingles(_norm_sentence(s).split())
        out, seen = [], set()
        for s in sentences(a):
            w = _norm_sentence(s).split()
            if len(w) < 8:
                continue
            key = " ".join(w)
            if key in seen:
                continue
            seen.add(key)
            sh = _shingles(w)
            novelty = sum(1 for x in sh if x not in b_sh) / len(sh)
            if novelty >= threshold:
                out.append((s, round(novelty, 3)))
        return out

    return side(cur, prev), side(prev, cur)


# --------------------------------------------------------------------------
# Exhibit 21
# --------------------------------------------------------------------------

class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip += 1
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).replace("\xa0", " ").split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            cells = [c for c in self._row if c and c not in ("%", "$")]
            if cells:
                self.rows.append(cells)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None and not self._skip:
            self._cell.append(data)


_SUB_HEADER = re.compile(
    r"^(?:name|legal|subsidiar|entity|company|legal name|jurisdiction|state or|country|place of|percent|ownership|"
    r"exhibit|list of|significant subsidiar|incorporat|organized|domestic|foreign|international|[*†(])",
    re.I,
)
_JURIS_TAIL = re.compile(r"^(.{3,}?)\s*(?:\(([^()]{2,60})\)|[-–—,]\s*([A-Z][A-Za-z .]{2,40})|\s{2,}(\S.{1,40}))\s*$")


def parse_subsidiaries(html: str) -> list[tuple[str, str | None]]:
    p = _Tables()
    p.feed(html)
    p.close()
    out = []
    for cells in p.rows:
        cells = [c for c in cells if not re.fullmatch(r"[\d.,%\s]+|[-–—*]+", c)]
        if not cells or _SUB_HEADER.match(cells[0]) or len(cells[0]) > 200:
            continue
        name = cells[0]
        juris = cells[-1] if len(cells) > 1 else None
        if juris and len(juris) > 80:
            juris = None
        out.append((name, juris))
    if len(out) >= 2:
        return out
    # Not tabular: one subsidiary per line, jurisdiction in parens / after a dash.
    out = []
    raw = html if "<" not in html[:2000] else None
    text_lines = [l for l in (raw.splitlines() if raw else [t for t, _ in html_lines(html)])]
    for l in text_lines:
        l = " ".join(l.split()) if raw is None else l.rstrip()
        if not l.strip() or _SUB_HEADER.match(l.strip()) or len(l) > 200:
            continue
        m = _JURIS_TAIL.match(l.strip() if raw is None else l)
        if m:
            out.append((" ".join(m.group(1).split()), (m.group(2) or m.group(3) or m.group(4) or "").strip() or None))
        elif re.search(r"\b(inc|llc|ltd|limited|corp|gmbh|b\.v|s\.a|plc|co|pte|kk|ag|srl|sas|l\.p)\b\.?", l, re.I):
            out.append((" ".join(l.split()), None))
    return out


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------

def _get_text(url: str) -> str | None:
    r = sec_http.get(url)
    if r.status_code != 200:
        return None
    r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else (r.apparent_encoding or "utf-8")
    return r.text


def filing_documents(cik: int, accn: str) -> list[dict]:
    """[{seq, desc, doc, type}] from the filing's -index.htm."""
    nodash = accn.replace("-", "")
    html = _get_text(f"{ARCHIVES}/{cik}/{nodash}/{accn}-index.htm")
    if not html:
        return []
    p = _Tables()
    rows: list[list[str]] = []
    # Keep hrefs: re-scan for rows of the document table.
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(cells) < 4:
            continue
        href = re.search(r'href="([^"]+)"', cells[2])
        clean = [" ".join(re.sub(r"<[^>]+>", " ", c).split()) for c in cells]
        rows.append(clean + [href.group(1) if href else ""])
    del p
    out = []
    for r in rows:
        doc = r[-1].rsplit("/", 1)[-1] if r[-1] else r[2].split(" ")[0]
        if doc.startswith("ix?doc="):
            doc = doc.split("/")[-1]
        out.append({"seq": r[0], "desc": r[1], "doc": doc, "type": r[3]})
    return out


def _ex21(docs: list[dict], form: str) -> dict | None:
    for d in docs:
        t = d["type"].upper()
        if t.startswith("EX-21") or (form.startswith("20-F") and re.match(r"EX-8(\.|$)", t)):
            if d["doc"].lower().endswith((".htm", ".html", ".txt")):
                return d
    for d in docs:
        n = d["doc"].lower()
        if re.search(r"ex(?:hibit)?[-_ ]?21", n) or (form.startswith("20-F") and re.search(r"ex(?:hibit)?[-_ ]?0?8(?:[-_.]?0?1)?\.htm", n)):
            return d
    return None


def annual_filings(ciks: list[int], n: int = 2) -> list[dict]:
    rows = []
    for cik in ciks:
        try:
            rec = universe.submissions(cik)["filings"]["recent"]
        except Exception:
            continue
        for i, form in enumerate(rec["form"]):
            if form in ANNUAL_FORMS:
                rows.append({"cik": cik, "accn": rec["accessionNumber"][i], "form": form,
                             "filed": rec["filingDate"][i], "period": rec["reportDate"][i] or None,
                             "doc": rec["primaryDocument"][i]})
        if len(rows) >= n:
            break
    rows.sort(key=lambda r: r["filed"], reverse=True)
    return rows[:n]


def _staged(accn: str) -> Path:
    return _dir("parsed") / f"{accn}.json.gz"


def process_filing(stock: dict, f: dict, want_subs: bool) -> dict:
    """Fetch + parse one filing into a staged record."""
    cik, accn, form = f["cik"], f["accn"], f["form"]
    nodash = accn.replace("-", "")
    rec = {"ticker": stock["ticker"], "cik": cik, "accn": accn, "form": form, "filed": f["filed"],
           "fiscal_period_end": f["period"], "primary_doc": f["doc"], "parser": PARSER_VERSION,
           "sections": {}, "risk_lines": [], "subsidiaries": None, "doc_words": 0,
           "parse_ok": False, "parse_method": None, "parse_error": None}
    docs = filing_documents(cik, accn) if (want_subs or form == "40-F") else []

    if form == "40-F":
        lines = []
        texts: dict[str, str] = {}
        for d in docs:
            if not d["type"].upper().startswith("EX-99") or not d["doc"].lower().endswith((".htm", ".html")):
                continue
            html = _get_text(f"{ARCHIVES}/{cik}/{nodash}/{d['doc']}")
            if not html:
                continue
            ls = html_lines(html)
            head = " ".join(t for t, _ in ls[:80]).upper().replace("’", "'")
            if "ANNUAL INFORMATION FORM" in head and "business" not in texts:
                for k, (s, e) in split_fallback(ls, ("business", "risk_factors", "cybersecurity")).items():
                    texts[k] = _slice(ls, s, e)
                    if k == "risk_factors":
                        rec["risk_lines"] = ls[s:e]
                lines += ls
            elif "MANAGEMENT'S DISCUSSION" in head and "mda" not in texts:
                texts["mda"] = _slice(ls, 0, len(ls))
                lines += ls
        rec["sections"] = texts
        full = "\n".join(t for t, _ in lines)
        rec["parse_method"] = "40f_exhibits"
        rec["parse_ok"] = _words(texts.get("risk_factors", "")) >= MIN_WORDS["risk_factors"]
        if not rec["parse_ok"]:
            rec["parse_error"] = "40f_no_aif" if not lines else "40f_short:risk_factors"
    else:
        html = _get_text(f"{ARCHIVES}/{cik}/{nodash}/{f['doc']}")
        if html is None:
            rec["parse_error"] = "fetch_failed"
            return rec
        if f["doc"].lower().endswith(".pdf"):
            rec["parse_error"] = "pdf"
            return rec
        lines = html_lines(html)
        del html
        full = "\n".join(t for t, _ in lines)
        spans, method, reason = split(lines, form)
        texts = {k: _slice(lines, s, e) for k, (s, e) in spans.items()}
        if "risk_factors" in spans:  # heading detection needs the emphasis flags
            rec["risk_lines"] = lines[slice(*spans["risk_factors"])]
        rec.update(sections=texts, parse_method=method, parse_error=reason, parse_ok=reason is None)

    rec["doc_words"] = _words(full)
    rec["ai"] = ai_counts(full)
    rec["ai_sections"] = ai_counts("\n".join(rec["sections"].values()))
    pats, pnum = patent_sentences(full)
    rec["patent_sentences"], rec["patent_count"] = pats, pnum
    rec["risk_factor_count"] = risk_factor_count(rec["risk_lines"]) if rec["risk_lines"] else None
    rec.pop("risk_lines")

    if want_subs:
        ex = _ex21(docs, form)
        if ex:
            h = _get_text(f"{ARCHIVES}/{cik}/{nodash}/{ex['doc']}")
            rec["subsidiaries"] = parse_subsidiaries(h) if h else []
            rec["ex21_doc"] = ex["doc"]
        else:
            rec["subsidiaries"] = []
            rec["ex21_doc"] = None
    return rec


def ingest(tickers: list[str] | None = None, workers: int = 3, retry_failed: bool = False) -> dict:
    stocks = [s for s in universe.stocks() if s["cik"]]
    if tickers:
        want = {t.upper() for t in tickers}
        stocks = [s for s in stocks if s["ticker"].upper() in want]
    jobs, stats = [], Counter()
    for s in stocks:
        fs = annual_filings(s["ciks"])
        if not fs:
            stats["no_annual_filing"] += 1
            print(f"{s['ticker']}: no 10-K/20-F/40-F", flush=True)
        for k, f in enumerate(fs):
            p = _staged(f["accn"])
            if p.exists():
                if not retry_failed:
                    stats["skipped"] += 1
                    continue
                old = json.loads(gzip.decompress(p.read_bytes()))
                if old.get("parse_ok"):
                    stats["skipped"] += 1
                    continue
            jobs.append((s, f, k == 0))

    def run(job):
        s, f, subs = job
        t0 = time.time()
        try:
            rec = process_filing(s, f, subs)
        except Exception as e:  # keep going; record why
            rec = {"ticker": s["ticker"], "cik": f["cik"], "accn": f["accn"], "form": f["form"], "filed": f["filed"],
                   "fiscal_period_end": f["period"], "primary_doc": f["doc"], "parse_ok": False,
                   "parse_error": f"exception:{type(e).__name__}", "error": traceback.format_exc()[-800:],
                   "sections": {}}
        tmp = _staged(f["accn"]).with_suffix(".part")
        tmp.write_bytes(gzip.compress(json.dumps(rec).encode(), 6))
        tmp.rename(_staged(f["accn"]))
        return rec, time.time() - t0

    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(run, j) for j in jobs]
        for n, fut in enumerate(as_completed(futs), 1):
            rec, dt = fut.result()
            stats["parsed"] += 1
            stats["ok" if rec["parse_ok"] else "failed"] += 1
            words = {k: _words(v) for k, v in rec.get("sections", {}).items()}
            print(f"[{n}/{len(jobs)}] {rec['ticker']:<6} {rec['form']:<5} {rec['accn']} "
                  f"{'ok ' if rec['parse_ok'] else 'ERR'} {rec.get('parse_error') or ''} {words} {dt:.1f}s", flush=True)
    return dict(stats)


# --------------------------------------------------------------------------
# Build Parquet
# --------------------------------------------------------------------------

def _load_staged() -> list[dict]:
    return [json.loads(gzip.decompress(p.read_bytes())) for p in sorted(_dir("parsed").glob("*.json.gz"))]


def _copy(con, ndjson: Path, target: Path, columns: dict[str, str]) -> int:
    part = target.with_suffix(".part")
    cols = ", ".join(f"'{k}': '{v}'" for k, v in columns.items())
    con.execute(f"""COPY (SELECT * FROM read_json('{ndjson}', format='newline_delimited', columns={{{cols}}}))
                    TO '{part}' (FORMAT parquet, COMPRESSION zstd)""")
    part.rename(target)
    ndjson.unlink()
    return con.execute(f"SELECT count(*) FROM read_parquet('{target}')").fetchone()[0]


def build() -> dict[str, int]:
    recs = _load_staged()
    universe_tickers = {s["ticker"] for s in universe.stocks()}
    recs = [r for r in recs if r["ticker"] in universe_tickers]
    by_ticker: dict[str, list[dict]] = {}
    for r in recs:
        by_ticker.setdefault(r["ticker"], []).append(r)
    d = _dir()
    tmp = {k: d / f"{k}.ndjson" for k in ("filings", "sections", "subsidiaries", "risk_diff")}
    fh = {k: open(p, "w") for k, p in tmp.items()}
    try:
        for t, rs in by_ticker.items():
            rs.sort(key=lambda r: r["filed"], reverse=True)
            for i, r in enumerate(rs):
                prev = rs[i + 1] if i + 1 < len(rs) else None
                added = removed = None
                cur_rf, prev_rf = r["sections"].get("risk_factors"), (prev or {}).get("sections", {}).get("risk_factors")
                if cur_rf and prev_rf and min(_words(cur_rf), _words(prev_rf)) >= MIN_WORDS["risk_factors"]:
                    a, rm = risk_diff(cur_rf, prev_rf)
                    added, removed = len(a), len(rm)
                    for kind, lst in (("added", a), ("removed", rm)):
                        for s, nov in lst:
                            fh["risk_diff"].write(json.dumps({"ticker": t, "accn": r["accn"], "prior_accn": prev["accn"],
                                                              "kind": kind, "sentence": s, "novelty": nov}) + "\n")
                ai = r.get("ai") or {}
                dw = r.get("doc_words") or 0
                rf_sents = len([s for s in sentences(cur_rf or "") if len(s.split()) >= 8])
                fh["filings"].write(json.dumps({
                    "ticker": t, "cik": r["cik"], "accn": r["accn"], "form": r["form"], "filed": r["filed"],
                    "fiscal_period_end": r.get("fiscal_period_end"), "primary_doc": r.get("primary_doc"),
                    "parse_ok": r["parse_ok"], "parse_method": r.get("parse_method"), "parse_error": r.get("parse_error"),
                    "doc_words": dw, "ai_mentions": sum(ai.values()), "ai_per_10k_words": round(sum(ai.values()) / dw * 1e4, 2) if dw else None,
                    "ai_term": ai.get("ai"), "artificial_intelligence": ai.get("artificial_intelligence"),
                    "machine_learning": ai.get("machine_learning"), "generative": ai.get("generative"),
                    "patent_count": r.get("patent_count"), "patent_sentences": r.get("patent_sentences") or [],
                    "risk_factor_count": r.get("risk_factor_count"), "risk_sentences": rf_sents,
                    "prior_accn": prev["accn"] if added is not None else None,
                    "risk_added": added, "risk_removed": removed,
                    "ex21_doc": r.get("ex21_doc"), "subsidiary_count": len(r["subsidiaries"]) if r.get("subsidiaries") is not None else None,
                }) + "\n")
                for sec, text in r["sections"].items():
                    text = unwrap(text)
                    fh["sections"].write(json.dumps({
                        "ticker": t, "cik": r["cik"], "accn": r["accn"], "form": r["form"],
                        "fiscal_period_end": r.get("fiscal_period_end"), "section": sec, "text": text,
                        "words": _words(text), "parse_ok": r["parse_ok"]}) + "\n")
                for name, juris in r.get("subsidiaries") or []:
                    fh["subsidiaries"].write(json.dumps({"ticker": t, "accn": r["accn"], "subsidiary": name,
                                                         "jurisdiction": juris}) + "\n")
    finally:
        for f in fh.values():
            f.close()
    con = duckdb.connect()
    try:
        return {
            "filings": _copy(con, tmp["filings"], d / "filings.parquet", {
                "ticker": "VARCHAR", "cik": "BIGINT", "accn": "VARCHAR", "form": "VARCHAR", "filed": "DATE",
                "fiscal_period_end": "DATE", "primary_doc": "VARCHAR", "parse_ok": "BOOLEAN", "parse_method": "VARCHAR",
                "parse_error": "VARCHAR", "doc_words": "BIGINT", "ai_mentions": "BIGINT", "ai_per_10k_words": "DOUBLE",
                "ai_term": "BIGINT", "artificial_intelligence": "BIGINT", "machine_learning": "BIGINT", "generative": "BIGINT",
                "patent_count": "BIGINT", "patent_sentences": "VARCHAR[]", "risk_factor_count": "BIGINT",
                "risk_sentences": "BIGINT", "prior_accn": "VARCHAR", "risk_added": "BIGINT", "risk_removed": "BIGINT",
                "ex21_doc": "VARCHAR", "subsidiary_count": "BIGINT"}),
            "sections": _copy(con, tmp["sections"], d / "sections.parquet", {
                "ticker": "VARCHAR", "cik": "BIGINT", "accn": "VARCHAR", "form": "VARCHAR", "fiscal_period_end": "DATE",
                "section": "VARCHAR", "text": "VARCHAR", "words": "BIGINT", "parse_ok": "BOOLEAN"}),
            "subsidiaries": _copy(con, tmp["subsidiaries"], d / "subsidiaries.parquet", {
                "ticker": "VARCHAR", "accn": "VARCHAR", "subsidiary": "VARCHAR", "jurisdiction": "VARCHAR"}),
            "risk_diff": _copy(con, tmp["risk_diff"], d / "risk_diff.parquet", {
                "ticker": "VARCHAR", "accn": "VARCHAR", "prior_accn": "VARCHAR", "kind": "VARCHAR",
                "sentence": "VARCHAR", "novelty": "DOUBLE"}),
        }
    finally:
        con.close()


def show(ticker: str, n_new: int = 8) -> None:
    d = _dir()
    con = duckdb.connect()
    t = ticker.upper()
    fs = con.execute(f"SELECT * FROM read_parquet('{d}/filings.parquet') WHERE ticker = ? ORDER BY filed DESC", [t]).fetchall()
    cols = [c[0] for c in con.description]
    if not fs:
        print(f"{t}: no filings")
        return
    for row in fs:
        f = dict(zip(cols, row))
        print(f"\n{t} {f['form']} {f['accn']} period {f['fiscal_period_end']} filed {f['filed']}  "
              f"parse_ok={f['parse_ok']} ({f['parse_method']}{', ' + f['parse_error'] if f['parse_error'] else ''})")
        secs = con.execute(f"SELECT section, words FROM read_parquet('{d}/sections.parquet') WHERE accn = ? ORDER BY section",
                           [f["accn"]]).fetchall()
        print("  sections: " + ", ".join(f"{s}={w:,}" for s, w in secs))
        print(f"  doc_words={f['doc_words']:,}  ai_mentions={f['ai_mentions']} ({f['ai_per_10k_words']}/10k words; "
              f"AI={f['ai_term']} artificial intelligence={f['artificial_intelligence']} "
              f"machine learning={f['machine_learning']} generative={f['generative']})")
        print(f"  risk factors: headings={f['risk_factor_count']} sentences={f['risk_sentences']} "
              f"added={f['risk_added']} removed={f['risk_removed']} vs {f['prior_accn']}")
        print(f"  subsidiaries={f['subsidiary_count']} ({f['ex21_doc']})  patent_count={f['patent_count']}")
        for s in (f["patent_sentences"] or [])[:2]:
            print(f"    patent: {s[:240]}")
        if f["prior_accn"]:
            new = con.execute(f"""SELECT sentence, novelty FROM read_parquet('{d}/risk_diff.parquet')
                                 WHERE accn = ? AND kind = 'added' ORDER BY novelty DESC, length(sentence) DESC LIMIT ?""",
                              [f["accn"], n_new]).fetchall()
            for s, nov in new:
                print(f"    + [{nov:.2f}] {s[:300]}")
    con.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    args = sys.argv[2:]
    if cmd == "ingest":
        retry = "--retry" in args
        t0 = time.time()
        print(json.dumps(ingest([a for a in args if not a.startswith("--")] or None, retry_failed=retry), indent=2))
        print(json.dumps(build(), indent=2))
        print(f"{time.time() - t0:.0f}s")
    elif cmd == "build":
        print(json.dumps(build(), indent=2))
    elif cmd == "show":
        show(args[0] if args else "MRVL")
    else:
        sys.exit(f"unknown command {cmd}")
