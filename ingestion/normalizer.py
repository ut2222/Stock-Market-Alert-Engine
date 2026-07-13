from datetime import datetime

def normalize_quote(raw: dict, symbol: str) -> dict:
    """
    Take the raw API response and return a clean, consistent dict.
    This is the standard shape every other part of the system will use.
    """
    return {
        "symbol":    symbol.upper(),
        "price":     float(raw.get("05. price", 0)),
        "open":      float(raw.get("02. open", 0)),
        "high":      float(raw.get("03. high", 0)),
        "low":       float(raw.get("04. low", 0)),
        "volume":    int(raw.get("06. volume", 0)),
        "change_pct": raw.get("10. change percent", "0%").replace("%", ""),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def normalize_bars(bars: list, symbol: str) -> list:
    """Normalize a list of intraday bars into the standard OHLCV shape."""
    return [
        {
            "symbol":    symbol.upper(),
            "timestamp": bar["timestamp"],
            "open":      bar["open"],
            "high":      bar["high"],
            "low":       bar["low"],
            "close":     bar["close"],
            "volume":    bar["volume"],
        }
        for bar in bars
    ]