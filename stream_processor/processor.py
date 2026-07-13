from stream_processor.indicators.sliding_window import SlidingWindowMinMax
from stream_processor.indicators.segment_tree import SegmentTree


def run_analysis(symbol: str, bars: list) -> None:
    """
    Run DSA-powered analysis on a list of daily bars.
    bars: list of dicts with 'close', 'high', 'low', 'timestamp' keys.
          Assumed newest-first (as returned by the API).
    """
    # Reverse so oldest is first — better for sequential processing
    bars = list(reversed(bars))
    closes = [bar["close"] for bar in bars]
    highs  = [bar["high"]  for bar in bars]

    print(f"\n{'='*50}")
    print(f"Analysis for {symbol} ({len(bars)} days)")
    print(f"{'='*50}")

    # ── Sliding window: 14-day rolling min/max ──────────────────────────────
    window = SlidingWindowMinMax(window_size=14)
    print("\n14-day rolling window (last 5 days):")
    print(f"  {'Date':<14} {'Close':>8} {'14d-Low':>10} {'14d-High':>10} {'Range':>8}")
    print(f"  {'-'*52}")

    for i, bar in enumerate(bars):
        window.add(bar["close"])
        if i >= 13:  # only print once we have a full window
            if i >= len(bars) - 5:  # show last 5 days
                print(f"  {bar['timestamp']:<14} "
                      f"${bar['close']:>7.2f} "
                      f"${window.get_min():>9.2f} "
                      f"${window.get_max():>9.2f} "
                      f"${window.get_range():>7.2f}")

    # ── Segment tree: arbitrary range queries on closing prices ─────────────
    max_tree = SegmentTree(closes, mode="max")
    min_tree = SegmentTree(closes, mode="min")

    print("\nSegment tree range queries on closing prices:")
    queries = [
        (0,  19,  "First 20 days"),
        (20, 49,  "Days 21–50"),
        (50, 79,  "Days 51–80"),
        (0,  99,  "Full 100 days"),
    ]
    for left, right, label in queries:
        high = max_tree.query(left, right)
        low  = min_tree.query(left, right)
        print(f"  {label:<16}  high=${high:.2f}  low=${low:.2f}  "
              f"spread=${high - low:.2f}")

    # ── Volatility signal using sliding window range ─────────────────────────
    vol_window = SlidingWindowMinMax(window_size=5)
    ranges = []
    for bar in bars:
        vol_window.add(bar["close"])
        if len(ranges) >= 4:
            ranges.append(vol_window.get_range())

    if ranges:
        avg_range = sum(ranges) / len(ranges)
        current_range = ranges[-1]
        signal = "HIGH VOLATILITY" if current_range > 1.5 * avg_range else "normal"
        print(f"\nVolatility signal (5-day range): {signal}")
        print(f"  Current 5d range: ${current_range:.2f}")
        print(f"  Average 5d range: ${avg_range:.2f}")