# finlarp

**Fin**ancial **L**earning **A**nd **R**esearch **P**latform.

A terminal research desk for an amateur. I don't work in finance; this is
where I practice the job: read filings, check the numbers, track a
portfolio, pretend I have a Bloomberg. It runs on public SEC EDGAR data
pulled to local files, with a terminal UI and a Neovim plugin on top.

It's a personal project shared as-is. Expect rough edges and assumptions
about my setup. Nothing here is investment advice.

## The rule

Every number on screen carries its source: a link to the filing that
reported it (opening at the quoted text), or the formula and inputs it was
computed from. Press `i` on any value to see where it came from. A value
without a source is treated as a bug. See [`tui/ARCHITECTURE.md`](tui/ARCHITECTURE.md).

## Screens

| Screen | What it shows |
|---|---|
| `dossier` | One-ticker briefing: revenue and segments, guidance, 13F flows, insider trades, new risk factors |
| `canslim` | CANSLIM scorecard, each letter graded with its evidence |
| `search` | Full-text search over 10-K/20-F text, earnings releases, guidance and patents |
| `chart` | Price history |
| `portfolio` | Your account: equity vs benchmark, drawdown, positions (E*TRADE; some tabs are placeholders) |
| `earnings` | Structured earnings report (proof of concept, MRVL only) |

## Data

Pulled once into `~/.local/share/nvim/finlarp/`, then read locally. The
universe is about 430 AI-exposed stocks (`data/ai_stocks.json`).

| Data | Source |
|---|---|
| Financial statements, 15+ years | XBRL companyfacts |
| Segment and geographic revenue | XBRL instance documents |
| Institutional holdings, 6 quarters | Form 13F data sets |
| Insider buys and sells | Form 3/4/5 data sets |
| Filing index and 8-K events | EDGAR submissions |
| 10-K / 20-F text, year-over-year new risk factors | Annual reports |
| Earnings releases and extracted guidance | 8-K item 2.02 exhibits |
| Granted US patents matched to tickers | PatentsView, USPTO AI Patent Dataset |
| Company profiles | Yahoo Finance |

[`research/FINDINGS.md`](research/FINDINGS.md) has coverage and known problems per source.

## Layout

```
tui/                 terminal UI (Rust, ratatui); reads the DuckDB file
lua/finlarp/         Neovim plugin: launches the TUI, treemap dashboards, pickers, document viewer
sources/             data pullers, one module per dataset
views/               derived data: search index, CANSLIM scores, dossiers
models/              scoring and extraction logic
jobs/                batch scripts
mcp_server.py        read-only MCP server over the same data
```

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.12+
- Rust toolchain
- Neovim 0.10+, for the plugin
- tmux (optional; the TUI opens in a tmux popup, otherwise a floating terminal)
- E*TRADE API keys, only for the portfolio screen

## Setup

```sh
git clone https://github.com/JacksonFaulkner/finlarp
cd finlarp
cp .env.example .env    # fill in the keys you need
just setup              # uv sync + cargo build --release
```

Neovim, with lazy.nvim:

```lua
{
  "JacksonFaulkner/finlarp",
  keys = {
    { "<leader>sf", function() require("finlarp").pick_search() end, desc = "finlarp: search filings" },
    { "<leader>sc", function() require("finlarp").pick_canslim() end, desc = "finlarp: CANSLIM" },
    { "<leader>sd", function() require("finlarp").pick_dossier() end, desc = "finlarp: dossier" },
    { "<leader>sw", function() require("finlarp").pick_universe() end, desc = "finlarp: universe" },
  },
}
```

The binary also runs on its own:

```sh
tui/target/release/finlarp "" "" "" dossier MRVL
```

Press `?` on any screen for its keys.

## Pulling data

Each puller in `sources/` runs on its own; its module docstring describes
what it fetches. SEC allows 10 requests per second per client; each process
defaults to 1.5 (`SEC_RPS` overrides it).

```sh
uv run python sources/bulk_pull.py              # large bulk files (patents, SEC data sets)
uv run python sources/sec_filing_text.py ingest
uv run python sources/sec_filing_text.py build
uv run python views/dossier.py --all
```

## MCP server

`mcp_server.py` gives an agent read access to the same data over stdio:
full-text search, company briefings, financial time series and read-only SQL.

```sh
claude mcp add finlarp -- "$PWD/.venv/bin/python" "$PWD/mcp_server.py"
```

## Development

```sh
just check   # stylua, selene, ruff, clippy, cargo test
just hooks   # install pre-commit hooks
```

## License

MIT
