from typing import Optional
from alert_engine.rule_store import RuleStore, AlertRule
from stream_processor.indicators.sliding_window import SlidingWindowMinMax
from stream_processor.indicators.segment_tree import SegmentTree


class AlertEvaluator:
    """
    Evaluates alert rules against incoming price data.

    This is where the DSA from Phase 2 earns its keep — every rule
    evaluation uses the segment tree or sliding window rather than
    naive scans.
    """

    def __init__(self, rule_store: RuleStore):
        self.store = rule_store
        self.alerts_fired: list[dict] = []

    def evaluate(self, symbol: str, bars: list) -> list[dict]:
        """
        Evaluate all rules for a symbol against its price bars.
        bars: list of dicts, oldest first, each with 'close', 'timestamp'.
        Returns list of fired alerts.
        """
        rules = self.store.get_for_symbol(symbol)
        if not rules:
            return []

        closes = [bar["close"] for bar in bars]
        fired  = []

        # Build segment tree once — reused for all range queries
        max_tree = SegmentTree(closes, mode="max")
        min_tree = SegmentTree(closes, mode="min")

        # Latest values
        latest_close = closes[-1]
        latest_date  = bars[-1]["timestamp"]

        for rule in rules:
            if rule.triggered:
                continue  # don't re-fire already triggered rules

            result = self._evaluate_rule(
                rule, closes, latest_close, latest_date,
                max_tree, min_tree
            )
            if result:
                fired.append(result)
                self.store.mark_triggered(rule.id)
                self.alerts_fired.append(result)

        return fired

    def _evaluate_rule(self, rule, closes, latest_close,
                       latest_date, max_tree, min_tree) -> Optional[dict]:
        n = len(closes)
        w = min(rule.window, n)  # don't exceed available data

        if rule.rule_type == "price_above":
            if latest_close > rule.threshold:
                return self._make_alert(rule, latest_date, latest_close,
                    f"{rule.symbol} closed at ${latest_close:.2f}, "
                    f"above threshold ${rule.threshold:.2f}")

        elif rule.rule_type == "price_below":
            if latest_close < rule.threshold:
                return self._make_alert(rule, latest_date, latest_close,
                    f"{rule.symbol} closed at ${latest_close:.2f}, "
                    f"below threshold ${rule.threshold:.2f}")

        elif rule.rule_type == "drop_pct":
            # Use segment tree to find the high over the window
            window_high = max_tree.query(n - w, n - 1)
            if window_high > 0:
                drop = (window_high - latest_close) / window_high * 100
                if drop >= rule.threshold:
                    return self._make_alert(rule, latest_date, latest_close,
                        f"{rule.symbol} dropped {drop:.1f}% from "
                        f"${window_high:.2f} to ${latest_close:.2f} "
                        f"over {w} days (threshold: {rule.threshold}%)")

        elif rule.rule_type == "range_exceeds":
            # Use segment tree to find high and low over the window
            window_high = max_tree.query(n - w, n - 1)
            window_low  = min_tree.query(n - w, n - 1)
            price_range = window_high - window_low
            if price_range > rule.threshold:
                return self._make_alert(rule, latest_date, latest_close,
                    f"{rule.symbol} {w}-day range is ${price_range:.2f} "
                    f"(${window_low:.2f}–${window_high:.2f}), "
                    f"exceeds threshold ${rule.threshold:.2f}")

        return None

    def _make_alert(self, rule, date, price, message) -> dict:
        return {
            "rule_id":   rule.id,
            "symbol":    rule.symbol,
            "rule_type": rule.rule_type,
            "date":      date,
            "price":     price,
            "message":   message,
        }


# Python 3.9 compatibility
