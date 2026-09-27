# Bulk-downloadable sources (checked 2026-09-27)

✅ = probed today (URL/API returned 200). Sizes from the source's own listing.
Current pulls for comparison: companyfacts + submissions per CIK, FSDS zips, 13F + insider bulk zips.

## Tier 1: pull these

| Source | ID / URL | Size | Cadence | What it gives us |
|---|---|---|---|---|
| PatentsView granted, disambiguated ✅ | ODP `PVGPATDIS` | 34.2GB (need ~1.9GB: see below) | quarterly, thru 2025-12 | **Disambiguated assignee IDs**, which mostly solves ticker alias mapping. Disambiguated inventors, which enables tracking engineer moves between companies |
| PatentsView pre-grant pubs, disambiguated ✅ | ODP `PVPGPUBDIS` | 7.8GB | quarterly, thru 2025-12 | Same for published applications (18mo lag, but earlier than grants) |
| Application front pages ✅ | ODP `APPBLXML` | 5.0GB total (weekly XML) | weekly | Titles, **abstracts**, CPC, applicant. Fills the 2026 gap PatentsView doesn't cover; abstracts go into search |
| Grant front pages ✅ | ODP `PTBLXML` | 19.8GB total (only need 2026 weeks) | weekly | Same for grants |
| Patent assignments ✅ | ODP `PASYR` + `PASDL` daily | 4.5GB + ~60MB/day | annual + daily | Ownership transfers: M&A, divestitures (MRVL auto patents → Infineon), patent sales. Keeps the alias map current |
| AI Patent Dataset ✅ | ODP `ECOPATAI` | 6.3GB | yearly (2026-02) | USPTO's own ML label for each patent's AI component, giving a **% AI patents per ticker**. Direct fit for an AI-exposure universe |
| SEC companyfacts bulk ✅ | `sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip` | 1.4GB | nightly | Every XBRL fact for every filer in one request. Replaces ~406 per-CIK calls |
| SEC submissions bulk ✅ | `.../bulkdata/submissions.zip` | 1.6GB | nightly | Every filing index. Replaces per-CIK submissions calls |
| DOL H-1B LCA disclosures ✅ | `dol.gov/.../LCA_Disclosure_Data_FY2026_Q3.xlsx` | ~100s MB/qtr | quarterly | Employer, **job title**, SOC code, worksite, wage. Hiring by role per company (e.g. "photonics design engineer" at MRVL). Automates `research/job_openings/` |

## Tier 2: useful, pull later

| Source | ID / URL | Size | Cadence | Use |
|---|---|---|---|---|
| SEC Financial Statement & **Notes** ✅ | `sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_08_notes.zip` | ~1–2GB/mo | monthly | Full XBRL incl. dimensional segment facts + note text blocks. Could replace per-filing instance parsing in `sec_segments` |
| Trademarks, daily applications ✅ | ODP `TRTDXFAP` (+ `TRTYRAP` annual) | 21GB (daily) | daily | New product names filed **before launch**. Filter by owner |
| Census intl trade API ✅ | `api.census.gov/data/timeseries/intltrade/imports/hs` | small | monthly | Imports/exports by HS code × country (8542 ICs, 8471 servers, 8517 network gear). Demand proxy for AI hardware |
| USAspending bulk awards ✅ | `api.usaspending.gov/api/v2/bulk_download/` | GBs | daily | Federal contracts by recipient. Gov/defense exposure (PLTR, etc.) |
| FRED ✅ | `fred.stlouisfed.org/graph/fredgraph.csv?id=...` | tiny | monthly | Industrial production (IPG3344S semis), rates, macro |
| Patent maintenance fees ✅ | ODP `PTMNFEE2` | 7.3GB | weekly | Which patents a company stops paying to maintain (pruning = strategic exit) |
| Patent litigation ✅ | ODP `PTLITIG` | 4.9GB | yearly (thru 2024) | Litigation exposure |
| SEC Form D ✅ | `sec.gov/files/datastandardsinnovation/data/form-d-data-sets/2026q2_d.zip` | small | quarterly | Private raises: private competitors/suppliers |

## Tier 3: known, not probed

- BIS Entity List / Consolidated Screening List (trade.gov CSV): export-control exposure (MRVL 36% China revenue).
- FCC equipment authorization: new hardware filings before launch.
- OpenAlex: research papers by company affiliation (like patents, but earlier and public).

## Skip

| Source | Why |
|---|---|
| Full-text + images (`APPDT` 4.3TB, `PTGRMP2`/`APPMP2` 14TB+, `PTGRDT` 2.9TB) | Images; front-page data has what we need |
| Full-text XML (`APPXML` 167GB, `PTGRXML` 129GB, PatentsView long text 110–120GB) | Claims/descriptions; only worth it for a watchlist, via the API |
| `PTFWPRE` file wrapper (65GB) | Prosecution history; the API covers the watchlist case |
| Office actions (`OACT`, `ECOPAIR` 300GB), Gazettes, CPC master, oath signatures, PEDS (pre-2001) | Examination process, not company signal |

## Proposed first pull
Download verified: `GET api.uspto.gov/api/v1/datasets/products/files/{ID}/{file}` with `X-API-Key` → 302 to a signed `data.uspto.gov/files/...` URL (supports Range).

| File | Zipped |
|---|---|
| PVGPATDIS `g_patent`, `g_application`, `g_assignee_disambiguated`, `g_cpc_current`, `g_wipo_technology` | 232 + 72 + 363 + 503 + 48 MB |
| PVGPATDIS `g_inventor_disambiguated` (talent moves) | 708 MB |
| PVGPATDIS `g_patent_abstract` (for search, optional) | 1,708 MB |
| PVPGPUBDIS same tables (pending apps) | ~2GB |
| ECOPATAI `2023_r1/ai_model_predictions.csv.zip` | 818 MB |
| PASYR (assignments) | 4.5GB |
| SEC companyfacts.zip + submissions.zip | 1.4 + 1.6GB |

~14GB download. Filtered to universe assignees, it drops to well under 1GB in DuckDB.
Order: PatentsView → ECOPATAI → PASYR → APPBLXML/PTBLXML 2026 weeks (gap fill) → SEC bulk zips → LCA.
