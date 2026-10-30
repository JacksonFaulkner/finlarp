from sources import yahoo

PAYLOAD = {
    "quoteSummary": {
        "result": [
            {
                "topHoldings": {
                    "holdings": [
                        {"symbol": "nvda", "holdingName": "NVIDIA Corp", "holdingPercent": {"raw": 0.0833}},
                        {"symbol": "FGXXX", "holdingName": "First American Government", "holdingPercent": {"raw": 0.15}},
                        {"symbol": "", "holdingName": "No ticker", "holdingPercent": {"raw": 0.01}},
                        {"symbol": "AMD", "holdingName": "Advanced Micro Devices", "holdingPercent": {}},
                    ]
                }
            }
        ],
        "error": None,
    }
}


def test_parse_top_holdings_keeps_weighted_rows_with_a_ticker():
    rows = yahoo.parse_top_holdings(PAYLOAD, "2026-10-30")
    assert [r["ticker"] for r in rows] == ["NVDA", "FGXXX"]
    assert rows[0] == {"ticker": "NVDA", "name": "NVIDIA Corp", "weight": 0.0833, "fetched_on": "2026-10-30"}


def test_parse_top_holdings_empty_payload():
    assert yahoo.parse_top_holdings({"quoteSummary": {"result": None}}, "2026-10-30") == []
    assert yahoo.parse_top_holdings({}, "2026-10-30") == []
