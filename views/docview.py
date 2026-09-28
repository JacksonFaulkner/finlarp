"""Fetch a source document once and turn it into something nvim can show,
for the "where did this number come from" jump (dossier `v`, search hits).

    SEC HTML (10-K/Q, 8-K, EX-99.1, index pages) -> markdown: tables rebuilt
        from cell text (SEC layout tables are mostly spacer cells, which
        pandoc renders as unreadable grids), prose via pandoc, <img> files
        downloaded next to it so snacks.image draws them inline.
    PDF -> kept as-is for snacks.image, plus `pdftotext -layout` text for
        finding the quote.
    Images / .txt / .md -> kept as-is.
    Google Patents -> the page as markdown (abstract, claims, figures).
    Yahoo profile / JS-only pages -> markdown built from what we pulled
        locally (the page itself needs a browser).

Cache: docs/<key>/ keyed by accession (SEC) or URL hash, so a second open
is instant and works offline. The `#:~:text=` fragment that dossier links
carry doubles as the quote to jump to.

    python views/docview.py URL [--quote TEXT] [--json]
    -> {"path", "kind": md|pdf|image|text, "text_path", "line", "title", "url"}
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import textwrap
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests

from sources import keys, sec_http, universe

DOCS = universe.data_dir("docs")
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg")


# ---- URL handling ----------------------------------------------------------

def split_fragment(url: str) -> tuple[str, str | None]:
    """'...#:~:text=Net%20revenue' -> (url, 'Net revenue')."""
    if "#:~:text=" in url:
        base, frag = url.split("#:~:text=", 1)
        return base, unquote(frag.split("&")[0].split(",")[0])
    return url.split("#")[0], None


def canonical(url: str) -> str:
    """Inline-XBRL viewer links point at the plain Archives document."""
    m = re.match(r"https?://www\.sec\.gov/ix\?doc=(/Archives/.+)", url)
    return f"https://www.sec.gov{m.group(1)}" if m else url


def cache_dir(url: str) -> Path:
    m = re.search(r"/Archives/edgar/data/(\d+)/(\d{18})/", url)
    key = f"sec_{int(m.group(1))}_{m.group(2)}" if m else "u_" + hashlib.sha1(url.encode()).hexdigest()[:12]
    d = DOCS / key
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch(url: str) -> requests.Response:
    if "sec.gov" in urlparse(url).netloc:
        r = sec_http.get(url)   # SEC UA + shared throttle
    else:
        r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=60)
    r.raise_for_status()
    return r


# ---- SEC HTML -> markdown ---------------------------------------------------

class _Table(HTMLParser):
    """Rows of (text, colspan)."""

    def __init__(self):
        super().__init__()
        self.rows: list[list[tuple[str, int]]] = []
        self.row: list[tuple[str, int]] | None = None
        self.cell: list[str] | None = None
        self.span = 1

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
            try:
                self.span = max(1, int(dict(attrs).get("colspan") or 1))
            except ValueError:
                self.span = 1
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append((" ".join("".join(self.cell).replace("\xa0", " ").split()), self.span))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


_PRE = ("$", "(", "$(", "($")
_POST = (")", "%", ")%", "%)")
_NUM = re.compile(r"^[$(\-−–—]*\s*[\d.,]+|^[—–-]$|^\(?[\d.,]+\)?\s*(%|bps|x)\)?$")


LABEL_W = 48      # label column wraps past this
TEXT_W = 40       # other text columns (descriptions, titles)
HEAD_W = 12       # headers wrap to their column, but no narrower than this
_PERIODS = [(r"\bthree months\b", "3M"), (r"\bsix months\b", "6M"), (r"\bnine months\b", "9M"),
            (r"\btwelve months\b", "12M"), (r"\b(fiscal )?years?\b", "FY"), (r"\bquarters?\b", "Q"),
            (r"\s*\bend(ed|ing)\b", ""), (r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?", r"\1")]


def _short_period(h: str) -> str:
    """'Three Months Ended August 31, 2026' -> '3M Aug 31, 2026': statement
    headers are what makes these tables too wide to read."""
    for pat, rep in _PERIODS:
        h = re.sub(pat, rep, h, flags=re.I)
    return " ".join(h.split())


def _place(rows: list[list[tuple[str, int]]]) -> list[list[tuple[str, int, int]]]:
    """Cells -> (text, first col, last col) on the expanded grid, with the
    '$' / '(' / ')' / '%' spacer cells glued onto their numbers."""
    out = []
    for row in rows:
        cells, col, pre = [], 0, ""
        for text, span in row:
            a, col = col, col + span
            if text in _PRE:
                pre += text
                continue
            if text in _POST and cells:
                t, x, y = cells[-1]
                cells[-1] = (t + text, x, y)
                continue
            if text:
                cells.append((pre + text, a, col - 1))
                pre = ""
        out.append(cells)
    return out


def _table_md(fragment: str) -> str:
    """SEC layout table -> aligned markdown table. Workiva-style tables put
    every number in a 1-wide cell between spacer / '$' / ')' cells, with
    headers and labels spanning several; so: find the columns that carry
    1-wide text, snap every cell onto one of them, stack multi-row headers
    into one, and lift title rows ('GAAP', '($ in millions)') above it."""
    p = _Table()
    p.feed(fragment)
    rows = [r for r in _place(p.rows) if r]
    if not rows:
        return ""
    if len(rows) == 1 and len(rows[0]) <= 2:          # layout table around a bullet/heading
        return "\n\n" + " ".join(t for t, _, _ in rows[0]) + "\n\n"

    cols = sorted({a for r in rows for _, a, b in r if a == b})
    for r in rows:                                     # spanning cells with no 1-wide column under them
        for _, a, b in r:
            if not any(a <= c <= b for c in cols):
                cols.append(a)
                cols.sort()
    grid: list[list[str]] = []
    spans: list[list[tuple[str, list[int]]]] = []
    for r in rows:
        line = [""] * len(cols)
        sp = []
        for t, a, b in r:
            under = [i for i, c in enumerate(cols) if a <= c <= b]
            k = under[-1] if _NUM.match(t) else under[0]   # numbers sit at the right of their span
            line[k] = (line[k] + " " + t).strip()
            sp.append((t, under))
        grid.append(line)
        spans.append(sp)
    data = [g for g in grid if any(_NUM.match(c) for c in g[1:])] or grid
    keep = [j for j in range(len(cols)) if j == 0 or any(g[j] for g in data)]   # header-only columns are spacers
    for sp in spans:                                   # re-home text that sat on a dropped column
        for t, under in sp:
            if under and not any(j in keep for j in under):
                keep.append(under[0])
    keep.sort()
    grid = [[g[j] for j in keep] for g in grid]
    spans = [[(t, [keep.index(j) for j in u if j in keep]) for t, u in sp] for sp in spans]
    w = len(keep)

    is_data = [any(_NUM.match(c) for c in g[1:]) for g in grid]
    if w <= 2 and not any(is_data):                    # footnotes / bullets: "(1) | text"
        return "\n\n" + "\n\n".join((" " if len(g[0]) <= 4 else " · ").join(c for c in g if c)
                                     for g in grid) + "\n\n"
    first = is_data.index(True) if any(is_data) else 1
    captions: list[str] = []
    header = [""] * w
    body_pre: list[list[str]] = []
    for g, sp in zip(grid[:first], spans[:first]):
        filled = [c for c in g if c]
        title = len(filled) == 1 and (g[0] or len(sp[0][1]) == w)   # in the label column or full width
        if title and not any(header):
            captions.append(filled[0])
        elif title:                                    # section row under the headers ("ASSETS")
            body_pre.append(g)
        else:
            for t, under in sp:                        # a spanning header labels every column under it
                for j in under:
                    header[j] = (header[j] + " " + t).strip()
    body = body_pre + grid[first:]
    if not any(header) and body:
        header, body = body[0], body[1:]
    header = [_short_period(h) for h in header]
    if len(header[0]) > LABEL_W:                       # a sentence over the label column is a title
        captions.append(header[0])
        header[0] = ""

    nonempty = lambda j: [r[j] for r in body if r[j]]
    numeric = [j > 0 and sum(bool(_NUM.match(c)) for c in nonempty(j)) * 2 >= max(1, len(nonempty(j)))
               for j in range(w)]
    cap_w = [LABEL_W if j == 0 else TEXT_W for j in range(w)]

    wrapped: list[list[str]] = []                      # long text continues on rows below; numbers sit on the last line
    for r in body:
        parts = [[c] if numeric[j] else (textwrap.wrap(c, cap_w[j]) or [""]) for j, c in enumerate(r)]
        h = max(len(x) for x in parts)
        for i in range(h):
            wrapped.append([(x[i - h + len(x)] if i >= h - len(x) else "") if numeric[j] else (x[i] if i < len(x) else "")
                            for j, x in enumerate(parts)])
    body = wrapped

    widths = [max([3, *(len(r[j]) for r in body)]) for j in range(w)]
    head = [textwrap.wrap(c, max(widths[j], HEAD_W), break_long_words=False) or [""] for j, c in enumerate(header)]
    widths = [max(widths[j], *(len(x) for x in head[j])) for j in range(w)]
    hh = max(len(x) for x in head)
    head_rows = [[x[i - hh + len(x)] if i >= hh - len(x) else "" for x in head] for i in range(hh)]

    esc = lambda c: c.replace("|", "\\|")
    fmt = lambda r: "| " + " | ".join(
        esc(c).rjust(widths[j]) if numeric[j] else esc(c).ljust(widths[j]) for j, c in enumerate(r)) + " |"
    # Header lines stack bottom-aligned; only the last is the GFM header row,
    # the ones above read as its continuation (as in a printed statement).
    lines = [fmt(r) for r in head_rows]
    lines.append("|" + "|".join("-" * (widths[j] + 1) + ":" if numeric[j] else "-" * (widths[j] + 2)
                                for j in range(w)) + "|")
    lines += [fmt(r) for r in body]
    cap = ""
    if captions:
        cap = "**" + captions[0] + "**" + "".join("  \n*" + c + "*" for c in captions[1:]) + "\n\n"
    return "\n\n" + cap + "\n".join(lines) + "\n\n"


def html_to_md(html: str) -> str:
    html = re.sub(r"(?is)<ix:header>.*?</ix:header>", "", html)          # hidden inline-XBRL facts
    html = re.sub(r'(?is)<div[^>]*display:\s*none[^>]*>.*?</div>', "", html)
    tables: list[str] = []

    def sub(m):
        tables.append(_table_md(m.group(0)))
        return f"<p>@@TABLE{len(tables) - 1}@@</p>"

    body = re.sub(r"(?is)<table.*?</table>", sub, html)
    md = subprocess.run(["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
                        input=body, capture_output=True, text=True, check=True).stdout
    md = re.sub(r"@@TABLE(\d+)@@", lambda m: tables[int(m.group(1))], md)
    md = re.sub(r"^\\$", "", md, flags=re.M)                             # pandoc's hard-break backslashes
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def localize_images(md: str, base_url: str, d: Path) -> str:
    """Download every ![](src) next to the markdown and point at the local copy."""
    def sub(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith("data:"):
            return m.group(0)
        name = re.sub(r"[^\w.\-]", "_", Path(urlparse(src).path).name) or "img"
        local = d / name
        if not local.exists():
            try:
                local.write_bytes(fetch(urljoin(base_url, src)).content)
            except Exception:
                return f"*[image unavailable: {src}]*"
        return f"![{alt}]({name})"
    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", sub, md)


# ---- other sources ----------------------------------------------------------

def index_docs(html: str, url: str) -> list[str]:
    """SEC '-index.htm' pages are navigation; their document table lists the
    filing itself first (for Form 4 / 13F the xsl-rendered view), then exhibits."""
    out = []
    for href in re.findall(r'href="(/Archives/edgar/data/\d+/\d+/[^"]+)"', html):
        if not href.endswith(("-index.htm", "-index.html", ".txt", ".xsd", ".zip")) and not re.search(r"_(cal|def|lab|pre)\.xml$", href):
            u = urljoin(url, href)
            if u not in out:
                out.append(u)
    return out


USPTO_PDF = "https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{}"
ODP_DOCS = "https://api.uspto.gov/api/v1/patent/applications/{}/documents"


def _odp_drawings(app: str, d: Path) -> Path | None:
    """Latest 'DRW' (drawings) PDF from the ODP file wrapper for an application."""
    try:
        key = keys.require("USPTO_API_KEY")
        r = requests.get(ODP_DOCS.format(app), headers={"X-API-Key": key}, timeout=60)
        r.raise_for_status()
        drw = [x for x in r.json().get("documentBag", []) if x.get("documentCode") == "DRW"]
        if not drw:
            return None
        doc = max(drw, key=lambda x: x.get("officialDate") or "")
        url = next(o["downloadUrl"] for o in doc["downloadOptionBag"] if o.get("mimeTypeIdentifier") == "PDF")
        pdf = d / f"drawings-{app}.pdf"
        dl = requests.get(url, headers={"X-API-Key": key}, timeout=120)
        if dl.ok and dl.content[:4] == b"%PDF":
            pdf.write_bytes(dl.content)
            return pdf
    except (requests.RequestException, StopIteration, SystemExit, KeyError):
        pass
    return None


def patent_drawings(html: str, url: str, d: Path) -> tuple[str, Path | None]:
    """Drawing sheets as inline PNGs. Google's figure images 403 outside a
    browser and the USPTO print PDF is scanned (no text to find sheet pages),
    so the drawings come from the ODP file wrapper's DRW document, which is
    exactly the sheets. The full print PDF is kept alongside for reading."""
    m = re.search(r"/patent/[A-Z]{2}(\w+?)(?:[A-Z]\d)?(?:/|$)", url)
    num = m.group(1) if m else None
    a = re.search(r"US(\d{2})/(\d{3}),(\d{3})", html)          # application number, e.g. US17/956,478
    app = "".join(a.groups()) if a else None
    full = d / f"US{num}.pdf" if num else None
    if full and not full.exists():
        try:
            r = requests.get(USPTO_PDF.format(num), headers={"User-Agent": BROWSER_UA}, timeout=60)
            if r.ok and r.content[:4] == b"%PDF":
                full.write_bytes(r.content)
        except requests.RequestException:
            pass
    drw = next(iter(d.glob("drawings-*.pdf")), None) or (_odp_drawings(app, d) if app else None)
    if drw and not list(d.glob("sheet-*.png")):
        subprocess.run(["pdftoppm", "-png", "-r", "80", str(drw), str(d / "sheet")], check=False)
    pngs = sorted(d.glob("sheet-*.png"))
    if not pngs:
        return "", full if full and full.exists() else None
    body = "\n\n".join(f"![sheet {i + 1}]({p.name})" for i, p in enumerate(pngs))
    note = f"Full patent PDF: {full.name}\n" if full and full.exists() else ""
    return f"\n\n## Drawings ({len(pngs)} sheets, USPTO file wrapper)\n\n{body}\n\n{note}", full


def yahoo_md(url: str) -> str | None:
    m = re.search(r"finance\.yahoo\.com/quote/([^/]+)/profile", url)
    prof = universe.DATA_ROOT / "profiles" / "profiles.parquet"
    if not m or not prof.exists():
        return None
    import duckdb
    t = unquote(m.group(1))
    con = duckdb.connect()
    r = con.execute(f"SELECT * FROM '{prof}' WHERE ticker = ?", [t]).fetchone()
    if not r:
        return None
    p = dict(zip([c[0] for c in con.description], r))
    officers = "\n".join(f"- {o.get('title')}: {o.get('name')}" for o in json.loads(p.get("officers") or "[]"))
    return (f"# {p['long_name']} ({t})\n\n*Yahoo Finance profile as pulled by sources/yahoo_profile.py — "
            f"live page: {url}*\n\n| field | value |\n|---|---|\n| Sector | {p['sector']} |\n| Industry | {p['industry']} |\n"
            f"| Country | {p['country']} |\n| Employees | {p['employees']} |\n| Website | {p['website']} |\n\n"
            f"## Business summary\n\n{p['summary']}\n\n## Officers\n\n{officers}\n")


# ---- quote -> line -----------------------------------------------------------

def _norm(s: str) -> str:
    s = s.replace("\\", "").replace("’", "'").replace("“", '"').replace("”", '"').replace("\xa0", " ")
    return " ".join(re.sub(r"[*_`•]", " ", s).split()).lower()


def find_line(path: Path, quote: str | None) -> int | None:
    """1-based line of the first line containing the quote's opening words;
    retries with fewer words since markup can split long quotes."""
    if not quote or not path.exists():
        return None
    lines = [_norm(l) for l in path.read_text(errors="ignore").splitlines()]
    words = _norm(quote).split()
    for n in (8, 6, 4, 3):
        needle = " ".join(words[:n])
        if len(needle) < 8:
            break
        for i, l in enumerate(lines):
            if needle in l:
                return i + 1
    return None


# ---- main --------------------------------------------------------------------

def open_doc(url: str, quote: str | None = None) -> dict:
    url, frag_quote = split_fragment(url)
    quote = quote or frag_quote
    url = canonical(url)
    d = cache_dir(url)
    name = re.sub(r"[^\w.\-]", "_", Path(urlparse(url).path).name) or "index"
    out = {"url": url, "title": name, "text_path": None}

    if (md := yahoo_md(url)) is not None:
        path = d / "profile.md"
        path.write_text(md)
        return out | {"path": str(path), "kind": "md", "line": find_line(path, quote)}

    ext = Path(name).suffix.lower()
    raw = d / name
    # an extensionless URL is saved under name + the Content-Type's extension,
    # so look for that too or it's re-downloaded on every open
    for alt, alt_ext in ((d / (name + ".pdf"), ".pdf"), (d / (name + ".html"), ".html")):
        if not raw.exists() and alt.exists():
            raw, ext = alt, alt_ext
    if not raw.exists():
        r = fetch(url)
        ctype = r.headers.get("Content-Type", "")
        if "pdf" in ctype and ext != ".pdf":
            raw = d / (name + ".pdf")
            ext = ".pdf"
        elif "html" in ctype and ext not in (".htm", ".html"):
            raw = d / (name + ".html")
            ext = ".html"
        part = raw.with_name(raw.name + ".part")  # a killed download must not look cached
        part.write_bytes(r.content)
        part.replace(raw)
    elif ext not in (".pdf", ".txt", ".md", *IMG_EXT):
        ext = ext or ".html"

    if ext == ".pdf":
        txt = raw.with_suffix(".txt")
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(raw), str(txt)], check=False)
        return out | {"path": str(raw), "kind": "pdf", "text_path": str(txt), "line": find_line(txt, quote)}
    if ext in IMG_EXT:
        return out | {"path": str(raw), "kind": "image", "line": None}
    if ext in (".txt", ".md"):
        return out | {"path": str(raw), "kind": "text" if ext == ".txt" else "md", "line": find_line(raw, quote)}

    if re.search(r"-index\.html?$", name):
        docs = index_docs(raw.read_text(errors="ignore"), url)
        first = None
        # With a quote, the right document is whichever contains it (an
        # earnings quote lives in EX-99.1, not the 8-K cover); else the filing itself.
        for u in docs[:8] if quote else docs[:1]:
            try:
                res = open_doc(u, quote) | {"index_url": url}
            except Exception:
                continue
            first = first or res
            if not quote or res.get("line"):
                return res
        if first:
            return first

    md_path = raw.with_suffix(".md")
    if not md_path.exists():
        html = raw.read_text(errors="ignore")
        m = re.search(r"(?is)<title>(.*?)</title>", html)
        md = html_to_md(html)
        if "patents.google.com" in url:
            drawings, _ = patent_drawings(html, url, d)
            md = drawings + md if drawings else md   # drawings first: they're what you came for
        md_path.write_text(localize_images(md, url, d))
        if m:
            (d / "title").write_text(" ".join(m.group(1).split()))
    title_f = d / "title"
    if title_f.exists():
        out["title"] = title_f.read_text().strip() or name
    pdfs = list(d.glob("US*.pdf"))
    if pdfs:
        out["pdf_path"] = str(pdfs[0])
    return out | {"path": str(md_path), "kind": "md", "line": find_line(md_path, quote)}


if __name__ == "__main__":
    args = sys.argv[1:]
    q = None
    if "--quote" in args:
        i = args.index("--quote")
        q = args[i + 1]
        del args[i:i + 2]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    res = open_doc(args[0], q)
    print(json.dumps(res) if as_json else f"{res['kind']} {res['path']} line={res['line']}")
