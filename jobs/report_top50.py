"""Build source-linked research reports for the Technology top 50.

Uses the saved market-cap screener, each issuer's latest SEC filing, Exa
search for issuer products/customers, and one GPT-6 Luna structured response.
Outputs one JSON per ticker and a manifest with token/search-based cost estimates.

    uv run jobs/report_top50.py
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import json
import re
from pathlib import Path

import requests

PLUGIN = Path(__file__).resolve().parents[1]
from models.earnings_scrape import SecurityReportPanels
from sources import keys, sec_http, universe, yahoo
from sources.sec_earnings import html_to_text

MODEL = "gpt-6-luna"
WORKERS = 4  # bounded so Exa stays well below its default QPS ceiling
EXA_RESULTS = 3
OUT_ROOT = PLUGIN / "research" / "top50_runs"
SEC_ID_PREFIX = "sec_"


def _sec_text(url: str) -> str:
    r = sec_http.get(url)
    r.raise_for_status()
    return r.text


def latest_filing(ticker: str) -> dict:
    ciks = universe.ciks(ticker)
    if not ciks:
        raise ValueError("no SEC CIK mapping")
    cik = ciks[0]
    sub = universe.submissions(cik)
    recent = sub["filings"]["recent"]
    forms = {"10-Q", "10-K", "20-F", "40-F", "6-K"}
    choices = []
    for i, form in enumerate(recent.get("form", [])):
        if form not in forms:
            continue
        filed = recent["filingDate"][i]
        if filed > dt.date.today().isoformat():
            continue
        choices.append({
            "cik": cik,
            "form": form,
            "filed": filed,
            "report_date": recent.get("reportDate", [""] * len(recent["form"]))[i],
            "accession": recent["accessionNumber"][i],
            "primary_document": recent["primaryDocument"][i],
        })
    if not choices:
        raise ValueError("no recent SEC periodic filing")
    # Prefer periodic financial reports over 6-Ks when dates are tied.
    choices.sort(key=lambda f: (f["filed"], f["form"] != "6-K"), reverse=True)
    filing = choices[0]
    accession_path = filing["accession"].replace("-", "")
    filing["url"] = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_path}/{filing['primary_document']}"
    return filing


def excerpts(text: str) -> str:
    lines = text.splitlines()
    patterns = re.compile(
        r"financial statements|statements of (operations|income|cash flows|financial position)|"
        r"management.s discussion|results of operations|revenue|customer|end market|"
        r"product|business overview|risk factors|liquidity|debt|guidance|outlook",
        re.I,
    )
    chunks, last_end = [], -1
    for i, line in enumerate(lines):
        if not patterns.search(line) or i <= last_end:
            continue
        lo, hi = max(0, i - 2), min(len(lines), i + 12)
        chunks.append("\n".join(lines[lo:hi]))
        last_end = hi
    # Avoid sending the whole annual filing; preserve the start as identity/context.
    return "\n\n[… filing excerpt …]\n\n".join(chunks[:55])[:45_000]


def exa_search(key: str, query: str, sid: str, domains: list[str] | None = None) -> list[dict]:
    payload = {
        "query": query,
        "type": "auto",
        "numResults": EXA_RESULTS,
        "contents": {"text": {"maxCharacters": 3500}},
    }
    if domains:
        payload["includeDomains"] = domains
    r = requests.post(
        "https://api.exa.ai/search",
        headers={"x-api-key": key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return [
        {
            "source_id": f"{sid}_{i + 1}",
            "label": item.get("title") or item["url"],
            "url": item["url"],
            "kind": "exa_search_result",
            "text": item.get("text", "")[:3500],
        }
        for i, item in enumerate(r.json().get("results", []))
        if item.get("url") and item.get("text")
    ]


def json_schema() -> dict:
    schema = SecurityReportPanels.model_json_schema()

    def convert(node):
        if isinstance(node, dict):
            if "oneOf" in node:
                node["anyOf"] = node.pop("oneOf")
            node.pop("discriminator", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}).keys())
            for value in node.values():
                convert(value)
        elif isinstance(node, list):
            for value in node:
                convert(value)

    convert(schema)
    return schema


def save_usage(path: Path, usage: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(usage))
    tmp.replace(path)


def quote_key(text: str) -> str:
    """Ignore HTML table punctuation/spacing while preserving word/number order."""
    return "".join(ch.casefold() for ch in text if ch.isalnum())


def run_ticker(company: dict, openai_key: str, exa_key: str, out_dir: Path) -> dict:
    ticker = company["symbol"].upper()
    report_path = out_dir / f"{ticker}.json"
    usage_path = out_dir / ".usage" / f"{ticker}.json"
    usage_state = {"exa_search_calls": 0, "exa_content_pages": 0, "input_tokens": 0,
                   "cached_input_tokens": 0, "output_tokens": 0}
    if report_path.exists():
        try:
            saved = json.loads(report_path.read_text())
            if saved.get("ticker") == ticker and saved.get("sections"):
                usage = saved.get("usage", {})
                input_tokens = int(usage.get("input_tokens", 0))
                cached_tokens = int(usage.get("cached_input_tokens", 0))
                output_tokens = int(usage.get("output_tokens", 0))
                openai_usd = max(0, input_tokens - cached_tokens) * 0.10 / 1_000_000 + cached_tokens * 0.01 / 1_000_000 + output_tokens * 0.50 / 1_000_000
                exa_usd = int(usage.get("exa_search_calls", 0)) * 7 / 1000 + int(usage.get("exa_content_pages", 0)) / 1000
                usage.update(estimated_openai_usd=round(openai_usd, 8), estimated_exa_usd=round(exa_usd, 8),
                             estimated_total_usd=round(openai_usd + exa_usd, 8))
                saved["usage"] = usage
                report_path.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")
                return {"ticker": ticker, "status": "cached", "market_cap": company.get("market_cap"),
                        "input_tokens": input_tokens, "cached_input_tokens": cached_tokens,
                        "output_tokens": output_tokens, "exa_search_calls": usage.get("exa_search_calls", 0),
                        "exa_content_pages": usage.get("exa_content_pages", 0),
                        "openai_usd": openai_usd, "exa_usd": exa_usd,
                        "cost_usd": openai_usd + exa_usd, "sourced_items": saved.get("validation", {}).get("sourced_items", 0)}
        except Exception:
            pass

    try:
        filing = latest_filing(ticker)
    except ValueError:
        # Some Yahoo US listings are foreign OTC tickers absent from SEC's
        # ticker map. Still produce a useful, explicitly web-sourced report.
        filing = None
    filing_text = html_to_text(_sec_text(filing["url"])) if filing else ""
    filing_id = f"{SEC_ID_PREFIX}{ticker.lower()}_{filing['form'].lower().replace('-', '')}" if filing else None
    sources = []
    if filing:
        sources.append({
            "source_id": filing_id,
            "label": f"{ticker} {filing['form']} filed {filing['filed']}",
            "url": filing["url"],
            "kind": "sec_filing",
            "text": filing_text,
        })
    name = company.get("shortName") or company.get("longName") or ticker
    searches = [
        (f"{name} {ticker} products applications customers end markets official company", f"{ticker.lower()}_business", None),
        (f"{name} {ticker} latest earnings revenue operating income cash flow filing", f"{ticker.lower()}_results", ["sec.gov"]),
    ]
    if not filing:
        searches = [
            (f"{name} {ticker} products applications customer end markets official", f"{ticker.lower()}_business", None),
            (f"{name} {ticker} latest earnings financial results official investor relations", f"{ticker.lower()}_results", None),
            (f"{name} annual report latest revenue customers products", f"{ticker.lower()}_annual", None),
        ]
    if usage_path.exists():
        try:
            usage_state.update(json.loads(usage_path.read_text()))
        except Exception:
            pass
    exa_calls = int(usage_state.get("exa_search_calls", 0))
    page_count = int(usage_state.get("exa_content_pages", 0))
    for query, sid, domains in searches:
        hits = exa_search(exa_key, query, sid, domains)
        exa_calls += 1
        page_count += len(hits)
        usage_state.update(exa_search_calls=exa_calls, exa_content_pages=page_count)
        save_usage(usage_path, usage_state)
        sources.extend(hits)

    context = []
    if filing:
        context.append(f"SOURCE_ID={filing_id}\nTITLE={sources[0]['label']}\nURL={filing['url']}\n{excerpts(filing_text)}")
    context.extend(
        f"SOURCE_ID={s['source_id']}\nTITLE={s['label']}\nURL={s['url']}\n{s['text']}"
        for s in sources[(1 if filing else 0):]
    )
    prompt = (
        f"Create a reviewable, source-grounded company report for {name} ({ticker}), centered on "
        + (f"its latest filed reporting period {filing.get('report_date') or filing['filed']} ({filing['form']}). " if filing else "the latest information in the supplied company and investor sources. ")
        + "Use 5-7 "
        "sections and only supplied Ratatui block types: table, kv, bars, series, text. Include business model; "
        "products and applications; end-market demand; documented customer/channel facts separately from "
        "inferred buyer archetypes; latest-quarter income statement and cash/debt facts when present; and "
        "drivers/risks. Label each factual leaf reported, inferred, or derived. Never invent named customers, "
        "products, or numbers. For every claim/value include an evidence source_id from the supplied catalog "
        "and a short verbatim quote from that exact source. If a requested fact is absent, omit it or say it is "
        "not disclosed with a source. Keep financial periods exactly as reported; distinguish quarter from YTD. "
        "Return concise data only.\n\nSOURCE CATALOG AND EXCERPTS:\n" + "\n\n========== SOURCE BREAK ==========\n\n".join(context)
    )
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "input": [
                {"role": "system", "content": "Produce conservative, source-grounded JSON. Cite only supplied source IDs; never create URLs."},
                {"role": "user", "content": prompt},
            ],
            "text": {"format": {"type": "json_schema", "name": "security_report", "strict": True, "schema": json_schema()}},
            "max_output_tokens": 7000,
        },
        timeout=240,
    )
    response.raise_for_status()
    payload = response.json()
    usage = payload.get("usage", {})
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    cached_tokens = int((usage.get("input_tokens_details") or {}).get("cached_tokens", 0))
    usage_state.update(
        input_tokens=usage_state.get("input_tokens", 0) + input_tokens,
        cached_input_tokens=usage_state.get("cached_input_tokens", 0) + cached_tokens,
        output_tokens=usage_state.get("output_tokens", 0) + output_tokens,
    )
    save_usage(usage_path, usage_state)
    output_text = "".join(
        part.get("text", "")
        for item in payload.get("output", []) if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    )
    panels = SecurityReportPanels.model_validate_json(output_text)
    source_map = {s["source_id"]: s for s in sources}
    referenced, dropped = set(), 0
    for section in panels.sections:
        clean_blocks = []
        for block in section.blocks:
            leaves = block.rows if block.type in ("table", "kv") else block.points if block.type == "series" else block.items if block.type == "bars" else [block]
            valid = []
            for leaf in leaves:
                ev = leaf.evidence
                src = source_map.get(ev.source_id)
                if src and ev.quote.strip() and quote_key(ev.quote) in quote_key(src["text"]):
                    valid.append(leaf)
                    referenced.add(ev.source_id)
                else:
                    dropped += 1
            if block.type == "table":
                block.rows = valid
            elif block.type == "kv":
                block.rows = valid
            elif block.type == "series":
                block.points = valid
            elif block.type == "bars":
                block.items = valid
            elif not valid:
                continue
            if valid:
                clean_blocks.append(block)
        section.blocks = clean_blocks
    if not referenced:
        raise ValueError("model returned no claims with verifiable evidence")

    # GPT-6 Luna standard short-context rates: uncached/cached input and output.
    uncached_tokens = max(0, usage_state["input_tokens"] - usage_state["cached_input_tokens"])
    llm_cost = uncached_tokens * 0.10 / 1_000_000 + usage_state["cached_input_tokens"] * 0.01 / 1_000_000 + usage_state["output_tokens"] * 0.50 / 1_000_000
    # Exa standard Search ($7/1k requests) + Contents ($1/1k returned pages).
    exa_cost = exa_calls * 7 / 1000 + page_count / 1000
    report = {
        "ticker": ticker,
        "company": name,
        "market_cap_usd": company.get("market_cap"),
        "as_of": (filing.get("report_date") or filing["filed"]) if filing else None,
        "filing": {k: filing[k] for k in ("form", "filed", "accession", "url")} if filing else None,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL,
        "source_count": len(referenced),
        "sources": [{k: s[k] for k in ("source_id", "label", "url", "kind")} for s in sources if s["source_id"] in referenced],
        "sections": [section.model_dump(mode="json") for section in panels.sections],
        "validation": {"all_source_ids_resolve": True, "all_quotes_verified": True, "unverified_claims_dropped": dropped,
                       "sourced_items": sum(len(b.rows) if b.type in ("table", "kv") else len(b.points) if b.type == "series" else len(b.items) if b.type == "bars" else 1 for s in panels.sections for b in s.blocks)},
        "usage": {"input_tokens": usage_state["input_tokens"], "cached_input_tokens": usage_state["cached_input_tokens"], "output_tokens": usage_state["output_tokens"],
                  "exa_search_calls": exa_calls, "exa_content_pages": page_count,
                  "estimated_openai_usd": round(llm_cost, 8), "estimated_exa_usd": round(exa_cost, 8),
                  "estimated_total_usd": round(llm_cost + exa_cost, 8)},
    }
    tmp = report_path.with_suffix(".json.part")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(report_path)
    return {"ticker": ticker, "status": "generated", "market_cap": company.get("market_cap"),
            "input_tokens": usage_state["input_tokens"], "cached_input_tokens": usage_state["cached_input_tokens"], "output_tokens": usage_state["output_tokens"],
            "exa_search_calls": exa_calls, "exa_content_pages": page_count,
            "openai_usd": llm_cost, "exa_usd": exa_cost, "cost_usd": llm_cost + exa_cost,
            "sourced_items": sum(len(b.rows) if b.type in ("table", "kv") else len(b.points) if b.type == "series" else len(b.items) if b.type == "bars" else 1 for s in panels.sections for b in s.blocks)}


def main() -> None:
    openai_key = keys.get("OPENAI_API_KEY")
    exa_key = keys.get("EXA_API_KEY")
    if not openai_key or not exa_key:
        raise SystemExit("OPENAI_API_KEY and EXA_API_KEY are required in .env")
    today = dt.date.today().isoformat()
    out_dir = OUT_ROOT / f"technology_top50_{today}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # This is the repo's named watchlist: Technology, top 50, sorted by market cap.
    companies = yahoo.cmd_screen(sector="Technology", industry=None, top=50)["quotes"]
    companies.sort(key=lambda c: c.get("market_cap") or 0, reverse=True)
    summary = []
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(run_ticker, c, openai_key, exa_key, out_dir): c for c in companies}
        for future in concurrent.futures.as_completed(futures):
            company = futures[future]
            try:
                result = future.result()
                summary.append(result)
                print(json.dumps({"ticker": result["ticker"], "status": result["status"], "cost_usd": round(result.get("cost_usd", 0), 5)}), flush=True)
            except Exception as exc:
                usage_path = out_dir / ".usage" / f"{str(company.get('symbol', '')).upper()}.json"
                partial = json.loads(usage_path.read_text()) if usage_path.exists() else {}
                in_tokens, out_tokens = partial.get("input_tokens", 0), partial.get("output_tokens", 0)
                exa_calls, pages = partial.get("exa_search_calls", 0), partial.get("exa_content_pages", 0)
                cached = partial.get("cached_input_tokens", 0)
                failed_openai = max(0, in_tokens - cached) * 0.10 / 1_000_000 + cached * 0.01 / 1_000_000 + out_tokens * 0.50 / 1_000_000
                failed_exa = exa_calls * 7 / 1000 + pages / 1000
                failure = {"ticker": company.get("symbol"), "market_cap": company.get("market_cap"), "error": str(exc)[:500],
                           "input_tokens": in_tokens, "output_tokens": out_tokens, "exa_search_calls": exa_calls,
                           "exa_content_pages": pages, "estimated_openai_usd": failed_openai,
                           "estimated_exa_usd": failed_exa, "estimated_cost_usd": failed_openai + failed_exa}
                failures.append(failure)
                print(json.dumps({"ticker": failure["ticker"], "status": "failed", "error": failure["error"]}), flush=True)
    summary.sort(key=lambda r: next((c.get("market_cap") or 0 for c in companies if c["symbol"].upper() == r["ticker"]), 0), reverse=True)
    failures.sort(key=lambda r: r["ticker"] or "")
    openai_usd = sum(r.get("openai_usd", 0) for r in summary) + sum(r.get("estimated_openai_usd", 0) for r in failures)
    exa_usd = sum(r.get("exa_usd", 0) for r in summary) + sum(r.get("estimated_exa_usd", 0) for r in failures)
    manifest = {
        "universe": "Technology top 50 by market cap (security_spread named watchlist)",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "market_cap_source": "Yahoo Finance screener; intradaymarketcap descending",
        "model": MODEL,
        "parallel_workers": WORKERS,
        "requested_companies": len(companies),
        "successful_reports": sum(r["status"] in ("generated", "cached") for r in summary),
        "generated_this_run": sum(r["status"] == "generated" for r in summary),
        "failures": failures,
        "estimated_openai_usd": round(openai_usd, 6),
        "estimated_exa_usd": round(exa_usd, 6),
        "estimated_total_usd": round(openai_usd + exa_usd, 6),
        "estimate_basis": "GPT-6 Luna standard short-context rates using API-reported cached tokens; Exa Search and returned-content per-page list rates. Exa free credits/account discounts are not included, so actual invoice charges may be lower.",
        "companies": summary,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manifest": str(out_dir / "run_manifest.json"), "reports": manifest["successful_reports"],
                      "failures": len(failures), "estimated_openai_usd": manifest["estimated_openai_usd"],
                      "estimated_exa_usd": manifest["estimated_exa_usd"], "estimated_total_usd": manifest["estimated_total_usd"]}), flush=True)


if __name__ == "__main__":
    main()
