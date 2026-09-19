--- Named watchlists for the picker. Each entry is either:
---   { kind = "portfolio" }                                 -- real etrade positions
---   { kind = "screen", sector = ..., industry = ..., top = N }  -- yahoo screener, sized by market cap
---   { kind = "symbols", symbols = { ... } }                 -- fixed list, yahoo quotes, equal-sized tiles

return {
  {
    name = "My Portfolio",
    kind = "portfolio",
  },
  {
    name = "Data Center / AI Infra (top 25 by market cap)",
    kind = "screen",
    industry = "Semiconductors",
    top = 25,
  },
  {
    name = "Technology (top 50 by market cap)",
    kind = "screen",
    sector = "Technology",
    top = 50,
  },
}
