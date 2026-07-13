from fastapi import APIRouter, HTTPException
from ingestion.fetcher import fetch_intraday
from ingestion.normalizer import normalize_bars
import json
import os

router = APIRouter()
CACHE_FILE = "historical_cache.json"


def load_cache() -> dict:
    """Load historical data from cache file."""
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


@router.get("/tickers")
def get_tickers():
    """Return list of all symbols we have data for."""
    cache = load_cache()
    return {"symbols": list(cache.keys())}


@router.get("/tickers/{symbol}/history")
def get_history(symbol: str, days: int = 30):
    """
    Return the last N days of OHLCV bars for a symbol.
    Example: GET /api/tickers/AAPL/history?days=14
    """
    cache = load_cache()
    symbol = symbol.upper()

    if symbol not in cache:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} not found. Available: {list(cache.keys())}"
        )

    bars = cache[symbol][:days]  # newest first, take first N
    return {
        "symbol": symbol,
        "days":   len(bars),
        "bars":   bars
    }


@router.get("/tickers/{symbol}/latest")
def get_latest(symbol: str):
    """Return just the latest bar for a symbol."""
    cache = load_cache()
    symbol = symbol.upper()

    if symbol not in cache:
        raise HTTPException(status_code=404, detail=f"{symbol} not found.")

    latest = cache[symbol][0]  # newest is first
    return {"symbol": symbol, "latest": latest}


@router.get("/tickers/{symbol}/stats")
def get_stats(symbol: str):
    """
    Return DSA-computed stats: 14-day rolling range,
    segment tree range queries across the full history.
    """
    from stream_processor.indicators.segment_tree import SegmentTree

    cache = load_cache()
    symbol = symbol.upper()

    if symbol not in cache:
        raise HTTPException(status_code=404, detail=f"{symbol} not found.")

    bars   = list(reversed(cache[symbol]))  # oldest first
    closes = [b["close"] for b in bars]

    max_tree = SegmentTree(closes, mode="max")
    min_tree = SegmentTree(closes, mode="min")
    n = len(closes)

    return {
        "symbol": symbol,
        "total_days": n,
        "latest_close": closes[-1],
        "range_queries": {
            "last_14_days": {
                "high":   max_tree.query(n - 14, n - 1),
                "low":    min_tree.query(n - 14, n - 1),
                "spread": max_tree.query(n - 14, n - 1) - min_tree.query(n - 14, n - 1)
            },
            "last_30_days": {
                "high":   max_tree.query(n - 30, n - 1),
                "low":    min_tree.query(n - 30, n - 1),
                "spread": max_tree.query(n - 30, n - 1) - min_tree.query(n - 30, n - 1)
            },
            "all_time": {
                "high":   max_tree.query(0, n - 1),
                "low":    min_tree.query(0, n - 1),
                "spread": max_tree.query(0, n - 1) - min_tree.query(0, n - 1)
            }
        }
    }