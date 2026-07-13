import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
BASE_URL = "https://www.alphavantage.co/query"

def fetch_quote(symbol: str) -> dict:
    """Fetch the latest price quote for a stock symbol."""
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "Global Quote" not in data:
        raise ValueError(f"Unexpected response for {symbol}: {data}")

    return data["Global Quote"]

def fetch_intraday(symbol: str, interval: str = "1min") -> list:
    """Fetch the last 100 daily price bars for a symbol."""
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY,
        "outputsize": "compact",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    key = "Time Series (Daily)"
    if key not in data:
        raise ValueError(f"Unexpected response for {symbol}: {data}")

    bars = []
    for timestamp, values in data[key].items():
        bars.append({
            "timestamp": timestamp,
            "open":   float(values["1. open"]),
            "high":   float(values["2. high"]),
            "low":    float(values["3. low"]),
            "close":  float(values["4. close"]),
            "volume": int(values["5. volume"]),
        })
    return bars