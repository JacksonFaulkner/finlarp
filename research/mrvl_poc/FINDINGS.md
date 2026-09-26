# MRVL POC: what public data is actually useful (2026-09-26)

Raw data in `raw/` (gitignored, ~1GB mostly 13F TSVs). `pull_docs.py` fetches 10-K + Form 4.

| Source | What we got for MRVL | Signal | Cost | Verdict |
|---|---|---|---|---|
| XBRL companyfacts (2 CIKs) | FY2008–FY2026 annual revenue, 588+378 concepts | Core fundamentals | 2 req/CIK | KEEP. Needs CIK alias map (1058057 -> 1835632) + concept fallback (`Revenues` pre-FY2019) |
| XBRL instance per 10-K/10-Q (`*_htm.xml`) | Data Center $6.10B / $8.19B (74%), revenue by country (CN $2.97B) | Product mix, geo exposure | 1 req/filing (~2.7MB) | KEEP. Beats FSDS zips for a 443-name universe; FSDS only for backfill |
| 10-K text | 70k words. 1A risk 23k, Item 8 21k, Item 7 MD&A 8k, Item 1 business 6.8k | Item 1 + 7 worth summarizing; 1A only as YoY diff; Item 8 redundant w/ XBRL | 1 req, regex split works | KEEP 1/1A/7 only |
| 8-K item codes (submissions JSON) | 2.02 earnings x81, 5.02 exec change x57, 1.01 material deal x20 | Event stream, earnings dates | Free (already in submissions) | KEEP. Drop 9.01/8.01 noise |
| Form 4 | 14 insiders, 67 filings/12mo, 0 open-mkt buys, $49.6M sells (10b5-1 / tax F) | Low for MRVL; only `P` buys matter | 67 req/yr | KEEP cheap: alert on code P only |
| 13F bulk (Q1 vs Q2 2026) | Stable-panel holders 1486 -> 2143 (+44%), shares 727M -> 700M, FMR -74M | Real CANSLIM "I" signal | 100MB zip/qtr, covers whole universe | KEEP. Needs sanity filter (CalSTRS reported 386M sh = junk), filer-panel normalization |
| Exhibit 21 | Subsidiary list (Cavium, etc.) | Only for patent assignee -> ticker mapping | 1 req | KEEP as lookup |
| Patents (USPTO ODP) | BLOCKED: PatentsView moved to ODP 2026-03-20, API + bulk need key (401) | 10-K: ">10,000 issued + pending" | Need ODP API key | TODO once key |
| Pre-2009 filings | 10-K/Q/8-K back to 2000, HTML only | Low | Parsing pain | SKIP |

Not yet tried: 8-K 2.02 EX-99.1 earnings press releases (guidance), 10-Q instances for quarterly segment history.
