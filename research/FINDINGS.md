# Public SEC data: what's actually useful (universe-wide, 2026-09-26)

428 stocks (15 deregistered tickers moved to `_meta.delisted`, 9 renamed), 406 with SEC CIKs.
Data under `~/.local/share/nvim/security_spread/` (+ `sec_13f/`). Pull scripts in `services/sec_*.py`.

| Source | Module | Size | Coverage | Verdict |
|---|---|---|---|---|
| XBRL facts | sec_financials | 25MB, 3.9M facts | 405/406 | **Core.** 15+ yrs annual, ~10 yrs quarterly for US filers. 20-F filers: no quarters, some missing FY2025 (TSM, UMC). History under shells/old businesses (MTCH=IAC, JCI=Tyco, NBIS=Yandex) needs per-ticker cutoff. |
| Segment revenue | sec_segments | 3MB | 384 useful splits | **High.** Geography comparable across cos (country codes); product/segment members are custom names, need a hand map for cross-co themes. |
| 13F holders | sec_13f | 125MB (6 qtrs, whole market) | 416/428 mapped | **High (CANSLIM I).** Needs typo cap + stable-filer panel. CUSIP changes break QoQ (HON). |
| Filing index / 8-K | sec_events | 16MB, 694k filings | 406/406 | **High, cheap.** 2.02 = reliable earnings dates for US filers; 5.02 noisy without text. Foreign filers: 6-K, no item codes. |
| Insider trades | sec_insiders | 2MB (6 qtrs bulk) | 380/407 CIKs | **Medium.** Buys rare (<1% rows); cluster buys w/ $25k floor give a short useful list. Bulk lags 0–3 months. |
| 10-K/20-F text | sec_filing_text | 93MB | 761/808 split OK | **High for search.** YoY new-risk sentences are real signal when <~40% new (NVDA China, MRVL AI EDA); above that = rewrite. 40-F weak. |
| Earnings releases | sec_earnings | 12MB, 1,575 releases | 402/406 | **High.** Rule-based guidance lines for 81% of releases (~75% precision). Small LLM pass over extracted lines would structure them. |
| Patents (USPTO) | — | — | — | **Blocked:** ODP API key required. |

Search: `services/search.py` (BM25, DuckDB fts) over filing text + new risks + earnings + guidance,
187k chunks, 368MB index, ~0.45s/query. `<leader>sf`, `f` on a heatmap tile.
