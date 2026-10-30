"""Dossier tab: Filings. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Latest annual report (filing_text): new risk factors (sentence diff vs prior
year), Item 1 business / Item 1 competition, Item 1A going-concern check,
Item 7 MD&A, Item 7A market risk, Item 1C cybersecurity, Exhibit 21
subsidiaries; plus 8-K item 5.02 officer changes from sec_events.

Not built (reported, not guessed):
  - full risk-factor list: section text is stored without emphasis, and the
    parser's headings (emphasised lines) cannot be recovered from it; a text
    heuristic over-counts about 2x against risk_factor_count.
  - executive officers: the business section has the heading on ~20% of
    filings and no fixed layout for the list.
  - supply chain / litigation: no reliable heading in the business section
    (~29% coverage); Item 3 is not parsed into filing_text.
"""
from __future__ import annotations

import re

from derive.dossier import D, Filings, _is_new, archive, derived, fragment, src
from sources import sec_events

# Exhibit 21 parser leaks headers, footnotes and bare jurisdictions (same filter as sources/patents.py).
_EX21_JUNK = re.compile(
    r"^(as of|at )|december \d|subsidiar|variable interest|wholly.owned|^vies?$|"
    r"^(united states|united kingdom|australia|belgium|brazil|canada|cayman islands|china|denmark|france|"
    r"germany|hong kong|india|ireland|israel|italy|japan|korea|mexico|netherlands|poland|singapore|spain|"
    r"sweden|switzerland|taiwan)$", re.I)
_GOING_CONCERN = re.compile(r"[^.\n]*substantial doubt[^.\n]*going concern[^.\n]*|[^.\n]*going concern[^.\n]*substantial doubt[^.\n]*", re.I)
_NEGATED = re.compile(r"\b(no|not|without|neither|nor)\b[^.\n]{0,60}substantial doubt", re.I)
_SENT_END = re.compile(r"[.!?][”\"]?(?=\s+[A-Z“\"(])")


def _doc(F: Filings, accn: str, name: str | None) -> str | None:
    """Document URL inside an accession, using the CIK that filed it (predecessors included)."""
    cik = (F.by_accn.get(accn) or (F.cik,))[0]
    return archive(cik, accn, name) if (cik and accn) else None


def _paras(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n") if p.strip()]


def _body(text: str) -> str | None:
    """First paragraph of 12+ words: skips item headings, run-in titles and the MD&A preamble."""
    return next((p for p in _paras(text) if len(p.split()) >= 12 and not p.startswith("•")
                 and "should be read in conjunction" not in p), None)


def _opening(p: str) -> str:
    m = _SENT_END.search(p)
    return p[:m.end()] if m else p


def _excerpt(p: str, limit: int = 600) -> str:
    if len(p) <= limit:
        return p
    cut = p[:limit]
    j = cut.rfind(". ")
    return (cut[:j + 1] if j > 200 else cut.rstrip()) + " …"


def _section_text(con, t: str, accn: str, section: str) -> str | None:
    r = con.execute(f"""SELECT text FROM '{D}/filing_text/sections.parquet'
                        WHERE ticker = ? AND accn = ? AND section = ? AND parse_ok LIMIT 1""", [t, accn, section]).fetchone()
    return r[0] if r and r[0] else None


def _text_block(F: Filings, accn: str, form: str, filed, name: str | None, label: str, para: str) -> dict:
    url = _doc(F, accn, name)
    return {"type": "text", "text": _excerpt(para),
            "src": src(f"{form} filed {filed} · {label}", fragment(url, _opening(para)))}


def _new_risks(con, t: str, F: Filings, form: str, filed, accn: str, risk_count, added, removed, ai, doc: str | None) -> list[dict]:
    kv = [{"label": "Risk sentences added / removed vs prior year", "value": f"{added} / {removed}",
           "new": _is_new(filed, 60), "src": derived("sentence diff of Item 1A", "sentences in this 1A not in prior-year 1A",
                                                       [src(f"{form} filed {filed}", doc)])},
          {"label": "AI mentions in annual report", "value": f"{ai}", "src": src(f"{form} filed {filed}", doc)}]
    if risk_count is not None:
        kv.append({"label": "Risk factors detected (Item 1A headings, parser count)", "value": f"{risk_count}",
                   "src": src(f"{form} filed {filed} · Item 1A", doc)})
    sents = con.execute(f"""
        SELECT sentence, novelty FROM '{D}/filing_text/risk_diff.parquet'
        WHERE ticker = ? AND accn = ? AND kind = 'added' ORDER BY novelty DESC NULLS LAST LIMIT 12""", [t, accn]).fetchall()
    rows = [{"cells": [s], "new": _is_new(filed, 60), "src": src(f"{form} {filed} · Item 1A", fragment(doc, s))}
            for s, _ in sents]
    return [{"type": "kv", "rows": kv},
            {"type": "table", "title": f"Most novel added sentences ({form} {filed})", "cols": ["sentence"], "rows": rows}]


def _going_concern(con, t: str, F: Filings, form: str, filed, accn: str, doc: str | None) -> tuple[dict | None, dict | None]:
    """(kv row, text block). Only the phrase pair 'substantial doubt' + 'going concern' in Item 1A or Item 7."""
    for sec in ("risk_factors", "mda"):
        txt = _section_text(con, t, accn, sec) or ""
        for m in _GOING_CONCERN.finditer(txt):
            sent = m.group(0).strip()
            if _NEGATED.search(sent):  # "no substantial doubt exists ..." is not a going-concern warning
                continue
            where = "Item 1A" if sec == "risk_factors" else "Item 7"
            return None, {"type": "text", "text": _excerpt(sent),
                          "src": src(f"{form} filed {filed} · {where}", fragment(doc, sent))}
    searched = src(f"{form} filed {filed} · Items 1A and 7 text", doc)
    row = {"label": "Going-concern doubt language (Items 1A, 7)", "value": "no doubt language found",
           "src": derived("phrase search", "regex 'substantial doubt' with 'going concern' in one sentence, "
                          "negated sentences ignored", [], searched)}
    return row, None


def _officer_changes(t: str, F: Filings) -> list[dict]:
    """8-K item 5.02 filings, last 365 days. 5.02 is high-tier in sec_events, so asking for medium and
    keeping item 5.02 gives the same rows as high alone."""
    evs = [e for e in sec_events.recent_events(t, 365, "medium") if e["item"] == "5.02"]
    return [{"cells": [str(e["filed"]), e["form"], e["label"]], "new": _is_new(e["filed"]),
             "src": src(f"{e['form']} {e['filed']} item 5.02", _doc(F, e["accn"], e.get("primary_doc")))}
            for e in evs]


def _subsidiaries(con, t: str, F: Filings, form: str, filed, accn: str, ex21: str | None) -> list[dict]:
    if not ex21:
        return []
    rows = con.execute(f"""SELECT subsidiary, jurisdiction FROM '{D}/filing_text/subsidiaries.parquet'
                           WHERE ticker = ? AND accn = ? ORDER BY subsidiary""", [t, accn]).fetchall()
    rows = [(s, j) for s, j in rows if s and not _EX21_JUNK.search(s)]
    if not rows:
        return []
    ex_url = _doc(F, accn, ex21)
    ex_src = src(f"Exhibit 21 · {ex21} · {form} filed {filed}", ex_url)
    return [{"type": "kv", "rows": [{"label": "Subsidiaries listed (Exhibit 21)", "value": f"{len(rows):,}",
                                     "src": derived("count of Exhibit 21 rows", f"{len(rows)} rows parsed from Exhibit 21",
                                                    [ex_src])}]},
            {"type": "table", "title": "Exhibit 21 subsidiaries", "cols": ["subsidiary", "jurisdiction"],
             "rows": [{"cells": [s, j or "—"], "src": ex_src} for s, j in rows]}]


def section(t: str, con, F: Filings, prof: dict | None) -> dict | None:
    ar = con.execute(f"""
        SELECT accn, form, filed, risk_factor_count, risk_added, risk_removed, ai_mentions, ex21_doc, primary_doc
        FROM '{D}/filing_text/filings.parquet' WHERE ticker = ? AND parse_ok ORDER BY filed DESC LIMIT 1""", [t]).fetchone()
    if not ar:
        return None
    accn, form, filed, risk_count, added, removed, ai, ex21, pd = ar
    doc = _doc(F, accn, pd)

    blocks = _new_risks(con, t, F, form, filed, accn, risk_count, added, removed, ai, doc)

    gc_row, gc_block = _going_concern(con, t, F, form, filed, accn, doc)
    if gc_row:
        blocks[0]["rows"].append(gc_row)
    if gc_block:
        blocks.append(gc_block)

    for section_id, label in (("business", "Item 1 Business"), ("mda", "Item 7 MD&A"),
                              ("market_risk", "Item 7A market risk"), ("cybersecurity", "Item 1C cybersecurity")):
        txt = _section_text(con, t, accn, section_id)
        para = _body(txt) if txt else None
        if para:
            blocks.append(_text_block(F, accn, form, filed, pd, label, para))

    biz = _section_text(con, t, accn, "business")
    if biz:
        lines = _paras(biz)
        i = next((k for k, l in enumerate(lines) if re.fullmatch(r"competition", l, re.I)), None)
        if i is not None:
            para = next((p for p in lines[i + 1:i + 4] if len(p.split()) >= 25), None)
            if para:
                blocks.append(_text_block(F, accn, form, filed, pd, "Item 1 Competition", para))

    officers = _officer_changes(t, F)
    if officers:
        blocks.append({"type": "table", "title": "Officer / director changes (8-K item 5.02, 12 months)",
                       "cols": ["filed", "form", "what"], "rows": officers})

    blocks.extend(_subsidiaries(con, t, F, form, filed, accn, ex21))
    return {"id": "filings", "title": "Filings", "blocks": blocks}
