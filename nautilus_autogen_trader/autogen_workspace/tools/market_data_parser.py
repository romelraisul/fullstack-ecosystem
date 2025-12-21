def parse_market_data(symbol):
    """
    Mock Market Data Parser.
    In production, connect to Nautilus Trader's Data Engine or external API.
    """
    print(f"[TOOL] Parsing Market Data for: {symbol}")
    return {"symbol": symbol, "price": 50000, "volume": 1000000, "trend": "UP"}
