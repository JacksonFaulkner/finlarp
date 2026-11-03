"""10-K / 20-F / 10-Q HTML -> a typed block list for the TUI reader.

sec_filing_text.py flattens a filing to lines and keeps only the narrative
items. This keeps the whole document and its structure, so the reader can
render tables as tables, headings as an outline, and link numbers to XBRL:

    {"t": "h",     "level": 0-3, "text", "item"?}   PART / Item / bold / italic headings
    {"t": "p",     "spans": [Span]}                  paragraph (styled runs)
    {"t": "li",    "spans": [Span], "marker"}        bullet (incl. 2-cell bullet tables)
    {"t": "table", "kind", ...}                      see _table_block
    {"t": "img",   "src", "alt"}
    {"t": "page",  "n"?}                             page break (with its printed number)
    {"t": "note",  "concept"}                        start of an ix TextBlock (a financial note)

    Span = {"s": text, "b"?: 1, "i"?: 1, "u"?: 1, "x"?: concept}

Table kinds: "num" (financial grid: label column + value columns, header
cells with spans, per-row indent level and rules, XBRL concept per value),
"text", "cover" (checkboxes), "toc", "exhibits", "signature". One-cell
layout tables become paragraphs, bullet tables become "li" blocks.

Cache: data/filing_blocks/raw/<accn>.htm.gz (source) and
data/filing_blocks/<accn>.json.gz (parsed). Re-parsing never refetches.

    uv run python sources/filing_blocks.py fetch TICKER [--form 10-K]
    uv run python sources/filing_blocks.py parse FILE.htm [--out FILE.json]
    uv run python sources/filing_blocks.py show ACCN|TICKER
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PARSER_VERSION = 2
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

_BLOCK = {
    "p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol",
    "section", "article", "header", "footer", "blockquote", "hr", "pre",
    "center", "dt", "dd", "title", "table", "tr",
}
_VOID = {"br", "hr", "img", "input", "meta", "link", "col", "area", "base", "wbr", "param", "source"}
_SKIP = {"script", "style", "ix:header", "head", "title"}

_BOLD = re.compile(r"font-weight\s*:\s*(bold|bolder|[6-9]00)", re.I)
_ITAL = re.compile(r"font-style\s*:\s*italic", re.I)
_UNDER = re.compile(r"text-decoration[^;]*underline", re.I)
_HIDDEN = re.compile(r"display\s*:\s*none", re.I)
_PB_BEFORE = re.compile(r"(page-)?break-before\s*:\s*(always|page)", re.I)
_PB_AFTER = re.compile(r"(page-)?break-after\s*:\s*(always|page)", re.I)
_INDENT = re.compile(r"(padding-left|margin-left|text-indent)\s*:\s*(-?[\d.]+)\s*(pt|px|em|in|%)?", re.I)
_FSIZE = re.compile(r"font-size\s*:\s*([\d.]+)\s*(pt|px)?", re.I)
_BORDER = re.compile(r"border-(top|bottom)(-style)?\s*:\s*([^;\"]*)", re.I)

_NUM = re.compile(r"^\(?\s*[$€£¥]?\s*\(?\s*-?[\d,]*\.?\d+\s*\)?\s*%?\s*\)?$")
_DASH = re.compile(r"^[—–-]+$")
_SYMBOL = {"$", "%", ")", "(", "€", "£", "¥", "%)"}
_BULLETS = set("•●▪◦·‣∙○■□➢➤►-–—")
_ITEM = re.compile(r"^\s*item\s+(\d{1,2}[a-d]?|\d\.[a-z])\b[\s.:\-–—]*(.*)$", re.I)
_PART = re.compile(r"^\s*part\s+([ivx]+)\b", re.I)
_PAGE_NO = re.compile(r"^(?:page\s+)?(?:[A-Z]-)?\d{1,3}$|^[ivxlc]{1,6}$|^-\s*\d+\s*-$", re.I)
_UNITS = re.compile(
    r"\(?\s*((?:[\w$]+\s+){0,3}in\s+(?:millions|thousands|billions)\b[^)]*?)\s*\)?$", re.I
)
_PAGE_OF = re.compile(r"^page \d+ of \d+$", re.I)
_SGML_STUB = re.compile(r"^EX-\d+(\.\d+)?\s+\d+\s+\S+\.html?\b", re.I)
_FOOTNOTE = re.compile(r"^(\(\d{1,2}\)|\(\w\)|\*{1,3}|\d{1,2}\)|[†‡§])\s")


def _pt(val: str, unit: str | None) -> float:
    v = float(val)
    unit = (unit or "pt").lower()
    return {"px": v * 0.75, "em": v * 10, "in": v * 72, "%": v * 0.5}.get(unit, v)


def _clean(s: str) -> str:
    return " ".join(s.replace("\xa0", " ").replace("​", "").split())


class _Frame:
    __slots__ = ("tag", "b", "i", "u", "hidden", "x", "indent", "size", "pb_after", "rule_top", "rule_bot", "note")

    def __init__(self, tag, b, i, u, hidden, x, indent, size, pb_after, rule_top, rule_bot, note):
        self.tag, self.b, self.i, self.u, self.hidden, self.x = tag, b, i, u, hidden, x
        self.indent, self.size, self.pb_after = indent, size, pb_after
        self.rule_top, self.rule_bot, self.note = rule_top, rule_bot, note


def _rule(style: str) -> tuple[str | None, str | None]:
    top = bot = None
    for side, _, val in _BORDER.findall(style):
        val = val.lower()
        if "none" in val or "hidden" in val or re.search(r"\b0(px|pt)?\b", val) and "solid" not in val:
            continue
        kind = "double" if "double" in val else ("single" if re.search(r"solid|dotted|dashed|\dpx|\dpt", val) else None)
        if not kind:
            continue
        if side.lower() == "top":
            top = kind
        else:
            bot = kind
    return top, bot


class _Parser(HTMLParser):
    def __init__(self, base_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.base = base_url.rsplit("/", 1)[0] + "/" if base_url else ""
        self.blocks: list[dict] = []
        self.stack: list[_Frame] = []
        self.skip = 0
        self.spans: list[dict] = []  # current paragraph runs
        self.para_size = 0.0
        self.para_indent = 0.0
        self.tables: list[dict] = []  # open tables (nested ones flatten into the outer cell)
        self.cell: dict | None = None
        self.row: dict | None = None

    # -- style state ------------------------------------------------------
    def _top(self) -> _Frame | None:
        return self.stack[-1] if self.stack else None

    def _push(self, tag: str, attrs: list[tuple[str, str | None]]) -> _Frame:
        a = {k: (v or "") for k, v in attrs}
        style = a.get("style", "")
        par = self._top()
        name = a.get("name", "")
        x = par.x if par else None
        note = None
        if tag == "ix:nonfraction":
            x = name
        elif tag == "ix:nonnumeric" and name.endswith("TextBlock"):
            note = name
        ind = sum(_pt(v, u) for k, v, u in _INDENT.findall(style) if k.lower() != "text-indent" or float(v) > 0)
        fs = _FSIZE.search(style)
        rt, rb = _rule(style)
        f = _Frame(
            tag,
            (par.b if par else False) or tag in ("b", "strong") or bool(_BOLD.search(style)),
            (par.i if par else False) or tag in ("i", "em") or bool(_ITAL.search(style)),
            (par.u if par else False) or tag == "u" or bool(_UNDER.search(style)),
            (par.hidden if par else False) or bool(_HIDDEN.search(style)),
            x,
            (par.indent if par else 0.0) + ind,
            _pt(fs.group(1), fs.group(2)) if fs else (par.size if par else 0.0),
            bool(_PB_AFTER.search(style)),
            rt, rb, note,
        )
        if _PB_BEFORE.search(style) and not self.tables:
            self._flush()
            self._page()
        return f

    # -- output -----------------------------------------------------------
    def _emit_text(self, text: str, f: _Frame | None) -> None:
        span: dict[str, Any] = {"s": text}
        if f:
            if f.b:
                span["b"] = 1
            if f.i:
                span["i"] = 1
            if f.u:
                span["u"] = 1
            if f.x:
                span["x"] = f.x
        target = self.cell["spans"] if self.cell is not None else self.spans
        if target and {k: v for k, v in target[-1].items() if k != "s"} == {k: v for k, v in span.items() if k != "s"}:
            target[-1]["s"] += text
        else:
            target.append(span)
        if self.cell is None and not self.para_size and f:
            self.para_size, self.para_indent = f.size, f.indent

    def _flush(self) -> None:
        spans = _tidy(self.spans)
        self.spans = []
        size, self.para_size = self.para_size, 0.0
        self.para_indent = 0.0
        if spans:
            self.blocks.append(_para(spans, size))

    def _page(self) -> None:
        n = None
        # The printed page number is the last short numeric line before the break.
        if self.blocks and self.blocks[-1]["t"] == "p":
            txt = _text(self.blocks[-1]["spans"])
            if _PAGE_NO.match(txt):
                n = txt
                self.blocks.pop()
        if self.blocks and self.blocks[-1]["t"] == "page":
            if n and not self.blocks[-1].get("n"):
                self.blocks[-1]["n"] = n
            return
        self.blocks.append({"t": "page", **({"n": n} if n else {})})

    # -- HTMLParser hooks -------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        f = self._push(tag, attrs)
        if f.note and not f.hidden and not self.tables:
            self._flush()
            self.blocks.append({"t": "note", "concept": f.note})
        if tag == "img" and not f.hidden:
            a = dict(attrs)
            src = a.get("src") or ""
            if src and not src.startswith("data:"):
                if self.tables and self.cell is not None:
                    self.cell["img"] = self.base + src if "://" not in src else src
                else:
                    self._flush()
                    self.blocks.append({"t": "img", "src": self.base + src if "://" not in src else src, "alt": a.get("alt") or ""})
        if tag == "table":
            if not self.tables:
                self._flush()
            self.tables.append({"rows": []})
        elif tag == "tr" and len(self.tables) == 1:
            self.row = {"cells": [], "top": f.rule_top, "bot": f.rule_bot}
        elif tag in ("td", "th") and len(self.tables) == 1 and self.row is not None:
            a = dict(attrs)
            span = a.get("colspan") or "1"
            self.cell = {
                "spans": [], "span": int(span) if span.isdigit() and int(span) > 0 else 1,
                "indent": f.indent, "top": f.rule_top, "bot": f.rule_bot, "th": tag == "th",
            }
        elif self.cell is not None and tag in _BLOCK and self.cell["spans"]:
            self.cell["spans"].append({"s": " "})
            if f.indent > self.cell["indent"] and not _text(self.cell["spans"]).strip():
                self.cell["indent"] = f.indent
        elif self.cell is not None:
            # Indent / rules often live on a div inside the td.
            if f.indent > self.cell["indent"] and not _text(self.cell["spans"]).strip():
                self.cell["indent"] = f.indent
            self.cell["top"] = self.cell["top"] or f.rule_top
            self.cell["bot"] = self.cell["bot"] or f.rule_bot
        elif tag in _BLOCK and not self.tables:
            self._flush()
        if tag in _VOID:
            if f.pb_after and not self.tables:
                self._flush()
                self._page()
            return
        self.stack.append(f)

    def handle_startendtag(self, tag, attrs):
        # XHTML-style <td /> or <div />: an empty element, so open and close it
        # (otherwise empty spacer cells vanish and columns shift left).
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag in _VOID:
            return
        idx = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i].tag == tag), None)
        if idx is None:
            return
        frames = self.stack[idx:]
        del self.stack[idx:]
        if tag in ("td", "th") and self.cell is not None and len(self.tables) == 1:
            self.cell["spans"] = _tidy(self.cell["spans"])
            if self.row is not None:
                self.row["cells"].append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None and len(self.tables) == 1:
            self.tables[-1]["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.tables:
            t = self.tables.pop()
            if not self.tables:
                self.cell = self.row = None
                self.blocks.extend(_table_blocks(t))
        elif tag in _BLOCK and not self.tables:
            self._flush()
        if any(fr.pb_after for fr in frames) and not self.tables:
            self._flush()
            self._page()

    def handle_data(self, data):
        if self.skip or not data:
            return
        f = self._top()
        if f and f.hidden:
            return
        if self.tables and self.cell is None:
            return  # whitespace between cells
        self._emit_text(data.replace("\xa0", " "), f)

    def close(self):
        super().close()
        self._flush()


# --------------------------------------------------------------------------
# Spans / paragraphs
# --------------------------------------------------------------------------

def _text(spans: list[dict]) -> str:
    return "".join(s["s"] for s in spans)


def _tidy(spans: list[dict]) -> list[dict]:
    """Collapse whitespace across runs and drop empty ones."""
    out: list[dict] = []
    for sp in spans:
        s = re.sub(r"\s+", " ", sp["s"].replace("​", ""))
        if not s:
            continue
        if out and out[-1]["s"].endswith(" ") and s.startswith(" "):
            s = s[1:]
        if not s:
            continue
        if out and {k: v for k, v in out[-1].items() if k != "s"} == {k: v for k, v in sp.items() if k != "s"}:
            out[-1]["s"] += s
        else:
            out.append({**sp, "s": s})
    if out:
        out[0]["s"] = out[0]["s"].lstrip()
        out[-1]["s"] = out[-1]["s"].rstrip()
    return [s for s in out if s["s"]]


def _share(spans: list[dict], flag: str) -> float:
    total = sum(len(s["s"].strip()) for s in spans) or 1
    return sum(len(s["s"].strip()) for s in spans if s.get(flag)) / total


def _para(spans: list[dict], size: float) -> dict:
    text = _text(spans)
    if text[:1] in _BULLETS and len(text) > 2 and text[1:2] in (" ", "\t"):
        rest = _tidy([{**spans[0], "s": spans[0]["s"][1:]}] + spans[1:])
        return {"t": "li", "marker": text[0], "spans": rest}
    if len(text) <= 200 and not text.endswith((",", ";")):
        if _PART.match(text) and len(text) < 60:
            return {"t": "h", "level": 0, "text": text}
        m = _ITEM.match(text)
        if m and len(text) < 180 and (_share(spans, "b") > 0.5 or text.isupper() or len(text) < 100):
            return {"t": "h", "level": 1, "text": text, "item": m.group(1).upper()}
        if _share(spans, "b") > 0.9 and len(text) < 160:
            return {"t": "h", "level": 2 if (text.isupper() or size >= 11) else 3, "text": text}
        if _share(spans, "i") > 0.9 and len(text) < 120 and not text.endswith("."):
            return {"t": "h", "level": 3, "text": text, "italic": 1}
    return {"t": "p", "spans": spans}


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

def _cell_text(c: dict) -> str:
    return _clean(_text(c["spans"]))


def _is_value(s: str) -> bool:
    return bool(_NUM.match(s) or _DASH.match(s)) and s not in _SYMBOL


def _grid(rows: list[dict]) -> list[list[tuple[int, int, dict]]]:
    """Each row as [(start_col, end_col, cell)] with colspans expanded."""
    out = []
    for r in rows:
        col, cells = 0, []
        for c in r["cells"]:
            cells.append((col, col + c["span"] - 1, c))
            col += c["span"]
        out.append(cells)
    return out


def _table_blocks(t: dict) -> list[dict]:
    rows = [r for r in t["rows"] if any(_cell_text(c) for c in r["cells"])]
    if not rows:
        return []
    texts = [[_cell_text(c) for c in r["cells"] if _cell_text(c) not in ("", *_SYMBOL)] for r in rows]
    cells = [c for row in texts for c in row]
    if not cells:
        return []
    flat = " ".join(cells)

    # Layout wrappers: one row / one real cell -> paragraph(s).
    if len(rows) == 1 and len(texts[0]) == 1:
        spans = next(c["spans"] for c in rows[0]["cells"] if _cell_text(c))
        return [_para(spans, 0)]

    # Bullets encoded as a 2-cell table: "•" | text.
    def bullet_row(r: dict) -> dict | None:
        real = [c for c in r["cells"] if _cell_text(c)]
        if len(real) == 2 and len(_cell_text(real[0])) <= 3 and _cell_text(real[0])[:1] in _BULLETS | set("0123456789(abcdefghijklmnopqrstuvwxyz"):
            m = _cell_text(real[0])
            if m[:1] in _BULLETS or re.match(r"^\(?\w{1,2}[.)]$", m):
                return {"t": "li", "marker": m, "spans": real[1]["spans"]}
        return None

    lis = [bullet_row(r) for r in rows]
    if all(lis):
        return lis  # type: ignore[return-value]

    if any(ch in flat for ch in "☐☒☑¨þý"):
        return [_text_table(rows, "cover")]
    if len(rows) >= 5 and sum(bool(_ITEM.match(t[0])) for t in texts if t) >= 4:
        return [_text_table(rows, "toc")]
    if re.search(r"/s/", flat):
        return [_text_table(rows, "signature")]
    if len(rows) > 6 and re.search(r"exhibit", " ".join(texts[0]), re.I) or (
        len(rows) > 8 and sum(bool(re.match(r"^\d{1,3}(\.\d{1,3})+[a-z*]?$", t[0])) for t in texts if t) > len(rows) / 2
    ):
        return [_text_table(rows, "exhibits")]

    vals = sum(_is_value(c) for c in cells)
    if vals / len(cells) >= 0.3 and max(len(t) for t in texts) >= 2:
        num = _num_table(rows)
        if num:
            return [num]
    return [_text_table(rows, "text")]


def _text_table(rows: list[dict], kind: str) -> dict:
    grid = _grid(rows)
    used = sorted({s for g in grid for s, _, c in g if _cell_text(c)})
    out = []
    for g in grid:
        line = []
        for col in used:
            hit = next((c for s, _, c in g if s == col), None)
            line.append(_cell_text(hit) if hit else "")
        if any(line):
            out.append(line)
    # Drop columns that ended up empty everywhere.
    keep = [i for i in range(len(used)) if any(r[i] for r in out)]
    return {"t": "table", "kind": kind, "rows": [[r[i] for i in keep] for r in out]}


def _num_table(rows: list[dict]) -> dict | None:
    """Financial grid: label column + value columns.

    EDGAR tables split each value over spacer, "$", number and ")" cells,
    so value columns are keyed by the END column of the cells holding a
    number; symbol cells fold into their neighbour and header cells map to
    the value columns they cover."""
    grid = _grid(rows)
    is_val = [[_is_value(_cell_text(c)) for _, _, c in g] for g in grid]
    first_body = next((i for i, v in enumerate(is_val) if any(v)), None)
    if first_body is None:
        return None
    # A header row is one before the first value row; year rows (2025 2024)
    # look numeric, so a row of only 4-digit years also counts as header.
    yearish = re.compile(r"^(19|20)\d\d$")
    while first_body < len(grid) and all(
        yearish.match(_cell_text(c)) for _, _, c in grid[first_body] if _cell_text(c) and _is_value(_cell_text(c))
    ) and not any(
        _cell_text(c) and not _is_value(_cell_text(c)) and s == 0 and not _UNITS.search(_cell_text(c))
        for s, _, c in grid[first_body]
    ):
        first_body += 1
    if first_body >= len(grid):
        return None

    ends = Counter()
    for g, v in zip(grid[first_body:], is_val[first_body:]):
        for (s, e, _c), isv in zip(g, v):
            if isv and s > 0:
                ends[e] += 1
    # A stray number in a label-side cell (footnote mark, a year in a
    # label) would add a phantom column; keep columns that carry a real
    # share of the values. Off-column values still land via col_for().
    top = max(ends.values(), default=0)
    data_cols = sorted(e for e, n in ends.items() if n >= max(1, top * 0.15))
    if not data_cols:
        return None
    label_end = data_cols[0]  # anything starting before the first value column is label

    def col_for(s: int, e: int) -> int | None:
        inside = [d for d in data_cols if s <= d <= e]
        if inside:
            return data_cols.index(inside[-1])
        after = [d for d in data_cols if d >= e]
        return data_cols.index(after[0]) if after else None

    units = None
    header: list[list[dict]] = []
    for g in grid[:first_body]:
        line: list[dict] = []
        label_txt = []
        for s, e, c in g:
            txt = _cell_text(c)
            if not txt or txt in _SYMBOL:
                continue
            m = _UNITS.search(txt)
            if m and not units:
                units = m.group(1)
                txt = _clean(txt[: m.start()] + txt[m.end():]).strip("() ")
                if not txt:
                    continue
            if s < label_end and e < label_end:
                label_txt.append(txt)
                continue
            covered = [i for i, d in enumerate(data_cols) if s <= d <= e]
            if not covered:
                ci = col_for(s, e)
                if ci is None:
                    continue
                covered = [ci]
            line.append({"s": txt, "c": covered[0] + 1, "span": len(covered)})
        if line or label_txt:
            # Merge cells landing on the same column.
            merged: dict[int, dict] = {}
            for cell in line:
                if cell["c"] in merged:
                    merged[cell["c"]]["s"] += " " + cell["s"]
                else:
                    merged[cell["c"]] = cell
            cells_ = sorted(merged.values(), key=lambda x: x["c"])
            # A year header drawn slightly left of its value column lands in
            # the label area: "2025 | 2024" with 2025 at col 0. Move it right.
            if len(label_txt) == 1 and yearish.match(label_txt[0]) and all(c["span"] == 1 for c in cells_):
                taken = {c["c"] for c in cells_}
                if 1 not in taken:
                    cells_.insert(0, {"s": label_txt.pop(), "c": 1, "span": 1})
                elif len(cells_) + 1 == len(data_cols):
                    cells_ = [{"s": t, "c": i + 1, "span": 1} for i, t in enumerate([label_txt.pop()] + [c["s"] for c in cells_])]
            header.append(([{"s": " ".join(label_txt), "c": 0, "span": 1}] if label_txt else []) + cells_)

    body: list[dict[str, Any]] = []
    indents: list[float] = []
    for r, g in zip(rows[first_body:], grid[first_body:]):
        label_parts, label_bold, label_indent = [], False, None
        values: list[dict | None] = [None] * len(data_cols)
        cur = None
        top = r["top"]
        bot = r["bot"]
        for s, e, c in g:
            txt = _cell_text(c)
            if s > 0 and s >= label_end or e >= label_end and _is_value(txt):
                top = top or c["top"]
                bot = bot or c["bot"]
            if not txt:
                continue
            if txt in ("$", "€", "£", "¥"):
                cur = txt
                continue
            if txt in (")", "%", "%)"):
                ci = col_for(s, e)
                tgt = values[ci - 1] if ci and values[ci - 1] else None
                tgt = tgt or next((v for v in reversed(values) if v), None)
                if tgt and not tgt["s"].endswith(txt):
                    tgt["s"] += txt
                continue
            if e < label_end:
                label_parts.append(txt)
                label_bold = label_bold or _share(c["spans"], "b") > 0.8
                if label_indent is None:
                    label_indent = c["indent"]
                continue
            ci = col_for(s, e)
            if ci is None:
                continue
            v: dict = {"s": txt.replace("$", "").replace("€", "").replace("£", "").strip()}
            if cur:
                v["cur"] = cur
                cur = None
            x = next((sp["x"] for sp in c["spans"] if sp.get("x")), None)
            if x:
                v["x"] = x
            if "(" in txt and ")" in txt or (txt.startswith("(") and _is_value(txt)):
                v["neg"] = 1
            prev = values[ci]
            if prev:
                prev["s"] += " " + v["s"]
            else:
                values[ci] = v
        if not label_parts and not any(values):
            continue
        indent = label_indent or 0.0
        indents.append(indent)
        row: dict = {"label": " ".join(label_parts), "v": [v or {"s": ""} for v in values], "_ind": indent}
        if label_bold:
            row["b"] = 1
        if top:
            row["rule"] = top
        if bot:
            row["rule_below"] = bot
        if not any(v and v["s"] for v in values):
            row["section"] = 1
        body.append(row)
    if not body:
        return None
    # An index of statements with page numbers ("Balance Sheets ... 64").
    if len(data_cols) == 1 and all(re.fullmatch(r"[A-Z]?-?\d{1,3}", r["v"][0]["s"] or "0") for r in body):
        return {"t": "table", "kind": "toc", "rows": [[r["label"], r["v"][0]["s"]] for r in body]}
    levels = sorted({round(i) for i in indents})
    for row in body:
        lvl = levels.index(round(row.pop("_ind")))
        if lvl:
            row["indent"] = min(lvl, 4)
    out = {"t": "table", "kind": "num", "cols": len(data_cols), "header": header, "rows": body}
    if units:
        out["units"] = units
    return out


# --------------------------------------------------------------------------
# Document
# --------------------------------------------------------------------------

def _post(blocks: list[dict]) -> list[dict]:
    """Drop running headers/footers, attach footnotes to tables, find units
    stated in the paragraph above a table."""
    counts = Counter(_text(b["spans"]) for b in blocks if b["t"] == "p" and len(_text(b["spans"])) < 90)
    counts.update(b["text"] for b in blocks if b["t"] == "h" and b.get("level", 9) >= 2)
    # Press releases print "Title / date / Page 2 of 9" atop each page: the
    # two short lines before a "Page N of M" line that recur are a running header.
    running: set[str] = set()
    for i, b in enumerate(blocks):
        if _PAGE_OF.match(_block_line(b)):
            for prev in blocks[max(0, i - 2):i]:
                t = _block_line(prev)
                if t and counts[t] >= 2:
                    running.add(t)
    out: list[dict] = []
    for b in blocks:
        line = _block_line(b)
        if line and (_PAGE_OF.match(line) or line in running or _SGML_STUB.match(line)):
            continue
        if b["t"] == "p":
            txt = _text(b["spans"])
            if len(txt) < 90 and counts[txt] > 8 or _PAGE_NO.match(txt) and len(txt) < 6:
                continue
            if txt.lower() in ("table of contents", "index"):
                continue
            last_tbl = next((o for o in reversed(out[-4:]) if o["t"] == "table"), None)
            if last_tbl and _FOOTNOTE.match(txt) and out and out[-1] is last_tbl:
                last_tbl.setdefault("notes", []).append(txt)
                continue
            m = _UNITS.search(txt)
            if m and len(txt) < 120:
                b["_units"] = m.group(1)
        if b["t"] == "h" and b.get("level", 0) >= 2 and counts[b["text"]] > 8:
            continue
        if b["t"] == "table" and b.get("kind") == "num" and "units" not in b and out:
            prev = out[-1]
            if prev.get("_units"):
                b["units"] = prev["_units"]
        out.append(b)
    for b in out:
        b.pop("_units", None)
    # Collapse runs of page markers.
    final: list[dict] = []
    for b in out:
        if b["t"] == "page" and final and final[-1]["t"] == "page":
            final[-1].update({k: v for k, v in b.items() if v})
            continue
        final.append(b)
    while final and final[0]["t"] == "page":
        final.pop(0)
    return _join_across_pages(final)


def _join_across_pages(blocks: list[dict]) -> list[dict]:
    """A paragraph cut by a page break continues in lowercase on the next
    page: glue it back and keep the page marker after the joined paragraph."""
    out: list[dict] = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if (
            b["t"] == "page" and i + 1 < len(blocks) and out
            and out[-1]["t"] in ("p", "li") and blocks[i + 1]["t"] == "p"
        ):
            nxt = blocks[i + 1]
            head, tail = _text(out[-1]["spans"]).rstrip(), _text(nxt["spans"]).lstrip()
            if tail[:1].islower() and head[-1:] not in ".:!?\u201d\"":
                out[-1]["spans"] = _tidy(out[-1]["spans"] + [{"s": " "}] + nxt["spans"])
                out.append(b)
                i += 2
                continue
        out.append(b)
        i += 1
    return out


def _block_line(b: dict) -> str:
    if b["t"] == "h":
        return b["text"]
    if b["t"] == "p":
        return _text(b["spans"])
    return ""


def parse(html: str, base_url: str = "") -> list[dict]:
    p = _Parser(base_url)
    p.feed(html)
    p.close()
    return _post(p.blocks)


def outline(blocks: list[dict]) -> list[dict]:
    """[{i, level, text}] for headings: the reader's left pane."""
    return [{"i": i, "level": b["level"], "text": b["text"]} for i, b in enumerate(blocks) if b["t"] == "h"]


def stats(blocks: list[dict]) -> dict:
    c = Counter(b["t"] if b["t"] != "table" else f"table_{b['kind']}" for b in blocks)
    words = sum(len(_text(b["spans"]).split()) for b in blocks if b["t"] in ("p", "li"))
    tagged = sum(1 for b in blocks if b.get("kind") == "num" for r in b["rows"] for v in r["v"] if v.get("x"))
    return {"words": words, "blocks": len(blocks), **dict(c), "xbrl_cells": tagged}


def document(html: str, meta: dict) -> dict:
    blocks = parse(html, meta.get("url", ""))
    return {"v": PARSER_VERSION, **meta, "stats": stats(blocks), "outline": outline(blocks), "blocks": blocks}


# --------------------------------------------------------------------------
# Cache / fetch
# --------------------------------------------------------------------------

def _dir(name: str = "") -> Path:
    from sources import universe

    d = universe.data_dir("filing_blocks")
    if name:
        d = d / name
        d.mkdir(parents=True, exist_ok=True)
    return d


def _raw(meta: dict) -> str:
    path = _dir("raw") / f"{meta['accn']}.htm.gz"
    if path.exists():
        return gzip.decompress(path.read_bytes()).decode("utf-8", errors="replace")
    from sources import sec_http

    r = sec_http.get(meta["url"])
    r.raise_for_status()
    r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else (r.apparent_encoding or "utf-8")
    html = r.text
    path.write_bytes(gzip.compress(html.encode("utf-8")))
    return html


def latest(ticker: str, form: str | None = None) -> dict | None:
    """Newest primary document for ticker (10-K/20-F by default) from the
    filing_text index."""
    import duckdb
    from sources import universe

    src = universe.data_dir("filing_text") / "filings.parquet"
    q = f"SELECT ticker, cik, accn, form, filed::VARCHAR, primary_doc FROM '{src}' WHERE ticker = ?"
    args: list = [ticker.upper()]
    if form:
        q += " AND form = ?"
        args.append(form)
    row = duckdb.execute(q + " ORDER BY filed DESC LIMIT 1", args).fetchone()
    if not row:
        return None
    t, cik, accn, f, filed, doc = row
    return {
        "ticker": t, "cik": int(cik), "accn": accn, "form": f, "filed": filed, "doc": doc,
        "url": f"{ARCHIVES}/{int(cik)}/{accn.replace('-', '')}/{doc}",
    }


def build(meta: dict, force: bool = False) -> Path:
    out = _dir() / f"{meta['accn']}.json.gz"
    if out.exists() and not force:
        cur = json.loads(gzip.decompress(out.read_bytes()))
        if cur.get("v") == PARSER_VERSION:
            return out
    doc = document(_raw(meta), meta)
    out.write_bytes(gzip.compress(json.dumps(doc, separators=(",", ":")).encode()))
    return out


def load(accn: str) -> dict:
    return json.loads(gzip.decompress((_dir() / f"{accn}.json.gz").read_bytes()))


def _show(doc: dict) -> None:
    print(f"{doc.get('ticker', '')} {doc.get('form', '')} {doc.get('filed', '')} {doc.get('accn', '')}")
    print(json.dumps(doc["stats"]))
    for h in doc["outline"][:80]:
        print("  " * h["level"] + h["text"][:100])


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "parse":
        src = Path(rest[0])
        html = (gzip.decompress(src.read_bytes()).decode("utf-8", "replace") if src.suffix == ".gz" else src.read_text(errors="replace"))
        doc = document(html, {"file": src.name})
        if "--out" in rest:
            Path(rest[rest.index("--out") + 1]).write_text(json.dumps(doc, indent=1))
        _show(doc)
        return 0
    if cmd in ("fetch", "show"):
        form = rest[rest.index("--form") + 1] if "--form" in rest else None
        key = rest[0]
        if re.match(r"^\d{10}-\d{2}-\d{6}$", key) and cmd == "show":
            _show(load(key))
            return 0
        meta = latest(key, form)
        if not meta:
            print(f"no annual report indexed for {key}", file=sys.stderr)
            return 1
        path = build(meta, force="--force" in rest)
        _show(load(meta["accn"]))
        print(path)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
