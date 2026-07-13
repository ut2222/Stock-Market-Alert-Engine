import time
import json
import os
from ingestion.fetcher import fetch_quote, fetch_intraday
from ingestion.normalizer import normalize_quote, normalize_bars

WATCHLIST = ["AAPL", "TSLA", "GOOGL"]

CACHE_FILE = "historical_cache.json"

def load_historical_data():
    if os.path.exists(CACHE_FILE):
        print("Loading from cache (no API call)...")
        with open(CACHE_FILE, "r") as f:
            return json.load(f)

    all_bars = {}
    for symbol in WATCHLIST:
        try:
            raw = fetch_intraday(symbol)
            bars = normalize_bars(raw, symbol)
            all_bars[symbol] = bars
            print(f"Loaded {len(bars)} bars for {symbol} — "
                  f"latest close: ${bars[0]['close']:.2f}")
            time.sleep(12)
        except Exception as e:
            print(f"Error loading {symbol}: {e}")

    with open(CACHE_FILE, "w") as f:
        json.dump(all_bars, f)
    print("Saved to cache.")
    return all_bars

def poll_quotes():
    """Poll one symbol at a time, slowly, to respect free tier limits."""
    print("\nStarting quote poller... (Ctrl+C to stop)\n")
    i = 0
    while True:
        symbol = WATCHLIST[i % len(WATCHLIST)]
        try:
            raw = fetch_quote(symbol)
            tick = normalize_quote(raw, symbol)
            print(f"[{tick['fetched_at']}] {tick['symbol']:6s}  "
                  f"${tick['price']:.2f}  "
                  f"({tick['change_pct']}%)")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
        i += 1
        time.sleep(15)  # one request every 15 seconds


if __name__ == "__main__":
    print("=== Loading historical data ===")
    historical = load_historical_data()

    print(f"\nLoaded data for: {list(historical.keys())}")
    print(f"Each symbol has {len(next(iter(historical.values())))} bars\n")

    # We'll pass `historical` into the stream processor in Phase 2
    # For now just confirm it's all loaded correctly
    print("=== Sample: last 3 AAPL closes ===")
    for bar in historical.get("AAPL", [])[:3]:
        print(f"  {bar['timestamp']}  close=${bar['close']:.2f}  vol={bar['volume']:,}")

    print("\n=== Phase 1 complete! Data pipeline working. ===\n")

    from stream_processor.processor import run_analysis
    print("=== Phase 2: DSA Analysis ===")
    for symbol, bars in historical.items():
        run_analysis(symbol, bars)


    # ── Phase 3: Alert Engine ─────────────────────────────────────────
    from alert_engine.rule_store import RuleStore, AlertRule
    from alert_engine.evaluator import AlertEvaluator
    from alert_engine.dispatcher import AlertDispatcher

    print("\n=== Phase 3: Alert Engine ===")
    store      = RuleStore()
    evaluator  = AlertEvaluator(store)
    dispatcher = AlertDispatcher()

    # Define some rules — tweak thresholds to match your data
    rules = [
        AlertRule("AAPL",  "price_above",   300.0, description="AAPL above $300"),
        AlertRule("AAPL",  "range_exceeds",  20.0, window=14,
                  description="AAPL 14-day range over $20"),
        AlertRule("TSLA",  "drop_pct",        5.0, window=14,
                  description="TSLA dropped 5%+ in 14 days"),
        AlertRule("TSLA",  "range_exceeds",  50.0, window=14,
                  description="TSLA 14-day range over $50"),
        AlertRule("GOOGL", "price_below",   400.0, description="GOOGL below $400"),
        AlertRule("GOOGL", "drop_pct",        8.0, window=20,
                  description="GOOGL dropped 8%+ in 20 days"),
    ]

    print("\nRegistering rules:")
    for rule in rules:
        store.add(rule)

    print("\nEvaluating rules against latest data...")
    for symbol, bars in historical.items():
        bars_oldest_first = list(reversed(bars))
        fired = evaluator.evaluate(symbol, bars_oldest_first)
        dispatcher.dispatch(fired)

    dispatcher.summary()
    print("\n=== Phase 3 complete! ===\n")

    poll_quotes()